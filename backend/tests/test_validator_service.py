"""驗證服務的單元測試。"""

import pytest

from services.validator_service import ValidatorService


class TestValidatorService:
    """驗證服務測試。"""

    def setup_method(self):
        """每個測試方法前建立 ValidatorService 實例。"""
        self.service = ValidatorService()

    # --- 統編驗證 ---

    def test_validate_valid_tax_id(self):
        """合法統編應通過驗證。"""
        assert self.service.validate_tax_id("04595257") is True

    def test_validate_invalid_tax_id(self):
        """不合法統編應未通過驗證。"""
        assert self.service.validate_tax_id("12345678") is False

    # --- 公司統編比對 ---

    def test_check_company_tax_id_match(self):
        """買方統編與公司統編一致時應回傳 True。"""
        assert self.service.check_company_tax_id("04595257", "04595257") is True

    def test_check_company_tax_id_mismatch(self):
        """買方統編與公司統編不一致時應回傳 False。"""
        assert self.service.check_company_tax_id("04595257", "22099131") is False

    def test_check_company_tax_id_not_configured(self):
        """公司統編未設定（空字串）時應回傳 False。"""
        assert self.service.check_company_tax_id("04595257", "") is False

    # --- 日期轉換（TODO：待 date_converter 實作後補齊） ---

    def test_convert_roc_date(self):
        """民國年日期應正確轉換。"""
        # TODO: 待 date_converter 實作後補齊
        pass

    # --- 重複偵測（TODO：待資料庫模型實作後補齊） ---

    def test_check_duplicate_found(self):
        """已存在的發票號碼應偵測為重複。"""
        # TODO: mock 資料庫查詢，測試重複偵測
        pass

    def test_check_duplicate_not_found(self):
        """不存在的發票號碼應回傳非重複。"""
        # TODO: mock 資料庫查詢，測試非重複情況
        pass
