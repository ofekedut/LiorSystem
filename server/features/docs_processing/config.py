from features.docs_processing.processing_orchestrator import DocumentProcessingOrchestrator
from features.docs_processing.processing_steps import ProcessingStepDefinition, ProcessingWorkflowHandler

PROCESSING_STEPS = [
    ProcessingStepDefinition(
        name="detect_document_type",
        description="Automatically determine the document type using machine learning classification.",
        sequence=1,
    ),
    ProcessingStepDefinition(
        name="ask_the_user_if_type_correct",
        description="Prompt the user to confirm or correct the detected document type.",
        sequence=2
    ),
    ProcessingStepDefinition(
        name="detect_document_type_was_wrong_fix_and_punish",
        description="If the user indicates an error in the detected type, adjust the classification and log the discrepancy.",
        sequence=3
    ),
    ProcessingStepDefinition(
        name="extract_text",
        description="Extract text from the document using OCR and related techniques.",
        sequence=4
    ),
    ProcessingStepDefinition(
        name="get_visual_embedings",
        description="Generate visual embeddings from the document images using a dedicated model.",
        sequence=5
    ),
    ProcessingStepDefinition(
        name="get_text_embedings",
        description="Generate text embeddings from the extracted text for semantic analysis.",
        sequence=6
    ),
    ProcessingStepDefinition(
        name="parse_fields",
        description="Parse and extract structured fields from the document's text.",
        sequence=7
    ),
    ProcessingStepDefinition(
        name="analyze_content",
        description="Perform in-depth analysis of the document content to derive insights.",
        sequence=8
    ),
    ProcessingStepDefinition(
        name="add_data_to_case",
        description="Integrate the extracted and analyzed data into the case record.",
        sequence=9
    ),
    ProcessingStepDefinition(
        name="report_extraction_completed",
        description="Finalize the extraction process and report the completion status.",
        sequence=10
    ),
]
PROCESSING_WORKFLOW = ProcessingWorkflowHandler(PROCESSING_STEPS)
PROCESSING_ORCHESTRATOR = DocumentProcessingOrchestrator(PROCESSING_WORKFLOW)
