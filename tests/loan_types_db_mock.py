"""
Mock database module for loan types to be used in tests
"""
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel


class LoanTypeInCreate(BaseModel):
    """Model for creating a loan type"""
    name: str
    value: str


class LoanTypeDb:
    """Mock class for loan type database operations"""
    
    @staticmethod
    async def create_loan_type(data: LoanTypeInCreate) -> Dict[str, Any]:
        """
        Mock function to create a loan type
        Returns a dictionary representing a loan type for testing
        """
        return {
            "id": uuid.uuid4(),
            "name": data.name,
            "value": data.value,
            "created_at": "2024-03-22T00:00:00.000000",
            "updated_at": "2024-03-22T00:00:00.000000"
        }

    @staticmethod
    async def get_loan_type_by_name(name: str) -> Dict[str, Any]:
        """
        Mock function to retrieve a loan type by name
        Returns a dictionary representing a loan type for testing
        """
        return {
            "id": uuid.uuid4(),
            "name": name,
            "value": name.lower().replace(" ", "_"),
            "created_at": "2024-03-22T00:00:00.000000",
            "updated_at": "2024-03-22T00:00:00.000000"
        }
