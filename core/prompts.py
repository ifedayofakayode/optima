SYSTEM_MESSAGE = "You are a careful, strict resume analyst. Reply with JSON only."


def create_prompt(resume, job_description):
    return f"""
Compare the Resume to the Job Description and return JSON only.

Step 1: List exactly 10 requirements from the Job Description (the most important skills, tools, qualifications and experience it asks for, must-haves first).
Step 2: For each requirement, set "found" to true ONLY if the Resume clearly shows it. If you are unsure, set it to false.
Step 3: Rate two things on a 1-5 scale using these definitions.

experience_level:
1 = no relevant experience
2 = a little related experience, far below what the role needs
3 = partly relevant, or below the seniority asked for
4 = relevant and close to what the role needs
5 = meets or clearly exceeds what the role needs

achievements_level:
1 = only duties, no results
2 = a few results, no numbers
3 = some measurable results
4 = most roles show measurable results
5 = nearly every role shows strong, measurable results

Return exactly this JSON structure:
{{
  "requirements": [
    {{
      "name": "<requirement>",
      "importance": "<high, medium or low>",
      "found": <true or false>,
      "evidence": "<short phrase copied from the resume, or empty string>",
      "suggestion": "<if not found: one way to add it using only truthful experience, otherwise empty string>"
    }}
  ],
  "experience_level": <integer 1-5>,
  "achievements_level": <integer 1-5>,
  "strengths": ["<short statement>"],
  "top_fixes": ["<specific, actionable change>"]
}}

Rules:
- Use only the Resume and Job Description below.
- Never invent experience, employers or numbers. If a metric is needed, tell the candidate to add their real figure.

Resume:
{resume}

Job Description:
{job_description}
"""