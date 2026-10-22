import json

from core.prompts import SYSTEM_MESSAGE, create_prompt

MODEL = "gpt-6-luna"  # change the model here, and only here


def call_llm(client, system_message, user_prompt):
    """Sends a prompt to the AI and returns its JSON reply as a Python dictionary.
    Returns None if anything goes wrong."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=4000,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Analysis error: {type(e).__name__}: {e}")
        return None


def analyze_resume(client, resume_text, jd_text):
    """Builds the prompt and asks the AI to analyze the resume."""
    prompt = create_prompt(resume_text, jd_text)
    return call_llm(client, SYSTEM_MESSAGE, prompt)