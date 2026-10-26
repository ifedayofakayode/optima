from dataclasses import dataclass, field
from typing import List

import pymupdf  # PyMuPDF, the library that reads PDF files

MIN_TEXT_LENGTH = 200  # fewer characters than this means the PDF is probably a scan


@dataclass
class PdfInfo:
    """Everything we learn about an uploaded resume PDF."""
    text: str
    page_count: int
    has_photo: bool
    likely_columns: bool
    has_tables: bool
    links: List[str] = field(default_factory=list)


def _has_photo(page):
    """Looks for a roughly square, mid-sized picture near the top of page 1."""
    try:
        images = page.get_image_info()
    except Exception:
        return False

    for img in images:
        x0, y0, x1, y1 = img["bbox"]
        width, height = x1 - x0, y1 - y0
        if height <= 0:
            continue
        squarish = 0.6 <= width / height <= 1.4
        photo_sized = 60 <= width <= 250 and 60 <= height <= 300
        near_top = y0 < page.rect.height * 0.45
        if squarish and photo_sized and near_top:
            return True
    return False


def _has_columns(page):
    """Guesses whether page 1 has two side-by-side columns of text."""
    width = page.rect.width
    # each block is (x0, y0, x1, y1, text, block_no, block_type); type 0 means text
    blocks = [b for b in page.get_text("blocks") if b[6] == 0 and len(b[4].strip()) > 20]
    if len(blocks) < 6:
        return False

    left = [b for b in blocks if b[2] < width * 0.55]    # block ends in the left half
    right = [b for b in blocks if b[0] > width * 0.40]   # block starts in the right half
    if len(left) < 3 or len(right) < 3:
        return False

    # real columns sit next to each other, so some left and right blocks share vertical space
    return any(l[1] < r[3] and r[1] < l[3] for l in left for r in right)


def _has_tables(page):
    """Checks whether the page contains table-like structures."""
    try:
        return len(page.find_tables().tables) > 0
    except Exception:
        return False


def inspect_pdf(pdf_bytes):
    """Opens the PDF once and returns a PdfInfo with the text and layout facts."""
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        text = ""
        links = []
        has_tables = False

        for page in doc:
            text += page.get_text()
            for link in page.get_links():
                uri = link.get("uri")
                if uri:
                    links.append(uri)
            if page.number < 2:  # tables are slow to detect, so only check the first two pages
                has_tables = has_tables or _has_tables(page)

        first_page = doc[0] if doc.page_count > 0 else None
        return PdfInfo(
            text=text,
            page_count=doc.page_count,
            has_photo=_has_photo(first_page) if first_page else False,
            likely_columns=_has_columns(first_page) if first_page else False,
            has_tables=has_tables,
            links=links,
        )


def has_readable_text(text):
    """Returns True if the text is long enough to be a real resume."""
    return len(text.strip()) >= MIN_TEXT_LENGTH