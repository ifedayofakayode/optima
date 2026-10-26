from core.rules import check_text


def codes(text):
    """Returns just the flag codes found in some text."""
    return [flag.code for flag in check_text(text)]


GOOD_CV = """
Ada Okafor
ada@example.com | +234 801 234 5678 | linkedin.com/in/adaokafor

Professional Summary
Customer support specialist with 4 years of remote experience using Slack and Zoom across GMT time zones.

Work Experience
Support Lead, Acme Ltd

Education
BSc Computer Science

Skills
Zendesk, Jira
"""


def test_detects_date_of_birth():
    assert "dob" in codes("Date of Birth: 12/05/1995")


def test_detects_marital_status():
    assert "marital" in codes("Marital Status: Single")


def test_detects_career_objective():
    assert "objective" in codes("CAREER OBJECTIVE\nTo work in a growing company")


def test_detects_local_phone_format():
    assert "phone_format" in codes("Call me on 08012345678")


def test_international_phone_is_fine():
    assert "phone_format" not in codes("Call me on +234 801 234 5678")


def test_age_does_not_match_inside_other_words():
    assert "age" not in codes("Project Management and Leverage skills")


def test_clean_cv_has_no_high_severity_flags():
    flags = check_text(GOOD_CV)
    assert [f.code for f in flags if f.severity == "high"] == []