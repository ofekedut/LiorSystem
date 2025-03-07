import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from database.finorg_database import create_fin_org_type, FinOrgTypeCreate
from server.api import app
from server.database.database import drop_all_tables, create_schema_if_not_exists, get_connection
from server.database.users_database import create_user, UserCreate, update_user_role, UserRole, delete_user, get_user, get_user_by_email
from server.features.users.security import create_access_token


def pytest_configure(config):
    config.option.asyncio_default_fixture_loop_scope = "function"


@pytest_asyncio.fixture(scope="module", autouse=True)
async def cleanup_database():
    """Cleanup database before running tests."""
    await drop_all_tables()
    await create_schema_if_not_exists()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    yield
    # Clean up the database after each test
    if found := await  get_user_by_email("ofekedut86@gmail.com"):
        await delete_user(found.id)
    if found := await  get_user_by_email("ofekedut345@gmail.com"):
        await delete_user(found.id)


@pytest.fixture(scope="module")
def client():
    """Fixture for synchronous TestClient."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture(scope="module")
async def async_client():
    """Fixture for asynchronous TestClient using httpx."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user():
    """Create and return an admin user."""
    user_data = UserCreate(
        password="123456qQ!",
        first_name='Super',
        last_name='Ofek',
        email='ofekedut345@gmail.com'
    )
    found = await  get_user_by_email('ofekedut345@gmail.com')
    if found:
        return found
    else:
        user = await create_user(user_data)
        await  update_user_role(user.id, UserRole.ADMIN)
    return user


@pytest_asyncio.fixture
async def regular_user():
    """Create and return a regular user."""
    user_data = UserCreate(
        password="123456qQ!",
        first_name='Ofek',
        last_name='Edut',
        email='ofekedut86@gmail.com'
    )
    found = await  get_user_by_email('ofekedut86@gmail.com')
    if found:
        return found
    else:
        user = await create_user(user_data)
        return user


@pytest.fixture
def admin_token(admin_user):
    """Generate JWT token for admin user."""
    return create_access_token(admin_user.id)


@pytest.fixture
def user_token(regular_user):
    """Generate JWT token for regular user."""
    return create_access_token(regular_user.id)


@pytest_asyncio.fixture
async def new_document_payload() -> dict:
    """
    Returns a valid payload for creating a new document.
    First creates a document type directly in the database and uses its ID.
    """
    # Check if the document type already exists, and if not, create it
    doc_type_name = "One Time"
    doc_type_value = "one-time"

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

    return {
        "name": "Test Document",
        "description": "A test document",
        "document_type_id": str(doc_type_id),  # Convert UUID to string for JSON
        "category": "tax",
        "period_type": None,
        "periods_required": None,
        "has_multiple_periods": False,
        "required_for": ["all"]
    }


@pytest_asyncio.fixture
async def created_fin_org_type():
    uid = str(uuid.uuid4())
    return await create_fin_org_type(FinOrgTypeCreate(
        name='bank' + uid,
        value='bank' + uid,
    ))
