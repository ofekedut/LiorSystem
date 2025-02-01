import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Protocol

logger = logging.getLogger(__name__)


class DocumentProcessor(Protocol):
    """Protocol defining the interface for document processors."""

    def process_document(
            self,
            image_bytes: bytes,
            filename: str,
            preprocess_passes: int,
            language: str
    ) -> Dict[str, Any]:
        ...


class LLMService(Protocol):
    """Protocol defining the interface for LLM services."""
    conversation_history: List[Dict[str, str]]

    def send_for_validation(
            self,
            ocr_text: str,
            extracted_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        ...


class DocumentStorageService:
    """
    A service to process documents via a doc_processor, validate/refine with an LLMService,
    and store results in a local SQLite database.
    """

    def __init__(
            self,
            doc_processor: DocumentProcessor,
            llm_service: LLMService,
            db_path: str = "documents.db"
    ):
        """
        Initialize with dependencies and ensure the SQLite database/table exists.

        Args:
            doc_processor: An instance of a DocumentProcessor-like class
            llm_service: An instance of the LLMService class for AI validation
            db_path: File path to the SQLite database
        """
        self.doc_processor = doc_processor
        self.llm_service = llm_service
        self.db_path = db_path

        # Ensure database is initialized
        self._initialize_db()

    def _initialize_db(self):
        """Create the interactions table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_path TEXT,
                        ocr_text TEXT,
                        validated_data TEXT,
                        conversation_history TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
            logger.info("Database initialized or already exists.")
        except Exception as e:
            logger.error(f"Failed to initialize DB: {e}")

    def process_and_store_document(
            self,
            document_path: str,
            search_values: List[str],
            previous_results: Dict[str, Any],
            ai_messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process a document using the doc_processor, send results to the LLM for validation,
        then store everything in SQLite.

        Args:
            document_path: Path to the document file
            search_values: Values we might search for (optional usage)
            previous_results: Already-known or previously extracted data
            ai_messages: Existing conversation messages

        Returns:
            Dictionary containing OCR output, validated data, and conversation history
        """
        # 1. Read the document bytes
        if not os.path.isfile(document_path):
            logger.error(f"Document not found: {document_path}")
            return {"error": f"File does not exist: {document_path}"}

        with open(document_path, "rb") as f:
            document_bytes = f.read()

        # 2. Update LLM conversation history with the given AI messages
        self.llm_service.conversation_history = ai_messages.copy()

        # 3. Use doc_processor to do OCR
        ocr_result = self.doc_processor.process_document(
            image_bytes=document_bytes,
            filename=document_path,
            preprocess_passes=2,
            language="eng"
        )

        ocr_text = ocr_result.get("text", "")
        logger.info(f"Document OCR text length: {len(ocr_text)}")

        # Combine previous results with any new data
        combined_data = {
            "search_values": search_values,
            **previous_results
        }

        # 4. Send data + OCR text to the LLM for validation
        validated_data = self.llm_service.send_for_validation(
            ocr_text=ocr_text,
            extracted_data=combined_data
        )

        # 5. Store the entire interaction in the database
        self._store_interaction(
            document_path=document_path,
            ocr_text=ocr_text,
            validated_data=validated_data,
            conversation_history=self.llm_service.conversation_history
        )

        # 6. Return a combined result object
        return {
            "ocr_result": ocr_result,
            "validated_data": validated_data,
            "ai_messages": self.llm_service.conversation_history
        }

    def _store_interaction(
            self,
            document_path: str,
            ocr_text: str,
            validated_data: Optional[Dict[str, Any]],
            conversation_history: List[Dict[str, str]]
    ):
        """
        Insert a record of the interaction into the SQLite database.

        Args:
            document_path: Path to the document processed
            ocr_text: OCR text extracted from the document
            validated_data: Data returned by the LLM after validation
            conversation_history: The updated conversation messages
        """
        validated_data_json = json.dumps(validated_data or {}, ensure_ascii=False)
        conversation_json = json.dumps(conversation_history, ensure_ascii=False)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO document_interactions
                    (document_path, ocr_text, validated_data, conversation_history, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document_path,
                        ocr_text,
                        validated_data_json,
                        conversation_json,
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
            logger.info(f"Stored interaction for document: {document_path}")
        except Exception as e:
            logger.error(f"Failed to store document interaction: {e}")

    def list_document_interactions(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = 0,
            filters: Optional[Dict[str, Any]] = None,
            sort_by: str = "created_at",
            sort_order: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve document interactions from the database with filtering and sorting options.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip for pagination
            filters: Dictionary of column:value pairs to filter results
            sort_by: Column name to sort by
            sort_order: Sort direction ('ASC' or 'DESC')

        Returns:
            List of document interaction records as dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM document_interactions"
                params = []

                if filters:
                    where_clauses = []
                    for column, value in filters.items():
                        if column in ["document_path", "ocr_text", "created_at"]:
                            where_clauses.append(f"{column} LIKE ?")
                            params.append(f"%{value}%")

                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)

                allowed_sort_columns = {"id", "document_path", "created_at"}
                if sort_by in allowed_sort_columns:
                    sort_order = "DESC" if sort_order.upper() == "DESC" else "ASC"
                    query += f" ORDER BY {sort_by} {sort_order}"

                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)
                if offset:
                    query += " OFFSET ?"
                    params.append(offset)

                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    if record.get('validated_data'):
                        record['validated_data'] = json.loads(record['validated_data'])
                    if record.get('conversation_history'):
                        record['conversation_history'] = json.loads(
                            record['conversation_history']
                        )
                    results.append(record)

                logger.info(
                    f"Retrieved {len(results)} document interactions "
                    f"(limit={limit}, offset={offset})"
                )
                return results

        except Exception as e:
            logger.error(f"Failed to list document interactions: {e}")
            return []

    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single document interaction by its ID.

        Args:
            document_id: The ID of the document interaction to retrieve

        Returns:
            Dictionary containing the document data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM document_interactions WHERE id = ?",
                    (document_id,)
                )
                row = cursor.fetchone()

                if not row:
                    logger.info(f"Document interaction {document_id} not found")
                    return None

                columns = [desc[0] for desc in cursor.description]
                record = dict(zip(columns, row))

                if record.get('validated_data'):
                    record['validated_data'] = json.loads(record['validated_data'])
                if record.get('conversation_history'):
                    record['conversation_history'] = json.loads(
                        record['conversation_history']
                    )

                logger.info(f"Retrieved document interaction {document_id}")
                return record

        except Exception as e:
            logger.error(f"Failed to retrieve document interaction {document_id}: {e}")
            return None

    def update_document(
            self,
            document_id: int,
            updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing document interaction.

        Args:
            document_id: The ID of the document interaction to update
            updates: Dictionary containing the fields to update and their new values

        Returns:
            Boolean indicating success of the update operation
        """
        try:
            allowed_fields = {
                'document_path', 'ocr_text', 'validated_data',
                'conversation_history'
            }
            update_fields = set(updates.keys()) & allowed_fields

            if not update_fields:
                logger.warning("No valid fields to update")
                return False

            set_clauses = []
            params = []

            for field in update_fields:
                set_clauses.append(f"{field} = ?")
                if field in {'validated_data', 'conversation_history'}:
                    params.append(json.dumps(updates[field], ensure_ascii=False))
                else:
                    params.append(updates[field])

            params.append(document_id)

            query = f"""
                UPDATE document_interactions 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)

                if cursor.rowcount == 0:
                    logger.warning(f"Document interaction {document_id} not found")
                    return False

                conn.commit()
                logger.info(f"Updated document interaction {document_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to update document interaction {document_id}: {e}")
            return False

    def delete_document(self, document_id: int) -> bool:
        """
        Delete a document interaction from the database.

        Args:
            document_id: The ID of the document interaction to delete

        Returns:
            Boolean indicating success of the delete operation
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM document_interactions WHERE id = ?",
                    (document_id,)
                )

                if cursor.rowcount == 0:
                    logger.warning(f"Document interaction {document_id} not found")
                    return False

                conn.commit()
                logger.info(f"Deleted document interaction {document_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete document interaction {document_id}: {e}")
            return False

    def bulk_delete_documents(self, document_ids: List[int]) -> Dict[str, Any]:
        """
        Delete multiple document interactions in a single transaction.

        Args:
            document_ids: List of document interaction IDs to delete

        Returns:
            Dictionary containing success count and failed IDs
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ','.join('?' * len(document_ids))
                cursor.execute(
                    f"DELETE FROM document_interactions WHERE id IN ({placeholders})",
                    document_ids
                )

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"Bulk deleted {deleted_count} document interactions")
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "total_requested": len(document_ids)
                }

        except Exception as e:
            logger.error(f"Failed to bulk delete document interactions: {e}")
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0,
                "total_requested": len(document_ids)
            }

    def search_documents(
            self,
            search_text: str,
            search_fields: Optional[List[str]] = None,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for document interactions across specified fields.

        Args:
            search_text: Text to search for
            search_fields: List of fields to search in (defaults to document_path and ocr_text)
            limit: Maximum number of results to return

        Returns:
            List of matching document interactions
        """
        try:
            allowed_fields = {'document_path', 'ocr_text'}
            if search_fields:
                search_fields = list(set(search_fields) & allowed_fields)
            else:
                search_fields = list(allowed_fields)

            if not search_fields:
                logger.warning("No valid search fields specified")
                return []

            where_clauses = [f"{field} LIKE ?" for field in search_fields]
            query = f"""
                SELECT * FROM document_interactions
                WHERE {' OR '.join(where_clauses)}
                ORDER BY created_at DESC
                LIMIT ?
            """

            params = [f"%{search_text}%"] * len(search_fields) + [limit]

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    if record.get('validated_data'):
                        record['validated_data'] = json.loads(record['validated_data'])
                        if record.get('conversation_history'):
                            record['conversation_history'] = json.loads(
                                record['conversation_history']
                            )
                        results.append(record)

                    logger.info(
                        f"Found {len(results)} documents matching search '{search_text}'"
                    )
                    return results

        except Exception as e:
            logger.error(f"Failed to search document interactions: {e}")
            return []


def get_total_documents(self) -> int:
    """
    Get the total count of documents in the database.

    Returns:
        Total number of document interactions stored
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_interactions")
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Failed to get total document count: {e}")
        return 0


def check_database_health(self) -> Dict[str, Any]:
    """
    Check the health and integrity of the database.

    Returns:
        Dictionary containing database health status and metrics
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            db_size = page_count * page_size

            return {
                "status": "healthy" if integrity == "ok" else "unhealthy",
                "integrity_check": integrity,
                "total_documents": self.get_total_documents(),
                "database_size_bytes": db_size,
                "last_checked": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "last_checked": datetime.now().isoformat()
        }


import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Protocol

logger = logging.getLogger(__name__)


class DocumentProcessor(Protocol):
    """Protocol defining the interface for document processors."""

    def process_document(
            self,
            image_bytes: bytes,
            filename: str,
            preprocess_passes: int,
            language: str
    ) -> Dict[str, Any]:
        ...


class LLMService(Protocol):
    """Protocol defining the interface for LLM services."""
    conversation_history: List[Dict[str, str]]

    def send_for_validation(
            self,
            ocr_text: str,
            extracted_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        ...


class DocumentStorageService:
    """
    A service to process documents via a doc_processor, validate/refine with an LLMService,
    and store results in a local SQLite database.
    """

    def __init__(
            self,
            doc_processor: DocumentProcessor,
            llm_service: LLMService,
            db_path: str = "documents.db"
    ):
        """
        Initialize with dependencies and ensure the SQLite database/table exists.

        Args:
            doc_processor: An instance of a DocumentProcessor-like class
            llm_service: An instance of the LLMService class for AI validation
            db_path: File path to the SQLite database
        """
        self.doc_processor = doc_processor
        self.llm_service = llm_service
        self.db_path = db_path

        # Ensure database is initialized
        self._initialize_db()

    def _initialize_db(self):
        """Create the interactions table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_path TEXT,
                        ocr_text TEXT,
                        validated_data TEXT,
                        conversation_history TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
            logger.info("Database initialized or already exists.")
        except Exception as e:
            logger.error(f"Failed to initialize DB: {e}")

    def process_and_store_document(
            self,
            document_path: str,
            search_values: List[str],
            previous_results: Dict[str, Any],
            ai_messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process a document using the doc_processor, send results to the LLM for validation,
        then store everything in SQLite.

        Args:
            document_path: Path to the document file
            search_values: Values we might search for (optional usage)
            previous_results: Already-known or previously extracted data
            ai_messages: Existing conversation messages

        Returns:
            Dictionary containing OCR output, validated data, and conversation history
        """
        # 1. Read the document bytes
        if not os.path.isfile(document_path):
            logger.error(f"Document not found: {document_path}")
            return {"error": f"File does not exist: {document_path}"}

        with open(document_path, "rb") as f:
            document_bytes = f.read()

        # 2. Update LLM conversation history with the given AI messages
        self.llm_service.conversation_history = ai_messages.copy()

        # 3. Use doc_processor to do OCR
        ocr_result = self.doc_processor.process_document(
            image_bytes=document_bytes,
            filename=document_path,
            preprocess_passes=2,
            language="eng"
        )

        ocr_text = ocr_result.get("text", "")
        logger.info(f"Document OCR text length: {len(ocr_text)}")

        # Combine previous results with any new data
        combined_data = {
            "search_values": search_values,
            **previous_results
        }

        # 4. Send data + OCR text to the LLM for validation
        validated_data = self.llm_service.send_for_validation(
            ocr_text=ocr_text,
            extracted_data=combined_data
        )

        # 5. Store the entire interaction in the database
        self._store_interaction(
            document_path=document_path,
            ocr_text=ocr_text,
            validated_data=validated_data,
            conversation_history=self.llm_service.conversation_history
        )

        # 6. Return a combined result object
        return {
            "ocr_result": ocr_result,
            "validated_data": validated_data,
            "ai_messages": self.llm_service.conversation_history
        }

    def _store_interaction(
            self,
            document_path: str,
            ocr_text: str,
            validated_data: Optional[Dict[str, Any]],
            conversation_history: List[Dict[str, str]]
    ):
        """
        Insert a record of the interaction into the SQLite database.

        Args:
            document_path: Path to the document processed
            ocr_text: OCR text extracted from the document
            validated_data: Data returned by the LLM after validation
            conversation_history: The updated conversation messages
        """
        validated_data_json = json.dumps(validated_data or {}, ensure_ascii=False)
        conversation_json = json.dumps(conversation_history, ensure_ascii=False)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO document_interactions
                    (document_path, ocr_text, validated_data, conversation_history, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document_path,
                        ocr_text,
                        validated_data_json,
                        conversation_json,
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
            logger.info(f"Stored interaction for document: {document_path}")
        except Exception as e:
            logger.error(f"Failed to store document interaction: {e}")

    def list_document_interactions(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = 0,
            filters: Optional[Dict[str, Any]] = None,
            sort_by: str = "created_at",
            sort_order: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve document interactions from the database with filtering and sorting options.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip for pagination
            filters: Dictionary of column:value pairs to filter results
            sort_by: Column name to sort by
            sort_order: Sort direction ('ASC' or 'DESC')

        Returns:
            List of document interaction records as dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM document_interactions"
                params = []

                if filters:
                    where_clauses = []
                    for column, value in filters.items():
                        if column in ["document_path", "ocr_text", "created_at"]:
                            where_clauses.append(f"{column} LIKE ?")
                            params.append(f"%{value}%")

                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)

                allowed_sort_columns = {"id", "document_path", "created_at"}
                if sort_by in allowed_sort_columns:
                    sort_order = "DESC" if sort_order.upper() == "DESC" else "ASC"
                    query += f" ORDER BY {sort_by} {sort_order}"

                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)
                if offset:
                    query += " OFFSET ?"
                    params.append(offset)

                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    if record.get('validated_data'):
                        record['validated_data'] = json.loads(record['validated_data'])
                    if record.get('conversation_history'):
                        record['conversation_history'] = json.loads(
                            record['conversation_history']
                        )
                    results.append(record)

                logger.info(
                    f"Retrieved {len(results)} document interactions "
                    f"(limit={limit}, offset={offset})"
                )
                return results

        except Exception as e:
            logger.error(f"Failed to list document interactions: {e}")
            return []

    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single document interaction by its ID.

        Args:
            document_id: The ID of the document interaction to retrieve

        Returns:
            Dictionary containing the document data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM document_interactions WHERE id = ?",
                    (document_id,)
                )
                row = cursor.fetchone()

                if not row:
                    logger.info(f"Document interaction {document_id} not found")
                    return None

                columns = [desc[0] for desc in cursor.description]
                record = dict(zip(columns, row))

                if record.get('validated_data'):
                    record['validated_data'] = json.loads(record['validated_data'])
                if record.get('conversation_history'):
                    record['conversation_history'] = json.loads(
                        record['conversation_history']
                    )

                logger.info(f"Retrieved document interaction {document_id}")
                return record

        except Exception as e:
            logger.error(f"Failed to retrieve document interaction {document_id}: {e}")
            return None

    def update_document(
            self,
            document_id: int,
            updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing document interaction.

        Args:
            document_id: The ID of the document interaction to update
            updates: Dictionary containing the fields to update and their new values

        Returns:
            Boolean indicating success of the update operation
        """
        try:
            allowed_fields = {
                'document_path', 'ocr_text', 'validated_data',
                'conversation_history'
            }
            update_fields = set(updates.keys()) & allowed_fields

            if not update_fields:
                logger.warning("No valid fields to update")
                return False

            set_clauses = []
            params = []

            for field in update_fields:
                set_clauses.append(f"{field} = ?")
                if field in {'validated_data', 'conversation_history'}:
                    params.append(json.dumps(updates[field], ensure_ascii=False))
                else:
                    params.append(updates[field])

            params.append(document_id)

            query = f"""
                UPDATE document_interactions 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)

                if cursor.rowcount == 0:
                    logger.warning(f"Document interaction {document_id} not found")
                    return False

                conn.commit()
                logger.info(f"Updated document interaction {document_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to update document interaction {document_id}: {e}")
            return False

    def delete_document(self, document_id: int) -> bool:
        """
        Delete a document interaction from the database.

        Args:
            document_id: The ID of the document interaction to delete

        Returns:
            Boolean indicating success of the delete operation
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM document_interactions WHERE id = ?",
                    (document_id,)
                )

                if cursor.rowcount == 0:
                    logger.warning(f"Document interaction {document_id} not found")
                    return False

                conn.commit()
                logger.info(f"Deleted document interaction {document_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete document interaction {document_id}: {e}")
            return False

    def bulk_delete_documents(self, document_ids: List[int]) -> Dict[str, Any]:
        """
        Delete multiple document interactions in a single transaction.

        Args:
            document_ids: List of document interaction IDs to delete

        Returns:
            Dictionary containing success count and failed IDs
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ','.join('?' * len(document_ids))
                cursor.execute(
                    f"DELETE FROM document_interactions WHERE id IN ({placeholders})",
                    document_ids
                )

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"Bulk deleted {deleted_count} document interactions")
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "total_requested": len(document_ids)
                }

        except Exception as e:
            logger.error(f"Failed to bulk delete document interactions: {e}")
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0,
                "total_requested": len(document_ids)
            }

    def search_documents(
            self,
            search_text: str,
            search_fields: Optional[List[str]] = None,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for document interactions across specified fields.

        Args:
            search_text: Text to search for
            search_fields: List of fields to search in (defaults to document_path and ocr_text)
            limit: Maximum number of results to return

        Returns:
            List of matching document interactions
        """
        try:
            allowed_fields = {'document_path', 'ocr_text'}
            if search_fields:
                search_fields = list(set(search_fields) & allowed_fields)
            else:
                search_fields = list(allowed_fields)

            if not search_fields:
                logger.warning("No valid search fields specified")
                return []

            where_clauses = [f"{field} LIKE ?" for field in search_fields]
            query = f"""
                SELECT * FROM document_interactions
                WHERE {' OR '.join(where_clauses)}
                ORDER BY created_at DESC
                LIMIT ?
            """

            params = [f"%{search_text}%"] * len(search_fields) + [limit]

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    if record.get('validated_data'): record['validated_data'] = json.loads(record['validated_data'])
                    if record.get('conversation_history'):
                        record['conversation_history'] = json.loads(
                            record['conversation_history']
                        )
                    results.append(record)

                logger.info(
                    f"Found {len(results)} documents matching search '{search_text}'"
                )
                return results

        except Exception as e:
            logger.error(f"Failed to search document interactions: {e}")
            return []

    def get_total_documents(self) -> int:
        """
        Get the total count of documents in the database.

        Returns:
            Total number of document interactions stored
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM document_interactions")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get total document count: {e}")
            return 0

    def check_database_health(self) -> Dict[str, Any]:
        """
        Check the health and integrity of the database.

        Returns:
            Dictionary containing database health status and metrics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]

                db_size = page_count * page_size

                return {
                    "status": "healthy" if integrity == "ok" else "unhealthy",
                    "integrity_check": integrity,
                    "total_documents": self.get_total_documents(),
                    "database_size_bytes": db_size,
                    "last_checked": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }
