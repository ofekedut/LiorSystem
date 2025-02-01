# database.py
import asyncpg
import logging

from server.database.database_schema import CREATE_SCHEMA_QUERIES, DROP_ALL_QUERIES

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dsn": "postgresql://lior_user:lior3412312qQ@localhost:5432/lior_system"
}

async def get_connection():
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect: {str(e)}")
        raise



# -------------------------------------------------
# 4. Schema Management Functions
# -------------------------------------------------
async def create_schema_if_not_exists() -> None:
    """Create document-related schema objects"""
    conn = await get_connection()
    try:
        async with conn.transaction():
            for query in CREATE_SCHEMA_QUERIES:
                await conn.execute(query)
    finally:
        await conn.close()


async def drop_all_tables() -> None:
    """Drop all document-related database objects"""
    conn = await get_connection()
    try:
        async with conn.transaction():
            await conn.execute(DROP_ALL_QUERIES)
    finally:
        await conn.close()