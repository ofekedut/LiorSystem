import os
import boto3
import json
import io
import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from pydantic import BaseModel
from collections import defaultdict
from datetime import datetime

from PyPDF2 import PdfReader
CANDIDATE_LABELS = ['תעודת זהות', 'רשיון נהיגה', 'דרכון', 'מסמך אחר']
LABEL2CATEGORY = {}

class ClassificationResult(BaseModel):
    label: str
    score: float
from server.features.docs_processing.utils import extract_text_from_pdf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

###############################################
# AWS Bedrock Classification Functions
###############################################

import string
import re


def fix_filename(filename):
    # Step 1: Filter to keep only allowed characters
    allowed_chars = set(string.ascii_letters + string.digits + '-()[]' + string.whitespace)
    filtered = ''.join(char for char in filename if char in allowed_chars)

    # Step 2: Replace any sequence of whitespace characters with a single space
    fixed = re.sub(r'\s+', ' ', filtered)

    return fixed
    
def classify_with_bedrock(document_text: str, filename: str, filebytes: bytes, candidate_labels: List[str]) -> Tuple[str, Dict]:
    """
    Use AWS Bedrock's model invocation to classify document text.

    The function sends a prompt containing the extracted document text and a list of candidate labels.
    The model is expected to return valid JSON using tools, in the following format:

      {
        "category": "<category label>",
        "confidence": <confidence score as float>,
        "notes": "optional notes or additional info if needed"
      }

    Parameters:
      - document_text: The text to classify.
      - filename: The filename.
      - filebytes: The raw file bytes.
      - candidate_labels: A list of candidate category labels.

    Returns:
      A tuple of (response_text, usage_info) from AWS Bedrock.
    """
    # Print the filename we're classifying for easier troubleshooting
    print(f"\n============= CLASSIFYING DOCUMENT: {filename} =============\n")
    
    # Build the tool schema for document classification
    tools = {
        'tools': [
            {
                'toolSpec': {
                    'name': 'classify_document',
                    'description': 'Classify the document into one of the provided categories',
                    'inputSchema': {
                        'json': {
                            'type': 'object',
                            'properties': {
                                'document': {
                                    'type': 'string',
                                    'description': 'The document to be classified'
                                },
                                'categories': {
                                    'type': 'array',
                                    'items': {'type': 'string'},
                                    'description': 'List of possible categories for classification'
                                }
                            },
                            'required': ['document', 'categories']
                        }
                    }
                }
            }
        ]
    }
    prompt = (
            "You are a document classifier. Given the following extracted document text, "
            "select the most appropriate category from the list below and provide a confidence score (0 to 1). "
            "Use the classify_document tool to return your answer as structured data.\n\n"
            "Candidate Categories:\n" +
            "\n".join(f"- {label}" for label in candidate_labels) +
            "\n\nDocument Text:\n" +
            document_text +
            "\n"
    )
    doc_part = None
    if filebytes.startswith(b'%PDF'):
        doc_part = {
            'document': {"format": 'pdf', "source": {'bytes': filebytes, }, "name": fix_filename(filename.replace('.pdf', ''))}
        }
    elif filebytes.startswith(b'\x89PNG'):
        doc_part = {
            'image': {"format": 'png', "sourc e": {'bytes': filebytes, }}
        }
    
    # Set up the tools configuration

    payload = {
        'system': [
            {'text': """אתה מומחה בסיווג מסמכים פיננסיים ומשפטיים. נתח את תוכן הטקסט וסווג אותו לאחת מהקטגוריות הבאות:

<document_categories>
{doc_categories}
</document_categories>

הנחיות:
1. קרא את כל הטקסט בקפידה - גם פרטים קטנים חשובים
2. שקול את מטרת המסמך, הפורמט והישויות המרכזיות
3. החזר רק את ערך הקטגוריה מהרשימה
4. אם אינך בטוח, החזר 'other' עם רמת ביטחון 0.0
5. רמת הביטחון חייבת להיות בין 0.0 ל-1.0

פורמט תשובה:
{{
  "document_type": "category_value",
  "confidence": 0.95,
  "text_source": "first_50_chars" 
}}"""}
        ],
        "messages": [
            {"role": "user", "content": [{'text': prompt}, *([doc_part] if doc_part else [])]}
        ],
        'inferenceConfig': {
            "maxTokens": 4096,
            "temperature": 0.1,  # Lower temperature for more predictable outputs
            "stopSequences": [],
            "topP": 1,
        },
        'toolConfig': tools,
        'modelId': "amazon.nova-lite-v1:0",
    }

    try:
        # Log detailed request information
        logger.info(f"AWS Bedrock Request (Nova Lite):")
        logger.info(f"Model ID: {payload['modelId']}")
        logger.info(f"Max Tokens: {payload['inferenceConfig']['maxTokens']}")
        logger.info(f"Temperature: {payload['inferenceConfig']['temperature']}")
        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.info(f"Document format: {'PDF' if filebytes.startswith(b'%PDF') else 'PNG' if filebytes.startswith(b'\x89PNG') else 'text'}")
        logger.info(f"Tools provided: {json.dumps(tools)}")
        
        # Print to console for immediate visibility
        print(f"\n============= SENDING REQUEST TO AWS BEDROCK (NOVA LITE) =============\n")
        print(f"Model: {payload['modelId']}")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Document format: {'PDF' if filebytes.startswith(b'%PDF') else 'PNG' if filebytes.startswith(b'\x89PNG') else 'text'}")
        print(f"Using tools for structured response")
        
        # Create the client and send the request
        client = boto3.client("bedrock-runtime", region_name='us-east-1')
        
        logger.info("Sending request to AWS Bedrock (Nova Lite)...")
        response = client.converse(**payload)
        
        # Log response information
        logger.info(f"AWS Bedrock (Nova Lite) Response received:")
        logger.info(f"Usage information: {response['usage']}")
        
        print(f"\n============= RECEIVED RESPONSE FROM AWS BEDROCK (NOVA LITE) =============\n")
        print(f"Usage: {response['usage']}")
        
        # Check for tool calls in the response
        tool_result = None
        for block in response['output']['message']['content']:
            # Log full response content
            logger.info(f"Response block type: {block.get('type', 'unknown')}")
            logger.info(f"Response content: {json.dumps(block, ensure_ascii=False)}")
            
            # Print response for debugging
            print(json.dumps(block, indent=2, ensure_ascii=False))
            
            # If this is a tool call, extract the result
            if block.get('toolUse') :
                tool_name = block['toolUse'].get('name')
                tool_input = block['toolUse'].get('input', {})
                logger.info(f"Tool used: {tool_name}")
                logger.info(f"Tool input: {json.dumps(tool_input, ensure_ascii=False)}")
                
                print(f"\nTool used: {tool_name}")
                print(f"Tool input: {json.dumps(tool_input, indent=2, ensure_ascii=False)}")
                
                # For Claude API, all tool outputs are processed the same way
                tool_result = json.dumps(tool_input)
                return tool_result, response['usage']
        
        # If no tool call was found, return the text from the first content block
        if tool_result is None:
            for block in response['output']['message']['content']:
                if block.get('text'):
                    return block['text'], response['usage']
            
            # If we got here, we didn't find any usable content
            return '{"category": "ERROR", "confidence": 0.0, "notes": "No valid response from model"}', response['usage']
    except Exception as e:
        logger.error(f"Error calling AWS Bedrock API (Nova Lite): {e}")
        print(f"\n\u274c AWS BEDROCK (NOVA LITE) ERROR: {e}\n")
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
        logger.info("Bedrock response text: %s", response_text)
        print(f"\nAttempting to parse JSON: {response_text}\n")
        
        # First try to parse it directly
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from markdown code blocks
            if "```json" in response_text:
                logger.info("Extracting JSON from markdown code block")
                json_text = response_text.split("```json")[1].split("```")[0].strip()
                data = json.loads(json_text)
            elif "```" in response_text:
                logger.info("Extracting content from generic code block")
                json_text = response_text.split("```")[1].split("```")[0].strip()
                data = json.loads(json_text)
            else:
                raise
        
        logger.info(f"Successfully parsed JSON result: {data}")
        print(f"Successfully parsed JSON result: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        category = data.get("category", "Unknown")
        confidence = float(data.get("confidence", 0.0))
        
        # Ensure the confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))
        
        # Return the original response_text for detailed logging
        return category, confidence, json.dumps(data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Bedrock response: {e}")
        print(f"\n❌ JSON PARSING ERROR: {e}\n")
        return "Unknown", 0.0, "{}"
    except Exception as e:
        logger.error(f"Error parsing Bedrock response: {e}")
        print(f"\n❌ ERROR PARSING RESPONSE: {e}\n")
        return "Unknown", 0.0, "{}"


class ClassificationError(Exception):
    """Custom Exception raised when classification fails."""
    pass


async def classify_document(
        labels: Dict[str, Dict[str, Union[int, str]]],
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        filebytes: Optional[bytes] = None,
        text: Optional[str] = None
) -> Dict[str, Any]:
    logger.info(f"Starting document classification process")
    logger.info(f"Input parameters: filename={filename}, filepath={filepath}, text_provided={'Yes' if text else 'No'}, filebytes_provided={'Yes' if filebytes else 'No'}")
    """
    Classify a document using AWS Bedrock based on one of the following inputs:
      1. Directly provided text,
      2. A file path from which text can be extracted,
      3. Or a filename string used as the text.

    At least one of 'text', 'filepath', 'filebytes', or 'filename' must be provided.

    Parameters:
        labels: A dictionary of label definitions, where keys are category labels.
        filename: An optional string representing the file name.
        filepath: An optional file path from which to extract document text.
        filebytes: Optional raw file bytes.
        text: Optional text content.

    Returns:
        A dictionary containing classification results.
    """
    try:
        # Track which source of text was used last
        source_used = "none"
        used_text = ""
        
        # Get the filename from filepath if not provided directly
        if not filename and filepath:
            filename = os.path.basename(filepath)
            logger.info(f"Extracted filename from filepath: {filename}")
            
            # Try to open the file for manual review
            if os.path.exists(filepath):
                try:
                    logger.info(f"Opening file for manual review: {filepath}")
                    os.system(f'open "{filepath}"')
                    print(f"\n📂 Opening file for review: {filepath}\n")
                except Exception as e:
                    logger.warning(f"Failed to open file for review: {e}")
        
        # Fallback filename
        if not filename:
            filename = "unknown_document"
        
        # Extract text from the file if available and no text was provided
        if text:
            used_text = text
            source_used = "text"
            logger.info(f"Using provided text, length: {len(text)} characters")
            print(f"\nUsing provided text, length: {len(text)} characters\n")
        
        # If we have file bytes, try to extract text
        if filebytes and not used_text:
            # Try extracting text from PDF
            if filebytes.startswith(b'%PDF'):
                try:
                    logger.info("Detected PDF from file bytes, attempting to extract text")
                    reader = PdfReader(io.BytesIO(filebytes))
                    extracted_text = ""
                    pages_with_text = 0
                    total_pages = len(reader.pages)
                    
                    logger.info(f"PDF has {total_pages} pages")
                    print(f"\n📄 PDF has {total_pages} pages\n")
                    
                    for i, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                extracted_text += page_text + "\n"
                                pages_with_text += 1
                                print(f"Extracted text from page {i+1}: {len(page_text)} characters")
                        except Exception as e:
                            logger.warning(f"Failed to extract text from page {i+1}: {e}")
                            print(f"Failed to extract text from page {i+1}: {e}")
                    
                    logger.info(f"Successfully extracted text from {pages_with_text}/{total_pages} pages")
                    
                    if extracted_text.strip():
                        used_text = extracted_text
                        source_used = "filebytes (PDF text)"
                        logger.info(f"Using extracted PDF text, length: {len(used_text)} characters")
                    else:
                        logger.warning("No text was extracted from PDF bytes")
                except Exception as e:
                    logger.warning(f"Error extracting text from PDF bytes: {e}", exc_info=True)
        
        # If we have a filepath and no text yet, try extracting from the file
        if filepath and not used_text:
            logger.info(f"Attempting to extract text from file at path: {filepath}")
            if os.path.exists(filepath):
                filesize = os.path.getsize(filepath)
                logger.info(f"File exists, size: {filesize} bytes ({bytes_to_mb(filesize):.2f} MB)")
                
                if filepath.lower().endswith(".pdf"):
                    try:
                        logger.info("Extracting text from PDF file")
                        pdf_text = extract_text_from_pdf(filepath)
                        if pdf_text.strip():
                            used_text = pdf_text
                            source_used = "filepath (PDF)"
                            logger.info(f"Successfully extracted text from PDF, length: {len(used_text)} characters")
                        else:
                            logger.warning("No text was extracted from PDF file")
                    except Exception as e:
                        logger.warning(f"Error extracting text from PDF file: {e}", exc_info=True)
                else:
                    logger.info(f"File is not a PDF, extension: {os.path.splitext(filepath)[1]}")
            else:
                logger.warning(f"File not found: {filepath}")
        
        # If still no text, use the filename as a last resort
        if not used_text:
            used_text = f"Document filename: {filename}"
            source_used = "filename"
            logger.warning("No text extracted from document; using filename as fallback.")
        
        # Get the file bytes for sending to Bedrock if not already provided
        if not filebytes and filepath and os.path.exists(filepath):
            logger.info(f"Reading file bytes from {filepath}")
            try:
                with open(filepath, 'rb') as f:
                    filebytes = f.read()
                logger.info(f"Successfully read file bytes, size: {len(filebytes)} bytes")
                print(f"\nRead file bytes: {len(filebytes)} bytes ({len(filebytes)/1024/1024:.2f} MB)\n")
            except Exception as e:
                logger.error(f"Error reading file bytes: {e}")
                print(f"\n❌ Error reading file: {e}\n")
        
        # If we don't have file bytes, create an empty bytes object
        if not filebytes:
            filebytes = b''
        
        # Call AWS Bedrock for classification
        logger.info(f"Sending document to AWS Bedrock for classification")
        logger.info(f"Text source: {source_used}, Text preview: {used_text[:100]}...")
        logger.info(f"Using {len(labels)} candidate labels for classification")
        
        # Print information to console for easier debugging
        print(f"\nDocument text source: {source_used}")
        print(f"Text preview: {used_text[:200]}...")
        print(f"Candidate labels: {list(labels.keys())}\n")
        
        response_text, usage_info = classify_with_bedrock(
            document_text=used_text,
            filename=filename,
            filebytes=filebytes,
            candidate_labels=list(labels.keys())
        )
        
        logger.info(f"Received response from AWS Bedrock")
        
        # Parse the response
        logger.info(f"Parsing Bedrock response")
        category_label, confidence, raw_response = parse_bedrock_response(response_text)
        logger.info(f"Parsed result: category={category_label}, confidence={confidence:.4f}")
        
        # Print results for debugging
        print(f"\n============= CLASSIFICATION RESULT =============\n")
        print(f"Category: {category_label}")
        print(f"Confidence: {confidence:.4f}")
        print(f"Raw response: {raw_response}\n")
        
        # Get the corresponding category info from labels dict
        if category_label in labels:
            category_info = labels[category_label]
            category_code = category_info.get("code", -1)
            logger.info(f"Found matching category in labels: {category_label}, code={category_code}")
        else:
            # Fallback to ERROR if the category is not found
            category_info = labels.get("ERROR", {"code": -1, "label": "Error"})
            category_code = category_info.get("code", -1)
            logger.warning(f"Category {category_label} not found in available labels. Using fallback.")
        
        result = {
            "filename": filename,
            "source": source_used,
            "used_text": used_text[:500] + ("..." if len(used_text) > 500 else ""),  # Truncate for readability
            "predicted_label": category_label,
            "category_info": category_info,
            "category_code": category_code,
            "confidence": confidence,
            "bedrock_response": raw_response,
            "usage_info": usage_info
        }
        
        logger.info(f"Document classification complete: {filename} -> {category_label} (confidence: {confidence:.4f})")
        return result
    
    except Exception as e:
        logger.error(f"Error during document classification: {e}")
        # Return error information
        return {
            "filename": filename or "unknown",
            "source": "error",
            "used_text": "",
            "predicted_label": "ERROR",
            "category_info": labels.get("ERROR", {"code": -1, "label": "Error"}),
            "category_code": -1,
            "confidence": 0.0,
            "bedrock_response": "{}",
            "error": str(e)
        }


# -------------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------------

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
