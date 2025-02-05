# processing_service.py
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import json

from pydantic import BaseModel
from server.database.database import get_connection


# =============================================================================
# 1. Pydantic Models
# =============================================================================

class ProcessingStateBase(BaseModel):
    case_id: UUID
    document_id: UUID
    step_name: str
    state: str  # e.g., 'pending', 'in_progress', 'completed', 'failed'
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingStateCreate(ProcessingStateBase):
    pass


class ProcessingStateInDB(ProcessingStateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ProcessingStepResultBase(BaseModel):
    processing_state_id: UUID
    result: Dict[str, Any]  # JSON result
    # `embedding_prop` might be a list[float] or None if you want to handle it in Python
    # but if you store it as a vector in Postgres, pass it as list[float] to be inserted/updated
    embedding_prop: Optional[List[float]] = None


class ProcessingStepResultCreate(ProcessingStepResultBase):
    pass


class ProcessingStepResultInDB(ProcessingStepResultBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class PendingProcessingDocumentBase(BaseModel):
    case_id: UUID
    document_id: UUID
    status: str = "pending"  # 'pending', 'processing', 'completed'
    submitted_at: Optional[datetime] = None


class PendingProcessingDocumentCreate(PendingProcessingDocumentBase):
    pass


class PendingProcessingDocumentInDB(PendingProcessingDocumentBase):
    id: UUID
    submitted_at: datetime
    updated_at: datetime


# =============================================================================
# 2. CRUD / Service Functions
# =============================================================================

# ----------------------------
# 2A. ProcessingStates
# ----------------------------

async def create_processing_state(state_in: ProcessingStateCreate) -> ProcessingStateInDB:
    """
    Insert a new record into processing_states.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO processing_states (
                    case_id, document_id, step_name,
                    state, message, started_at, completed_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                state_in.case_id,
                state_in.document_id,
                state_in.step_name,
                state_in.state,
                state_in.message,
                state_in.started_at,
                state_in.completed_at
            )
            return ProcessingStateInDB(**dict(row))
    finally:
        await conn.close()


async def get_processing_state(state_id: UUID) -> Optional[ProcessingStateInDB]:
    """
    Retrieve a single processing_state record by ID.
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM processing_states WHERE id = $1", state_id)
        return ProcessingStateInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def update_processing_state(state_id: UUID, updates: Dict[str, Any]) -> Optional[ProcessingStateInDB]:
    """
    Partially update a processing_state record.
    """
    existing = await get_processing_state(state_id)
    if not existing:
        return None

    # Merge the updates with existing data
    data = existing.dict()
    data.update({k: v for k, v in updates.items() if v is not None})

    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE processing_states
                SET state = $1,
                    message = $2,
                    started_at = $3,
                    completed_at = $4,
                    updated_at = NOW()
                WHERE id = $5
                RETURNING *
                """,
                data["state"],
                data["message"],
                data["started_at"],
                data["completed_at"],
                state_id
            )
            return ProcessingStateInDB(**dict(row)) if row else None
    finally:
        await conn.close()


# ----------------------------
# 2B. ProcessingStepResults
# ----------------------------

async def create_processing_step_result(
        result_in: ProcessingStepResultCreate
) -> ProcessingStepResultInDB:
    """
    Insert a new record into processing_step_results.
    If storing embeddings as vector, ensure you handle conversion properly.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            # Convert Python list to Postgres vector literal if using vector columns
            # e.g., embeddings -> `'[1.0,2.0,3.0]'::vector`
            embedding_literal = None
            if result_in.embedding_prop is not None:
                # Convert to `'[x,y,z]'` format
                embedding_literal = "[" + ",".join(str(x) for x in result_in.embedding_prop) + "]"

            row = await conn.fetchrow(
                f"""
                INSERT INTO processing_step_results (
                    processing_state_id, result, embedding_prop
                )
                VALUES ($1, $2, {f"'{embedding_literal}'" if embedding_literal else "NULL"} )
                RETURNING *;
                """,
                result_in.processing_state_id,
                json.dumps(result_in.result)
            )
            return ProcessingStepResultInDB(
                **dict(row),
                # If embedding_prop is stored as vector, re-convert it or set None
                # e.g., embedding_prop=row["embedding_prop"]
            )
    finally:
        await conn.close()


async def get_processing_step_result(state_id: UUID) -> Optional[ProcessingStepResultInDB]:
    """
    Retrieve the processing_step_result by state ID (1-to-1 relationship).
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM processing_step_results WHERE processing_state_id = $1", state_id)
        return ProcessingStepResultInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def update_processing_step_result(
        state_id: UUID,
        updates: Dict[str, Any]
) -> Optional[ProcessingStepResultInDB]:
    """
    Update the result record, including embedding if needed.
    """
    existing = await get_processing_step_result(state_id)
    if not existing:
        return None

    data = existing.dict()
    data.update({k: v for k, v in updates.items() if v is not None})

    # Convert embedding if present
    embedding_literal = None
    if data.get("embedding_prop") is not None:
        emb_list = data["embedding_prop"]
        embedding_literal = "[" + ",".join(str(x) for x in emb_list) + "]"

    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                f"""
                UPDATE processing_step_results
                SET result = $1,
                    embedding_prop = {f"'{embedding_literal}'" if embedding_literal else "NULL"},
                    updated_at = NOW()
                WHERE processing_state_id = $2
                RETURNING *
                """,
                json.dumps(data["result"]),
                state_id
            )
            return ProcessingStepResultInDB(**dict(row)) if row else None
    finally:
        await conn.close()


# ----------------------------
# 2C. PendingProcessingDocuments
# ----------------------------

async def create_pending_document(
        doc_in: PendingProcessingDocumentCreate
) -> PendingProcessingDocumentInDB:
    """
    Insert a record into pending_processing_documents.
    """
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO pending_processing_documents (
                    case_id, document_id, status, submitted_at
                )
                VALUES ($1, $2, $3, COALESCE($4, NOW()))
                RETURNING *
                """,
                doc_in.case_id,
                doc_in.document_id,
                doc_in.status,
                doc_in.submitted_at
            )
            return PendingProcessingDocumentInDB(**dict(row))
    finally:
        await conn.close()


async def get_pending_document(doc_id: UUID) -> Optional[PendingProcessingDocumentInDB]:
    """
    Retrieve a single record from pending_processing_documents by its primary key.
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM pending_processing_documents WHERE id = $1",
            doc_id
        )
        return PendingProcessingDocumentInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def update_pending_document(
        doc_id: UUID,
        updates: Dict[str, Any]
) -> Optional[PendingProcessingDocumentInDB]:
    """
    Partially update a pending processing document.
    """
    existing = await get_pending_document(doc_id)
    if not existing:
        return None

    data = existing.dict()
    data.update({k: v for k, v in updates.items() if v is not None})

    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE pending_processing_documents
                SET status = $1,
                    updated_at = NOW()
                WHERE id = $2
                RETURNING *
                """,
                data["status"],
                doc_id
            )
            return PendingProcessingDocumentInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def list_pending_documents(case_id: UUID) -> List[PendingProcessingDocumentInDB]:
    """
    List all pending documents for a given case.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM pending_processing_documents WHERE case_id = $1",
            case_id
        )
        return [PendingProcessingDocumentInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()
