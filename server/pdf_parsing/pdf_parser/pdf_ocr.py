import os
from typing import List
from pdf2image import convert_from_path
import pytesseract
import fitz
from server.pdf_parsing.pdf_parser.pdf_result import PDFPageResult, Content, TextBlock, Position, PageDimensions, ProcessingInfo


class PDFProcessor:
    def __init__(self, lang='eng'):
        self.lang = lang

    def extract_metadata(self, pdf_path: str) -> dict:
        """Extract PDF metadata using PyMuPDF"""
        doc = fitz.open(pdf_path)
        metadata = {
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'subject': doc.metadata.get('subject', ''),
            'keywords': doc.metadata.get('keywords', ''),
            'creator': doc.metadata.get('creator', ''),
            'producer': doc.metadata.get('producer', ''),
            'creation_date': doc.metadata.get('creationDate', ''),
            'modification_date': doc.metadata.get('modDate', ''),
            'page_count': len(doc),
            'file_size': os.path.getsize(pdf_path)
        }
        doc.close()
        return metadata

    def process_pdf(self, pdf_path: str) -> List[PDFPageResult]:
        """
        Process PDF and return list of PDFPageResult objects

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            List[PDFPageResult]: List of processed page results with typed data
        """
        try:
            # Extract metadata
            metadata = self.extract_metadata(pdf_path)
            filename = os.path.basename(pdf_path)

            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)

            results = []

            # Process each page
            for page_num, image in enumerate(images, 1):
                # Perform OCR
                ocr_result = pytesseract.image_to_data(
                    image,
                    lang=self.lang,
                    output_type=pytesseract.Output.DICT
                )

                # Create text blocks
                text_blocks = []
                for i in range(len(ocr_result['text'])):
                    if float(ocr_result['conf'][i]) > 30 and ocr_result['text'][i].strip():
                        # Create Position object
                        position = Position(
                            x=ocr_result['left'][i],
                            y=ocr_result['top'][i],
                            width=ocr_result['width'][i],
                            height=ocr_result['height'][i]
                        )

                        # Create TextBlock object
                        text_block = TextBlock(
                            text=ocr_result['text'][i],
                            confidence=float(ocr_result['conf'][i]),
                            block_num=ocr_result['block_num'][i],
                            line_num=ocr_result['line_num'][i],
                            position=position
                        )
                        text_blocks.append(text_block)

                # Create page dimensions
                page_dimensions = PageDimensions(
                    width=image.width,
                    height=image.height
                )

                # Create content object
                content = Content(
                    text_blocks=text_blocks,
                    page_dimensions=page_dimensions
                )

                # Create processing info
                processing_info = ProcessingInfo(
                    method='ocr',
                    searchable=False,
                    lang=self.lang,
                    ocr_engine='Tesseract'
                )

                # Create page result
                page_result = PDFPageResult(
                    filename=filename,
                    page_number=page_num,
                    content=content,
                    processing_info=processing_info,
                    metadata=metadata
                )

                results.append(page_result)

            return results

        except Exception as e:
            # Return error result
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


def main():
    processor = PDFProcessor()
    pdf_path = input("Enter PDF path: ")

    if not os.path.exists(pdf_path):
        print("File not found!")
        return

    print("Processing PDF...")
    results = processor.process_pdf(pdf_path)

    # Print sample of results using typed objects
    print(f"\nProcessed {len(results)} pages")
    print("\nSample structure of first page:")
    first_page = results[0]

    if first_page.error:
        print(f"Error: {first_page.error}")
    else:
        print(f"Page number: {first_page.page_number}")
        print(f"Document title: {first_page.metadata['title']}")
        print(f"Number of text blocks: {len(first_page.content.text_blocks)}")
        if first_page.content.text_blocks:
            first_block = first_page.content.text_blocks[0]
            print(f"First block text: {first_block.text}")
            print(f"First block confidence: {first_block.confidence}")

    return results


if __name__ == "__main__":
    main()
