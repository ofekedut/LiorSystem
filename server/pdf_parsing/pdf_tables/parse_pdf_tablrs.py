from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
import io
import tempfile
import os
import pandas as pd
import camelot


@dataclass
class TableLocation:
    """Location of a table in the PDF"""
    page: int
    area: Optional[tuple[float, float, float, float]] = None  # (top, left, bottom, right)
    table_number: int = 0
    accuracy: float = 0.0
    whitespace: float = 0.0


@dataclass
class ExtractedTable:
    """Represents an extracted table from PDF"""
    data: pd.DataFrame
    location: TableLocation
    headers: List[str]
    error: Optional[str] = None


class PdfTables:
    """Extract tables from PDF documents using Camelot"""

    def __init__(self, source: Union[str, Path, bytes, io.BytesIO]):
        """
        Initialize PDF table extractor

        Args:
            source: PDF source - can be path (str/Path), bytes, or BytesIO
        """
        self.source = source
        self._temp_path: Optional[str] = None

        # Initialize the source
        if isinstance(source, (str, Path)):
            self.pdf_path = str(source)
        else:
            # Create temporary file for bytes/BytesIO
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                if isinstance(source, bytes):
                    tmp.write(source)
                else:
                    tmp.write(source.read())
                self._temp_path = tmp.name
            self.pdf_path = self._temp_path

    def __del__(self):
        """Cleanup temporary files"""
        if self._temp_path and os.path.exists(self._temp_path):
            os.unlink(self._temp_path)

    def extract_tables(self,
                       pages: Optional[Union[str, List[int]]] = None,
                       flavor: str = 'lattice',
                       table_areas: Optional[List[tuple[float, float, float, float]]] = None
                       ) -> List[ExtractedTable]:
        """
        Extract tables from PDF using Camelot

        Args:
            pages: Page numbers to extract from (string like '1,3-5' or list of integers)
            flavor: Table extraction flavor ('lattice' or 'stream')
            table_areas: List of table boundary areas (top, left, bottom, right) in PDF coordinate space

        Returns:
            List of ExtractedTable objects
        """
        try:
            # Convert pages list to string if needed
            if isinstance(pages, list):
                pages = ','.join(map(str, pages))

            # Prepare extraction options
            options = {
                'pages': pages or 'all',
                'flavor': flavor
            }

            if table_areas:
                options['table_areas'] = table_areas

            # Extract tables
            tables = camelot.read_pdf(self.pdf_path, **options)

            results = []
            for idx, table in enumerate(tables):
                location = TableLocation(
                    page=table.page,
                    table_number=idx + 1,
                    accuracy=table.accuracy,
                    whitespace=table.whitespace
                )

                # Convert to pandas DataFrame and get headers
                df = table.df
                headers = list(df.columns)

                # Create ExtractedTable object
                extracted = ExtractedTable(
                    data=df,
                    location=location,
                    headers=headers
                )

                results.append(extracted)

            return results

        except Exception as e:
            return [ExtractedTable(
                data=pd.DataFrame(),
                location=TableLocation(page=0),
                headers=[],
                error=str(e)
            )]

    def table_to_dict(self, table: ExtractedTable) -> Dict[str, Any]:
        """Convert ExtractedTable to dictionary format"""
        return {
            'data': table.data.to_dict('records'),
            'location': {
                'page': table.location.page,
                'area': table.location.area,
                'table_number': table.location.table_number,
                'accuracy': table.location.accuracy,
                'whitespace': table.location.whitespace
            },
            'headers': table.headers,
            'error': table.error
        }


# Example usage
if __name__ == "__main__":
    pdf_path = "example.pdf"
    extractor = PdfTables(pdf_path)

    # Extract tables using lattice mode
    print("Extracting tables (lattice mode)...")
    lattice_tables = extractor.extract_tables(flavor='lattice')

    # Extract tables using stream mode
    print("\nExtracting tables (stream mode)...")
    stream_tables = extractor.extract_tables(flavor='stream')


    # Print results
    def print_tables(tables, mode):
        print(f"\n{mode.upper()} MODE RESULTS:")
        print("-" * 50)

        for table in tables:
            if table.error:
                print(f"Error: {table.error}")
                continue

            print(f"\nTable {table.location.table_number} on page {table.location.page}")
            print(f"Accuracy: {table.location.accuracy:.2f}")
            print(f"Whitespace: {table.location.whitespace:.2f}")
            print(f"Headers: {table.headers}")
            print("\nFirst few rows:")
            print(table.data.head())
            print("-" * 50)


    print_tables(lattice_tables, "Lattice")
    print_tables(stream_tables, "Stream")