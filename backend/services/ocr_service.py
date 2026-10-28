"""
OCR / text extraction — PDF (native + scanned), DOCX, images
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PageText:
    page_number: int
    text: str
    is_ocr: bool


def extract_text(file_path: Path, file_type: str) -> list[PageText]:
    """Extract page-wise text from an uploaded case document."""
    ext = file_type.lower().lstrip(".")
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if ext == "pdf":
        return _extract_pdf(path)
    if ext == "docx":
        return _extract_docx(path)
    if ext in {"jpg", "jpeg", "png"}:
        return _extract_image(path)
    raise ValueError(f"Unsupported file type for OCR: {ext}")


def pages_to_raw_text(pages: list[PageText]) -> str:
    parts: list[str] = []
    for page in pages:
        header = f"\n\n--- Page {page.page_number} ---\n"
        parts.append(header + (page.text or "").strip())
    return "\n".join(parts).strip()


def _extract_pdf(path: Path) -> list[PageText]:
    import fitz  # PyMuPDF

    doc = fitz.open(path)
    pages: list[PageText] = []
    try:
        for i, page in enumerate(doc):
            page_number = i + 1
            text = (page.get_text("text") or "").strip()
            if len(text) >= 40:
                pages.append(PageText(page_number=page_number, text=text, is_ocr=False))
                continue

            # Scanned / image-heavy page → render + Tesseract
            ocr_text = _ocr_pixmap(page)
            pages.append(
                PageText(
                    page_number=page_number,
                    text=ocr_text or text,
                    is_ocr=True,
                )
            )
    finally:
        doc.close()

    if not pages:
        # Fallback via pymupdf4llm markdown (preserves structure when available)
        try:
            import pymupdf4llm

            md = pymupdf4llm.to_markdown(str(path)) or ""
            if md.strip():
                return [PageText(page_number=1, text=md.strip(), is_ocr=False)]
        except Exception:
            pass
    return pages


def _ocr_pixmap(page) -> str:
    try:
        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return (pytesseract.image_to_string(img) or "").strip()
    except Exception:
        return ""


def _extract_docx(path: Path) -> list[PageText]:
    from docx import Document as DocxDocument

    document = DocxDocument(str(path))
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
    text = "\n".join(paragraphs)
    return [PageText(page_number=1, text=text, is_ocr=False)]


def _extract_image(path: Path) -> list[PageText]:
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(path)
        text = (pytesseract.image_to_string(img) or "").strip()
        return [PageText(page_number=1, text=text, is_ocr=True)]
    except Exception as exc:
        raise RuntimeError(f"Image OCR failed: {exc}") from exc
