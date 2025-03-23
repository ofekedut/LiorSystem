"""
Database operations for unique document types management.
"""
import json
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
class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None


class Links(BaseModel):
    url: Optional[str] = None
    additional_url: Optional[str] = None


class UniqueDocTypeBase(BaseModel):
    display_name: str
    category: DocumentCategory
    issuer: Optional[str] = None
    target_object: DocumentTargetObject
    document_type: DocumentType
    is_recurring: bool
    frequency: Optional[DocumentFrequency] = None
    links: Optional[Links] = None
    contact_info: Optional[ContactInfo] = None

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
    links: Optional[Links] = None
    contact_info: Optional[ContactInfo] = None


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
                    document_type, is_recurring, frequency,
                    links, contact_info
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, display_name, category, issuer, target_object,
                        document_type, is_recurring, frequency,
                        links, contact_info, created_at, updated_at
                """,
                doc_type.display_name,
                doc_type.category,
                doc_type.issuer,
                doc_type.target_object,
                doc_type.document_type,
                doc_type.is_recurring,
                doc_type.frequency,
                json.dumps(doc_type.links.model_dump()) if doc_type.links else None,
                json.dumps(doc_type.contact_info.model_dump()) if doc_type.contact_info else None
            )

            # Convert the record to a dict
            doc_dict = dict(record)

            # Parse JSON fields
            if doc_dict['links']:
                doc_dict['links'] = Links.model_validate(json.loads(doc_dict['links']))

            if doc_dict['contact_info']:
                doc_dict['contact_info'] = ContactInfo.model_validate(json.loads(doc_dict['contact_info']))

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
               links, contact_info, created_at, updated_at
        FROM unique_doc_types
        WHERE id = $1
        """

        record = await conn.fetchrow(query, doc_type_id)

        if not record:
            return None

        # Convert to dict
        doc_dict = dict(record)

        # Parse JSON fields
        if doc_dict['links']:
            doc_dict['links'] = Links.model_validate(json.loads(doc_dict['links']))

        if doc_dict['contact_info']:
            doc_dict['contact_info'] = ContactInfo.model_validate(json.loads(doc_dict['contact_info']))

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

            if doc_type_update.links is not None:
                fields_to_update.append(f"links = ${param_idx}")
                params.append(json.dumps(doc_type_update.links.model_dump()) if doc_type_update.links else None)
                param_idx += 1

            if doc_type_update.contact_info is not None:
                fields_to_update.append(f"contact_info = ${param_idx}")
                params.append(json.dumps(doc_type_update.contact_info.model_dump()) if doc_type_update.contact_info else None)
                param_idx += 1

            # If there are fields to update, execute the update query
            if fields_to_update:
                update_query = f"""
                    UPDATE unique_doc_types
                    SET {", ".join(fields_to_update)}
                    WHERE id = ${param_idx}
                    RETURNING id, display_name, category, issuer, target_object,
                            document_type, is_recurring, frequency,
                            links, contact_info, created_at, updated_at
                """
                params.append(doc_type_id)
                record = await conn.fetchrow(update_query, *params)
                doc_dict = dict(record)

                # Parse JSON fields
                if doc_dict['links']:
                    doc_dict['links'] = Links.model_validate(json.loads(doc_dict['links']))

                if doc_dict['contact_info']:
                    doc_dict['contact_info'] = ContactInfo.model_validate(json.loads(doc_dict['contact_info']))

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
               links, contact_info, created_at, updated_at
        FROM unique_doc_types
        ORDER BY display_name
        """
        records = await conn.fetch(query)
        
        result = []
        
        for record in records:
            doc_dict = dict(record)
            
            # Parse JSON fields
            if doc_dict['links']:
                doc_dict['links'] = Links.model_validate(json.loads(doc_dict['links']))
                
            if doc_dict['contact_info']:
                doc_dict['contact_info'] = ContactInfo.model_validate(json.loads(doc_dict['contact_info']))
                
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
               links, contact_info, created_at, updated_at
        FROM unique_doc_types
        WHERE category = $1
        ORDER BY display_name
        """
        records = await conn.fetch(query, category)
        
        result = []
        
        for record in records:
            doc_dict = dict(record)
            
            # Parse JSON fields
            if doc_dict['links']:
                doc_dict['links'] = Links.model_validate(json.loads(doc_dict['links']))
                
            if doc_dict['contact_info']:
                doc_dict['contact_info'] = ContactInfo.model_validate(json.loads(doc_dict['contact_info']))
                
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
               links, contact_info, created_at, updated_at
        FROM unique_doc_types
        WHERE target_object = $1
        ORDER BY display_name
        """
        records = await conn.fetch(query, target_object)
        
        result = []
        
        for record in records:
            doc_dict = dict(record)
            
            # Parse JSON fields
            if doc_dict['links']:
                doc_dict['links'] = Links.model_validate(json.loads(doc_dict['links']))
                
            if doc_dict['contact_info']:
                doc_dict['contact_info'] = ContactInfo.model_validate(json.loads(doc_dict['contact_info']))
                
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
