import re

SUSPICIOUS_PHRASES = [
    "ignore previous instructions",
    "ignore all previous",
    "ignore your instructions",
    "ignore the above",
    "disregard the above",
    "disregard previous",
    "new instructions",
    "system prompt",
    "you are now",
    "give a perfect score",
    "give me a perfect score",
    "give this candidate",
]


def clean_untrusted_text(text):
    """Removes angle brackets so user text can't fake our <resume> or <job_description> tags."""
    return text.replace("<", "(").replace(">", ")")


def looks_like_injection(text):
    """Returns True if the text contains a phrase commonly used to give orders to an AI."""
    normalized = re.sub(r'\s+', ' ', text.lower())
    return any(phrase in normalized for phrase in SUSPICIOUS_PHRASES)