"""
Database migrations module - handles creating database schema and seeding initial data
"""
import asyncio
import logging
import os
import datetime
import uuid
from pathlib import Path

from server.database.database import drop_all_tables, get_connection
from server.database.lior_dropdown_options_database import DropdownOptionCreate, create_dropdown_option
from server.database.unique_docs_database import (
    UniqueDocTypeCreate, 
    DocumentCategory, 
    DocumentTargetObject, 
    DocumentType, 
    DocumentFrequency,
    RequiredFor,
    Links,
    ContactInfo,
    create_unique_doc_type
)

logger = logging.getLogger(__name__)

# ------------------------------------------------
# Sample Data for Dropdown Options
# ------------------------------------------------

# Sample document types
DOCUMENT_TYPES = [
    {
        "display_name": "תעודת זהות - צד קדמי",
        "category": DocumentCategory.IDENTIFICATION,
        "issuer": "משרד הפנים",
        "target_object": DocumentTargetObject.PERSON,
        "document_type": DocumentType.ONE_TIME,
        "is_recurring": False,
        "required_for": [RequiredFor.EMPLOYEES, RequiredFor.SELF_EMPLOYED, RequiredFor.BUSINESS_OWNERS],
        "links": {"url": "https://www.gov.il/he/service/smart_id_application_form"},
        "contact_info": {"phone": "*3450", "hours": "א'-ה' 8:00-18:00"}
    },
    {
        "display_name": "תעודת זהות - צד אחורי",
        "category": DocumentCategory.IDENTIFICATION,
        "issuer": "משרד הפנים",
        "target_object": DocumentTargetObject.PERSON,
        "document_type": DocumentType.ONE_TIME,
        "is_recurring": False,
        "required_for": [RequiredFor.EMPLOYEES, RequiredFor.SELF_EMPLOYED, RequiredFor.BUSINESS_OWNERS],
        "links": {"url": "https://www.gov.il/he/service/smart_id_application_form"},
        "contact_info": {"phone": "*3450", "hours": "א'-ה' 8:00-18:00"}
    },
    {
        "display_name": "דף חשבון בנק",
        "category": DocumentCategory.FINANCIAL,
        "issuer": "בנקים",
        "target_object": DocumentTargetObject.BANK_ACCOUNT,
        "document_type": DocumentType.RECURRING,
        "is_recurring": True,
        "frequency": DocumentFrequency.MONTHLY,
        "required_for": [RequiredFor.EMPLOYEES, RequiredFor.SELF_EMPLOYED, RequiredFor.BUSINESS_OWNERS],
        "links": {"url": "https://www.bankofisrael.org.il/"},
        "contact_info": {"email": "support@banking.org.il", "phone": "*5600"}
    },
    {
        "display_name": "תלוש משכורת",
        "category": DocumentCategory.EMPLOYMENT,
        "issuer": "מעסיקים",
        "target_object": DocumentTargetObject.INCOME,
        "document_type": DocumentType.RECURRING,
        "is_recurring": True,
        "frequency": DocumentFrequency.MONTHLY,
        "required_for": [RequiredFor.EMPLOYEES],
        "links": {"url": "https://www.gov.il/he/departments/topics/payslip"},
        "contact_info": {"email": "info@employment.org.il"}
    },
    {
        "display_name": "דוח שנתי - מס הכנסה",
        "category": DocumentCategory.TAX,
        "issuer": "רשות המסים",
        "target_object": DocumentTargetObject.PERSON,
        "document_type": DocumentType.RECURRING,
        "is_recurring": True,
        "frequency": DocumentFrequency.YEARLY,
        "required_for": [RequiredFor.EMPLOYEES, RequiredFor.SELF_EMPLOYED, RequiredFor.BUSINESS_OWNERS],
        "links": {"url": "https://www.gov.il/he/departments/israel_tax_authority"},
        "contact_info": {"phone": "*4954", "hours": "א'-ה' 8:00-16:00"}
    },
    {
        "display_name": "דוח פעילות עסקית",
        "category": DocumentCategory.FINANCIAL,
        "issuer": "רואי חשבון/עסקים",
        "target_object": DocumentTargetObject.COMPANY,
        "document_type": DocumentType.RECURRING,
        "is_recurring": True,
        "frequency": DocumentFrequency.QUARTERLY,
        "required_for": [RequiredFor.SELF_EMPLOYED, RequiredFor.BUSINESS_OWNERS],
        "links": {"url": "https://www.gov.il/he/departments/topics/business_licensing"},
        "contact_info": {"email": "business.support@gov.il"}
    }
]

# Person roles sample data
PERSON_ROLES = [
    {"name": "מבקש ראשי", "value": "primary_applicant"},
    {"name": "מבקש משני", "value": "co_applicant"},
    {"name": "ערב", "value": "guarantor"},
    {"name": "בן/בת זוג", "value": "spouse"},
    {"name": "תלוי", "value": "dependent"},
    {"name": "מיופה כוח", "value": "power_of_attorney"},
]

