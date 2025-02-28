from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Pattern
import re
from pathlib import Path
import io
from PyPDF2 import PdfReader

from pdf_parsing.pdf_parser.main import process_single_pdf
from pdf_parsing.pdf_parser.pdf_result import PDFPageResult, TextBlock, Content, ProcessingInfo


@dataclass
class Query:
    """Query configuration for searching in PDF"""
    pattern: str  # regex pattern
    flags: int = re.IGNORECASE  # default flags for regex
    name: str = ""  # identifier for this query
    description: Optional[str] = None

    def __post_init__(self):
        # Compile the regex pattern
        self._compiled_pattern: Pattern = re.compile(self.pattern, self.flags)

    def search(self, text: str) -> List[str]:
        """
        Search text using the query pattern

        Args:
            text: Text to search in

        Returns:
            List of matched strings
        """
        return [match.group(0) for match in self._compiled_pattern.finditer(text)]


@dataclass
class SearchResult:
    """Result of a single query search"""
    query_name: str
    matches: List[str]
    page_number: int
    confidence: float  # OCR confidence if applicable


@dataclass
class DocumentSearchResult:
    """Complete search results for a document"""
    filename: str
    results: List[SearchResult]
    processing_info: dict
    error: Optional[str] = None


class SearchInPdf:
    """Class for searching text in PDFs using regex patterns"""

    def __init__(self, source: Union[str, Path, bytes, io.BytesIO]):
        """
        Initialize PDF searcher

        Args:
            source: PDF source - can be path (str/Path), bytes, or BytesIO
        """
        self.source = source
        self._processed_results: Optional[List[PDFPageResult]] = None

    def _process_pdf(self) -> List[PDFPageResult]:
        """Process PDF and get text content"""
        if isinstance(self.source, (str, Path)):
            # Process from file path
            return process_single_pdf(str(self.source))
        elif isinstance(self.source, (bytes, io.BytesIO)):
            # Create temporary file-like object
            if isinstance(self.source, bytes):
                pdf_file = io.BytesIO(self.source)
            else:
                pdf_file = self.source

            # Read PDF directly
            reader = PdfReader(pdf_file)
            results = []

            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():  # Only process non-empty pages
                    result = self._create_page_result(text, page_num, 'direct_extraction')
                    results.append(result)

            return results
        else:
            raise ValueError(f"Unsupported source type: {type(self.source)}")

    def _create_page_result(self, text: str, page_num: int, method: str) -> PDFPageResult:
        """Create a PDFPageResult object from extracted text"""

        text_block = TextBlock(
            text=text,
            confidence=100.0,
            block_num=1,
            position=None
        )

        content = Content(
            text_blocks=[text_block]
        )

        processing_info = ProcessingInfo(
            method=method,
            searchable=True
        )

        return PDFPageResult(
            filename=str(self.source) if isinstance(self.source, (str, Path)) else "memory",
            page_number=page_num,
            content=content,
            processing_info=processing_info
        )

    def search(self, queries: Dict[str, Query]) -> DocumentSearchResult:
        """
        Search PDF using provided queries

        Args:
            queries: Dictionary of query name to Query object

        Returns:
            DocumentSearchResult containing all matches
        """
        try:
            if not self._processed_results:
                self._processed_results = self._process_pdf()

            search_results: List[SearchResult] = []

            for page_result in self._processed_results:
                # Combine all text blocks into one string for searching
                page_text = " ".join(block.text for block in page_result.content.text_blocks)

                # Get confidence score (average of all blocks)
                confidence = sum(block.confidence for block in page_result.content.text_blocks) / len(page_result.content.text_blocks)

                # Search with each query
                for query_name, query in queries.items():
                    matches = query.search(page_text)
                    if matches:
                        search_results.append(
                            SearchResult(
                                query_name=query_name,
                                matches=matches,
                                page_number=page_result.page_number,
                                confidence=confidence
                            )
                        )

            return DocumentSearchResult(
                filename=self._processed_results[0].filename,
                results=search_results,
                processing_info={
                    'method': self._processed_results[0].processing_info.method,
                    'searchable': self._processed_results[0].processing_info.searchable,
                    'total_pages': len(self._processed_results)
                }
            )

        except Exception as e:
            return DocumentSearchResult(
                filename=str(self.source) if isinstance(self.source, (str, Path)) else "memory",
                results=[],
                processing_info={'method': 'failed'},
                error=str(e)
            )
