# api.py
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from server.database.users_database import UserCreate, create_user, update_user_role, UserRole
from server.database.database import create_schema_if_not_exists, drop_all_tables
from server.database.d_migrations import run_migrations
from server.database.documents_database import list_tables
from server.routers.documents_router import router as documents_router
from server.routers.users_router import router as users_router
from server.routers.cases_router import router as cases_router
from server.routers.auth_router import router as auth_router
from server.routers.fin_org_router import router as fin_org_router
from server.routers.person_roles_router import router as person_roles_router
from server.routers.bank_account_type_router import router as bank_account_type_router
from server.routers.company_types_router import router as company_types_router
from server.routers.credit_card_types_router import router as credit_card_types_router
from server.routers.employment_types_router import router as employment_types_router
from server.routers.income_sources_types_router import router as income_sources_types_router
from server.routers.loan_goals_router import router as loan_goals_router
from server.routers.loan_types_router import router as loan_types_router
from server.routers.person_marital_statuses_router import router as person_marital_statuses_router
from server.routers.related_person_relationships_types_router import router as related_person_relationships_types_router
from server.routers.document_types_router import router as document_types_router
from server.routers.document_categories_router import router as document_categories_router
from server.routers.asset_types_router import router as asset_types_router
from server.routers.person_assets_router import router as person_assets_router
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
        await  update_user_role(user.id, UserRole.ADMIN)
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
app.include_router(person_roles_router)
app.include_router(bank_account_type_router)
app.include_router(company_types_router)
app.include_router(credit_card_types_router)
app.include_router(employment_types_router)
app.include_router(income_sources_types_router)
app.include_router(loan_goals_router)
app.include_router(loan_types_router)
app.include_router(person_marital_statuses_router)
app.include_router(related_person_relationships_types_router)
app.include_router(document_types_router)
app.include_router(document_categories_router)
app.include_router(asset_types_router)
app.include_router(person_assets_router)
app.include_router(docs_processing_router)


async def create_schema_and_admin():
    await drop_all_tables()
    await create_schema_if_not_exists()
    await run_migrations()
    


if __name__ == "__main__":
    asyncio.run(create_schema_and_admin())
    uvicorn.run("server.api:app", host="0.0.0.0", port=8000, workers=1)
