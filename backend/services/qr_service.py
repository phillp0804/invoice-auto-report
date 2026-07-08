"""QR Code 偵測與解碼服務（優先辨識路徑）。

負責偵測上傳圖片中是否有 QR Code，若有則解碼為結構化資料。
若偵測不到 QR Code，回傳明確的「無 QR Code」結果，交由 ocr_service 接手。
"""

from PIL import Image

from schemas.invoice_schema import InvoiceRecognitionResult
from utils.qr_parser import parse_invoice_qr_string


class QrService:
    """QR Code 偵測與解碼服務。"""

    def detect_and_decode(self, image: Image.Image) -> InvoiceRecognitionResult | None:
        """偵測圖片中的 QR Code 並解碼。

        Args:
            image: PIL Image 物件。

        Returns:
            辨識結果（recognition_method="qr_code"），若無 QR Code 則回傳 None。
        """
        # TODO: 使用 pyzbar 偵測 QR Code
        # TODO: 若偵測到，呼叫 parse_invoice_qr_string 解析
        # TODO: 回傳 InvoiceRecognitionResult（field_confidence=None，視為 100% 可信）
        raise NotImplementedError
