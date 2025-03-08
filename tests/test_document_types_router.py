import pytest
from fastapi.testclient import TestClient
from fastapi import status

from server.api import app
from server.database.database import get_connection


class TestDocumentTypesRouter:
    """
    Test cases for the document_types_router.
    """

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup database connection before each test."""
        # We will handle connections in each test method
        yield
        # No need to disconnect

    @pytest.fixture
    def client(self):
        """Return a TestClient instance."""
        return TestClient(app)

    def test_create_document_type(self, client):
        """Test creating a new document type."""
        response = client.post(
            "/document_types/",
            json={"name": "Monthly", "value": "monthly"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Monthly"
        assert data["value"] == "monthly"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Cleanup - delete the created document type
        client.delete(f"/document_types/{data['id']}")

    def test_read_document_types(self, client):
        """Test retrieving all document types."""
        # Create a document type to ensure there's at least one
        create_response = client.post(
            "/document_types/",
            json={"name": "Quarterly", "value": "quarterly"},
        )
        create_response = client.post(
            "/document_types/",
            json={"name": "Monthly", "value": "monthly"},
        )
        create_response = client.post(
            "/document_types/",
            json={"name": "Yearly", "value": "yearly"},
        )
        create_response = client.post(
            "/document_types/",
            json={"name": "Dynamic", "value": "Dynamic"},
        )
        created_data = create_response.json()

        # Get all document types
        response = client.get("/document_types/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # There should be at least the built-in types plus our new one
        assert len(data) >= 4  # one-time, updatable, recurring, and quarterly

        # Cleanup
        client.delete(f"/document_types/{created_data['id']}")

    def test_read_document_type_by_id(self, client):
        """Test retrieving a document type by ID."""
        # Create a document type
        create_response = client.post(
            "/document_types/",
            json={"name": "Semi-Annual", "value": "semi-annual"},
        )
        created_data = create_response.json()

        # Get by ID
        response = client.get(f"/document_types/{created_data['id']}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_data["id"]
        assert data["name"] == "Semi-Annual"
        assert data["value"] == "semi-annual"

        # Cleanup
        client.delete(f"/document_types/{created_data['id']}")

    def test_read_document_type_not_found(self, client):
        """Test retrieving a document type that doesn't exist."""
        response = client.get("/document_types/00000000-0000-0000-0000-000000000000")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_document_type(self, client):
        """Test updating a document type."""
        # Create a document type
        create_response = client.post(
            "/document_types/",
            json={"name": "Annual", "value": "annual"},
        )
        created_data = create_response.json()

        # Update it with a unique name
        response = client.put(
            f"/document_types/{created_data['id']}",
            json={"name": "Annual Report", "value": "annual-report"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_data["id"]
        assert data["name"] == "Annual Report"
        assert data["value"] == "annual-report"

        # Cleanup
        client.delete(f"/document_types/{data['id']}")

    def test_update_document_type_partial(self, client):
        """Test partial update of a document type."""
        # Create a document type
        create_response = client.post(
            "/document_types/",
            json={"name": "Biweekly", "value": "biweekly"},
        )
        created_data = create_response.json()

        # Update only the name
        response = client.put(
            f"/document_types/{created_data['id']}",
            json={"name": "Every Two Weeks"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_data["id"]
        assert data["name"] == "Every Two Weeks"
        assert data["value"] == "biweekly"  # value shouldn't change

        # Cleanup
        client.delete(f"/document_types/{created_data['id']}")

    def test_update_document_type_not_found(self, client):
        """Test updating a document type that doesn't exist."""
        response = client.put(
            "/document_types/00000000-0000-0000-0000-000000000000",
            json={"name": "Not Found"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_document_type(self, client):
        """Test deleting a document type."""
        # Create a document type
        create_response = client.post(
            "/document_types/",
            json={"name": "Weekly", "value": "weekly"},
        )
        created_data = create_response.json()

        # Delete it
        response = client.delete(f"/document_types/{created_data['id']}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's gone
        get_response = client.get(f"/document_types/{created_data['id']}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_document_type_not_found(self, client):
        """Test deleting a document type that doesn't exist."""
        response = client.delete("/document_types/00000000-0000-0000-0000-000000000000")
        assert response.status_code == status.HTTP_404_NOT_FOUND
