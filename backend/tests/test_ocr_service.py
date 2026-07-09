"""AI 辨識服務（OcrService）的單元測試（不呼叫真實 Claude API）。"""

import json
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from services.ocr_service import OcrService


def _make_service() -> tuple[OcrService, MagicMock]:
    """建立 OcrService，並回傳其內部 ClaudeClient 的 mock 實例。"""
    with patch("services.ocr_service.ClaudeClient") as mock_claude_client_cls:
        mock_client = MagicMock()
        mock_claude_client_cls.return_value = mock_client
        service = OcrService(api_key="test-key")
    return service, mock_client


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
        service, mock_client = _make_service()
        mock_client.send_message.return_value = json.dumps(
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

    def test_missing_confidence_field_does_not_crash(self):
        service, mock_client = _make_service()
        mock_client.send_message.return_value = json.dumps(
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
        service, mock_client = _make_service()
        mock_client.send_message.return_value = "這不是 JSON"

        with pytest.raises(RuntimeError, match="不是合法 JSON"):
            service.recognize(Image.new("RGB", (500, 500)))

    def test_sends_jpeg_image_content_to_claude(self):
        service, mock_client = _make_service()
        mock_client.send_message.return_value = json.dumps(
            {
                "invoice_number": None,
                "tax_id": None,
                "date": None,
                "amount": None,
                "items": None,
            }
        )

        service.recognize(Image.new("RGB", (500, 500)))

        _, kwargs = mock_client.send_message.call_args
        image_block = kwargs["user_content"][0]
        assert image_block["type"] == "image"
        assert image_block["source"]["media_type"] == "image/jpeg"
        assert image_block["source"]["type"] == "base64"
