import json
import logging
import sentry_sdk

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from pydantic import ValidationError

from core.prompts import SYSTEM_MESSAGE, create_prompt, RESUME_PARSE_SYSTEM_MESSAGE, create_resume_parse_prompt, create_resume_generation_prompt, COVER_LETTER_SYSTEM_MESSAGE, create_cover_letter_prompt
from core.schemas import AnalysisResult, ConfirmableItem, ParsedResume, ResumeData, CoverLetter

MODEL = "gpt-6-luna"  # change the model here, and only here
MAX_ATTEMPTS = 2      # first try plus one retry
MAX_PROMPT_LENGTH = 15000  # maximum length of the prompt


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
        logger.error(f"OpenAI request failed: {type(e).__name__}: {e}")
        sentry_sdk.capture_exception(e)
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

            # Handle confirmable_items from LLM response
            if "confirmable_items" in data:
                confirmable_items = []
                for item_data in data["confirmable_items"]:
                    confirmable_items.append(ConfirmableItem(
                        name=item_data.get("name", ""),
                        jd_source=item_data.get("jd_source", ""),
                        category=item_data.get("category", "domain"),
                        importance=item_data.get("importance", "medium"),
                        suggestion=item_data.get("suggestion", ""),
                    ))
                data["confirmable_items"] = confirmable_items

            return AnalysisResult.model_validate(data)  # dictionary -> checked object
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Attempt {attempt} produced an invalid reply: {str(e)[:500]}")

            if len(prompt) > MAX_PROMPT_LENGTH:
                logger.error(f"Prompt too long for retry ({len(prompt)} characters), giving up.")
                return None

            prompt += (
                f"\n\nYour previous reply was invalid: {str(e)[:500]}\n"
                "Return corrected JSON only, following the exact structure above."
            )

    return None


def parse_resume(client, resume_text):
    """Parse resume text into structured ParsedResume, or None if it could not get a valid one."""
    prompt = create_resume_parse_prompt(resume_text)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = call_llm(client, RESUME_PARSE_SYSTEM_MESSAGE, prompt)

        if raw is None:
            return None  # the request itself failed (billing, key, network), so retrying won't help

        try:
            data = json.loads(raw)                    # text -> Python dictionary
            return ParsedResume.model_validate(data)  # dictionary -> checked object
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Parse attempt {attempt} produced an invalid reply: {str(e)[:500]}")

            if len(prompt) > MAX_PROMPT_LENGTH:
                logger.error(f"Prompt too long for retry ({len(prompt)} characters), giving up.")
                return None

            prompt += (
                f"\n\nYour previous reply was invalid: {str(e)[:500]}\n"
                "Return corrected JSON only, following the exact structure above."
            )

    return None


def generate_resume(client, parsed_resume: ParsedResume, jd_text: str, confirmed_items: list):
    """Generate a tailored resume using the parsed resume, JD, and confirmed items."""
    prompt = create_resume_generation_prompt(
        parsed_resume.model_dump_json(),
        jd_text,
        confirmed_items
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = call_llm(client, SYSTEM_MESSAGE, prompt)

        if raw is None:
            return None  # the request itself failed (billing, key, network), so retrying won't help

        try:
            data = json.loads(raw)                    # text -> Python dictionary
            return ResumeData.model_validate(data)  # dictionary -> checked object
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Generation attempt {attempt} produced an invalid reply: {str(e)[:500]}")

            if len(prompt) > MAX_PROMPT_LENGTH:
                logger.error(f"Prompt too long for retry ({len(prompt)} characters), giving up.")
                return None

            prompt += (
                f"\n\nYour previous reply was invalid: {str(e)[:500]}\n"
                "Return corrected JSON only, following the exact structure above."
            )

    return None


def generate_cover_letter(
    client,
    parsed_resume: ParsedResume,
    jd_text: str,
    confirmed_items: list,
    tone: str = "professional",
    hiring_manager: str = "",
    why_company: str = ""
):
    """Generate a cover letter using the parsed resume, JD, and confirmed items."""
    prompt = create_cover_letter_prompt(
        parsed_resume.model_dump_json(),
        jd_text,
        confirmed_items,
        tone,
        hiring_manager,
        why_company
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = call_llm(client, COVER_LETTER_SYSTEM_MESSAGE, prompt)

        if raw is None:
            return None  # the request itself failed (billing, key, network), so retrying won't help

        try:
            data = json.loads(raw)                    # text -> Python dictionary
            cover_letter = CoverLetter.model_validate(data)  # dictionary -> checked object

            # Validate word count
            word_count = len(cover_letter.full_text.split())
            if word_count < 200 or word_count > 400:
                logger.warning(f"Cover letter word count {word_count} outside target range (250-350)")
                # Don't fail, just log it - the user can edit

            return cover_letter
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Cover letter generation attempt {attempt} produced an invalid reply: {str(e)[:500]}")

            if len(prompt) > MAX_PROMPT_LENGTH:
                logger.error(f"Prompt too long for retry ({len(prompt)} characters), giving up.")
                return None

            prompt += (
                f"\n\nYour previous reply was invalid: {str(e)[:500]}\n"
                "Return corrected JSON only, following the exact structure above."
            )

    return None

