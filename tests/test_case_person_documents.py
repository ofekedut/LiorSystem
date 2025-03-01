import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status

from server.api import app
from server.database.cases_database import (
    CasePersonDocumentCreate,
    CaseStatus,
    CaseInCreate,
    CasePersonCreate,
    PersonGender,
    PersonRole,
    create_case,
    create_case_person,
)
from server.database.documents_databse import (
    create_document,
    DocumentInCreate,
)
from server.database.database import get_connection


# =============================================================================
# Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def async_client():
    """
    Provides an AsyncClient for making requests to the FastAPI app.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def created_main_doc():
    """
    Creates a test document for use in testing.
    """
    # Get or create document type first
    doc_type_name = "Recurring"
    doc_type_value = "recurring"
    
    conn = await get_connection()
    try:
        # Try to get existing document type
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
        
    # Generate a unique document name using uuid
    unique_name = f'test doc {uuid.uuid4()}'
    
    return await create_document(DocumentInCreate(
        name=unique_name,
        description='test doc',
        document_type_id=doc_type_id,
        category='identification',
        period_type='quarter',
        periods_required=4,
        has_multiple_periods=True,
        required_for=[],
    ))


@pytest_asyncio.fixture
async def created_case():
    """
    Creates a new case for testing and returns the resulting CaseInDB.
    """
    return await create_case(CaseInCreate(
        name="Test Case",
        status=CaseStatus.active,
        case_purpose="Testing",
        loan_type="Mortgage",
    ))


@pytest_asyncio.fixture
async def created_person(created_case):
    """
    Creates a new person linked to the created_case fixture.
    """
    # Generate a random ID number to avoid unique constraint violations
    unique_id_number = str(uuid.uuid4().int)[:9]
    
    return await create_case_person(CasePersonCreate(
        case_id=created_case.id,
        first_name="John",
        last_name="Doe",
        id_number=unique_id_number,
        gender=PersonGender.male,
        role=PersonRole.primary,
        birth_date="1980-01-01",
        phone="1234567890",
        email="johndoe@example.com",
        status="active",
    ))


# =============================================================================
# Tests for Case Person Documents Endpoints
# =============================================================================

@pytest.mark.asyncio
class TestCasePersonDocumentsEndpoints:
    async def test_create_case_person_document(self, async_client, created_case, created_person, created_main_doc):
        """
        Test creating a new case-person-document link.
        """
        response = await async_client.post(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents",
            json={
                "case_id": str(created_case.id),
                "person_id": str(created_person.id),
                "document_id": str(created_main_doc.id),
                "is_primary": True
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["case_id"] == str(created_case.id)
        assert data["person_id"] == str(created_person.id)
        assert data["document_id"] == str(created_main_doc.id)
        assert data["is_primary"] == True
        
        # Test attempting to create with mismatched IDs
        response = await async_client.post(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents",
            json={
                "case_id": str(uuid.uuid4()),  # Different case ID
                "person_id": str(created_person.id),
                "document_id": str(created_main_doc.id),
                "is_primary": True
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_case_person_document(self, async_client, created_case, created_person, created_main_doc):
        """
        Test retrieving a specific case-person-document link.
        """
        # First create a link
        response = await async_client.post(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents",
            json={
                "case_id": str(created_case.id),
                "person_id": str(created_person.id),
                "document_id": str(created_main_doc.id),
                "is_primary": True
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Now retrieve it
        response = await async_client.get(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents/{created_main_doc.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["case_id"] == str(created_case.id)
        assert data["person_id"] == str(created_person.id)
        assert data["document_id"] == str(created_main_doc.id)
        assert data["is_primary"] == True
        
        # Test retrieving a non-existent link
        non_existent_doc_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents/{non_existent_doc_id}"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_case_person_documents(self, async_client, created_case, created_person, created_main_doc):
        """
        Test listing all documents for a specific person in a case.
        """
        # First create a link
        response = await async_client.post(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents",
            json={
                "case_id": str(created_case.id),
                "person_id": str(created_person.id),
                "document_id": str(created_main_doc.id),
                "is_primary": True
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Now list all documents
        response = await async_client.get(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Verify the document we just created is in the list
        found = False
        for doc in data:
            if doc["document_id"] == str(created_main_doc.id):
                found = True
                assert doc["case_id"] == str(created_case.id)
                assert doc["person_id"] == str(created_person.id)
                assert doc["is_primary"] == True
                break
        
        assert found, "Created document link not found in the list"

    async def test_update_case_person_document(self, async_client, created_case, created_person, created_main_doc):
        """
        Test updating a case-person-document link.
        """
        # First create a link
        response = await async_client.post(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents",
            json={
                "case_id": str(created_case.id),
                "person_id": str(created_person.id),
                "document_id": str(created_main_doc.id),
                "is_primary": True
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Now update it
        response = await async_client.patch(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents/{created_main_doc.id}",
            json={
                "is_primary": False
            }
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["case_id"] == str(created_case.id)
        assert data["person_id"] == str(created_person.id)
        assert data["document_id"] == str(created_main_doc.id)
        assert data["is_primary"] == False
        
        # Test updating a non-existent link
        non_existent_doc_id = str(uuid.uuid4())
        response = await async_client.patch(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents/{non_existent_doc_id}",
            json={
                "is_primary": True
            }
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_case_person_document(self, async_client, created_case, created_person, created_main_doc):
        """
        Test deleting a case-person-document link.
        """
        # First create a link
        response = await async_client.post(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents",
            json={
                "case_id": str(created_case.id),
                "person_id": str(created_person.id),
                "document_id": str(created_main_doc.id),
                "is_primary": True
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Now delete it
        response = await async_client.delete(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents/{created_main_doc.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Confirm it's deleted by trying to get it
        response = await async_client.get(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents/{created_main_doc.id}"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test deleting a non-existent link
        non_existent_doc_id = str(uuid.uuid4())
        response = await async_client.delete(
            f"/cases/{created_case.id}/persons/{created_person.id}/documents/{non_existent_doc_id}"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
