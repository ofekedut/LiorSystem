"""
Database migrations module - handles seeding initial data using application models
"""
import asyncio
import logging
import os
import datetime
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from server.database.database import drop_all_tables, get_connection
from server.database.document_types_database import (
    DocumentTypeInCreate,
    DocumentType,
    create_document_type
)
from server.database.document_categories_database import (
    DocumentCategoryInCreate,
    DocumentCategory,
    create_document_category
)
from server.database.documents_database import (
    DocumentInCreate,
    DocumentInDB,
    create_document
)

logger = logging.getLogger(__name__)

# ------------------------------------------------
# Document Types Migration
# ------------------------------------------------

# Document types to create - (name, value) - keep values in English
DOCUMENT_TYPES = [
    ('אחר', 'other'),
    ('פרוטוקול', 'protocol'),
    ('חד פעמי', 'one-time'),
    ('ניתן לעדכון', 'updatable'),
    ('מתחדש', 'recurring'),
    ('דו-שנתי', 'biennial'),
    ('שנתי', 'annual'),
    ('רבעוני', 'quarterly'),
    ('חודשי', 'monthly'),
    ('שבועי', 'weekly'),
    ('אישור', 'approval'),
    ('תעודת זהות', 'id'),
    ('רישיון', 'license'),
    ('דו"ח', 'report'),
    ('תעודה', 'certificate'),
    ('חוזה', 'contract'),
    ('תוכנית', 'plan'),
    ('הלוואה', 'loan'),
    ('היתר', 'permit'),
    ('מס', 'tax'),
    ('פוליסה', 'policy'),
    ('קבלה', 'receipt'),
    ('חשבונית', 'invoice'),
    ('הצהרה', 'declaration'),
    ('הסכם', 'agreement')
]


async def create_document_types() -> Dict[str, UUID]:
    """
    Create document types and return a mapping of value to ID
    """
    logger.info("Creating document types...")
    logger.info(f"Document types to create: {[value for _, value in DOCUMENT_TYPES]}")
    type_map = {}

    for name, value in DOCUMENT_TYPES:
        try:
            # Create a document type using the model
            doc_type = await create_document_type(
                DocumentTypeInCreate(name=name, value=value)
            )

            # Store the ID in the map for later use
            type_map[value] = doc_type.id
            logger.info(f"Created document type: {name} ({value})")

        except Exception as e:
            logger.error(f"Error creating document type {name}: {str(e)}")

    logger.info(f"Created {len(type_map)}/{len(DOCUMENT_TYPES)} document types")
    return type_map


# ------------------------------------------------
# Document Categories Migration
# ------------------------------------------------

# Document categories to create - (name, value) - values remain English
DOCUMENT_CATEGORIES = [
    ('מסמכים מנהליים', 'administrative'),
    ('מסמכים פיננסיים', 'financial'),
    ('מסמכי נדל"ן', 'property'),
    ('מסמכי זיהוי', 'identification'),
    ('מסמכים עסקיים', 'business'),
    ('מסמכי נכסים', 'asset'),
    ('מסמכי מס', 'tax'),
    ('מסמכי תעסוקה', 'employment'),
    ('מסמכים אישיים', 'personal'),
    ('מסמכי הלוואות', 'loan'),
    ('מסמכי חשבון בנק', 'bank_account'),
    ('מסמכי חברה', 'company'),
    ('מסמכי כרטיסי אשראי', 'credit_card'),
    ('מסמכי הכנסה', 'income'),
    ('דוחות כספיים', 'financial_statements'),
    ('מסמכי ביטוח', 'insurance'),
    ('מסמכי השקעות', 'investments'),
    ('מסמכי פנסיה', 'pension'),
    ('מסמכי בריאות', 'health'),
    ('מסמכים משפטיים', 'legal'),
    ('מסמכי חינוך', 'education'),
    ('מסמכי צבא', 'military')
]


