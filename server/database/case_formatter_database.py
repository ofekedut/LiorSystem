"""
Utility for formatting case data to match the sample JSON structure
"""
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from server.database.database import get_connection
from server.database.cases_database import get_case, CaseInDB
from server.database.documents_database import DocumentInDB


async def get_formatted_case(case_id: uuid.UUID) -> Dict[str, Any]:
    """
    Get a case with all related data formatted to match the sample JSON structure
    """
    # Get the base case data
    case_data = await get_case(case_id)
    if not case_data:
        return {}

    # Build the case structure
    result = {
        "case": {
            "id": str(case_data.id),
            "application_status": case_data.status,
            "created_date": case_data.created_at.strftime("%Y-%m-%d"),
            "last_updated": case_data.updated_at.strftime("%Y-%m-%d"),
        }
    }

    # Get desired product (loan type and goal)
    loan_type = await get_loan_type(case_data.loan_type_id) if case_data.loan_type_id else None

    # Add desired product if loan type exists
    if loan_type:
        result["case"]["desired_product"] = {
            "loan_type": loan_type["value"],
        }

    # Get persons in case with all related data
    result["case"]["persons_in_case"] = await get_case_persons_with_details(case_id)

    # Get companies in case with all related data
    result["case"]["companies_in_case"] = await get_case_companies_with_details(case_id)

    return result


