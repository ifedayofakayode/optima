import re
from dataclasses import dataclass


@dataclass
class Flag:
    """One issue found in a resume."""
    code: str       # short ID used in tests, e.g. "dob"
    severity: str   # "high", "medium" or "low"
    title: str      # what we found
    why: str        # why it matters for remote applications
    fix: str        # what to do about it


# ---------- Personal details that many remote employers don't expect ----------

# (code, pattern to search for, label, severity)
PERSONAL_DETAILS = [
    ("dob", r"date\s+of\s+birth|\bd\.?o\.?b\b|\bborn\s+on\b|\bbirth\s*date\b", "Date of birth", "high"),
    ("age", r"\bage\s*[:\-]\s*\d{2}\b", "Age", "high"),
    ("marital", r"marital\s+status", "Marital status", "high"),
    ("religion", r"\breligion\b", "Religion", "high"),
    ("origin", r"state\s+of\s+origin|local\s+government(\s+area)?|\blga\b", "State of origin", "medium"),
    ("gender", r"\b(gender|sex)\s*[:\-]\s*(male|female)", "Gender", "medium"),
    ("nationality", r"\bnationality\s*[:\-]", "Nationality", "medium"),
]

PERSONAL_WHY = (
    "Employers in the US, UK and EU usually avoid collecting this to prevent discrimination, "
    "so many recruiters expect it to be absent. It also uses space that should show your skills."
)

# ---------- Words that suggest remote-work experience ----------

REMOTE_SIGNALS = (
    r"\b(remote|async|asynchronous|slack|zoom|notion|jira|asana|trello|"
    r"time\s*zone|timezone|gmt|utc|distributed|virtual)\b"
)

# ---------- Headings an ATS looks for ----------

EXPERIENCE_HEADINGS = ["experience", "employment", "work history", "career history"]
EDUCATION_HEADINGS = ["education", "qualifications", "academic"]
SKILLS_HEADINGS = ["skills", "competencies", "technologies", "tools"]


def _has_heading(text, names):
    """True if a short line looks like a section heading containing one of the names."""
    for line in text.splitlines():
        cleaned = line.strip().lower().rstrip(":")
        if 0 < len(cleaned) <= 30 and any(name in cleaned for name in names):
            return True
    return False


def check_text(text, links=()):
    """Runs every check that only needs the resume's text. Returns a list of Flags."""
    flags = []
    lowered = text.lower()
    all_links = " ".join(links).lower()

    # 1. Personal details
    for code, pattern, label, severity in PERSONAL_DETAILS:
        if re.search(pattern, lowered, re.MULTILINE):
            flags.append(Flag(
                code=code,
                severity=severity,
                title=f"{label} is listed",
                why=PERSONAL_WHY,
                fix=f"Delete the {label.lower()} line from your CV.",
            ))

    # 2. Career objective
    if re.search(r"^\s*(career\s+)?objective\b", lowered, re.MULTILINE):
        flags.append(Flag(
            code="objective",
            severity="medium",
            title="Uses a 'career objective'",
            why="Objective statements read as dated to many recruiters abroad. They want a short summary of what you have already achieved.",
            fix="Replace it with a 2-3 line professional summary: your role, your years of experience, and your strongest result.",
        ))

    # 3. References line
    if re.search(r"\breferees?\b|references\s+(are\s+)?(available|upon|on\s+request)", lowered):
        flags.append(Flag(
            code="referees",
            severity="low",
            title="Mentions referees or 'references available on request'",
            why="Recruiters assume you can provide references, so the line wastes space.",
            fix="Delete it. Prepare references separately for when an employer asks.",
        ))

    # 4. Contact details
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        flags.append(Flag(
            code="no_email",
            severity="high",
            title="No email address found",
            why="Recruiters and ATS tools need an email address to contact you.",
            fix="Add a professional email address near the top of your CV.",
        ))

    if "linkedin.com" not in lowered and "linkedin.com" not in all_links:
        flags.append(Flag(
            code="no_linkedin",
            severity="medium",
            title="No LinkedIn link found",
            why="Remote recruiters usually check your LinkedIn profile before replying.",
            fix="Add your LinkedIn profile address in your contact line.",
        ))

    has_international = re.search(r"\+\s*\d{1,3}[\s\-.()]*\d", text)
    has_local = re.search(r"(?<!\d)0\d{2,3}[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}(?!\d)", text)
    if has_local and not has_international:
        flags.append(Flag(
            code="phone_format",
            severity="medium",
            title="Phone number has no country code",
            why="A recruiter in another country can't dial a number that starts with 0.",
            fix="Write it in international format, for example +234 801 234 5678.",
        ))

    # 5. Section headings an ATS expects
    if not _has_heading(text, EXPERIENCE_HEADINGS):
        flags.append(Flag(
            code="no_experience_heading",
            severity="high",
            title="No clear 'Experience' section heading",
            why="An ATS sorts your resume by section headings. Without one it may not find your work history.",
            fix="Use a standard heading such as 'Work Experience' or 'Professional Experience'.",
        ))
    if not _has_heading(text, EDUCATION_HEADINGS):
        flags.append(Flag(
            code="no_education_heading",
            severity="medium",
            title="No clear 'Education' section heading",
            why="An ATS looks for an Education section to read your qualifications.",
            fix="Add a heading called 'Education'.",
        ))
    if not _has_heading(text, SKILLS_HEADINGS):
        flags.append(Flag(
            code="no_skills_heading",
            severity="medium",
            title="No clear 'Skills' section heading",
            why="Keyword matching works best when your skills sit under a standard heading.",
            fix="Add a heading called 'Skills' and list your tools and strengths.",
        ))

    # 6. Remote-work evidence
    signals = set(re.findall(REMOTE_SIGNALS, lowered))
    if len(signals) < 2:
        flags.append(Flag(
            code="remote_evidence",
            severity="low",
            title="Little evidence of remote-work experience",
            why="Remote employers look for proof that you can work independently across time zones.",
            fix="Mention remote tools you've used (Slack, Zoom, Notion, Jira), your time zone and overlap hours, and any work done independently or with distributed teams.",
        ))

    return flags


def check_layout(info):
    """Runs the checks that need the PDF's layout. `info` is a PdfInfo from pdf_reader."""
    flags = []

    if info.has_photo:
        flags.append(Flag(
            code="photo",
            severity="medium",
            title="Your CV appears to include a photo",
            why="Employers in the US, UK and EU generally don't want photos on CVs, to avoid bias. Photos can also confuse ATS software.",
            fix="Remove the photo. Put your name, role and contact details at the top instead.",
        ))

    if info.likely_columns:
        flags.append(Flag(
            code="columns",
            severity="medium",
            title="Your CV possibly uses two columns",
            why="Many ATS tools read across both columns line by line, which scrambles your content.",
            fix="Use a single-column layout with standard headings.",
        ))

    if info.has_tables:
        flags.append(Flag(
            code="tables",
            severity="medium",
            title="Your CV appears to contain tables",
            why="Text inside tables is often read in the wrong order, or skipped, by an ATS.",
            fix="Replace tables with plain bullet lists and headings.",
        ))

    if info.page_count > 2:
        flags.append(Flag(
            code="too_long",
            severity="low",
            title=f"Your CV is {info.page_count} pages long",
            why="Recruiters usually skim a CV in under a minute, and long ones often go unread.",
            fix="Aim for 1-2 pages. Cut older or less relevant roles.",
        ))

    return flags


def run_all_checks(info):
    """Runs every check and returns one combined list of Flags."""
    return check_layout(info) + check_text(info.text, info.links)