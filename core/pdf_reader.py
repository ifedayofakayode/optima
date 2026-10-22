import pymupdf  # PyMuPDF, the library that reads PDF files

MIN_TEXT_LENGTH = 200  # fewer characters than this means the PDF is probably a scan


def extract_text_from_pdf(file):
    """Takes an uploaded PDF file and returns all its text as one string."""
    with pymupdf.open(stream=file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return text


def has_readable_text(text):
    """Returns True if the text is long enough to be a real resume."""
    return len(text.strip()) >= MIN_TEXT_LENGTH