async def create_document_categories() -> Dict[str, UUID]:
    """
    Create document categories and return a mapping of value to ID
    """
    logger.info("Creating document categories...")
    category_map = {}

    for name, value in DOCUMENT_CATEGORIES:
        try:
            # Create a document category using the model
            category = await create_document_category(
                DocumentCategoryInCreate(name=name, value=value)
            )

            # Store the ID in the map for later use
            category_map[value] = category.id
            logger.info(f"Created document category: {name} ({value})")

        except Exception as e:
            logger.error(f"Error creating document category {name}: {str(e)}")

    logger.info(f"Created {len(category_map)}/{len(DOCUMENT_CATEGORIES)} document categories")
    return category_map


# ------------------------------------------------
# Documents Migration
# ------------------------------------------------

# Documents to create - (name, description, category, has_multiple_periods, document_type_value)
DOCUMENTS = [
    # Basic documents
    ('DNA_ADMINISTRATIVE', 'DNA_מינהלי', 'administrative', False, 'other'),
    ('DNA_OSH', 'DNA_בטיחות', 'administrative', False, 'other'),
    ('NEW_ID_CARD', 'תעודת זהות חדשה', 'identification', False, 'id'),
    ('DRIVERS_LICENSE', 'רישיון נהיגה', 'identification', False, 'license'),
    ('RATING_REPORT', 'דו"ח דירוג', 'financial', False, 'report'),
    ('COMPLETION_CERTIFICATE', 'תעודת השלמה', 'administrative', False, 'certificate'),
    ('BDI_DATA_SUMMARY', 'BDI_סיכום נתונים', 'financial', False, 'report'),
    ('DNA_INFORMATION_REQUESTS', 'DNA_בקשות מידע', 'administrative', False, 'other'),
    ('DNA_GENERAL', 'DNA_כללי', 'administrative', False, 'other'),
    ('RIGHTS_CONFIRMATION', 'אישור זכויות', 'property', False, 'certificate'),
    ('HOUSE_SCRIPT', 'תסריט בית', 'property', False, 'plan'),
    ('BUILDING_PLAN', 'תוכנית בניין', 'property', False, 'plan'),
    ('ID_APPENDIX', 'נספח תעודת זהות', 'identification', False, 'id'),
    ('BUSINESS_LICENSE', 'רישיון עסק', 'business', False, 'license'),
    ('BDI_PUBLIC_ENTITIES', 'BDI_גופים ציבוריים', 'financial', False, 'report'),
    ('PROPERTY_EXTRACT', 'תעודת מקרקעין', 'property', False, 'certificate'),
    ('SALES_CONTRACT', 'חוזה מכר', 'property', False, 'contract'),
    ('VEHICLE_LICENSE', 'רישיון רכב', 'asset', False, 'license'),
    ('SIGNATURE_PROTOCOL', 'פרוטוקול חתימה', 'administrative', False, 'protocol'),
    ('COMPANY_EXTRACT', 'תקציר חברה', 'business', False, 'certificate'),
    ('PASSPORT', 'דרכון', 'identification', False, 'id'),
    ('BDI_TRANSACTION_SUMMARY', 'BDI_סיכום עסקאות', 'financial', False, 'report'),
    ('BDI_TREND_ANALYSIS', 'BDI_ניתוח מגמות', 'financial', False, 'report'),
    ('LEASE_CONTRACT', 'חוזה שכירות', 'property', False, 'contract'),
    ('DNA_LOANS', 'DNA הלוואות', 'financial', False, 'loan'),
    ('APPRAISAL', 'שמאות', 'property', False, 'report'),
    ('CREDIT_REPORT', 'דו"ח אשראי', 'financial', False, 'report'),
    ('BUILDING_PERMIT', 'היתר בניה', 'property', False, 'permit'),
    ('OLD_ID_CARD', 'תעודת זהות ישנה', 'identification', False, 'id'),
    ('CERTIFICATE_OF_INCORPORATION', 'תעודת התאגדות', 'business', False, 'certificate'),
    ('PROPERTY_TAX', 'ארנונה', 'tax', False, 'tax'),

    # Identification documents
    ('BIRTH_CERTIFICATE', 'תעודת לידה', 'identification', False, 'id'),
    ('MARRIAGE_CERTIFICATE', 'תעודת נישואין', 'identification', False, 'certificate'),
    ('DIVORCE_CERTIFICATE', 'תעודת גירושין', 'identification', False, 'certificate'),
    ('IMMIGRATION_DOCUMENT', 'מסמך הגירה', 'identification', False, 'id'),

    # Financial documents
    ('BANK_STATEMENT', 'דף חשבון בנק', 'financial', True, 'report'),
    ('CREDIT_CARD_STATEMENT', 'דף חשבון כרטיס אשראי', 'financial', True, 'report'),
    ('INVESTMENT_STATEMENT', 'דוח השקעות', 'financial', True, 'report'),
    ('RETIREMENT_ACCOUNT_STATEMENT', 'דוח חשבון פנסיה', 'financial', True, 'report'),
    ('LIFE_INSURANCE_POLICY', 'פוליסת ביטוח חיים', 'financial', False, 'policy'),
    ('HEALTH_INSURANCE_POLICY', 'פוליסת ביטוח בריאות', 'financial', False, 'policy'),
    ('LOAN_STATEMENT', 'דוח הלוואה', 'financial', True, 'loan'),
    ('MORTGAGE_STATEMENT', 'דוח משכנתא', 'financial', True, 'loan'),
    ('ACCOUNT_OWNERSHIP_CONFIRMATION', 'אישור בעלות חשבון', 'financial', False, 'certificate'),
    ('STOCK_CERTIFICATE', 'תעודת מניה', 'financial', False, 'certificate'),
    ('BOND_CERTIFICATE', 'תעודת איגרת חוב', 'financial', False, 'certificate'),
    ('CREDIT_HISTORY_REPORT', 'דוח היסטוריית אשראי', 'financial', False, 'report'),
    ('INSURANCE_CLAIM', 'תביעת ביטוח', 'financial', False, 'other'),

    # Tax documents
    ('INCOME_TAX_RETURN', 'דוח מס הכנסה', 'tax', True, 'tax'),
    ('VAT_RETURN', 'דוח מע״מ', 'tax', True, 'tax'),
    ('TAX_ASSESSMENT', 'הערכת מס', 'tax', False, 'tax'),
    ('TAX_WITHHOLDING_CERTIFICATE', 'אישור ניכוי מס במקור', 'tax', False, 'certificate'),

    # Employment documents
    ('EMPLOYMENT_CONTRACT', 'חוזה העסקה', 'employment', False, 'contract'),
    ('SALARY_SLIP', 'תלוש שכר', 'employment', True, 'report'),
    ('EMPLOYMENT_VERIFICATION', 'אישור העסקה', 'employment', False, 'certificate'),
    ('SEVERANCE_LETTER', 'מכתב פיטורין', 'employment', False, 'other'),

    # Property documents
    ('DEED', 'שטר', 'property', False, 'certificate'),
    ('MORTGAGE_DEED', 'שטר משכנתא', 'property', False, 'certificate'),
    ('PROPERTY_INSURANCE_POLICY', 'פוליסת ביטוח רכוש', 'property', False, 'policy'),
    ('HOMEOWNERS_ASSOCIATION_STATEMENT', 'דוח ועד בית', 'property', True, 'report'),
    ('UTILITY_BILL', 'חשבון שירותים', 'property', True, 'report'),
    ('SECURITY_DEED', 'שטר בטחון', 'property', False, 'certificate'),
    ('HOME_INSPECTION_REPORT', 'דוח בדיקת בית', 'property', False, 'report'),

    # Asset documents
    ('VEHICLE_REGISTRATION', 'רישום רכב', 'asset', False, 'certificate'),
    ('VEHICLE_INSURANCE_POLICY', 'פוליסת ביטוח רכב', 'asset', False, 'policy'),
    ('ART_APPRAISAL', 'הערכת אומנות', 'asset', False, 'report'),
    ('JEWELRY_APPRAISAL', 'הערכת תכשיטים', 'asset', False, 'report'),
    ('VEHICLE_TITLE', 'בעלות רכב', 'asset', False, 'certificate'),

    # Bank account documents
    ('BANK_ACCOUNT_OPENING_DOCUMENTS', 'מסמכי פתיחת חשבון בנק', 'bank_account', False, 'certificate'),
    ('BANK_REFERENCE_LETTER', 'מכתב המלצה מהבנק', 'bank_account', False, 'other'),

    # Company documents
    ('ARTICLES_OF_INCORPORATION', 'תקנון התאגדות', 'company', False, 'certificate'),
    ('BUSINESS_PLAN', 'תוכנית עסקית', 'company', False, 'plan'),
    ('FINANCIAL_STATEMENTS', 'דוחות פיננסיים', 'company', True, 'report'),
    ('BUSINESS_REGISTRATION', 'רישום עסק', 'company', False, 'certificate'),
    ('BUSINESS_FINANCIAL_STATEMENT', 'דוח פיננסי עסקי', 'company', True, 'report'),

    # Credit card documents
    ('CREDIT_CARD_AGREEMENT', 'הסכם כרטיס אשראי', 'credit_card', False, 'contract'),

    # Income documents
    ('INCOME_VERIFICATION', 'אישור הכנסה', 'income', False, 'certificate'),
    ('PENSION_STATEMENT', 'דוח פנסיה', 'income', True, 'report'),
    ('RENTAL_INCOME_STATEMENT', 'דוח הכנסות משכירות', 'income', True, 'report'),
    ('DIVIDEND_STATEMENT', 'דוח דיבידנדים', 'income', True, 'report'),

    # Loan documents
    ('LOAN_AGREEMENT', 'הסכם הלוואה', 'loan', False, 'contract'),
    ('LOAN_PAYMENT_SCHEDULE', 'לוח תשלומי הלוואה', 'loan', False, 'plan'),
    ('LOAN_APPLICATION', 'בקשת הלוואה', 'loan', False, 'other'),
    ('PROMISSORY_NOTE', 'שטר חוב', 'loan', False, 'contract'),

    # Personal documents
    ('MEDICAL_RECORD', 'רשומה רפואית', 'personal', False, 'other'),
    ('MILITARY_SERVICE_RECORD', 'רשומת שירות צבאי', 'personal', False, 'other'),
    ('EDUCATION_CERTIFICATE', 'תעודת השכלה', 'personal', False, 'certificate'),
    ('POWER_OF_ATTORNEY', 'ייפוי כוח', 'personal', False, 'certificate'),
    ('WILL', 'צוואה', 'personal', False, 'certificate'),
    ('TRUST_DOCUMENT', 'מסמך נאמנות', 'personal', False, 'certificate'),
    ('COLLEGE_TRANSCRIPT', 'גיליון ציונים אקדמי', 'personal', False, 'report'),
    ('PRENUPTIAL_AGREEMENT', 'הסכם טרום נישואין', 'personal', False, 'contract'),
    ('CUSTODY_AGREEMENT', 'הסכם משמורת', 'personal', False, 'contract'),
    ('BENEFICIARY_DESIGNATION', 'הגדרת מוטב', 'personal', False, 'certificate')
]


