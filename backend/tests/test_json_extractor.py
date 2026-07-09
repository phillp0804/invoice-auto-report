"""AI JSON 回應解析工具（utils/json_extractor.py）的單元測試。

實測發現 Gemini 常把 JSON 包在 ```json ... ``` 裡（即使 prompt 要求
「僅輸出 JSON」），這裡涵蓋該情境的回歸測試。
"""

import json

import pytest

from utils.json_extractor import parse_json_response


class TestParseJsonResponse:
    """parse_json_response() 測試。"""

    def test_plain_json(self):
        result = parse_json_response('{"category": "餐飲"}')

        assert result == {"category": "餐飲"}

    def test_json_wrapped_in_labeled_code_fence(self):
        text = '```json\n{"category": "餐飲"}\n```'

        result = parse_json_response(text)

        assert result == {"category": "餐飲"}

    def test_json_wrapped_in_plain_code_fence(self):
        text = '```\n{"category": "餐飲"}\n```'

        result = parse_json_response(text)

        assert result == {"category": "餐飲"}

    def test_tolerates_surrounding_whitespace(self):
        text = '  \n```json\n{"category": "餐飲"}\n```\n  '

        result = parse_json_response(text)

        assert result == {"category": "餐飲"}

    def test_multiline_json_in_code_fence(self):
        text = (
            "```json\n"
            "{\n"
            '  "invoice_number": "AB12345678",\n'
            '  "amount": 810\n'
            "}\n"
            "```"
        )

        result = parse_json_response(text)

        assert result == {"invoice_number": "AB12345678", "amount": 810}

    def test_invalid_json_still_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_json_response("這不是 JSON")

    def test_invalid_json_inside_code_fence_still_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_json_response("```json\n這不是 JSON\n```")
