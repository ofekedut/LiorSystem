# cases_router_test.py

import uuid
import pytest
import pytest_asyncio
from datetime import datetime, date
from httpx import AsyncClient
from fastapi import status
from pathlib import Path
from server.database.database import get_connection

# Import your main FastAPI app that includes the cases_router.
# Adjust the import below to match your project's structure.
from server.api import app


# Sample fixture that might create a "documents" row if you need real doc references.
# If you want to skip testing case_documents foreign-key constraints, you can omit this.
@pytest_asyncio.fixture
async def seeded_document():
    """
    Creates an entry in the 'documents' table so that case_documents can reference it.
    Adjust the fields as needed for your 'documents' schema.
    """
    # First, create or get a document type
    conn = await get_connection()
    try:
        # Try to get existing document type
        doc_type_name = "One Time"
        doc_type_value = "one-time"

        existing = await conn.fetchrow(
            """SELECT id FROM document_types WHERE name = $1""",
            doc_type_name
        )

        if existing:
            doc_type_id = existing['id']
        else:
            # Create a new document type
            doc_type = await conn.fetchrow(
                """INSERT INTO document_types (name, value) 
                   VALUES ($1, $2) 
                   RETURNING id""",
                doc_type_name, doc_type_value
            )
            doc_type_id = doc_type['id']
    finally:
        await conn.close()

    # Now create the document with the document_type_id
    from server.database.documents_database import create_document, DocumentInCreate, RequiredFor
    import uuid
    unique_doc_name = f"Router_Test_Doc_{uuid.uuid4()}"
    doc_data = DocumentInCreate(
        name=unique_doc_name,
        description="Used for case_documents foreign key tests",
        document_type_id=doc_type_id,  # Use the UUID from the document_types table
        category='tax',
        period_type=None,
        periods_required=None,
        has_multiple_periods=False,
        required_for=[],
    )
    doc_in_db = await create_document(doc_data)
    return doc_in_db


