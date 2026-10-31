from core.rewriter import invents_numbers

ORIGINAL = "Managed a team of 5 support agents"


def test_keeps_original_numbers():
    assert not invents_numbers(ORIGINAL, "Led 5 support agents, reducing backlog by [X%]")


def test_rejects_invented_numbers():
    assert invents_numbers(ORIGINAL, "Led 5 support agents, reducing backlog by 40%")


def test_placeholders_are_allowed():
    assert not invents_numbers(ORIGINAL, "Led 5 agents handling [number] tickets per week")


def test_original_with_no_numbers():
    assert invents_numbers("Handled customer complaints", "Resolved 120 complaints monthly")