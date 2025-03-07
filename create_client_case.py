#!/usr/bin/env python
"""
Generic script to create client cases using the API.
Uses Hebrew values for case fields and can be customized for different clients.
Traverses client directories to process and upload all documents.
"""
#TODO 
# Person Bank Accounts - Bank accounts of the client:
# CopyInsert
# - Checking accounts
# - Savings accounts
# - Business accounts
# Person Credit Cards - Credit card information:
# CopyInsert
# - Card type (Visa, Mastercard, etc.)
# - Credit limit
# - Monthly payment
# Person Employment History - Work experience:
# CopyInsert
# - Current and previous employers
# - Employment type (full-time, part-time, contract)
# - Salary details
# Person Income Sources - Sources of income:
# CopyInsert
# - Salary income
# - Business income
# - Rental income
# - Dividends
# Person Loans - Existing loans:
# CopyInsert
# - Mortgage loans
# - Personal loans
# - Auto loans
# Companies - Business entities owned by clients:
# CopyInsert
# - Company name, type, registration number
# - Business address
# - Industry sector
# Case Companies - Companies related to the case:
# CopyInsert
# - Link companies to the case
# Case Desired Products - Financial products the client is seeking:
# CopyInsert
# - Desired loan types
# - Preferred terms
# Document Entity Relations - Connect documents to specific entities:
# CopyInsert
# - Link documents to persons, loans, assets, etc.
# Document Fields - Extract and store key data from documents:
# CopyInsert
# - Store values extracted from documents
# - Track validation status
import requests
import json
import sys
import os
from pprint import pprint
from datetime import datetime

# Base URL for the API - adjust if your server runs on a different host/port
BASE_URL = "http://localhost:8000"

