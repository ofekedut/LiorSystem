import os
import logging
import json
import re
import boto3
from typing import Optional, Dict, Any, Union, List, Tuple

from features.docs_processing.document_processing_db import CANDIDATE_LABELS
from features.docs_processing.utils import extract_text_from_pdf

# Configure logging if needed
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


###############################################
# AWS Bedrock Classification Functions
###############################################

def classify_with_bedrock(document_text: str, filename, filebytes, candidate_labels: List[str]) -> dict:
    """
    Use AWS Bedrock's model invocation to classify document text.

    The function sends a prompt containing the extracted document text and a list of candidate labels.
    The model is expected to return **valid JSON only** in the following format:

      {
        "category": "<category label>",
        "confidence": <confidence score as float>,
        "notes": "optional notes or additional info if needed"
      }

    Parameters:
      - document_text: The text to classify.
      - candidate_labels: A list of candidate category labels.

    Returns:
      A dictionary representing the response from AWS Bedrock (the raw output text).
    """
    # Build the prompt
    prompt = (
            "You are a document classifier. Given the following extracted document text, "
            "select the most appropriate category from the list below and provide a confidence score (0 to 1). "
            "Return your answer in **JSON only** using the following format:\n\n"
            "{\n"
            '  "category": "<category label>",\n'
            '  "confidence": 0.0,\n'
            '  "notes": "any additional information if needed",\n'
            '  "extracted_fields":{'
            '},\n'
            "}\n\n"
            "No additional text or explanation. Only output valid JSON.\n\n"

            "Candidate Categories:\n" +
            "\n".join(f"- {label}" for label in candidate_labels) +
            "\n\nDocument Text:\n" +
            document_text +
            "\n"
    )
    doc_part = None
    if filebytes.startswith(b'%PDF'):
        doc_part = {
            'document': {"format": 'pdf', 'source': {'bytes': filebytes, }, 'name': filename.replace('.pdf', '')},
        }
    if filebytes.startswith(b'\x89PNG'):
        doc_part = {
            'image': {"format": 'png', 'source': {'bytes': filebytes, }},
        }
    payload = {
        'system': [
            {'text':
                 "You are a helpful document classifier."}
        ],
        "messages": [
            {"role": "user", "content": [{'text': prompt}, *([doc_part] if doc_part else [])]}
        ],
        'inferenceConfig': {
            "maxTokens": 4096,
            "temperature": .3
        },
        'modelId': "amazon.nova-lite-v1:0",
    }

    try:
        client = boto3.client("bedrock-runtime", region_name='us-east-1')
        response = client.converse(**payload)
        print(response['usage'])
        for block in response['output']['message']['content']:
            print(json.dumps(block, indent=2, ensure_ascii=False))
            return block['text'], response['usage']
    except Exception as e:
        logger.error("Error calling AWS Bedrock API: %s", e)
        raise e


def call_bedrock(text: str):
    prompt = (
        '''
        You are an assistant that takes a JSON object representing a "case" from Monday.com. The schema for my Postgres `cases` table is:
        
        ```sql
        CREATE TABLE IF NOT EXISTS cases (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          name TEXT NOT NULL CHECK (length(name) > 0),
          status case_status NOT NULL,
          case_purpose text NOT NULL,
          loan_type text not null,
          last_active TIMESTAMP WITH TIME ZONE NOT NULL,
          created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
          updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
        ```
        
        - `id` should be a UUID (in many cases you might generate one if Monday.com doesn’t provide it).
        - `name` is the “name” of the case from Monday.
        - `status` is an enum of type `case_status` (`active`, `inactive`, `pending`). If Monday’s data uses something else (e.g., "לא משתף פעולה"), we have to map it to a valid status (like `inactive`).
        - `case_purpose` can be taken from Monday.com’s “מהות התיק” field (or whichever field best describes the reason/purpose of the case).
        - `loan_type` can be the “סוג הלוואה” from Monday.
        - `last_active` is a timestamp that we can guess from the item’s last update or from the “last_move_date” if present. If that’s missing, we can fallback to `NOW()`.
        - `created_at` and `updated_at` will generally be set by the DB. 
        - If we want to supply them, we can, or just rely on the DB default.  
          
        
        ### Input
        
        A JSON object with the shape:
        
        ```json
        {
            "id": "1762267925",
            "name": "שבתאי צ'אוש",
            "column_values": [...],
            "subitems": [...],
            "case_nature": "גיוס לכל מטרה",
            "loan_type": "סולו",
            "case_status": "לא משתף פעולה",
            "priority": "חלש",
            "main_contact": "שבתאי",
            "phone": "0552822855",
            "national_id": "054737051",
            "item_id": "1762267925",
            "solution_date": "",
            "last_move_date": ""
        }
        ```
        
        ### Your Task
        
        1. **Read** the input JSON and **map** its fields to the `cases` table columns:
           - `id` → you can use the Monday `item_id` or generate a new UUID.
           - `name` → from the JSON `name` (e.g., `"שבתאי צ'אוש"`).
           - `status` → must be one of (`active`, `inactive`, `pending`). If `case_status` is “לא משתף פעולה,” let's map that to `inactive`.
           - `case_purpose` → from `case_nature` (e.g., `"גיוס לכל מטרה"`).
           - `loan_type` → from the JSON `loan_type` field (e.g., `"סולו"`).
           - `last_active` → from `last_move_date` or default to `NOW()` if empty.
        2. **Output** a **Python list** containing a **single dictionary** that can be inserted into the `cases` table. For example:
           ```python
           [
               {
                   "id": "1762267925",
                   "name": "שבתאי צ'אוש",
                   "status": "inactive",
                   "case_purpose": "גיוס לכל מטרה",
                   "loan_type": "סולו",
                   "last_active": "2025-01-07T11:52:54Z"
               }
           ]
           ```
           You may omit `created_at` and `updated_at` if you want the database defaults to be used.
        
        ### Example of the Output
        
        ```json
        [
          {
            "id": "1762267925",
            "name": "שבתאי צ'אוש",
            "status": "inactive",
            "case_purpose": "גיוס לכל מטרה",
            "loan_type": "סולו",
            "last_active": "2025-02-14T16:15:00Z",
          }
        ]```
        
        in you reply, only return the json.
            ''')
    payload = {
        'system': [
            {'text':
                 prompt}
        ],
        "messages": [
            {"role": "user", "content": [{'text': text}]}
        ],
        'inferenceConfig': {
            "maxTokens": 4096,
            "temperature": .3
        },
        'modelId': "amazon.nova-pro-v1:0",
    }

    try:
        client = boto3.client("bedrock-runtime", region_name='us-east-1')
        response = client.converse(**payload)
        print(response['usage'])
        for block in response['output']['message']['content']:
            return block['text'], response['usage']
    except Exception as e:
        logger.error("Error calling AWS Bedrock API: %s", e)
        raise e


