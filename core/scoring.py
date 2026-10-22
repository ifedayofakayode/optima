def compute_overall_score(result):
    """Combines the four sub-scores using fixed weights."""
    overall = (
        result.skills_score * 0.40
        + result.experience_score * 0.25
        + result.keyword_score * 0.20
        + result.achievements_score * 0.15
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