@pytest_asyncio.fixture
async def async_client():
    """
    Provides an async HTTP client for testing FastAPI endpoints.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


# =============================================================================
# Tests for Cases
# =============================================================================

@pytest.mark.asyncio
class TestCasesRouter:
    @pytest.fixture
    def new_case_payload(self, created_loan_type):
        return {
            "name": "Test Case Router",
            "status": "pending",
            "last_active": datetime.utcnow().isoformat(),
            "case_purpose": "Testing case purpose",
            "loan_type_id": str(created_loan_type['id'])
        }

    async def test_create_case(self, async_client: AsyncClient, new_case_payload: dict):
        response = await async_client.post("/cases", json=new_case_payload)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "id" in data
        assert data["name"] == new_case_payload["name"]

    async def test_list_cases(self, async_client: AsyncClient, new_case_payload: dict):
        # Create a case first
        await async_client.post("/cases", json=new_case_payload)
        # List
        resp = await async_client.get("/cases")
        assert resp.status_code == status.HTTP_200_OK

        cases_list = resp.json()
        assert isinstance(cases_list, list)
        assert len(cases_list) >= 1

    async def test_get_case_valid_id(self, async_client: AsyncClient, new_case_payload: dict):
        # Create
        create_resp = await async_client.post("/cases", json=new_case_payload)
        case_id = create_resp.json()["id"]
        # Get
        get_resp = await async_client.get(f"/cases/{case_id}")
        assert get_resp.status_code == status.HTTP_200_OK

        data = get_resp.json()
        assert data["id"] == case_id

    async def test_get_case_invalid_id(self, async_client: AsyncClient):
        bad_id = uuid.uuid4()
        resp = await async_client.get(f"/cases/{bad_id}")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_case(self, async_client: AsyncClient, new_case_payload: dict, created_loan_type):
        # Create
        create_resp = await async_client.post("/cases", json=new_case_payload, )
        created = create_resp.json()
        case_id = created["id"]

        update_payload = {
            "name": "Updated Router Case",
            "status": "active",
            'loan_type_id': str(created_loan_type['id']),
            'case_purpose': 'Testing case purpose',
        }
        update_resp = await async_client.put(f"/cases/{case_id}", json=update_payload)
        assert update_resp.status_code == status.HTTP_200_OK

        updated = update_resp.json()
        assert updated["name"] == "Updated Router Case"
        assert updated["status"] == "active"
        assert str(updated['loan_type_id']) == str(created_loan_type['id'])
        assert updated['case_purpose'] == 'Testing case purpose'

    async def test_delete_case(self, async_client: AsyncClient, new_case_payload: dict):
        # Create
        create_resp = await async_client.post("/cases", json=new_case_payload)
        case_id = create_resp.json()["id"]

        # Delete
        del_resp = await async_client.delete(f"/cases/{case_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        # Verify
        get_resp = await async_client.get(f"/cases/{case_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Tests for Case Persons
# =============================================================================

@pytest.mark.asyncio
class TestCasePersonsRouter:
    @pytest_asyncio.fixture
    async def created_case_id(self, async_client: AsyncClient, created_loan_type):
        payload = {
            "name": "Case for Persons",
            "status": "pending",
            "activity_level": 10,
            "last_active": datetime.utcnow().isoformat(),
            "project_count": 1,
            "case_purpose": "Purpose for Persons",
            "loan_type_id": str(created_loan_type['id'])
        }
        resp = await async_client.post("/cases", json=payload)
        return resp.json()["id"]

    @pytest.fixture
    def new_person_payload(self, created_case_id, created_role):
        return {
            "case_id": created_case_id,
            "first_name": "Alice",
            "last_name": "Example",
            "id_number": str(uuid.uuid4())[:8],
            "age": 30,
            "gender": "female",
            "role_id": str(created_role.id),
            "birth_date": date(1990, 1, 1).isoformat(),
            "phone": "+123456789",
            "email": "alice@example.com",
            "status": "active"
        }

    async def test_create_person_for_case(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_person_payload: dict
    ):
        url = f"/cases/{created_case_id}/persons"
        resp = await async_client.post(url, json=new_person_payload)
        assert resp.status_code == status.HTTP_201_CREATED

        data = resp.json()
        assert data["id"] is not None
        assert data["case_id"] == str(created_case_id)

    async def test_list_case_persons(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_person_payload: dict
    ):
        # Create person
        await async_client.post(f"/cases/{created_case_id}/persons", json=new_person_payload)

        # List
        resp = await async_client.get(f"/cases/{created_case_id}/persons")
        assert resp.status_code == status.HTTP_200_OK
        persons_list = resp.json()
        assert len(persons_list) >= 1

    async def test_get_case_person_valid_id(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_person_payload: dict
    ):
        # Create person
        create_resp = await async_client.post(f"/cases/{created_case_id}/persons", json=new_person_payload)
        person_id = create_resp.json()["id"]

        # Get
        get_resp = await async_client.get(f"/persons/{person_id}")
        assert get_resp.status_code == status.HTTP_200_OK
        data = get_resp.json()
        assert data["id"] == person_id

    async def test_get_case_person_invalid_id(self, async_client: AsyncClient):
        bad_id = uuid.uuid4()
        resp = await async_client.get(f"/persons/{bad_id}")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_case_person(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_person_payload: dict
    ):
        # Create person
        create_resp = await async_client.post(f"/cases/{created_case_id}/persons", json=new_person_payload)
        person_id = create_resp.json()["id"]

        update_payload = {
            "phone": "+999999999",
            "role": "guarantor"
        }
        update_resp = await async_client.put(f"/persons/{person_id}", json=update_payload)
        assert update_resp.status_code == status.HTTP_200_OK

        data = update_resp.json()
        assert data["phone"] == "+999999999"

    async def test_delete_case_person(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_person_payload: dict
    ):
        # Create person
        create_resp = await async_client.post(f"/cases/{created_case_id}/persons", json=new_person_payload)
        person_id = create_resp.json()["id"]

        # Delete
        del_resp = await async_client.delete(f"/persons/{person_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        # Verify
        get_resp = await async_client.get(f"/persons/{person_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Tests for Case Documents
# =============================================================================

@pytest.mark.asyncio
class TestCaseDocumentsRouter:
    @pytest_asyncio.fixture
    async def created_case_id(self, async_client: AsyncClient, created_loan_type):
        payload = {
            "name": "Case for Documents",
            "status": "pending",
            "last_active": datetime.utcnow().isoformat(),
            "case_purpose": "Purpose for Documents",
            "loan_type_id": str(created_loan_type['id'])
        }
        resp = await async_client.post("/cases", json=payload)
        return resp.json()["id"]

    @pytest_asyncio.fixture
    async def seeded_doc_id(self, seeded_document):
        """
        This uses the fixture that inserts a row into 'documents' table and returns its ID.
        """
        return seeded_document.id  # Or however your doc_in_db is structured

    @pytest.fixture
    def case_document_payload(self, created_case_id, seeded_doc_id):
        return {
            "case_id": created_case_id,
            "document_id": str(seeded_doc_id),  # ensure it's string for JSON
            "status": "pending",
            "processing_status": "pending"
        }

    async def test_create_case_document(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, case_document_payload: dict
    ):
        # POST /cases/{case_id}/documents
        resp = await async_client.post(f"/cases/{created_case_id}/documents", json=case_document_payload)
        assert resp.status_code == status.HTTP_201_CREATED

        data = resp.json()
        assert data["case_id"] == str(created_case_id)
        assert data["document_id"] == case_document_payload["document_id"]

    async def test_list_case_documents(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, case_document_payload: dict
    ):
        # Create
        await async_client.post(f"/cases/{created_case_id}/documents", json=case_document_payload)

        # List
        resp = await async_client.get(f"/cases/{created_case_id}/documents")
        assert resp.status_code == status.HTTP_200_OK
        docs_list = resp.json()
        assert len(docs_list) >= 1

    async def test_update_case_document(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, case_document_payload: dict
    ):
        create_resp = await async_client.post(f"/cases/{created_case_id}/documents", json=case_document_payload)
        doc_link = create_resp.json()
        document_id = doc_link["document_id"]

        update_payload = {
            "status": "approved",
            "processing_status_id": 1  # 1 corresponds to 'processed' in the enum
        }
        update_resp = await async_client.put(
            f"/cases/{created_case_id}/documents/{document_id}",
            json=update_payload
        )
        assert update_resp.status_code == status.HTTP_200_OK
        updated = update_resp.json()
        assert updated["status"] == "approved"
        # Verify the processing_status in the response matches what we expect
        assert updated["processing_status"] == "processed"

    async def test_delete_case_document(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, case_document_payload: dict
    ):
        create_resp = await async_client.post(f"/cases/{created_case_id}/documents", json=case_document_payload)
        document_id = create_resp.json()["document_id"]

        del_resp = await async_client.delete(f"/cases/{created_case_id}/documents/{document_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        # Verify
        get_resp = await async_client.get(f"/cases/{created_case_id}/documents/{document_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_upload_case_document_file(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, case_document_payload: dict, tmp_path: Path
    ):
        """
        Demonstrates file upload to /cases/{case_id}/documents/{document_id}/upload
        Requires an updated schema with 'file_path' or similar in your DB if you plan to store it.
        """
        # 1. Create a case-document link
        create_resp = await async_client.post(f"/cases/{created_case_id}/documents", json=case_document_payload)
        assert create_resp.status_code == 201
        doc_link = create_resp.json()
        document_id = doc_link["document_id"]

        # 2. Prepare a dummy file to upload
        dummy_file = tmp_path / "test_upload.txt"
        dummy_file.write_text("Hello, this is a test file.")

        # 3. Upload file
        with dummy_file.open("rb") as f:
            files = {"file": ("test_upload.txt", f, "text/plain")}
            upload_resp = await async_client.post(
                f"/cases/{created_case_id}/documents/{document_id}/upload",
                files=files  # because it's a form-data file
            )
        # The endpoint returns updated doc link
        assert upload_resp.status_code == 201


# =============================================================================
# Tests for Case Loans
# =============================================================================

@pytest.mark.asyncio
class TestCaseLoansRouter:
    @pytest.fixture
    def new_loan_payload(self, created_case_id):
        return {
            "case_id": str(created_case_id),
            "amount": 12345.67,
            "status": "active",
            "start_date": date.today().isoformat(),
            "end_date": None
        }

    async def test_create_loan_for_case(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_loan_payload: dict
    ):
        resp = await async_client.post(f"/cases/{created_case_id}/loans", json=new_loan_payload)
        assert resp.status_code == status.HTTP_201_CREATED

        data = resp.json()
        assert "id" in data
        assert data["status"] == "active"

    async def test_list_case_loans(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_loan_payload: dict
    ):
        await async_client.post(f"/cases/{created_case_id}/loans", json=new_loan_payload)
        resp = await async_client.get(f"/cases/{created_case_id}/loans")
        assert resp.status_code == status.HTTP_200_OK

        loans_list = resp.json()
        assert isinstance(loans_list, list)
        assert len(loans_list) >= 1

    async def test_get_loan_valid_id(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_loan_payload: dict
    ):
        create_resp = await async_client.post(f"/cases/{created_case_id}/loans", json=new_loan_payload)
        loan_id = create_resp.json()["id"]

        get_resp = await async_client.get(f"/loans/{loan_id}")
        assert get_resp.status_code == status.HTTP_200_OK
        data = get_resp.json()
        assert data["id"] == loan_id

    async def test_get_loan_invalid_id(self, async_client: AsyncClient):
        bad_id = uuid.uuid4()
        resp = await async_client.get(f"/loans/{bad_id}")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_loan(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_loan_payload: dict
    ):
        create_resp = await async_client.post(f"/cases/{created_case_id}/loans", json=new_loan_payload)
        loan_id = create_resp.json()["id"]

        update_payload = {
            "amount": 99999.99,
            "status": "closed"
        }
        update_resp = await async_client.put(f"/loans/{loan_id}", json=update_payload)
        assert update_resp.status_code == status.HTTP_200_OK

        updated_loan = update_resp.json()
        assert updated_loan["amount"] == 99999.99
        assert updated_loan["status"] == "closed"

    async def test_delete_loan(
            self, async_client: AsyncClient, created_case_id: uuid.UUID, new_loan_payload: dict
    ):
        create_resp = await async_client.post(f"/cases/{created_case_id}/loans", json=new_loan_payload)
        loan_id = create_resp.json()["id"]

        del_resp = await async_client.delete(f"/loans/{loan_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        # Verify
        get_resp = await async_client.get(f"/loans/{loan_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND
