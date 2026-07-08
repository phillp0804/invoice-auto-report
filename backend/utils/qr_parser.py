"""電子發票 QR Code 字串解析器。

純函式，將 QR Code 解碼後的原始字串依財政部規範解析為結構化資料。
"""

from dataclasses import dataclass


@dataclass
class InvoiceQrData:
    """QR Code 解析後的結構化資料。"""

    invoice_number: str  # 發票號碼（例如 "AB12345678"）
    date: str  # 日期（民國年，例如 "1130708"）
    random_code: str  # 隨機碼（4位）
    seller_tax_id: str  # 賣方統編
    buyer_tax_id: str  # 買方統編（無則為 "00000000"）
    total_amount: int  # 總金額


def parse_invoice_qr_string(qr_string: str) -> InvoiceQrData:
    """解析電子發票 QR Code 字串為結構化資料。

    依財政部電子發票 QR Code 編碼規範解析各欄位。

    Args:
        qr_string: QR Code 解碼後的原始字串。

    Returns:
        InvoiceQrData 結構化資料。

    Raises:
        ValueError: QR Code 字串格式不符規範。
    """
    # TODO: 依財政部規範切割並解析 QR Code 字串
    raise NotImplementedError
