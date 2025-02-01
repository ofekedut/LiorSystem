import logging
import requests
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMService:
    """
    A comprehensive AI service class for interacting with a locally running LLM instance
    (e.g., Ollama). It supports:
      - Data validation and refinement (tool calls),
      - Free-form chat messages in a conversational context,
      - Storing conversation history,
      - Handling user corrections and revalidation.
    """

    def __init__(
            self,
            base_url: str = "http://localhost:11434",
            model_name: str = "llama3.2-vision"
    ):
        """
        Initialize the LLM service.
        Args:
            base_url (str): The base URL for the LLM endpoint.
            model_name (str): The LLM model name (e.g., "llama3.2-vision").
        """
        self.base_url = base_url
        self.model_name = model_name

        # Will store the latest validated or processed data for further refinement
        self.current_data: Optional[Dict[str, Any]] = None

        # Holds a list of messages forming a conversation history
        # Example format: [{"role": "system", "content": "..."}, ...]
        self.conversation_history: List[Dict[str, str]] = []

    def prepare_query(
            self,
            data: Dict[str, Any],
            instructions: str,
            include_history: bool = True
    ) -> Dict[str, Any]:
        """
        Prepares a query payload to send to the LLM.

        Args:
            data (Dict[str, Any]): The data/context to validate or discuss with the LLM.
            instructions (str): High-level instructions for the LLM.
            include_history (bool): Whether to include the conversation history.

        Returns:
            Dict[str, Any]: The query payload to send to the LLM endpoint.
        """
        query = {
            "instructions": instructions,
            "data": data
        }
        if include_history:
            query["conversation_history"] = self.conversation_history
        return query

    def query_model(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send the query payload to the LLM endpoint and get the response.

        Args:
            query (Dict[str, Any]): The query payload.

        Returns:
            Dict[str, Any]: The parsed JSON response from the LLM,
                            expected to contain a status and possibly data.
        """
        url = f"{self.base_url}/api/models/{self.model_name}/query"
        logger.info("Sending query to LLM model...")

        try:
            response = requests.post(url, json=query)
            response.raise_for_status()
            logger.info("LLM response received successfully.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to query LLM: {e}")
            return {"status": "error", "message": str(e)}

    def process_response(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process the LLM response, updating conversation history and current data as needed.

        Args:
            response (Dict[str, Any]): The LLM's response.

        Returns:
            Dict[str, Any] | None: Parsed/validated data if successful, or None if there's an error.
        """
        # If there's an assistant message, append it to the conversation history
        if "assistant_message" in response:
            self.conversation_history.append({
                "role": "assistant",
                "content": response["assistant_message"]
            })

        status = response.get("status", "error")
        if status == "success":
            # This field name can vary based on your LLM's output structure
            validated_data = response.get("validated_data", {})
            self.current_data = validated_data
            logger.info("LLM validation/refinement successful.")
            return validated_data

        error_message = response.get("message", "Unknown error from LLM.")
        logger.error(f"LLM response not successful: {error_message}")
        return None

    def send_for_validation(
            self,
            ocr_text: str,
            extracted_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        High-level method to send OCR text and extracted data for initial validation.

        Args:
            ocr_text (str): The raw text extracted by OCR.
            extracted_data (Dict[str, Any]): Data to be validated/refined by the LLM.

        Returns:
            Optional[Dict[str, Any]]: Validated data from the LLM, or None if an error occurred.
        """
        # Start the conversation with a system message (optional)
        self.conversation_history.append({
            "role": "system",
            "content": (
                "You are an AI assistant that validates and refines extracted document data. "
                "Please return valid JSON with the refined data."
            )
        })

        # Merge OCR text into the data payload
        data_payload = {
            "ocr_text": ocr_text,
            "extracted_data": extracted_data
        }

        instructions = (
            "Validate and refine the extracted_data based on the ocr_text. "
            "Return a JSON object in the field 'validated_data' with the corrected or completed data."
        )
        query = self.prepare_query(data_payload, instructions=instructions, include_history=True)
        response = self.query_model(query)
        return self.process_response(response)

    def accept_correction(self, corrections: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Accept user-provided corrections and update the current data.

        Args:
            corrections (Dict[str, Any]): Corrections supplied by the user.

        Returns:
            Optional[Dict[str, Any]]: The updated current data, or None if no data is set.
        """
        if self.current_data is None:
            logger.warning("Cannot apply corrections because no current data is set.")
            return None

        # Log the user's correction in the conversation
        self.conversation_history.append({
            "role": "user",
            "content": f"User corrections: {corrections}"
        })

        # Merge corrections into current data
        self.current_data.update(corrections)
        logger.info("User corrections have been applied to current data.")
        return self.current_data

    def resend_for_revalidation(self, additional_instructions: str = "") -> Optional[Dict[str, Any]]:
        """
        Resend the (corrected) current data to the LLM for revalidation, optionally with more instructions.

        Args:
            additional_instructions (str): Extra instructions for the AI.

        Returns:
            Optional[Dict[str, Any]]: The revalidated data, or None if no current data exists.
        """
        if self.current_data is None:
            logger.warning("No current data to resend for revalidation.")
            return None

        self.conversation_history.append({
            "role": "user",
            "content": "Please revalidate the updated data. " + additional_instructions
        })

        instructions = (
                "Revalidate the current data. Ensure user corrections are accurately reflected. "
                + additional_instructions
        )
        query = self.prepare_query(self.current_data, instructions=instructions, include_history=True)
        response = self.query_model(query)
        return self.process_response(response)

    def send_chat_message(
            self,
            message: str,
            context_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a free-form user message to the AI within the ongoing conversation context.

        Args:
            message (str): The user's message to the AI.
            context_data (Dict[str, Any], optional): Additional data to include in the query.

        Returns:
            Optional[Dict[str, Any]]: The AI's response (e.g., refined data) if available, else None.
        """
        # Append user message to conversation
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        data_payload = context_data if context_data else {}
        instructions = (
            "Continue the conversation with the user. Provide assistance and refine data if needed."
        )
        query = self.prepare_query(data_payload, instructions=instructions, include_history=True)
        response = self.query_model(query)
        return self.process_response(response)
