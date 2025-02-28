import os
from PyPDF2 import PdfReader
from pdf_parsing.pdf_parser.check_pdf import check_pdf_text
from pdf_parsing.pdf_parser.pdf_ocr import PDFProcessor
from pdf_parsing.pdf_parser.pdf_result import (
    PDFPageResult,
    Content,
    TextBlock,
    ProcessingInfo
)
from typing import List


def process_single_pdf(pdf_path: str) -> List[PDFPageResult]:
    """
    Process a single PDF file, using either direct extraction or OCR based on PDF type

    Args:
        pdf_path (str): Path to PDF file

    Returns:
        List[PDFPageResult]: List of typed results for each page
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        directory = os.path.dirname(pdf_path)
        filename = os.path.basename(pdf_path)

        # Check if PDF has searchable text
        has_text = check_pdf_text(directory).get(filename, False)

        results: List[PDFPageResult] = []

        if has_text:
            # Process searchable PDF
            reader = PdfReader(pdf_path)

            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()

                # Create typed objects for direct extraction
                text_block = TextBlock(
                    text=text,
                    confidence=100.0,
                    block_num=1,
                    position=None
                )

                content = Content(
                    text_blocks=[text_block],
                    page_dimensions=None
                )

                processing_info = ProcessingInfo(
                    method='direct_extraction',
                    searchable=True
                )

                result = PDFPageResult(
                    filename=filename,
                    page_number=page_num,
                    content=content,
                    processing_info=processing_info
                )

                results.append(result)
        else:
            # Process with OCR
            ocr_processor = PDFProcessor()
            ocr_results = ocr_processor.process_pdf(pdf_path)
            results.extend(ocr_results)  # OCR processor now returns PDFPageResult objects

        return results

    except Exception as e:
        # Create typed error result
        error_content = Content(text_blocks=[])
        error_processing_info = ProcessingInfo(
            method='failed',
            searchable=False,
            error_type=type(e).__name__
        )

        error_result = PDFPageResult(
            filename=os.path.basename(pdf_path),
            page_number=0,
            content=error_content,
            processing_info=error_processing_info,
            error=str(e)
        )

        return [error_result]


if __name__ == "__main__":
    pdf_path = input("Enter PDF path: ")
    results = process_single_pdf(pdf_path)

    # Print summary using typed objects
    if results[0].error:
        print(f"Error processing PDF: {results[0].error}")
    else:
        print(f"Successfully processed {len(results)} pages")
        print(f"Method: {results[0].processing_info.method}")

        # Example of accessing structured data
        first_page = results[0]
        print("\nFirst page details:")
        print(f"Filename: {first_page.filename}")
        print(f"Page number: {first_page.page_number}")
        print(f"Number of text blocks: {len(first_page.content.text_blocks)}")
        if first_page.content.text_blocks:
            first_block = first_page.content.text_blocks[0]
            print(f"First block text: {first_block.text[:100]}...")  # Show first 100 chars
            print(f"First block confidence: {first_block.confidence}")