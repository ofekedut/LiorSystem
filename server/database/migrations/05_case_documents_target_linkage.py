"""
Database migration to ensure case_documents table has proper columns
for document type and entity linkage.

This migration ensures the case_documents table structure matches the requirements
in the document management backend integration guide.
"""
from typing import List

UP_QUERIES = [
    # Ensure target_object_type and target_object_id columns exist
    """
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='case_documents' AND column_name='target_object_type'
        ) THEN
            ALTER TABLE case_documents ADD COLUMN target_object_type VARCHAR(50);
        END IF;
    END $$;
    """,
    """
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='case_documents' AND column_name='target_object_id'
        ) THEN
            ALTER TABLE case_documents ADD COLUMN target_object_id UUID;
        END IF;
    END $$;
    """,
    
    # Ensure processing_status column exists
    """
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='case_documents' AND column_name='processing_status'
        ) THEN
            ALTER TABLE case_documents ADD COLUMN processing_status VARCHAR(30) NOT NULL DEFAULT 'pending';
        END IF;
    END $$;
    """,
    
    # Ensure doc_type_id column references unique_doc_types table
    """
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_case_documents_doc_type_id' 
            AND table_name = 'case_documents'
        ) THEN
            ALTER TABLE case_documents 
            ADD CONSTRAINT fk_case_documents_doc_type_id 
            FOREIGN KEY (doc_type_id) 
            REFERENCES unique_doc_types(id);
        END IF;
    END $$;
    """,
    
    # Create document_version_history table if it doesn't exist
    """
    CREATE TABLE IF NOT EXISTS document_version_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_document_id UUID NOT NULL REFERENCES case_documents(id) ON DELETE CASCADE,
        version_number INT NOT NULL,
        file_path TEXT NOT NULL,
        uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        uploaded_by UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        UNIQUE(case_document_id, version_number)
    );
    """,
    
    # Create index for target object lookup
    """
    CREATE INDEX IF NOT EXISTS idx_case_documents_target_object ON case_documents(target_object_type, target_object_id);
    """,
    
    # Create index for doc_type_id lookup
    """
    CREATE INDEX IF NOT EXISTS idx_case_documents_doc_type_id ON case_documents(doc_type_id);
    """
]

DOWN_QUERIES: List[str] = []  # We don't want to reverse these migrations
