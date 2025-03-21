import json
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from server.database.database import get_connection


# -------------------------------------------------
# 2. Pydantic Models
# -------------------------------------------------
class DocumentBase(BaseModel):
    name: str
    description: Optional[str] = None
    document_type_id: UUID  # References lior_dropdown_options.id
    category_id: Optional[UUID] = None  # References lior_dropdown_options.id
    period_type: Optional[str] = None
    periods_required: Optional[int] = None
    has_multiple_periods: bool


class DocumentInCreate(DocumentBase):
    required_for: List[str] = Field(default_factory=list)  # Use strings directly


class DocumentInDB(DocumentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    required_for: List[str] = Field(default_factory=list)  # Use strings directly


class DocumentUpdate(DocumentBase):
    required_for: Optional[List[str]] = None  # Use strings directly


class DocumentField(BaseModel):
    id: UUID
    document_id: UUID
    name: str
    type: str
    field_type: str
    is_identifier: bool
    is_required: bool


class DocumentFieldCreate(BaseModel):
    document_id: UUID
    name: str
    type: str
    field_type: str
    is_identifier: bool
    is_required: bool


class ValidationRule(BaseModel):
    id: UUID
    document_id: UUID
    field: str
    operator: str  # Changed from enum to string
    value: Optional[dict] = None
    error_message: str


class ValidationRuleCreate(BaseModel):
    document_id: UUID
    field: str
    operator: str  # Changed from enum to string
    value: Optional[dict] = None
    error_message: str


class DocumentWithDetails(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    document_type_id: UUID
    category_id: UUID
    created_at: datetime
    updated_at: datetime
    case_status: str
    file_path: Optional[str] = None


class DocumentCategoryModel(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    validation_rules: Optional[dict] = None
    value: str
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------
# 5. CRUD Operations
# -------------------------------------------------
async def create_document(doc_in: DocumentInCreate) -> DocumentInDB:
    conn = await get_connection()
    try:
        async with conn.transaction():
            record = await conn.fetchrow(
                """INSERT INTO documents (
                    name, description, document_type_id,
                    category_id, period_type, periods_required, has_multiple_periods
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *""",
                doc_in.name,
                doc_in.description,
                doc_in.document_type_id,
                doc_in.category_id,
                doc_in.period_type,
                doc_in.periods_required,
                doc_in.has_multiple_periods
            )
            new_doc = DocumentInDB(**dict(record))
            if doc_in.required_for:
                for rf in doc_in.required_for:
                    await conn.execute(
                        "INSERT INTO documents_required_for VALUES ($1, $2)",
                        new_doc.id,
                        rf  # Using string directly
                    )
            new_doc.required_for = doc_in.required_for.copy()
            return new_doc
    finally:
        await conn.close()


async def get_document(document_id: UUID) -> Optional[DocumentInDB]:
    conn = await get_connection()
    try:
        # Get the document
        doc = await conn.fetchrow(
            """SELECT * FROM documents WHERE id = $1""",
            document_id
        )

        if not doc:
            return None

        # Convert to dict
        doc_dict = dict(doc)

        # Get required_for values
        required_for_rows = await conn.fetch(
            """SELECT required_for FROM documents_required_for 
               WHERE document_id = $1""",
            document_id
        )

        # Parse required_for values
        if required_for_rows:
            # Use strings directly
            doc_dict['required_for'] = [row['required_for'] for row in required_for_rows]
        else:
            doc_dict['required_for'] = []

        # Create DocumentInDB object
        return DocumentInDB(**doc_dict)
    finally:
        await conn.close()


async def update_document(document_id: UUID, doc_update: DocumentUpdate) -> Optional[DocumentInDB]:
    existing = await get_document(document_id)
    if not existing:
        return None

    updated_data = existing.model_copy(update=doc_update.model_dump(exclude_unset=True))
    conn = await get_connection()
    try:
        async with conn.transaction():
            record = await conn.fetchrow(
                """UPDATE documents SET
                    name = $1,
                    description = $2,
                    document_type_id = $3,
                    category_id = $4,
                    period_type = $5,
                    periods_required = $6,
                    has_multiple_periods = $7
                WHERE id = $8
                RETURNING *""",
                updated_data.name,
                updated_data.description,
                updated_data.document_type_id,
                updated_data.category_id,
                updated_data.period_type,
                updated_data.periods_required,
                updated_data.has_multiple_periods,
                document_id
            )

            if doc_update.required_for is not None:
                await conn.execute(
                    "DELETE FROM documents_required_for WHERE document_id = $1",
                    document_id
                )
                for rf in doc_update.required_for:
                    await conn.execute(
                        "INSERT INTO documents_required_for VALUES ($1, $2)",
                        document_id,
                        rf  # Using string directly
                    )

            if record is not None:
                updated = DocumentInDB(**dict(record))
                updated.required_for = doc_update.required_for.copy() if doc_update.required_for is not None else updated.required_for
                return updated
            return None
    finally:
        await conn.close()


async def delete_document(document_id: UUID) -> bool:
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
            return "DELETE 1" in result
    finally:
        await conn.close()


async def list_documents() -> List[DocumentInDB]:
    conn = await get_connection()
    try:
        # Get all documents with a single query
        # Left join with documents_required_for to get required_for values
        query = """
        SELECT d.id, d.name, d.description, d.document_type_id, 
               d.category_id, d.period_type, d.periods_required, d.has_multiple_periods,
               d.created_at, d.updated_at,
               ARRAY_AGG(drf.required_for) FILTER (WHERE drf.required_for IS NOT NULL) AS required_for
        FROM documents d
        LEFT JOIN documents_required_for drf ON d.id = drf.document_id
        GROUP BY d.id, d.name, d.description, d.document_type_id, 
                 d.category_id, d.period_type, d.periods_required, 
                 d.has_multiple_periods, d.created_at, d.updated_at
        ORDER BY d.name
        """

        records = await conn.fetch(query)

        result = []
        for record in records:
            doc_dict = dict(record)

            # Handle the required_for array from the query
            required_for_list = doc_dict.get('required_for', [])
            # Remove None values if any
            if required_for_list and None in required_for_list:
                required_for_list = [rf for rf in required_for_list if rf is not None]
            # Handle empty arrays
            if not required_for_list or required_for_list == [None]:
                required_for_list = []

            doc_dict['required_for'] = required_for_list

            # Create DocumentInDB object
            result.append(DocumentInDB(**doc_dict))

        return result
    finally:
        await conn.close()


# Document Fields CRUD
async def create_document_field(field: DocumentFieldCreate) -> DocumentField:
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """INSERT INTO document_fields (document_id, name, type, is_identifier, field_type, is_required)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *""",
            field.document_id,
            field.name,
            field.type,
            field.is_identifier,
            field.field_type,
            field.is_required
        )
        return DocumentField(**dict(row))
    finally:
        await conn.close()


async def get_document_fields(document_id: UUID) -> List[DocumentField]:
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM document_fields WHERE document_id = $1",
            document_id
        )
        return [DocumentField(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def delete_document_field(field_id: UUID) -> bool:
    conn = await get_connection()
    try:
        result = await conn.execute(
            "DELETE FROM document_fields WHERE id = $1",
            field_id
        )
        return "DELETE 1" in result
    finally:
        await conn.close()


# Validation Rules CRUD
async def create_validation_rule(rule: ValidationRuleCreate) -> ValidationRule:
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """INSERT INTO validation_rules (
                document_id, field, operator, value, error_message
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING *""",
            rule.document_id,
            rule.field,
            rule.operator,  # String value directly
            json.dumps(rule.value) if rule.value else None,
            rule.error_message
        )
        return ValidationRule(**{
            **dict(row),
            "value": json.loads(row["value"]) if row["value"] else None
        })
    finally:
        await conn.close()


async def get_validation_rules(document_id: UUID) -> List[ValidationRule]:
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM validation_rules WHERE document_id = $1",
            document_id
        )
        return [
            ValidationRule(**{
                **dict(row),
                "value": json.loads(row["value"]) if row["value"] else None
            })
            for row in rows
        ]
    finally:
        await conn.close()


async def delete_validation_rule(rule_id: UUID) -> bool:
    conn = await get_connection()
    try:
        result = await conn.execute(
            "DELETE FROM validation_rules WHERE id = $1",
            rule_id
        )
        return "DELETE 1" in result
    finally:
        await conn.close()


# Utility: List Tables
async def list_tables() -> List[str]:
    """
    List all table names in the current database, excluding system tables.
    Returns a list of table names.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch("""
            SELECT tablename 
            FROM pg_catalog.pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY tablename;
        """)
        return [row['tablename'] for row in rows]
    finally:
        await conn.close()


async def list_case_documents_by_category(case_id: UUID, category_id: UUID) -> List[DocumentWithDetails]:
    query = """
        SELECT 
            d.id, d.name, d.description, 
            d.document_type_id, d.category_id,
            d.created_at, d.updated_at,
            'pending' as case_status, -- Default status since the column doesn't exist
            cdoc.file_path
        FROM documents d
        JOIN case_documents cdoc ON d.id = cdoc.document_id
        WHERE cdoc.case_id = $1 AND d.category_id = $2
    """
    conn = await get_connection()
    try:
        results = await conn.fetch(query, case_id, category_id)
        return [DocumentWithDetails(**dict(r)) for r in results]
    finally:
        await conn.close()


async def get_document_category_by_value(value: str) -> Optional[DocumentCategoryModel]:
    """Get a document category by its value field from lior_dropdown_options table"""
    conn = await get_connection()
    try:
        query = """
        SELECT id, name, value, created_at, updated_at 
        FROM lior_dropdown_options 
        WHERE category = 'document_categories' AND value = $1
        """
        result = await conn.fetchrow(query, value)

        if not result:
            return None

        # Create a document category model with the fields we have
        return DocumentCategoryModel(
            id=result['id'],
            name=result['name'],
            value=result['value'],
            created_at=result['created_at'],
            updated_at=result['updated_at'],
            description=None,  # These fields don't exist in lior_dropdown_options
            validation_rules=None
        )
    finally:
        await conn.close()


async def get_all_document_categories() -> List[DocumentCategoryModel]:
    """Get all document categories from the lior_dropdown_options table"""
    conn = await get_connection()
    try:
        query = """
        SELECT id, name, value, created_at, updated_at 
        FROM lior_dropdown_options
        WHERE category = 'document_categories'
        ORDER BY name
        """
        results = await conn.fetch(query)

        return [
            DocumentCategoryModel(
                id=r['id'],
                name=r['name'],
                value=r['value'],
                created_at=r['created_at'],
                updated_at=r['updated_at'],
                description=None,  # These fields don't exist in lior_dropdown_options
                validation_rules=None
            )
            for r in results
        ]
    finally:
        await conn.close()


async def verify_case_access(user_id: UUID, case_id: UUID) -> bool:
    """Check if user has access to a case"""
    conn = await get_connection()
    try:
        # Simple implementation - in reality, this would have more complex access control
        # Normally you'd check if the user is assigned to the case or has a role with access
        query = "SELECT 1 FROM cases WHERE id = $1"
        result = await conn.fetchrow(query, case_id)
        return bool(result)
    finally:
        await conn.close()


async def get_document_by_name(name: str) -> Optional[DocumentInDB]:
    """
    Get a document by its name

    Args:
        name: The name of the document to retrieve

    Returns:
        The document if found, None otherwise
    """
    conn = await get_connection()
    try:
        query = """
        SELECT id, name, description, document_type_id, category_id, 
               period_type, periods_required, has_multiple_periods,
               created_at, updated_at
        FROM documents
        WHERE name = $1
        """
        result = await conn.fetchrow(query, name)

        if not result:
            return None

        doc_dict = dict(result)

        # Get required_for values
        required_for_rows = await conn.fetch(
            """SELECT required_for FROM documents_required_for 
               WHERE document_id = $1""",
            doc_dict['id']
        )

        # Parse required_for values
        if required_for_rows:
            doc_dict['required_for'] = [row['required_for'] for row in required_for_rows]
        else:
            doc_dict['required_for'] = []

        return DocumentInDB(**doc_dict)
    finally:
        await conn.close()