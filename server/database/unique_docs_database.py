"""
Database operations for unique document types management.
"""
import json
import csv
import io
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from enum import Enum, auto
from pydantic import BaseModel, Field, ConfigDict

from server.database.database import get_connection


# -------------------------------------------------
# Enumerations
# -------------------------------------------------
class DocumentCategory(str, Enum):
    IDENTIFICATION = "identification"
    FINANCIAL = "financial"
    PROPERTY = "property"
    EMPLOYMENT = "employment"
    TAX = "tax"
    INSURANCE = "insurance"
    LEGAL = "legal"
    OTHER = "other"


class DocumentTargetObject(str, Enum):
    CASE = "case"
    PERSON = "person"
    BANK_ACCOUNT = "bank_account"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    ASSET = "asset"
    INCOME = "income"
    COMPANY = "company"


class DocumentType(str, Enum):
    ONE_TIME = "one_time"
    UPDATABLE = "updatable"
    RECURRING = "recurring"


class DocumentFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class RequiredFor(str, Enum):
    EMPLOYEES = "employees"
    SELF_EMPLOYED = "self_employed"
    BUSINESS_OWNERS = "business_owners"


# -------------------------------------------------
# Pydantic Models
# -------------------------------------------------
# Removed ContactInfo and Links classes as they are not specified in the PRD


class UniqueDocTypeBase(BaseModel):
    display_name: str
    category: DocumentCategory
    issuer: Optional[str] = None
    target_object: DocumentTargetObject
    document_type: DocumentType
    is_recurring: bool
    frequency: Optional[DocumentFrequency] = None
    # Removed links and contact_info as they are not specified in the PRD

    model_config = ConfigDict(
        use_enum_values=True,
    )


class UniqueDocTypeCreate(UniqueDocTypeBase):
    required_for: List[RequiredFor]


class UniqueDocTypeUpdate(UniqueDocTypeBase):
    display_name: Optional[str] = None
    category: Optional[DocumentCategory] = None
    issuer: Optional[str] = None
    target_object: Optional[DocumentTargetObject] = None
    document_type: Optional[DocumentType] = None
    is_recurring: Optional[bool] = None
    frequency: Optional[DocumentFrequency] = None
    required_for: Optional[List[RequiredFor]] = None
    # Removed links and contact_info as they are not specified in the PRD


class UniqueDocTypeInDB(UniqueDocTypeBase):
    id: UUID
    required_for: List[RequiredFor] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------
# CRUD Operations
# -------------------------------------------------
async def create_unique_doc_type(doc_type: UniqueDocTypeCreate) -> UniqueDocTypeInDB:
    """
    Create a new unique document type in the database.
    """
    # Validate frequency if recurring
    if doc_type.is_recurring and not doc_type.frequency:
        raise ValueError("Frequency is required for recurring documents")

    # Ensure required_for is not empty
    if not doc_type.required_for:
        raise ValueError("At least one required_for value must be provided")

    conn = await get_connection()
    try:
        async with conn.transaction():
            # Insert the main document type record
            record = await conn.fetchrow(
                """
                INSERT INTO unique_doc_types (
                    display_name, category, issuer, target_object,
                    document_type, is_recurring, frequency
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, display_name, category, issuer, target_object,
                        document_type, is_recurring, frequency,
                        created_at, updated_at
                """,
                doc_type.display_name,
                doc_type.category,
                doc_type.issuer,
                doc_type.target_object,
                doc_type.document_type,
                doc_type.is_recurring,
                doc_type.frequency
            )

            # Convert the record to a dict
            doc_dict = dict(record)

            # Insert required_for relationships
            for rf in doc_type.required_for:
                await conn.execute(
                    """
                    INSERT INTO required_for (doc_type_id, required_for)
                    VALUES ($1, $2)
                    """,
                    doc_dict['id'],
                    rf
                )

            # Prepare the response with required_for list
            doc_dict['required_for'] = [rf for rf in doc_type.required_for]

            return UniqueDocTypeInDB.model_validate(doc_dict)
    finally:
        await conn.close()


