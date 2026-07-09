"""Claude API 共用客戶端的單元測試（不呼叫真實 API，全部使用 mock）。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from anthropic import APIError

from services.claude_client import ClaudeClient


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


class TestClaudeClientInit:
    """初始化行為測試。"""

    def test_creates_anthropic_client_with_api_key_and_retries(self):
        with patch("services.claude_client.anthropic.Anthropic") as mock_anthropic:
            ClaudeClient(api_key="test-key")

        mock_anthropic.assert_called_once_with(api_key="test-key", max_retries=2)


class TestSendMessage:
    """send_message() 測試。"""

    def test_returns_concatenated_text_blocks(self):
        with patch("services.claude_client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = SimpleNamespace(
                content=[_text_block("Hello, "), _text_block("world!")]
            )

            service = ClaudeClient(api_key="test-key")
            result = service.send_message(
                system_prompt="system", user_content=[{"type": "text", "text": "hi"}]
            )

        assert result == "Hello, world!"

    def test_ignores_non_text_blocks(self):
        with patch("services.claude_client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = SimpleNamespace(
                content=[
                    SimpleNamespace(type="thinking", thinking="..."),
                    _text_block("final answer"),
                ]
            )

            service = ClaudeClient(api_key="test-key")
            result = service.send_message(system_prompt="s", user_content=[])

        assert result == "final answer"

    def test_sends_expected_request_params(self):
        with patch("services.claude_client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = SimpleNamespace(
                content=[_text_block("ok")]
            )

            service = ClaudeClient(api_key="test-key")
            service.send_message(
                system_prompt="你是發票辨識助手",
                user_content=[{"type": "text", "text": "辨識這張發票"}],
                max_tokens=2048,
            )

        mock_client.messages.create.assert_called_once_with(
            model="claude-opus-4-8",
            max_tokens=2048,
            system="你是發票辨識助手",
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "辨識這張發票"}],
                }
            ],
        )

    def test_api_error_wrapped_as_runtime_error(self):
        with patch("services.claude_client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            mock_client.messages.create.side_effect = APIError(
                "rate limit exceeded", request, body=None
            )

            service = ClaudeClient(api_key="test-key")
            with pytest.raises(RuntimeError, match="Claude API 呼叫失敗"):
                service.send_message(system_prompt="s", user_content=[])
