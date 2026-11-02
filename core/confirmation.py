from core.schemas import ConfirmableItem, Requirement


def extract_confirmable_items(result) -> list:
    """Convert missing requirements into confirmable items."""
    confirmable = []
    for req in result.requirements:
        if not req.found:  # Only missing requirements
            # Determine category based on content
            category = _guess_category(req.name)

            confirmable.append(ConfirmableItem(
                name=req.name,
                jd_source=req.name,  # In production, you'd extract exact JD phrase
                category=category,
                importance=req.importance,
                suggestion=req.suggestion,
            ))
    return confirmable


def _guess_category(name: str) -> str:
    """Simple heuristic to categorize a requirement."""
    name_lower = name.lower()
    if any(word in name_lower for word in ["experience", "years", "worked"]):
        return "experience"
    if any(word in name_lower for word in ["degree", "bachelor", "master", "phd", "certif"]):
        return "certification"
    if any(word in name_lower for word in ["skill", "knowledge", "proficient"]):
        return "skill"
    if any(word in name_lower for word in ["tool", "software", "framework", "language"]):
        return "tool"
    return "domain"


def build_confirmed_gap_data(confirmable_items: list) -> dict:
    """Build the confirmed gap data structure."""
    confirmed = [item for item in confirmable_items if item.is_confirmed]
    excluded = [item for item in confirmable_items if not item.is_confirmed]

    return {
        "confirmed_items": confirmed,
        "excluded_items": excluded,
    }
