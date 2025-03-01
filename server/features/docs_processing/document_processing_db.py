# file: document_processing_db.py

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import uuid

from pydantic import BaseModel, Field

from server.database.database import get_connection

# -------------------------------------------------------------------
# DATABASE FUNCTIONS FOR DOCUMENT CATEGORIES AND TYPES
# -------------------------------------------------------------------

async def get_all_document_types() -> List[Dict[str, Any]]:
    """
    Get all document types from the database
    """
    query = """
    SELECT 
        id, 
        name, 
        value,
        created_at,
        updated_at
    FROM document_types
    ORDER BY name
    """
    
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_document_types() -> List[Dict[str, Any]]:
    """
    Get all document_types from the database (different from documents table)
    """
    query = """
    SELECT 
        id, 
        name, 
        value,
        created_at,
        updated_at
    FROM document_types
    ORDER BY name
    """
    
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_document_type_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a document type by its name"""
    query = """
    SELECT 
        id, 
        name, 
        value,
        created_at,
        updated_at
    FROM document_types
    WHERE name = $1
    """
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, name)
        return dict(row) if row else None
    finally:
        await conn.close()

async def get_document_type_by_value(value: str) -> Optional[Dict[str, Any]]:
    """Get a document type by its value"""
    query = """
    SELECT 
        id, 
        name, 
        value,
        created_at,
        updated_at
    FROM document_types
    WHERE value = $1
    """
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, value)
        return dict(row) if row else None
    finally:
        await conn.close()

async def get_document_type_by_value_from_document_types(value: str) -> Optional[Dict[str, Any]]:
    """Get a document type by its value from document_types table"""
    query = """
    SELECT 
        id, 
        name, 
        value,
        created_at,
        updated_at
    FROM document_types
    WHERE value = $1
    """
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, value)
        return dict(row) if row else None
    finally:
        await conn.close()

async def get_document_categories() -> List[Dict[str, Any]]:
    """Get all document categories from the database"""
    query = """
    SELECT 
        id, 
        name, 
        value,
        created_at,
        updated_at
    FROM document_categories
    ORDER BY name
    """
    
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_document_category_by_value(value: str) -> Optional[Dict[str, Any]]:
    """Get a document category by its value"""
    query = """
    SELECT 
        id, 
        name, 
        value,
        created_at,
        updated_at
    FROM document_categories
    WHERE value = $1
    """
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, value)
        return dict(row) if row else None
    finally:
        await conn.close()

async def get_all_documents() -> List[Dict[str, Any]]:
    """
    Get all documents from the database
    """
    query = """
    SELECT 
        d.id, 
        d.name, 
        d.description,
        d.category,
        d.has_multiple_periods,
        dt.name as document_type_name,
        dt.value as document_type_value
    FROM documents d
    JOIN document_types dt ON d.document_type_id = dt.id
    ORDER BY d.name
    """
    
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def get_labels() -> Dict[str, Dict[str, Any]]:
    """
    Get all documents from the database and format them as labels
    Returns a dictionary of document names mapped to their details
    """
    rows = await get_all_documents()
    
    result = {}
    for i, row in enumerate(rows, start=1):
        # Use the document name as the label key
        key = row['name'].upper().replace(' ', '_')
        result[key] = {
            "code": i,
            "hebrew": row.get('description', row['name']),  # Use description if available, otherwise use name
            "id": str(row['id']),
            "value": row['name'].lower().replace(' ', '_'),
            "document_type": row['document_type_value'],
            "category": row['category']
        }
    
    # Add ERROR category 
    result["ERROR"] = {"code": 999, "hebrew": "שגיאה", "id": None, "value": "error"}
    
    return result

# Cache for document categories
_document_categories = None

async def get_document_category_enum():
    """
    Dynamically create a DocumentCategory Enum class based on database values
    """
    global _document_categories
    
    # Return cached version if available
    if _document_categories is not None:
        return _document_categories
    
    # Fetch documents from the database
    docs = await get_all_document_types()
    
    # Create enum members dictionary
    enum_members = {}
    for i, doc in enumerate(docs, start=1):
        # Use the document name as the enum key (uppercase with underscores)
        key = doc['name'].upper().replace(' ', '_')
        enum_members[key] = i
    
    # Add ERROR category
    enum_members["ERROR"] = 999
    
    # Create the Enum dynamically
    DocumentCategory = Enum('DocumentCategory', enum_members)
    
    # Add from_name method
    def from_name(cls, name: str):
        """
        Attempt to map the category name to a DocumentCategory enum.
        If it fails, returns DocumentCategory.ERROR.
        """
        try:
            return cls[name]
        except (KeyError, ValueError):
            return cls.ERROR
    
    DocumentCategory.from_name = classmethod(from_name)
    
    # Cache the enum
    _document_categories = DocumentCategory
    
    return DocumentCategory


class ClassificationResultModel(BaseModel):
    """Data model for classification results using Pydantic"""
    id: Optional[uuid.UUID] = None
    category_id: int = Field(..., description="Numeric code for the document category")
    category_name: str = Field(..., description="Name of the document category")
    confidence: float = Field(..., description="Confidence score for the classification")
    reasons: str = Field(..., description="Explanation or reasoning behind the prediction")
    page_count: int = Field(..., description="Number of pages processed")
    file_name: str = Field(..., description="Name of the file processed")
    extracted_text: Optional[str] = Field(None, description="The extracted text from the document")
    correct_category: Optional[str] = Field(None, description="Corrected category if manually updated")
    error: Optional[str] = Field(None, description="Any error encountered during processing")
    processed_at: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp when processed")
    
    def to_tuple(self):
        """Return a tuple of values in the order expected by the database."""
        return (
            self.file_name, 
            self.category_id, 
            self.category_name, 
            self.confidence, 
            self.reasons, 
            self.page_count, 
            self.error or None, 
            self.correct_category or None,
            self.extracted_text or None
        )


class ClassificationResult:
    """Simple result container for classifier output"""
    def __init__(self, category: int, confidence: float, reasons: str, page_count: int, file_name: str, error: Optional[str] = None):
        self.category = category
        self.confidence = confidence
        self.reasons = reasons
        self.page_count = page_count
        self.file_name = file_name
        self.error = error
    
    def to_dict(self):
        return {
            "category": self.category,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "page_count": self.page_count,
            "file_name": self.file_name,
            "error": self.error
        }


# -------------------------------------------------------------------
# DATABASE OPERATIONS
# -------------------------------------------------------------------

async def init_db() -> None:
    """
    Initialize the PostgreSQL database.
    Creates the document_processing_results table if it doesn't already exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS document_processing_results (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        file_name TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        confidence REAL NOT NULL,
        reasons TEXT NOT NULL,
        page_count INTEGER NOT NULL,
        error TEXT,
        correct_category TEXT,
        extracted_text TEXT,
        processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """
    
    conn = await get_connection()
    try:
        await conn.execute(create_table_query)
    finally:
        await conn.close()


async def insert_classification_result(result: dict, extracted_text: str) -> uuid.UUID:
    """
    Inserts a classification result into the PostgreSQL database.

    :param result: Dictionary with keys:
        {
            "category": {"id": int, "name": str},
            "confidence": float,
            "reasons": str,
            "metadata": {"page_count": int, "file_name": str},
            "error": str or None,
            "correct_category": str (optional)
        }
    :param extracted_text: Full text extracted from the PDF or image (for training).
    :return: UUID of the inserted record
    """
    # Parse and validate result data
    try:
        category_id = result["category"]["id"]
        category_name = result["category"]["name"]
        confidence = result["confidence"]
        reasons = result["reasons"]
        page_count = result["metadata"]["page_count"]
        file_name = result["metadata"]["file_name"]
        error = result.get("error")
        correct_category = result.get("correct_category")
    except KeyError as e:
        raise ValueError(f"Missing required field in result: {e}")
    
    # SQL query
    query = """
    INSERT INTO document_processing_results 
    (file_name, category_id, category_name, confidence, reasons, page_count, error, correct_category, extracted_text)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    RETURNING id
    """
    
    # Execute query
    conn = await get_connection()
    try:
        result_id = await conn.fetchval(
            query, 
            file_name, 
            category_id, 
            category_name, 
            confidence, 
            reasons, 
            page_count, 
            error, 
            correct_category, 
            extracted_text
        )
        return result_id
    finally:
        await conn.close()


async def get_all_results() -> List[Dict[str, Any]]:
    """
    Fetches all classification results from the PostgreSQL database.
    Returns a list of dictionaries with result data.
    """
    query = """
    SELECT 
        id, 
        file_name, 
        category_id, 
        category_name, 
        confidence, 
        reasons, 
        page_count, 
        error, 
        correct_category, 
        processed_at, 
        extracted_text
    FROM document_processing_results
    ORDER BY processed_at DESC
    """
    
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_result_by_filename(filename: str) -> Optional[Dict[str, Any]]:
    """
    Fetches classification result for a specific filename from the PostgreSQL database.
    Returns a dictionary with result data or None if not found.
    """
    query = """
    SELECT 
        id, 
        file_name, 
        category_id, 
        category_name, 
        confidence, 
        reasons, 
        page_count, 
        error, 
        correct_category, 
        processed_at, 
        extracted_text
    FROM document_processing_results
    WHERE file_name = $1
    ORDER BY processed_at DESC
    LIMIT 1
    """
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, filename)
        return dict(row) if row else None
    finally:
        await conn.close()


async def update_correct_category(record_id: uuid.UUID, correction: str) -> None:
    """
    Updates the 'correct_category' field for the given record in the database.
    """
    query = """
    UPDATE document_processing_results
    SET correct_category = $1
    WHERE id = $2
    """
    
    conn = await get_connection()
    try:
        await conn.execute(query, correction, record_id)
    finally:
        await conn.close()


async def load_feedback_from_db() -> List[Dict[str, Any]]:
    """
    Loads rows from DB, uses 'correct_category' if present,
    otherwise uses the original category. Returns a list of
    dicts in the form needed by the FeedbackDataset.
    """
    query = """
    SELECT 
        file_name, 
        category_id, 
        category_name, 
        correct_category,
        extracted_text
    FROM document_processing_results
    WHERE extracted_text IS NOT NULL
    """
    
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        
        feedback_data = []
        for row in rows:
            # Use the corrected category if available, otherwise use original
            category = row['correct_category'] if row['correct_category'] else row['category_name']
            
            feedback_data.append({
                'text': row['extracted_text'],
                'label': category
            })
        
        return feedback_data
    finally:
        await conn.close()


async def save_bedrock_result_to_db(bedrock_result: dict, filepath: str) -> uuid.UUID:
    """
    Save Bedrock classification result to the database
    
    :param bedrock_result: The classification result from Bedrock
    :param filepath: Path to the classified file
    :return: UUID of the inserted record
    """
    category_name = bedrock_result.get('category', 'ERROR')
    
    # Get labels dynamically from the database
    labels = await get_labels()
    
    # Try to find the category in the labels
    try:
        category_info = labels.get(category_name, {'code': 999})
        category_id = category_info['code']
    except (KeyError, TypeError):
        category_id = 999  # ERROR code
    
    confidence = bedrock_result.get('confidence', 0.0)
    reasons = bedrock_result.get('notes', '')
    extracted_text = bedrock_result.get('text', '')
    file_name = os.path.basename(filepath)
    page_count = bedrock_result.get('page_count', 1)
    error = bedrock_result.get('error')
    
    # Prepare the result format
    result = {
        "category": {
            "id": category_id,
            "name": category_name
        },
        "confidence": confidence,
        "reasons": reasons,
        "metadata": {
            "page_count": page_count,
            "file_name": file_name
        },
        "error": error
    }
    
    # Insert into database
    return await insert_classification_result(result, extracted_text)
