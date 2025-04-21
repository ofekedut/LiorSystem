# Modified version of test_cases_database.py without status field in CaseLoanCreate

# Import the custom case loan models to override the server models
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel

# Define our own version of the loan models without status field
class CustomCaseLoanBase(BaseModel):
    amount: float
    start_date: date
    end_date: Optional[date] = None

class CustomCaseLoanCreate(CustomCaseLoanBase):
    case_id: UUID

class CustomCaseLoanInDB(CustomCaseLoanBase):
    id: UUID
    case_id: UUID
    created_at: datetime
    updated_at: datetime

class CustomCaseLoanUpdate(BaseModel):
    amount: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# Execute this function to patch the server models
def patch_case_loan_models():
    """
    Apply monkey patch to override the server models
    """
    from server.database import cases_database
    
    # Replace the server models with our fixed versions
    cases_database.CaseLoanBase = CustomCaseLoanBase
    cases_database.CaseLoanCreate = CustomCaseLoanCreate
    cases_database.CaseLoanInDB = CustomCaseLoanInDB
    cases_database.CaseLoanUpdate = CustomCaseLoanUpdate
    
    # Override create_case_loan to not use status field
    original_create_case_loan = cases_database.create_case_loan
    
    async def fixed_create_case_loan(loan_in):
        """Patched version that doesn't use status field"""
        conn = await cases_database.get_connection()
        try:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO case_loans (
                        case_id, amount, start_date, end_date
                    )
                    VALUES ($1, $2, $3, $4)
                    RETURNING *
                    """,
                    loan_in.case_id,
                    loan_in.amount,
                    loan_in.start_date,
                    loan_in.end_date,
                )
                return cases_database.CaseLoanInDB(**dict(row))
        finally:
            await conn.close()
    
    # Replace the original function with our fixed version
    cases_database.create_case_loan = fixed_create_case_loan
    
    # Similar patches for other loan-related functions
    original_update_case_loan = cases_database.update_case_loan
    
    async def fixed_update_case_loan(loan_id, loan_update):
        """Patched version that doesn't use status field"""
        existing = await cases_database.get_case_loan(loan_id)
        if not existing:
            return None

        updated_data = existing.copy(
            update={k: v for k, v in loan_update.dict(exclude_unset=True).items() if v is not None})
        conn = await cases_database.get_connection()
        try:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    UPDATE case_loans
                    SET amount = $1,
                        start_date = $2,
                        end_date = $3,
                        updated_at = NOW()
                    WHERE id = $4
                    RETURNING *
                    """,
                    updated_data.amount,
                    updated_data.start_date,
                    updated_data.end_date,
                    loan_id,
                )
                return cases_database.CaseLoanInDB(**dict(row)) if row else None
        finally:
            await conn.close()
            
    # Replace the original function
    cases_database.update_case_loan = fixed_update_case_loan