"""AI 支出分類服務（ClassifierService）的單元測試（不呼叫真實 AI API）。"""

import json
from unittest.mock import MagicMock

from services.classifier_service import EXPENSE_CATEGORIES, ClassifierService


def _make_service() -> tuple[ClassifierService, MagicMock]:
    """建立 ClassifierService，注入一個 mock 的 ai_client（介面與 ClaudeClient/GeminiClient 一致）。"""
    mock_ai_client = MagicMock()
    service = ClassifierService(ai_client=mock_ai_client)
    return service, mock_ai_client


class TestClassify:
    """classify() 測試。"""

    def test_valid_category_returned_as_is(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_text.return_value = json.dumps({"category": "餐飲"})

        result = service.classify(items=["排骨便當"], amount=120)

        assert result == "餐飲"

    def test_response_wrapped_in_markdown_code_fence_still_parses(self):
        """迴歸測試：Gemini 實測會把 JSON 包在 ```json ... ``` 裡。"""
        service, mock_ai_client = _make_service()
        mock_ai_client.send_text.return_value = '```json\n{"category": "交通"}\n```'

        result = service.classify(items=["計程車資"])

        assert result == "交通"

    def test_category_outside_fixed_list_falls_back_to_other(self):
        """AI 若自由生成清單外的類別，不可採信，須回退為「其他」（core rule 5）。"""
        service, mock_ai_client = _make_service()
        mock_ai_client.send_text.return_value = json.dumps({"category": "娛樂"})

        result = service.classify(items=["電影票"])

        assert result == "其他"

    def test_malformed_json_falls_back_to_other(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_text.return_value = "不是 JSON"

        result = service.classify(items=["某品項"])

        assert result == "其他"

    def test_empty_items_uses_placeholder_text(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_text.return_value = json.dumps({"category": "其他"})

        service.classify(items=[])

        _, kwargs = mock_ai_client.send_text.call_args
        assert "無品項資訊" in kwargs["user_text"]

    def test_amount_included_in_user_content_when_provided(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_text.return_value = json.dumps({"category": "交通"})

        service.classify(items=["計程車資"], amount=350)

        _, kwargs = mock_ai_client.send_text.call_args
        assert "計程車資" in kwargs["user_text"]
        assert "350" in kwargs["user_text"]

    def test_system_prompt_lists_all_fixed_categories(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_text.return_value = json.dumps({"category": "其他"})

        service.classify(items=["某品項"])

        _, kwargs = mock_ai_client.send_text.call_args
        system_prompt = kwargs["system_prompt"]
        for category in EXPENSE_CATEGORIES:
            assert category in system_prompt
