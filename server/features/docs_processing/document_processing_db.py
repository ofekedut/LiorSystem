# file: document_processing_db.py

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from pydantic import BaseModel, Field

# Database file name
DB_FILENAME = "document_processing_results.db"

# -------------------------------------------------------------------
# CANDIDATE LABELS & MAPPING
# -------------------------------------------------------------------
labels = {
    "DNA_ADMINISTRATIVE": {"code": 1, "hebrew": "DNA_מינהלי"},
    "DNA_OSH": {"code": 2, "hebrew": "DNA_בטיחות"},
    "NEW_ID_CARD": {"code": 3, "hebrew": "תעודת זהות חדשה"},
    "DRIVERS_LICENSE": {"code": 4, "hebrew": "רישיון נהיגה"},
    "RATING_REPORT": {"code": 5, "hebrew": "דו\"ח דירוג"},
    "COMPLETION_CERTIFICATE": {"code": 6, "hebrew": "תעודת השלמה"},
    "BDI_DATA_SUMMARY": {"code": 7, "hebrew": "BDI_סיכום נתונים"},
    "DNA_INFORMATION_REQUESTS": {"code": 8, "hebrew": "DNA_בקשות מידע"},
    "DNA_GENERAL": {"code": 9, "hebrew": "DNA_כללי"},
    "RIGHTS_CONFIRMATION": {"code": 10, "hebrew": "אישור זכויות"},
    "HOUSE_SCRIPT": {"code": 11, "hebrew": "תסריט בית"},
    "BUILDING_PLAN": {"code": 12, "hebrew": "תוכנית בניין"},
    "ID_APPENDIX": {"code": 13, "hebrew": "נספח תעודת זהות"},
    "BUSINESS_LICENSE": {"code": 14, "hebrew": "רישיון עסק"},
    "BDI_PUBLIC_ENTITIES": {"code": 15, "hebrew": "BDI_גופים ציבוריים"},
    "PROPERTY_EXTRACT": {"code": 16, "hebrew": "תעודת מקרקעין"},
    "SALES_CONTRACT": {"code": 17, "hebrew": "חוזה מכר"},
    "VEHICLE_LICENSE": {"code": 18, "hebrew": "רישיון רכב"},
    "SIGNATURE_PROTOCOL": {"code": 19, "hebrew": "פרוטוקול חתימה"},
    "COMPANY_EXTRACT": {"code": 20, "hebrew": "תקציר חברה"},
    "PASSPORT": {"code": 21, "hebrew": "דרכון"},
    "BDI_TRANSACTION_SUMMARY": {"code": 22, "hebrew": "BDI_סיכום עסקאות"},
    "BDI_TREND_ANALYSIS": {"code": 23, "hebrew": "BDI_ניתוח מגמות"},
    "LEASE_CONTRACT": {"code": 24, "hebrew": "חוזה שכירות"},
    "DNA_LOANS": {"code": 25, "hebrew": "DNA הלוואות"},
    "APPRAISAL": {"code": 26, "hebrew": "שמאות"},
    "CREDIT_REPORT": {"code": 27, "hebrew": "דו\"ח אשראי"},
    "BUILDING_PERMIT": {"code": 28, "hebrew": "יתר בניה"},
    "OLD_ID_CARD": {"code": 29, "hebrew": "תעודת זהות ישנה"},
    "CERTIFICATE_OF_INCORPORATION": {"code": 30, "hebrew": "תעודת התאגדות"},
    "PROPERTY_TAX": {"code": 31, "hebrew": "ארנונה"},
    "MORTGAGE_APPROVAL": {"code": 32, "hebrew": "אישור משכנתא"},
    "DEAL_SUMMARY": {"code": 33, "hebrew": "סיכום עסקה"},
    "PAYSLIP": {"code": 34, "hebrew": "תלוש שכר"},
    "LIFE_INSURANCE_POLICY": {"code": 35, "hebrew": "פוליסת ביטוח חיים"},
    "BUILDING_INSURANCE_POLICY": {"code": 36, "hebrew": "פוליסת ביטוח מבנה"},
    "INTEREST_IMPROVEMENT_REQ": {"code": 37, "hebrew": "בקשת שיפור ריבית"},
    "DIRECT_FINANCE": {"code": 38, "hebrew": "מימון ישיר"},
    "CLIENT_MEETING": {"code": 39, "hebrew": "פגישת לקוח"},
    "CLIENT_INTERPRETATION": {"code": 40, "hebrew": "פרשנות לקוח"},
    "PROFIT_LOSS_REPORT": {"code": 41, "hebrew": "דו\"ח רווח והפסד"},
    "BANK_TRANSACTIONS": {"code": 42, "hebrew": "פעולות בנק"},
    "REFERRAL_TO_APPRAISAL": {"code": 43, "hebrew": "הפניה לשמאות"},
    "ACCOUNT_MANAGEMENT_APPROVAL": {"code": 44, "hebrew": "אישור ניהול חשבון"},
    "LEGAL_CONTRACT": {"code": 46, "hebrew": "חוזה משפטי"},
    "EMPLOYMENT_CONTRACT": {"code": 47, "hebrew": "חוזה עבודה"},
    "INVOICE": {"code": 48, "hebrew": "חשבונית"},
    "RECEIPT": {"code": 49, "hebrew": "קבלה"},
    "TAX_DOCUMENT": {"code": 50, "hebrew": "מסמך מס"},
    "BANK_STATEMENT": {"code": 51, "hebrew": "דו\"ח בנקאי"},
    "FINANCIAL_STATEMENT": {"code": 52, "hebrew": "דו\"ח כספי"},
    "LEGAL_DOCUMENT": {"code": 53, "hebrew": "מסמך משפטי"},
    "CERTIFICATE_OF_QUALITY": {"code": 54, "hebrew": "תעודת איכות"},
    "LOAN": {"code": 55, "hebrew": "הלוואה"},
    "OTHER": {"code": 56, "hebrew": "אחר"},
    "ERROR": {"code": 999, "hebrew": "שגיאה"},

}

