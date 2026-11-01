"""Text cleaning service for CampusPilot AI.

Provides deterministic, conservative text cleaning for extracted PDF documents
prior to chunking. Preserves headings, code indentation, mathematical symbols,
and paragraph structure while removing artifact noise from PDF extraction.
"""

import re
from functools import lru_cache


class TextCleaner:
    """Conservative text cleaning utility for document processing."""

    def __init__(self) -> None:
        # Regex to match hyphenated words broken across a line break: e.g. "connec-\ntion" -> "connection"
        self._hyphen_linebreak_pattern = re.compile(r"(\b[a-zA-Z]{2,})-\n[ \t]*([a-zA-Z]{2,}\b)")
        # Regex to match 3 or more consecutive newlines
        self._excess_newlines_pattern = re.compile(r"\n{3,}")
        # Regex to match horizontal whitespace (spaces, tabs, non-breaking spaces) that repeat more than once,
        # but only on lines that are not code blocks (handled carefully)
        self._non_breaking_space_pattern = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]")

    def clean_text(self, text: str) -> str:
        """Clean raw extracted document text conservatively.

        Rules applied:
        1. Handle empty / whitespace-only text safely.
        2. Normalize non-breaking and unusual unicode spaces to standard spaces.
        3. De-hyphenate words broken across line wraps (e.g. 'struc-\\nture' -> 'structure').
        4. Normalize horizontal whitespace per line (trim trailing spaces on each line).
        5. Collapse 3+ consecutive newlines to 2 to preserve paragraph and section boundaries.
        6. Strip overall leading/trailing whitespace.
        7. Maintain all mathematical symbols, punctuation, and code formatting.
        """
        if not text or not text.strip():
            return ""

        # Step 1: Replace non-standard unicode whitespace with standard space
        cleaned = self._non_breaking_space_pattern.sub(" ", text)

        # Step 2: Fix hyphenated word breaks from PDF column/page line wraps
        # e.g., "algo-\nrithm" -> "algorithm"
        cleaned = self._hyphen_linebreak_pattern.sub(r"\1\2", cleaned)

        # Step 3: Process line by line to strip trailing whitespace while preserving indentation for code
        lines = cleaned.split("\n")
        cleaned_lines = []
        for line in lines:
            # Strip trailing whitespace on each line
            rstripped = line.rstrip()
            cleaned_lines.append(rstripped)

        cleaned = "\n".join(cleaned_lines)

        # Step 4: Collapse 3 or more consecutive newlines into 2 (one empty line between blocks)
        cleaned = self._excess_newlines_pattern.sub("\n\n", cleaned)

        # Step 5: Strip surrounding leading/trailing whitespace
        return cleaned.strip()


@lru_cache()
def get_text_cleaner() -> TextCleaner:
    """Return cached singleton instance of TextCleaner."""
    return TextCleaner()
