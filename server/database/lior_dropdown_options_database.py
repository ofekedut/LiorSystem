"""
Database operations for dropdown options management
"""
import uuid
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

from server.database.database import get_connection


class DropdownOptionBase(BaseModel):
    category: str
    name: str
    value: str


class DropdownOptionCreate(DropdownOptionBase):
    pass


class DropdownOptionInDB(DropdownOptionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DropdownOptionUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


async def create_dropdown_option(payload: DropdownOptionCreate) -> DropdownOptionInDB:
    """
    Create a new dropdown option
    """
    query = """
    INSERT INTO lior_dropdown_options (
        id, category, name, value, created_at, updated_at
    )
    VALUES ($1, $2, $3, $4, NOW(), NOW())
    RETURNING id, category, name, value, created_at, updated_at
    """

    option_id = uuid.uuid4()
    values = [
        option_id,
        payload.category,
        payload.name,
        payload.value
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return DropdownOptionInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_dropdown_option_by_id(option_id: uuid.UUID) -> Optional[DropdownOptionInDB]:
    """
    Get a specific dropdown option by ID
    """
    query = """
    SELECT id, category, name, value, created_at, updated_at
    FROM lior_dropdown_options
    WHERE id = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, option_id)
        if row:
            return DropdownOptionInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_dropdown_option_by_value(category: str, value: str) -> Optional[DropdownOptionInDB]:
    """
    Get a specific dropdown option by category and value
    """
    query = """
    SELECT id, category, name, value, created_at, updated_at
    FROM lior_dropdown_options
    WHERE category = $1 AND value = $2
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, category, value)
        if row:
            return DropdownOptionInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_dropdown_options_by_category(category: str) -> List[DropdownOptionInDB]:
    """
    Get all dropdown options for a specific category
    """
    query = """
    SELECT id, category, name, value, created_at, updated_at
    FROM lior_dropdown_options
    WHERE category = $1
    ORDER BY name
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, category)
        return [DropdownOptionInDB.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def get_all_dropdown_options() -> Dict[str, List[DropdownOptionInDB]]:
    """
    Get all dropdown options organized by category
    """
    query = """
    SELECT id, category, name, value, created_at, updated_at
    FROM lior_dropdown_options
    ORDER BY category, name
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query)

        # Organize by category
        result = {}
        for row in rows:
            data = dict(row)
            category = data['category']
            if category not in result:
                result[category] = []

            result[category].append(DropdownOptionInDB.model_validate(data))

        return result
    finally:
        await conn.close()


async def get_all_categories() -> List[str]:
    """
    Get a list of all distinct categories
    """
    query = """
    SELECT DISTINCT category
    FROM lior_dropdown_options
    ORDER BY category
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [row['category'] for row in rows]
    finally:
        await conn.close()


async def update_dropdown_option(
        option_id: uuid.UUID,
        payload: DropdownOptionUpdate
) -> Optional[DropdownOptionInDB]:
    """
    Update a dropdown option
    """
    existing = await get_dropdown_option_by_id(option_id)
    if not existing:
        return None

    # Build SET clause dynamically based on provided fields
    set_parts = []
    values = [option_id]  # First parameter is always the ID
    param_index = 2  # Start parameter index at 2

    if payload.name is not None:
        set_parts.append(f"name = ${param_index}")
        values.append(payload.name)
        param_index += 1

    if payload.value is not None:
        set_parts.append(f"value = ${param_index}")
        values.append(payload.value)
        param_index += 1

    # If nothing to update, return existing record
    if not set_parts:
        return existing

    # Always update updated_at timestamp
    set_parts.append("updated_at = NOW()")

    query = f"""
    UPDATE lior_dropdown_options
    SET {", ".join(set_parts)}
    WHERE id = $1
    RETURNING id, category, name, value, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return DropdownOptionInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_dropdown_option(option_id: uuid.UUID) -> bool:
    """
    Delete a dropdown option
    """
    query = """
    DELETE FROM lior_dropdown_options
    WHERE id = $1
    RETURNING id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, option_id)
        return row is not None
    finally:
        await conn.close()


async def check_option_in_use(option_id: uuid.UUID) -> bool:
    """
    Check if a dropdown option is being used in any related tables
    """
    conn = await get_connection()
    try:
        # Get the option first to determine its category
        option = await get_dropdown_option_by_id(option_id)
        if not option:
            return False

        # Define tables to check based on category
        tables_to_check = []

        if option.category == 'asset_types':
            tables_to_check.append(("person_assets", "asset_type_id"))

        elif option.category == 'bank_account_types':
            tables_to_check.append(("person_bank_accounts", "account_type_id"))

        elif option.category == 'company_types':
            tables_to_check.append(("case_companies", "company_type_id"))

        elif option.category == 'credit_card_types':
            tables_to_check.append(("person_credit_cards", "card_type_id"))

        elif option.category == 'document_types':
            tables_to_check.append(("documents", "document_type_id"))

        elif option.category == 'document_categories':
            tables_to_check.append(("documents", "category_id"))

        elif option.category == 'employment_types':
            tables_to_check.append(("person_employment_history", "employment_type_id"))

        elif option.category == 'fin_org_types':
            tables_to_check.append(("fin_orgs", "type_id"))

        elif option.category == 'income_sources_types':
            tables_to_check.append(("person_income_sources", "income_source_type_id"))

        elif option.category == 'loan_goals':
            tables_to_check.append(("case_desired_products", "loan_goal_id"))

        elif option.category == 'loan_types':
            tables_to_check.append(("cases", "loan_type_id"))
            tables_to_check.append(("person_loans", "loan_type_id"))
            tables_to_check.append(("case_desired_products", "loan_type_id"))

        elif option.category == 'person_marital_statuses':
            tables_to_check.append(("case_persons", "marital_status_id"))

        elif option.category == 'person_roles':
            tables_to_check.append(("case_persons", "role_id"))
            tables_to_check.append(("case_companies", "role_id"))

        elif option.category == 'related_person_relationships_types':
            tables_to_check.append(("case_person_relations", "relationship_type_id"))

        elif option.category == 'case_status':
            # case_status is stored as enum in the cases table, not referenced by ID
            return False

        # Check each table for references to this option
        for table, column in tables_to_check:
            count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {table} WHERE {column} = $1",
                option_id
            )
            if count > 0:
                return True

        # If no references found in any tables
        return False
    finally:
        await conn.close()