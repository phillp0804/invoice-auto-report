"""民國年轉西元年的單元測試。"""

import pytest
from datetime import date

from utils.date_converter import convert_roc_to_ad


class TestConvertRocToAd:
    """民國年轉換測試。"""

    def test_slash_format(self):
        """斜線分隔格式（例如 "113/07/08"）。"""
        # TODO: 測試 "113/07/08" → date(2024, 7, 8)
        pass

    def test_dash_format(self):
        """連字號分隔格式（例如 "113-07-08"）。"""
        # TODO: 測試 "113-07-08" → date(2024, 7, 8)
        pass

    def test_continuous_format(self):
        """連續數字格式（例如 "1130708"）。"""
        # TODO: 測試 "1130708" → date(2024, 7, 8)
        pass

    def test_invalid_format(self):
        """無法解析的格式應拋出 ValueError。"""
        # TODO: 測試不合法的日期字串
        pass
