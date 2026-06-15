from app.services.llm.json_utils import coerce_section_value, parse_json_object


def test_parse_json_object_from_fence():
    raw = '```json\n{"background": "Test background"}\n```'
    result = parse_json_object(raw)
    assert result["background"] == "Test background"


def test_coerce_section_value_from_dict():
    assert coerce_section_value({"content": "Hello"}) == "Hello"


def test_parse_nested_sections():
    raw = '{"sections": {"objectives": "Primary objective"}}'
    result = parse_json_object(raw)
    assert result["sections"]["objectives"] == "Primary objective"
