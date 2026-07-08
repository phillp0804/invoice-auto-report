"""AI 辨識服務（無 QR Code 時的備援路徑）。

呼叫 Claude Vision API 辨識發票圖片內容，回傳結構化資料與各欄位信心分數。
"""

from PIL import Image

from schemas.invoice_schema import InvoiceRecognitionResult


class OcrService:
    """Claude Vision AI 辨識服務。"""

    def __init__(self, api_key: str):
        """初始化 OcrService。

        Args:
            api_key: Anthropic API 金鑰。
        """
        self.api_key = api_key

    def compress_image(self, image: Image.Image, max_edge: int = 1500) -> Image.Image:
        """壓縮圖片至指定最長邊，降低 Token 消耗。

        Args:
            image: 原始 PIL Image。
            max_edge: 最長邊像素上限（預設 1500px）。

        Returns:
            壓縮後的 PIL Image。
        """
        # TODO: 計算等比縮放尺寸，轉為 JPEG 格式
        raise NotImplementedError

    def recognize(self, image: Image.Image) -> InvoiceRecognitionResult:
        """使用 Claude Vision 辨識發票圖片。

        Args:
            image: PIL Image 物件（應先經過 compress_image 壓縮）。

        Returns:
            辨識結果，包含各欄位信心分數（recognition_method="ai_vision"）。
        """
        # TODO: 將圖片編碼為 base64
        # TODO: 呼叫 Claude API 多模態辨識
        # TODO: 解析 AI 回傳的 JSON，映射為 InvoiceRecognitionResult
        raise NotImplementedError
