import pytest
from fastapi.testclient import TestClient
from fastapi import status

from server.api import app
from server.database.database import get_connection


class TestDocumentCategoriesRouter:
    """
    Test cases for the document_categories_router.
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

    def test_create_document_category(self, client):
        """Test creating a new document category."""
        response = client.post(
            "/document_categories/",
            json={"name": "Legal", "value": "legal"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Legal"
        assert data["value"] == "legal"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Cleanup - delete the created document category
        client.delete(f"/document_categories/{data['id']}")

    def test_read_document_categories(self, client):
        """Test retrieving all document categories."""
        # Create a document category to ensure there's at least one
        create_response = client.post(
            "/document_categories/",
            json={"name": "Medical", "value": "medical"},
        )
        created_data = create_response.json()

        # Get all document categories
        response = client.get("/document_categories/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # In the test environment, we should at least have the category we just created
        assert len(data) >= 1  # At minimum, the 'medical' category we just created
        # Note: In production, there would be more categories from migrations, but we don't run those in tests

        # Cleanup
        client.delete(f"/document_categories/{created_data['id']}")

    def test_read_document_category_by_id(self, client):
        """Test retrieving a document category by ID."""
        # Create a document category
        create_response = client.post(
            "/document_categories/",
            json={"name": "Education", "value": "education"},
        )
        created_data = create_response.json()

        # Get by ID
        response = client.get(f"/document_categories/{created_data['id']}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_data["id"]
        assert data["name"] == "Education"
        assert data["value"] == "education"

        # Cleanup
        client.delete(f"/document_categories/{created_data['id']}")

    def test_read_document_category_by_value(self, client):
        """Test retrieving a document category by value."""
        # Create a document category
        create_response = client.post(
            "/document_categories/",
            json={"name": "Insurance", "value": "insurance"},
        )
        created_data = create_response.json()

        # Get by value
        response = client.get(f"/document_categories/value/insurance")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_data["id"]
        assert data["name"] == "Insurance"
        assert data["value"] == "insurance"

        # Cleanup
        client.delete(f"/document_categories/{created_data['id']}")

    def test_read_document_category_not_found(self, client):
        """Test retrieving a document category that doesn't exist."""
        response = client.get("/document_categories/00000000-0000-0000-0000-000000000000")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_document_category(self, client):
        """Test updating a document category."""
        # Create a document category
        create_response = client.post(
            "/document_categories/",
            json={"name": "Personal", "value": "personal"},
        )
        created_data = create_response.json()

        # Update it
        response = client.put(
            f"/document_categories/{created_data['id']}?cascade_updates=true",
            json={"name": "Personal Documents", "value": "personal-docs"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_data["id"]
        assert data["name"] == "Personal Documents"
        assert data["value"] == "personal-docs"

        # Cleanup
        client.delete(f"/document_categories/{created_data['id']}")

    def test_update_document_category_partial(self, client):
        """Test partial update of a document category."""
        # Create a document category
        create_response = client.post(
            "/document_categories/",
            json={"name": "Utility", "value": "utility"},
        )
        created_data = create_response.json()

        # Update only the name
        response = client.put(
            f"/document_categories/{created_data['id']}",
            json={"name": "Utility Bills"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_data["id"]
        assert data["name"] == "Utility Bills"
        assert data["value"] == "utility"  # value shouldn't change

        # Cleanup
        client.delete(f"/document_categories/{created_data['id']}")

    def test_update_document_category_not_found(self, client):
        """Test updating a document category that doesn't exist."""
        response = client.put(
            "/document_categories/00000000-0000-0000-0000-000000000000",
            json={"name": "Not Found"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_document_category(self, client):
        """Test deleting a document category."""
        # Create a document category
        create_response = client.post(
            "/document_categories/",
            json={"name": "Travel", "value": "travel"},
        )
        created_data = create_response.json()

        # Delete it
        response = client.delete(f"/document_categories/{created_data['id']}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's gone
        get_response = client.get(f"/document_categories/{created_data['id']}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_document_category_not_found(self, client):
        """Test deleting a document category that doesn't exist."""
        response = client.delete("/document_categories/00000000-0000-0000-0000-000000000000")
        assert response.status_code == status.HTTP_404_NOT_FOUND

