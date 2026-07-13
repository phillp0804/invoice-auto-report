"""QR Code 偵測與解碼服務（優先辨識路徑）。

負責偵測上傳圖片中是否有 QR Code，若有則解碼為結構化資料。
若偵測不到 QR Code，回傳明確的「無 QR Code」結果，交由 ocr_service 接手。
"""

from PIL import Image
from pyzbar.pyzbar import decode as decode_qr_codes

from schemas.invoice_schema import InvoiceRecognitionResult
from utils.qr_parser import parse_invoice_qr_string


class QrService:
    """QR Code 偵測與解碼服務。"""

    def detect_and_decode(self, image: Image.Image) -> InvoiceRecognitionResult | None:
        """偵測圖片中的 QR Code 並解碼。

        Args:
            image: PIL Image 物件。

        Returns:
            辨識結果（recognition_method="qr_code"），若偵測不到 QR Code、
            或偵測到的 QR Code 不符合電子發票格式，則回傳 None，交由
            ocr_service 接手 AI 辨識備援。
        """
        for symbol in decode_qr_codes(image):
            try:
                qr_string = symbol.data.decode("utf-8")
                qr_data = parse_invoice_qr_string(qr_string)
            except (UnicodeDecodeError, ValueError):
                # 圖片中可能混有非發票用途的 QR Code（例如商家其他宣傳碼），略過並嘗試下一個
                continue

            return InvoiceRecognitionResult(
                invoice_number=qr_data.invoice_number,
                tax_id=qr_data.seller_tax_id,
                buyer_tax_id=qr_data.buyer_tax_id,
                date=qr_data.date,
                amount=float(qr_data.total_amount),
                items=None,
                recognition_method="qr_code",
                field_confidence=None,
            )

        return None
