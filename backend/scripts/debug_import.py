"""Debug script for import-text LLM splitting. Run from backend/:
  set -a && source ../.env && set +a
  PYTHONPATH=. python scripts/debug_import.py
"""
import asyncio
import json
import os
import traceback

SAMPLE_TEXT = """
Background: This study examines diabetes treatment outcomes in a regional hospital.
Research questions: Does treatment A improve HbA1c compared to treatment B?
Objectives: Primary objective is HbA1c reduction at 12 months.
Data sources: Electronic health records from Hospital X (2019-2024).
Study population: Adults aged 18+ with type 2 diabetes.
Variables: HbA1c (primary endpoint), age, sex, BMI.
Methods: Multivariable regression with propensity score adjustment.
Application: Clinicians need a web dashboard to select cohorts and view outcome tables.
Ethics: IRB approval #12345. Data use agreement in place.
Timeline: 6 months for analysis and app prototype.
Risks: Selection bias from incomplete records.
References: Smith et al. 2020.
"""


async def main() -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()

    print("=== Config ===")
    print(f"LLM_MODEL: {settings.llm_model}")
    print(f"GEMINI_API_KEY set: {bool(settings.gemini_api_key)}")
    print(f"Key prefix: {settings.gemini_api_key[:8]}..." if settings.gemini_api_key else "Key prefix: (none)")

    if settings.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
        os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key

    print("\n=== Direct LiteLLM call ===")
    try:
        from litellm import acompletion

        response = await acompletion(
            model=settings.llm_model,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_tokens=50,
        )
        content = response.choices[0].message.content
        print(f"Direct call OK. Response: {content!r}")
    except Exception as exc:
        print(f"Direct call FAILED: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return

    print("\n=== split_full_text_into_sections ===")
    try:
        from app.services.wizards.orchestrator import split_full_text_into_sections

        sections, model, debug = await split_full_text_into_sections(SAMPLE_TEXT)
        filled = {k: v for k, v in sections.items() if v.strip()}
        print(f"Model used: {model}")
        print(f"Debug: {debug}")
        print(f"Filled sections: {len(filled)} / {len(sections)}")
        for key, value in filled.items():
            preview = value[:80] + ("..." if len(value) > 80 else "")
            print(f"  {key}: {preview}")
        if not filled:
            print("ERROR: All sections empty!")
    except Exception as exc:
        print(f"Split FAILED: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return

    print("\n=== Raw complete_json (manual) ===")
    try:
        from app.services.llm.gateway import LLMGateway
        from app.services.llm.prompts import PROJECT_DOC_SECTIONS, SECTION_LABELS

        gw = LLMGateway()
        section_spec = {k: SECTION_LABELS[k] for k in PROJECT_DOC_SECTIONS}
        keys_list = ", ".join(PROJECT_DOC_SECTIONS)
        messages = [
            {
                "role": "system",
                "content": (
                    f"Return JSON only with snake_case keys: {keys_list}. "
                    f"Labels: {json.dumps(section_spec)}"
                ),
            },
            {"role": "user", "content": SAMPLE_TEXT},
        ]
        parsed, raw, _, _ = await gw.complete_json(messages, max_tokens=8192)
        print(f"Raw length: {len(raw)}")
        print(f"Raw preview (500 chars):\n{raw[:500]}")
        print(f"Parsed keys: {list(parsed.keys())[:15]}")
        if "raw" in parsed:
            print("WARNING: parse fell back to raw wrapper")
    except Exception as exc:
        print(f"Manual debug FAILED: {type(exc).__name__}: {exc}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
