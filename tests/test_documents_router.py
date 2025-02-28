import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status

from server.api import app
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


# =============================================================================
# Tests for Documents Endpoints
# =============================================================================

@pytest.mark.asyncio
class TestDocumentsEndpoints:
    async def test_create_document(self, async_client: AsyncClient, new_document_payload: dict):
        """
        Test creating a new document (POST /documents).
        """
        response = await async_client.post("/documents", json=new_document_payload)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        # Verify UUID
        assert "id" in data
        assert isinstance(data["id"], str)
        # You could optionally attempt to parse UUID(data["id"]) to ensure it's valid
        assert data["name"] == new_document_payload["name"]
        assert data["description"] == new_document_payload["description"]
        assert data["required_for"] == new_document_payload["required_for"]

    async def test_list_documents(self, async_client: AsyncClient, new_document_payload: dict):
        """
        Test listing documents (GET /documents).
        Create one document first, then retrieve the list.
        """
        # Create a document
        await async_client.post("/documents", json=new_document_payload)

        # List documents
        response = await async_client.get("/documents")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        # Expect at least one document in the list.
        assert len(data) > 0

    async def test_get_document_valid_id(self, async_client: AsyncClient, new_document_payload: dict):
        """
        Test retrieving a specific document by ID (GET /documents/{document_id}).
        """
        # Create a document
        create_resp = await async_client.post("/documents", json=new_document_payload)
        created_doc = create_resp.json()
        doc_id = created_doc["id"]

        # Retrieve the document by its ID
        response = await async_client.get(f"/documents/{doc_id}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == doc_id
        assert data["name"] == new_document_payload["name"]

    async def test_get_document_invalid_id(self, async_client: AsyncClient):
        """
        Test retrieving a non-existent document should return 404.
        """
        # A random or fixed UUID that (likely) doesn't exist
        invalid_uuid = "11111111-1111-1111-1111-111111111111"
        response = await async_client.get(f"/documents/{invalid_uuid}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_document(self, async_client: AsyncClient, new_document_payload: dict):
        """
        Test updating an existing document (PUT /documents/{document_id}).
        """
        # Create a document
        create_resp = await async_client.post("/documents", json=new_document_payload)
        created_doc = create_resp.json()
        doc_id = created_doc["id"]

        # Get or create a recurring document type for the update
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
                recurring_type_id = existing['id']
            else:
                # Create a new document type
                recurring_type = await conn.fetchrow(
                    """INSERT INTO document_types (name, value) 
                       VALUES ($1, $2) 
                       RETURNING id""",
                    doc_type_name, doc_type_value
                )
                recurring_type_id = recurring_type['id']
        finally:
            await conn.close()
        
        # Prepare update payload. Ensure all required fields are provided.
        update_payload = {
            "name": "Updated Document Name",
            "description": "Updated description",
            "document_type_id": str(recurring_type_id),  # Change to a different document type
            "category": "financial",
            "period_type": "month",
            "periods_required": 12,
            "has_multiple_periods": True,
            "required_for": ["employees", "self-employed"]
        }
        update_resp = await async_client.put(f"/documents/{doc_id}", json=update_payload)
        assert update_resp.status_code == status.HTTP_200_OK

        updated_doc = update_resp.json()
        assert updated_doc["name"] == update_payload["name"]
        assert updated_doc["document_type_id"] == update_payload["document_type_id"]
        assert updated_doc["required_for"] == update_payload["required_for"]

    async def test_delete_document(self, async_client: AsyncClient, new_document_payload: dict):
        """
        Test deleting an existing document (DELETE /documents/{document_id}).
        """
        # Create a document
        create_resp = await async_client.post("/documents", json=new_document_payload)
        created_doc = create_resp.json()
        doc_id = created_doc["id"]

        # Delete the document
        del_resp = await async_client.delete(f"/documents/{doc_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        # Verify that the document no longer exists
        get_resp = await async_client.get(f"/documents/{doc_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Tests for Document Fields Endpoints
# =============================================================================

@pytest.mark.asyncio
class TestDocumentFieldsEndpoints:
    @pytest_asyncio.fixture
    async def document_for_fields(self, async_client: AsyncClient, new_document_payload: dict):
        """
        Creates a new document for testing document fields endpoints.
        """
        response = await async_client.post("/documents", json=new_document_payload)
        return response.json()

    async def test_create_document_field(self, async_client: AsyncClient, document_for_fields: dict):
        """
        Test creating a new document field (POST /documents/{document_id}/fields).
        """
        doc_id = document_for_fields["id"]
        field_payload = {
            "document_id": doc_id,
            "name": "Test Field",
            "type": "string",
            "is_identifier": False,
            "field_type": "document_field",
            "is_required": True,
        }
        resp = await async_client.post(f"/documents/{doc_id}/fields", json=field_payload)
        assert resp.status_code == status.HTTP_201_CREATED

        data = resp.json()
        assert "id" in data
        assert data["document_id"] == doc_id
        assert data["name"] == field_payload["name"]

    async def test_get_document_fields(self, async_client: AsyncClient, document_for_fields: dict):
        """
        Test listing document fields (GET /documents/{document_id}/fields).
        """
        doc_id = document_for_fields["id"]

        # Create a couple of fields for the document
        for i in range(2):
            field_payload = {
                "document_id": doc_id,
                "name": f"Field {i}",
                "type": "string",
                "is_identifier": False,
                "is_required": False,
                'field_type': 'document_field',
            }
            resp = await async_client.post(f"/documents/{doc_id}/fields", json=field_payload)
            assert resp.status_code == status.HTTP_201_CREATED

        # Retrieve document fields
        resp = await async_client.get(f"/documents/{doc_id}/fields")
        assert resp.status_code == status.HTTP_200_OK

        fields = resp.json()
        assert isinstance(fields, list)
        assert len(fields) >= 2

    async def test_delete_document_field(self, async_client: AsyncClient, document_for_fields: dict):
        """
        Test deleting a document field (DELETE /fields/{field_id}).
        """
        doc_id = document_for_fields["id"]
        # Create a field first
        field_payload = {
            "document_id": doc_id,
            "name": "Field to Delete",
            "type": "string",
            "is_identifier": True,
            "is_required": False,
            'field_type': 'document_field',
        }
        create_resp = await async_client.post(f"/documents/{doc_id}/fields", json=field_payload)
        field_id = create_resp.json()["id"]

        # Delete the field
        del_resp = await async_client.delete(f"/fields/{field_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        # Verify the field has been deleted
        list_resp = await async_client.get(f"/documents/{doc_id}/fields")
        fields_list = list_resp.json()
        assert all(field["id"] != field_id for field in fields_list)


# =============================================================================
# Tests for Validation Rules Endpoints
# =============================================================================

@pytest.mark.asyncio
class TestValidationRulesEndpoints:
    @pytest_asyncio.fixture
    async def document_for_rules(self, async_client: AsyncClient, new_document_payload: dict):
        """
        Creates a new document for testing validation rules endpoints.
        """
        payload = new_document_payload.copy()
        payload.update({
            "name": "Validation Rule Test Document",
            "document_type": "recurring",
            "category": "financial",
            "period_type": "month",
            "periods_required": 6,
            "has_multiple_periods": True,
            "required_for": ["employees"]
        })
        resp = await async_client.post("/documents", json=payload)
        return resp.json()

    async def test_create_validation_rule(self, async_client: AsyncClient, document_for_rules: dict):
        """
        Test creating a validation rule (POST /documents/{document_id}/validation_rules).
        """
        doc_id = document_for_rules["id"]
        rule_payload = {
            "document_id": doc_id,
            "field": "test_field",
            "operator": "equals",
            "value": {"expected": "value"},
            "error_message": "Field must equal 'value'"
        }
        resp = await async_client.post(f"/documents/{doc_id}/validation_rules", json=rule_payload)
        assert resp.status_code == status.HTTP_201_CREATED

        data = resp.json()
        assert "id" in data
        assert data["document_id"] == doc_id
        assert data["operator"] == rule_payload["operator"]
        assert data["value"] == rule_payload["value"]

    async def test_get_validation_rules(self, async_client: AsyncClient, document_for_rules: dict):
        """
        Test retrieving validation rules for a document (GET /documents/{document_id}/validation_rules).
        """
        doc_id = document_for_rules["id"]

        # Create a validation rule
        rule_payload = {
            "document_id": doc_id,
            "field": "another_field",
            "operator": "greater_than",
            "value": {"min": 10},
            "error_message": "Value must be greater than 10"
        }
        await async_client.post(f"/documents/{doc_id}/validation_rules", json=rule_payload)

        # Retrieve validation rules
        resp = await async_client.get(f"/documents/{doc_id}/validation_rules")
        assert resp.status_code == status.HTTP_200_OK

        rules = resp.json()
        assert isinstance(rules, list)
        assert len(rules) >= 1

    async def test_delete_validation_rule(self, async_client: AsyncClient, document_for_rules: dict):
        """
        Test deleting a validation rule (DELETE /validation_rules/{rule_id}).
        """
        doc_id = document_for_rules["id"]
        rule_payload = {
            "document_id": doc_id,
            "field": "delete_rule_field",
            "operator": "not_equals",
            "value": {"not": "bad_value"},
            "error_message": "Value must not equal bad_value"
        }
        create_resp = await async_client.post(f"/documents/{doc_id}/validation_rules", json=rule_payload)
        rule_id = create_resp.json()["id"]

        # Delete the rule
        del_resp = await async_client.delete(f"/validation_rules/{rule_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        # Verify
        list_resp = await async_client.get(f"/documents/{doc_id}/validation_rules")
        rules_list = list_resp.json()
        assert all(rule["id"] != rule_id for rule in rules_list)
