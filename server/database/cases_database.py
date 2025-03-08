# cases_database.py
import enum
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, Field, validator
from server.database.database import get_connection
from server.database.person_roles_database import get_person_role_by_value, get_person_role


class CaseStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"


class PersonRole(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("Person role must be a string")
        role = get_person_role_by_value(v)
        if role is None:
            raise ValueError("Invalid person role")
        return v


class PersonGender(str, enum.Enum):
    male = "male"
    female = "female"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class DocumentProcessingStatus(str, enum.Enum):
    processed = "processed"
    pending = "pending"
    error = "error"
    userActionRequired = "userActionRequired"


class LoanStatus(str, enum.Enum):
    active = "active"
    closed = "closed"
    defaulted = "defaulted"


# =============================================================================
# 2. Pydantic Models
# =============================================================================

# ----------------------------
# 2A. Cases
# ----------------------------
class CaseBase(BaseModel):
    name: str
    status: CaseStatus
    case_purpose: str
    loan_type_id: UUID
    last_active: datetime = Field(default_factory=datetime.utcnow)
    primary_contact_id: Optional[UUID | None] = Field(default=None)


class CaseMondayRelationInCreate(BaseModel):
    monday_id: UUID
    case_id: UUID


class CaseMondayRelationInDB(CaseMondayRelationInCreate):
    id: UUID


class CaseInCreate(CaseBase):
    """
    Model for creating a new case.
    """


class CaseInDB(CaseBase):
    """
    Model representing a case as stored in the database.
    """
    id: UUID
    created_at: datetime
    updated_at: datetime


class CaseUpdate(BaseModel):
    """
    Model for updating an existing case.
    Only includes fields that can be changed.
    """
    name: Optional[str] = None
    status: Optional[CaseStatus] = None
    last_active: Optional[datetime] = None
    case_purpose: str
    loan_type_id: UUID
    primary_contact_id: Optional[UUID] = None


# ----------------------------
# 2B. Case Persons
# ----------------------------
class CasePersonBase(BaseModel):
    first_name: str
    last_name: str
    id_number: str
    gender: PersonGender
    role_id: UUID | str  # Accept either UUID or string
    birth_date: date
    marital_status_id: Optional[UUID] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: str = "active"  # Using string status (must be 'active' or 'inactive')


class CasePersonCreate(CasePersonBase):
    """
    Model for creating a new person record linked to a specific case.
    """
    case_id: UUID


class CasePersonInDB(CasePersonBase):
    """
    Model representing a case person as stored in the database.
    """
    id: UUID
    case_id: UUID
    created_at: datetime
    updated_at: datetime


class CasePersonUpdate(BaseModel):
    """
    Model for updating an existing case person record.
    Only includes fields that can be changed.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    id_number: Optional[str] = None
    gender: Optional[PersonGender] = None
    role_id: Optional[UUID] = None
    marital_status_id: Optional[UUID] = None  # Added marital_status_id field
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None  # Using string status (must be 'active' or 'inactive')


# ----------------------------
# 2C. Case Person Relations
# ----------------------------
class CasePersonRelationBase(BaseModel):
    """
    Represents a relationship between two persons in a single case.
    For example: parent-child, partner, etc.
    """
    from_person_id: UUID
    to_person_id: UUID
    relationship_type_id: UUID


class CasePersonRelationCreate(CasePersonRelationBase):
    """
    Model for creating a new relationship record between two persons.
    """


class CasePersonRelationInDB(CasePersonRelationBase):
    """
    Model representing a person-to-person relationship as stored in the database.
    """
    pass


# ----------------------------
# 2D. Case Documents
# ----------------------------
class CaseDocumentBase(BaseModel):
    """
    Base model for case-document links. Contains common fields across all document operations.
    """
    status: DocumentStatus
    processing_status: DocumentProcessingStatus = DocumentProcessingStatus.pending
    uploaded_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None


class CaseDocumentCreate(CaseDocumentBase):
    """
    Model for creating a new case-document link.
    """
    case_id: UUID
    document_id: UUID


class CaseDocumentInDB(CaseDocumentBase):
    """
    Model representing a case-document link as stored in the database.
    """
    case_id: UUID
    document_id: UUID
    file_path: str | None = None


class CaseDocumentUpdate(BaseModel):
    """
    Model for updating the status or processing information of an existing case-document link.
    """
    status: Optional[str] = None  # Using status_id instead of DocumentStatus enum
    processing_status_id: Optional[int] = None  # Using processing_status_id instead of DocumentProcessingStatus enum
    reviewed_at: Optional[datetime] = None
    file_path: Optional[str] = None


# ----------------------------
# 2E. Case Loans
# ----------------------------
class CaseLoanBase(BaseModel):
    amount: float
    status: str
    start_date: date
    end_date: Optional[date] = None


class CaseLoanCreate(CaseLoanBase):
    """
    Model for creating a new loan record linked to a specific case.
    """
    case_id: UUID


class CaseLoanInDB(CaseLoanBase):
    """
    Model representing a case loan as stored in the database.
    """
    id: UUID
    case_id: UUID
    created_at: datetime
    updated_at: datetime


class CaseLoanUpdate(BaseModel):
    """
    Model for updating fields of an existing case loan record.
    """
    amount: Optional[float] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ----------------------------
# 2F. Case Person Documents
# ----------------------------
class CasePersonDocumentBase(BaseModel):
    """
    Base model for case_person_documents junction table.
    """
    is_primary: bool = False


class CasePersonDocumentCreate(CasePersonDocumentBase):
    """
    Model for creating a new person-document link within a case.
    """
    case_id: UUID
    person_id: UUID
    document_id: UUID


class CasePersonDocumentInDB(CasePersonDocumentBase):
    """
    Model representing a person-document link as stored in the database.
    """
    case_id: UUID
    person_id: UUID
    document_id: UUID
    created_at: datetime


class CasePersonDocumentUpdate(BaseModel):
    """
    Model for updating a person-document link.
    """
    is_primary: Optional[bool] = None


# =============================================================================
# 3. CRUD Operations
# =============================================================================

# ----------------------------
# 3A. Cases
# ----------------------------
async def create_case(case_in: CaseInCreate) -> CaseInDB:
    """
    Create a new case record.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO cases (name, status,  last_active,case_purpose, loan_type_id, primary_contact_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                case_in.name,
                case_in.status,
                case_in.last_active,
                case_in.case_purpose,
                case_in.loan_type_id,
                None,
            )
            return CaseInDB(**dict(row))
    finally:
        await conn.close()


async def create_case_monday_relation(case_relation_in: CaseMondayRelationInCreate) -> CaseInDB:
    """
    Create a new case record.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO cases_monday_relation (
                case_id, monday_id)
                VALUES ($1, $2)
                RETURNING *
                """,
                case_relation_in.case_id,
                case_relation_in.monday_id,
            )
            return CaseMondayRelationInDB(**dict(row))
    finally:
        await conn.close()