async def get_case_persons_with_details(case_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Get all persons in a case with their related details
    """
    conn = await get_connection()
    try:
        # Get all persons in the case
        persons_query = """
        SELECT 
            p.id, p.first_name, p.last_name, p.id_number, p.gender, 
            p.birth_date, p.phone, p.email, p.status,
            role.value as role_value,
            ms.value as marital_status_value
        FROM 
            case_persons p
        LEFT JOIN 
            lior_dropdown_options role ON p.role_id = role.id AND role.category = 'person_roles'
        LEFT JOIN 
            lior_dropdown_options ms ON p.marital_status_id = ms.id AND ms.category = 'person_marital_statuses'
        WHERE 
            p.case_id = $1
        """

        persons = await conn.fetch(persons_query, case_id)

        result = []
        for person in persons:
            person_data = dict(person)
            person_id = person_data["id"]

            # Create person JSON
            person_json = {
                "id": str(person_id),
                "role": person_data["role_value"],
                "personal_info": {
                    "first_name": person_data["first_name"],
                    "last_name": person_data["last_name"],
                    "id_number": person_data["id_number"],
                    "date_of_birth": person_data["birth_date"].strftime("%Y-%m-%d") if person_data[
                        "birth_date"] else None,
                    "gender": person_data["gender"],
                    "marital_status": person_data["marital_status_value"],
                    "phone": person_data["phone"],
                    "email": person_data["email"]
                }
            }

            # Add documents
            person_json["documents"] = await get_person_documents(person_id)

            # Add employment history
            person_json["employment_history"] = await get_person_employment_history(person_id)

            # Add income sources
            person_json["income_sources"] = await get_person_income_sources(person_id)

            # Add bank accounts
            person_json["bank_accounts"] = await get_person_bank_accounts(person_id)

            # Add credit cards
            person_json["credit_cards"] = await get_person_credit_cards(person_id)

            # Add loans
            person_json["loans"] = await get_person_loans(person_id)

            # Add assets
            person_json["assets"] = await get_person_assets(person_id)

            # Add related persons
            person_json["related_persons"] = await get_person_relationships(person_id)

            result.append(person_json)

        return result
    finally:
        await conn.close()


async def get_person_bank_accounts(person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get bank accounts for a person"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            pba.id, pba.bank_name, pba.account_number,
            acc_type.value as account_type_value
        FROM 
            person_bank_accounts pba
        LEFT JOIN 
            lior_dropdown_options acc_type ON pba.account_type_id = acc_type.id AND acc_type.category = 'bank_account_types'
        WHERE 
            pba.person_id = $1
        """

        accounts = await conn.fetch(query, person_id)

        result = []
        for account in accounts:
            account_data = dict(account)
            account_id = account_data["id"]

            # Get documents for this bank account
            account_documents = await get_entity_documents('bank_account', account_id)

            account_json = {
                "id": str(account_id),
                "account_type": account_data["account_type_value"],
                "bank_name": account_data["bank_name"],
                "account_number": f"****{account_data['account_number'][-4:]}",
                "documents": account_documents
            }

            result.append(account_json)

        return result
    finally:
        await conn.close()


async def get_person_credit_cards(person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get credit cards for a person"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            pcc.id, pcc.issuer, pcc.last_four,
            card_type.value as card_type_value
        FROM 
            person_credit_cards pcc
        LEFT JOIN 
            lior_dropdown_options card_type ON pcc.card_type_id = card_type.id AND card_type.category = 'credit_card_types'
        WHERE 
            pcc.person_id = $1
        """

        cards = await conn.fetch(query, person_id)

        result = []
        for card in cards:
            card_data = dict(card)
            card_id = card_data["id"]

            # Get documents for this credit card
            card_documents = await get_entity_documents('credit_card', card_id)

            card_json = {
                "id": str(card_id),
                "issuer": card_data["issuer"],
                "card_type": card_data["card_type_value"],
                "last_four": card_data["last_four"],
                "documents": card_documents
            }

            result.append(card_json)

        return result
    finally:
        await conn.close()


async def get_person_loans(person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get loans for a person"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            pl.id, pl.lender,
            loan_type.value as loan_type_value
        FROM 
            person_loans pl
        LEFT JOIN 
            lior_dropdown_options loan_type ON pl.loan_type_id = loan_type.id AND loan_type.category = 'loan_types'
        WHERE 
            pl.person_id = $1
        """

        loans = await conn.fetch(query, person_id)

        result = []
        for loan in loans:
            loan_data = dict(loan)
            loan_id = loan_data["id"]

            # Get documents for this loan
            loan_documents = await get_entity_documents('loan', loan_id)

            loan_json = {
                "id": str(loan_id),
                "type": loan_data["loan_type_value"],
                "lender": loan_data["lender"],
                "documents": loan_documents
            }

            result.append(loan_json)

        return result
    finally:
        await conn.close()


async def get_person_assets(person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get assets for a person"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            pa.id, pa.description,
            asset_type.value as asset_type_value
        FROM 
            person_assets pa
        LEFT JOIN 
            lior_dropdown_options asset_type ON pa.asset_type_id = asset_type.id AND asset_type.category = 'asset_types'
        WHERE 
            pa.person_id = $1
        """

        assets = await conn.fetch(query, person_id)

        result = []
        for asset in assets:
            asset_data = dict(asset)
            asset_id = asset_data["id"]

            # Get documents for this asset
            asset_documents = await get_entity_documents('asset', asset_id)

            asset_json = {
                "id": str(asset_id),
                "type": asset_data["asset_type_value"],
                "description": asset_data["description"],
                "documents": asset_documents
            }

            result.append(asset_json)

        return result
    finally:
        await conn.close()


async def get_person_relationships(person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get relationships for a person"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            cpr.from_person_id, cpr.to_person_id,
            rel_type.value as relationship_type_value,
            cp.first_name, cp.last_name
        FROM 
            case_person_relations cpr
        LEFT JOIN 
            lior_dropdown_options rel_type ON cpr.relationship_type_id = rel_type.id AND rel_type.category = 'related_person_relationships_types'
        JOIN
            case_persons cp ON (
                CASE 
                    WHEN cpr.from_person_id = $1 THEN cpr.to_person_id = cp.id
                    ELSE cpr.from_person_id = cp.id
                END
            )
        WHERE 
            cpr.from_person_id = $1 OR cpr.to_person_id = $1
        """

        relationships = await conn.fetch(query, person_id)

        result = []
        for rel in relationships:
            rel_data = dict(rel)

            # Determine which person is the related one
            related_person_id = rel_data["to_person_id"] if rel_data["from_person_id"] == person_id else rel_data[
                "from_person_id"]

            # Get documents for this relationship
            rel_documents = await get_relationship_documents(rel_data["from_person_id"], rel_data["to_person_id"])

            rel_json = {
                "person_id": str(related_person_id),
                "relationship": rel_data["relationship_type_value"],
                "documents": rel_documents
            }

            result.append(rel_json)

        return result
    finally:
        await conn.close()


async def get_entity_documents(entity_type: str, entity_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get documents associated with a specific entity"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            d.id, d.name, doc_type.value as doc_type
        FROM 
            document_entity_relations der
        JOIN 
            documents d ON der.document_id = d.id
        LEFT JOIN 
            lior_dropdown_options doc_type ON d.document_type_id = doc_type.id AND doc_type.category = 'document_types'
        WHERE 
            der.entity_type = $1 AND der.entity_id = $2
        """

        documents = await conn.fetch(query, entity_type, entity_id)

        return [
            {
                "name": doc["name"],
                "of_type": doc["doc_type"],
                "url": f"/documents/{doc['id']}.pdf"
            }
            for doc in documents
        ]
    finally:
        await conn.close()


async def get_relationship_documents(from_person_id: uuid.UUID, to_person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get documents associated with a relationship between two persons"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            d.id, d.name, doc_type.value as doc_type
        FROM 
            document_entity_relations der
        JOIN 
            documents d ON der.document_id = d.id
        LEFT JOIN 
            lior_dropdown_options doc_type ON d.document_type_id = doc_type.id AND doc_type.category = 'document_types'
        WHERE 
            der.entity_type = 'relationship' AND 
            der.entity_id = $1
        """

        # Create a composite ID for the relationship (could be implemented differently based on your schema)
        relationship_id = str(from_person_id) + "_" + str(to_person_id)

        documents = await conn.fetch(query, relationship_id)

        return [
            {
                "name": doc["name"],
                "of_type": doc["doc_type"],
                "url": f"/documents/{doc['id']}.pdf"
            }
            for doc in documents
        ]
    finally:
        await conn.close()


async def get_loan_type(loan_type_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Get a loan type by ID"""
    conn = await get_connection()
    try:
        query = """
        SELECT id, name, value
        FROM lior_dropdown_options
        WHERE id = $1 AND category = 'loan_types'
        """

        row = await conn.fetchrow(query, loan_type_id)

        if row:
            return dict(row)
        return None
    finally:
        await conn.close()


async def get_case_companies_with_details(case_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Get all companies in a case with their related details
    """
    conn = await get_connection()
    try:
        # Get all companies in the case
        companies_query = """
        SELECT 
            c.id, c.name,
            comp_type.value as company_type_value,
            role.value as role_value
        FROM 
            case_companies c
        LEFT JOIN 
            lior_dropdown_options comp_type ON c.company_type_id = comp_type.id AND comp_type.category = 'company_types'
        LEFT JOIN 
            lior_dropdown_options role ON c.role_id = role.id AND role.category = 'person_roles'
        WHERE 
            c.case_id = $1
        """

        companies = await conn.fetch(companies_query, case_id)

        result = []
        for company in companies:
            company_data = dict(company)
            company_id = company_data["id"]

            # Create company JSON
            company_json = {
                "id": str(company_id),
                "name": company_data["name"],
                "type": company_data["company_type_value"],
                "role": company_data["role_value"],
                "documents": await get_company_documents(company_id)
            }

            result.append(company_json)

        return result
    finally:
        await conn.close()


# Helper functions for getting related data
async def get_person_documents(person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get all documents for a person"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            d.id, d.name, doc_type.value as doc_type
        FROM 
            case_person_documents cpd
        JOIN 
            documents d ON cpd.document_id = d.id
        LEFT JOIN 
            lior_dropdown_options doc_type ON d.document_type_id = doc_type.id AND doc_type.category = 'document_types'
        WHERE 
            cpd.person_id = $1
        """

        documents = await conn.fetch(query, person_id)

        return [
            {
                "name": doc["name"],
                "of_type": doc["doc_type"],
                "url": f"/documents/{doc['id']}.pdf"
            }
            for doc in documents
        ]
    finally:
        await conn.close()


async def get_company_documents(company_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get all documents for a company"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            d.id, d.name, doc_type.value as doc_type
        FROM 
            document_entity_relations der
        JOIN 
            documents d ON der.document_id = d.id
        LEFT JOIN 
            lior_dropdown_options doc_type ON d.document_type_id = doc_type.id AND doc_type.category = 'document_types'
        WHERE 
            der.entity_type = 'company' AND der.entity_id = $1
        """

        documents = await conn.fetch(query, company_id)

        return [
            {
                "name": doc["name"],
                "of_type": doc["doc_type"],
                "url": f"/documents/{doc['id']}.pdf"
            }
            for doc in documents
        ]
    finally:
        await conn.close()


async def get_person_employment_history(person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get employment history for a person"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            peh.id, peh.employer_name, peh.position, peh.current_employer,
            emp_type.value as employment_type_value
        FROM 
            person_employment_history peh
        LEFT JOIN 
            lior_dropdown_options emp_type ON peh.employment_type_id = emp_type.id AND emp_type.category = 'employment_types'
        WHERE 
            peh.person_id = $1
        """

        employments = await conn.fetch(query, person_id)

        return [
            {
                "employer_name": emp["employer_name"],
                "position": emp["position"],
                "employment_type": emp["employment_type_value"],
                "current_employer": emp["current_employer"]
            }
            for emp in employments
        ]
    finally:
        await conn.close()


async def get_person_income_sources(person_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Get income sources for a person"""
    conn = await get_connection()
    try:
        query = """
        SELECT 
            pis.id, pis.label,
            income_type.value as income_source_type_value
        FROM 
            person_income_sources pis
        LEFT JOIN 
            lior_dropdown_options income_type ON pis.income_source_type_id = income_type.id AND income_type.category = 'income_sources_types'
        WHERE 
            pis.person_id = $1
        """

        incomes = await conn.fetch(query, person_id)

        result = []
        for income in incomes:
            income_data = dict(income)
            income_id = income_data["id"]

            # Get documents for this income source
            income_documents = await get_entity_documents('income_source', income_id)

            income_json = {
                "label": income_data["label"],
                "type": income_data["income_source_type_value"],
                "documents": income_documents
            }

            result.append(income_json)

        return result
    finally:
        await conn.close()