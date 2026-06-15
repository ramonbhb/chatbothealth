import json
import re


def strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def parse_json_object(text: str) -> dict:
    cleaned = strip_code_fence(text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {"raw": text}


def coerce_section_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("content", "text", "value", "body"):
            if key in value and value[key]:
                return str(value[key])
        return json.dumps(value, indent=2)
    return str(value).strip()
