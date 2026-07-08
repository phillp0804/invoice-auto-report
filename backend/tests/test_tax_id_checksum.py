"""統編檢查碼驗證演算法的單元測試。"""

import pytest

from utils.tax_id_checksum import validate_tax_id


class TestValidateTaxId:
    """統一編號驗證測試。"""

    def test_valid_tax_id(self):
        """合法統編應回傳 True。"""
        # TODO: 填入合法統編案例
        pass

    def test_invalid_tax_id(self):
        """不合法統編應回傳 False。"""
        # TODO: 填入不合法統編案例
        pass

    def test_invalid_length(self):
        """長度不為 8 的字串應回傳 False。"""
        # TODO: 測試長度錯誤的情況
        pass

    def test_non_numeric(self):
        """包含非數字字元的字串應回傳 False。"""
        # TODO: 測試非數字輸入
        pass
