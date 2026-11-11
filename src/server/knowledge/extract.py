"""Text extraction for the knowledge base. Supported: .pdf .pptx .docx .md .txt  ->  [(page_or_slide_number, text), ...]"""
from pathlib import Path

SUPPORTED = {".pdf", ".pptx", ".docx", ".md", ".txt"}


class ExtractError(Exception):
    pass


def _pdf(path):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise ExtractError("encrypted PDF")
    return [(i + 1, pg.extract_text() or "") for i, pg in enumerate(reader.pages)]


def _shape_text(shape, out):
    if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
        t = "\n".join(p.text for p in shape.text_frame.paragraphs if p.text.strip())
        if t:
            out.append(t)
    if getattr(shape, "has_table", False) and shape.has_table:
        for row in shape.table.rows:
            out.append(" | ".join(c.text.strip() for c in row.cells))
    if getattr(shape, "shapes", None) is not None and hasattr(shape, "shape_type") and shape.shape_type == 6:   # group
        for sub in shape.shapes:
            _shape_text(sub, out)


def _pptx(path):
    from pptx import Presentation
    pages = []
    for i, slide in enumerate(Presentation(str(path)).slides, 1):
        parts = []
        for shape in slide.shapes:
            _shape_text(shape, parts)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                parts.append("Notes: " + notes)
        pages.append((i, "\n".join(parts)))
    return pages


def _docx(path):
    """Extract text from a Word document (.docx), grouping by heading-delimited sections.

    Because Word documents lack explicit page boundaries, headings serve as logical
    page breaks. Safely checks paragraph styles to ensure custom or un-named styles
    do not cause attribute errors.
    """
    from docx import Document
    doc = Document(str(path))
    sections, current, n = [], [], 1
    for p in doc.paragraphs:
        if p.style is not None and getattr(p.style, "name", None) and p.style.name.lower().startswith("heading") and current:
            sections.append((n, "\n".join(current)))
            current, n = [], n + 1
        if p.text.strip():
            current.append(p.text)
    for t in doc.tables:
        for row in t.rows:
            current.append(" | ".join(c.text.strip() for c in row.cells))
    sections.append((n, "\n".join(current)))
    return sections


def _text(path):
    return [(1, Path(path).read_text(encoding="utf-8", errors="ignore"))]


_EXTRACTORS = {".pdf": _pdf, ".pptx": _pptx, ".docx": _docx, ".md": _text, ".txt": _text}


def extract(path) -> list[tuple[int, str]]:
    path = Path(path)
    fn = _EXTRACTORS.get(path.suffix.lower())
    if not fn:
        raise ExtractError(f"unsupported file type {path.suffix}")
    try:
        pages = fn(path)
    except ExtractError:
        raise
    except Exception as e:
        raise ExtractError(f"{type(e).__name__}: {e}")
    pages = [(n, " ".join(t.split())) for n, t in pages]
    return [(n, t) for n, t in pages if t]
