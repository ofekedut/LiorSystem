import uuid
from fastapi.testclient import TestClient
from server.api import app

client = TestClient(app)


def test_create_asset_type():
    # Test data with unique values for testing
    test_asset_type = {
        "name": "Test Car Type",
        "value": "test_car_type"
    }
    
    # Create a new asset type
    response = client.post("/asset-types", json=test_asset_type)
    assert response.status_code == 201
    
    # Validate response data
    data = response.json()
    assert "id" in data
    assert data["name"] == test_asset_type["name"]
    assert data["value"] == test_asset_type["value"]
    
    # Try to create the same asset type again (should fail with conflict)
    response = client.post("/asset-types", json=test_asset_type)
    assert response.status_code == 409


def test_get_asset_types():
    # First create a new asset type with unique values
    test_asset_type = {
        "name": "Test Real Estate Type",
        "value": "test_real_estate_type"
    }
    
    response = client.post("/asset-types", json=test_asset_type)
    assert response.status_code == 201
    
    # Get all asset types
    response = client.get("/asset-types")
    assert response.status_code == 200
    
    # Validate response data
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check if our created asset type is in the list
    found = False
    for asset_type in data:
        if asset_type["value"] == test_asset_type["value"]:
            found = True
            break
    
    assert found


def test_get_asset_type_by_id():
    # First create a new asset type with unique values
    test_asset_type = {
        "name": "Test Stock Type",
        "value": "test_stock_type"
    }
    
    response = client.post("/asset-types", json=test_asset_type)
    assert response.status_code == 201
    created_asset_type = response.json()
    asset_type_id = created_asset_type["id"]
    
    # Get the asset type by ID
    response = client.get(f"/asset-types/{asset_type_id}")
    assert response.status_code == 200
    
    # Validate response data
    data = response.json()
    assert data["id"] == asset_type_id
    assert data["name"] == test_asset_type["name"]
    assert data["value"] == test_asset_type["value"]
    
    # Try to get an asset type with a non-existent ID
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/asset-types/{non_existent_id}")
    assert response.status_code == 404


def test_update_asset_type():
    # First create a new asset type with unique values
    test_asset_type = {
        "name": "Test Bond Type",
        "value": "test_bond_type"
    }
    
    create_response = client.post("/asset-types", json=test_asset_type)
    assert create_response.status_code == 201
    created_asset_type = create_response.json()
    asset_type_id = created_asset_type["id"]
    
    # Update the asset type
    update_data = {
        "name": "Test Bond Type Updated"
    }
    response = client.put(f"/asset-types/{asset_type_id}", json=update_data)
    assert response.status_code == 200
    
    # Validate response data
    data = response.json()
    assert data["id"] == asset_type_id
    assert data["name"] == update_data["name"]
    assert data["value"] == test_asset_type["value"]  # Value should not change
    
    # Try to update with a value that already exists
    # First, create another asset type
    another_asset_type = {
        "name": "Test Another Bond Type",
        "value": "test_another_bond_type"
    }
    response = client.post("/asset-types", json=another_asset_type)
    assert response.status_code == 201
    
    # Now try to update the first asset type with the second's value
    update_data = {
        "value": "test_another_bond_type"
    }
    response = client.put(f"/asset-types/{asset_type_id}", json=update_data)
    assert response.status_code == 409
    
    # Try to update a non-existent asset type
    non_existent_id = str(uuid.uuid4())
    response = client.put(f"/asset-types/{non_existent_id}", json=update_data)
    assert response.status_code == 404


def test_delete_asset_type():
    # First create a new asset type with unique values
    test_asset_type = {
        "name": "Test Commodity Type",
        "value": "test_commodity_type"
    }
    
    create_response = client.post("/asset-types", json=test_asset_type)
    assert create_response.status_code == 201
    created_asset_type = create_response.json()
    asset_type_id = created_asset_type["id"]
    
    # Delete the asset type
    response = client.delete(f"/asset-types/{asset_type_id}")
    assert response.status_code == 204
    
    # Verify that it's deleted by trying to get it
    response = client.get(f"/asset-types/{asset_type_id}")
    assert response.status_code == 404
    
    # Try to delete a non-existent asset type
    non_existent_id = str(uuid.uuid4())
    response = client.delete(f"/asset-types/{non_existent_id}")
    assert response.status_code == 404
