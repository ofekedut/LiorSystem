import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from server.api import app
from server.database.database import drop_all_tables, create_schema_if_not_exists
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
