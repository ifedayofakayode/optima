from io import BytesIO

from docx import Document
from docx.shared import Pt, Cm
from core.schemas import CoverLetter, ResumeData
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


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


def build_pdf(data: ResumeData):
    """Takes a ResumeData and returns the .pdf file as bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomTitle', fontSize=18, fontName='Helvetica-Bold', spaceAfter=12))
    styles.add(ParagraphStyle(name='CustomHeading', fontSize=12, fontName='Helvetica-Bold', spaceAfter=6, spaceBefore=12))
    styles.add(ParagraphStyle(name='CustomBody', fontSize=10, fontName='Helvetica', spaceAfter=6))

    story = []

    # Name
    story.append(Paragraph(data.full_name, styles['CustomTitle']))

    # Contact line
    contact_parts = [part for part in [data.email, data.phone, data.location, data.linkedin] if part]
    story.append(Paragraph(" | ".join(contact_parts), styles['CustomBody']))
    story.append(Spacer(1, 12))

    # Summary
    if data.summary:
        story.append(Paragraph("Professional Summary", styles['CustomHeading']))
        story.append(Paragraph(data.summary, styles['CustomBody']))
        story.append(Spacer(1, 12))

    # Jobs
    if data.jobs:
        story.append(Paragraph("Work Experience", styles['CustomHeading']))
        for job in data.jobs:
            story.append(Paragraph(f"{job.title}, {job.company}", styles['CustomHeading']))
            story.append(Paragraph(f"{job.start} – {job.end}{' | ' + job.location if job.location else ''}", styles['CustomBody']))
            for bullet in job.bullets:
                if bullet.strip():
                    story.append(Paragraph(f"• {bullet.strip()}", styles['CustomBody']))
            story.append(Spacer(1, 6))

    # Education
    if data.education:
        story.append(Paragraph("Education", styles['CustomHeading']))
        for school in data.education:
            text = f"{school.qualification}, {school.institution}"
            if school.year:
                text += f" ({school.year})"
            story.append(Paragraph(text, styles['CustomBody']))
        story.append(Spacer(1, 12))

    # Skills
    if data.skills:
        story.append(Paragraph("Skills", styles['CustomHeading']))
        story.append(Paragraph(", ".join(data.skills), styles['CustomBody']))

    doc.build(story)
    return buffer.getvalue()


def build_cover_letter_docx(cover_letter: CoverLetter):
    """Takes a CoverLetter and returns the .docx file as bytes."""
    doc = Document()
    _style_document(doc)

    # Sender info (left-aligned)
    sender = doc.add_paragraph()
    sender.paragraph_format.space_after = Pt(0)
    # We don't have sender address, so skip it

    # Date
    from datetime import datetime
    doc.add_paragraph(datetime.now().strftime("%B %d, %Y"))

    # Recipient info
    if cover_letter.recipient_name:
        doc.add_paragraph(cover_letter.recipient_name)
    if cover_letter.company_name:
        doc.add_paragraph(cover_letter.company_name)

    # Greeting
    doc.add_paragraph(cover_letter.greeting or "Dear Hiring Manager,")

    # Body paragraphs
    doc.add_paragraph(cover_letter.hook)
    doc.add_paragraph(cover_letter.body_paragraph_1)
    doc.add_paragraph(cover_letter.body_paragraph_2)
    doc.add_paragraph(cover_letter.closing)

    # Sign-off
    doc.add_paragraph(cover_letter.sign_off or "Sincerely,")

    # Placeholder for signature
    doc.add_paragraph("[Your Name]")

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
