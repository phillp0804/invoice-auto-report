"""電子發票 QR Code 解析器的單元測試。"""

import pytest

from utils.qr_parser import parse_invoice_qr_string, InvoiceQrData


# --- 測試用 QR Code 字串建構輔助 ---
# 依財政部規範：發票號碼(10) + 日期(7) + 隨機碼(4) + 銷售額hex(8) + 總計額hex(8)
#              + 買方統編(8) + 賣方統編(8) + 加密驗證(24)
# 各欄位以冒號分隔

def _build_qr(
    invoice_number: str = "AB12345678",
    date: str = "1130708",
    random_code: str = "1234",
    sales_hex: str = "000003E8",   # 1000 元（未稅）
    total_hex: str = "0000041A",   # 1050 元（含稅）
    buyer_tax_id: str = "00000000",
    seller_tax_id: str = "04595257",
    encrypt_info: str = "ABCDEFGHIJKLMNOPQRSTUVWX",  # 24 碼假資料
) -> str:
    """建構符合財政部規範的 QR Code 字串（冒號分隔）。"""
    return ":".join([
        invoice_number + date + random_code,
        sales_hex + total_hex,
        buyer_tax_id + seller_tax_id,
        encrypt_info,
    ])


class TestParseInvoiceQrString:
    """QR Code 解析測試。"""

    # --- 正常解析 ---

    def test_valid_qr_string_standard(self):
        """標準 QR Code 字串應正確解析所有欄位。"""
        qr = _build_qr()
        result = parse_invoice_qr_string(qr)

        assert result.invoice_number == "AB12345678"
        assert result.date == "1130708"
        assert result.random_code == "1234"
        assert result.sales_amount == 0x3E8    # 1000
        assert result.total_amount == 0x41A    # 1050
        assert result.buyer_tax_id == "00000000"
        assert result.seller_tax_id == "04595257"

    def test_valid_qr_with_buyer_tax_id(self):
        """有買方統編的發票應正確解析。"""
        qr = _build_qr(buyer_tax_id="22099131")
        result = parse_invoice_qr_string(qr)

        assert result.buyer_tax_id == "22099131"

    def test_no_buyer_tax_id(self):
        """一般消費者（無買方統編）應填入 00000000。"""
        qr = _build_qr(buyer_tax_id="00000000")
        result = parse_invoice_qr_string(qr)

        assert result.buyer_tax_id == "00000000"

    def test_total_amount_hex_conversion(self):
        """金額應從十六進位正確轉為十進位。"""
        # 0x000186A0 = 100000（十萬元）
        qr = _build_qr(sales_hex="0000C350", total_hex="000186A0")
        result = parse_invoice_qr_string(qr)

        assert result.sales_amount == 50000
        assert result.total_amount == 100000

    def test_invoice_number_uppercase(self):
        """發票字軌應自動轉為大寫。"""
        qr = _build_qr(invoice_number="ab12345678")
        result = parse_invoice_qr_string(qr)

        assert result.invoice_number == "AB12345678"

    def test_whitespace_trimmed(self):
        """前後空白應被自動去除。"""
        qr = "  " + _build_qr() + "  "
        result = parse_invoice_qr_string(qr)

        assert result.invoice_number == "AB12345678"

    def test_zero_amount(self):
        """金額為 0 時應正確解析。"""
        qr = _build_qr(sales_hex="00000000", total_hex="00000000")
        result = parse_invoice_qr_string(qr)

        assert result.sales_amount == 0
        assert result.total_amount == 0

    def test_extra_data_after_fixed_fields(self):
        """固定區段後有額外資料（品項明細等）應不影響解析。"""
        qr = _build_qr() + ":extra:data:here"
        result = parse_invoice_qr_string(qr)

        assert result.invoice_number == "AB12345678"
        assert result.total_amount == 0x41A

    # --- 格式錯誤 ---

    def test_empty_string(self):
        """空字串應拋出 ValueError。"""
        with pytest.raises(ValueError, match="不可為空"):
            parse_invoice_qr_string("")

    def test_none_input(self):
        """None 輸入應拋出 ValueError。"""
        with pytest.raises(ValueError, match="不可為空"):
            parse_invoice_qr_string(None)

    def test_too_short(self):
        """字串太短應拋出 ValueError。"""
        with pytest.raises(ValueError, match="長度不足"):
            parse_invoice_qr_string("AB12345678113070812340000")

    def test_invalid_invoice_number_no_alpha(self):
        """發票號碼缺少英文字軌應拋出 ValueError。"""
        qr = _build_qr(invoice_number="1234567890")
        with pytest.raises(ValueError, match="發票號碼格式不合法"):
            parse_invoice_qr_string(qr)

    def test_invalid_invoice_number_wrong_digits(self):
        """發票號碼數字部分含英文應拋出 ValueError。"""
        qr = _build_qr(invoice_number="AB1234ABCD")
        with pytest.raises(ValueError, match="發票號碼格式不合法"):
            parse_invoice_qr_string(qr)

    def test_random_garbage_string(self):
        """隨機亂碼應拋出 ValueError。"""
        with pytest.raises(ValueError):
            parse_invoice_qr_string("這不是一個有效的QR Code字串")
