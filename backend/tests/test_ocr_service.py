"""AI 辨識服務（OcrService）的單元測試（不呼叫真實 AI API）。"""

import json
from unittest.mock import MagicMock

import pytest
from PIL import Image

from services.ocr_service import OcrService


def _make_service() -> tuple[OcrService, MagicMock]:
    """建立 OcrService，注入一個 mock 的 ai_client（介面與 ClaudeClient/GeminiClient 一致）。"""
    mock_ai_client = MagicMock()
    service = OcrService(ai_client=mock_ai_client)
    return service, mock_ai_client


class TestCompressImage:
    """compress_image() 測試：完整案例已移至 test_image_compressor.py，
    這裡只驗證 OcrService 有正確委派給 utils.image_compressor。"""

    def setup_method(self):
        self.service, _ = _make_service()

    def test_delegates_to_utils_image_compressor(self):
        image = Image.new("RGB", (3000, 1500))
        result = self.service.compress_image(image, max_edge=1500)

        assert max(result.size) == 1500


class TestRecognize:
    """recognize() 測試。"""

    def test_valid_response_maps_to_recognition_result(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_image.return_value = json.dumps(
            {
                "invoice_number": "AB12345678",
                "tax_id": "04595257",
                "date": "113/07/08",
                "amount": 1050,
                "items": ["午餐"],
                "confidence": {
                    "invoice_number": "high",
                    "tax_id": "high",
                    "date": "medium",
                    "amount": "high",
                    "items": "low",
                },
            }
        )

        result = service.recognize(Image.new("RGB", (500, 500)))

        assert result.invoice_number == "AB12345678"
        assert result.tax_id == "04595257"
        assert result.amount == 1050
        assert result.items == ["午餐"]
        assert result.recognition_method == "ai_vision"
        assert result.field_confidence.invoice_number == "high"
        assert result.field_confidence.items == "low"

    def test_response_wrapped_in_markdown_code_fence_still_parses(self):
        """迴歸測試：Gemini 實測會把 JSON 包在 ```json ... ``` 裡，即使
        prompt 要求「僅輸出 JSON」，這裡確保這種格式不會導致辨識失敗。"""
        service, mock_ai_client = _make_service()
        raw_json = json.dumps(
            {
                "invoice_number": "AB12345678",
                "tax_id": None,
                "date": None,
                "amount": None,
                "items": None,
            }
        )
        mock_ai_client.send_image.return_value = f"```json\n{raw_json}\n```"

        result = service.recognize(Image.new("RGB", (500, 500)))

        assert result.invoice_number == "AB12345678"

    def test_missing_buyer_tax_id_defaults_to_all_zero(self):
        """依財政部規範，一般消費者未提供買方統編時預設為 00000000，不可回傳 None。"""
        service, mock_ai_client = _make_service()
        mock_ai_client.send_image.return_value = json.dumps(
            {
                "invoice_number": "AB12345678",
                "tax_id": None,
                "buyer_tax_id": None,
                "date": None,
                "amount": None,
                "items": None,
            }
        )

        result = service.recognize(Image.new("RGB", (500, 500)))

        assert result.buyer_tax_id == "00000000"

    def test_missing_confidence_field_does_not_crash(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_image.return_value = json.dumps(
            {
                "invoice_number": None,
                "tax_id": None,
                "date": None,
                "amount": None,
                "items": None,
            }
        )

        result = service.recognize(Image.new("RGB", (500, 500)))

        assert result.field_confidence.invoice_number is None
        assert result.invoice_number is None

    def test_invalid_json_raises_runtime_error(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_image.return_value = "這不是 JSON"

        with pytest.raises(RuntimeError, match="不是合法 JSON"):
            service.recognize(Image.new("RGB", (500, 500)))

    def test_sends_jpeg_image_to_ai_client(self):
        service, mock_ai_client = _make_service()
        mock_ai_client.send_image.return_value = json.dumps(
            {
                "invoice_number": None,
                "tax_id": None,
                "date": None,
                "amount": None,
                "items": None,
            }
        )

        service.recognize(Image.new("RGB", (500, 500)))

        _, kwargs = mock_ai_client.send_image.call_args
        assert kwargs["media_type"] == "image/jpeg"
        assert isinstance(kwargs["image_bytes"], bytes)
        assert kwargs["user_text"]
