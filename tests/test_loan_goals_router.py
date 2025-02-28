# tests/test_loan_goals_router.py
import pytest
from httpx import AsyncClient
import uuid
from server.routers.loan_goals_router import LoanGoalInCreate, LoanGoalInUpdate


@pytest.mark.asyncio
class TestLoanGoalsRouter:
    """Tests for the loan_goals_router endpoints."""

    async def test_create_loan_goal(self, async_client: AsyncClient, admin_token):
        """Test creating a new loan goal."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        new_goal = {
            "name": "Test Loan Goal",
            "value": "test_loan_goal"
        }
        
        # Create the loan goal
        response = await async_client.post("/loan_goals/", json=new_goal, headers=headers)
        assert response.status_code == 201, response.text
        
        data = response.json()
        assert data['name'] == new_goal['name']
        assert data['value'] == new_goal['value']
        assert 'id' in data
        
        # Clean up - delete the created loan goal
        delete_response = await async_client.delete(f"/loan_goals/{data['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_loan_goals(self, async_client: AsyncClient, admin_token):
        """Test listing all loan goals."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test loan goal first
        new_goal = {
            "name": "Test Loan Goal List",
            "value": "test_loan_goal_list"
        }
        create_response = await async_client.post("/loan_goals/", json=new_goal, headers=headers)
        assert create_response.status_code == 201
        created_goal = create_response.json()
        
        # Get all loan goals
        response = await async_client.get("/loan_goals/", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify our created goal is in the list
        found = False
        for item in data:
            if item['id'] == created_goal['id']:
                found = True
                assert item['name'] == new_goal['name']
                assert item['value'] == new_goal['value']
                break
        
        assert found, "Created loan goal not found in the list"
        
        # Clean up
        delete_response = await async_client.delete(f"/loan_goals/{created_goal['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_loan_goal_by_id(self, async_client: AsyncClient, admin_token):
        """Test getting a specific loan goal by ID."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test loan goal first
        new_goal = {
            "name": "Test Loan Goal Get",
            "value": "test_loan_goal_get"
        }
        create_response = await async_client.post("/loan_goals/", json=new_goal, headers=headers)
        assert create_response.status_code == 201
        created_goal = create_response.json()
        
        # Get the loan goal by ID
        response = await async_client.get(f"/loan_goals/{created_goal['id']}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == created_goal['id']
        assert data['name'] == new_goal['name']
        assert data['value'] == new_goal['value']
        
        # Clean up
        delete_response = await async_client.delete(f"/loan_goals/{created_goal['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_loan_goal_not_found(self, async_client: AsyncClient, admin_token):
        """Test getting a non-existent loan goal."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to get a non-existent loan goal
        response = await async_client.get(f"/loan_goals/{random_id}", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_loan_goal(self, async_client: AsyncClient, admin_token):
        """Test updating a loan goal."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test loan goal first
        new_goal = {
            "name": "Test Loan Goal Update",
            "value": "test_loan_goal_update"
        }
        create_response = await async_client.post("/loan_goals/", json=new_goal, headers=headers)
        assert create_response.status_code == 201
        created_goal = create_response.json()
        
        # Update the loan goal
        update_data = {
            "name": "Updated Loan Goal",
            "value": "updated_loan_goal"
        }
        response = await async_client.put(f"/loan_goals/{created_goal['id']}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_goal = response.json()
        assert updated_goal['id'] == created_goal['id']
        assert updated_goal['name'] == update_data['name']
        assert updated_goal['value'] == update_data['value']
        
        # Verify the update by getting the loan goal
        get_response = await async_client.get(f"/loan_goals/{created_goal['id']}", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data['name'] == update_data['name']
        assert get_data['value'] == update_data['value']
        
        # Clean up
        delete_response = await async_client.delete(f"/loan_goals/{created_goal['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_update_loan_goal_partial(self, async_client: AsyncClient, admin_token):
        """Test partially updating a loan goal."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test loan goal first
        new_goal = {
            "name": "Test Loan Goal Partial Update",
            "value": "test_loan_goal_partial_update"
        }
        create_response = await async_client.post("/loan_goals/", json=new_goal, headers=headers)
        assert create_response.status_code == 201
        created_goal = create_response.json()
        
        # Update only the name
        update_data = {
            "name": "Partially Updated Loan Goal"
        }
        response = await async_client.put(f"/loan_goals/{created_goal['id']}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_goal = response.json()
        assert updated_goal['id'] == created_goal['id']
        assert updated_goal['name'] == update_data['name']
        assert updated_goal['value'] == new_goal['value']  # Value should remain unchanged
        
        # Clean up
        delete_response = await async_client.delete(f"/loan_goals/{created_goal['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_update_loan_goal_not_found(self, async_client: AsyncClient, admin_token):
        """Test updating a non-existent loan goal."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to update a non-existent loan goal
        update_data = {
            "name": "Non-existent Loan Goal",
            "value": "non_existent_loan_goal"
        }
        response = await async_client.put(f"/loan_goals/{random_id}", json=update_data, headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_loan_goal(self, async_client: AsyncClient, admin_token):
        """Test deleting a loan goal."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test loan goal first
        new_goal = {
            "name": "Test Loan Goal Delete",
            "value": "test_loan_goal_delete"
        }
        create_response = await async_client.post("/loan_goals/", json=new_goal, headers=headers)
        assert create_response.status_code == 201
        created_goal = create_response.json()
        
        # Delete the loan goal
        delete_response = await async_client.delete(f"/loan_goals/{created_goal['id']}", headers=headers)
        assert delete_response.status_code == 204
        
        # Verify it's deleted by trying to get it
        get_response = await async_client.get(f"/loan_goals/{created_goal['id']}", headers=headers)
        assert get_response.status_code == 404

    async def test_delete_loan_goal_not_found(self, async_client: AsyncClient, admin_token):
        """Test deleting a non-existent loan goal."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to delete a non-existent loan goal
        response = await async_client.delete(f"/loan_goals/{random_id}", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