async def get_unique_doc_type(doc_type_id: UUID) -> Optional[UniqueDocTypeInDB]:
    """
    Get a specific unique document type by ID.
    """
    conn = await get_connection()
    try:
        # Get the main document type record
        query = """
        SELECT id, display_name, category, issuer, target_object,
               document_type, is_recurring, frequency,
               created_at, updated_at
        FROM unique_doc_types
        WHERE id = $1
        """

        record = await conn.fetchrow(query, doc_type_id)

        if not record:
            return None

        # Convert to dict
        doc_dict = dict(record)

        # Get required_for values
        required_for_query = """
        SELECT required_for
        FROM required_for
        WHERE doc_type_id = $1
        """

        required_for_rows = await conn.fetch(required_for_query, doc_type_id)

        # Add required_for to the result
        doc_dict['required_for'] = [row['required_for'] for row in required_for_rows]

        return UniqueDocTypeInDB.model_validate(doc_dict)
    finally:
        await conn.close()


async def update_unique_doc_type(
    doc_type_id: UUID,
    doc_type_update: UniqueDocTypeUpdate
) -> Optional[UniqueDocTypeInDB]:
    """
    Update an existing unique document type by ID.
    """
    # First, get the existing document type
    existing = await get_unique_doc_type(doc_type_id)
    if not existing:
        return None

    # Validate frequency if is_recurring is True
    if doc_type_update.is_recurring or (existing.is_recurring and doc_type_update.is_recurring is not False):
        if doc_type_update.frequency is None and existing.frequency is None:
            raise ValueError("Frequency is required for recurring documents")

    conn = await get_connection()
    try:
        async with conn.transaction():
            # Build update query dynamically based on provided fields
            fields_to_update = []
            params = []
            param_idx = 1

            # Add fields if they are provided in the update
            if doc_type_update.display_name is not None:
                fields_to_update.append(f"display_name = ${param_idx}")
                params.append(doc_type_update.display_name)
                param_idx += 1

            if doc_type_update.category is not None:
                fields_to_update.append(f"category = ${param_idx}")
                params.append(doc_type_update.category)
                param_idx += 1

            if doc_type_update.issuer is not None:
                fields_to_update.append(f"issuer = ${param_idx}")
                params.append(doc_type_update.issuer)
                param_idx += 1

            if doc_type_update.target_object is not None:
                fields_to_update.append(f"target_object = ${param_idx}")
                params.append(doc_type_update.target_object)
                param_idx += 1

            if doc_type_update.document_type is not None:
                fields_to_update.append(f"document_type = ${param_idx}")
                params.append(doc_type_update.document_type)
                param_idx += 1

            if doc_type_update.is_recurring is not None:
                fields_to_update.append(f"is_recurring = ${param_idx}")
                params.append(doc_type_update.is_recurring)
                param_idx += 1

            if doc_type_update.frequency is not None:
                fields_to_update.append(f"frequency = ${param_idx}")
                params.append(doc_type_update.frequency)
                param_idx += 1

            # Remove links and contact_info handling as they're not in the PRD

            # If there are fields to update, execute the update query
            if fields_to_update:
                update_query = f"""
                    UPDATE unique_doc_types
                    SET {", ".join(fields_to_update)}
                    WHERE id = ${param_idx}
                    RETURNING id, display_name, category, issuer, target_object,
                            document_type, is_recurring, frequency,
                            created_at, updated_at
                """
                params.append(doc_type_id)
                record = await conn.fetchrow(update_query, *params)
                doc_dict = dict(record)

                # Update required_for if provided
                if doc_type_update.required_for is not None:
                    # First delete existing relationships
                    await conn.execute(
                        "DELETE FROM required_for WHERE doc_type_id = $1",
                        doc_type_id
                    )

                    # Then insert new relationships
                    for rf in doc_type_update.required_for:
                        await conn.execute(
                            """
                            INSERT INTO required_for (doc_type_id, required_for)
                            VALUES ($1, $2)
                            """,
                            doc_type_id,
                            rf
                        )

                    # Add required_for to the result
                    doc_dict['required_for'] = [rf for rf in doc_type_update.required_for]
                else:
                    # Get existing required_for values
                    required_for_query = """
                    SELECT required_for
                    FROM required_for
                    WHERE doc_type_id = $1
                    """
                    required_for_rows = await conn.fetch(required_for_query, doc_type_id)
                    doc_dict['required_for'] = [row['required_for'] for row in required_for_rows]

                return UniqueDocTypeInDB.model_validate(doc_dict)
            else:
                # If no fields to update in the main table, but required_for is updated
                if doc_type_update.required_for is not None:
                    # Delete existing relationships
                    await conn.execute(
                        "DELETE FROM required_for WHERE doc_type_id = $1",
                        doc_type_id
                    )

                    # Insert new relationships
                    for rf in doc_type_update.required_for:
                        await conn.execute(
                            """
                            INSERT INTO required_for (doc_type_id, required_for)
                            VALUES ($1, $2)
                            """,
                            doc_type_id,
                            rf
                        )

                # Return the updated document type
                return await get_unique_doc_type(doc_type_id)
    finally:
        await conn.close()


