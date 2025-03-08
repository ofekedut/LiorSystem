# database.py
import asyncpg
import logging
import asyncio
import re
from server.database.database_schema import CREATE_SCHEMA_QUERIES, DROP_ALL_QUERIES

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

async def create_schema_if_not_exists() -> None:
    conn = await get_connection()
    try:
        async with conn.transaction():
            for query in CREATE_SCHEMA_QUERIES:
                # Check if the query is a CREATE TABLE statement
                query_upper = query.strip().upper()
                if query_upper.startswith("CREATE TABLE"):
                    # Extract table name, handling quoted or unquoted names
                    match = re.search(r'CREATE TABLE\s+(".*?"|\S+)', query, re.IGNORECASE)
                    if match:
                        table_name = match.group(1).strip('"')
                        print(f"Creating table: {table_name}")
                res = await conn.execute(query)
                print(res)
        logger.info("Schema created successfully.")
    except Exception as e:
        logger.error(f"Failed to create schema: {str(e)}")
        raise
    finally:
        await conn.close()

async def drop_all_tables() -> None:
    conn = await get_connection()
    try:
        async with conn.transaction():
            await conn.execute(DROP_ALL_QUERIES)
        logger.info("All tables dropped successfully.")
    except Exception as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        raise
    finally:
        await conn.close()

async def list_tables() -> None:
    conn = await get_connection()
    try:
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        print("Tables in the database:")
        for table in tables:
            print(table['table_name'])
    finally:
        await conn.close()

async def main():
    await drop_all_tables()
    await create_schema_if_not_exists()
    await list_tables()

if __name__ == "__main__":
    asyncio.run(main())