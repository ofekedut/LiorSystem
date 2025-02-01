import pytest
from server.database.users_database import (
    get_user_by_email,
    get_user, UserRole, delete_user,
)
from server.features.users.security import (
    verify_password,
    get_current_user,
)


@pytest.mark.asyncio
async def test_create_admin_user(admin_user):
    """
    Verify that the admin_user fixture successfully creates a user in the DB.
    Check that user is retrievable and the password is properly hashed.
    """
    # Ensure we can retrieve the user by email
    db_user = await get_user_by_email(admin_user.email)
    assert db_user is not None, "Admin user should be created and retrievable by email."
    assert db_user.email == admin_user.email

    # Password should be hashed, so it shouldn't match raw
    # But we can check verify_password if we have the raw password
    assert db_user.password_hash != "123456qQ!", "Password should be hashed, not stored in plain text."

    # If your create_user sets a role, test that
    assert db_user.role == UserRole.ADMIN, "Admin user should have role='admin'."


@pytest.mark.asyncio
async def test_create_regular_user(regular_user):
    """
    Similar check for regular_user fixture.
    """
    db_user = await get_user_by_email(regular_user.email)
    assert db_user is not None, "Regular user should be created and retrievable by email."
    assert db_user.email == regular_user.email

    assert db_user.password_hash != "123456qQ!", "Password should be hashed."
    assert db_user.role in ("user", "USER"), "Regular user should have role='user'."



