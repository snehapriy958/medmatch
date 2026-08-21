import logging
from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

import fitz
from fastapi import UploadFile

from app.config.settings import settings

logger = logging.getLogger(__name__)


class PDFService:
    """
    Handles PDF storage and text extraction.
    """

    def __init__(self) -> None:
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_pdf(
        self,
        file: UploadFile,
    ) -> Path:
        """
        Save the uploaded PDF and return its path.
        """

        filename = f"{uuid4()}.pdf"
        destination = self.upload_dir / filename

        with destination.open("wb") as buffer:
            copyfileobj(file.file, buffer)

        return destination

    def extract_text(
        self,
        pdf_path: Path,
    ) -> str:
        """
        Extract raw text from every page of the PDF.

        Raises:
            ValueError: If the PDF is invalid or contains no extractable text.
        """

        try:
            with fitz.open(pdf_path) as document:
                pages = [
                    page.get_text()
                    for page in document
                ]

        except Exception as exc:
            logger.exception(
                "Failed to open PDF: %s",
                pdf_path,
            )

            raise ValueError(
                "Invalid PDF file."
            ) from exc

        text = "\n".join(pages).strip()

        if not text:
            logger.warning(
                "PDF contains no extractable text: %s",
                pdf_path,
            )

            raise ValueError(
                "PDF contains no extractable text."
            )

        return text