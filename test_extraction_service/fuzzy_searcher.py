import re
from rapidfuzz import fuzz
from rapidfuzz import process


class FuzzySearch:
    """
    A class that encapsulates:
      - A keyword to search for
      - A list of regex patterns
      - OCR-extracted text to search within
      - A list of possible target values for fuzzy matching
    """

    def __init__(
            self,
            keyword: str,
            regex_patterns: list[str],
            text: str,
            values: list[str],
            threshold: int = 75
    ):
        """
        :param keyword: The primary term you want to search for.
        :param regex_patterns: A list of regular expressions to apply on text.
        :param text: The OCR-extracted text to search.
        :param values: A list of strings to compare to the keyword via fuzzy matching.
        :param threshold: A score threshold above which we consider a match valid.
        """
        self.keyword = keyword
        self.regex_patterns = regex_patterns
        self.original_text = text
        self.values = values
        self.threshold = threshold

        # Preprocess the OCR text
        self.text = self._preprocess_text(text)

    def _preprocess_text(self, text: str) -> str:
        """
        Clean and normalize OCR text to improve matching.
        You might tailor this for your OCR system.
        """
        # Basic cleanup: lowercasing, trimming, replacing extra spaces, etc.
        cleaned = text.lower()
        cleaned = cleaned.strip()
        cleaned = re.sub(r"\s+", " ", cleaned)  # Replace multiple spaces/newlines with single space

        # Optional: handle common OCR misreads, for example:
        # cleaned = cleaned.replace("0", "o")  # if your OCR frequently misreads O/0
        # (Add your own domain-specific rules as needed.)

        return cleaned

    def _apply_regex(self, text: str) -> list[str]:
        """
        Apply each regex pattern to the text, return a list of matched segments.
        """
        matched_segments = []
        for pattern in self.regex_patterns:
            # Compile regex pattern for performance if you’ll run it multiple times
            regex = re.compile(pattern, flags=re.IGNORECASE)
            matches = regex.findall(text)
            matched_segments.extend(matches)
        return matched_segments

    def _calculate_similarity(self, source: str, target: str) -> int:
        """
        Calculate a similarity score (0-100) between two strings using RapidFuzz's ratio.
        """
        return fuzz.ratio(source, target)

    def fuzzy_match(self) -> list[dict]:
        """
        Performs fuzzy matching of `self.keyword` against the known `self.values`.
        Returns a list of dictionaries with match info.
        """
        # RapidFuzz's process.extract can also do a bulk match. For example:
        # matches = process.extract(self.keyword, self.values, scorer=fuzz.ratio, limit=None)
        # Alternatively, do it manually here for demonstration:
        results = []
        for val in self.values:
            score = self._calculate_similarity(self.keyword, val)
            if score >= self.threshold:
                results.append({"value": val, "score": score})
        return results

    def search(self) -> dict:
        """
        Orchestrates:
          - Regex matching in the text (if relevant)
          - Fuzzy matching of the keyword in the set of values
          - Returns a structured dictionary of results
        """
        # 1) Apply regex patterns to find candidate segments in text
        regex_matches = self._apply_regex(self.text)

        # 2) Fuzzy match the self.keyword against the self.values
        fuzzy_results = self.fuzzy_match()

        # 3) Optionally, you can also do fuzzy matching for each regex match found in OCR text
        #    if you want to see which matches are closest to your known set of values, etc.
        #    This step is optional and depends on your use case:
        #
        # matched_segments = []
        # for segment in regex_matches:
        #     match_score = self._calculate_similarity(segment, self.keyword)
        #     if match_score >= self.threshold:
        #         matched_segments.append({"segment": segment, "score": match_score})

        return {
            "keyword": self.keyword,
            "regex_matches": regex_matches,
            "fuzzy_results": fuzzy_results
            # "matched_segments": matched_segments,  # If you implemented segment matching
        }


# Usage Example
if __name__ == "__main__":
    # Suppose we have some OCR-extracted text
    ocr_text = """
    Here is some sample text with Invoice number: INV12345
    and also Bill No. 67890 somewhere in the text.
    We want to detect the word 'invoice' and some possible values like 'invoice 12345'.
    """

    # Instantiate the class
    fs = FuzzySearch(
        keyword="invoice",
        regex_patterns=[r"invoice\s*\w+", r"bill\s*no\.\s*\d+"],
        text=ocr_text,
        values=["invoice 12345", "invoice 67890", "bill no. 67890"],
        threshold=70
    )

    # Run the search
    results = fs.search()
    print("Results:", results)