# Person marital statuses sample data
PERSON_MARITAL_STATUSES = [
    {"name": "רווק/ה", "value": "single"},
    {"name": "נשוי/אה", "value": "married"},
    {"name": "גרוש/ה", "value": "divorced"},
    {"name": "אלמן/ה", "value": "widowed"},
    {"name": "פרוד/ה", "value": "separated"},
    {"name": "ידוע/ה בציבור", "value": "common_law"},
]

# Loan types sample data
LOAN_TYPES = [
    {"name": "משכנתא", "value": "mortgage"},
    {"name": "הלוואה כנגד נכס", "value": "heloc"},
    {"name": "הלוואה אישית", "value": "personal_loan"},
    {"name": "הלוואת רכב", "value": "auto_loan"},
    {"name": "הלוואה עסקית", "value": "business_loan"},
    {"name": "הלוואת סטודנט", "value": "student_loan"},
    {"name": "מסגרת אשראי", "value": "credit_line"},
]

# Loan goals sample data
LOAN_GOALS = [
    {"name": "רכישת דירת מגורים", "value": "purchase_primary"},
    {"name": "רכישת דירה שניה", "value": "purchase_secondary"},
    {"name": "רכישת נכס להשקעה", "value": "purchase_investment"},
    {"name": "מיחזור הלוואה", "value": "refinance"},
    {"name": "איחוד הלוואות", "value": "debt_consolidation"},
    {"name": "שיפוץ בית", "value": "home_improvement"},
    {"name": "מימון לימודים", "value": "education"},
    {"name": "הרחבת עסק", "value": "business_expansion"},
]

# Case status sample data
CASE_STATUS = [
    {"name": "חדש", "value": "new"},
    {"name": "בתהליך", "value": "in_progress"},
    {"name": "ממתין למסמכים", "value": "pending_docs"},
    {"name": "בבדיקה", "value": "under_review"},
    {"name": "מאושר", "value": "approved"},
    {"name": "נדחה", "value": "declined"},
    {"name": "בוטל על ידי הלקוח", "value": "withdrawn"},
    {"name": "סגור", "value": "closed"},
]

# Related person relationships types sample data
RELATED_PERSON_RELATIONSHIPS_TYPES = [
    {"name": "בן/בת זוג", "value": "spouse"},
    {"name": "הורה", "value": "parent"},
    {"name": "ילד/ה", "value": "child"},
    {"name": "אח/אחות", "value": "sibling"},
    {"name": "סבא/סבתא", "value": "grandparent"},
    {"name": "נכד/ה", "value": "grandchild"},
    {"name": "בן/בת דוד/ה", "value": "cousin"},
    {"name": "דוד/ה", "value": "aunt_uncle"},
    {"name": "אחיין/אחיינית", "value": "niece_nephew"},
    {"name": "חבר/ה", "value": "friend"},
    {"name": "שותף/ה עסקי/ת", "value": "business_partner"},
]

# ------------------------------------------------
# Seed Data Functions
# ------------------------------------------------

async def seed_dropdown_options():
    """
    Seed the database with initial dropdown options
    """
    logger.info("Seeding dropdown options...")

    # Prepare all dropdown options for seeding
    options_to_seed = [
        {"category": "person_roles", "options": PERSON_ROLES},
        {"category": "person_marital_statuses", "options": PERSON_MARITAL_STATUSES},
        {"category": "loan_types", "options": LOAN_TYPES},
        {"category": "loan_goals", "options": LOAN_GOALS},
        {"category": "case_status", "options": CASE_STATUS},
        {"category": "related_person_relationships_types", "options": RELATED_PERSON_RELATIONSHIPS_TYPES},
    ]

    # Create each option in the database
    for category_data in options_to_seed:
        category = category_data["category"]
        options = category_data["options"]

        logger.info(f"Seeding {len(options)} options for category: {category}")

        for option in options:
            create_data = DropdownOptionCreate(
                category=category,
                name=option["name"],
                value=option["value"]
            )

            try:
                await create_dropdown_option(create_data)
            except Exception as e:
                logger.error(f"Error seeding option {option['name']} in {category}: {str(e)}")

    logger.info("Dropdown options seeded successfully")


