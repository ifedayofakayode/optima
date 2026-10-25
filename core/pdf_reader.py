import pymupdf  # PyMuPDF, the library that reads PDF files

MIN_TEXT_LENGTH = 200  # fewer characters than this means the PDF is probably a scan


def extract_text_from_pdf(file):
    """Takes an uploaded PDF file and returns all its text as one string."""

    if not hasattr(file, 'read'):
        raise ValueError("The provided file object is not readable")

    try:
        file_content = file.read()
    except Exception as e:
        raise ValueError(f"Error reading the file: {e}")
    
    with pymupdf.open(stream=file_content, filetype="pdf") as doc:
        text = ""
        text_parts = [page.get_text() for page in doc]
        text = "".join(text_parts)
    return text


def has_readable_text(text):
    """Returns True if the text is long enough to be a real resume."""
    return len(text.strip()) >= MIN_TEXT_LENGTH