"""AI 辨識服務（無 QR Code 時的備援路徑）。

呼叫 Claude Vision API 辨識發票圖片內容，回傳結構化資料與各欄位信心分數。
"""

import base64
import io
import json

from PIL import Image

from schemas.invoice_schema import FieldConfidence, InvoiceRecognitionResult
from services.claude_client import ClaudeClient
from services.prompts.recognize_invoice_prompt import RECOGNIZE_INVOICE_SYSTEM_PROMPT
from utils.image_compressor import compress_image as _compress_image


class OcrService:
    """Claude Vision AI 辨識服務。"""

    def __init__(self, api_key: str):
        """初始化 OcrService。

        Args:
            api_key: Anthropic API 金鑰。
        """
        self.claude_client = ClaudeClient(api_key)

    def compress_image(self, image: Image.Image, max_edge: int = 1500) -> Image.Image:
        """壓縮圖片至指定最長邊，降低 Token 消耗。

        實際邏輯在 utils/image_compressor.py（純函式，供本服務與
        storage_service 共用），這裡保留方法介面以維持既有呼叫方式。

        Args:
            image: 原始 PIL Image。
            max_edge: 最長邊像素上限（預設 1500px）。

        Returns:
            壓縮後的 PIL Image（RGB 模式，最長邊不超過 max_edge，不放大原圖）。
        """
        return _compress_image(image, max_edge)

    def recognize(self, image: Image.Image) -> InvoiceRecognitionResult:
        """使用 Claude Vision 辨識發票圖片。

        Args:
            image: PIL Image 物件，內部會先呼叫 compress_image 壓縮再送出辨識。

        Returns:
            辨識結果，包含各欄位信心分數（recognition_method="ai_vision"）。

        Raises:
            RuntimeError: Claude 回傳內容不是合法 JSON。
        """
        compressed = self.compress_image(image)

        buffer = io.BytesIO()
        compressed.save(buffer, format="JPEG")
        image_base64 = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

        response_text = self.claude_client.send_message(
            system_prompt=RECOGNIZE_INVOICE_SYSTEM_PROMPT,
            user_content=[
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64,
                    },
                },
                {"type": "text", "text": "請辨識這張發票圖片的內容。"},
            ],
        )

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Claude 回傳的辨識結果不是合法 JSON：{response_text}"
            ) from exc

        confidence_data = data.get("confidence") or {}

        return InvoiceRecognitionResult(
            invoice_number=data.get("invoice_number"),
            tax_id=data.get("tax_id"),
            date=data.get("date"),
            amount=data.get("amount"),
            items=data.get("items"),
            recognition_method="ai_vision",
            field_confidence=FieldConfidence(
                invoice_number=confidence_data.get("invoice_number"),
                tax_id=confidence_data.get("tax_id"),
                date=confidence_data.get("date"),
                amount=confidence_data.get("amount"),
                items=confidence_data.get("items"),
            ),
        )
