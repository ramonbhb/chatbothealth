from app.services.wizards.text_import import (
    assemble_sections_from_assignments,
    match_section_heading,
    paragraph_chunks,
    should_use_chunked_import,
    split_by_headings,
)


def test_should_use_chunked_import_for_long_text():
    assert should_use_chunked_import("x" * 6000) is True
    assert should_use_chunked_import("short text") is False


def test_split_by_headings():
    text = """Contexto
Intro do estudo.

Objetivos
Objetivo principal.

Métodos
Regressão logística.
"""
    sections = split_by_headings(text)
    assert "Intro do estudo" in sections["background"]
    assert "Objetivo principal" in sections["objectives"]
    assert "Regressão logística" in sections["methods_analysis"]


def test_match_section_heading_accepts_markdown():
    assert match_section_heading("## Fontes de Dados") == "data_sources"


def test_paragraph_chunks_respects_limit():
    text = "\n\n".join(f"Parágrafo {i}. " + ("texto " * 200) for i in range(10))
    chunks = paragraph_chunks(text, max_chars=1200)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1300 for chunk in chunks)


def test_assemble_sections_from_assignments():
    chunks = ["parte A", "parte B", "parte C"]
    assignments = {0: "background", 1: "objectives", 2: "objectives"}
    sections = assemble_sections_from_assignments(chunks, assignments)
    assert sections["background"] == "parte A"
    assert sections["objectives"] == "parte B\n\nparte C"
