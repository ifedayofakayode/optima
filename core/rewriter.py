import json
import re

from pydantic import ValidationError

from core.llm import call_llm
from core.prompts import REWRITE_SYSTEM_MESSAGE, create_rewrite_prompt
from core.schemas import RewriteResult

MAX_ATTEMPTS = 2
NUMBER_PATTERN = re.compile(r"\d[\d,.]*")


def _numbers(text):
    """Every number in the text, as a set of strings."""
    return {n.strip(",.") for n in NUMBER_PATTERN.findall(text)}


def invents_numbers(original, rewrite):
    """True if the rewrite contains a number that is neither in the original
    nor inside [square brackets]."""
    without_placeholders = re.sub(r"\[[^\]]*\]", " ", rewrite)
    return bool(_numbers(without_placeholders) - _numbers(original))


def rewrite_bullet(client, bullet, job_context=""):
    """Returns a RewriteResult with only safe rewrites, or None if it could not."""
    prompt = create_rewrite_prompt(bullet, job_context)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = call_llm(client, REWRITE_SYSTEM_MESSAGE, prompt)
        if raw is None:
            return None  # the request itself failed, so retrying won't help

        try:
            result = RewriteResult.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Rewrite attempt {attempt}: invalid reply: {str(e)[:300]}")
            prompt += "\n\nYour previous reply was invalid. Return corrected JSON only, in the exact structure above."
            continue

        safe = [r for r in result.rewrites if not invents_numbers(bullet, r.text)]
        if safe:
            result.rewrites = safe
            return result

        print(f"Rewrite attempt {attempt}: every rewrite contained invented numbers")
        prompt += (
            "\n\nYour previous rewrites contained numbers that are not in the original bullet. "
            "Use bracketed placeholders like [X%] instead of any new number."
        )

    return None