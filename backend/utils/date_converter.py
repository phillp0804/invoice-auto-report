"""民國年轉西元年工具。

純函式，無外部依賴，方便撰寫單元測試。
"""

from datetime import date


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
        ValueError: 無法解析的日期格式。
    """
    # TODO: 解析民國年格式，加上 1911 轉為西元年
    raise NotImplementedError
