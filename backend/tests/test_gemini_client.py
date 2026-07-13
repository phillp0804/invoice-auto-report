"""Gemini API 共用客戶端的單元測試（不呼叫真實 API，全部使用 mock）。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from google.genai import errors as genai_errors

from services.ai_errors import AiQuotaExceededError
from services.gemini_client import GeminiClient


def _make_client():
    with patch("services.gemini_client.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        service = GeminiClient(api_key="test-key", model="gemini-2.5-flash")
    return service, mock_client, mock_client_cls


class TestGeminiClientInit:
    """初始化行為測試。"""

    def test_creates_genai_client_with_api_key(self):
        _, _, mock_client_cls = _make_client()

        mock_client_cls.assert_called_once_with(api_key="test-key")


class TestSendText:
    """send_text() 測試。"""

    def test_returns_response_text(self):
        service, mock_client, _ = _make_client()
        mock_client.models.generate_content.return_value = SimpleNamespace(text="分類結果")

        result = service.send_text(system_prompt="system", user_text="品項：午餐")

        assert result == "分類結果"

    def test_sends_expected_request_params(self):
        service, mock_client, _ = _make_client()
        mock_client.models.generate_content.return_value = SimpleNamespace(text="ok")

        service.send_text(system_prompt="你是分類助手", user_text="品項：午餐", max_tokens=256)

        _, kwargs = mock_client.models.generate_content.call_args
        assert kwargs["model"] == "gemini-2.5-flash"
        assert kwargs["contents"] == ["品項：午餐"]
        assert kwargs["config"].system_instruction == "你是分類助手"
        assert kwargs["config"].max_output_tokens == 256

    def test_none_response_text_returns_empty_string(self):
        """Gemini 有時會在被安全機制擋下時回傳 text=None，不應該讓呼叫端拿到 None。"""
        service, mock_client, _ = _make_client()
        mock_client.models.generate_content.return_value = SimpleNamespace(text=None)

        result = service.send_text(system_prompt="s", user_text="u")

        assert result == ""

    def test_api_error_wrapped_as_runtime_error(self):
        service, mock_client, _ = _make_client()
        mock_client.models.generate_content.side_effect = genai_errors.APIError(
            500, {"error": {"message": "internal error"}}
        )

        with pytest.raises(RuntimeError, match="Gemini API 呼叫失敗"):
            service.send_text(system_prompt="s", user_text="u")

    def test_quota_exceeded_wrapped_as_ai_quota_exceeded_error(self):
        """429（額度/速率限制達上限）應拋出 AiQuotaExceededError，方便呼叫端分開處理。"""
        service, mock_client, _ = _make_client()
        mock_client.models.generate_content.side_effect = genai_errors.APIError(
            429, {"error": {"message": "quota exceeded"}}
        )

        with pytest.raises(AiQuotaExceededError, match="Gemini API 額度已用完"):
            service.send_text(system_prompt="s", user_text="u")


class TestSendImage:
    """send_image() 測試。"""

    def test_sends_image_part_and_text(self):
        service, mock_client, _ = _make_client()
        mock_client.models.generate_content.return_value = SimpleNamespace(text="ok")

        result = service.send_image(
            system_prompt="system",
            image_bytes=b"\xff\xd8\xff",
            media_type="image/jpeg",
            user_text="請辨識這張發票圖片的內容。",
        )

        assert result == "ok"
        _, kwargs = mock_client.models.generate_content.call_args
        contents = kwargs["contents"]
        assert len(contents) == 2
        assert contents[0].inline_data.mime_type == "image/jpeg"
        assert contents[0].inline_data.data == b"\xff\xd8\xff"
        assert contents[1] == "請辨識這張發票圖片的內容。"
