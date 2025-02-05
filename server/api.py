# api.py
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from server.database.users_database import UserCreate, create_user, update_user_role, UserRole
from server.database.database import create_schema_if_not_exists
from server.database.documents_databse import list_tables
from server.routers.documents_router import router as documents_router
from server.routers.users_router import router as users_router
from server.routers.cases_router import router as cases_router
from server.routers.auth_router import router as auth_router
from server.routers.fin_org_router import router as fin_org_router


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


async def create_schema_and_admin():
    await create_schema_if_not_exists()


if __name__ == "__main__":
    asyncio.run(create_schema_and_admin())
    uvicorn.run("server.api:app", host="0.0.0.0", port=8000, workers=1)
