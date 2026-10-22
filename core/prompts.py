SYSTEM_MESSAGE = "You are a careful resume and ATS expert. Reply with JSON only."


def create_prompt(resume, job_description):
    return f"""
Compare the Resume to the Job Description and return JSON only.

Scoring rubric (each score is an integer from 0 to 100):
- skills_score: how many of the job's required skills and tools appear in the resume
- experience_score: how well the seniority, years and type of experience fit the role
- keyword_score: how many important job-description keywords appear in the resume
- achievements_score: how much of the resume shows measurable results, not just duties
A score of 90+ means an excellent fit, about 60 means a partial fit, 30 or below means a poor fit.

Return exactly this JSON structure:
{{
  "skills_score": <integer 0-100>,
  "experience_score": <integer 0-100>,
  "keyword_score": <integer 0-100>,
  "achievements_score": <integer 0-100>,
  "missing_keywords": [
    {{
      "keyword": "<missing skill or keyword>",
      "importance": "<high, medium or low>",
      "why_it_matters": "<one sentence>",
      "suggestion": "<one specific way to add it, using only truthful experience>"
    }}
  ],
  "strengths": ["<short statement>"],
  "top_fixes": ["<specific, actionable change>"]
}}

Rules:
- Base every value only on the Resume and Job Description below.
- Never invent experience, employers or numbers. If a metric is needed, tell the candidate to add their real figure.
- List at most 8 missing keywords, ordered by importance.

Resume:
{resume}

Job Description:
{job_description}
"""