"""電子發票 QR Code 解析器的單元測試。"""

import pytest

from utils.qr_parser import parse_invoice_qr_string, InvoiceQrData


class TestParseInvoiceQrString:
    """QR Code 解析測試。"""

    def test_valid_qr_string(self):
        """合法的 QR Code 字串應正確解析。"""
        # TODO: 使用符合財政部規範的 QR Code 字串測試
        pass

    def test_invalid_qr_string(self):
        """不合規範的字串應拋出 ValueError。"""
        # TODO: 測試不合法的 QR Code 字串
        pass

    def test_no_buyer_tax_id(self):
        """無買方統編時應填入預設值 "00000000"。"""
        # TODO: 測試無買方統編的情況
        pass