async def create_documents(type_map: Dict[str, UUID], category_map: Dict[str, UUID]) -> List[Tuple[str, str]]:
    """
    Create document records using the type and category mappings
    
    Returns:
        List of (name, category) tuples for created items
    """
    logger.info("Creating documents...")
    created_count = 0
    created_items = []

    # Debug: Log available document types
    logger.info(f"Available document types in type_map: {list(type_map.keys())}")

    for name, description, category, has_multiple_periods, doc_type_value in DOCUMENTS:
        try:
            # Skip if document type doesn't exist
            if doc_type_value not in type_map:
                logger.warning(f"Skipping document {name}: document type {doc_type_value} not found")
                continue

            # Get the document type ID
            document_type_id = type_map[doc_type_value]

            # Get the category ID if it exists
            category_id = category_map.get(category)

            # Create the document using the model
            doc = await create_document(DocumentInCreate(
                name=name,
                description=description,
                document_type_id=document_type_id,
                category=category,
                category_id=category_id,
                has_multiple_periods=has_multiple_periods,
                required_for=[]  # Empty list of requirements
            ))

            created_count += 1
            created_items.append((name, category))
            logger.info(f"Created document: {name}")

        except Exception as e:
            logger.error(f"Error creating document {name}: {str(e)}")

    logger.info(f"Created {created_count}/{len(DOCUMENTS)} documents")
    return created_items