async def get_case(case_id: UUID) -> Optional[CaseInDB]:
    """
    Retrieve a single case by its UUID.
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM cases WHERE id = $1", case_id)
        return CaseInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def update_case(case_id: UUID, case_update: CaseUpdate) -> Optional[CaseInDB]:
    """
    Update an existing case record.
    """
    existing = await get_case(case_id)
    if not existing:
        return None

    updated_data = existing.copy(update=case_update.dict(exclude_unset=True))
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE cases
                SET name = $1,
                    status = $2,
                    case_purpose = $3,
                    last_active = $4,
                    loan_type_id = $5,
                    updated_at = NOW(),
                    primary_contact_id = $6
                WHERE id = $7
                RETURNING *
                """,
                updated_data.name,
                updated_data.status,
                updated_data.case_purpose,
                updated_data.last_active,
                updated_data.loan_type_id,
                updated_data.primary_contact_id,
                case_id,
            )
            return CaseInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def delete_case(case_id: UUID) -> bool:
    """
    Delete a case record by its UUID.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute("DELETE FROM cases WHERE id = $1", case_id)
            return "DELETE 1" in result
    finally:
        await conn.close()


async def list_cases() -> List[CaseInDB]:
    """
    Retrieve all cases, ordered by creation date descending.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM cases ORDER BY created_at DESC")
        return [CaseInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


# ----------------------------
# 3B. Case Persons
# ----------------------------
async def create_case_person(person_in: CasePersonCreate) -> CasePersonInDB:
    """
    Create a new person record tied to a specific case.
    """
    # Use the role_id directly from the input
    # The role_id is already validated by the Pydantic model

    query = """
    INSERT INTO case_persons (
        case_id, first_name, last_name, id_number, gender, 
         role_id, birth_date, marital_status_id, phone, email, status
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    RETURNING 
        id, case_id, first_name, last_name, id_number, gender, 
        role_id, birth_date, marital_status_id, phone, email, status, created_at, updated_at
    """
    values = [
        person_in.case_id,
        person_in.first_name,
        person_in.last_name,
        person_in.id_number,
        person_in.gender.value,
        person_in.role_id,
        person_in.birth_date,
        person_in.marital_status_id,
        person_in.phone,
        person_in.email,
        person_in.status
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return CasePersonInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_case_person(person_id: UUID) -> Optional[CasePersonInDB]:
    """
    Retrieve a single case person record by its UUID.
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM case_persons WHERE id = $1", person_id)
        return CasePersonInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def list_case_persons(case_id: UUID) -> List[CasePersonInDB]:
    """
    Retrieve all persons associated with a specific case.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM case_persons WHERE case_id = $1", case_id)
        return [CasePersonInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_case_person(person_id: UUID, person_update: CasePersonUpdate) -> CasePersonInDB:
    """
    Update an existing case person record by ID.
    """
    # Validate role if provided
    role_obj = None

    if person_update.role_id is not None:
        role_obj = await get_person_role(str(person_update.role_id))
        if not role_obj:
            raise ValueError(f"Invalid person role: {person_update.role_id}")

    # Get current data
    current_person = await get_case_person(person_id)
    if not current_person:
        return None

    # Build update query dynamically
    update_parts = []
    values = [person_id]  # First param is always the ID
    param_index = 2

    # For each field in the update model, add it to the query if it's not None
    if person_update.first_name is not None:
        update_parts.append(f"first_name = ${param_index}")
        values.append(person_update.first_name)
        param_index += 1

    if person_update.last_name is not None:
        update_parts.append(f"last_name = ${param_index}")
        values.append(person_update.last_name)
        param_index += 1

    if person_update.id_number is not None:
        update_parts.append(f"id_number = ${param_index}")
        values.append(person_update.id_number)
        param_index += 1

    if person_update.gender is not None:
        update_parts.append(f"gender = ${param_index}")
        values.append(person_update.gender.value)
        param_index += 1

    if person_update.role_id is not None:
        update_parts.append(f"role_id = ${param_index}")
        values.append(role_obj.id)
        param_index += 1

    if person_update.birth_date is not None:
        update_parts.append(f"birth_date = ${param_index}")
        values.append(person_update.birth_date)
        param_index += 1

    if person_update.marital_status_id is not None:
        update_parts.append(f"marital_status_id = ${param_index}")
        values.append(person_update.marital_status_id)
        param_index += 1

    if person_update.phone is not None:
        update_parts.append(f"phone = ${param_index}")
        values.append(person_update.phone)
        param_index += 1

    if person_update.email is not None:
        update_parts.append(f"email = ${param_index}")
        values.append(person_update.email)
        param_index += 1

    if person_update.status is not None:
        update_parts.append(f"status = ${param_index}")
        values.append(person_update.status)
        param_index += 1

    # If nothing to update, return the current data
    if not update_parts:
        return current_person

    # Build the final query
    update_clause = ", ".join(update_parts)
    query = f"""
    UPDATE case_persons
    SET {update_clause}, updated_at = NOW()
    WHERE id = $1
    RETURNING 
        id, case_id, first_name, last_name, id_number, gender, 
         role_id, birth_date, marital_status_id, phone, email, status, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return CasePersonInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_case_person(person_id: UUID) -> bool:
    """
    Delete a case person record by its UUID.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute("DELETE FROM case_persons WHERE id = $1", person_id)
            return "DELETE 1" in result
    finally:
        await conn.close()


# ----------------------------
# 3C. Case Person Relations
# ----------------------------
async def create_person_relation(rel_in: CasePersonRelationCreate) -> CasePersonRelationInDB:
    """
    Create a relationship record between two persons in the same case.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO case_person_relations (from_person_id, to_person_id, relationship_type_id)
                VALUES ($1, $2, $3)
                """,
                rel_in.from_person_id,
                rel_in.to_person_id,
                rel_in.relationship_type_id,
            )
            return CasePersonRelationInDB(**rel_in.dict())
    finally:
        await conn.close()


async def list_person_relations(person_id: UUID) -> List[CasePersonRelationInDB]:
    """
    List all person-to-person relationships where the given person is either the source or target.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT *
            FROM case_person_relations
            WHERE from_person_id = $1
               OR to_person_id = $1
            """,
            person_id,
        )
        return [CasePersonRelationInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def delete_person_relation(from_person_id: UUID, to_person_id: UUID) -> bool:
    """
    Delete a specific relationship record by the two person IDs.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute(
                """
                DELETE FROM case_person_relations
                WHERE from_person_id = $1
                  AND to_person_id = $2
                """,
                from_person_id,
                to_person_id,
            )
            return "DELETE 1" in result
    finally:
        await conn.close()


# ----------------------------
# 3D. Case Documents
# ----------------------------
async def create_case_document(doc_in: CaseDocumentCreate) -> CaseDocumentInDB:
    """
    Create a link between a case and a document, representing a specific document needed or provided.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO case_documents (
                    case_id, document_id, status, processing_status, uploaded_at, reviewed_at
                )
                VALUES ($1, $2, $3, $4, COALESCE($5, NOW()), $6)
                RETURNING *
                """,
                doc_in.case_id,
                doc_in.document_id,
                doc_in.status,
                doc_in.processing_status,
                doc_in.uploaded_at,
                doc_in.reviewed_at,
            )
            return CaseDocumentInDB(**dict(row))
    finally:
        await conn.close()


async def get_case_document(case_id: UUID, document_id: UUID) -> Optional[CaseDocumentInDB]:
    """
    Retrieve the link record for a specific document in a specific case.
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM case_documents
            WHERE case_id = $1
              AND document_id = $2
            """,
            case_id,
            document_id,
        )
        return CaseDocumentInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def list_case_documents(case_id: UUID) -> List[CaseDocumentInDB]:
    """
    List all documents linked to a particular case.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM case_documents WHERE case_id = $1", case_id)
        return [CaseDocumentInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_case_document(case_id: UUID, document_id: UUID, doc_update: CaseDocumentUpdate) -> Optional[CaseDocumentInDB]:
    """
    Update the status, processing info, or file_path of an existing case-document link.
    """
    existing = await get_case_document(case_id, document_id)
    if not existing:
        return None

    updated_data = existing.copy(update=doc_update.dict(exclude_unset=True))
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE case_documents
                SET 
                    status            = $1,
                    processing_status = $2,
                    reviewed_at       = $3 ,
                    file_path         = $4      -- We want to set it exactly, even if it's None
                WHERE case_id = $5
                  AND document_id = $6
                RETURNING *
                """,
                updated_data.status,
                updated_data.processing_status,
                updated_data.reviewed_at,
                updated_data.file_path,
                case_id,
                document_id,
            )
            return CaseDocumentInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def delete_case_document(case_id: UUID, document_id: UUID) -> bool:
    """
    Delete the link record between a case and a document.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute(
                """
                DELETE FROM case_documents
                WHERE case_id = $1
                  AND document_id = $2
                """,
                case_id,
                document_id,
            )
            return "DELETE 1" in result
    finally:
        await conn.close()


# ----------------------------
# 3E. Case Loans
# ----------------------------
async def create_case_loan(loan_in: CaseLoanCreate) -> CaseLoanInDB:
    """
    Create a new loan record tied to a specific case.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO case_loans (
                    case_id, amount, status, start_date, end_date
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                loan_in.case_id,
                loan_in.amount,
                loan_in.status,
                loan_in.start_date,
                loan_in.end_date,
            )
            return CaseLoanInDB(**dict(row))
    finally:
        await conn.close()


async def get_case_loan(loan_id: UUID) -> Optional[CaseLoanInDB]:
    """
    Retrieve a single case loan by its UUID.
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM case_loans WHERE id = $1", loan_id)
        return CaseLoanInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def list_case_loans(case_id: UUID) -> List[CaseLoanInDB]:
    """
    List all loans associated with a specific case.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM case_loans WHERE case_id = $1", case_id)
        return [CaseLoanInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_case_loan(loan_id: UUID, loan_update: CaseLoanUpdate) -> Optional[CaseLoanInDB]:
    """
    Update fields of an existing case loan record.
    """
    existing = await get_case_loan(loan_id)
    if not existing:
        return None

    updated_data = existing.copy(update=loan_update.dict(exclude_unset=True))
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE case_loans
                SET amount = $1,
                    status = $2,
                    start_date = $3,
                    end_date = $4,
                    updated_at = NOW()
                WHERE id = $5
                RETURNING *
                """,
                updated_data.amount,
                updated_data.status,
                updated_data.start_date,
                updated_data.end_date,
                loan_id,
            )
            return CaseLoanInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def delete_case_loan(loan_id: UUID) -> bool:
    """
    Delete a case loan record by its UUID.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute("DELETE FROM case_loans WHERE id = $1", loan_id)
            return "DELETE 1" in result
    finally:
        await conn.close()


# ----------------------------
# 3F. Case Person Documents
# ----------------------------
async def create_case_person_document(doc_in: CasePersonDocumentCreate) -> CasePersonDocumentInDB:
    """
    Create a link between a person and a document within a case context.
    """
    conn = await get_connection()
    try:
        # Verify that the person is associated with the case
        person_exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM case_persons 
                WHERE id = $1 AND case_id = $2
            )
            """,
            doc_in.person_id, doc_in.case_id
        )

        if not person_exists:
            raise ValueError("Person is not associated with the specified case")

        # Verify that the document exists
        document_exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM documents 
                WHERE id = $1
            )
            """,
            doc_in.document_id
        )

        if not document_exists:
            raise ValueError("Document does not exist")

        # Insert the record with the specified attributes
        record = await conn.fetchrow(
            """
            INSERT INTO case_person_documents 
            (case_id, person_id, document_id, is_primary) 
            VALUES ($1, $2, $3, $4)
            RETURNING case_id, person_id, document_id, is_primary, created_at
            """,
            doc_in.case_id, doc_in.person_id, doc_in.document_id, doc_in.is_primary
        )

        # Return the created record
        return CasePersonDocumentInDB(
            case_id=record["case_id"],
            person_id=record["person_id"],
            document_id=record["document_id"],
            is_primary=record["is_primary"],
            created_at=record["created_at"]
        )
    finally:
        await conn.close()


async def get_case_person_document(case_id: UUID, person_id: UUID, document_id: UUID) -> CasePersonDocumentInDB:
    """
    Retrieve the specific link between a person and a document within a case.
    """
    conn = await get_connection()
    try:
        record = await conn.fetchrow(
            """
            SELECT * FROM case_person_documents
            WHERE case_id = $1 AND person_id = $2 AND document_id = $3
            """,
            case_id, person_id, document_id
        )

        if not record:
            raise ValueError(f"No document found for person {person_id} in case {case_id} with document ID {document_id}")

        return CasePersonDocumentInDB(
            case_id=record["case_id"],
            person_id=record["person_id"],
            document_id=record["document_id"],
            is_primary=record["is_primary"],
            created_at=record["created_at"]
        )
    finally:
        await conn.close()


async def list_case_person_documents(case_id: UUID, person_id: UUID) -> List[CasePersonDocumentInDB]:
    """
    List all documents linked to a specific person within a case.
    """
    conn = await get_connection()
    try:
        records = await conn.fetch(
            """
            SELECT * FROM case_person_documents
            WHERE case_id = $1 AND person_id = $2
            """,
            case_id, person_id
        )

        return [
            CasePersonDocumentInDB(
                case_id=record["case_id"],
                person_id=record["person_id"],
                document_id=record["document_id"],
                is_primary=record["is_primary"],
                created_at=record["created_at"]
            )
            for record in records
        ]
    finally:
        await conn.close()


async def update_case_person_document(
        case_id: UUID,
        person_id: UUID,
        document_id: UUID,
        doc_update: CasePersonDocumentUpdate
) -> CasePersonDocumentInDB:
    """
    Update a person-document link within a case.
    """
    conn = await get_connection()
    try:
        # Check if the record exists
        record = await conn.fetchrow(
            """
            SELECT * FROM case_person_documents
            WHERE case_id = $1 AND person_id = $2 AND document_id = $3
            """,
            case_id, person_id, document_id
        )

        if not record:
            raise ValueError(f"No document found for person {person_id} in case {case_id} with document ID {document_id}")

        # Prepare update values
        update_fields = []
        update_values = []

        if doc_update.is_primary is not None:
            update_fields.append("is_primary = $" + str(len(update_values) + 4))
            update_values.append(doc_update.is_primary)

        # If there's nothing to update, return the existing record
        if not update_fields:
            return CasePersonDocumentInDB(
                case_id=record["case_id"],
                person_id=record["person_id"],
                document_id=record["document_id"],
                is_primary=record["is_primary"],
                created_at=record["created_at"]
            )

        # Build the update query
        query = f"""
            UPDATE case_person_documents
            SET {', '.join(update_fields)}
            WHERE case_id = $1 AND person_id = $2 AND document_id = $3
            RETURNING *
        """

        # Execute the update
        updated = await conn.fetchrow(
            query,
            case_id, person_id, document_id, *update_values
        )

        return CasePersonDocumentInDB(
            case_id=updated["case_id"],
            person_id=updated["person_id"],
            document_id=updated["document_id"],
            is_primary=updated["is_primary"],
            created_at=updated["created_at"]
        )
    finally:
        await conn.close()


async def delete_case_person_document(case_id: UUID, person_id: UUID, document_id: UUID) -> bool:
    """
    Delete a person-document link within a case.
    """
    conn = await get_connection()
    try:
        result = await conn.execute(
            """
            DELETE FROM case_person_documents
            WHERE case_id = $1 AND person_id = $2 AND document_id = $3
            """,
            case_id, person_id, document_id
        )

        # Check if a record was deleted
        return result and "DELETE 1" in result
    finally:
        await conn.close()
