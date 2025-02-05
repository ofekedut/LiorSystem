import asyncio
import json
import os
import io
import traceback
from typing import Optional, Dict, Any

import ollama
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

prompt_instructions = (
    '''
    אתה מומחה לסיווג מסמכים בעל יכולת קריאה וניתוח חזותי וטקסטואלי (למשל, קבצי PDF, תמונות וטקסט). כאשר תינתן לך תמונה, קובץ PDF או טקסט, עליך לנתח את המאפיינים החזותיים והטקסטואליים של המסמך ולסווג אותו לאחת מהקטגוריות הבאות:
    
    1. דנא - פעולות מנהליות  
    2. דנא - עוש  
    3. כרטיס ת.ז חדש  
    4. רשיון נהיגה  
    5. דוח דירוג (בידיאי/דיאנבי)  
    6. תעודת גמר  
    7. בידיאי - תמצית נתונים (רגיל/בוצעה מחיקת נתונים)  
    8. דנא - פניות לקבלת מידע / מידע מגופים ציבוריים  
    9. דנא - כללי  
    10. אישור זכויות (חברה משכנת / רמי)  
    11. תסריט בית  
    12. גרמושקה  
    13. ספח ת.ז  
    14. תעודת עוסק (עוסק מורשה)  
    15. בידיאי - מידע מגופים ציבוריים (חשבון מוגבל / הוצלפים)  
    16. נסח טאבו  
    17. חוזה מכר (הסכם מכר)  
    18. רשיון רכב  
    19. פרוטוקול מורשה חתימה  
    20. נסח חברה  
    21. דרכון (כולל דרכונים של בני הזוג)  
    22. בידיאי - ריכוז עסקות  
    23. בידיאי - ניתוח מגמות  
    24. חוזה חכירה  
    25. דנא - הלוואות + כרטיסי אשראי  
    26. שמאות  
    27. דוח נתוני אשראי  
    28. היתר בניה  
    29. כרטיס ת.ז ישן  
    30. תעודת התאגדות  
    31. טופס ארנונה  
    
    המטרה שלך היא לבחור את הקטגוריה המתאימה ביותר למסמך על בסיס ניתוח המאפיינים (כותרות, מילות מפתח, עיצוב, תוכן וכדומה). במקרה של חוסר ודאות, ציין את המאפיינים העיקריים שזיהית אשר מובילים לבחירה זו.
    
    ענה רק עם שם הקטגוריה ונמק בקצרה את הסיבות לסיווג זה.
    '''
)


def try_read_pdf(pdf_path: str) -> Optional[str]:
    try:
        if not pdf_path.endswith('.pdf'):
            return ''
        pages_text = ''
        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            pages_text += text
            pages_text += f'\n -------------------- {page_num} -------------------- \n'
        return pages_text
    except Exception as e:
        print(e)
        traceback.print_exc()
        return None


class OllamaVisionClassifier:
    """
    A wrapper class for using a local, vision-capable Llama model via Ollama.
    """

    def __init__(self, model_name: str = "llava"):
        self.model_name = model_name

    async def classify_document(
            self,
            file_path: Optional[str] = None,
            text: Optional[str] = None,
            dpi: int = 200,
            max_pages: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Classify a document that can be a PDF, an image, or plain text.
        If a file path is provided, the function checks whether it is a PDF or an image,
        processes it accordingly, and combines any extracted text with the provided `text`.

        :param file_path: Optional file path (PDF or image) to classify.
        :param text: Optional plain text to include.
        :param dpi: Resolution used for converting PDF pages to images (if applicable).
        :param max_pages: Maximum number of pages to process for PDFs.
        :return: Dictionary containing the classification result (and page count if applicable).
        """
        images = []
        final_text = text if text is not None else ""
        page_count = 0

        if file_path is not None:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found at: {file_path}")

            if file_path.lower().endswith('.pdf'):
                # Extract text from PDF and combine with any provided text.
                pdf_text = try_read_pdf(file_path) or ""
                if pdf_text:
                    final_text = pdf_text if final_text == "" else final_text + "\n" + pdf_text

                # Convert PDF pages to images.
                pages = convert_from_path(file_path, dpi=dpi)
                if max_pages is not None:
                    pages = pages[:max_pages]
                page_count = len(pages)
                for page in pages:
                    img_buffer = io.BytesIO()
                    page.save(img_buffer, format="PNG")
                    images.append(img_buffer.getvalue())
            else:
                # Assume the file is an image.
                with open(file_path, "rb") as f:
                    image_bytes = f.read()
                images.append(image_bytes)
                page_count = 1

        messages = [
            {"role": "system", "content": prompt_instructions},
        ]
        user_msg = {}
        if final_text:
            user_msg["content"] = final_text
        if images:
            user_msg["images"] = images
        messages.append({"role": "user", **user_msg})

        # Send the request to the model.
        response = ollama.chat(
            model=self.model_name,
            messages=messages
        )

        # Prepare and return the final result.
        result = {
            "classification": response.get("message", {}).get("content", "").strip(),
            "page_count": page_count
        }
        return result


async def main():
    classifier = OllamaVisionClassifier(model_name="minicpm-v")
    for f in os.listdir('/Users/ofekedut/development/otech/projects/lior_arbivv/test_extraction_service/monday_assets'):
        try:
            pdf_result = await classifier.classify_document(file_path=f'/Users/ofekedut/development/otech/projects/lior_arbivv/test_extraction_service/monday_assets/{f}',
                                                            max_pages=2)
            print("PDF Result:")
            print(json.dumps(pdf_result, indent=4, ensure_ascii=False))
        except FileNotFoundError:
            print(f"File {f} not found.")


if __name__ == "__main__":
    asyncio.run(main())
