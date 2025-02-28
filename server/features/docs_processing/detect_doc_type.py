#!/usr/bin/env python
import os
import re
from collections import defaultdict
from datetime import datetime

import boto3

from features.docs_processing.detect_doc_type_ollama import classify_document_ollama
from features.docs_processing.document_processing_db import get_result_by_filename
from features.docs_processing.utils import extract_text_from_pdf, convert_pdf_to_images
from server.features.docs_processing.detect_doc_type_bedrock import classify_document

os.environ["TOKENIZERS_PARALLELISM"] = "false"
import asyncio
import json
import io
import logging
from typing import Optional, Dict, Any, List

import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    CLIPProcessor,
    CLIPModel,
    pipeline
)
from torch.utils.data import Dataset

# DB
from document_processing_db import (
    init_db,
    insert_classification_result,
    load_feedback_from_db,
    DB_FILENAME, CANDIDATE_LABELS, ClassificationResult, LABEL2CATEGORY, labels
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# KEY RECOMMENDATION: Dynamically detect device
# -------------------------------------------------------------------
device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
logger.info(f"Using device: {device}")



def extract_image_from_file_path(file_path: str) -> Image.Image:
    """Open an image file and return a PIL Image."""
    return Image.open(file_path)


class ClassificationError(Exception):
    """Custom Exception raised when classification fails."""
    pass


class DocumentClassifier:
    """
    Document classifier that uses extracted text (optionally including filename as context)
    to compute scores using:
      - A zero-shot text classification pipeline.
      - CLIP text encoder similarity.
    The scores are combined (weighted) to determine the final predicted label.
    """

    def __init__(self,
                 model_name: str = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
                 clip_model_name: str = "openai/clip-vit-base-patch32",
                 text_weight: float = 0.5,
                 image_weight: float = 0.5):
        self.device = device
        self.text_weight = text_weight
        self.image_weight = image_weight

        logger.info(f"Loading text model '{model_name}' for zero-shot classification...")
        text_model = AutoModelForSequenceClassification.from_pretrained(model_name)
        text_tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.text_classifier = pipeline(
            "zero-shot-classification",
            model=text_model,
            tokenizer=text_tokenizer,
            device=0 if self.device == "cuda" else -1,
            framework="pt"
        )

        logger.info("Loading CLIP model for text embedding similarity...")
        self.clip_model = CLIPModel.from_pretrained(clip_model_name)
        self.clip_processor = CLIPProcessor.from_pretrained(clip_model_name)
        self.clip_model.to(self.device)

        logger.info("Pre-computing CLIP text embeddings for candidate labels...")
        self.clip_label_embeddings = self._encode_label_prompts(CANDIDATE_LABELS)

    def _encode_label_prompts(self, labels: List[str]) -> torch.Tensor:
        """Encode candidate labels as prompts using CLIP's text encoder."""
        prompts = [f"This document is about {lbl}." for lbl in labels]
        inputs = self.clip_processor(
            text=prompts,
            images=None,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=77
        )
        for k, v in inputs.items():
            inputs[k] = v.to(self.device)
        with torch.no_grad():
            text_outputs = self.clip_model.get_text_features(**inputs)
            text_outputs = text_outputs / text_outputs.norm(dim=-1, keepdim=True)
        return text_outputs

    def _compute_clip_text_scores(self, text: str) -> torch.Tensor:
        """Compute similarity scores for input text using CLIP's text encoder."""
        try:
            inputs = self.clip_processor(
                text=[text],
                images=None,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77
            )
            for k, v in inputs.items():
                inputs[k] = v.to(self.device)
            with torch.no_grad():
                text_emb = self.clip_model.get_text_features(**inputs)
                text_emb = text_emb / text_emb.norm(dim=-1, keepdim=True)
            scores = text_emb @ self.clip_label_embeddings.T
            probs = torch.softmax(scores, dim=-1).squeeze(0)
            return probs
        except Exception as e:
            logger.warning(f"CLIP text scoring failed: {e}")
            return torch.zeros(len(CANDIDATE_LABELS), device=self.device)

    def _compute_text_scores(self, text: str) -> torch.Tensor:
        """
        Compute combined text scores by blending:
          - Zero-shot text classification scores.
          - CLIP text similarity scores.
        """
        try:
            result = self.text_classifier(
                text,
                candidate_labels=CANDIDATE_LABELS,
                multi_label=False
            )
            label2score = dict(zip(result["labels"], result["scores"]))
            zs_scores = torch.tensor([label2score.get(lbl, 0.0) for lbl in CANDIDATE_LABELS], device=self.device)
        except Exception as e:
            logger.warning(f"Zero-shot classification failed: {e}")
            zs_scores = torch.zeros(len(CANDIDATE_LABELS), device=self.device)

        clip_scores = self._compute_clip_text_scores(text)
        weight = 0.5  # Adjust to change the balance between the two scores
        combined_scores = weight * zs_scores + (1 - weight) * clip_scores
        return combined_scores

    def _compute_image_scores(self, image: Image.Image) -> torch.Tensor:
        """Compute similarity scores between the image and candidate labels using CLIP."""
        try:
            inputs = self.clip_processor(images=image, return_tensors="pt")
            for k, v in inputs.items():
                inputs[k] = v.to(self.device)
            with torch.no_grad():
                image_emb = self.clip_model.get_image_features(**inputs)
                image_emb = image_emb / image_emb.norm(dim=-1, keepdim=True)
            scores = image_emb @ self.clip_label_embeddings.T
            probs = torch.softmax(scores, dim=-1).squeeze(0)
            return probs
        except Exception as e:
            logger.warning(f"Image scoring with CLIP failed: {e}")
            return torch.zeros(len(CANDIDATE_LABELS), device=self.device)

    def _classify_multimodal(self, text: str, image: Optional[Image.Image]) -> Dict[str, Any]:
        """Combine text and image scores to rank candidate labels."""
        if not text.strip():
            logger.warning("No text extracted; using fallback text.")
            text = "Document with no readable text."
        text_scores = self._compute_text_scores(text)
        image_scores = self._compute_image_scores(image) if image else torch.zeros(len(CANDIDATE_LABELS), device=self.device)
        combined = self.text_weight * text_scores + self.image_weight * image_scores
        sorted_indices = torch.argsort(combined, descending=True)
        final_labels = [CANDIDATE_LABELS[i] for i in sorted_indices.tolist()]
        final_scores = combined[sorted_indices].tolist()
        return {"labels": final_labels, "scores": final_scores}

    async def classify_document(
            self,
            file_path: Optional[str] = None,
            file_bytes: Optional[bytes] = None,
            file_name: Optional[str] = None,
            text: Optional[str] = None,
            dpi: int = 200,
            max_pages: Optional[int] = 1,
    ) -> ClassificationResult:
        """
        Extract document text (and optionally an image via OCR) then classify it.
        """
        try:
            file_name = os.path.basename(file_path) if file_path else (file_name or "uploaded_file")
            extracted_text = text or ""
            images: List[Image.Image] = []
            page_count = 0

            if file_bytes is not None:
                if file_bytes.startswith(b"%PDF"):
                    try:
                        reader = PdfReader(io.BytesIO(file_bytes))
                        pages_text = [page.extract_text() or "" for page in reader.pages]
                        pdf_text = "\n".join(pages_text)
                        if pdf_text.strip():
                            extracted_text = pdf_text if not extracted_text else f"{extracted_text}\n{pdf_text}"
                    except Exception as e:
                        logger.warning(f"PDF text extraction failed: {e}")
                    try:
                        pdf_pages = convert_from_bytes(file_bytes, dpi=dpi)
                        if max_pages is not None:
                            pdf_pages = pdf_pages[:max_pages]
                        images = pdf_pages
                        page_count = len(pdf_pages)
                    except Exception as e:
                        logger.warning(f"PDF->Image conversion failed: {e}")
                else:
                    try:
                        image = Image.open(io.BytesIO(file_bytes))
                        ocr_text = pytesseract.image_to_string(image, lang='heb')
                        if ocr_text.strip():
                            extracted_text = (extracted_text + "\n" + ocr_text) if extracted_text else ocr_text
                        images = [image]
                        page_count = 1
                    except Exception as e:
                        raise ClassificationError(f"Failed to process image bytes: {e}")
            elif file_path is not None:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                if file_path.lower().endswith(".pdf"):
                    try:
                        pdf_text = extract_text_from_pdf(file_path)
                        if pdf_text.strip():
                            extracted_text = (extracted_text + "\n" + pdf_text) if extracted_text else pdf_text
                    except Exception as e:
                        logger.warning(f"PDF text extraction fallback: {e}")
                    try:
                        pdf_pages = convert_pdf_to_images(file_path, dpi, max_pages)
                        images = pdf_pages
                        page_count = len(pdf_pages)
                    except Exception as e:
                        logger.warning(f"PDF->Image conversion failed: {e}")
                else:
                    try:
                        image = extract_image_from_file_path(file_path)
                        ocr_text = pytesseract.image_to_string(image, lang='heb')
                        if ocr_text.strip():
                            extracted_text = (extracted_text + "\n" + ocr_text) if extracted_text else ocr_text
                        images = [image]
                        page_count = 1
                    except Exception as e:
                        raise ClassificationError(f"Failed to process image file: {e}")
            else:
                raise ClassificationError("No file path or file bytes provided.")

            # Optionally, append the filename as additional context.
            combined_text = extracted_text + "\nFilename: " + file_name

            main_image = images[0] if images else None
            result_dict = await asyncio.to_thread(self._classify_multimodal, combined_text, main_image)
            top_label = result_dict["labels"][0]
            top_score = result_dict["scores"][0]
            category_code = LABEL2CATEGORY.get(top_label, labels["ERROR"]["code"])
            reasons = f"Document classification => '{top_label}' (score={top_score:.2f})."
            return ClassificationResult(
                category=category_code,
                confidence=top_score,
                reasons=reasons,
                page_count=page_count,
                file_name=file_name
            )
        except (FileNotFoundError, ClassificationError) as e:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during classification: {e}", exc_info=True)
            raise ClassificationError(f"Document classification failed: {str(e)}")


# -------------------------------------------------------------------
# HUMAN FEEDBACK & TRAINING FUNCTIONS (DB-based only)
# -------------------------------------------------------------------
def collect_human_feedback(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    feedback_results = []
    for entry in results:
        corrected = entry.get("correct_category", "").strip()
        if corrected:
            entry["category"]["id"] = corrected
            entry["category"]["name"] = corrected
        feedback_results.append(entry)
    return feedback_results


class FeedbackDataset(Dataset):
    def __init__(self, feedback_data: List[Dict[str, Any]], tokenizer, max_length: int = 512):
        self.data = feedback_data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item.get("reasons", "")
        inputs = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt"
        )
        label_id = int(item["category"]["id"])
        inputs = {k: v.squeeze(0) for k, v in inputs.items()}
        inputs["labels"] = torch.tensor(label_id, dtype=torch.long)
        return inputs


def train_model_from_db(db_path: str = DB_FILENAME,
                        output_model_dir: str = "fine_tuned_model",
                        model_name: str = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"):
    feedback_data = load_feedback_from_db(db_path)
    if not feedback_data:
        return "No data found for training."
    num_labels = len(labels)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    dataset = FeedbackDataset(feedback_data, tokenizer)
    training_args = TrainingArguments(
        output_dir=output_model_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=5e-5,
        logging_steps=10,
        save_steps=50,
        evaluation_strategy="no",
        disable_tqdm=False,
        push_to_hub=False
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset
    )
    trainer.train()
    trainer.save_model(output_model_dir)
    return f"DB-based model fine-tuned and saved to {output_model_dir}"


# -------------------------------------------------------------------
# MAIN FLOW
# -------------------------------------------------------------------
async def process_files():
    """
    Processes files from a directory, classifies them using DocumentClassifier,
    inserts the results into the DB, and visualizes outcomes.
    """
    init_db()
    classifier = DocumentClassifier(
        model_name="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
    )
    base_dir = "./monday_assets"  # Adjust as needed
    for root, _, files in os.walk(base_dir):
        for f_name in files:
            file_path = os.path.join(root, f_name)
            print(f"\nProcessing file: {file_path}")
            try:
                result = await classifier.classify_document(file_path=file_path, max_pages=1)
                result_dict = result.to_dict()
                insert_classification_result(result_dict, result.reasons)
                print(f"Category  : {result_dict['category_name']}")
                print(f"Confidence: {result_dict['confidence']:.2f}")
                print(f"Pages     : {result_dict['metadata']['page_count']}")
            except Exception as e:
                print(f"Error processing '{file_path}': {e}")


def human_feedback_loop():
    """
    Simulates a human feedback loop:
      - Classifies documents.
      - Retrieves feedback from the DB.
      - Fine-tunes the model using the feedback.
    """
    print("Retraining from DB feedback...")
    msg = train_model_from_db()
    print(msg)
    print("You can now re-classify with the newly trained model if desired.")


# -------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------
i = 0


def get_filesize(filepath):
    """
    Returns the size of the file at the given filepath in bytes.
    If the file does not exist or an error occurs, returns None.
    """
    try:
        return os.path.getsize(filepath)
    except OSError as e:
        print(f"Error accessing file: {e}")
        return None


def bytes_to_mb(byte_value):
    """
    Convert a given number of bytes to megabytes (MB).

    Args:
        byte_value (int or float): The size in bytes.

    Returns:
        float: The size converted to megabytes.
    """
    MB_FACTOR = 1024 * 1024  # 1,048,576 bytes in 1 MB
    return byte_value / MB_FACTOR


def average_files_per_month(data):
    """
    Calculates the average number of files uploaded per month.

    Parameters:
        data (list): A list of records (dictionaries). Each record is expected to have
                     a "column_values" key containing a list of columns. The column with the id "files__1"
                     should have a "value" key that is a JSON string representing file upload information,
                     for example:

                     '{"files": [{"name": "file.pdf", "assetId": 12345, "isImage": "false",
                                  "fileType": "ASSET", "createdAt": 1734946539896, "createdBy": "68720225"}]}'

    Returns:
        float: The average number of files uploaded per distinct (year, month) combination.
               Returns 0 if no file information is found.
    """
    # Dictionary to count files per (year, month)
    month_counts = defaultdict(int)
    total_files = 0

    for record in data:
        column_values = record.get("column_values", [])
        for col in column_values:
            # Look for the column with id "files__1"
            column_info = col.get("column", {})
            if 'file' not in column_info.get("id"):
                continue
            value_str = col.get("value")
            if not value_str:
                continue
            try:
                file_info = json.loads(value_str)
            except json.JSONDecodeError:
                continue
            files = file_info.get("files", [])
            for file_item in files:
                created_at = file_item.get("createdAt")
                if created_at is None:
                    continue
                # Convert the timestamp (assumed to be in milliseconds) to a datetime object
                dt = datetime.fromtimestamp(created_at / 1000)
                key = (dt.year, dt.month)
                month_counts[key] += 1
                total_files += 1

    if not month_counts:
        return 0

    # Calculate average = total files / number of distinct (year, month) groups
    average = total_files / len(month_counts)
    return average