def parse_bedrock_response(response_text: str) -> Tuple[str, float, str]:
    """
    Parse the AWS Bedrock response (which should be valid JSON) to extract:
      - category label
      - confidence score
      - any notes or additional information

    Expected response format:
      {
        "category": "<string>",
        "confidence": <float>,
        "notes": "<string>"
      }

    Parameters:
      - response_text: The raw JSON string from AWS Bedrock.

    Returns:
      A tuple of (category_label, confidence, full_json_response).

      If parsing fails, returns ("Unknown", 0.0, "{}").
    """
    try:
        logger.info("Assistant response text: %s", response_text)
        data = json.loads(response_text)  # Attempt to parse the JSON
        category = data.get("category", "Unknown")
        confidence = float(data.get("confidence", 0.0))
        return category, confidence, response_text
    except Exception as e:
        logger.error("Error parsing Bedrock response as JSON: %s", e)
        return "Unknown", 0.0, "{}"


###############################################
# Main Document Classification Function
###############################################

def classify_document(
        labels: Dict[str, Dict[str, Union[int, str]]],
        filename: Optional[str] = None,
        filepath: Optional[str] = None
) -> Dict[str, Any]:
    """
    Classify a document using AWS Bedrock based on one of the following inputs:
      1. Directly provided text,
      2. A file path from which text can be extracted,
      3. Or a filename string used as the text.

    At least one of 'text', 'filepath', or 'filename' must be provided.

    Parameters:
        labels: A dictionary of label definitions, where keys are category labels.
        filename: An optional string representing the file name (used as text if no other text is provided).
        filepath: An optional file path from which to extract document text.

    Returns:
        A dictionary containing:
            - "filename": The provided filename, if any.
            - "source": A description of which parameter contributed the text (last used).
            - "used_text": The text that was sent for classification.
            - "predicted_label": The category label returned by AWS Bedrock.
            - "category_info": The corresponding label details from the labels dict (or the "ERROR" label if not found).
            - "confidence": The confidence score returned by AWS Bedrock.
            - "aws_response": The full raw response from AWS Bedrock (JSON string).
    """
    used_text = ""
    source_label = ""

    # 1. Decide which text to classify
    file_bytes = None
    if filepath:
        try:
            if filename and filename.endswith('pdf') or filename.startswith('pdf'):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                pdf_text = extract_text_from_pdf(filepath)[:1000]
                used_text += f"\n[Extracted PDF from {filepath}]\n{pdf_text}\n"
                source_label = f"PDF file: {filepath}"
            elif filename and (filename.endswith("png") or filename.endswith("jpg") or filename.endswith("jpeg")):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                # You can add your OCR logic here if needed.
                source_label = f"Image file: {filepath}"

        except Exception as e:
            logger.error(f"Error reading file '{filepath}': {e}")
            raise
    used_text = ''
    if filename and filename.strip():
        used_text += f"\n[Filename parameter]\n{filename}\n"
        if not source_label:
            source_label = "filename parameter"

    # 2. Check that we actually have text to classify
    if not used_text.strip():
        raise ValueError(f"No text extracted from {source_label} for classification.")

    # 3. Prepare the list of candidate labels
    candidate_labels = list(labels.keys())

    # 4. Call AWS Bedrock classification (the model should return JSON only)
    bedrock_response_text, usage = classify_with_bedrock(used_text, filename, file_bytes, candidate_labels)

    # 5. Parse the JSON to get the category label and confidence
    category_label, confidence, full_response = parse_bedrock_response(bedrock_response_text)

    # 6. Map the returned label to the provided labels dict; default to "ERROR" if not found.
    category_info = labels.get(category_label, labels.get("ERROR"))

    return {
        "filename": filename,
        "source": source_label,
        "used_text": used_text,
        "predicted_label": category_label,
        "category_info": category_info,
        "confidence": confidence,
        "aws_response": full_response,
    }, usage


classify_with_bedrock('', 'ecb0f2c3', open(
    '/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/subitems/1720652971_דנא__בידיאי/pdf.ecb0f2c3',
    'rb').read(),
                      candidate_labels=CANDIDATE_LABELS)
