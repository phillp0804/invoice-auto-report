"""驗證服務的單元測試。"""

import pytest

from services.validator_service import ValidatorService


class TestValidatorService:
    """驗證服務測試。"""

    def test_validate_valid_tax_id(self):
        """合法統編應通過驗證。"""
        # TODO: 測試合法統編
        pass

    def test_validate_invalid_tax_id(self):
        """不合法統編應未通過驗證。"""
        # TODO: 測試不合法統編
        pass

    def test_convert_roc_date(self):
        """民國年日期應正確轉換。"""
        # TODO: 測試日期轉換
        pass

    def test_check_duplicate_found(self):
        """已存在的發票號碼應偵測為重複。"""
        # TODO: mock 資料庫查詢，測試重複偵測
        pass

    def test_check_duplicate_not_found(self):
        """不存在的發票號碼應回傳非重複。"""
        # TODO: mock 資料庫查詢，測試非重複情況
        pass
