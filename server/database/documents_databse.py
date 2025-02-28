import enum
import json
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from server.database.database import get_connection


# -------------------------------------------------
# 1. Document-related Enums
# -------------------------------------------------
class DocumentType(str, enum.Enum):
    one_time = 'one-time'
    updatable = 'updatable'
    recurring = 'recurring'


class DocumentCategory(str, enum.Enum):
    identification = 'identification'
    financial = 'financial'
    property = 'property'
    employment = 'employment'
    tax = 'tax'


class RequiredFor(str, enum.Enum):
    employees = 'employees'
    self_employed = 'self-employed'
    business_owners = 'business-owners'
    all = 'all'


class ValidationOperator(str, enum.Enum):
    equals = 'equals'
    not_equals = 'not_equals'
    greater_than = 'greater_than'
    less_than = 'less_than'
    between = 'between'
    contains = 'contains'
    starts_with = 'starts_with'
    ends_with = 'ends_with'
    before = 'before'
    after = 'after'


# -------------------------------------------------
# 2. Pydantic Models
# -------------------------------------------------
class DocumentBase(BaseModel):
    name: str
    description: Optional[str] = None
    document_type_id: UUID
    category: DocumentCategory
    category_id: Optional[UUID] = None
    period_type: Optional[str] = None
    periods_required: Optional[int] = None
    has_multiple_periods: bool


class DocumentInCreate(DocumentBase):
    required_for: List[RequiredFor] = Field(default_factory=list)


class DocumentInDB(DocumentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    required_for: List[RequiredFor] = Field(default_factory=list)


class DocumentUpdate(DocumentBase):
    required_for: Optional[List[RequiredFor]] = None


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
    operator: ValidationOperator
    value: Optional[dict] = None
    error_message: str


class ValidationRuleCreate(BaseModel):
    document_id: UUID
    field: str
    operator: ValidationOperator
    value: Optional[dict] = None
    error_message: str


# -------------------------------------------------
# 5. CRUD Operations
# -------------------------------------------------
async def create_document(doc_in: DocumentInCreate) -> DocumentInDB:
    conn = await get_connection()
    try:
        async with conn.transaction():
            record = await conn.fetchrow(
                """INSERT INTO documents (
                    name, description, document_type_id, category,
                    category_id, period_type, periods_required, has_multiple_periods
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *""",
                doc_in.name,
                doc_in.description,
                doc_in.document_type_id,
                doc_in.category.value,
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
                        rf.value
                    )
            new_doc.required_for = doc_in.required_for.copy()
            return new_doc
    finally:
        await conn.close()


async def get_document(document_id: UUID) -> Optional[DocumentInDB]:
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """SELECT d.*, array_agg(rf.required_for) as required_for
            FROM documents d
            LEFT JOIN documents_required_for rf ON d.id = rf.document_id
            WHERE d.id = $1
            GROUP BY d.id""",
            document_id
        )
        return DocumentInDB(**dict(row)) if row else None
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
                    category = $4,
                    category_id = $5,
                    period_type = $6,
                    periods_required = $7,
                    has_multiple_periods = $8
                WHERE id = $9
                RETURNING *""",
                updated_data.name,
                updated_data.description,
                updated_data.document_type_id,
                updated_data.category.value,
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
                        rf.value
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
        rows = await conn.fetch(
            """SELECT d.*, array_agg(rf.required_for) as required_for
            FROM documents d
            LEFT JOIN documents_required_for rf ON d.id = rf.document_id
            GROUP BY d.id
            ORDER BY d.id"""
        )
        return [DocumentInDB(**dict(row)) for row in rows]
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
            rule.operator.value,
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
