import os
import logging
import json
import re
from typing import Optional, Dict, Any, Union, List, Tuple

import ollama  # Use the Ollama Python library instead of requests
from pytesseract import pytesseract

from features.docs_processing.utils import extract_text_from_pdf, convert_pdf_to_images

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


###############################################
# Ollama Classification Functions
###############################################

def classify_with_ollama(document_text: str, filename: str, filebytes: Optional[bytes], candidate_labels: List[str]) -> str:
    """
    Use Ollama's Python library to classify document text.

    This function builds a prompt that instructs the model to select the most appropriate
    category from a list of candidate labels. The prompt instructs the model to return
    **valid JSON only** in the following format:

      {
        "category": "<category label>",
        "confidence": <confidence score as float>,
        "notes": "any additional information if needed"
      }

    Parameters:
      - document_text: The text to classify.
      - filename: The file name.
      - filebytes: The file bytes (if any) for additional context.
      - candidate_labels: A list of candidate category labels.

    Returns:
      A raw JSON string returned by Ollama.
    """
    prompt = (
            "You are a document classifier. Given the following extracted document text, "
            "select the most appropriate category from the list below and provide a confidence score (0 to 1). "
            "Return your answer in **JSON only** using the following format:\n\n"
            "{\n"
            '  "category": "<category label>",\n'
            '  "confidence": 0.0,\n'
            '  "notes": "any additional information if needed"\n'
            "}\n\n"
            "No additional text or explanation. Only output valid JSON.\n\n"
            "Candidate Categories:\n" +
            "\n".join(f"- {label}" for label in candidate_labels) +
            "\n\nDocument Text:\n" +
            document_text[:500] +
            "\n"
    )

    full_prompt = prompt

    try:
        # Use the Ollama Python library's chat function.
        response = ollama.chat(
            options={
                'temperature': .3
            },
            model="llama3.2:3b",  # Replace with your desired model name if needed.
            messages=[{'role': 'user', 'content': full_prompt}]
        )
        # Expect the response content to be in the 'message' field.
        print(full_prompt)
        print(response['message']['content'])
        return response['message']['content']
    except Exception as e:
        logger.error("Error calling Ollama API: %s", e)
        raise e


def parse_ollama_response(response_text: str) -> Tuple[str, float, str]:
    """
    Parse the Ollama response (expected to be valid JSON) to extract:
      - category label,
      - confidence score,
      - and any notes.

    Expected response format:
      {
        "category": "<string>",
        "confidence": <float>,
        "notes": "<string>"
      }

    Returns:
      A tuple (category_label, confidence, full_json_response).
      If parsing fails, returns ("Unknown", 0.0, "{}").
    """
    try:
        logger.info("Ollama response text: %s", response_text)
        data = json.loads(response_text)
        category = data.get("category", "Unknown")
        confidence = float(data.get("confidence", 0.0))
        return category, confidence, response_text
    except Exception as e:
        logger.error("Error parsing Ollama response as JSON: %s", e)
        return "Unknown", 0.0, "{}"


###############################################
# Main Document Classification Function
###############################################

def classify_document_ollama(
        labels: Dict[str, Dict[str, Union[int, str]]],
        filename: Optional[str] = None,
        text: Optional[str] = None,
        filepath: Optional[str] = None
) -> Dict[str, Any]:
    """
    Classify a document using Ollama based on one of the following inputs:
      1. Directly provided text,
      2. A file path from which text can be extracted,
      3. Or a filename string used as fallback text.

    At least one of 'text', 'filepath', or 'filename' must be provided.

    Returns a dictionary containing:
      - "filename": Provided filename.
      - "source": Which parameter contributed the text.
      - "used_text": The text that was sent for classification.
      - "predicted_label": The category label returned by Ollama.
      - "category_info": The corresponding label details from the labels dict (or "ERROR" if not found).
      - "confidence": The confidence score from Ollama.
      - "ollama_response": The raw JSON response from Ollama.
    """
    used_text = ""
    source_label = ""

    # 1. Decide which text to classify
    if text and text.strip():
        used_text += f"\n[From text parameter]\n{text}\n"
        source_label = "text parameter"

    file_bytes = None
    if filepath:
        try:
            if filename and (filename.endswith('.pdf') or filename.startswith('pdf')):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                pdf_text = extract_text_from_pdf(filepath)
                if not pdf_text:
                    return None
                    pdf_pages_img = convert_pdf_to_images(filepath, 600)
                    for image in pdf_pages_img:
                        pdf_text += pytesseract.image_to_string(image, lang='heb')
                used_text += f"\n[Extracted PDF from {filepath}]\n{pdf_text}\n"
                source_label = f"PDF file: {filepath}"
            elif filename and (filename.lower().endswith("png") or filename.lower().endswith("jpg") or filename.lower().endswith("jpeg")):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                # Add OCR logic here if needed.
                source_label = f"Image file: {filepath}"
        except Exception as e:
            logger.error(f"Error reading file '{filepath}': {e}")
            raise e

    if filename and filename.strip():
        used_text += f"\n[Filename parameter]\n{filename}\n"
        if not source_label:
            source_label = "filename parameter"

    if not used_text.strip():
        raise ValueError(f"No text extracted from {source_label} for classification.")

    candidate_labels = [f'{label} - {v['hebrew']}' for label, v in labels.items()]

    # 2. Call Ollama classification using the Python library.
    ollama_response_text = classify_with_ollama(used_text, filename, file_bytes, candidate_labels)

    # 3. Parse the response.
    category_label, confidence, full_response = parse_ollama_response(ollama_response_text)

    # 4. Map returned label to labels dict; default to "ERROR" if not found.
    category_info = labels.get(category_label, labels.get("ERROR"))

    return {
        "filename": filename,
        "source": source_label,
        "used_text": used_text,
        "predicted_label": category_label,
        "category_info": category_info,
        "confidence": confidence,
        "ollama_response": full_response,
    }
