"""電子發票 QR Code 字串解析器。

純函式，將 QR Code 解碼後的原始字串依財政部規範解析為結構化資料。
本模組僅處理左側 QR Code（包含發票核心資訊）。

財政部電子發票左側 QR Code 編碼規範：
- 欄位之間以冒號「:」分隔
- 前 77 碼為固定格式的表頭資訊，各欄位依序為：
  | 欄位       | 長度 | 說明                                      |
  |-----------|------|------------------------------------------|
  | 發票號碼    | 10   | 字軌 2 碼 + 數字 8 碼（例如 AB12345678）     |
  | 開立日期    |  7   | 民國年 YYYMMDD（例如 1130708）              |
  | 隨機碼     |  4   | 4 位純數字                                 |
  | 銷售額     |  8   | 未稅金額，16 進位（無法分離時填 00000000）     |
  | 總計額     |  8   | 含稅總金額，16 進位                          |
  | 買方統編    |  8   | 一般消費者填 00000000                       |
  | 賣方統編    |  8   | 賣方統一編號                                |
  | 加密驗證    | 24   | AES 加密 + Base64 編碼                     |
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
    total_amount: int  # 含稅總金額
    sales_amount: int  # 未稅銷售額（無法分離時為 0）


# 各欄位在固定區段中的起始位置與長度（前 77 碼，不含冒號分隔符）
_FIELD_SPEC = {
    "invoice_number": (0, 10),   # 字軌 2 碼 + 數字 8 碼
    "date":           (10, 7),   # 民國年 YYYMMDD
    "random_code":    (17, 4),   # 4 位隨機碼
    "sales_amount":   (21, 8),   # 未稅金額（16 進位）
    "total_amount":   (29, 8),   # 含稅總金額（16 進位）
    "buyer_tax_id":   (37, 8),   # 買方統編
    "seller_tax_id":  (45, 8),   # 賣方統編
    "encrypt_info":   (53, 24),  # 加密驗證資訊
}

# 固定區段總長度（不含冒號）
_FIXED_LENGTH = 77


def parse_invoice_qr_string(qr_string: str) -> InvoiceQrData:
    """解析電子發票左側 QR Code 字串為結構化資料。

    依財政部電子發票 QR Code 編碼規範解析各欄位。
    欄位之間以冒號分隔，去除冒號後前 77 碼為固定格式。

    Args:
        qr_string: QR Code 解碼後的原始字串。

    Returns:
        InvoiceQrData 結構化資料。

    Raises:
        ValueError: QR Code 字串格式不符規範。
    """
    if not isinstance(qr_string, str) or not qr_string.strip():
        raise ValueError("QR Code 字串不可為空")

    qr_string = qr_string.strip()

    # 去除冒號分隔符，取得連續字串
    # 財政部規範以冒號分隔各欄位，但各欄位長度固定
    raw = qr_string.replace(":", "")

    if len(raw) < _FIXED_LENGTH:
        raise ValueError(
            f"QR Code 字串長度不足：去除冒號後為 {len(raw)} 碼，"
            f"需至少 {_FIXED_LENGTH} 碼"
        )

    # 切割各欄位
    invoice_number = raw[0:10]
    date_str = raw[10:17]
    random_code = raw[17:21]
    sales_hex = raw[21:29]
    total_hex = raw[29:37]
    buyer_tax_id = raw[37:45]
    seller_tax_id = raw[45:53]

    # 驗證發票號碼格式：2 碼英文字軌 + 8 碼數字
    if len(invoice_number) != 10:
        raise ValueError(
            f"發票號碼格式不合法：'{invoice_number}'，"
            "應為 10 碼（2 碼英文字軌 + 8 碼數字）"
        )

    if not (invoice_number[:2].isalpha() and invoice_number[2:].isdigit()):
        raise ValueError(
            f"發票號碼格式不合法：'{invoice_number}'，"
            "應為 2 碼英文字軌 + 8 碼數字"
        )

    # 驗證日期格式：7 碼純數字（YYYMMDD）
    if not date_str.isdigit() or len(date_str) != 7:
        raise ValueError(f"日期格式不合法：'{date_str}'，應為 7 碼數字（YYYMMDD）")

    # 驗證隨機碼：4 碼純數字
    if not random_code.isdigit() or len(random_code) != 4:
        raise ValueError(f"隨機碼格式不合法：'{random_code}'，應為 4 碼數字")

    # 驗證統編格式：8 碼純數字
    if not seller_tax_id.isdigit():
        raise ValueError(f"賣方統編格式不合法：'{seller_tax_id}'")
    if not buyer_tax_id.isdigit():
        raise ValueError(f"買方統編格式不合法：'{buyer_tax_id}'")

    # 解析金額（16 進位轉 10 進位）
    try:
        sales_amount = int(sales_hex, 16)
    except ValueError:
        raise ValueError(f"銷售額格式不合法：'{sales_hex}'，應為 8 碼十六進位")

    try:
        total_amount = int(total_hex, 16)
    except ValueError:
        raise ValueError(f"總計額格式不合法：'{total_hex}'，應為 8 碼十六進位")

    return InvoiceQrData(
        invoice_number=invoice_number.upper(),
        date=date_str,
        random_code=random_code,
        seller_tax_id=seller_tax_id,
        buyer_tax_id=buyer_tax_id,
        total_amount=total_amount,
        sales_amount=sales_amount,
    )
