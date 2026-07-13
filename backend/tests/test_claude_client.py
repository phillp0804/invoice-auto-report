"""Claude API 共用客戶端的單元測試（不呼叫真實 API，全部使用 mock）。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from anthropic import APIError, RateLimitError

from services.ai_errors import AiQuotaExceededError
from services.claude_client import ClaudeClient


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _make_client():
    with patch("services.claude_client.anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        service = ClaudeClient(api_key="test-key")
    return service, mock_client


class TestClaudeClientInit:
    """初始化行為測試。"""

    def test_creates_anthropic_client_with_api_key_and_retries(self):
        with patch("services.claude_client.anthropic.Anthropic") as mock_anthropic:
            ClaudeClient(api_key="test-key")

        mock_anthropic.assert_called_once_with(api_key="test-key", max_retries=2)


class TestSendText:
    """send_text() 測試。"""

    def test_returns_concatenated_text_blocks(self):
        service, mock_client = _make_client()
        mock_client.messages.create.return_value = SimpleNamespace(
            content=[_text_block("Hello, "), _text_block("world!")]
        )

        result = service.send_text(system_prompt="system", user_text="hi")

        assert result == "Hello, world!"

    def test_ignores_non_text_blocks(self):
        service, mock_client = _make_client()
        mock_client.messages.create.return_value = SimpleNamespace(
            content=[
                SimpleNamespace(type="thinking", thinking="..."),
                _text_block("final answer"),
            ]
        )

        result = service.send_text(system_prompt="s", user_text="")

        assert result == "final answer"

    def test_sends_expected_request_params(self):
        service, mock_client = _make_client()
        mock_client.messages.create.return_value = SimpleNamespace(content=[_text_block("ok")])

        service.send_text(system_prompt="你是發票辨識助手", user_text="辨識這張發票", max_tokens=2048)

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
        service, mock_client = _make_client()
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        mock_client.messages.create.side_effect = APIError(
            "internal error", request, body=None
        )

        with pytest.raises(RuntimeError, match="Claude API 呼叫失敗"):
            service.send_text(system_prompt="s", user_text="")

    def test_rate_limit_error_wrapped_as_ai_quota_exceeded_error(self):
        """429（額度/速率限制達上限）應拋出 AiQuotaExceededError，方便呼叫端分開處理。"""
        service, mock_client = _make_client()
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        response = httpx.Response(429, request=request)
        mock_client.messages.create.side_effect = RateLimitError(
            "rate limit exceeded", response=response, body=None
        )

        with pytest.raises(AiQuotaExceededError, match="Claude API 額度已用完"):
            service.send_text(system_prompt="s", user_text="")


class TestSendImage:
    """send_image() 測試。"""

    def test_sends_image_and_text_content_blocks(self):
        service, mock_client = _make_client()
        mock_client.messages.create.return_value = SimpleNamespace(content=[_text_block("ok")])

        result = service.send_image(
            system_prompt="system",
            image_bytes=b"\xff\xd8\xff",
            media_type="image/jpeg",
            user_text="請辨識這張發票圖片的內容。",
            max_tokens=512,
        )

        assert result == "ok"
        _, kwargs = mock_client.messages.create.call_args
        content = kwargs["messages"][0]["content"]
        assert content[0]["type"] == "image"
        assert content[0]["source"]["media_type"] == "image/jpeg"
        assert content[0]["source"]["type"] == "base64"
        assert content[1] == {"type": "text", "text": "請辨識這張發票圖片的內容。"}
