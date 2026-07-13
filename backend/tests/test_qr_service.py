"""QR Code 偵測與解碼服務的單元測試。"""

from unittest.mock import patch

from pyzbar.pyzbar import Decoded

from services.qr_service import QrService


def _build_qr_string(
    invoice_number: str = "AB12345678",
    date: str = "1130708",
    random_code: str = "1234",
    sales_hex: str = "000003E8",
    total_hex: str = "0000041A",
    buyer_tax_id: str = "00000000",
    seller_tax_id: str = "04595257",
    encrypt_info: str = "ABCDEFGHIJKLMNOPQRSTUVWX",
) -> str:
    """建構符合財政部規範的 QR Code 字串（冒號分隔）。"""
    return ":".join(
        [
            invoice_number + date + random_code,
            sales_hex + total_hex,
            buyer_tax_id + seller_tax_id,
            encrypt_info,
        ]
    )


def _decoded(data: bytes) -> Decoded:
    """建構 pyzbar 解碼結果，僅 data 欄位對 QrService 有意義。"""
    return Decoded(data=data, type="QRCODE", rect=None, polygon=None, quality=0, orientation=None)


class TestQrServiceDetectAndDecode:
    """detect_and_decode() 測試。"""

    def setup_method(self):
        self.service = QrService()

    def test_valid_qr_code_returns_recognition_result(self):
        """偵測到符合規範的 QR Code 應回傳結構化辨識結果。"""
        qr_bytes = _build_qr_string().encode("utf-8")
        with patch("services.qr_service.decode_qr_codes", return_value=[_decoded(qr_bytes)]):
            result = self.service.detect_and_decode(image=object())

        assert result is not None
        assert result.invoice_number == "AB12345678"
        assert result.tax_id == "04595257"
        assert result.buyer_tax_id == "00000000"
        assert result.date == "1130708"
        assert result.amount == float(0x41A)
        assert result.recognition_method == "qr_code"
        assert result.field_confidence is None

    def test_buyer_tax_id_passed_through_when_present(self):
        """買方統編非 00000000（例如公司報帳開立抬頭）時應正確帶出。"""
        qr_bytes = _build_qr_string(buyer_tax_id="12345675").encode("utf-8")
        with patch("services.qr_service.decode_qr_codes", return_value=[_decoded(qr_bytes)]):
            result = self.service.detect_and_decode(image=object())

        assert result is not None
        assert result.buyer_tax_id == "12345675"

    def test_no_qr_code_detected_returns_none(self):
        """圖片中沒有 QR Code 時應回傳 None，交由 AI 辨識備援。"""
        with patch("services.qr_service.decode_qr_codes", return_value=[]):
            result = self.service.detect_and_decode(image=object())

        assert result is None

    def test_qr_code_not_invoice_format_returns_none(self):
        """QR Code 內容不符合電子發票格式時應回傳 None。"""
        with patch(
            "services.qr_service.decode_qr_codes",
            return_value=[_decoded(b"https://example.com/not-an-invoice")],
        ):
            result = self.service.detect_and_decode(image=object())

        assert result is None

    def test_skips_non_invoice_qr_and_uses_valid_one(self):
        """圖片中混有多個 QR Code 時，應略過不符格式者，採用符合格式的發票 QR Code。"""
        qr_bytes = _build_qr_string(invoice_number="CD87654321").encode("utf-8")
        decoded_list = [
            _decoded(b"https://example.com/promo"),
            _decoded(qr_bytes),
        ]
        with patch("services.qr_service.decode_qr_codes", return_value=decoded_list):
            result = self.service.detect_and_decode(image=object())

        assert result is not None
        assert result.invoice_number == "CD87654321"

    def test_non_utf8_qr_data_returns_none(self):
        """QR Code 資料無法以 UTF-8 解碼時應視為非發票格式，回傳 None。"""
        with patch(
            "services.qr_service.decode_qr_codes",
            return_value=[_decoded(b"\xff\xfe\xfd")],
        ):
            result = self.service.detect_and_decode(image=object())

        assert result is None