# Create mapping dictionaries
LABEL2CATEGORY: Dict[str, int] = {k: v['code'] for k, v in labels.items()}
CATEGORY2LABEL: Dict[int, str] = {v['code']: k for k, v in labels.items()}
CANDIDATE_LABELS = list(labels.keys())


class DocumentCategory(Enum):
    DNA_ADMINISTRATIVE = 1
    DNA_CRIMINAL_RECORD = 2
    NEW_ID_CARD = 3
    DRIVERS_LICENSE = 4
    RATING_REPORT = 5
    COMPLETION_CERTIFICATE = 6
    BDI_DATA_SUMMARY = 7
    DNA_INFORMATION_REQUESTS = 8
    DNA_GENERAL = 9
    RIGHTS_CONFIRMATION = 10
    HOUSE_SCRIPT = 11
    BUILDING_PLAN = 12
    ID_APPENDIX = 13
    BUSINESS_LICENSE = 14
    BDI_PUBLIC_ENTITIES = 15
    PROPERTY_EXTRACT = 16
    SALES_CONTRACT = 17
    VEHICLE_LICENSE = 18
    SIGNATURE_PROTOCOL = 19
    COMPANY_EXTRACT = 20
    PASSPORT = 21
    BDI_TRANSACTION_SUMMARY = 22
    BDI_TREND_ANALYSIS = 23
    LEASE_CONTRACT = 24
    DNA_LOANS = 25
    APPRAISAL = 26
    CREDIT_REPORT = 27
    BUILDING_PERMIT = 28
    OLD_ID_CARD = 29
    CERTIFICATE_OF_INCORPORATION = 30
    PROPERTY_TAX = 31
    ERROR = 999

    @classmethod
    def from_name(cls, name: str):
        """
        Attempt to map the category name to a DocumentCategory enum.
        If it fails, returns DocumentCategory.ERROR.
        """
        try:
            return cls[name]
        except KeyError:
            return cls.ERROR


class ClassificationResultModel(BaseModel):
    category_id: int = Field(..., description="Numeric code for the document category")
    category_name: str = Field(..., description="Name of the document category")
    confidence: float = Field(..., description="Confidence score for the classification")
    reasons: str = Field(..., description="Explanation or reasoning behind the prediction")
    page_count: int = Field(..., description="Number of pages processed")
    file_name: str = Field(..., description="Name of the file processed")
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
            self.error,
            "",
            self.processed_at.strftime("%Y-%m-%d %H:%M:%S"),
            ""
        )


class ClassificationResult(BaseModel):
    category: int
    confidence: float
    reasons: str
    page_count: int
    file_name: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category,
            "category_name": CATEGORY2LABEL.get(self.category, "Unknown"),
            "confidence": self.confidence,
            "reasons": self.reasons,
            "metadata": {"page_count": self.page_count, "file_name": self.file_name},
            "error": self.error
        }


