#!/usr/bin/env python
"""
Generic script to create client cases using the API.
Uses Hebrew values for case fields and can be customized for different clients.
Traverses client directories to process and upload all documents.
"""

import requests
import json
import sys
import os
from pprint import pprint
from datetime import datetime
import glob
from pathlib import Path

# Base URL for the API - adjust if your server runs on a different host/port
BASE_URL = "http://localhost:8000"

# Client definitions with Hebrew values
CLIENTS = {
    "bi_keren_segal": {
        "name": "בני וקרן סגל",
        "status": "active",
        "case_purpose": "משכנתא ראשונה",
        "loan_type": "רוכשים דירה ראשונה",
        "folder_path": "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720650218_בני_וקרן_סגל"
    },
    # "yitzhak_legziel": {
    #     "name": "יצחק לגזיאל",
    #     "status": "active",
    #     "case_purpose": "משכנתא ראשונה",
    #     "loan_type": "רוכשים דירה ראשונה",
    #     "folder_path": "/uploads/yitzhak_legziel"
    # },
    # "svetlana_polyakov": {
    #     "name": "סבטלנה פוליאקוב",
    #     "status": "active",
    #     "case_purpose": "משכנתא ראשונה",
    #     "loan_type": "רוכשים דירה ראשונה",
    #     "folder_path": "/uploads/svetlana_polyakov"
    # },
    # "yaakov_pnina": {
    #     "name": "יעקב רחמים ופנינה בן הראש",
    #     "status": "active",
    #     "case_purpose": "משכנתא ראשונה",
    #     "loan_type": "רוכשים דירה ראשונה",
    #     "folder_path": "/uploads/yaakov_pnina"
    # },
    # "hassan_ula": {
    #     "name": "חסן ועולא אבו ריש",
    #     "status": "active",
    #     "case_purpose": "משכנתא ראשונה",
    #     "loan_type": "רוכשים דירה ראשונה",
    #     "folder_path": "/uploads/hassan_ula"
    # }
    # },
    #     "name": "משפחת יוניס",
    #     "status": "active",
    #     "case_purpose": "משכנתא חדשה",
    #     "loan_type": "דירה להשקעה",
    #     "folder_path": "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/monday_assets_bar/1720649846_התהליכים_של_ליאור/1720654087_יוניס"
    # },
    # "ahmad_udi": {
    #     "name": "אחמד ואודי",
    #     "status": "active",
    #     "case_purpose": "משכנתא משותפת",
    #     "loan_type": "מימון בנייה",
    #     "folder_path": "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/monday_assets_bar/1720649846_התהליכים_של_ליאור/1720654086_אחמד_ואודי"
    # },
    # "hila_ohion": {
    #     "name": "הילה אוחיון",
    #     "status": "active",
    #     "case_purpose": "משכנתא",
    #     "loan_type": "לקוח קיים",
    #     "folder_path": "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/monday_assets_bar/1720649846_התהליכים_של_ליאור/1720654085_הילה_אוחיון"
    # }
}

