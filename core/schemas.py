from typing import List, Literal

from pydantic import BaseModel, Field


class Gap(BaseModel):
    """One missing keyword or skill, with advice on fixing it."""
    keyword: str
    importance: Literal["high", "medium", "low"]
    why_it_matters: str
    suggestion: str


class AnalysisResult(BaseModel):
    """The full analysis of one resume against one job description."""
    skills_score: int = Field(ge=0, le=100)
    experience_score: int = Field(ge=0, le=100)
    keyword_score: int = Field(ge=0, le=100)
    achievements_score: int = Field(ge=0, le=100)
    missing_keywords: List[Gap]
    strengths: List[str]
    top_fixes: List[str]