async def is_doc_type_in_use(doc_type_id: UUID) -> bool:
    """
    Check if a document type is in use by any case documents.
    Returns True if the document type is in use, False otherwise.
    """
    conn = await get_connection()
    try:
        query = """
        SELECT EXISTS(
            SELECT 1 FROM case_documents
            WHERE doc_type_id = $1
        )
        """
        return await conn.fetchval(query, doc_type_id)
    finally:
        await conn.close()


async def delete_unique_doc_type(doc_type_id: UUID) -> bool:
    """
    Delete a unique document type by ID.
    Returns True if the document type was deleted, False if not found.
    """
    conn = await get_connection()
    try:
        # Check if the document type exists
        exists_query = "SELECT EXISTS(SELECT 1 FROM unique_doc_types WHERE id = $1)"
        exists = await conn.fetchval(exists_query, doc_type_id)

        if not exists:
            return False

        # Check if the document type is in use
        in_use = await is_doc_type_in_use(doc_type_id)
        if in_use:
            raise ValueError("Cannot delete document type that is in use by case documents")

        # Delete the document type (required_for will be deleted by CASCADE)
        delete_query = "DELETE FROM unique_doc_types WHERE id = $1"
        await conn.execute(delete_query, doc_type_id)

        return True
    finally:
        await conn.close()


async def list_unique_doc_types() -> List[UniqueDocTypeInDB]:
    """
    Get all unique document types.
    """
    conn = await get_connection()
    try:
        # Get all document types
        query = """
        SELECT id, display_name, category, issuer, target_object,
               document_type, is_recurring, frequency,
               created_at, updated_at
        FROM unique_doc_types
        ORDER BY display_name
        """
        records = await conn.fetch(query)

        result = []

        for record in records:
            doc_dict = dict(record)

            # Get required_for values
            required_for_query = """
            SELECT required_for
            FROM required_for
            WHERE doc_type_id = $1
            """
            required_for_rows = await conn.fetch(required_for_query, doc_dict['id'])

            # Add required_for to the result
            doc_dict['required_for'] = [row['required_for'] for row in required_for_rows]

            result.append(UniqueDocTypeInDB.model_validate(doc_dict))

        return result
    finally:
        await conn.close()


async def filter_by_category(category: str) -> List[UniqueDocTypeInDB]:
    """
    Filter unique document types by category.
    """
    conn = await get_connection()
    try:
        # Get document types by category
        query = """
        SELECT id, display_name, category, issuer, target_object,
               document_type, is_recurring, frequency,
               created_at, updated_at
        FROM unique_doc_types
        WHERE category = $1
        ORDER BY display_name
        """
        records = await conn.fetch(query, category)

        result = []

        for record in records:
            doc_dict = dict(record)

            # Get required_for values
            required_for_query = """
            SELECT required_for
            FROM required_for
            WHERE doc_type_id = $1
            """
            required_for_rows = await conn.fetch(required_for_query, doc_dict['id'])

            # Add required_for to the result
            doc_dict['required_for'] = [row['required_for'] for row in required_for_rows]

            result.append(UniqueDocTypeInDB.model_validate(doc_dict))

        return result
    finally:
        await conn.close()