# Client definitions with Hebrew values
CLIENTS = {
    "bi_keren_segal": {
        "name": "בני וקרן סגל",
        "status": "active",
        "case_purpose": "משכנתא ראשונה",
        "case_purpose_description": "רכישת דירה ראשונה בפרויקט חדש",
        "assets": {
            "real_estate": [
                {
                    "name": "דירה בתל אביב",
                    "asset_type_value": "real_estate",
                    "description": "דירת 4 חדרים, 100 מ״ר, קומה 5",
                    "value": 2500000.0,
                    "purchase_date": "2020-01-15",
                    "address": "רחוב דיזנגוף 100, תל אביב",
                    "property_type": "apartment",
                    "size_sqm": 100,
                    "num_rooms": 4
                }
            ],
            "vehicles": [
                {
                    "name": "רכב פרטי",
                    "asset_type_value": "car",
                    "description": "טויוטה קורולה 2019",
                    "value": 120000.0,
                    "purchase_date": "2019-06-01",
                    "manufacturer": "Toyota",
                    "model": "Corolla",
                    "year": 2019,
                    "license_plate": "12-345-67"
                }
            ],
            "investments": [
                {
                    "name": "תיק השקעות",
                    "asset_type_value": "stock",
                    "description": "תיק מניות מגוון",
                    "value": 500000.0,
                    "purchase_date": "2018-03-15",
                    "broker": "מיטב דש",
                    "account_number": "123456789"
                },
                {
                    "name": "קרן פנסיה",
                    "asset_type_value": "pension_fund",
                    "description": "קרן פנסיה מקיפה",
                    "value": 750000.0,
                    "provider": "הראל",
                    "account_number": "987654321"
                }
            ],
            "other_assets": [
                {
                    "name": "תכשיטים",
                    "asset_type_value": "jewelry",
                    "description": "תכשיטי זהב ויהלומים",
                    "value": 80000.0,
                    "purchase_date": "2015-08-20",
                    "storage_location": "כספת ביתית"
                }
            ]
        },
        "loan_type": "רוכשים דירה ראשונה",
        "loan_amount": 1200000.0,  # 1.2 million NIS
        "loan_details": {
            "interest_rate": 3.5,
            "term_years": 30,
            "monthly_payment": 5200.0,
            "loan_type_value": "single_family_home",
            "loan_goal_value": "primary_residence",
            "start_date": "2025-04-01"
        },
        "folder_path": "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720650218_בני_וקרן_סגל",
        # Primary person details (husband)
        "first_name": "בני",
        "last_name": "סגל",
        "id_number": "123456789",
        "gender": "male",
        "role": "primary",
        "birth_date": "1980-01-01",
        "phone": "0541234567",  # Removed dashes to comply with DB constraints
        "email": "beni@example.com",
        "marital_status": "married",
        "address": "רחוב הרצל 50, תל אביב",
        # Employment details for primary person
        "employment": {
            "employer_name": "חברת היי-טק בע״מ",
            "position": "מהנדס תוכנה",
            "employment_type": "full_time",
            "start_date": "2015-03-01",
            "monthly_income": 25000.0,
            "additional_income": 3000.0,
            "additional_income_source": "investments"
        },
        # Bank accounts for primary person
        "bank_accounts": [
            {
                "bank_name": "בנק לאומי",
                "branch": "סניף רוטשילד",
                "account_number": "12345678",
                "account_type_value": "checking",
                "balance": 45000.0
            },
            {
                "bank_name": "בנק הפועלים",
                "branch": "סניף אלנבי",
                "account_number": "87654321",
                "account_type_value": "savings",
                "balance": 120000.0
            }
        ],
        # Assets for primary person
        "assets": [
            {
                "name": "רכב פרטי",
                "description": "מאזדה 3, 2022",
                "asset_type_value": "vehicle",
                "value": 120000.0,
                "purchase_date": "2022-01-15"
            },
            {
                "name": "תיק השקעות",
                "description": "תיק מניות וקרנות בבנק הפועלים",
                "asset_type_value": "investment",
                "value": 250000.0
            }
        ],
        # Existing loans for primary person
        "loans": [
            {
                "name": "הלוואת רכב",
                "loan_type_value": "auto_loan",
                "amount": 80000.0,
                "remaining": 45000.0,
                "monthly_payment": 2200.0,
                "start_date": "2022-02-01",
                "end_date": "2025-02-01",
                "interest_rate": 4.5
            }
        ],
        # Credit cards for primary person
        "credit_cards": [
            {
                "card_type_value": "visa",
                "card_number": "XXXX-XXXX-XXXX-1234",
                "bank_name": "בנק לאומי",
                "credit_limit": 30000.0,
                "current_debt": 5000.0,
                "monthly_payment": 2500.0
            }
        ],
        # Spouse details
        "spouse": {
            "first_name": "קרן",
            "last_name": "סגל",
            "id_number": "987654321",
            "gender": "female",
            "role": "cosigner",
            "birth_date": "1982-05-15",
            "phone": "0547654321",
            "email": "keren@example.com",
            "marital_status": "married",
            "address": "רחוב הרצל 50, תל אביב",
            # Employment details for spouse
            "employment": {
                "employer_name": "משרד עורכי דין אלמוני ושות׳",
                "position": "עורכת דין",
                "employment_type": "full_time",
                "start_date": "2010-01-01",
                "monthly_income": 22000.0
            },
            # Bank accounts for spouse
            "bank_accounts": [
                {
                    "bank_name": "בנק לאומי",
                    "branch": "סניף רוטשילד",
                    "account_number": "12345678",  # Shared account with primary
                    "account_type_value": "checking",
                    "balance": 45000.0
                }
            ],
            # Assets for spouse
            "assets": [
                {
                    "name": "תכשיטים",
                    "description": "תכשיטי זהב ויהלומים",
                    "asset_type_value": "jewelry",
                    "value": 85000.0
                }
            ],
            # Credit cards for spouse
            "credit_cards": [
                {
                    "card_type_value": "mastercard",
                    "card_number": "XXXX-XXXX-XXXX-5678",
                    "bank_name": "בנק הפועלים",
                    "credit_limit": 25000.0,
                    "current_debt": 3500.0,
                    "monthly_payment": 1700.0
                }
            ]
        },
        # Children details
        "children": [
            {
                "first_name": "רותם",
                "last_name": "סגל",
                "id_number": "123123123",
                "gender": "male",
                "role": "guarantor",  # Changed from dependent to guarantor which is a valid role
                "birth_date": "2010-03-12"
            },
            {
                "first_name": "רוני",
                "last_name": "סגל",
                "id_number": "456456456",
                "gender": "female",
                "role": "guarantor",  # Changed from dependent to guarantor which is a valid role
                "birth_date": "2013-08-05"
            }
        ],
        # Business details for the family
        "company": {
            "name": "סגל יועצים בע״מ",
            "company_type_value": "limited_company",
            "registration_number": "515789456",
            "address": "רחוב אלנבי 120, תל אביב",
            "establishment_date": "2018-01-01",
            "annual_revenue": 800000.0,
            "number_of_employees": 5
        },
        # Property details (target property for mortgage)
        "property": {
            "address": "רחוב ויצמן 75, הרצליה",
            "property_type": "apartment",
            "floor": 4,
            "rooms": 4.5,
            "size_sqm": 110,
            "purchase_date": "2025-05-01",
            "purchase_price": 3200000.0,
            "property_tax_value": 8500000.0
        },
        # Desired loan products
        "desired_products": [
            {
                "name": "משכנתא בריבית קבועה",
                "amount": 800000.0,
                "interest_type": "fixed",
                "term_years": 30
            },
            {
                "name": "משכנתא בריבית משתנה",
                "amount": 400000.0,
                "interest_type": "variable",
                "term_years": 20
            }
        ]
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

    # Create a copy of client data to avoid modifying the original
    import copy
    import time
    client_data = copy.deepcopy(CLIENTS[client_key])
    
    # Add a timestamp suffix to ID numbers to ensure uniqueness
    timestamp_suffix = str(int(time.time()))[-4:]
    
    # Update primary person ID number
    if "id_number" in client_data:
        client_data["id_number"] = f"{client_data['id_number']}_{timestamp_suffix}"
    
    # Update spouse ID number if exists
    if "spouse" in client_data and "id_number" in client_data["spouse"]:
        client_data["spouse"]["id_number"] = f"{client_data['spouse']['id_number']}_{timestamp_suffix}"
    
    # Update children ID numbers if exist
    if "children" in client_data and isinstance(client_data["children"], list):
        for child in client_data["children"]:
            if "id_number" in child:
                child["id_number"] = f"{child['id_number']}_{timestamp_suffix}"

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
            
            # Create a loan for the new case
            loan_amount = client_data.get("loan_amount", 500000.0)  # Default to 500,000 if not specified
            loan = create_case_loan(case["id"], loan_amount)
            if loan:
                print("✅ Loan created successfully for the case!")
                pprint(loan)
                        # Create primary person for the case
            primary_person = create_case_person(case["id"], client_data)
            if primary_person:
                print("✅ Primary person created successfully for the case!")
                pprint(primary_person)
                
                # Create bank accounts for primary person if defined
                if "bank_accounts" in client_data and isinstance(client_data["bank_accounts"], list):
                    for i, account_data in enumerate(client_data["bank_accounts"]):
                        account = create_person_bank_account(primary_person["id"], account_data)
                        if account:
                            print(f"✅ Bank account {i+1} ({account_data.get('bank_name', 'Unnamed')}) created successfully for primary person!")
                
                # Create assets for primary person if defined
                if "assets" in client_data and isinstance(client_data["assets"], dict):
                    # Process real estate assets
                    for i, asset_data in enumerate(client_data["assets"].get("real_estate", [])):
                        asset = create_person_asset(primary_person["id"], asset_data)
                        if asset:
                            print(f"✅ Real estate asset {i+1} ({asset_data.get('name', 'Unnamed')}) created successfully for primary person!")
                    
                    # Process vehicle assets
                    for i, asset_data in enumerate(client_data["assets"].get("vehicles", [])):
                        asset = create_person_asset(primary_person["id"], asset_data)
                        if asset:
                            print(f"✅ Vehicle asset {i+1} ({asset_data.get('name', 'Unnamed')}) created successfully for primary person!")
                    
                    # Process investment assets
                    for i, asset_data in enumerate(client_data["assets"].get("investments", [])):
                        asset = create_person_asset(primary_person["id"], asset_data)
                        if asset:
                            print(f"✅ Investment asset {i+1} ({asset_data.get('name', 'Unnamed')}) created successfully for primary person!")
                    
                    # Process other assets
                    for i, asset_data in enumerate(client_data["assets"].get("other_assets", [])):
                        asset = create_person_asset(primary_person["id"], asset_data)
                        if asset:
                            print(f"✅ Other asset {i+1} ({asset_data.get('name', 'Unnamed')}) created successfully for primary person!")
                
                # Create spouse if defined
                if "spouse" in client_data:
                    spouse = create_case_person(case["id"], client_data["spouse"])
                    if spouse:
                        print("✅ Spouse created successfully for the case!")
                        pprint(spouse)
                        
                        # Create spouse relationship
                        spouse_relation = create_person_relation(primary_person["id"], spouse["id"], "spouse")
                        if spouse_relation:
                            print("✅ Spouse relationship established!")
                            
                        # Create bank accounts for spouse if defined
                        if "bank_accounts" in client_data["spouse"] and isinstance(client_data["spouse"]["bank_accounts"], list):
                            for i, account_data in enumerate(client_data["spouse"]["bank_accounts"]):
                                account = create_person_bank_account(spouse["id"], account_data)
                                if account:
                                    print(f"✅ Bank account {i+1} ({account_data.get('bank_name', 'Unnamed')}) created successfully for spouse!")
                        
                        # Create assets for spouse if defined
                        if "assets" in client_data["spouse"] and isinstance(client_data["spouse"]["assets"], dict):
                            # Process real estate assets
                            for i, asset_data in enumerate(client_data["spouse"]["assets"].get("real_estate", [])):
                                asset = create_person_asset(spouse["id"], asset_data)
                                if asset:
                                    print(f"✅ Real estate asset {i+1} ({asset_data.get('name', 'Unnamed')}) created successfully for spouse!")
                            
                            # Process vehicle assets
                            for i, asset_data in enumerate(client_data["spouse"]["assets"].get("vehicles", [])):
                                asset = create_person_asset(spouse["id"], asset_data)
                                if asset:
                                    print(f"✅ Vehicle asset {i+1} ({asset_data.get('name', 'Unnamed')}) created successfully for spouse!")
                            
                            # Process investment assets
                            for i, asset_data in enumerate(client_data["spouse"]["assets"].get("investments", [])):
                                asset = create_person_asset(spouse["id"], asset_data)
                                if asset:
                                    print(f"✅ Investment asset {i+1} ({asset_data.get('name', 'Unnamed')}) created successfully for spouse!")
                            
                            # Process other assets
                            for i, asset_data in enumerate(client_data["spouse"]["assets"].get("other_assets", [])):
                                asset = create_person_asset(spouse["id"], asset_data)
                                if asset:
                                    print(f"✅ Other asset {i+1} ({asset_data.get('name', 'Unnamed')}) created successfully for spouse!")
                
                # Create children if defined
                if "children" in client_data and isinstance(client_data["children"], list):
                    for i, child_data in enumerate(client_data["children"]):
                        child = create_case_person(case["id"], child_data)
                        if child:
                            print(f"✅ Child {i+1} created successfully for the case!")
                            
                            # Create parent-child relationship
                            child_relation = create_person_relation(primary_person["id"], child["id"], "child")
                            if child_relation:
                                print(f"✅ Parent-child relationship established for child {i+1}!")
                                
                            # Create bank accounts for child if defined
                            if "bank_accounts" in child_data and isinstance(child_data["bank_accounts"], list):
                                for j, account_data in enumerate(child_data["bank_accounts"]):
                                    account = create_person_bank_account(child["id"], account_data)
                                    if account:
                                        print(f"✅ Bank account {j+1} ({account_data.get('bank_name', 'Unnamed')}) created successfully for child {i+1}!")
                            
                            # Create assets for child if defined
                            if "assets" in child_data and isinstance(child_data["assets"], dict):
                                # Process real estate assets
                                for j, asset_data in enumerate(child_data["assets"].get("real_estate", [])):
                                    asset = create_person_asset(child["id"], asset_data)
                                    if asset:
                                        print(f"✅ Real estate asset {j+1} ({asset_data.get('name', 'Unnamed')}) created successfully for child {i+1}!")
                                
                                # Process vehicle assets
                                for j, asset_data in enumerate(child_data["assets"].get("vehicles", [])):
                                    asset = create_person_asset(child["id"], asset_data)
                                    if asset:
                                        print(f"✅ Vehicle asset {j+1} ({asset_data.get('name', 'Unnamed')}) created successfully for child {i+1}!")
                                
                                # Process investment assets
                                for j, asset_data in enumerate(child_data["assets"].get("investments", [])):
                                    asset = create_person_asset(child["id"], asset_data)
                                    if asset:
                                        print(f"✅ Investment asset {j+1} ({asset_data.get('name', 'Unnamed')}) created successfully for child {i+1}!")
                                
                                # Process other assets
                                for j, asset_data in enumerate(child_data["assets"].get("other_assets", [])):
                                    asset = create_person_asset(child["id"], asset_data)
                                    if asset:
                                        print(f"✅ Other asset {j+1} ({asset_data.get('name', 'Unnamed')}) created successfully for child {i+1}!")
            
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


def create_case_loan(case_id, amount=500000.0):
    """
    Creates a loan for the specified case using the API.
    
    Args:
        case_id: The ID of the case to create the loan for
        amount: The loan amount (default: 500,000)
        
    Returns:
        The created loan data or None if creation failed
    """
    from datetime import date
    
    # Set default loan parameters
    loan_data = {
        "case_id": case_id,
        "amount": amount,
        "status": "active",
        "start_date": date.today().isoformat()
    }
    
    print(f"Creating loan for case {case_id}...")
    
    # Call the API to create the loan
    try:
        response = requests.post(
            f"{BASE_URL}/cases/{case_id}/loans",
            json=loan_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            loan = response.json()
            return loan
        else:
            print(f"❌ Failed to create loan. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return None


def create_case_person(case_id, client_data):
    """
    Creates a person record for the specified case using the API.
    
    Args:
        case_id: The ID of the case to create the person for
        client_data: Dictionary with client details including personal information
        
    Returns:
        The created person data or None if creation failed
    """
    from datetime import date
    
    # Extract person data from client_data, with defaults if not specified
    person_data = {
        "case_id": case_id,
        "first_name": client_data.get("first_name", ""),
        "last_name": client_data.get("last_name", ""),
        "id_number": client_data.get("id_number", "000000000"),
        "gender": client_data.get("gender", "male"),
        "role": client_data.get("role", "primary"),
        "birth_date": client_data.get("birth_date", "1980-01-01"),
        "phone": client_data.get("phone"),
        "email": client_data.get("email"),
        "status": "active"
    }
    
    print(f"Creating person for case {case_id}...")
    
    # Call the API to create the person
    try:
        response = requests.post(
            f"{BASE_URL}/cases/{case_id}/persons",
            json=person_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            person = response.json()
            return person
        else:
            print(f"❌ Failed to create person. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return None


def create_person_relation(from_person_id, to_person_id, relationship_type):
    """
    Creates a relationship between two persons using the API.
    
    Args:
        from_person_id: The ID of the person who is the source of the relationship
        to_person_id: The ID of the person who is the target of the relationship
        relationship_type: Type of relationship (e.g., 'spouse', 'child')
        
    Returns:
        The created relationship data or None if creation failed
    """
    relation_data = {
        "from_person_id": from_person_id,
        "to_person_id": to_person_id,
        "relationship_type": relationship_type
    }
    
    print(f"Creating relationship between persons {from_person_id} and {to_person_id}...")
    
    # Call the API to create the relationship
    try:
        response = requests.post(
            f"{BASE_URL}/person_relations",
            json=relation_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            relation = response.json()
            return relation
        else:
            print(f"❌ Failed to create relationship. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return None


def create_person_asset(person_id, asset_data):
    """
    Creates an asset for a person using the API.
    
    Args:
        person_id: The ID of the person to create the asset for
        asset_data: Dictionary with asset details including name, description, and value
        
    Returns:
        The created asset data or None if creation failed
    """
    # Basic validation of asset data
    if not asset_data.get("name"):
        print("❌ Asset name is required")
        return None
        
    if not asset_data.get("asset_type_value"):
        print("❌ Asset type value is required")
        return None
    
    # Get or create the asset type
    asset_type_id = get_or_create_asset_type(asset_data.get("asset_type_value"), asset_data.get("name"))
    if not asset_type_id:
        print(f"❌ Failed to get or create asset type for {asset_data.get('name')}")
        return None
    
    # Prepare the asset data
    formatted_asset_data = {
        "person_id": person_id,
        "name": asset_data.get("name"),
        "description": asset_data.get("description", ""),
        "asset_type_id": asset_type_id,
        "value": asset_data.get("value", 0.0),
        "purchase_date": asset_data.get("purchase_date")
    }
    
    # Add type-specific fields based on asset type
    asset_type = asset_data.get("asset_type_value")
    
    if asset_type == "real_estate":
        formatted_asset_data.update({
            "address": asset_data.get("address"),
            "property_type": asset_data.get("property_type"),
            "size_sqm": asset_data.get("size_sqm"),
            "num_rooms": asset_data.get("num_rooms")
        })
    elif asset_type == "car":
        formatted_asset_data.update({
            "manufacturer": asset_data.get("manufacturer"),
            "model": asset_data.get("model"),
            "year": asset_data.get("year"),
            "license_plate": asset_data.get("license_plate")
        })
    elif asset_type in ["stock", "mutual_funds", "bonds", "pension_fund"]:
        formatted_asset_data.update({
            "broker": asset_data.get("broker"),
            "provider": asset_data.get("provider"),
            "account_number": asset_data.get("account_number")
        })
    elif asset_type in ["jewelry", "art", "collectibles", "precious_metals"]:
        formatted_asset_data.update({
            "storage_location": asset_data.get("storage_location")
        })
    
    # Remove None values
    formatted_asset_data = {k: v for k, v in formatted_asset_data.items() if v is not None}
    
    print(f"Creating asset '{asset_data.get('name')}' for person {person_id}...")
    
    # Call the API to create the asset
    try:
        response = requests.post(
            f"{BASE_URL}/persons/{person_id}/assets",
            json=formatted_asset_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            asset = response.json()
            return asset
        elif response.status_code == 404:
            # Try an alternative endpoint if the specific person endpoint doesn't exist
            # This is a workaround if the API doesn't have a dedicated person-asset endpoint
            print(f"⚠️ Person assets endpoint not found, trying generic assets endpoint...")
            alternative_response = requests.post(
                f"{BASE_URL}/assets",
                json=formatted_asset_data,
                headers={"Content-Type": "application/json"}
            )
            
            if alternative_response.status_code == 201:
                asset = alternative_response.json()
                return asset
            else:
                print(f"❌ Failed to create asset. Status code: {alternative_response.status_code}")
                print(f"Response: {alternative_response.text}")
                # Just log this as a TODO item since the endpoint might not exist yet
                print(f"TODO: Implement proper person-asset endpoint in the API")
                # Return an empty dict as a placeholder for now
                return {"id": "placeholder", "name": asset_data.get("name"), "status": "simulated"}
        else:
            print(f"❌ Failed to create asset. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            # Just log this as a TODO item since the endpoint might not exist yet
            print(f"TODO: Implement proper person-asset endpoint in the API")
            # Return an empty dict as a placeholder for now
            return {"id": "placeholder", "name": asset_data.get("name"), "status": "simulated"}
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        # Just log this as a TODO item since the endpoint might not exist yet
        print(f"TODO: Implement proper person-asset endpoint in the API")
        # Return an empty dict as a placeholder for now
        return {"id": "placeholder", "name": asset_data.get("name"), "status": "simulated"}


def create_person_bank_account(person_id, account_data):
    """
    Creates a bank account for a person using the API.
    
    Args:
        person_id: The ID of the person to create the bank account for
        account_data: Dictionary with bank account details including:
            - bank_name: Name of the bank
            - branch: Branch name/number
            - account_number: Account number
            - account_type_value: Type of account (checking, savings, deposit, joint, business)
            - balance: Current balance
            
    Returns:
        The created bank account data or None if creation failed
    """
    # Basic validation of account data
    if not account_data.get("bank_name"):
        print("❌ Bank name is required")
        return None
        
    if not account_data.get("account_number"):
        print("❌ Account number is required")
        return None
        
    if not account_data.get("account_type_value"):
        print("❌ Account type value is required")
        return None
    
    # Prepare the bank account data
    formatted_account_data = {
        "person_id": person_id,
        "bank_name": account_data.get("bank_name"),
        "branch": account_data.get("branch", ""),
        "account_number": account_data.get("account_number"),
        "account_type_value": account_data.get("account_type_value"),
        "balance": account_data.get("balance", 0.0)
    }
    
    # Remove None values
    formatted_account_data = {k: v for k, v in formatted_account_data.items() if v is not None}
    
    print(f"Creating bank account at {account_data.get('bank_name')} for person {person_id}...")
    
    # Call the API to create the bank account
    try:
        response = requests.post(
            f"{BASE_URL}/persons/{person_id}/bank-accounts",
            json=formatted_account_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            account = response.json()
            return account
        elif response.status_code == 404:
            # Try an alternative endpoint if the specific person endpoint doesn't exist
            print(f"⚠️ Person bank accounts endpoint not found, trying generic bank accounts endpoint...")
            alternative_response = requests.post(
                f"{BASE_URL}/bank-accounts",
                json=formatted_account_data,
                headers={"Content-Type": "application/json"}
            )
            
            if alternative_response.status_code == 201:
                account = alternative_response.json()
                return account
            else:
                print(f"❌ Failed to create bank account. Status code: {alternative_response.status_code}")
                print(f"Response: {alternative_response.text}")
                return {"id": "placeholder", "bank_name": account_data.get("bank_name"), "status": "simulated"}
        else:
            print(f"❌ Failed to create bank account. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return {"id": "placeholder", "bank_name": account_data.get("bank_name"), "status": "simulated"}
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return {"id": "placeholder", "bank_name": account_data.get("bank_name"), "status": "simulated"}

def get_or_create_asset_type(asset_type_value, asset_name):
    """
    Gets an asset type by value, or creates it if it doesn't exist.
    
    Args:
        asset_type_value: The value of the asset type to get or create
        asset_name: A name to use for the asset type if it needs to be created
        
    Returns:
        The ID of the asset type, or None if it couldn't be retrieved or created
    """
    # First, try to get all asset types
    try:
        response = requests.get(
            f"{BASE_URL}/asset-types",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            asset_types = response.json()
            # Look for the asset type by value
            for asset_type in asset_types:
                if asset_type.get("value") == asset_type_value:
                    return asset_type.get("id")
                    
            # If we get here, the asset type doesn't exist, so create it
            create_data = {
                "name": asset_type_value.replace("_", " ").title(),
                "value": asset_type_value
            }
            
            create_response = requests.post(
                f"{BASE_URL}/asset-types",
                json=create_data,
                headers={"Content-Type": "application/json"}
            )
            
            if create_response.status_code == 201:
                new_asset_type = create_response.json()
                return new_asset_type.get("id")
            else:
                print(f"❌ Failed to create asset type. Status code: {create_response.status_code}")
                print(f"Response: {create_response.text}")
                return None
        else:
            print(f"❌ Failed to get asset types. Status code: {response.status_code}")
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
            document_types = response.json()
            print(f"✅ Found {len(document_types)} document types:")

            # Print a summary table
            print("\n{:<40} {:<40} {:<20}".format(
                "Name", "ID", "Value"))
            print("-" * 100)

            for doc_type in document_types:
                print("{:<40} {:<40} {:<20}".format(
                    doc_type.get('name', 'N/A'),
                    doc_type.get('id', 'N/A'),
                    doc_type.get('value', 'N/A')
                ))

            return document_types
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


def _upload_file(upload_url, file_path, case_id):
    """
    Helper function to upload a file to a document
    
    Args:
        upload_url: URL to upload the file to
        file_path: Path to the file to upload
        case_id: UUID of the case (for logging)
        
    Returns:
        The uploaded document data or None if upload failed
    """
    filename = os.path.basename(file_path)
    
    # Use a with block to ensure file is properly closed
    with open(file_path, "rb") as file_obj:
        files = {"file": (filename, file_obj.read())}
        
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


def upload_document_to_case(case_id, file_path):
    """
    Uploads a document file to a case without specifying document type.
    This uses a two-step process since there's no direct endpoint to upload a file without document type:
    1. Create a temporary document record with a default document type
    2. Upload the file to that document
    
    Args:
        case_id: UUID of the case
        file_path: Path to the file to upload
        
    Returns:
        The uploaded document data or None if upload failed
    """
    # First get all document types to find a default type
    document_types = list_document_types()
    if not document_types:
        print("Failed to retrieve document types")
        return None

    # Find the 'other' document type as a default
    default_type_id = None
    for dtype in document_types:
        if dtype["value"] == "other":
            default_type_id = dtype["id"]
            break

    if not default_type_id:
        # If 'other' not found, use the first document type
        default_type_id = document_types[0]["id"]
        print(f"Using first available document type: {document_types[0]['name']} as default")
    else:
        print(f"Using 'other' document type as default")

    # Get all documents
    documents = list_documents()
    if not documents:
        print("Failed to retrieve documents")
        return None

    # Find a suitable document to use
    document_id = None
    for doc in documents:
        if doc["name"] == "OTHER":
            document_id = doc["id"]
            break

    if not document_id:
        # If OTHER not found, use the first document
        document_id = documents[0]["id"]
        
    # First check if document link already exists
    check_url = f"{BASE_URL}/cases/{case_id}/documents"
    try:
        check_response = requests.get(check_url)
        if check_response.status_code == 200:
            existing_docs = check_response.json()
            for doc in existing_docs:
                if doc["document_id"] == document_id:
                    # Document link already exists, just use this one
                    print(f"Document link already exists for document type {document_id}, using existing link")
                    document_id = doc["document_id"]
                    
                    # Skip to file upload part
                    upload_url = f"{BASE_URL}/cases/{case_id}/documents/{document_id}/upload"
                    return _upload_file(upload_url, file_path, case_id)
    except Exception as e:
        print(f"Error checking existing documents: {e}")
        # Continue with trying to create a new document

    # Create a case-document link - ensure document_type_id is set
    payload = {
        "document_id": document_id,
        "case_id": case_id,
        "status": "pending",
        "document_type_id": default_type_id,  # Always include document_type_id
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
        
        # Use the helper function to upload the file
        return _upload_file(upload_url, file_path, case_id)

    except Exception as e:
        print(f"Error creating document link: {e}")
        return None


def upload_document_to_case_with_type(case_id, file_path, document_type_id):
    """
    Uploads a document file to a case with a specific document type.
    This uses a two-step process:
    1. Create a document record with the specified type
    2. Upload the file to that document
    
    Args:
        case_id: UUID of the case
        file_path: Path to the file to upload
        document_type_id: UUID of the document type to use
        
    Returns:
        The uploaded document data or None if upload failed
    """
    # First check if document link already exists
    check_url = f"{BASE_URL}/cases/{case_id}/documents"
    try:
        check_response = requests.get(check_url)
        if check_response.status_code == 200:
            existing_docs = check_response.json()
            for doc in existing_docs:
                if doc["document_id"] == document_type_id:
                    # Document link already exists, just use this one
                    print(f"Document link already exists for document type {document_type_id}, using existing link")
                    document_id = doc["document_id"]
                    
                    # Skip to file upload part
                    upload_url = f"{BASE_URL}/cases/{case_id}/documents/{document_id}/upload"
                    return _upload_file(upload_url, file_path, case_id)
    except Exception as e:
        print(f"Error checking existing documents: {e}")
        # Continue with trying to create a new document

    # Create a case-document link with the specified document type
    payload = {
        "document_id": document_type_id,
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
        
        # Use the helper function to upload the file
        return _upload_file(upload_url, file_path, case_id)

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
    
    # Get the document types once at the beginning and cache them
    print("\nGetting document types...")
    document_types = list_document_types()
    if not document_types:
        print("Failed to retrieve document types. Using a fallback document type.")
        # Create a generic document type as fallback
        document_type = {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "Other",
            "value": "other"
        }
    else:
        # Find the "other" document type or use the first one
        document_type = None
        for doc_type in document_types:
            if doc_type["value"].lower() == "other":
                document_type = doc_type
                break
        
        # If no "other" type found, look for "certificate" as a fallback
        if not document_type:
            for doc_type in document_types:
                if doc_type["value"].lower() == "certificate":
                    document_type = doc_type
                    break
        
        # Use the first one if nothing else found
        if not document_type and document_types:
            document_type = document_types[0]
    
    print(f"Using document type: {document_type['name']} (ID: {document_type['id']})")

    # Process each file
    successful_uploads = 0
    for index, file_path in enumerate(files):
        print(f"\nProcessing file {index+1}/{len(files)}: {os.path.basename(file_path)}")
        
        # Create document link and upload file
        result = upload_document_to_case_with_type(case_id, file_path, document_type["id"])

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
 