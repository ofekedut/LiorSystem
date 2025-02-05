from typing import List, Optional
from pydantic import BaseModel


class ProcessingStepDefinition(BaseModel):
    """
    A definition for a single step in the document processing workflow.
    Kept in code (not in DB) for easier versioning and updates.
    """
    name: str  # e.g. "extract_text"
    description: Optional[str] = None
    sequence: int  # The order in which this step occurs (1, 2, 3, etc.)
    is_mandatory: bool = True  # Whether this step is required before continuing


class ProcessingWorkflowHandler:
    """
    A handler that manages a set of ProcessingStepDefinition objects
    and provides convenience methods for retrieving next steps, etc.
    """

    def __init__(self, steps: List[ProcessingStepDefinition]):
        # Sort steps by sequence so that we can navigate them in order
        self.steps = sorted(steps, key=lambda s: s.sequence)

    def get_all_steps(self) -> List[ProcessingStepDefinition]:
        """
        Return all steps in sorted order.
        """
        return self.steps

    def get_first_step(self) -> Optional[ProcessingStepDefinition]:
        """
        Return the first step in the workflow, or None if no steps defined.
        """
        return self.steps[0] if self.steps else None

    def get_next_step(self, current_step_name: str) -> Optional[ProcessingStepDefinition]:
        """
        Given the name of the current step, find the next step in sequence.
        Returns None if at the last step or if current_step_name not found.
        """
        for i, step in enumerate(self.steps):
            if step.name == current_step_name:
                # If there's a step after this one, return it
                if i + 1 < len(self.steps):
                    return self.steps[i + 1]
                else:
                    return None
        return None  # current step name not found

    def get_step_by_name(self, step_name: str) -> Optional[ProcessingStepDefinition]:
        """
        Retrieve a specific step by name.
        """
        for step in self.steps:
            if step.name == step_name:
                return step
        return None
