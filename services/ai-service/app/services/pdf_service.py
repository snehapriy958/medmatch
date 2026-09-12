import logging
from pathlib import Path
from uuid import uuid4

import pymupdf
from fastapi import UploadFile

from app.config.settings import settings


logger = logging.getLogger(__name__)


class PDFService:
    """
    Handles secure PDF storage and text extraction.
    """

    CHUNK_SIZE = 1024 * 1024
    PDF_SIGNATURE = b"%PDF-"

    def __init__(self) -> None:
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save_pdf(
        self,
        file: UploadFile,
    ) -> Path:
        """
        Save an uploaded PDF safely.

        Validates:
        - File extension
        - PDF signature
        - Maximum file size
        - Non-empty content
        - PDF readability

        Returns:
            Path to the saved PDF.

        Raises:
            ValueError: If the uploaded file is invalid.
        """

        original_filename = file.filename or ""

        if not original_filename.lower().endswith(
            ".pdf"
        ):
            raise ValueError(
                "Only PDF files are allowed."
            )

        max_size_bytes = (
            settings.MAX_UPLOAD_SIZE_MB
            * 1024
            * 1024
        )

        filename = f"{uuid4()}.pdf"

        destination = (
            self.upload_dir
            / filename
        )

        total_size = 0

        try:
            first_chunk = file.file.read(
                self.CHUNK_SIZE
            )

            if not first_chunk:
                raise ValueError(
                    "Uploaded PDF file is empty."
                )

            if not first_chunk.startswith(
                self.PDF_SIGNATURE
            ):
                raise ValueError(
                    "Uploaded file is not a valid PDF."
                )

            total_size += len(
                first_chunk
            )

            if total_size > max_size_bytes:
                raise ValueError(
                    f"File exceeds the maximum allowed "
                    f"size of "
                    f"{settings.MAX_UPLOAD_SIZE_MB} MB."
                )

            with destination.open(
                "wb"
            ) as buffer:

                buffer.write(
                    first_chunk
                )

                while True:

                    chunk = file.file.read(
                        self.CHUNK_SIZE
                    )

                    if not chunk:
                        break

                    total_size += len(
                        chunk
                    )

                    if total_size > max_size_bytes:
                        raise ValueError(
                            f"File exceeds the maximum allowed "
                            f"size of "
                            f"{settings.MAX_UPLOAD_SIZE_MB} MB."
                        )

                    buffer.write(
                        chunk
                    )

            self._validate_pdf(
                destination
            )

            logger.info(
                "Saved PDF '%s' successfully.",
                destination.name,
            )

            return destination

        except ValueError:

            self._delete_file(
                destination
            )

            raise

        except Exception as exc:

            self._delete_file(
                destination
            )

            logger.exception(
                "Failed to save uploaded PDF '%s'.",
                original_filename,
            )

            raise ValueError(
                "Failed to save uploaded PDF."
            ) from exc

    def extract_text(
        self,
        pdf_path: str | Path
    ) -> str:
        """
        Extract raw text from every page of the PDF.

        Raises:
            ValueError: If the PDF is invalid or contains
            no extractable text.
        """

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise ValueError(
                "PDF file does not exist."
            )

        if not pdf_path.is_file():
            raise ValueError(
                "PDF path is invalid."
            )

        try:
            with pymupdf.open(
                pdf_path
            ) as document:

                if document.page_count == 0:
                    raise ValueError(
                        "PDF contains no pages."
                    )

                pages = [
                    page.get_text()
                    for page in document
                ]

        except ValueError:
            raise

        except Exception as exc:

            logger.exception(
                "Failed to extract text from PDF: %s",
                pdf_path,
            )

            raise ValueError(
                "Invalid or unreadable PDF file."
            ) from exc

        text = "\n".join(
            pages
        ).strip()

        if not text:

            logger.warning(
                "PDF contains no extractable text: %s",
                pdf_path,
            )

            raise ValueError(
                "PDF contains no extractable text."
            )

        return text
    @staticmethod
    def _validate_pdf(
        pdf_path: str | Path,
    ) -> None:
        """
        Verify that the saved file is a readable PDF.
        """

        try:
            with pymupdf.open(
                pdf_path
            ) as document:

                if document.page_count == 0:
                    raise ValueError(
                        "PDF contains no pages."
                    )

        except ValueError:
            raise

        except Exception as exc:

            logger.warning(
                "Uploaded file is not a valid PDF: %s",
                pdf_path,
            )

            raise ValueError(
                "Uploaded file is not a valid PDF."
            ) from exc

    @staticmethod
    def _delete_file(
        file_path: Path,
    ) -> None:
        """
        Delete a file if it exists.

        Used to clean up failed or invalid uploads.
        """

        try:

            if file_path.exists():
                file_path.unlink()

        except Exception:

            logger.exception(
                "Failed to delete file during cleanup: %s",
                file_path,
            )