async def filter_by_target_object(target_object: str) -> List[UniqueDocTypeInDB]:
    """
    Filter unique document types by target object.
    """
    conn = await get_connection()
    try:
        # Get document types by target object
        query = """
        SELECT id, display_name, category, issuer, target_object,
               document_type, is_recurring, frequency,
               created_at, updated_at
        FROM unique_doc_types
        WHERE target_object = $1
        ORDER BY display_name
        """
        records = await conn.fetch(query, target_object)

        result = []

        for record in records:
            doc_dict = dict(record)

            # Get required_for values
            required_for_query = """
            SELECT required_for
            FROM required_for
            WHERE doc_type_id = $1
            """
            required_for_rows = await conn.fetch(required_for_query, doc_dict['id'])

            # Add required_for to the result
            doc_dict['required_for'] = [row['required_for'] for row in required_for_rows]

            result.append(UniqueDocTypeInDB.model_validate(doc_dict))

        return result
    finally:
        await conn.close()


async def import_doc_types_from_csv(csv_content: str) -> Dict[str, Any]:
    """
    Import document types from a CSV file.
    This implements the "Import document types in bulk via CSV" feature mentioned in the PRD.

    Expected CSV format:
    display_name,category,target_object,document_type,is_recurring,frequency,issuer,required_for

    Where:
    - required_for is a comma-separated list of required_for values within quotes (e.g., "employees,self_employed")
    - is_recurring is "true" or "false"
    - frequency is only required if is_recurring is "true"

    Args:
        csv_content: String containing CSV content

    Returns:
        Dict containing success status, counts, and any errors
    """
    conn = await get_connection()
    try:
        # Parse CSV content
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        # Prepare counters
        created_count = 0
        error_count = 0
        errors = []
        
        # Process each row
        async with conn.transaction():
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header row
                try:
                    # Required fields
                    if not all(key in row for key in ['display_name', 'category', 'target_object', 'document_type']):
                        errors.append(f"Row {row_num}: Missing required fields")
                        error_count += 1
                        continue
                    
                    # Process boolean field
                    is_recurring = row.get('is_recurring', 'false').lower() == 'true'
                    
                    # Validate frequency if recurring
                    frequency = row.get('frequency')
                    if is_recurring and not frequency:
                        errors.append(f"Row {row_num}: Frequency is required for recurring documents")
                        error_count += 1
                        continue
                    
                    # Parse required_for
                    required_for_str = row.get('required_for', '').strip('"\'')
                    required_for = [rf.strip() for rf in required_for_str.split(',') if rf.strip()]
                    
                    # Validate category
                    try:
                        category = DocumentCategory(row['category'])
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid category '{row['category']}'")
                        error_count += 1
                        continue
                    
                    # Validate target_object
                    try:
                        target_object = DocumentTargetObject(row['target_object'])
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid target_object '{row['target_object']}'")
                        error_count += 1
                        continue
                    
                    # Validate document_type
                    try:
                        document_type = DocumentType(row['document_type'])
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid document_type '{row['document_type']}'")
                        error_count += 1
                        continue
                    
                    # Validate frequency if provided
                    if frequency:
                        try:
                            frequency = DocumentFrequency(frequency)
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid frequency '{frequency}'")
                            error_count += 1
                            continue
                    
                    # Validate required_for values
                    valid_required_for = []
                    for rf in required_for:
                        try:
                            valid_required_for.append(RequiredFor(rf))
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid required_for value '{rf}'")
                            error_count += 1
                            continue
                    
                    if not valid_required_for:
                        errors.append(f"Row {row_num}: At least one valid required_for value is needed")
                        error_count += 1
                        continue
                    
                    # Create doc type object
                    doc_type = UniqueDocTypeCreate(
                        display_name=row['display_name'],
                        category=category,
                        target_object=target_object,
                        document_type=document_type,
                        is_recurring=is_recurring,
                        frequency=frequency if frequency else None,
                        issuer=row.get('issuer'),
                        required_for=valid_required_for
                    )
                    
                    # Create the document type
                    await create_unique_doc_type(doc_type)
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
        
        return {
            "success": error_count == 0,
            "created_count": created_count,
            "error_count": error_count,
            "errors": errors
        }
        
    finally:
        await conn.close()
