"""民國年轉西元年的單元測試。"""

import pytest
from datetime import date

from utils.date_converter import convert_roc_to_ad


class TestConvertRocToAd:
    """民國年轉換測試。"""

    # --- 斜線分隔格式 ---

    def test_slash_format_standard(self):
        """斜線分隔格式：113/07/08 → 2024-07-08。"""
        assert convert_roc_to_ad("113/07/08") == date(2024, 7, 8)

    def test_slash_format_single_digit(self):
        """斜線分隔格式（單位數月日）：113/1/5 → 2024-01-05。"""
        assert convert_roc_to_ad("113/1/5") == date(2024, 1, 5)

    def test_slash_format_two_digit_year(self):
        """斜線分隔格式（兩位數年份）：89/12/31 → 2000-12-31。"""
        assert convert_roc_to_ad("89/12/31") == date(2000, 12, 31)

    # --- 連字號分隔格式 ---

    def test_dash_format_standard(self):
        """連字號分隔格式：113-07-08 → 2024-07-08。"""
        assert convert_roc_to_ad("113-07-08") == date(2024, 7, 8)

    def test_dash_format_single_digit(self):
        """連字號分隔格式（單位數月日）：115-3-1 → 2026-03-01。"""
        assert convert_roc_to_ad("115-3-1") == date(2026, 3, 1)

    # --- 連續數字格式 ---

    def test_continuous_format(self):
        """連續數字格式：1130708 → 2024-07-08。"""
        assert convert_roc_to_ad("1130708") == date(2024, 7, 8)

    def test_continuous_format_january(self):
        """連續數字格式（一月）：1150101 → 2026-01-01。"""
        assert convert_roc_to_ad("1150101") == date(2026, 1, 1)

    def test_continuous_format_leap_year(self):
        """連續數字格式（閏年 2 月 29 日）：1130229 → 2024-02-29。"""
        assert convert_roc_to_ad("1130229") == date(2024, 2, 29)

    # --- 邊界值 ---

    def test_roc_year_1(self):
        """民國元年：01/01/01 → 1912-01-01。"""
        assert convert_roc_to_ad("01/01/01") == date(1912, 1, 1)

    def test_whitespace_trimmed(self):
        """前後空白應被自動去除。"""
        assert convert_roc_to_ad("  113/07/08  ") == date(2024, 7, 8)

    # --- 錯誤案例 ---

    def test_invalid_format_random_text(self):
        """無法解析的文字應拋出 ValueError。"""
        with pytest.raises(ValueError, match="無法解析"):
            convert_roc_to_ad("不是日期")

    def test_invalid_format_western_date(self):
        """西元年格式（4 位年份）不在支援範圍，應拋出 ValueError。"""
        with pytest.raises(ValueError):
            convert_roc_to_ad("2024/07/08")

    def test_invalid_month_13(self):
        """13 月不合法，應拋出 ValueError。"""
        with pytest.raises(ValueError, match="日期不合法"):
            convert_roc_to_ad("113/13/01")

    def test_invalid_day_32(self):
        """32 日不合法，應拋出 ValueError。"""
        with pytest.raises(ValueError, match="日期不合法"):
            convert_roc_to_ad("113/07/32")

    def test_invalid_non_leap_year_feb29(self):
        """非閏年 2 月 29 日不合法，應拋出 ValueError。"""
        with pytest.raises(ValueError, match="日期不合法"):
            convert_roc_to_ad("1140229")  # 民國 114 年 = 西元 2025 年，非閏年

    def test_empty_string(self):
        """空字串應拋出 ValueError。"""
        with pytest.raises(ValueError):
            convert_roc_to_ad("")

    def test_none_input(self):
        """None 輸入應拋出 ValueError。"""
        with pytest.raises(ValueError):
            convert_roc_to_ad(None)
