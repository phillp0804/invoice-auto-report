"""AI 廠商選擇工廠函式（create_ai_client）的單元測試。"""

from unittest.mock import MagicMock, patch

import pytest

from services.ai_client import create_ai_client


class TestCreateAiClient:
    """create_ai_client() 測試。"""

    def test_defaults_to_claude(self):
        settings = MagicMock(ai_provider="claude", anthropic_api_key="claude-key")

        with patch("services.ai_client.ClaudeClient") as mock_claude_cls:
            client = create_ai_client(settings)

        mock_claude_cls.assert_called_once_with(api_key="claude-key")
        assert client is mock_claude_cls.return_value

    def test_selects_gemini_when_configured(self):
        settings = MagicMock(
            ai_provider="gemini", gemini_api_key="gemini-key", gemini_model="gemini-2.5-flash"
        )

        with patch("services.ai_client.GeminiClient") as mock_gemini_cls:
            client = create_ai_client(settings)

        mock_gemini_cls.assert_called_once_with(api_key="gemini-key", model="gemini-2.5-flash")
        assert client is mock_gemini_cls.return_value

    def test_unsupported_provider_raises_value_error(self):
        settings = MagicMock(ai_provider="openai")

        with pytest.raises(ValueError, match="不支援的 AI_PROVIDER"):
            create_ai_client(settings)
