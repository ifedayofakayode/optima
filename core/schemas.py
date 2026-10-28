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