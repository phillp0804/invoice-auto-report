"""AI 支出分類服務（ClassifierService）的單元測試（不呼叫真實 Claude API）。"""

import json
from unittest.mock import MagicMock, patch

from services.classifier_service import EXPENSE_CATEGORIES, ClassifierService


def _make_service() -> tuple[ClassifierService, MagicMock]:
    """建立 ClassifierService，並回傳其內部 ClaudeClient 的 mock 實例。"""
    with patch("services.classifier_service.ClaudeClient") as mock_claude_client_cls:
        mock_client = MagicMock()
        mock_claude_client_cls.return_value = mock_client
        service = ClassifierService(api_key="test-key")
    return service, mock_client


class TestClassify:
    """classify() 測試。"""

    def test_valid_category_returned_as_is(self):
        service, mock_client = _make_service()
        mock_client.send_message.return_value = json.dumps({"category": "餐飲"})

        result = service.classify(items=["排骨便當"], amount=120)

        assert result == "餐飲"

    def test_category_outside_fixed_list_falls_back_to_other(self):
        """AI 若自由生成清單外的類別，不可採信，須回退為「其他」（core rule 5）。"""
        service, mock_client = _make_service()
        mock_client.send_message.return_value = json.dumps({"category": "娛樂"})

        result = service.classify(items=["電影票"])

        assert result == "其他"

    def test_malformed_json_falls_back_to_other(self):
        service, mock_client = _make_service()
        mock_client.send_message.return_value = "不是 JSON"

        result = service.classify(items=["某品項"])

        assert result == "其他"

    def test_empty_items_uses_placeholder_text(self):
        service, mock_client = _make_service()
        mock_client.send_message.return_value = json.dumps({"category": "其他"})

        service.classify(items=[])

        _, kwargs = mock_client.send_message.call_args
        user_text = kwargs["user_content"][0]["text"]
        assert "無品項資訊" in user_text

    def test_amount_included_in_user_content_when_provided(self):
        service, mock_client = _make_service()
        mock_client.send_message.return_value = json.dumps({"category": "交通"})

        service.classify(items=["計程車資"], amount=350)

        _, kwargs = mock_client.send_message.call_args
        user_text = kwargs["user_content"][0]["text"]
        assert "計程車資" in user_text
        assert "350" in user_text

    def test_system_prompt_lists_all_fixed_categories(self):
        service, mock_client = _make_service()
        mock_client.send_message.return_value = json.dumps({"category": "其他"})

        service.classify(items=["某品項"])

        _, kwargs = mock_client.send_message.call_args
        system_prompt = kwargs["system_prompt"]
        for category in EXPENSE_CATEGORIES:
            assert category in system_prompt
