"""民國年轉西元年工具。

純函式，無外部依賴，方便撰寫單元測試。
"""

import re
from datetime import date

# 民國元年對應西元 1912 年，因此民國年 + 1911 = 西元年
_ROC_YEAR_OFFSET = 1911

# 支援的日期格式正規表達式
# 分隔格式：113/07/08 或 113-07-08（年份 2~3 碼，月日各 1~2 碼）
_SEPARATED_PATTERN = re.compile(r"^(\d{2,3})[/\-](\d{1,2})[/\-](\d{1,2})$")
# 連續格式：1130708（年份 3 碼 + 月份 2 碼 + 日期 2 碼，共 7 碼）
_CONTINUOUS_PATTERN = re.compile(r"^(\d{3})(\d{2})(\d{2})$")


def convert_roc_to_ad(roc_date_str: str) -> date:
    """將民國年日期字串轉換為西元年 date 物件。

    支援格式：
    - "113/07/08"（民國年/月/日，以斜線分隔）
    - "113-07-08"（民國年-月-日，以連字號分隔）
    - "1130708"（民國年月日連續數字，3位年份+2位月份+2位日期）

    Args:
        roc_date_str: 民國年日期字串。

    Returns:
        轉換後的 Python date 物件。

    Raises:
        ValueError: 無法解析的日期格式或日期不合法。
    """
    if not isinstance(roc_date_str, str):
        raise ValueError(f"輸入必須為字串，收到 {type(roc_date_str).__name__}")

    roc_date_str = roc_date_str.strip()

    # 嘗試分隔格式（斜線或連字號）
    match = _SEPARATED_PATTERN.match(roc_date_str)
    if match:
        roc_year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return _to_date(roc_year, month, day, roc_date_str)

    # 嘗試連續數字格式
    match = _CONTINUOUS_PATTERN.match(roc_date_str)
    if match:
        roc_year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return _to_date(roc_year, month, day, roc_date_str)

    raise ValueError(f"無法解析的民國年日期格式：'{roc_date_str}'")


def _to_date(roc_year: int, month: int, day: int, original: str) -> date:
    """將解析出的民國年、月、日轉換為 date 物件。

    Args:
        roc_year: 民國年份。
        month: 月份。
        day: 日期。
        original: 原始輸入字串（用於錯誤訊息）。

    Returns:
        轉換後的 Python date 物件。

    Raises:
        ValueError: 日期不合法（例如 13 月、32 日）。
    """
    ad_year = roc_year + _ROC_YEAR_OFFSET
    try:
        return date(ad_year, month, day)
    except ValueError:
        raise ValueError(
            f"日期不合法：民國 {roc_year} 年 {month} 月 {day} 日 "
            f"（原始輸入：'{original}'）"
        )
