from app.services.wizards.chat_context import section_context_summary, truncate_text


def test_truncate_text():
    assert truncate_text("abc", 10) == "abc"
    assert truncate_text("1234567890", 5) == "1234…"


def test_section_context_summary_uses_previews():
    summary = section_context_summary(
        {
            "background": "x" * 800,
            "objectives": "objetivo curto",
        }
    )
    assert "background" in summary
    assert "objectives" in summary
    assert "x" * 800 not in summary
    assert len(summary) < 900
