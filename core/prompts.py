SYSTEM_MESSAGE = "You are a helpful HR assistant. Reply with JSON only."


def create_prompt(resume, job_description):
    return f"""
You are an expert career coach and ATS expert.
Compare the Resume and Job Description below.

You MUST return valid JSON only, using exactly these keys:
- "match_score": integer from 0 to 100 (how well the resume fits the job)
- "ats_score": integer from 0 to 100 (how easily an ATS can read and match the resume)
- "missing_keywords": list of important keywords from the job description that are missing from the resume
- "strengths": list of short statements about what the resume does well for this job
- "critical_gaps": list of the most serious missing qualifications or experience
- "improvements": list of specific, actionable changes to the resume

Base every value on the actual Resume and Job Description. Do not invent experience.

Resume:
{resume}

Job Description:
{job_description}
"""