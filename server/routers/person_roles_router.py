import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from server.database.person_roles_database import (
    PersonRole,
    PersonRoleInCreate,
    PersonRoleInUpdate,
    create_person_role,
    delete_person_role,
    get_person_role,
    get_person_roles,
    update_person_role,
    get_person_role_by_value,
)

router = APIRouter(prefix="/person_roles", tags=["person_roles"])


@router.post("/", response_model=PersonRole, status_code=status.HTTP_201_CREATED)
async def create_person_role_endpoint(payload: PersonRoleInCreate):
    """
    Create a new person role.
    """
    return await create_person_role(payload)


@router.get("/", response_model=List[PersonRole])
async def read_person_roles():
    """
    Retrieve all person roles.
    """
    return await get_person_roles()


@router.get("/value/{value}", response_model=PersonRole)
async def read_person_role_by_value(value: str):
    """
    Retrieve a person role by its value.
    """
    person_role = await get_person_role_by_value(value)
    if person_role is None:
        raise HTTPException(status_code=404, detail="Person role not found")
    return person_role


@router.get("/{person_role_id}", response_model=PersonRole)
async def read_person_role(person_role_id: uuid.UUID):
    """
    Retrieve a person role by ID.
    """
    person_role = await get_person_role(person_role_id)
    if person_role is None:
        raise HTTPException(status_code=404, detail="Person role not found")
    return person_role


@router.put("/{person_role_id}", response_model=PersonRole)
async def update_person_role_endpoint(person_role_id: uuid.UUID, payload: PersonRoleInUpdate):
    """
    Update a person role.
    """
    person_role = await update_person_role(person_role_id, payload)
    if person_role is None:
        raise HTTPException(status_code=404, detail="Person role not found")
    return person_role


@router.delete("/{person_role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person_role_endpoint(person_role_id: uuid.UUID):
    """
    Delete a person role.
    """
    deleted = await delete_person_role(person_role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Person role not found")
    return None
