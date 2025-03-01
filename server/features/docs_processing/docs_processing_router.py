# file: docs_processing_router.py

from fastapi import APIRouter, FastAPI, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
import os
import uuid

from starlette.responses import JSONResponse

from server.features.docs_processing.document_processing_db import (
    get_all_results,
    update_correct_category,
    init_db, 
    get_labels,
    get_document_category_enum,
    get_result_by_filename
)

router = APIRouter(prefix="/processing")

# Global labels variable to cache results
_labels = None


@router.get("/result", response_class=HTMLResponse)
async def view_result(index: int = 0) -> HTMLResponse:
    """
    Displays one classification result by index.
    """
    results = await get_all_results()
    
    # Get labels
    global _labels
    if _labels is None:
        _labels = await get_labels()
        
    # Generate HTML with the current result
    # ... rest of the implementation
    html_content = "Result implementation"
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/get-labels", response_class=HTMLResponse)
async def view_labels() -> HTMLResponse:
    """Return labels in HTML format"""
    # Get labels from database
    global _labels
    if _labels is None:
        _labels = await get_labels()
    
    # Generate HTML with labels
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Document Categories</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { padding: 8px; text-align: left; border: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
      </style>
    </head>
    <body>
      <h1>Document Categories</h1>
      <table>
        <tr>
          <th>Code</th>
          <th>Name</th>
          <th>Hebrew</th>
        </tr>
    """
    
    for key, item in _labels.items():
        html_content += f"""
        <tr>
          <td>{item['code']}</td>
          <td>{key}</td>
          <td>{item['hebrew']}</td>
        </tr>
        """
    
    html_content += """
      </table>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)


@router.post("/result/update", response_class=HTMLResponse)
async def update_result(record_id: str = Form(...), correction: str = Form(...), index: int = Form(...)) -> HTMLResponse:
    """
    Updates user correction for a record. Then auto-redirects to the next file (or stays on the same if none).
    """
    # Convert string UUID to UUID object
    from uuid import UUID
    record_uuid = UUID(record_id)
    
    await update_correct_category(record_uuid, correction)
    results = await get_all_results()
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
async def list_results() -> HTMLResponse:
    """
    Lists all classification results with links to view each individually.
    """
    results = await get_all_results()
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
        record_id = row['id']
        file_name = row['file_name']
        category_name = row['category_name']
        
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


@app.on_event("startup")
async def startup_event():
    """
    Initialize the DB on app startup, just to be sure.
    """
    await init_db()
    # Also preload labels
    global _labels
    _labels = await get_labels()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
