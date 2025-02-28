# file: results_app.py

from fastapi import APIRouter, FastAPI, Form
from fastapi.responses import HTMLResponse
import os

from starlette.responses import JSONResponse

from server.features.docs_processing.document_processing_db import (
    get_all_results,
    DB_FILENAME,
    update_correct_category,
    init_db, DocumentCategory,
)

router = APIRouter(prefix="/processing")




@router.get("/result", response_class=JSONResponse)
def view_result(index: int = 0) -> HTMLResponse:
    """
    Displays one classification result by index.
    """
    results = get_all_results(DB_FILENAME)
    return HTMLResponse(content=html_content, status_code=200)

@router.get("/get-labels", response_class=HTMLResponse)
def view_result(index: int = 0) -> HTMLResponse:

    return HTMLResponse(content=html_content, status_code=200)


@router.post("/result/update", response_class=HTMLResponse)
def update_result(record_id: int = Form(...), correction: str = Form(...), index: int = Form(...)) -> HTMLResponse:
    """
    Updates user correction for a record. Then auto-redirects to the next file (or stays on the same if none).
    """
    update_correct_category(record_id, correction)
    results = get_all_results(DB_FILENAME)
    total = len(results)
    next_index = index + 1 if (index + 1) < total else index
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta http-equiv="refresh" content="1; url=/result?index={next_index}" />
    </head>
    <body>
      <p>Correction updated. Redirecting...</p>
      <p>If you are not redirected automatically, <a href="/result?index={next_index}">click here</a>.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)


@router.get("/results", response_class=HTMLResponse)
def list_results() -> HTMLResponse:
    """
    Lists all classification results with links to view each individually.
    """
    results = get_all_results(DB_FILENAME)
    if not results:
        return HTMLResponse("<h1>No classification results found.</h1>", status_code=200)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>All Document Processing Results</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        ul { list-style: none; padding: 0; }
        li { margin: 5px 0; }
        a { text-decoration: none; color: #333; }
      </style>
    </head>
    <body>
      <h1>All Document Processing Results</h1>
      <ul>
    """
    for idx, row in enumerate(results):
        (
            record_id,
            file_name,
            category_id,
            category_name,
            confidence,
            reasons,
            page_count,
            error,
            correct_category,
            processed_at,
            extracted_text
        ) = row
        cat_display = category_name if category_name else "N/A"
        html += f'<li><a href="/result?index={idx}">{file_name} - {cat_display}</a></li>'
    html += """
      </ul>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)


app = FastAPI()
app.include_router(router)


# app.mount("/monday_assets", StaticFiles(directory="monday_assets"), name="monday_assets")


@app.on_event("startup")
def startup_event():
    """
    Initialize the DB on app startup, just to be sure.
    """
    init_db()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run('docs_processing_router:app', host="0.0.0.0", port=8000, reload=True)
