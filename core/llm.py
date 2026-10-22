import json

from pydantic import ValidationError

from core.prompts import SYSTEM_MESSAGE, create_prompt
from core.schemas import AnalysisResult

MODEL = "gpt-6-luna"  # change the model here, and only here
MAX_ATTEMPTS = 2      # first try plus one retry


def call_llm(client, system_message, user_prompt):
    """Sends a prompt to the AI and returns the raw reply text, or None on failure."""
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
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI request failed: {type(e).__name__}: {e}")
        return None


def analyze_resume(client, resume_text, jd_text):
    """Returns a validated AnalysisResult, or None if it could not get a valid one."""
    prompt = create_prompt(resume_text, jd_text)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = call_llm(client, SYSTEM_MESSAGE, prompt)

        if raw is None:
            return None  # the request itself failed (billing, key, network), so retrying won't help

        try:
            data = json.loads(raw)                    # text -> Python dictionary
            return AnalysisResult.model_validate(data)  # dictionary -> checked object
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Attempt {attempt} produced an invalid reply: {str(e)[:500]}")
            prompt += (
                f"\n\nYour previous reply was invalid: {str(e)[:500]}\n"
                "Return corrected JSON only, following the exact structure above."
            )

    return None