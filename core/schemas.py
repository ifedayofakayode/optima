from typing import List, Literal
from dataclasses import dataclass

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """One requirement from the job description, checked against the resume."""
    name: str
    importance: Literal["high", "medium", "low"]
    found: bool          # True only if the resume clearly shows it
    evidence: str        # short phrase from the resume proving it ("" if not found)
    suggestion: str      # how to add it truthfully ("" if found)


@dataclass
class ConfirmableItem:
    """A missing requirement that the user can confirm they have."""
    name: str                      # e.g., "Python"
    jd_source: str                 # e.g., "3+ years of Python experience"
    category: str                 # "skill", "tool", "experience", "certification", "domain"
    importance: Literal["high", "medium", "low"]
    suggestion: str               # From the original analysis

    # User's response
    response: Literal["yes", "partially", "no", "unanswered"] = "unanswered"
    evidence: str = ""            # User's free-text evidence for yes/partially

    # Whether this was confirmed and should be included in generation
    is_confirmed: bool = False


class ConfirmedGapData(BaseModel):
    """All the data from the gap confirmation flow."""
    confirmed_items: List[ConfirmableItem]
    excluded_items: List[ConfirmableItem]
    honesty_summary: str = ""


class AnalysisResult(BaseModel):
    requirements: List[Requirement]
    experience_level: int = Field(ge=1, le=5)
    achievements_level: int = Field(ge=1, le=5)
    strengths: List[str]
    top_fixes: List[str]
    confirmable_items: List[ConfirmableItem] = Field(default_factory=list)

    # ATS-specific fields
    ats_score: int = Field(ge=0, le=100, default=0)
    ats_score_explanation: str = ""
    must_have_keywords: List[str] = Field(default_factory=list)
    nice_to_have_keywords: List[str] = Field(default_factory=list)
    critical_gaps: List[str] = Field(default_factory=list)
    ats_format_issues: List[str] = Field(default_factory=list)

class Rewrite(BaseModel):
    approach: str   # for example "Results first"
    text: str


class RewriteResult(BaseModel):
    problems: List[str]
    rewrites: List[Rewrite]
    metric_questions: List[str]

class Job(BaseModel):
    title: str
    company: str
    location: str = ""
    start: str          # "Jan 2022"
    end: str            # "Present" or "Mar 2024"
    bullets: List[str]


class School(BaseModel):
    qualification: str
    institution: str
    year: str = ""


class ResumeData(BaseModel):
    full_name: str
    headline: str = ""              # for example "Customer Support Specialist"
    email: str
    phone: str = ""
    location: str = ""              # for example "Lagos, Nigeria (GMT+1)"
    linkedin: str = ""
    summary: str = ""
    jobs: List[Job] = []
    education: List[School] = []
    skills: List[str] = []


class ParsedResume(BaseModel):
    """The original resume parsed into structured data."""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    summary: str = ""
    jobs: List[Job] = Field(default_factory=list)
    education: List[School] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)


class CoverLetter(BaseModel):
    """A generated cover letter."""
    recipient_name: str = ""  # Hiring manager or "Hiring Manager"
    company_name: str = ""
    job_title: str = ""
    greeting: str = ""  # e.g., "Dear Mr. Smith," or "Dear Hiring Manager,"
    hook: str = ""  # Opening paragraph
    body_paragraph_1: str = ""  # First evidence-based paragraph
    body_paragraph_2: str = ""  # Second evidence-based paragraph
    closing: str = ""  # Brief closing
    sign_off: str = ""  # e.g., "Sincerely,"
    full_text: str = ""  # Complete cover letter as text