# ------------------------------------------------
# Person Roles Migration
# ------------------------------------------------

# Person roles to create - (name, value)
PERSON_ROLES = [
    ('Primary', 'primary'),
    ('Cosigner', 'cosigner'),
    ('Guarantor', 'guarantor')
]


async def create_person_roles() -> List[Tuple[str, str]]:
    """
    Create person roles
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating person roles...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in PERSON_ROLES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO person_roles (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created person role: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating person role {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(PERSON_ROLES)} person roles")
    return created_items


# ------------------------------------------------
# Loan Types Migration
# ------------------------------------------------

# Loan types to create - (name, value)
LOAN_TYPES = [
    ('משכנתא לבית פרטי', 'single_family_home'),
    ('משכנתא לבניין מגורים', 'multi_family_home'),
    ('משכנתא לקונדומיניום', 'condominium'),
    ('משכנתא לטאונהאוס', 'townhouse'),
    ('הלוואה אישית', 'personal_loan'),
    ('הלוואת רכב', 'auto_loan'),
    ('הלוואה עסקית', 'business_loan'),
    ('הלוואת גישור', 'bridge_loan'),
    ('הלוואת משכנתא הפוכה', 'reverse_mortgage'),
    ('הלוואת בנייה', 'construction_loan'),
    ('הלוואת חינוך', 'education_loan'),
    ('הלוואת מימון מחדש', 'refinance_loan'),
    ('הלוואת איחוד חובות', 'debt_consolidation_loan')
]


async def create_loan_types() -> List[Tuple[str, str]]:
    """
    Create loan types
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating loan types...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in LOAN_TYPES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO loan_types (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created loan type: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating loan type {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(LOAN_TYPES)} loan types")
    return created_items


# ------------------------------------------------
# Loan Goals Migration
# ------------------------------------------------

# Loan goals to create - (name, value)
LOAN_GOALS = [
    ('מגורים עיקריים', 'primary_residence'),
    ('מגורים משניים', 'secondary_residence'),
    ('נכס להשקעה', 'investment_property'),
    ('מימון מחדש', 'refinance'),
    ('שיפוץ בית', 'home_improvement'),
    ('איחוד חובות', 'debt_consolidation'),
    ('הרחבת עסק', 'business_expansion'),
    ('רכישת רכב', 'vehicle_purchase'),
    ('מימון לימודים', 'education_funding'),
    ('הוצאות רפואיות', 'medical_expenses'),
    ('מימון חתונה', 'wedding_expenses'),
    ('יציאה לחופשה', 'vacation_funding'),
    ('הקמת עסק חדש', 'new_business_startup')
]


async def create_loan_goals() -> List[Tuple[str, str]]:
    """
    Create loan goals
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating loan goals...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in LOAN_GOALS:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO loan_goals (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created loan goal: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating loan goal {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(LOAN_GOALS)} loan goals")
    return created_items


# ------------------------------------------------
# Person Marital Statuses Migration
# ------------------------------------------------

# Person marital statuses to create - (name, value)
PERSON_MARITAL_STATUSES = [
    ('רווק/ה', 'single'),
    ('נשוי/אה', 'married'),
    ('גרוש/ה', 'divorced'),
    ('אלמן/ה', 'widowed'),
    ('פרוד/ה', 'separated'),
    ('ידוע/ה בציבור', 'common_law'),
    ('נשוי/אה שנית', 'remarried')
]


async def create_person_marital_statuses() -> List[Tuple[str, str]]:
    """
    Create person marital statuses
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating person marital statuses...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in PERSON_MARITAL_STATUSES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO person_marital_statuses (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created person marital status: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating person marital status {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(PERSON_MARITAL_STATUSES)} person marital statuses")
    return created_items


# ------------------------------------------------
# Employment Types Migration
# ------------------------------------------------

# Employment types to create - (name, value)
EMPLOYMENT_TYPES = [
    ('משרה מלאה', 'full_time'),
    ('משרה חלקית', 'part_time'),
    ('עצמאי', 'self_employed'),
    ('קבלן', 'contractor'),
    ('מובטל', 'unemployed'),
    ('פנסיונר', 'retired'),
    ('סטודנט', 'student'),
    ('חייל/ת', 'military_service'),
    ('חל"ת', 'unpaid_leave'),
    ('עובד/ת זמני/ת', 'temporary_employee'),
    ('עובד/ת לפי שעות', 'hourly_employee'),
    ('פרילנסר', 'freelancer'),
    ('בעל/ת עסק', 'business_owner'),
    ('שכיר ועצמאי', 'employed_and_self_employed')
]


async def create_employment_types() -> List[Tuple[str, str]]:
    """
    Create employment types
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating employment types...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in EMPLOYMENT_TYPES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO employment_types (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created employment type: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating employment type {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(EMPLOYMENT_TYPES)} employment types")
    return created_items


# ------------------------------------------------
# Asset Types Migration
# ------------------------------------------------

# Asset types to create - (name, value)
ASSET_TYPES = [
    ('רכב', 'car'),
    ('נדל"ן', 'real_estate'),
    ('מזומן', 'cash'),
    ('מניות', 'stock'),
    ('תכשיטים', 'jewelry'),
    ('מטבע קריפטוגרפי', 'crypto'),
    ('אמנות', 'art'),
    ('פריטי אספנות', 'collectibles'),
    ('קרנות נאמנות', 'mutual_funds'),
    ('אגרות חוב', 'bonds'),
    ('ביטוח חיים', 'life_insurance'),
    ('זהב וכסף', 'precious_metals'),
    ('חשבונות חיסכון', 'savings_accounts'),
    ('ציוד עסקי', 'business_equipment'),
    ('קרן פנסיה', 'pension_fund')
]


async def create_asset_types() -> List[Tuple[str, str]]:
    """
    Create asset types
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating asset types...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in ASSET_TYPES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO asset_types (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created asset type: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating asset type {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(ASSET_TYPES)} asset types")
    return created_items


# ------------------------------------------------
# Bank Account Types Migration
# ------------------------------------------------

# Bank account types to create - (name, value)
BANK_ACCOUNT_TYPES = [
    ('חשבון עו"ש', 'checking'),
    ('חשבון חיסכון', 'savings'),
    ('פיקדון', 'deposit'),
    ('חשבון משותף', 'joint'),
    ('חשבון עסקי', 'business')
]


async def create_bank_account_types() -> List[Tuple[str, str]]:
    """
    Create bank account types
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating bank account types...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in BANK_ACCOUNT_TYPES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO bank_account_type (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created bank account type: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating bank account type {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(BANK_ACCOUNT_TYPES)} bank account types")
    return created_items


# ------------------------------------------------
# Credit Card Types Migration
# ------------------------------------------------

# Credit card types to create - (name, value)
CREDIT_CARD_TYPES = [
    ('ויזה', 'visa'),
    ('מאסטרקארד', 'mastercard'),
    ('אמריקן אקספרס', 'amex'),
    ('ישראכרט', 'isracard'),
    ('דיינרס', 'diners')
]


async def create_credit_card_types() -> List[Tuple[str, str]]:
    """
    Create credit card types
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating credit card types...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in CREDIT_CARD_TYPES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO credit_card_types (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created credit card type: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating credit card type {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(CREDIT_CARD_TYPES)} credit card types")
    return created_items


# ------------------------------------------------
# Income Sources Types Migration
# ------------------------------------------------

# Income sources types to create - (name, value)
INCOME_SOURCES_TYPES = [
    ('משכורת', 'salary'),
    ('עצמאי', 'self_employed'),
    ('קצבה', 'pension'),
    ('שכירות', 'rental'),
    ('השקעות', 'investments'),
    ('דיבידנדים', 'dividends')
]


async def create_income_sources_types() -> List[Tuple[str, str]]:
    """
    Create income sources types
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating income sources types...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in INCOME_SOURCES_TYPES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO income_sources_types (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created income source type: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating income source type {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(INCOME_SOURCES_TYPES)} income source types")
    return created_items


# ------------------------------------------------
# Related Person Relationships Types Migration
# ------------------------------------------------

# Related person relationships types to create - (name, value)
RELATED_PERSON_RELATIONSHIPS_TYPES = [
    ('בן/בת זוג', 'spouse'),
    ('ילד/ה', 'child'),
    ('הורה', 'parent'),
    ('אח/אחות', 'sibling'),
    ('סבא/סבתא', 'grandparent'),
    ('נכד/ה', 'grandchild'),
    ('קרוב משפחה אחר', 'other_relative'),
    ('ערב', 'guarantor')
]


async def create_related_person_relationships_types() -> List[Tuple[str, str]]:
    """
    Create related person relationships types
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating related person relationships types...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in RELATED_PERSON_RELATIONSHIPS_TYPES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO related_person_relationships_types (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created related person relationship type: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating related person relationship type {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(RELATED_PERSON_RELATIONSHIPS_TYPES)} related person relationship types")
    return created_items


# ------------------------------------------------
# Company Types Migration
# ------------------------------------------------

# Company types to create - (name, value)
COMPANY_TYPES = [
    ('חברה בע"מ', 'ltd'),
    ('שותפות', 'partnership'),
    ('עוסק מורשה', 'self_employed'),
    ('עוסק פטור', 'exempt_dealer'),
    ('עמותה', 'non_profit'),
    ('חברה ציבורית', 'public_company')
]


async def create_company_types() -> List[Tuple[str, str]]:
    """
    Create company types
    
    Returns:
        List of (name, value) tuples for created items
    """
    logger.info("Creating company types...")
    created_count = 0
    created_items = []

    conn = await get_connection()
    try:
        async with conn.transaction():
            for name, value in COMPANY_TYPES:
                try:
                    # Use direct SQL since we don't have model functions for these yet
                    await conn.execute(
                        """INSERT INTO company_types (id, name, value) 
                           VALUES (gen_random_uuid(), $1, $2) 
                           ON CONFLICT (value) DO NOTHING""",
                        name, value
                    )
                    created_count += 1
                    created_items.append((name, value))
                    logger.info(f"Created company type: {name} ({value})")
                except Exception as e:
                    logger.error(f"Error creating company type {name}: {str(e)}")
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(COMPANY_TYPES)} company types")
    return created_items


# ------------------------------------------------
# Financial Organization Types Migration
# ------------------------------------------------

FIN_ORG_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

# Generate meaningful UUIDs using both name and value
FIN_ORG_TYPES_BANK_UID = uuid.uuid5(FIN_ORG_NAMESPACE, 'bank')

FIN_ORG_TYPES = [
    (FIN_ORG_TYPES_BANK_UID, 'בנק', 'bank'),
    (uuid.uuid5(FIN_ORG_NAMESPACE, 'insurance'), 'חברת ביטוח', 'insurance'),
    (uuid.uuid5(FIN_ORG_NAMESPACE, 'pension_fund'), 'קרן פנסיה', 'pension_fund'),
    (uuid.uuid5(FIN_ORG_NAMESPACE, 'provident_fund'), 'קופת גמל', 'provident_fund'),
    (uuid.uuid5(FIN_ORG_NAMESPACE, 'credit_company'), 'חברת אשראי', 'credit_company'),
    (uuid.uuid5(FIN_ORG_NAMESPACE, 'mortgage'), 'משכנתאות', 'mortgage')
]


async def create_fin_org_types() -> int:
    """
    Create financial organization types in the database with UUIDs based on name/value pairs.

    Returns:
        int: Number of successfully created organization types
    """
    logger.info("Creating financial organization types...")
    created_count = 0

    conn = await get_connection()
    try:
        async with conn.transaction():
            for uid, name, value in FIN_ORG_TYPES:
                if not all([uid, name, value]):
                    logger.error(f"Invalid data for {name} ({value})")
                    continue

                try:
                    await conn.execute(
                        """INSERT INTO fin_org_types (id, name, value) 
                           VALUES ($1, $2, $3) 
                           ON CONFLICT (value) DO NOTHING""",
                        uid, name, value
                    )
                    created_count += 1
                    logger.info(f"Created financial organization type: {name} ({value}) with UUID: {uid}")
                except Exception as e:
                    logger.error(f"Error creating financial organization type {name}: {str(e)}")
                    continue
    except Exception as e:
        logger.error(f"Transaction failed: {str(e)}")
        raise
    finally:
        await conn.close()

    logger.info(f"Created {created_count}/{len(FIN_ORG_TYPES)} financial organization types")
    return created_count


# Function to regenerate/verify UUID based on name and value
def generate_fin_org_uuid(name: str, value: str) -> uuid.UUID:
    """Generate a deterministic UUID based on name and value pair"""
    return uuid.uuid5(FIN_ORG_NAMESPACE, name + value)


# ------------------------------------------------
# Main Migration Process
# ------------------------------------------------

def generate_html_report(migration_results: Dict[str, List[Tuple[str, str]]]) -> str:
    """
    Generate an HTML report for all created items
    
    Args:
        migration_results: Dictionary with category names as keys and lists of (name, value) tuples as values
        
    Returns:
        Path to the generated HTML file
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_dir = Path("./reports")
    report_dir.mkdir(exist_ok=True)

    report_path = report_dir / f"seed_data_report_{timestamp}.html"

    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Database Seed Data Report</title>
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
            .timestamp {{
                text-align: center;
                color: #7f8c8d;
                font-style: italic;
                margin-bottom: 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}
            th, td {{
                padding: 12px 15px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            tbody tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .summary {{
                background-color: #e8f4f8;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .category-count {{
                font-weight: bold;
                color: #2980b9;
            }}
        </style>
    </head>
    <body>
        <h1>Database Seed Data Report</h1>
        <div class="timestamp">Generated on {datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</div>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>Total categories: <span class="category-count">{len(migration_results)}</span></p>
            <p>Total items: <span class="category-count">{sum(len(items) for items in migration_results.values())}</span></p>
        </div>
    """

    # Add each category table
    for category, items in migration_results.items():
        if not items:
            continue

        html_content += f"""
        <h2>{category.replace('_', ' ').title()} ({len(items)} items)</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
        """

        for idx, (name, value) in enumerate(items, 1):
            html_content += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{name}</td>
                    <td>{value}</td>
                </tr>
            """

        html_content += """
            </tbody>
        </table>
        """

    # Close HTML
    html_content += """
    </body>
    </html>
    """

    # Write to file
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return str(report_path)


async def run_migrations():
    """
    Run all migrations in the correct order
    """
    logger.info("Starting database migrations...")
    migration_results = {}

    # Reference table migrations
    migration_results["person_roles"] = await create_person_roles()
    migration_results["loan_types"] = await create_loan_types()
    migration_results["loan_goals"] = await create_loan_goals()
    migration_results["person_marital_statuses"] = await create_person_marital_statuses()
    migration_results["employment_types"] = await create_employment_types()
    migration_results["asset_types"] = await create_asset_types()
    migration_results["bank_account_types"] = await create_bank_account_types()
    migration_results["credit_card_types"] = await create_credit_card_types()
    migration_results["income_sources_types"] = await create_income_sources_types()
    migration_results["related_person_relationships_types"] = await create_related_person_relationships_types()
    migration_results["company_types"] = await create_company_types()
    migration_results["financial_organization_types"] = await create_fin_org_types()

    # Document related migrations
    # First, extract all the unique document types used in DOCUMENTS
    used_doc_types = set(doc[4] for doc in DOCUMENTS)  # Extract the doc_type_value (5th item) from each document
    print(f"Document types used in DOCUMENTS: {used_doc_types}")

    # Log the document types that will be created
    defined_types = set(value for _, value in DOCUMENT_TYPES)
    print(f"Document types defined in DOCUMENT_TYPES: {defined_types}")

    # Log any missing document types
    missing_types = used_doc_types - defined_types
    if missing_types:
        print(f"MISSING DOCUMENT TYPES: {missing_types}")

    type_map = await create_document_types()
    category_map = await create_document_categories()
    migration_results["document_types"] = [(name, value) for name, value in DOCUMENT_TYPES]
    migration_results["document_categories"] = [(name, value) for name, value in DOCUMENT_CATEGORIES]
    documents_created = await create_documents(type_map, category_map)
    if documents_created:
        migration_results["documents"] = documents_created

    # Filter out empty results
    filtered_results = {k: v for k, v in migration_results.items() if v}

    # Generate HTML report
    report_path = generate_html_report(filtered_results)
    logger.info(f"HTML report generated at: {report_path}")

    # Open the report in browser
    try:
        os.system(f"open {report_path}")
        logger.info(f"Opened HTML report in browser")
    except Exception as e:
        logger.error(f"Failed to open HTML report: {str(e)}")

    logger.info("Database migrations completed successfully")


# For standalone script execution
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(run_migrations())