def create_client_case(client_key):
    """
    Creates a case for the specified client using the API.
    
    Args:
        client_key: Key to use from the CLIENTS dictionary
        
    Returns:
        The created case data or None if creation failed
    """
    if client_key not in CLIENTS:
        print(f"❌ Unknown client key: {client_key}")
        print(f"Valid keys are: {', '.join(CLIENTS.keys())}")
        return None
    
    client_data = CLIENTS[client_key]
    
    case_data = {
        "name": client_data["name"],
        "status": client_data["status"],
        "case_purpose": client_data["case_purpose"],
        "loan_type": client_data["loan_type"],
    }
    
    print(f"Creating case for {client_data['name']}...")
    
    # Call the API to create the case
    try:
        response = requests.post(
            f"{BASE_URL}/cases",
            json=case_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            case = response.json()
            print("✅ Case created successfully!")
            pprint(case)
            return case
        else:
            print(f"❌ Failed to create case. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return None


def list_all_cases():
    """
    Fetches and displays all cases from the API.
    
    Returns:
        List of all cases or None if the request failed
    """
    print("\n📋 Listing all cases...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/cases",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            cases = response.json()
            print(f"✅ Found {len(cases)} cases:")
            
            # Print a summary table
            print("\n{:<40} {:<20} {:<25} {:<20}".format(
                "Name", "Status", "Purpose", "Loan Type"))
            print("-" * 110)
            
            for case in cases:
                print("{:<40} {:<20} {:<25} {:<20}".format(
                    case['name'], 
                    case['status'], 
                    case['case_purpose'], 
                    case['loan_type']
                ))
            
            return cases
        else:
            print(f"❌ Failed to list cases. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return None


def list_document_types():
    """
    Fetches and displays all document types from the API.
    
    Returns:
        List of all document types or None if the request failed
    """
    print("\n📋 Listing all document types...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/document_types",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            doc_types = response.json()
            print(f"✅ Found {len(doc_types)} document types:")
            
            # Print a summary table
            print("\n{:<40} {:<40} {:<40}".format(
                "ID", "Name", "Value"))
            print("-" * 120)
            
            for doc_type in doc_types:
                print("{:<40} {:<40} {:<40}".format(
                    doc_type.get('id', 'N/A'), 
                    doc_type.get('name', 'N/A'), 
                    doc_type.get('value', 'N/A')
                ))
            
            return doc_types
        else:
            print(f"❌ Failed to list document types. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return None


def list_documents():
    """
    Fetches and displays all documents from the API.
    
    Returns:
        List of all documents or None if the request failed
    """
    print("\n📋 Listing all documents...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/documents",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Found {len(documents)} documents:")
            
            # Print a summary table
            print("\n{:<40} {:<40} {:<20} {:<20}".format(
                "Name", "Document Type ID", "Category", "Has Multiple Periods"))
            print("-" * 120)
            
            for doc in documents:
                print("{:<40} {:<40} {:<20} {:<20}".format(
                    doc.get('name', 'N/A'), 
                    doc.get('document_type_id', 'N/A'), 
                    doc.get('category', 'N/A'),
                    str(doc.get('has_multiple_periods', False))
                ))
            
            return documents
        else:
            print(f"❌ Failed to list documents. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return None


def list_document_categories():
    """
    Fetches and displays all document categories from the API.
    
    Returns:
        List of all document categories or None if the request failed
    """
    print("\n📋 Listing all document categories...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/document-categories"
        )
        
        if response.status_code == 200:
            categories = response.json()
            if categories:
                print(f"✅ Found {len(categories)} categories:")
                for cat in categories:
                    print(f"- {cat['name']} ({cat['value']})")
            else:
                print("❌ No categories found.")
            return categories
        else:
            print(f"❌ Failed to get categories. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting categories: {str(e)}")
        return None


def upload_document_to_case(case_id, file_path):
    """
    Uploads a document file to a case without specifying document type.
    This uses a two-step process since there's no direct endpoint to upload a file without document type:
    1. Create a temporary document record
    2. Upload the file to that document
    
    Args:
        case_id: UUID of the case
        file_path: Path to the file to upload
        
    Returns:
        The uploaded document data or None if upload failed
    """
    # First create a temporary document link with a generic document type
    # For now, we'll use "OTHER" as a placeholder
    documents = list_documents()
    if not documents:
        print("Failed to retrieve documents")
        return None
    
    # Find the OTHER document type as a fallback
    document_id = None
    for doc in documents:
        if doc["name"] == "OTHER":
            document_id = doc["id"]
            break
    
    if not document_id:
        # If OTHER not found, use the first document
        document_id = documents[0]["id"]
    
    # Create a case-document link
    payload = {
        "document_id": document_id,
        "case_id": case_id,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    url = f"{BASE_URL}/cases/{case_id}/documents"
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 201:
            print(f"Failed to create document link. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        case_doc = response.json()
        document_id = case_doc["document_id"]
        
        # Now upload the file
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist")
            return None

        # Upload URL
        upload_url = f"{BASE_URL}/cases/{case_id}/documents/{document_id}/upload"
        
        # Prepare the file for upload
        filename = os.path.basename(file_path)
        files = {"file": (filename, open(file_path, "rb"))}
        
        try:
            upload_response = requests.post(upload_url, files=files)
            if upload_response.status_code == 201:
                print(f"Successfully uploaded {filename} to case {case_id}")
                return upload_response.json()
            else:
                print(f"Failed to upload file. Status: {upload_response.status_code}")
                print(f"Response: {upload_response.text}")
                return None
        except Exception as e:
            print(f"Error during file upload: {e}")
            return None
        finally:
            # Make sure file is closed
            files["file"][1].close()
            
    except Exception as e:
        print(f"Error creating document link: {e}")
        return None


def upload_document_file_for_case(case_id, file_path):
    """
    Uploads a document file to a case without specifying document type.
    
    Args:
        case_id: UUID of the case
        file_path: Path to the file to upload
        
    Returns:
        The processed document data or None if any step failed
    """
    # Upload the document directly
    result = upload_document_to_case(case_id, file_path)
    return result


def find_client_files(client_folder_path):
    """
    Find all files in the client's folder and its subdirectories.
    
    Args:
        client_folder_path: Path to the client's folder
        
    Returns:
        List of file paths (only supported file types)
    """
    supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.doc', '.docx', '.xls', '.xlsx']
    files = []
    
    # Check if path exists
    if not os.path.exists(client_folder_path):
        print(f"❌ Client folder not found: {client_folder_path}")
        return files
    
    # Walk through all subdirectories
    for root, dirs, filenames in os.walk(client_folder_path):
        # Skip directories with metadata.json only
        for filename in filenames:
            if filename.lower() == 'metadata.json':
                continue
                
            file_path = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext in supported_extensions:
                files.append(file_path)
    
    return files


def process_client_files(case_id, client_key):
    """
    Process all files for a client and upload them to the case.
    
    Args:
        case_id: UUID of the case
        client_key: Key to use from the CLIENTS dictionary
        
    Returns:
        Number of files successfully processed
    """
    if client_key not in CLIENTS:
        print(f"❌ Unknown client key: {client_key}")
        return 0
    
    client_data = CLIENTS[client_key]
    client_folder = client_data["folder_path"]
    
    # Find all files
    print(f"Finding files in {client_folder}...")
    files = find_client_files(client_folder)
    
    if not files:
        print("No files found for the client.")
        return 0
    
    print(f"Found {len(files)} files to process.")
    
    # Process each file
    successful_uploads = 0
    for file_path in files:
        print(f"\nProcessing file: {os.path.basename(file_path)}")
        result = upload_document_file_for_case(case_id, file_path)
        
        if result:
            successful_uploads += 1
            print(f"✅ Successfully uploaded file {successful_uploads}/{len(files)}")
        else:
            print(f"❌ Failed to upload file: {os.path.basename(file_path)}")
            
        # Small delay to avoid overwhelming the server
        import time
        time.sleep(1)
    
    return successful_uploads


# when we rerun the api we drop all tables, so we need to recreate the case client once
recreate_clients = False
if __name__ == "__main__":
    # Process command line arguments
    client_key = "bi_keren_segal"  # Default client
    mode = "all"  # Default mode: process all files
    
    # Parse arguments
    if len(sys.argv) > 1:
        # First argument is the client key
        client_key = sys.argv[1]
        
        # Second argument (optional) is the mode: 'all' to process all files or 'test' to run the test case
        if len(sys.argv) > 2:
            mode = sys.argv[2]
    
    if client_key not in CLIENTS:
        print(f"❌ Unknown client key: {client_key}")
        print(f"Valid keys are: {', '.join(CLIENTS.keys())}")
        print("Usage: python create_client_case.py <client_key> [all|test]")
        sys.exit(1)
    
    print(f"Working with client: {CLIENTS[client_key]['name']}")
    
    if recreate_clients:
        for case_name in CLIENTS:
            create_client_case(case_name)
    
    # List cases to get the case ID
    print("\n===== Listing Cases =====")
    cases = list_all_cases()
    
    # Find case for the specified client or create a new one
    target_case = None
    if cases:
        for case in cases:
            if case["name"] == CLIENTS[client_key]["name"]:
                target_case = case
                break
    
    if not target_case:
        print(f"No case found for {CLIENTS[client_key]['name']}. Creating a new case...")
        target_case = create_client_case(client_key)
        if not target_case:
            print("Failed to create a case. Exiting.")
            sys.exit(1)
    
    # Get the case ID
    case_id = target_case["id"]
    print(f"\n===== Working with Case ID: {case_id} for {target_case['name']} =====")
    
    # Choose operation mode
    if mode.lower() == "all":
        # Process all files for the client
        print("\n===== Processing All Client Files =====")
        successful_files = process_client_files(case_id, client_key)
        print(f"\n===== Summary =====")
        print(f"Total files successfully processed: {successful_files}")
        print("Done!")
    else:
        # Original test mode - process a single document and check status
        # List available documents 
        print("\n===== Available Documents =====")
        documents = list_documents()
        
        if not documents or len(documents) == 0:
            print("No documents available in the system. Note: This does not affect upload functionality.")
        
        # Use a real document from the local assets for testing
        client_path = CLIENTS[client_key]["folder_path"]
        
        # Try to find a PDF file for testing
        print("Finding a test document...")
        test_files = find_client_files(client_path)
        
        if not test_files:
            print(f"Error: No document files found in {client_path}")
            sys.exit(1)
        
        # Pick the first PDF file if available, otherwise use the first file
        real_document_path = None
        for file_path in test_files:
            if file_path.lower().endswith('.pdf'):
                real_document_path = file_path
                break
        
        if not real_document_path and test_files:
            real_document_path = test_files[0]
        
        # Verify the file exists
        if not os.path.exists(real_document_path):
            print(f"Error: Document file not found at {real_document_path}")
            sys.exit(1)
            
        print(f"\n===== Uploading Test Document: {os.path.basename(real_document_path)} =====")
        # Upload the file
        result = upload_document_file_for_case(case_id, real_document_path)
        if result:
            # Wait and check document processing status
            document_id = result.get("document_id")
            
            if document_id:
                print("\n===== Checking Document Processing Status =====")
                print("Waiting for document processing to complete...")
                
                # Wait for a few seconds for processing to start
                import time
                for i in range(5):
                    time.sleep(5)
                    
                    # Check document status
                    doc_status_url = f"{BASE_URL}/cases/{case_id}/documents/{document_id}"
                    try:
                        status_response = requests.get(doc_status_url)
                        if status_response.status_code == 200:
                            doc_status = status_response.json()
                            print(f"Document processing status: {doc_status.get('processing_status')}")
                            print("Document details:")
                            print(json.dumps(doc_status, indent=2))
                        else:
                            print(f"Failed to get document status. Status: {status_response.status_code}")
                    except Exception as e:
                        print(f"Error checking document status: {e}")
        
            print("Document uploaded successfully!")
            print(f"Document details: {json.dumps(result, indent=2)}")
        else:
            print("Failed to upload document.")
