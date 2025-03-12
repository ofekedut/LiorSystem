"""
Database operations for unified enum management
"""
import asyncpg
import uuid
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

from server.database.database import get_connection


class EnumOperation(str, Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"


class EnumValueBase(BaseModel):
    name: str
    value: str


class EnumValueInDB(EnumValueBase):
    id: uuid.UUID


class EnumRequest(BaseModel):
    enum_name: str
    operation: EnumOperation
    key: str
    value: Optional[str] = None  # Not required for delete operation


# Mapping of enum names to their respective database tables
ENUM_TABLE_MAP = {
    "asset_types": "asset_types",
    "bank_account_types": "bank_account_type",
    "company_types": "company_types",
    "credit_card_types": "credit_card_types",
    "document_categories": "document_categories",
    "document_types": "document_types",
    "employment_types": "employment_types",
    "fin_org_types": "fin_org_types",
    "income_sources_types": "income_sources_types",
    "loan_goals": "loan_goals",
    "loan_types": "loan_types",
    "person_marital_statuses": "person_marital_statuses",
    "person_roles": "person_roles",
    "related_person_relationships_types": "related_person_relationships_types",
}


async def get_enum_values(enum_name: str) -> List[EnumValueInDB]:
    """
    Get all values for a specific enum type.

    Args:
        enum_name: The name of the enum type

    Returns:
        List of enum values

    Raises:
        ValueError: If enum_name is not valid
    """
    if enum_name not in ENUM_TABLE_MAP:
        raise ValueError(f"Invalid enum name: {enum_name}")

    table_name = ENUM_TABLE_MAP[enum_name]

    conn = await get_connection()
    try:
        rows = await conn.fetch(f"SELECT id, name, value FROM {table_name}")
        return [EnumValueInDB(id=row['id'], name=row['name'], value=row['value']) for row in rows]
    finally:
        await conn.close()


async def manage_enum_value(request: EnumRequest) -> Dict[str, Any]:
    """
    Add, update, or delete an enum value.

    Args:
        request: EnumRequest containing operation details

    Returns:
        Dictionary containing operation result

    Raises:
        ValueError: If enum_name is not valid or operation fails
    """
    if request.enum_name not in ENUM_TABLE_MAP:
        raise ValueError(f"Invalid enum name: {request.enum_name}")

    table_name = ENUM_TABLE_MAP[request.enum_name]
    conn = await get_connection()

    try:
        async with conn.transaction():
            if request.operation == EnumOperation.ADD:
                if not request.value:
                    raise ValueError("Value is required for add operation")

                # Check if value already exists
                existing = await conn.fetchrow(
                    f"SELECT id FROM {table_name} WHERE value = $1",
                    request.key
                )

                if existing:
                    raise ValueError(f"Value '{request.key}' already exists")

                # Insert new value
                row = await conn.fetchrow(
                    f"INSERT INTO {table_name} (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
                    uuid.uuid4(), request.value, request.key
                )

                return {
                    "operation": "add",
                    "status": "success",
                    "data": {
                        "id": row['id'],
                        "name": row['name'],
                        "value": row['value']
                    }
                }

            elif request.operation == EnumOperation.UPDATE:
                if not request.value:
                    raise ValueError("Value is required for update operation")

                # Check if value exists
                existing = await conn.fetchrow(
                    f"SELECT id FROM {table_name} WHERE value = $1",
                    request.key
                )

                if not existing:
                    raise ValueError(f"Value '{request.key}' not found")

                # Update value
                row = await conn.fetchrow(
                    f"UPDATE {table_name} SET name = $1 WHERE value = $2 RETURNING id, name, value",
                    request.value, request.key
                )

                return {
                    "operation": "update",
                    "status": "success",
                    "data": {
                        "id": row['id'],
                        "name": row['name'],
                        "value": row['value']
                    }
                }

            elif request.operation == EnumOperation.DELETE:
                # Check if value exists
                existing = await conn.fetchrow(
                    f"SELECT id FROM {table_name} WHERE value = $1",
                    request.key
                )

                if not existing:
                    raise ValueError(f"Value '{request.key}' not found")

                # Delete value
                await conn.execute(
                    f"DELETE FROM {table_name} WHERE value = $1",
                    request.key
                )

                return {
                    "operation": "delete",
                    "status": "success",
                    "data": {
                        "value": request.key
                    }
                }

            else:
                raise ValueError(f"Invalid operation: {request.operation}")

    except Exception as e:
        # Re-raise with more context
        raise ValueError(f"Error managing enum value: {str(e)}")
    finally:
        await conn.close()


async def get_all_enums() -> Dict[str, List[EnumValueInDB]]:
    """
    Get all enums with their values.

    Returns:
        Dictionary with enum names as keys and lists of enum values as values
    """
    result = {}

    for enum_name in ENUM_TABLE_MAP:
        try:
            values = await get_enum_values(enum_name)
            result[enum_name] = values
        except Exception as e:
            print(f"Error retrieving enum values for {enum_name}: {str(e)}")
            result[enum_name] = []

    return result