import re

_MULTIPLE_BLANK_LINES_PATTERN = re.compile(r"\n{2,}")
_MULTIPLE_SPACES_PATTERN = re.compile(r"[ \t]+")
_PAGE_NUMBER_PATTERN = re.compile(
    r"(?im)^page\s+\d+\s*$"
)
_NEWLINE_WHITESPACE_PATTERN = re.compile(
    r"[ \t]*\n[ \t]*"
)


class TextCleaner:
    """
    Cleans raw text extracted from PDFs.
    """

    def clean(
        self,
        text: str,
    ) -> str:
        """
        Clean extracted PDF text.
        """

        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r", "\n")

        # Remove multiple blank lines
        text = _MULTIPLE_BLANK_LINES_PATTERN.sub(
            "\n",
            text,
        )

        # Replace multiple spaces/tabs with a single space
        text = _MULTIPLE_SPACES_PATTERN.sub(
            " ",
            text,
        )

        # Remove page numbers like:
        # Page 1
        # Page 12
        text = _PAGE_NUMBER_PATTERN.sub(
            "",
            text,
        )

        # Trim whitespace around line breaks
        text = _NEWLINE_WHITESPACE_PATTERN.sub(
            "\n",
            text,
        )

        return text.strip()