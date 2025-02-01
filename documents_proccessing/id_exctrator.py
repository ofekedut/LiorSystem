import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ollama_llm.bedrock_llm import BedrockConfig, BedrockClient, define_tool, BedrockMessage, BedrockMessageContent, BedrockImage


@dataclass
class ExtractionResponse:
    extracted_fields: Dict[str, Any]
    usage: Dict[str, int]
    stop_reason: str
    raw_response: Dict[str, Any]


class IDDataTool:
    TOOL_DEFINITION = define_tool(
        name="save_id_data",
        description="Save extracted ID information to a JSON file",
        properties={
            "id_number": ("string", "ID number"),
            "full_name": ("string", "Full name in Hebrew"),
            "date_of_birth": ("string", "Date of birth (YYYY-MM-DD)"),
            "issue_date": ("string", "ID issue date"),
            "expiration_date": ("string", "ID expiration date"),
            "gender": ("string", "Gender in Hebrew (זכר/נקבה)"),
        }
    )


class IDExtractor:
    def __init__(self, config: Optional[BedrockConfig] = None):
        self.bedrock_client = BedrockClient(config)
        self.data_tool = IDDataTool()

    def _get_system_prompt(self) -> str:
        return """You are a specialized document details extractor for mortgage brokerage purposes. 
Your task is to analyze identification documents and extract key data points accurately.

When you find the information, you should call the save_id_data tool with the extracted fields.

Focus on these critical aspects:
1. ID Number (including validation)
2. Full Name (properly formatted, in Hebrew if available)
3. Date of Birth (formatted as YYYY-MM-DD)
4. ID Issue Date (formatted as YYYY-MM-DD)
5. ID Expiration Date (formatted as YYYY-MM-DD)
6. Gender (in Hebrew, זכר/נקבה)
7. Grandpa Name (optional, if present on the ID)

Important Guidelines:
- Extract the exact numbers and dates as they appear on the document.
- Ensure proper formatting of Hebrew names and maintain consistency with official records.
- If any field is unclear, incomplete, or missing, use `null` as the value.
- Pay special attention to Hebrew/English character distinctions when reading text.
- Avoid making assumptions about missing data; stick to what's explicitly on the document.
- Always ensure sensitive information is handled securely and adheres to privacy standards.
- Focus on accurate data extraction for use in mortgage-related applications.

### Tool Usage
You must not return the data directly in your response. Instead, you should use the `save_id_data` tool to store the extracted information. Pass the data fields as input to the tool in the following format:
```json
{
    "id_number": "123456789",
    "full_name": "אדם דוגמא",
    "date_of_birth": "1985-05-15",
    "issue_date": "2015-03-01",
    "expiration_date": "2025-03-01",
    "gender": "זכר"
}
"""

    def extract_from_image(self, image_path: str) -> ExtractionResponse:
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            with open(image_path, 'rb') as f:
                image_data = f.read()

            messages = [
                BedrockMessage(
                    role='user', content=[
                        BedrockMessageContent(
                            text='Extract information from this ID document:',
                            image=None
                        )
                        , BedrockMessageContent(
                            text=None,
                            image=BedrockImage(
                                format=image_path.suffix[1:],
                                source={"bytes": image_data}
                            )
                        )
                    ]
                )
            ]

            system = [{'text': self._get_system_prompt()}]
            tool_config = {"tools": [{'toolSpec': self.data_tool.TOOL_DEFINITION}]}

            response = self.bedrock_client.converse(messages=[x.to_dict() for x in messages], system=system, tool_config=tool_config)

            if response.get('stopReason') == 'tool_use':
                tool_call = next(
                    (x for x in response['output']['message']['content'] if x.get('toolUse')), None
                )
                if tool_call and tool_call['toolUse']['name'] == 'save_id_data':
                    saved_data = tool_call['toolUse']['input']
                return ExtractionResponse(
                    extracted_fields=saved_data,
                    usage={
                        "input_tokens": response['usage']['inputTokens'],
                        "output_tokens": response['usage']['outputTokens'],
                        "total_tokens": response['usage']['totalTokens']
                    },
                    stop_reason=response['stopReason'],
                    raw_response=response
                )

                return ExtractionResponse(
                    extracted_fields={},
                    usage=response['usage'],
                    stop_reason=response['stopReason'],
                    raw_response=response
                )

        except Exception as e:
            raise Exception(f"Extraction failed: {str(e)}")


if __name__ == "__main__":
    try:
        extractor = IDExtractor()
        image_path = '/כרטיס ת.ז חדש.png'

        result = extractor.extract_from_image(image_path)

        if result.extracted_fields:
            print("\nExtracted and Saved Fields:")
            print(json.dumps(result.extracted_fields, ensure_ascii=False, indent=2))
            print("\nData has been saved to JSON file")
        else:
            print("\nNo data was extracted or saved")

        print("\nUsage Statistics:")
        print(f"Input Tokens: {result.usage['input_tokens']}")
        print(f"Output Tokens: {result.usage['output_tokens']}")
        print(f"Total Tokens: {result.usage['total_tokens']}")

    except Exception as e:
        print(f"Error: {str(e)}")
