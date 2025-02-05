from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any

from database.docements_processing_database import ProcessingStateCreate, create_processing_state, get_processing_state, update_processing_state, get_processing_step_result, \
    ProcessingStepResultCreate, create_processing_step_result, update_processing_step_result
from features.docs_processing.processing_steps import ProcessingWorkflowHandler


class DocumentProcessingOrchestrator:
    """
    Orchestrates the workflow steps for a single case-document pair
    using a code-defined list of ProcessingStepDefinition objects.
    """

    def __init__(self, workflow_handler: ProcessingWorkflowHandler):
        """
        :param workflow_handler: Handler with the list of steps in sorted order.
        """
        self.workflow_handler = workflow_handler

    async def start_processing(
            self,
            case_id: UUID,
            document_id: UUID
    ) -> None:
        """
        Initiate processing for this document by creating the first step's state if not existing.
        """
        first_step = self.workflow_handler.get_first_step()
        if not first_step:
            print("No steps defined in the workflow; nothing to do.")
            return

        state_in = ProcessingStateCreate(
            case_id=case_id,
            document_id=document_id,
            step_name=first_step.name,
            state="pending",  # 'pending' → we haven't done anything yet
            message=None,
            started_at=None,
            completed_at=None
        )
        await create_processing_state(state_in)
        print(f"Document {document_id} for case {case_id} is now at step: {first_step.name} [pending]")

    async def process_current_step(
            self,
            state_id: UUID,
            result_data: Dict[str, Any],
            embedding_vector: Optional[list[float]] = None
    ) -> None:
        """
        Perform the logic for the current step:
        - Mark the step as 'in_progress'
        - Actually do the 'step' logic (simulated here)
        - Mark the step as 'completed'
        - Store results in processing_step_results
        """
        # 1. Retrieve the existing state to see which step we're on
        current_state = await get_processing_state(state_id)
        if not current_state:
            print("No processing state found, cannot proceed.")
            return

        # 2. Mark state as 'in_progress'
        await update_processing_state(
            state_id,
            {
                "state": "in_progress",
                "message": "Step execution started",
                "started_at": datetime.utcnow()
            }
        )

        # 3. (In a real system, do the actual step logic here)
        # We'll just simulate a pass/fail or do something with 'result_data'

        # 4. Mark state as 'completed'
        updated_state = await update_processing_state(
            state_id,
            {
                "state": "completed",
                "message": "Step execution finished",
                "completed_at": datetime.utcnow()
            }
        )

        # 5. Insert or update processing_step_results
        existing_result = await get_processing_step_result(state_id)
        if not existing_result:
            # Create
            result_in = ProcessingStepResultCreate(
                processing_state_id=state_id,
                result=result_data,
                embedding_prop=embedding_vector
            )
            await create_processing_step_result(result_in)
        else:
            # Update
            await update_processing_step_result(
                state_id,
                {
                    "result": result_data,
                    "embedding_prop": embedding_vector
                }
            )

        print(f"Step '{updated_state.step_name}' completed with state_id={state_id}. Results saved.")

    async def advance_to_next_step(
            self,
            state_id: UUID
    ) -> None:
        """
        Looks at the current step, finds the next step from workflow_handler,
        and creates a new processing_state entry for that next step if it exists.
        """
        current_state = await get_processing_state(state_id)
        if not current_state:
            print("Cannot advance steps; current state missing.")
            return

        # 1. Identify next step from our workflow definition
        next_step = self.workflow_handler.get_next_step(current_state.step_name)
        if not next_step:
            print(f"No next step after '{current_state.step_name}'. Workflow is complete.")
            return

        # 2. Create a new processing_state for the next step
        next_state_in = ProcessingStateCreate(
            case_id=current_state.case_id,
            document_id=current_state.document_id,
            step_name=next_step.name,
            state="pending",
            message=None,
            started_at=None,
            completed_at=None
        )
        new_state = await create_processing_state(next_state_in)
        print(f"Document {current_state.document_id} advanced to step '{next_step.name}' with state={new_state.id}.")
