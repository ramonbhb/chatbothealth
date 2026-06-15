from app.services.docgen.builder import build_project_doc


def test_build_project_doc_creates_sections():
    doc = build_project_doc(
        title="Test Study",
        section_data={"background": "Test background content."},
        user_email="test@example.com",
        session_id=1,
        model_used="test-model",
    )
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Test Study" in text
    assert "Test background content." in text
    assert "test@example.com" in text
