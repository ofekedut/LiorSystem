import os
import json
from typing import List, Optional, Dict
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# === IMPORTS FROM YOUR PROJECT CODE ===
# Adjust these imports to match your actual file/module names
from text_extraction import DocumentProcessor, PDFProcessor, OCRConfig
from database_service import DocumentStorageService
from visual_ai import LLMService
from fuzzy_searcher import FuzzySearch


# === Initialize Components ===
config = OCRConfig()
doc_processor = DocumentProcessor(config)
pdf_processor = PDFProcessor(config)
llm_service = LLMService(base_url="http://localhost:11434")
storage_service = DocumentStorageService(doc_processor, llm_service)


# === FastAPI App ===
app = FastAPI(
    title="Document Processing API",
    description="API for processing documents with OCR and AI validation",
    version="1.0.0"
)

# Mount static directory to serve index.html, style.css, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

# === Add CORS Middleware (if needed) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Pydantic Models ===
class ProcessingOptions(BaseModel):
    language: str = "eng"
    preprocess_passes: int = 2
    search_values: List[str] = []
    custom_regex_patterns: List[str] = []


class SearchQuery(BaseModel):
    keyword: str
    threshold: int = 75
    regex_patterns: List[str] = []


class ProcessingResponse(BaseModel):
    document_id: str
    filename: str
    processing_time: float
    ocr_confidence: float
    validated_data: Dict
    search_results: Optional[Dict] = None


# === Endpoints ===

@app.post("/documents/upload", response_model=ProcessingResponse)
async def upload_document(
    file: UploadFile = File(...),
    options: ProcessingOptions = ProcessingOptions()
):
    """
    Upload and process a single document (PDF or image).
    Returns extracted and validated information.
    """
    try:
        # Read file content
        content = await file.read()

        # Process based on file type
        if file.filename.lower().endswith('.pdf'):
            result = pdf_processor.process_pdf(
                content,
                language=options.language,
                preprocess_passes=options.preprocess_passes
            )
            # Combine text from all pages
            text = ' '.join(page['text'] for page in result['pages'])
            confidence = sum(page['confidence'] for page in result['pages']) / len(result['pages'])
        else:
            result = doc_processor.process_document(
                content,
                filename=file.filename,
                language=options.language,
                preprocess_passes=options.preprocess_passes
            )
            text = result['text']
            confidence = result['confidence']

        # Perform fuzzy search if search values are provided
        search_results = None
        if options.search_values:
            fuzzy = FuzzySearch(
                keyword=options.search_values[0],  # Primary search term
                regex_patterns=options.custom_regex_patterns or [
                    r"\b\w+\b"  # Default pattern
                ],
                text=text,
                values=options.search_values,
                threshold=75
            )
            search_results = fuzzy.search()

        # Store in DB and get validated data from LLM
        validated_data = storage_service.process_and_store_document(
            document_path=file.filename,
            search_values=options.search_values,
            previous_results=search_results or {},
            ai_messages=[{
                "role": "system",
                "content": "Extract and validate document information."
            }]
        )

        return ProcessingResponse(
            document_id=str(validated_data.get('id', '')),
            filename=file.filename,
            processing_time=result.get('processing_time', 0),
            ocr_confidence=confidence,
            validated_data=validated_data,
            search_results=search_results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/batch", response_model=List[ProcessingResponse])
async def upload_batch(
    files: List[UploadFile] = File(...),
    options: ProcessingOptions = ProcessingOptions()
):
    """
    Process multiple documents in a batch.
    """
    results = []
    for file in files:
        try:
            result = await upload_document(file, options)
            results.append(result)
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
    return results


@app.post("/documents/search")
async def search_documents(query: SearchQuery):
    """
    Search through processed documents using fuzzy matching.
    """
    try:
        # The following method _connect() is assumed to exist 
        # within DocumentStorageService or you might have a different approach:
        with storage_service._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM document_interactions")
            documents = cursor.fetchall()

        results = []
        for doc in documents:
            doc_id = doc[0]          # ID (AUTOINCREMENT)
            doc_path = doc[1]       # document_path
            ocr_text = doc[2]       # ocr_text

            fuzzy = FuzzySearch(
                keyword=query.keyword,
                regex_patterns=query.regex_patterns,
                text=ocr_text,
                values=[query.keyword],
                threshold=query.threshold
            )
            search_result = fuzzy.search()
            # If either fuzzy or regex matches exist
            if search_result['fuzzy_results'] or search_result['regex_matches']:
                results.append({
                    "document_id": doc_id,
                    "filename": os.path.basename(doc_path),
                    "matches": search_result
                })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}")
async def get_document(document_id: int = Path(..., description="The ID of the document to retrieve")):
    """
    Retrieve a specific document's processed information.
    """
    try:
        with storage_service._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM document_interactions WHERE id = ?",
                (document_id,)
            )
            doc = cursor.fetchone()

            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            return {
                "id": doc[0],
                "filename": os.path.basename(doc[1]),
                "ocr_text": doc[2],
                "validated_data": json.loads(doc[3]),
                "conversation_history": json.loads(doc[4]),
                "created_at": doc[5]
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    List processed documents with pagination.
    """
    try:
        with storage_service._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM document_interactions ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, skip)
            )
            documents = cursor.fetchall()

            return [{
                "id": doc[0],
                "filename": os.path.basename(doc[1]),
                "created_at": doc[5],
                "validated_data": json.loads(doc[3])
            } for doc in documents]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