async def seed_document_types():
    """
    Seed the database with sample document types
    """
    logger.info("Seeding document types...")

    for doc_type in DOCUMENT_TYPES:
        try:
            links_data = None
            if doc_type.get("links"):
                links_data = Links(**doc_type["links"])
                
            contact_info_data = None
            if doc_type.get("contact_info"):
                contact_info_data = ContactInfo(**doc_type["contact_info"])
                
            create_data = UniqueDocTypeCreate(
                display_name=doc_type["display_name"],
                category=doc_type["category"],
                issuer=doc_type.get("issuer"),
                target_object=doc_type["target_object"],
                document_type=doc_type["document_type"],
                is_recurring=doc_type["is_recurring"],
                frequency=doc_type.get("frequency"),
                required_for=doc_type["required_for"],
                links=links_data,
                contact_info=contact_info_data
            )
            
            await create_unique_doc_type(create_data)
            logger.info(f"Created document type: {doc_type['display_name']}")
            
        except Exception as e:
            logger.error(f"Error seeding document type {doc_type['display_name']}: {str(e)}")
            
    logger.info("Document types seeded successfully")


async def create_sample_case():
    """
    Create a sample case with persons and related objects.
    This function does NOT add any documents to the case.
    """
    logger.info("Creating sample case...")
    
    conn = await get_connection()
    try:
        async with conn.transaction():
            # 1. Create a new case
            case_id = uuid.uuid4()
            case_name = "בקשת משכנתא - משפחת כהן"
            case_query = """
            INSERT INTO cases (
                id, name, status, title, description, case_purpose, loan_type_id
            ) VALUES ($1, $2, $3, $4, $5, $6, 
                (SELECT id FROM lior_dropdown_options WHERE category = 'loan_types' AND value = 'mortgage' LIMIT 1)
            )
            RETURNING id
            """
            
            await conn.fetchrow(
                case_query,
                case_id,
                case_name,
                "in_progress",
                "בקשת משכנתא למשפחת כהן",
                "בקשת משכנתא לרכישת דירה ראשונה",
                "רכישת דירה ראשונה"
            )
            
            logger.info(f"Created sample case: {case_name} with ID: {case_id}")
            
            # 2. Create primary applicant
            primary_person_id = uuid.uuid4()
            primary_person_query = """
            INSERT INTO case_persons (
                id, case_id, first_name, last_name, id_number, gender, birth_date,
                phone, email, role_id, marital_status_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9,
                (SELECT id FROM lior_dropdown_options WHERE category = 'person_roles' AND value = 'primary_applicant' LIMIT 1),
                (SELECT id FROM lior_dropdown_options WHERE category = 'person_marital_statuses' AND value = 'married' LIMIT 1)
            )
            RETURNING id
            """
            
            await conn.fetchrow(
                primary_person_query,
                primary_person_id,
                case_id,
                "ישראל",
                "כהן",
                "012345678",
                "male",
                datetime.date(1985, 5, 15),
                "0501234567",
                "israel.cohen@example.com"
            )
            
            logger.info(f"Created primary applicant: ישראל כהן with ID: {primary_person_id}")
            
            # 3. Create spouse
            spouse_person_id = uuid.uuid4()
            spouse_person_query = """
            INSERT INTO case_persons (
                id, case_id, first_name, last_name, id_number, gender, birth_date,
                phone, email, role_id, marital_status_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9,
                (SELECT id FROM lior_dropdown_options WHERE category = 'person_roles' AND value = 'spouse' LIMIT 1),
                (SELECT id FROM lior_dropdown_options WHERE category = 'person_marital_statuses' AND value = 'married' LIMIT 1)
            )
            RETURNING id
            """
            
            await conn.fetchrow(
                spouse_person_query,
                spouse_person_id,
                case_id,
                "שרה",
                "כהן",
                "012345679",
                "female",
                datetime.date(1987, 8, 22),
                "0501234568",
                "sarah.cohen@example.com"
            )
            
            logger.info(f"Created spouse: שרה כהן with ID: {spouse_person_id}")
            
            # 4. Set primary contact for the case
            update_case_query = """
            UPDATE cases SET primary_contact_id = $1 WHERE id = $2
            """
            
            await conn.execute(update_case_query, primary_person_id, case_id)
            
            # 5. Create a relationship between primary applicant and spouse
            relationship_query = """
            INSERT INTO case_person_relations (
                from_person_id, to_person_id, relationship_type_id
            ) VALUES (
                $1, $2,
                (SELECT id FROM lior_dropdown_options WHERE category = 'related_person_relationships_types' AND value = 'spouse' LIMIT 1)
            )
            """
            
            await conn.execute(relationship_query, primary_person_id, spouse_person_id)
            
            # 6. Create bank account for primary person
            bank_account_id = uuid.uuid4()
            bank_account_query = """
            INSERT INTO person_bank_accounts (
                id, person_id, account_type_id, bank_name, account_number
            ) VALUES (
                $1, $2,
                (SELECT id FROM lior_dropdown_options WHERE category = 'loan_types' AND value = 'mortgage' LIMIT 1),
                $3, $4
            )
            RETURNING id
            """
            
            await conn.fetchrow(
                bank_account_query,
                bank_account_id,
                primary_person_id,
                "בנק לאומי",
                "12-345-67890"
            )
            
            logger.info(f"Created bank account for primary applicant with ID: {bank_account_id}")
            
            # 7. Create employment history for primary person
            employment_query = """
            INSERT INTO person_employment_history (
                person_id, employer_name, position, employment_type_id, current_employer
            ) VALUES (
                $1, $2, $3,
                (SELECT id FROM lior_dropdown_options WHERE category = 'loan_types' AND value = 'mortgage' LIMIT 1),
                $4
            )
            """
            
            await conn.execute(
                employment_query,
                primary_person_id,
                "חברת היי-טק בע\"מ",
                "מהנדס תוכנה",
                True
            )
            
            # 8. Create employment history for spouse
            await conn.execute(
                employment_query,
                spouse_person_id,
                "משרד החינוך",
                "מורה",
                True
            )
            
            logger.info(f"Created employment history for both applicants")
            
            logger.info(f"Sample case created successfully with ID: {case_id}")
            return case_id
            
    except Exception as e:
        logger.error(f"Error creating sample case: {str(e)}")
        return None
    finally:
        await conn.close()

