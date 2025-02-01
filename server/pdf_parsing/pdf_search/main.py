from server.pdf_parsing.pdf_search.pdf_search import Query, SearchInPdf

# Example usage
if __name__ == "__main__":
    # Create some example queries
    queries = {
        'email': Query(
            pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            name='Email Address',
            description='Find email addresses'
        ),
        'phone': Query(
            pattern=r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            name='Phone Number',
            description='Find phone numbers'
        ),
        'date': Query(
            pattern=r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            name='Date',
            description='Find dates in MM/DD/YYYY format'
        )
    }

    # Example with file path
    pdf_path = "example.pdf"
    searcher = SearchInPdf(pdf_path)
    results = searcher.search(queries)

    # Print results
    if results.error:
        print(f"Error: {results.error}")
    else:
        print(f"Results for {results.filename}:")
        for result in results.results:
            print(f"\nQuery: {result.query_name}")
            print(f"Page {result.page_number} (confidence: {result.confidence:.2f})")
            print("Matches:", result.matches)