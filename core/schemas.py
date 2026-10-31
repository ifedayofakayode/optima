from typing import List, Literal

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """One requirement from the job description, checked against the resume."""
    name: str
    importance: Literal["high", "medium", "low"]
    found: bool          # True only if the resume clearly shows it
    evidence: str        # short phrase from the resume proving it ("" if not found)
    suggestion: str      # how to add it truthfully ("" if found)


class AnalysisResult(BaseModel):
    requirements: List[Requirement]
    experience_level: int = Field(ge=1, le=5)
    achievements_level: int = Field(ge=1, le=5)
    strengths: List[str]
    top_fixes: List[str]

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