def init_db(db_path: str = DB_FILENAME):
    """
    Initialize the SQLite database.
    Creates the document_results table if it doesn't already exist,
    including a column for extracted text used in classification.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            category_id INTEGER,
            category_name TEXT,
            confidence REAL,
            reasons TEXT,
            page_count INTEGER,
            error TEXT,
            correct_category TEXT,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            extracted_text TEXT,
             file_path text 
        )
    ''')
    conn.commit()
    conn.close()


def insert_classification_result(result: dict, extracted_text: str, db_path: str = DB_FILENAME):
    """
    Inserts a classification result into the SQLite database.

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
    :param db_path: Path to the SQLite DB file.
    """
    file_name = result.get("metadata", {}).get("file_name", "unknown")
    category = result.get("category", {})
    category_id = category.get("id")
    category_name = category.get("name")
    confidence = result.get("confidence")
    reasons = result.get("reasons")
    page_count = result.get("metadata", {}).get("page_count")
    filepath = result.get("filepath")
    error = result.get("error")
    correct_category = result.get("correct_category", None)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO document_results (  
            file_name,
            category_id,
            category_name,
            confidence,
            reasons,
            page_count,
            error,
            correct_category,
            extracted_text, file_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (file_name, category_id, category_name, confidence, reasons,
          page_count, error, correct_category, extracted_text, filepath))
    conn.commit()
    conn.close()


def get_all_results(db_path: str = DB_FILENAME):
    """
    Fetches all classification results from the SQLite database.
    Returns a list of rows as tuples:
    (
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
    )
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
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
            extracted_text, file_path
        FROM document_results
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_result_by_filename(filename, db_path: str = DB_FILENAME):
    """
    Fetches all classification results from the SQLite database.
    Returns a list of rows as tuples:
    (
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
    )
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
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
            extracted_text, file_path
        FROM document_results where file_name  = ?
    ''', (filename,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_correct_category(record_id: int, correction: str, db_path: str = DB_FILENAME):
    """
    Updates the 'correct_category' field for the given record in the database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE document_results
        SET correct_category = ?
        WHERE id = ?
    ''', (correction, record_id))
    conn.commit()
    conn.close()


def load_feedback_from_db(db_path: str = DB_FILENAME) -> List[Dict[str, Any]]:
    """
    Loads rows from DB, uses 'correct_category' if present,
    otherwise uses the original category. Returns a list of
    dicts in the form needed by the FeedbackDataset.
    """
    rows = get_all_results(db_path)
    feedback_data = []

    for row in rows:
        (record_id, file_name, category_id, category_name, confidence, reasons,
         page_count, error, correct_category, processed_at, extracted_text) = row

        # Determine final category id/name
        final_id = category_id
        final_name = category_name
        if correct_category and correct_category.strip():
            # user corrected with a name, attempt to map
            cat_enum = DocumentCategory.from_name(correct_category.strip())
            final_id = cat_enum.value
            final_name = cat_enum.name

        # We'll train on extracted_text if available, else fallback to reasons
        text_for_training = extracted_text if extracted_text else (reasons or "")

        feedback_data.append({
            "category": {
                "id": final_id,
                "name": final_name
            },
            "confidence": confidence,
            "reasons": text_for_training,
            "metadata": {
                "page_count": page_count,
                "file_name": file_name
            },
            "error": error,
            "correct_category": correct_category or "",
        })

    return feedback_data
def save_bedrock_result_to_db(bedrock_result: dict, filepath, db_path: str = DB_FILENAME):
    filename = bedrock_result.get("filename", "unknown")
    used_text = bedrock_result.get("used_text", "")
    predicted_label = bedrock_result.get("predicted_label", "ERROR")
    confidence = bedrock_result.get("confidence", 0.0)
    aws_response = bedrock_result.get("aws_response", "")
    category_info = bedrock_result.get("category_info", "")

    # Map the predicted label to its numeric category ID.
    category_id = LABEL2CATEGORY.get(predicted_label, labels["ERROR"]["code"])

    # Build the result dictionary expected by the DB insertion function.
    result_dict = {
        'filepath': filepath,
        "metadata": {
            "page_count": 1,  # Default page count (adjust if available)
            "file_name": filename
        },
        "category": {
            "id": category_id,
            "name": predicted_label
        },
        "confidence": confidence,
        "reasons": (
            f"Bedrock classification predicted '{predicted_label}' with confidence {confidence:.2f}. "
            f"Category info: {category_info}. AWS response: {aws_response}"
        ),
        "error": None,
        "correct_category": ""
    }

    # Call the DB function to insert the result, using used_text as the extracted text.
    insert_classification_result(result_dict, extracted_text=used_text, db_path=db_path)


if __name__ == '__main__':
    print(get_all_results())
