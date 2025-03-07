#!/usr/bin/env python3

import asyncio
import asyncpg
import os
from server.database.database import get_connection

async def fix_document_type_ids():
    """
    This script fixes the document_type_id column in the documents table
    by setting a default document type ID for all documents where it's NULL.
    """
    conn = await get_connection()
    try:
        # 1. First, verify that document types exist
        doc_types = await conn.fetch("SELECT id, name, value FROM document_types")
        if not doc_types:
            print("❌ No document types found in the database.")
            return False
        
        print(f"✅ Found {len(doc_types)} document types:")
        for dt in doc_types:
            print(f"  • {dt['name']} ({dt['value']}): {dt['id']}")
        
        # Get the 'other' document type as a fallback
        other_doc_type = None
        for dt in doc_types:
            if dt['value'] == 'other':
                other_doc_type = dt
                break
        
        if not other_doc_type:
            print("❌ Could not find 'other' document type. Using the first available type.")
            other_doc_type = doc_types[0]
        
        # 2. Check for documents with NULL document_type_id
        null_docs = await conn.fetch("SELECT id, name FROM documents WHERE document_type_id IS NULL")
        if not null_docs:
            print("✅ No documents found with NULL document_type_id.")
            return True
        
        print(f"⚠️ Found {len(null_docs)} documents with NULL document_type_id:")
        for doc in null_docs:
            print(f"  • {doc['name']} ({doc['id']})")
        
        # 3. Fix documents with NULL document_type_id
        print(f"\nFixing documents with NULL document_type_id using default type: {other_doc_type['name']} ({other_doc_type['id']})")
        
        async with conn.transaction():
            result = await conn.execute(
                "UPDATE documents SET document_type_id = $1 WHERE document_type_id IS NULL",
                other_doc_type['id']
            )
            print(f"✅ Update result: {result}")
        
        # 4. Verify fix
        null_docs_after = await conn.fetch("SELECT id, name FROM documents WHERE document_type_id IS NULL")
        if not null_docs_after:
            print("✅ All documents now have a valid document_type_id.")
            return True
        else:
            print(f"❌ Still found {len(null_docs_after)} documents with NULL document_type_id.")
            return False
            
    finally:
        await conn.close()

async def main():
    success = await fix_document_type_ids()
    if success:
        print("\n✅ Database schema fixed successfully!")
    else:
        print("\n❌ Failed to fix database schema.")

if __name__ == "__main__":
    asyncio.run(main())
