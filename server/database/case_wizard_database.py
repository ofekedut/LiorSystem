"""
Database operations for the New Case Wizard functionality.
This module implements the guided workflow for new case creation as specified in the PRD.
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from server.database.database import get_connection
from server.database.cases_database import (
    CaseInCreate, 
    CaseInDB, 
    create_case,
    CasePersonCreate, 
    create_case_person, 
    CasePersonRelationCreate, 
    create_person_relation
)
from server.database.companies_database import CompanyInCreate, create_company
from server.database.bank_accounts_database import BankAccountInCreate, create_bank_account
from server.database.credit_cards_database import CreditCardInCreate, create_credit_card
from server.database.person_loans_database import PersonLoanInCreate, create_person_loan
from server.database.person_assets_database import PersonAssetInCreate, create_person_asset
from server.database.income_sources_database import IncomeSourceInCreate, create_income_source


# -----------------------------------------------------------------------------
# Wizard Data Models
# -----------------------------------------------------------------------------

class PersonDeclaration(BaseModel):
    """Person information declared in the wizard"""
    first_name: str
    last_name: str
    id_number: str
    role_id: uuid.UUID
    gender: str
    birth_date: Optional[str] = None
    relationship_to_primary: Optional[uuid.UUID] = None  # Relationship type ID if not primary
    marital_status_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class CompanyDeclaration(BaseModel):
    """Company information declared in the wizard"""
    name: str
    company_type_id: uuid.UUID
    company_id_num: str
    owner_person_index: int  # Index of the person in the persons array who owns this company


class BankAccountDeclaration(BaseModel):
    """Bank account information declared in the wizard"""
    bank_name: str
    account_type_id: uuid.UUID
    account_number: str
    owner_person_index: int  # Index of the person in the persons array who owns this account


class CreditCardDeclaration(BaseModel):
    """Credit card information declared in the wizard"""
    issuer: str
    card_type_id: uuid.UUID
    last_four: int
    owner_person_index: int  # Index of the person in the persons array who owns this card


class LoanDeclaration(BaseModel):
    """Loan information declared in the wizard"""
    loan_type_id: uuid.UUID
    lender: str
    owner_person_index: int  # Index of the person in the persons array who has this loan


class AssetDeclaration(BaseModel):
    """Asset information declared in the wizard"""
    asset_type_id: uuid.UUID
    label: str  # Primary identification field as per PRD
    owner_person_index: int  # Index of the person in the persons array who owns this asset


class IncomeSourceDeclaration(BaseModel):
    """Income source information declared in the wizard"""
    income_source_type_id: uuid.UUID
    label: str  # Primary identification field as per PRD
    owner_person_index: int  # Index of the person in the persons array who has this income


class CaseDeclarationSurvey(BaseModel):
    """
    Declaration survey model for collecting all information needed to setup a case structure.
    This implements the "declaration survey" mentioned in the PRD.
    """
    # Basic case information
    case_name: str
    case_purpose: str
    loan_type_id: uuid.UUID
    
    # Persons involved in the case
    persons: List[PersonDeclaration]
    
    # Companies related to persons in the case
    companies: Optional[List[CompanyDeclaration]] = Field(default_factory=list)
    
    # Financial entities
    bank_accounts: Optional[List[BankAccountDeclaration]] = Field(default_factory=list)
    credit_cards: Optional[List[CreditCardDeclaration]] = Field(default_factory=list)
    loans: Optional[List[LoanDeclaration]] = Field(default_factory=list)
    assets: Optional[List[AssetDeclaration]] = Field(default_factory=list)
    
    # Income sources
    income_sources: Optional[List[IncomeSourceDeclaration]] = Field(default_factory=list)


class WizardResult(BaseModel):
    """Result of the new case wizard process"""
    case: CaseInDB
    created_entities: Dict[str, List[Dict[str, Any]]]
    success: bool
    errors: Optional[List[str]] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Wizard Database Operations
# -----------------------------------------------------------------------------

async def create_case_with_wizard(survey: CaseDeclarationSurvey) -> WizardResult:
    """
    Create a new case with all related entities based on the declaration survey.
    This implements the "New Case Wizard" guided workflow mentioned in the PRD.
    
    Args:
        survey (CaseDeclarationSurvey): The declaration survey containing all information
        
    Returns:
        WizardResult: Results of the wizard process including the created case and all related entities
    """
    conn = await get_connection()
    created_entities = {
        "persons": [],
        "companies": [],
        "bank_accounts": [],
        "credit_cards": [],
        "loans": [],
        "assets": [],
        "income_sources": [],
        "relationships": []
    }
    errors = []
    
    try:
        # Start a transaction to ensure all entities are created or none are
        async with conn.transaction():
            # 1. Create the case
            case_data = CaseInCreate(
                name=survey.case_name,
                status="active",
                case_purpose=survey.case_purpose,
                loan_type_id=survey.loan_type_id
            )
            
            case = await create_case(case_data)
            
            # 2. Create all person records and store their IDs
            person_ids = []
            primary_person_id = None
            
            for i, person_declaration in enumerate(survey.persons):
                try:
                    person_data = CasePersonCreate(
                        case_id=case.id,
                        first_name=person_declaration.first_name,
                        last_name=person_declaration.last_name,
                        id_number=person_declaration.id_number,
                        role_id=person_declaration.role_id,
                        gender=person_declaration.gender,
                        birth_date=datetime.strptime(person_declaration.birth_date, "%Y-%m-%d").date() if person_declaration.birth_date else datetime.now().date(),
                        marital_status_id=person_declaration.marital_status_id,
                        email=person_declaration.email,
                        phone=person_declaration.phone
                    )
                    
                    person = await create_case_person(person_data)
                    person_ids.append(person.id)
                    created_entities["persons"].append({"id": str(person.id), "name": f"{person.first_name} {person.last_name}"})
                    
                    # Set primary person (first person is assumed to be primary)
                    if i == 0:
                        primary_person_id = person.id
                        
                        # Update case with primary contact
                        from server.database.cases_database import update_case
                        from server.database.cases_database import CaseUpdate
                        
                        await update_case(case.id, CaseUpdate(primary_contact_id=primary_person_id))
                        
                except Exception as e:
                    errors.append(f"Error creating person {person_declaration.first_name} {person_declaration.last_name}: {str(e)}")
                    raise
            
            # 3. Create person relationships (if more than one person)
            if len(person_ids) > 1:
                for i, person_declaration in enumerate(survey.persons):
                    # Skip primary person (index 0)
                    if i == 0:
                        continue
                        
                    # If relationship type is specified, create the relationship
                    if person_declaration.relationship_to_primary:
                        try:
                            relation_data = CasePersonRelationCreate(
                                from_person_id=primary_person_id,
                                to_person_id=person_ids[i],
                                relationship_type_id=person_declaration.relationship_to_primary
                            )
                            
                            relation = await create_person_relation(relation_data)
                            created_entities["relationships"].append({
                                "from_person_id": str(primary_person_id),
                                "to_person_id": str(person_ids[i]),
                                "relationship_type_id": str(person_declaration.relationship_to_primary)
                            })
                            
                        except Exception as e:
                            errors.append(f"Error creating relationship between persons: {str(e)}")
                            # Continue even if a relationship fails
            
            # 4. Create companies
            for company_declaration in survey.companies:
                try:
                    # Ensure the owner person index is valid
                    if company_declaration.owner_person_index >= len(person_ids):
                        errors.append(f"Invalid owner person index for company {company_declaration.name}")
                        continue
                        
                    company_data = CompanyInCreate(
                        case_id=case.id,
                        name=company_declaration.name,
                        company_type_id=company_declaration.company_type_id,
                        company_id_num=company_declaration.company_id_num
                    )
                    
                    company = await create_company(company_data)
                    created_entities["companies"].append({
                        "id": str(company.id),
                        "name": company.name,
                        "company_id_num": company.company_id_num,  # Added primary identification field as per PRD
                        "owner_person_id": str(person_ids[company_declaration.owner_person_index])
                    })
                    
                except Exception as e:
                    errors.append(f"Error creating company {company_declaration.name}: {str(e)}")
                    # Continue even if a company creation fails
            
            # 5. Create bank accounts
            for bank_account_declaration in survey.bank_accounts:
                try:
                    # Ensure the owner person index is valid
                    if bank_account_declaration.owner_person_index >= len(person_ids):
                        errors.append(f"Invalid owner person index for bank account {bank_account_declaration.account_number}")
                        continue
                        
                    account_data = BankAccountInCreate(
                        person_id=person_ids[bank_account_declaration.owner_person_index],
                        account_type_id=bank_account_declaration.account_type_id,
                        bank_name=bank_account_declaration.bank_name,
                        account_number=bank_account_declaration.account_number
                    )
                    
                    account = await create_bank_account(account_data)
                    created_entities["bank_accounts"].append({
                        "id": str(account.id),
                        "bank_name": account.bank_name,
                        "account_number": account.account_number,
                        "owner_person_id": str(person_ids[bank_account_declaration.owner_person_index])
                    })
                    
                except Exception as e:
                    errors.append(f"Error creating bank account {bank_account_declaration.account_number}: {str(e)}")
                    # Continue even if a bank account creation fails
            
            # 6. Create credit cards
            for credit_card_declaration in survey.credit_cards:
                try:
                    # Ensure the owner person index is valid
                    if credit_card_declaration.owner_person_index >= len(person_ids):
                        errors.append(f"Invalid owner person index for credit card {credit_card_declaration.issuer}")
                        continue
                        
                    credit_card_data = CreditCardInCreate(
                        person_id=person_ids[credit_card_declaration.owner_person_index],
                        issuer=credit_card_declaration.issuer,
                        card_type_id=credit_card_declaration.card_type_id,
                        last_four=credit_card_declaration.last_four
                    )
                    
                    credit_card = await create_credit_card(credit_card_data)
                    created_entities["credit_cards"].append({
                        "id": str(credit_card.id),
                        "issuer": credit_card.issuer,
                        "last_four": credit_card.last_four,
                        "owner_person_id": str(person_ids[credit_card_declaration.owner_person_index])
                    })
                    
                except Exception as e:
                    errors.append(f"Error creating credit card {credit_card_declaration.issuer}: {str(e)}")
                    # Continue even if a credit card creation fails
            
            # 7. Create loans
            for loan_declaration in survey.loans:
                try:
                    # Ensure the owner person index is valid
                    if loan_declaration.owner_person_index >= len(person_ids):
                        errors.append(f"Invalid owner person index for loan from {loan_declaration.lender}")
                        continue
                        
                    loan_data = PersonLoanInCreate(
                        person_id=person_ids[loan_declaration.owner_person_index],
                        loan_type_id=loan_declaration.loan_type_id,
                        lender=loan_declaration.lender
                    )
                    
                    loan = await create_person_loan(loan_data)
                    created_entities["loans"].append({
                        "id": str(loan.id),
                        "lender": loan.lender,
                        "owner_person_id": str(person_ids[loan_declaration.owner_person_index])
                    })
                    
                except Exception as e:
                    errors.append(f"Error creating loan from {loan_declaration.lender}: {str(e)}")
                    # Continue even if a loan creation fails
            
            # 8. Create assets
            for asset_declaration in survey.assets:
                try:
                    # Ensure the owner person index is valid
                    if asset_declaration.owner_person_index >= len(person_ids):
                        errors.append(f"Invalid owner person index for asset {asset_declaration.label}")
                        continue
                        
                    asset_data = PersonAssetInCreate(
                        person_id=person_ids[asset_declaration.owner_person_index],
                        asset_type_id=asset_declaration.asset_type_id,
                        label=asset_declaration.label  # Using label as primary identification field as per PRD
                    )
                    
                    asset = await create_person_asset(asset_data)
                    created_entities["assets"].append({
                        "id": str(asset.id),
                        "label": asset.label,  # Changed from description to label to match PRD
                        "owner_person_id": str(person_ids[asset_declaration.owner_person_index])
                    })
                    
                except Exception as e:
                    errors.append(f"Error creating asset {asset_declaration.label}: {str(e)}")
                    # Continue even if an asset creation fails
            
            # 9. Create income sources (including employment)
            for income_declaration in survey.income_sources:
                try:
                    # Ensure the owner person index is valid
                    if income_declaration.owner_person_index >= len(person_ids):
                        errors.append(f"Invalid owner person index for income source {income_declaration.label}")
                        continue
                        
                    income_data = IncomeSourceInCreate(
                        person_id=person_ids[income_declaration.owner_person_index],
                        income_source_type_id=income_declaration.income_source_type_id,
                        label=income_declaration.label
                    )
                    
                    income = await create_income_source(income_data)
                    created_entities["income_sources"].append({
                        "id": str(income.id),
                        "label": income.label,
                        "owner_person_id": str(person_ids[income_declaration.owner_person_index])
                    })
                    
                    # If this is a work income, create employment history entry
                    # We need to check if this is a work-type income source
                    query = """
                    SELECT name, value
                    FROM lior_dropdown_options
                    WHERE id = $1
                    """
                    income_type = await conn.fetchrow(query, income_declaration.income_source_type_id)
                    
                    if income_type and income_type["value"].lower() == "work":
                        from server.database.employment_history_database import (
                            EmploymentHistoryInCreate,
                            create_employment_history
                        )
                        
                        # Create employment history entry
                        employment_data = EmploymentHistoryInCreate(
                            person_id=person_ids[income_declaration.owner_person_index],
                            employer_name=income_declaration.label,
                            position="",  # Default empty position
                            employment_type_id=income_declaration.income_source_type_id,  # Using same ID
                            current_employer=True
                        )
                        
                        await create_employment_history(employment_data)
                    
                except Exception as e:
                    errors.append(f"Error creating income source {income_declaration.label}: {str(e)}")
                    # Continue even if an income source creation fails
            
            # Get the updated case info to return
            from server.database.cases_database import get_case
            updated_case = await get_case(case.id)
            
            return WizardResult(
                case=updated_case,
                created_entities=created_entities,
                success=len(errors) == 0,
                errors=errors
            )
            
    except Exception as e:
        # If any critical error occurs, the transaction will rollback
        return WizardResult(
            case=None,
            created_entities={},
            success=False,
            errors=[f"Critical error in wizard process: {str(e)}"]
        )
    finally:
        await conn.close()
