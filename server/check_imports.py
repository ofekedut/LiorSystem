"""
Simple script to check if the database schema and migrations can be imported without errors.
"""
import sys
print("Starting import check")

try:
    from server.database.database_schema import CREATE_SCHEMA_QUERIES
    print("✅ Successfully imported database_schema")
except Exception as e:
    print(f"❌ Error importing database_schema: {e}")
    sys.exit(1)

try:
    from server.database.d_migrations import run_migrations
    print("✅ Successfully imported d_migrations")
except Exception as e:
    print(f"❌ Error importing d_migrations: {e}")
    sys.exit(1)

try:
    from server.database.unique_docs_database import (
        UniqueDocTypeCreate,
        DocumentCategory,
        DocumentTargetObject,
        DocumentType,
        DocumentFrequency,
        RequiredFor,
        create_unique_doc_type
    )
    print("✅ Successfully imported unique_docs_database")
except Exception as e:
    print(f"❌ Error importing unique_docs_database: {e}")
    sys.exit(1)

print("All imports successful!")
