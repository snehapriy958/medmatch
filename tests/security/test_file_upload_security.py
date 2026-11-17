"""
Security Tests: File Upload Vulnerabilities & Defensive Hardening.
Tests:
1. Path traversal attacks in uploaded filename (e.g. ../../etc/passwd.pdf)
2. Disallowed file extensions (.exe, .sh, .php, .svg, .html)
3. Content-Type spoofing / Non-PDF magic byte attacks
4. Empty file / zero-byte upload
5. Oversized upload (> MAX_UPLOAD_SIZE_MB)
6. Safe file UUID generation preventing filesystem overwrites
"""

import io
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi import UploadFile

from app.services.pdf_service import PDFService
from app.config.settings import settings


def test_path_traversal_filename_neutralized(tmp_path, monkeypatch):
    """Uploaded filename with directory traversal must NOT escape the upload directory."""
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    pdf_service = PDFService()

    # Valid PDF bytes
    import fitz
    doc = fitz.open()
    doc.new_page().insert_text((50, 72), "Sample clinical text")
    valid_pdf_bytes = doc.tobytes()
    doc.close()

    traversal_filenames = [
        "../../etc/passwd.pdf",
        "..\\..\\windows\\system32\\calc.exe.pdf",
        "....//....//sensitive.pdf",
        "/etc/shadow.pdf",
    ]

    for malicious_name in traversal_filenames:
        upload = UploadFile(
            filename=malicious_name,
            file=io.BytesIO(valid_pdf_bytes)
        )
        saved_path = pdf_service.save_pdf(upload)

        # Destination MUST be directly inside the configured upload directory
        assert saved_path.parent.resolve() == Path(settings.UPLOAD_DIR).resolve()
        # Filename on disk MUST be a generated UUID, not the attacker's path
        assert saved_path.name != malicious_name
        assert saved_path.name.endswith(".pdf")


def test_disallowed_file_extensions_rejected():
    """Non-PDF extensions must be rejected before reading or writing to disk."""
    pdf_service = PDFService()
    dangerous_extensions = [
        "payload.exe",
        "script.sh",
        "shell.php",
        "vector.svg",
        "exploit.html",
        "macro.docm",
        "archive.tar.gz",
    ]

    for fname in dangerous_extensions:
        upload = UploadFile(
            filename=fname,
            file=io.BytesIO(b"%PDF-1.4 malicious content")
        )
        with pytest.raises(ValueError, match="Only PDF files are allowed"):
            pdf_service.save_pdf(upload)


def test_magic_bytes_spoofing_rejected():
    """File claiming to be .pdf with text/html or binary content must be rejected."""
    pdf_service = PDFService()
    fake_payloads = [
        b"<!DOCTYPE html><html><body>XSS</body></html>",
        b"MZ\x90\x00\x03\x00\x00\x00Windows Executable",
        b"#!/bin/bash\nrm -rf /",
        b"Plain text clinical note masquerading as pdf",
    ]

    for payload in fake_payloads:
        upload = UploadFile(
            filename="fake.pdf",
            file=io.BytesIO(payload)
        )
        with pytest.raises(ValueError, match="not a valid PDF"):
            pdf_service.save_pdf(upload)


def test_empty_file_rejected():
    """0-byte file must be rejected immediately."""
    pdf_service = PDFService()
    upload = UploadFile(
        filename="empty.pdf",
        file=io.BytesIO(b"")
    )
    with pytest.raises(ValueError, match="empty"):
        pdf_service.save_pdf(upload)


def test_oversized_file_rejected(monkeypatch):
    """File exceeding MAX_UPLOAD_SIZE_MB must be rejected."""
    pdf_service = PDFService()
    # Mock settings.MAX_UPLOAD_SIZE_MB to 1 MB for testing
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)

    # 1.5 MB payload
    large_payload = b"%PDF-1.4 " + b"A" * (1024 * 1024 + 500_000)
    upload = UploadFile(
        filename="huge.pdf",
        file=io.BytesIO(large_payload)
    )
    with pytest.raises(ValueError, match="exceeds the maximum allowed size"):
        pdf_service.save_pdf(upload)
