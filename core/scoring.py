IMPORTANCE_WEIGHT = {"high": 3, "medium": 2, "low": 1}


def requirements_score(result):
    """Percentage of requirements met, counting important ones more."""
    total = sum(IMPORTANCE_WEIGHT[r.importance] for r in result.requirements)
    if total == 0:
        return 0
    met = sum(IMPORTANCE_WEIGHT[r.importance] for r in result.requirements if r.found)
    return round(100 * met / total)


def compute_overall_score(result):
    """Combines the three parts using fixed weights."""
    overall = (
        requirements_score(result) * 0.60
        + result.experience_level * 20 * 0.25
        + result.achievements_level * 20 * 0.15
    )
    return round(overall)


def score_band(score):
    """Turns a number into a label people can understand."""
    if score >= 80:
        return "Strong match"
    if score >= 60:
        return "Good match, with gaps to fix"
    if score >= 40:
        return "Needs significant work"
    return "Weak match for this role"