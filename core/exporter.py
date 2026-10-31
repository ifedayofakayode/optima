from io import BytesIO

from docx import Document
from docx.shared import Pt, Cm


def _style_document(doc):
    """One clean font, narrow-but-readable margins."""
    for section in doc.sections:
        section.top_margin = Cm(1.8)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)


def _heading(doc, text):
    paragraph = doc.add_paragraph()
    run = paragraph.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(11.5)
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(2)


def build_docx(data):
    """Takes a ResumeData and returns the .docx file as bytes."""
    doc = Document()
    _style_document(doc)

    # Name and headline
    name = doc.add_paragraph()
    run = name.add_run(data.full_name)
    run.bold = True
    run.font.size = Pt(18)
    if data.headline:
        doc.add_paragraph(data.headline)

    # Contact line (plain text, in one line, so an ATS reads it easily)
    contact_parts = [data.email, data.phone, data.location, data.linkedin]
    doc.add_paragraph(" | ".join(part for part in contact_parts if part))

    if data.summary:
        _heading(doc, "Professional Summary")
        doc.add_paragraph(data.summary)

    if data.jobs:
        _heading(doc, "Work Experience")
        for job in data.jobs:
            line = doc.add_paragraph()
            line.paragraph_format.space_before = Pt(6)
            line.paragraph_format.space_after = Pt(0)
            title = line.add_run(f"{job.title}, {job.company}")
            title.bold = True
            dates = f"{job.start} – {job.end}"
            place = f" | {job.location}" if job.location else ""
            doc.add_paragraph(dates + place).paragraph_format.space_after = Pt(2)
            for bullet in job.bullets:
                if bullet.strip():
                    doc.add_paragraph(bullet.strip(), style="List Bullet")

    if data.education:
        _heading(doc, "Education")
        for school in data.education:
            text = f"{school.qualification}, {school.institution}"
            if school.year:
                text += f" ({school.year})"
            doc.add_paragraph(text)

    if data.skills:
        _heading(doc, "Skills")
        doc.add_paragraph(", ".join(data.skills))

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()