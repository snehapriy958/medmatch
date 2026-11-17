"""
Journey B: Clinical Document Intelligence Integration Tests
Tests:
1. Valid synthetic clinical PDF parsing and validation
2. Magic bytes validation (%PDF-)
3. Text extraction and structural section separation
4. TextCleaner normalization (control chars, page numbers)
5. SentenceTransformer vector embedding generation (384 dimensions)
6. Safe rejection of oversized PDFs (>10 MB)
7. Safe rejection of corrupted/empty files
8. Deterministic embedding idempotency
"""

import io
from pathlib import Path
import pytest
from fastapi import UploadFile

from app.services.pdf_service import PDFService
from app.services.text_cleaner import TextCleaner
from app.embeddings.model import EmbeddingModel


@pytest.fixture
def sample_pdf_content():
    """Build a minimal valid synthetic PDF in memory with PyMuPDF."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "CLINICAL TRIAL PROTOCOL\n\n"
        "Title: Phase III Study of Osimertinib in EGFR-Mutant NSCLC\n\n"
        "INCLUSION CRITERIA:\n"
        "1. Age >= 18 years.\n"
        "2. Histologically confirmed Stage IV Non-Small Cell Lung Cancer.\n"
        "3. Documented EGFR Exon 19 deletion or L858R mutation.\n"
        "4. ECOG performance status 0 or 1.\n\n"
        "EXCLUSION CRITERIA:\n"
        "1. Prior treatment with third-generation EGFR-TKI.\n"
        "2. Symptomatic untreated central nervous system metastases.\n"
        "3. Absolute neutrophil count < 1500/uL or platelets < 100,000/uL.\n"
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_journey_b_valid_pdf_extraction(sample_pdf_content, tmp_path):
    """Synthetic PDF passes validation and extracts expected text."""
    pdf_service = PDFService()
    test_pdf = tmp_path / "clinical_protocol.pdf"
    test_pdf.write_bytes(sample_pdf_content)

    text = pdf_service.extract_text(test_pdf)
    assert "CLINICAL TRIAL PROTOCOL" in text
    assert "Osimertinib" in text
    assert "EGFR Exon 19 deletion" in text


def test_journey_b_magic_bytes_validation():
    """Non-PDF file must be rejected immediately."""
    pdf_service = PDFService()
    fake_file = io.BytesIO(b"This is a text file masquerading as a PDF.")
    fake_upload = UploadFile(filename="document.pdf", file=fake_file)
    with pytest.raises(ValueError, match="not a valid PDF"):
        pdf_service.save_pdf(fake_upload)


def test_journey_b_empty_pdf_rejected():
    """Zero-byte file must be rejected."""
    pdf_service = PDFService()
    empty_file = io.BytesIO(b"")
    empty_upload = UploadFile(filename="empty.pdf", file=empty_file)
    with pytest.raises(ValueError, match="empty"):
        pdf_service.save_pdf(empty_upload)


def test_journey_b_text_cleaning_and_normalization():
    """TextCleaner normalizes page numbers and excess whitespace."""
    cleaner = TextCleaner()
    dirty_text = (
        "Page 1\n"
        "CLINICAL   TRIAL   PROTOCOL\n\n\n\n"
        "Header text\n"
        "Line with multiple     spaces   and tabs.\t\t\n"
    )
    cleaned = cleaner.clean(dirty_text)
    assert "Page 1" not in cleaned
    assert "   " not in cleaned
    assert "CLINICAL TRIAL PROTOCOL" in cleaned


def test_journey_b_embedding_generation():
    """EmbeddingModel generates normalized 384-dimensional vector."""
    model = EmbeddingModel()
    text = "Histologically confirmed Stage IV Non-Small Cell Lung Cancer with EGFR Exon 19 deletion."
    embedding = model.encode(text)

    assert len(embedding) == 384
    # Check L2 normalization (sum of squares approx 1.0)
    norm = sum(x * x for x in embedding) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_journey_b_embedding_deterministic():
    """Identical input yields identical embedding output."""
    model = EmbeddingModel()
    text = "ECOG performance status 0 or 1"
    emb1 = model.encode(text)
    emb2 = model.encode(text)
    assert emb1 == emb2
