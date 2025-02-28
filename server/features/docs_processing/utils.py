import re
from typing import Optional, List

import pytesseract
from PIL.Image import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from transformers import pipeline

# -------------------------------------------------------------------
# Tesseract check
# -------------------------------------------------------------------
try:
    _ = pytesseract.get_tesseract_version()
except (EnvironmentError, ImportError):
    print("Tesseract not found or not installed properly. OCR will fail if needed.")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using PyPDF2."""
    try:
        reader = PdfReader(pdf_path)
        pages_text = []
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            pages_text.append(text)
            # pages_text.append(f"\n-------------------- {page_num} --------------------\n")
        return "".join(pages_text)
    except Exception as e:
        print("Error extracting text from PDF '%s': %s".format(pdf_path, e))
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def is_containing_hebrew_letters(text: str) -> bool:
    """
    Returns True if the input text contains any Hebrew letters.

    Hebrew letters are in the Unicode range U+0590 to U+05FF.
    """
    # Define a regex pattern for Hebrew letters
    pattern = re.compile(r'[\u0590-\u05FF]')
    return bool(pattern.search(text))


def convert_pdf_to_images(pdf_path: str, dpi: int = 200, max_pages: Optional[int] = None) -> List[Image]:
    """Convert a PDF to a list of PIL Image objects."""
    try:
        pages = convert_from_path(pdf_path, dpi=dpi)
        if max_pages is not None:
            pages = pages[:max_pages]
        return pages
    except Exception as e:
        print(f"Error converting PDF to images for {pdf_path}")
        raise Exception(f"Failed to convert PDF to images: {str(e)}")


def normalize_name(name: str, lang: str) -> str:
    # Normalize whitespace and remove diacritics if necessary
    name = " ".join(name.split())

    # Example: Remove common prefixes
    if lang == "arabic":
        # Remove the Arabic definite article "ال" if it's attached to a word
        name = re.sub(r'\bال', '', name)
    elif lang == "hebrew":
        # For Hebrew, you might want to handle prefixes like "בן" or "בת" specially
        name = re.sub(r'\b(בן|בת)\s+', '', name)

    return name


def extract_first_last(fullname: str, lang: str = "hebrew") -> tuple:
    # Normalize the full name first
    normalized_fullname = normalize_name(fullname, lang)

    model_name = "Davlan/distilbert-base-multilingual-cased-ner-hrl"
    ner = pipeline(
        "ner",
        model=model_name,
        aggregation_strategy="simple",
        device="mps",
    )

    # Get entities from the input fullname
    entities = ner(normalized_fullname)

    # Filter the entities to keep only person entities
    person_entities = [entity for entity in entities if entity.get("entity_group") == "PER"]

    # Fallback if the model is not confident or doesn't return two distinct entities.
    if len(person_entities) >= 2:
        # In some cases, you might want to join adjacent tokens if they represent a compound name.
        first_name = person_entities[0]["word"]
        last_name = person_entities[-1]["word"]
    else:
        # Fallback: split the fullname by whitespace.
        parts = normalized_fullname.split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = parts[-1]
        else:
            first_name = normalized_fullname
            last_name = ""

    # Additional rule: if last name appears to be a patronymic marker or very short, re-adjust.
    if lang == "arabic" and len(last_name) <= 2:
        parts = normalized_fullname.split()
        if len(parts) > 1:
            last_name = parts[-1]

    return (first_name, last_name)


data_he = [
    "דוד כהן",
    "בנימין אשר פלדמן",
    "צביה אלישבע לוי",
    "רפאל לוין",
    "שלמה דניאל וינברג",
    "משה עידו גליקמן",
    "שלומית ברקוביץ",
    "איריס נעמי גרין",
    "יעל גולדשטיין",
    "אורן מנשה חזון-צוקרמן",
    "מאירה שולמית גוטמן",
    "נעם עמיר רובין",
    "מרים תמר בלומנטל",
    "אבי זיו גרינברג",
    "שמואל יעקב לנדאו",
    "ורד שלומית הורוביץ",
    "שרה אברהמי",
    "יוסף דניאל בן-דוד",
    "טלי יוכבד חן",
    "צחי בן ארי",
    "חיים אליעזר רוזנפלד",
    "רחל ברכה וינברג",
    "נחום יאיר לוי",
    "נעמי בת שבע פרידמן",
    "עודד שלו כהן",
    "גלית דבורה רוזן",
    "יעקב אהרן שטרן",
    "דנה דבורה גל",
    "עופר זאב רבינוביץ",
    "אלינה שושנה וייס",
    "אבישי אורי כהן",
    "נועה ברק שמעוני",
    "אודי מיכאל קסלר",
    "מירה שולמית ברקוביץ",
    "רובי אברהם מלמד",
    "חגית אילנה דרור",
    "עדי דליה שולמן",
    "ישראל חיים רוזן",
    "שי צור לוי",
    "קרן עפרי גולדברג",
    "דורון טל רוזנברג",
    "דניאל יוסף קפלן",
    "אריאל מנחם בן נון",
    "איילת שני שגב",
    "אלחנן הלל שינדלר",
    "אלה גיטלר",
    "דני תומר כהן",
    "רונה דקלה גורדון",
    "שאול גור ארי",
    "אביגיל שולמית כהן-פרידמן"

]
data_arabic = [
    "אחמד מוחמד עלי",
    "עאישה מוסתפא מג'די",
    "עבדאללה חסן ג'מאל",
    "זיינב מוראד חוסיין",
    "חאלד עבד אלרחמן אלעלי",
    "פאטימה חאלד אלראשדי",
    "מריאם עלי אלשמרי",
    "ספאא ראשיד אלהאשם",
    "נור סולימאן חלף-אלרפעי",
    "אמג'ד רדוואן אחמד",
    "לימאע עבדאללה יאסר",
    "מהא איימן אלטאאי",
    "ג'ומאנה סמיר ח'ליל",
    "איברהים סאמי יוסף",
    "סאלם מוחמד סרחאן",
    "בילאל עאדיל אלתוויל",
    "סארה עומר איברהים",
    "חסן רזא ג'אבר",
    "חוסיין מוחמד אקרם",
    "עאדיל נור אלדין אלדלימאי-אלתמימי",
    "מייסון חאלד סעד",
    "רשד חמד אלסעיד",
    "אימאן פוזי ג'מאל",
    "פארח וליד חמד",
    "סלווא איחסאן עבד אלחאי",
    "בשאר מג'די עבד אלג'פור",
    "עז אלדין מוחמד עבדאללה",
    "נור אלדין עאמר חוסיין",
    "פאטימה עבד אלעזיז עמאד",
    "חמזה סלים חאלד",
    "הנד סאלם סאלח",
    "סעיד אקרם אלרפעי",
    "אסמאע ג'אנם אלראשד",
    "נוואל סאמיה עבד אלעאל",
    "רים סארה אבו סעוד",
    "עדנאן עבד אללטיף אלאנצארי",
    "רגד מוראם אלזההירי",
    "מסתורה שאהר אלמטירי",
    "דימה עלי אלחארתי",
    "זיין פייסל בן עלי",
    "נאיף סעוד אלראשיד",
    "עבד אלמלכ עלי איברהים",
    "נצר אלדין רזא מוסתפא",
    "ג'אבר מוסא אלהאשם",
    "אמירה עליוו חמאדי",
    "נורה עבד אלקאדר אלסאלם",
    "לאיף קאסם חליף",
    "שיימא ג'מאל אלשחאבי",
    "אליאסין הית'ם חאלד",
    "מוהנד וסאם אלזאידי"
]
# for x in data_he:
#     print(f'{x} - {extract_first_last(x, 'hebrew')}')
# for x in data_arabic:
#     print(f'{x} - {extract_first_last(x, 'hebrew')}')
