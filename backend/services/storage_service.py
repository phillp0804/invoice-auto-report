"""發票圖片備份儲存服務。

將辨識完成的發票圖片壓縮後存到本機磁碟，檔名依
「[員工姓名][發票日期][發票號碼]」規則命名，方便總務事後人工核對原始圖片。
"""

import re
from datetime import date as date_cls
from pathlib import Path

from PIL import Image

from config import get_settings
from utils.image_compressor import compress_image

# 檔名只允許文字/數字/底線/連字號（\w 在預設 Unicode 模式下已涵蓋中文字），
# 其餘字元（含路徑分隔符 / \、..等）一律替換為底線，
# 避免員工姓名或發票號碼混入特殊字元造成路徑穿越或無效檔名
_UNSAFE_CHARS = re.compile(r"[^\w\-]+")


def _sanitize(value: str) -> str:
    """將字串轉為檔名安全片段：去除頭尾空白，非允許字元合併換成底線。"""
    sanitized = _UNSAFE_CHARS.sub("_", value.strip()).strip("_")
    return sanitized or "unknown"


def build_invoice_filename(
    employee_name: str,
    invoice_number: str,
    invoice_date: date_cls | None,
    fallback_date: date_cls | None = None,
) -> str:
    """依「[姓名][日期][發票號碼]」規則組出檔名（不含副檔名）。

    Args:
        employee_name: 上傳員工姓名。
        invoice_number: 發票號碼。
        invoice_date: 辨識/確認後的發票日期，優先使用。
        fallback_date: invoice_date 缺失時使用（通常為上傳當天）；
            兩者皆缺時退回今天日期。

    Returns:
        檔名字串（不含副檔名），例如 "王小明_20240708_AB12345678"。
    """
    effective_date = invoice_date or fallback_date or date_cls.today()
    return "_".join(
        [
            _sanitize(employee_name),
            effective_date.strftime("%Y%m%d"),
            _sanitize(invoice_number),
        ]
    )


def save_invoice_image(image: Image.Image, base_filename: str) -> str:
    """壓縮圖片並存到 UPLOAD_DIR，回傳相對路徑（存入 Invoice.image_url）。

    圖片會先壓縮（沿用 utils/image_compressor 的規則）再落地，
    控制備份檔案占用空間。若檔名已存在（例如同一天同員工同發票號碼
    重複上傳），自動加上流水號尾碼避免覆蓋既有備份檔案。

    Args:
        image: 原始 PIL Image。
        base_filename: build_invoice_filename() 產生的檔名（不含副檔名）。

    Returns:
        相對於 backend 執行目錄的圖片路徑字串。
    """
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    path = upload_dir / f"{base_filename}.jpg"
    suffix = 2
    while path.exists():
        path = upload_dir / f"{base_filename}_{suffix}.jpg"
        suffix += 1

    compressed = compress_image(image)
    compressed.save(path, format="JPEG")

    return path.as_posix()
