import json
import os
import re
import asyncio

from features.docs_processing.detect_doc_type_ollama import classify_document_ollama
from features.docs_processing.document_processing_db import (
    init_db, 
    get_result_by_filename, 
    get_all_results,
    insert_classification_result,
    get_labels, 
    save_bedrock_result_to_db
)
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, root_validator, model_validator

from features.docs_processing.utils import extract_first_last, is_containing_hebrew_letters


class SubCaseAttachment(BaseModel):
    """
    Represents a file or resource attached to a subitem.
    """
    name: str
    public_url: str


class SubCase(BaseModel):
    """
    Represents a Monday.com subitem (what you called a 'subitem').
    This model extracts core columns like 'בטיפול', 'סטטוס סאבים', etc.
    """
    id: str
    name: str
    assigned_to: Optional[str] = None  # "בטיפול" -> id='people__1'
    sub_status: Optional[str] = None  # "סטטוס סאבים" -> id='status'
    timeline: Optional[str] = None  # "ציר זמן" -> id='timeline3__1'
    files_text: Optional[str] = None  # "קבצים" (display text) -> id='files__1'
    date_main: Optional[str] = None  # "תאריך" -> id='date__1'
    date_extra: Optional[str] = None  # "Date" -> id='date_mkmcxhj7'
    subitem_id: Optional[str] = None  # "Item ID" -> id='item_id_Mjj6mEi1'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'assigned_to': self.assigned_to,
            'sub_status': self.sub_status,
            'timeline': self.timeline,
            'files_text': self.files_text,
            'date_main': self.date_main,
            'date_extra': self.date_extra,
            'subitem_id': self.subitem_id,
        }

    # Holds the raw column_values if you want to store them as well.
    column_values: Optional[List[Dict[str, Any]]] = None

    # The 'assets' field lists any attached files with their public URLs.
    assets: Optional[List[SubCaseAttachment]] = None

    @root_validator(pre=True)
    def populate_fields_from_columns(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        A root validator to extract subitem columns by matching IDs
        (e.g., 'people__1' or 'status') and populate our fields.
        """

        # A helper to find a column's .text by its ID
        def get_text(col_id: str, column_vals: List[Dict[str, Any]]) -> Optional[str]:
            for col_dict in column_vals:
                if col_dict.get("column", {}).get("id") == col_id:
                    return col_dict.get("text")
            return None

        col_vals = values.get("column_values") or []

        # Map each relevant subitem column ID to the appropriate field.
        values["assigned_to"] = get_text("people__1", col_vals)
        values["sub_status"] = get_text("status", col_vals)
        values["timeline"] = get_text("timeline3__1", col_vals)
        values["files_text"] = get_text("files__1", col_vals)
        values["date_main"] = get_text("date__1", col_vals)
        values["date_extra"] = get_text("date_mkmcxhj7", col_vals)
        values["subitem_id"] = get_text("item_id_Mjj6mEi1", col_vals)

        # Convert the "assets" array (if any) to SubCaseAttachment objects
        raw_assets = values.get("assets") or []
        if isinstance(raw_assets, list):
            attachments = []
            for asset in raw_assets:
                # We expect each asset to have 'name' and 'public_url'
                att = SubCaseAttachment(**asset)
                attachments.append(att)
            values["assets"] = attachments

        return values

    class Config:
        extra = "allow"


class Case(BaseModel):
    id: str
    name: str
    case_nature: Optional[str] = None  # "מהות התיק" -> id='dropdown__1'
    loan_type: Optional[str] = None  # "סוג הלוואה" -> id='dropdown9__1'
    case_status: Optional[str] = None  # "סטטוס הכנת תיק לקוח" -> id='project_status'
    priority: Optional[str] = None  # "עדיפות" -> id='priority_1'
    rosy_remarks: Optional[str] = None  # "הערות רוזי" -> id='status_mkkr2t94'
    financing_percent: Optional[str] = None  # "אחוז מגיוס" -> id='numbers6__1'
    expected_fee: Optional[str] = None  # "שכ"ט צפוי" -> id='numbers8__1'
    main_contact: Optional[str] = None  # "לקוח איתו מתנהלים" -> id='text7__1'
    phone: Optional[str] = None  # "טלפון" -> id='phone__1'
    national_id: Optional[str] = None  # "ת.ז" -> id='text8__1'
    item_id: Optional[str] = None  # "Item ID" -> id='item_id_Mjj6uqvW'
    solution_date: Optional[str] = None  # "תאריך חיפוש פיתרון" -> id='date_mkkt63tm'
    last_move_date: Optional[str] = None  # "תאריך מעבר אחרון" -> id='date_mkktze1j'

    column_values: Optional[List[Dict[str, Any]]] = None

    subitems: Optional[List["SubCase"]] = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'case_nature': self.case_nature,
            'loan_type': self.loan_type,
            'case_status': self.case_status,
            'priority': self.priority,
            'rosy_remarks': self.rosy_remarks,
            'financing_percent': self.financing_percent,
            'expected_fee': self.expected_fee,
            'main_contact': self.main_contact,
            'phone': self.phone,
            'national_id': self.national_id,
            'item_id': self.item_id,
            'solution_date': self.solution_date,
            'last_move_date': self.last_move_date,
        }

    @model_validator(mode='before')
    def populate_fields_from_columns(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        This root validator runs *before* normal field parsing.
        It extracts column data from 'column_values' by matching on 'column.id'
        and sets each target field accordingly.
        """

        # Helper to find a column by ID and return either its 'text' or None.
        def get_text_for_column(col_id: str) -> Optional[str]:
            col_vals = values.get("column_values") or []
            for col in col_vals:
                if col.get("column", {}).get("id") == col_id:
                    return col.get("text")
            return None

        # Fill each of our fields from the matching column ID:
        values["case_nature"] = get_text_for_column("dropdown__1")
        values["loan_type"] = get_text_for_column("dropdown9__1")
        values["case_status"] = get_text_for_column("project_status")
        values["priority"] = get_text_for_column("priority_1")
        values["rosy_remarks"] = get_text_for_column("status_mkkr2t94")
        values["financing_percent"] = get_text_for_column("numbers6__1")
        values["expected_fee"] = get_text_for_column("numbers8__1")
        values["main_contact"] = get_text_for_column("text7__1")
        values["phone"] = get_text_for_column("phone__1")
        values["national_id"] = get_text_for_column("text8__1")
        values["item_id"] = get_text_for_column("item_id_Mjj6uqvW")
        values["solution_date"] = get_text_for_column("date_mkkt63tm")
        values["last_move_date"] = get_text_for_column("date_mkktze1j")

        # Also parse subitems (if any), converting them to our Case model
        # We'll store them in the 'subitems' field
        raw_subitems = values.get("subitems")
        if isinstance(raw_subitems, list):
            values["subitems"] = [SubCase(**sub) for sub in raw_subitems]

        return values

    def print(self):
        print(f'{self.id} {self.name} - {self.case_nature} | {self.case_status}')


async def create_data():
    """Test function to create sample data in the database"""
    results = await get_all_results()
    print(f"Database has {len(results)} results.")

    try:
        # Test inserting a data entry
        # Get labels from database
        labels = await get_labels()
        # Find a document type by name
        document_key = next(iter(labels.keys()))
        document_info = labels[document_key]
        
        test_result = {
            "category": {"id": document_info['code'], "name": document_key},
            "confidence": 0.95,
            "reasons": "This is a test entry",
            "metadata": {"page_count": 1, "file_name": "test_file.pdf"},
            "error": None
        }
        await insert_classification_result(test_result, "Test extracted text")
        print("Test data inserted successfully")
    except Exception as e:
        print(f"Error inserting test data: {e}")


async def main():
    """Main function to run the document processing pipeline"""
    # Initialize the database
    await init_db()
    
    # Get labels from database
    labels = await get_labels()
    
    i = 0
    outputTokens = 0
    inputTokens = 0
    basedir = './monday_assets_bar'
    for board_dir in os.listdir(f"./{basedir}"):
        if not os.path.isdir(f"./{basedir}/{board_dir}"): continue
        for item_dir in os.listdir(f"./{basedir}/{board_dir}"):
            if not os.path.isdir(f"./{basedir}/{board_dir}/{item_dir}/subitems"): continue
            for subitem_dir in os.listdir(f'./{basedir}/{board_dir}/{item_dir}/subitems'):
                for filename in os.listdir(f'./{basedir}/{board_dir}/{item_dir}/subitems/{subitem_dir}'):
                    if not 'pdf' in filename: continue
                    filepath = f'./{basedir}/{board_dir}/{item_dir}/subitems/{subitem_dir}/{filename}'
                    # Check for existing results - need to use asyncio.run for the async function
                    if await get_result_by_filename(filename):
                        print(f"skipped {filename}")
                        continue
                    metadata = json.load(open(f'./{basedir}/{board_dir}/{item_dir}/subitems/{subitem_dir}/metadata.json', 'r'))
                    if not is_containing_hebrew_letters(filename): continue
                    print(filename)
                    result, usage = classify_document_ollama(
                        labels=labels,
                        filename=filename,
                        filepath=filepath
                    )
                    if result:
                        await save_bedrock_result_to_db(result, filepath)
                        with open(filepath + '_result.json', 'w') as f:
                            json.dump(result, f)
                        i += 1
                    if usage:
                        outputTokens += usage['outputTokens']
                        inputTokens += usage['inputTokens']


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
    # asyncio.run(create_data())
