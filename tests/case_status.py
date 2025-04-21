"""
Mock case status enum for testing
"""
from enum import Enum, auto


class CaseStatus(str, Enum):
    """Case status enum for use in tests"""
    active = "active"
    pending = "pending"
    completed = "completed"
    archived = "archived"
