# Unique Documents API Implementation

## Overview

The Unique Documents API has been implemented to provide a structured approach to document type management within the system. This implementation separates:

1. **Unique Document Types** - Templates/definitions for document types with metadata and target object relationships
2. **Case Documents** - Actual document files uploaded to cases, which are instances of specific unique document types

## Implementation Details

### 1. Database Schema Changes

The following tables have been added to the database schema:

#### `unique_doc_types` Table
```sql
CREATE TABLE IF NOT EXISTS unique_doc_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    issuer VARCHAR(255),
    target_object VARCHAR(50) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    is_recurring BOOLEAN NOT NULL DEFAULT false,
    frequency VARCHAR(50),
    links JSONB,
    contact_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

#### `required_for` Junction Table
```sql
CREATE TABLE IF NOT EXISTS required_for (
    doc_type_id UUID REFERENCES unique_doc_types(id) ON DELETE CASCADE,
    required_for VARCHAR(50) NOT NULL,
    PRIMARY KEY (doc_type_id, required_for)
);
```

#### Modified `case_documents` Table
The `case_documents` table has been updated to reference `unique_doc_types` and include target object information:

```sql
CREATE TABLE IF NOT EXISTS case_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    doc_type_id UUID REFERENCES unique_doc_types(id),
    target_object_type VARCHAR(50),
    target_object_id UUID,
    status VARCHAR(20) NOT NULL,
    processing_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    file_path TEXT DEFAULT NULL,
    CONSTRAINT unique_case_document UNIQUE (case_id, document_id)
);
```

### 2. Data Models

The following Pydantic models were implemented:

- **Enumerations**:
  - `DocumentCategory` (identification, financial, property, etc.)
  - `DocumentTargetObject` (case, person, bank_account, etc.)
  - `DocumentType` (one_time, updatable, recurring)
  - `DocumentFrequency` (monthly, quarterly, yearly)
  - `RequiredFor` (employees, self_employed, business_owners)

- **Base Models**:
  - `ContactInfo` - Contains optional contact information
  - `Links` - Contains optional URLs for additional information
  - `UniqueDocTypeBase` - Base document type attributes
  
- **Request/Response Models**:
  - `UniqueDocTypeCreate` - For creating document types
  - `UniqueDocTypeUpdate` - For updating document types
  - `UniqueDocTypeInDB` - Full document type information with ID and timestamps

### 3. Database Operations

The database layer implements the following operations:

- **CRUD Operations for Unique Doc Types**:
  - `create_unique_doc_type()`
  - `get_unique_doc_type()`
  - `update_unique_doc_type()`
  - `delete_unique_doc_type()`
  - `list_unique_doc_types()`
  
- **Filtering Functions**:
  - `filter_by_category()` - Get document types by category
  - `filter_by_target_object()` - Get document types by target object
  
- **Validation Functions**:
  - `is_doc_type_in_use()` - Check if a document type is referenced by case documents

- **Case Documents Operations**:
  - `create_case_document()`
  - `get_case_document()`
  - `update_case_document()`
  - `delete_case_document()`
  - `get_case_documents()`
  - `get_documents_by_doc_type()`
  - `get_documents_by_target_object()`

### 4. API Endpoints

The following REST API endpoints have been implemented:

- **Document Types Management**:
  - `GET /unique-docs` - List all document types
  - `GET /unique-docs/{id}` - Get a specific document type
  - `POST /unique-docs` - Create a new document type
  - `PUT /unique-docs/{id}` - Update a document type
  - `DELETE /unique-docs/{id}` - Delete a document type
  
- **Filtering Endpoints**:
  - `GET /unique-docs/category/{category}` - Filter by category
  - `GET /unique-docs/target/{targetObject}` - Filter by target object

### 5. Error Handling

The API implements proper error handling:

- Validation of required fields
- Check for frequency on recurring documents
- Prevention of deletion for document types in use
- Appropriate HTTP status codes (400, 404, 409) with descriptive messages

## Usage Examples

### Creating a Document Type

```json
POST /unique-docs
{
  "display_name": "Bank Statement",
  "category": "financial",
  "issuer": "All Banks",
  "target_object": "bank_account",
  "document_type": "recurring",
  "is_recurring": true,
  "frequency": "monthly",
  "required_for": ["employees", "self_employed", "business_owners"],
  "links": {
    "url": "https://example.com/bank-statements-guide"
  },
  "contact_info": {
    "email": "support@lior.com",
    "phone": "123-456-7890"
  }
}
```

### Filtering by Target Object

```
GET /unique-docs/target/bank_account
```

This returns all document types that relate to bank accounts, which can be shown when a user is uploading a document to a bank account.

## Integration with Document Upload Flow

The document upload flow will now be able to:

1. List appropriate document types based on context (e.g., only show bank account related document types when a bank account is selected)
2. Save uploaded documents with proper document type and target object linkages
3. Find related documents by object (e.g., "Show me all documents for this bank account")

## Future Extensions

The implemented API supports future extensions such as:

1. Document status tracking (e.g., "Bank statement for account 123 is missing for March")
2. Intelligent document type detection based on content analysis
3. Document expiration and renewal reminders based on frequency
4. Role-based document requirements (e.g., different documents for different client types)