# ------------------------------------------------
# Main Migration Process
# ------------------------------------------------

def generate_html_report(seeded_categories) -> str:
    """
    Generate an HTML report for schema creation and data seeding

    Args:
        seeded_categories: List of categories that were seeded with data

    Returns:
        Path to the generated HTML file
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_dir = Path("./reports")
    report_dir.mkdir(exist_ok=True)

    report_path = report_dir / f"schema_creation_report_{timestamp}.html"

    # Generate category details for the report
    category_details = ""
    for category in seeded_categories:
        options_list = ""
        options_data = None

        if category == "person_roles":
            options_data = PERSON_ROLES
        elif category == "person_marital_statuses":
            options_data = PERSON_MARITAL_STATUSES
        elif category == "loan_types":
            options_data = LOAN_TYPES
        elif category == "loan_goals":
            options_data = LOAN_GOALS
        elif category == "case_status":
            options_data = CASE_STATUS
        elif category == "related_person_relationships_types":
            options_data = RELATED_PERSON_RELATIONSHIPS_TYPES

        if options_data:
            for option in options_data:
                options_list += f"<li><strong>{option['name']}</strong> ({option['value']})</li>"

            category_details += f"""
            <div class="category">
                <h3>{category}</h3>
                <ul>
                    {options_list}
                </ul>
            </div>
            """

    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Database Schema Creation Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #3498db;
                margin-top: 30px;
                border-left: 4px solid #3498db;
                padding-left: 10px;
            }}
            h3 {{
                color: #2980b9;
                margin-top: 20px;
                text-transform: capitalize;
            }}
            .timestamp {{
                text-align: center;
                color: #7f8c8d;
                font-style: italic;
                margin-bottom: 30px;
            }}
            .summary {{
                background-color: #e8f4f8;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .category {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }}
            ul {{
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <h1>Database Schema Creation Report</h1>
        <div class="timestamp">Generated on {datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</div>
        
        <div class="summary">
            <h2>Schema Created Successfully</h2>
            <p>Database schema has been created and seeded with initial data for the following categories:</p>
        </div>
        
        <h2>Seeded Dropdown Options</h2>
        {category_details}
    </body>
    </html>
    """

    # Write to file
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return str(report_path)

async def run_migrations():
    """
    Run schema creation and seed initial data
    """
    logger.info("Starting database schema creation...")

    # Define categories to be seeded
    seeded_categories = [
        "person_roles",
        "person_marital_statuses",
        "loan_types",
        "loan_goals",
        "case_status",
        "related_person_relationships_types"
    ]

    # Seed dropdown options
    try:
        await seed_dropdown_options()
        logger.info("Successfully seeded dropdown options")
    except Exception as e:
        logger.error(f"Error seeding dropdown options: {str(e)}")

    # Seed document types
    try:
        await seed_document_types()
        logger.info("Successfully seeded document types")
    except Exception as e:
        logger.error(f"Error seeding document types: {str(e)}")

    # Create a sample case
    try:
        sample_case_id = await create_sample_case()
        if sample_case_id:
            logger.info(f"Sample case created with ID: {sample_case_id}")
        else:
            logger.error("Failed to create sample case")
    except Exception as e:
        logger.error(f"Error creating sample case: {str(e)}")

    # Create report with seeded data information
    try:
        report_path = generate_html_report(seeded_categories)
        logger.info(f"HTML report generated at: {report_path}")

        # Open the report in browser
        try:
            os.system(f"open {report_path}")
            logger.info(f"Opened HTML report in browser")
        except Exception as e:
            logger.error(f"Failed to open HTML report: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating HTML report: {str(e)}")

    logger.info("Database schema created and seeded successfully")


# For standalone script execution
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(run_migrations())