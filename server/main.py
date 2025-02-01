import os
from pathlib import Path
from typing import Dict, List

from server.pdf_parsing.pdf_parser.main import process_single_pdf
from server.pdf_parsing.pdf_parser.pdf_result import PDFPageResult
from server.pdf_parsing.pdf_search.pdf_search import SearchInPdf, Query
from server.pdf_parsing.pdf_tables.parse_pdf_tablrs import PdfTables, ExtractedTable


class PDFProcessor:
    """Main class for processing PDFs"""

    def __init__(self, pdf_path: str):
        """
        Initialize PDF processor

        Args:
            pdf_path: Path to PDF file
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.pdf_path = pdf_path
        self.filename = Path(pdf_path).name

        # Initialize components
        self.searcher = SearchInPdf(pdf_path)
        self.table_extractor = PdfTables(pdf_path)

        # Store results
        self.text_results: List[PDFPageResult] = []
        self.table_results: List[ExtractedTable] = []
        self.search_results: Dict = {}

    def process_all(self, queries: Dict[str, Query] = None) -> Dict:
        """
        Process PDF through all available methods

        Args:
            queries: Optional dictionary of search queries

        Returns:
            Dictionary containing all processing results
        """
        try:
            # 1. Extract text
            print(f"Processing text from {self.filename}...")
            self.text_results = process_single_pdf(self.pdf_path)

            # 2. Extract tables
            print("Extracting tables...")
            self.table_results = self.table_extractor.extract_tables()

            # 3. Perform searches if queries provided
            if queries:
                print("Performing searches...")
                self.search_results = self.searcher.search(queries)

            # Compile results
            return self._compile_results()

        except Exception as e:
            return {
                'error': str(e),
                'filename': self.filename,
                'status': 'failed'
            }

    def _compile_results(self) -> Dict:
        """Compile all results into a single dictionary"""

        # Process text results
        text_data = []
        for page in self.text_results:
            if not page.error:
                text_data.append({
                    'page_number': page.page_number,
                    'text': [block.text for block in page.content.text_blocks],
                    'confidence': sum(block.confidence for block in page.content.text_blocks) / len(page.content.text_blocks),
                    'method': page.processing_info.method
                })

        # Process table results
        table_data = []
        for table in self.table_results:
            if not table.error:
                table_data.append({
                    'page': table.location.page,
                    'table_number': table.location.table_number,
                    'headers': table.headers,
                    'rows': len(table.data),
                    'columns': len(table.headers),
                    'data': table.data.to_dict('records'),
                    'accuracy': table.location.accuracy
                })

        # Compile final results
        results = {
            'filename': self.filename,
            'status': 'success',
            'metadata': self.text_results[0].metadata if self.text_results and self.text_results[0].metadata else {},
            'pages': {
                'total': max(page.page_number for page in self.text_results) if self.text_results else 0,
                'processed': len(self.text_results)
            },
            'text_extraction': {
                'method': self.text_results[0].processing_info.method if self.text_results else None,
                'pages': text_data
            },
            'tables': {
                'count': len(table_data),
                'data': table_data
            }
        }

        # Add search results if available
        if self.search_results and not isinstance(self.search_results, dict):
            results['searches'] = {
                'total_matches': len(self.search_results.results),
                'results': [
                    {
                        'query': result.query_name,
                        'matches': result.matches,
                        'page': result.page_number,
                        'confidence': result.confidence
                    }
                    for result in self.search_results.results
                    if hasattr(result, 'matches') and result.matches  # Only include results with matches
                ]
            }

        return results


def main():
    # Example queries for demonstration
    sample_queries = {
        'email': Query(
            pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            name='Email Address'
        ),
        'date': Query(
            pattern=r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            name='Date'
        )
    }

    # Get PDF path
    pdf_path = "Enter path to PDF file: "

    try:
        # Initialize and process
        processor = PDFProcessor(pdf_path)
        results = processor.process_all(queries=sample_queries)

        # Print results summary
        if 'error' in results:
            print(f"\nError processing PDF: {results['error']}")
            return

        print("\nProcessing Summary:")
        print("-" * 50)
        print(f"Filename: {results['filename']}")
        print(f"Total pages: {results['pages']['total']}")
        print(f"Text extraction method: {results['text_extraction']['method']}")
        print(f"Tables found: {results['tables']['count']}")

        if 'searches' in results:
            print(f"Total search matches: {results['searches']['total_matches']}")

        print("\nText Content:")
        for page in results['text_extraction']['pages']:
            print(f"\nPage {page['page_number']}:")
            print('\n'.join(page['text']))

        print("\nTable Data:")
        for table in results['tables']['data']:
            print(f"\nTable on page {table['page']}:")
            print(f"Headers: {table['headers']}")
            print(f"Rows: {table['rows']}")
            print("First few rows:", table['data'][:3])

        if 'searches' in results:
            print("\nSearch Results:")
            for match in results['searches']['results']:
                print(f"\nQuery: {match['query']}")
                print(f"Page {match['page']}: {match['matches']}")

        print("\nMetadata:")
        for key, value in results['metadata'].items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()