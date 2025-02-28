import asyncio
from datetime import datetime
from uuid import UUID

from database.cases_database import (
    CaseInCreate,
    CaseStatus,
    CaseDocumentCreate,
    CaseDocumentUpdate,
    DocumentStatus,
    DocumentProcessingStatus,
    create_case,
    create_case_document,
    update_case_document  # <-- we need this for updating file path
)
from database.documents_databse import (
    DocumentInCreate,
    DocumentType,
    DocumentCategory,
    RequiredFor,
    create_document
)


def get_docs_dataset() -> dict[str, DocumentInCreate]:
    """
    Returns a dictionary of 55 DocumentInCreate instances,
    keyed by their internal string identifiers (e.g. 'DNA_ADMINISTRATIVE').

    No loops or iteration are used; this is a fully expanded, static dataset.
    """
    return {
        "DNA_ADMINISTRATIVE": DocumentInCreate(
            name="DNA_מינהלי",
            description="Doc code=1, InternalKey=DNA_ADMINISTRATIVE",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "DNA_OSH": DocumentInCreate(
            name="DNA_בטיחות",
            description="Doc code=2, InternalKey=DNA_OSH",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "NEW_ID_CARD": DocumentInCreate(
            name="תעודת זהות חדשה",
            description="Doc code=3, InternalKey=NEW_ID_CARD",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "DRIVERS_LICENSE": DocumentInCreate(
            name="רישיון נהיגה",
            description="Doc code=4, InternalKey=DRIVERS_LICENSE",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "RATING_REPORT": DocumentInCreate(
            name="דו\"ח דירוג",
            description="Doc code=5, InternalKey=RATING_REPORT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "COMPLETION_CERTIFICATE": DocumentInCreate(
            name="תעודת השלמה",
            description="Doc code=6, InternalKey=COMPLETION_CERTIFICATE",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BDI_DATA_SUMMARY": DocumentInCreate(
            name="BDI_סיכום נתונים",
            description="Doc code=7, InternalKey=BDI_DATA_SUMMARY",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "DNA_INFORMATION_REQUESTS": DocumentInCreate(
            name="DNA_בקשות מידע",
            description="Doc code=8, InternalKey=DNA_INFORMATION_REQUESTS",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "DNA_GENERAL": DocumentInCreate(
            name="DNA_כללי",
            description="Doc code=9, InternalKey=DNA_GENERAL",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "RIGHTS_CONFIRMATION": DocumentInCreate(
            name="אישור זכויות",
            description="Doc code=10, InternalKey=RIGHTS_CONFIRMATION",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "HOUSE_SCRIPT": DocumentInCreate(
            name="תסריט בית",
            description="Doc code=11, InternalKey=HOUSE_SCRIPT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BUILDING_PLAN": DocumentInCreate(
            name="תוכנית בניין",
            description="Doc code=12, InternalKey=BUILDING_PLAN",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "ID_APPENDIX": DocumentInCreate(
            name="נספח תעודת זהות",
            description="Doc code=13, InternalKey=ID_APPENDIX",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BUSINESS_LICENSE": DocumentInCreate(
            name="רישיון עסק",
            description="Doc code=14, InternalKey=BUSINESS_LICENSE",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BDI_PUBLIC_ENTITIES": DocumentInCreate(
            name="BDI_גופים ציבוריים",
            description="Doc code=15, InternalKey=BDI_PUBLIC_ENTITIES",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "PROPERTY_EXTRACT": DocumentInCreate(
            name="תעודת מקרקעין",
            description="Doc code=16, InternalKey=PROPERTY_EXTRACT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "SALES_CONTRACT": DocumentInCreate(
            name="חוזה מכר",
            description="Doc code=17, InternalKey=SALES_CONTRACT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "VEHICLE_LICENSE": DocumentInCreate(
            name="רישיון רכב",
            description="Doc code=18, InternalKey=VEHICLE_LICENSE",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "SIGNATURE_PROTOCOL": DocumentInCreate(
            name="פרוטוקול חתימה",
            description="Doc code=19, InternalKey=SIGNATURE_PROTOCOL",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "COMPANY_EXTRACT": DocumentInCreate(
            name="תקציר חברה",
            description="Doc code=20, InternalKey=COMPANY_EXTRACT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "PASSPORT": DocumentInCreate(
            name="דרכון",
            description="Doc code=21, InternalKey=PASSPORT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BDI_TRANSACTION_SUMMARY": DocumentInCreate(
            name="BDI_סיכום עסקאות",
            description="Doc code=22, InternalKey=BDI_TRANSACTION_SUMMARY",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BDI_TREND_ANALYSIS": DocumentInCreate(
            name="BDI_ניתוח מגמות",
            description="Doc code=23, InternalKey=BDI_TREND_ANALYSIS",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "LEASE_CONTRACT": DocumentInCreate(
            name="חוזה שכירות",
            description="Doc code=24, InternalKey=LEASE_CONTRACT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "DNA_LOANS": DocumentInCreate(
            name="DNA הלוואות",
            description="Doc code=25, InternalKey=DNA_LOANS",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "APPRAISAL": DocumentInCreate(
            name="שמאות",
            description="Doc code=26, InternalKey=APPRAISAL",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "CREDIT_REPORT": DocumentInCreate(
            name="דו\"ח אשראי",
            description="Doc code=27, InternalKey=CREDIT_REPORT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BUILDING_PERMIT": DocumentInCreate(
            name="יתר בניה",
            description="Doc code=28, InternalKey=BUILDING_PERMIT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "OLD_ID_CARD": DocumentInCreate(
            name="תעודת זהות ישנה",
            description="Doc code=29, InternalKey=OLD_ID_CARD",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "CERTIFICATE_OF_INCORPORATION": DocumentInCreate(
            name="תעודת התאגדות",
            description="Doc code=30, InternalKey=CERTIFICATE_OF_INCORPORATION",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "PROPERTY_TAX": DocumentInCreate(
            name="ארנונה",
            description="Doc code=31, InternalKey=PROPERTY_TAX",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "MORTGAGE_APPROVAL": DocumentInCreate(
            name="אישור משכנתא",
            description="Doc code=32, InternalKey=MORTGAGE_APPROVAL",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "DEAL_SUMMARY": DocumentInCreate(
            name="סיכום עסקה",
            description="Doc code=33, InternalKey=DEAL_SUMMARY",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "PAYSLIP": DocumentInCreate(
            name="תלוש שכר",
            description="Doc code=34, InternalKey=PAYSLIP",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "LIFE_INSURANCE_POLICY": DocumentInCreate(
            name="פוליסת ביטוח חיים",
            description="Doc code=35, InternalKey=LIFE_INSURANCE_POLICY",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BUILDING_INSURANCE_POLICY": DocumentInCreate(
            name="פוליסת ביטוח מבנה",
            description="Doc code=36, InternalKey=BUILDING_INSURANCE_POLICY",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "INTEREST_IMPROVEMENT_REQ": DocumentInCreate(
            name="בקשת שיפור ריבית",
            description="Doc code=37, InternalKey=INTEREST_IMPROVEMENT_REQ",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "DIRECT_FINANCE": DocumentInCreate(
            name="מימון ישיר",
            description="Doc code=38, InternalKey=DIRECT_FINANCE",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "CLIENT_MEETING": DocumentInCreate(
            name="פגישת לקוח",
            description="Doc code=39, InternalKey=CLIENT_MEETING",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "CLIENT_INTERPRETATION": DocumentInCreate(
            name="פרשנות לקוח",
            description="Doc code=40, InternalKey=CLIENT_INTERPRETATION",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "PROFIT_LOSS_REPORT": DocumentInCreate(
            name="דו\"ח רווח והפסד",
            description="Doc code=41, InternalKey=PROFIT_LOSS_REPORT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BANK_TRANSACTIONS": DocumentInCreate(
            name="פעולות בנק",
            description="Doc code=42, InternalKey=BANK_TRANSACTIONS",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "REFERRAL_TO_APPRAISAL": DocumentInCreate(
            name="הפניה לשמאות",
            description="Doc code=43, InternalKey=REFERRAL_TO_APPRAISAL",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "ACCOUNT_MANAGEMENT_APPROVAL": DocumentInCreate(
            name="אישור ניהול חשבון",
            description="Doc code=44, InternalKey=ACCOUNT_MANAGEMENT_APPROVAL",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "LEGAL_CONTRACT": DocumentInCreate(
            name="חוזה משפטי",
            description="Doc code=46, InternalKey=LEGAL_CONTRACT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "EMPLOYMENT_CONTRACT": DocumentInCreate(
            name="חוזה עבודה",
            description="Doc code=47, InternalKey=EMPLOYMENT_CONTRACT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "INVOICE": DocumentInCreate(
            name="חשבונית",
            description="Doc code=48, InternalKey=INVOICE",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "RECEIPT": DocumentInCreate(
            name="קבלה",
            description="Doc code=49, InternalKey=RECEIPT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "TAX_DOCUMENT": DocumentInCreate(
            name="מסמך מס",
            description="Doc code=50, InternalKey=TAX_DOCUMENT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "BANK_STATEMENT": DocumentInCreate(
            name="דו\"ח בנקאי",
            description="Doc code=51, InternalKey=BANK_STATEMENT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "FINANCIAL_STATEMENT": DocumentInCreate(
            name="דו\"ח כספי",
            description="Doc code=52, InternalKey=FINANCIAL_STATEMENT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "LEGAL_DOCUMENT": DocumentInCreate(
            name="מסמך משפטי",
            description="Doc code=53, InternalKey=LEGAL_DOCUMENT",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "CERTIFICATE_OF_QUALITY": DocumentInCreate(
            name="תעודת איכות",
            description="Doc code=54, InternalKey=CERTIFICATE_OF_QUALITY",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
        "LOAN": DocumentInCreate(
            name="הלוואה",
            description="Doc code=55, InternalKey=LOAN",
            document_type=DocumentType.one_time,
            category=DocumentCategory.financial,
            period_type=None,
            periods_required=None,
            has_multiple_periods=False,
            required_for=[RequiredFor.all],
        ),
    }


async def main():
    doc1 = DocumentInCreate(
        name="דנא בידיאי",
        description=(
            "Document from path: "
            "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/"
            "docs_processing/monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/"
            "subitems/1720652971_דנא__בידיאי/pdf.ecb0f2c3"
        ),
        document_type=DocumentType.one_time,
        category=DocumentCategory.financial,
        has_multiple_periods=False,
        required_for=[RequiredFor.all]
    )

    doc2 = DocumentInCreate(
        name="אישור זכויות ניירת אחרונה",
        description=(
            "Document from path: "
            "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/"
            "docs_processing/monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/"
            "subitems/1720652973_אישור_זכויות_ניירת_אחרונה/4c2d33b3-1ed6-4a2b-82f7-de915f8fb2ebpdf_00e72932"
        ),
        document_type=DocumentType.recurring,
        category=DocumentCategory.property,
        has_multiple_periods=True,
        periods_required=12,
        required_for=[RequiredFor.business_owners]
    )

    doc3 = DocumentInCreate(
        name="תעודת זהות + ספח",
        description=(
            "Document from path: "
            "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/"
            "docs_processing/monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/"
            "subitems/1720652992_תז_של_כל_הקשורים/תעודת_זהות___ספח35jpeg_a5046f77"
        ),
        document_type=DocumentType.updatable,
        category=DocumentCategory.identification,
        has_multiple_periods=False,
        required_for=[RequiredFor.all]
    )

    doc4 = DocumentInCreate(
        name="פענוח לקוח",
        description=(
            "Document from path: "
            "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/"
            "docs_processing/monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/"
            "subitems/1720652995_פענוח_לקוח/CamScanner_10-15-2024_190547pdf_ea86c0e3"
        ),
        document_type=DocumentType.one_time,
        category=DocumentCategory.financial,
        has_multiple_periods=False,
        required_for=[RequiredFor.self_employed]
    )

    # Create a case to attach documents to
    case_in = CaseInCreate(
        name="First Time Home Loan",
        status=CaseStatus.active,
        case_purpose="Mortgage application",
        loan_type="Residential Mortgage",
        last_active=datetime.utcnow(),
    )
    case_id: UUID = await create_case(case_in)

    # Document definitions and their file paths
    documents = [doc1, doc2, doc3, doc4]
    paths = [
        "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/"
        "monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/"
        "subitems/1720652971_דנא__בידיאי/pdf.ecb0f2c3",

        "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/"
        "monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/"
        "subitems/1720652973_אישור_זכויות_ניירת_אחרונה/4c2d33b3-1ed6-4a2b-82f7-de915f8fb2ebpdf_00e72932",

        "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/"
        "monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/"
        "subitems/1720652992_תז_של_כל_הקשורים/תעודת_זהות___ספח35jpeg_a5046f77",

        "/Users/ofekedut/development/otech/projects/lior_arbivv/server/features/docs_processing/"
        "monday_assets_bar/1720649847_הכנת_תיק_לקוח/1720649922_סאמר_אלקרינאוי/"
        "subitems/1720652995_פענוח_לקוח/CamScanner_10-15-2024_190547pdf_ea86c0e3",
    ]

    case_documents = []

    for doc_in_create, file_path in zip(documents, paths):
        # 1) Insert each DocumentInCreate into DB => returns a DocumentInDB
        created_doc_in_db = await create_document(doc_in_create)
        document_id = created_doc_in_db.id

        # 2) Create a row in case_documents WITHOUT setting file_path:
        new_link = await create_case_document(
            CaseDocumentCreate(
                case_id=case_id,
                document_id=document_id,
                status=DocumentStatus.pending,
                processing_status=DocumentProcessingStatus.pending,
                uploaded_at=datetime.utcnow(),
                uploaded_by=None  # or any real user UUID
            )
        )

        # 3) Now read or handle the file if needed.
        #    For demonstration, we just open it and read it:
        with open(file_path, "rb") as f:
            file_content = f.read()
            # Possibly upload to S3 or some other storage. For now, just a placeholder.

        # 4) **Use CaseDocumentUpdate** to set the file_path
        updated_link = await update_case_document(
            case_id,
            document_id,
            CaseDocumentUpdate(file_path=file_path)
        )
        case_documents.append(updated_link)

    print("Case and documents created & updated successfully!")
    for cd in case_documents:
        print(f"- Document {cd.document_id} → file_path={cd.file_path}")


if __name__ == "__main__":
    asyncio.run(main())
