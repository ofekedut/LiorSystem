# api.py
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from server.routers.person_assets_router import router as person_assets_router
from server.routers.unique_docs_router import router as unique_docs_router
from server.database.users_database import UserCreate, create_user, update_user_role, UserRole
from server.database.database import create_schema_if_not_exists, drop_all_tables
from server.database.d_migrations import run_migrations
from server.database.documents_database import list_tables
from server.routers.documents_router import router as documents_router
from server.routers.users_router import router as users_router
from server.routers.cases_router import router as cases_router
from server.routers.auth_router import router as auth_router
from server.routers.fin_org_router import router as fin_org_router
from server.routers.employment_history_router import router as employment_history_router
from server.routers.income_sources_router import router as income_sources_router
from server.routers.bank_accounts_router import router as bank_accounts_router
from server.routers.credit_cards_person_router import router as credit_cards_router
from server.routers.person_loans_router import router as person_loans_router
from server.routers.person_relationships_router import router as person_relationships_router
from server.routers.companies_router import router as companies_router
from server.routers.case_formatter_router import router as case_formatter_router
from server.routers.lior_dropdown_options_router import router as dropdown_options_router

from server.features.docs_processing.docs_processing_router import router as docs_processing_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    tables = await list_tables()
    for table in tables:
        print(table)
    user_data = UserCreate(
        password="123456qQ!",
        first_name='Super',
        last_name='Ofek',
        email='ofekedut345@gmail.com'
    )
    try:
        user = await create_user(user_data)
        print("User created")
        await  update_user_role(user.id, "admin")
        print("User role set")
    except Exception as e:
        print("User creation failed")
        print(e)
        pass
    yield


app = FastAPI(title="Document Management API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/hello")
async def read_documents():
    """
    Retrieve all documents.
    """
    return HTMLResponse(content="<h1>Hello</h1>")


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(cases_router)
app.include_router(fin_org_router)
app.include_router(person_assets_router)
app.include_router(docs_processing_router)
app.include_router(employment_history_router)
app.include_router(income_sources_router)
app.include_router(bank_accounts_router)
app.include_router(credit_cards_router)
app.include_router(person_loans_router)
app.include_router(person_relationships_router)
app.include_router(companies_router)
app.include_router(case_formatter_router)
app.include_router(dropdown_options_router)
app.include_router(unique_docs_router)


async def create_schema_and_admin():
    await drop_all_tables()
    await create_schema_if_not_exists()
    await run_migrations()
    


if __name__ == "__main__":
    asyncio.run(create_schema_and_admin())
    uvicorn.run("server.api:app", host="0.0.0.0", port=8000, workers=1)
