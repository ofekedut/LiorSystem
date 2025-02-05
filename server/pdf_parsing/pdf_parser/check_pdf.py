import os
from PyPDF2 import PdfReader


def check_pdf_text(directory: str) -> dict[str, bool]:
    """
    Scan a directory for PDFs and check which ones have selectable text.

    Args:
        directory (str): Path to directory containing PDF files

    Returns:
        Dict[str, bool]: Dictionary with PDF filenames as keys and boolean indicating if they have text
    """
    results = {}

    # Get all PDF files in directory
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]

    for pdf_file in pdf_files:
        full_path = os.path.join(directory, pdf_file)
        try:
            # Open PDF and check first page for text
            reader = PdfReader(full_path)
            first_page = reader.pages[0]
            text = first_page.extract_text()

            # If we can extract any text (excluding whitespace), mark as having text
            has_text = bool(text.strip())
            results[pdf_file] = has_text

        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
            results[pdf_file] = False

    return results
