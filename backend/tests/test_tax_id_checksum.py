"""統編檢查碼驗證演算法的單元測試。"""

import pytest

from utils.tax_id_checksum import is_company_tax_id, validate_tax_id


class TestValidateTaxId:
    """統一編號驗證測試。"""

    # --- 合法統編案例 ---

    def test_valid_tax_id_04595257(self):
        """合法統編：04595257（一般情況）。"""
        assert validate_tax_id("04595257") is True

    def test_valid_tax_id_22099131(self):
        """合法統編：22099131（一般情況）。"""
        assert validate_tax_id("22099131") is True

    def test_valid_tax_id_10458575(self):
        """合法統編：10458575（第 7 碼為 7 的例外規則）。"""
        assert validate_tax_id("10458575") is True

    # --- 不合法統編案例 ---

    def test_invalid_tax_id_12345678(self):
        """不合法統編：12345678。"""
        assert validate_tax_id("12345678") is False

    def test_invalid_tax_id_00000001(self):
        """不合法統編：00000001。"""
        assert validate_tax_id("00000001") is False

    # --- 格式錯誤案例 ---

    def test_invalid_length_short(self):
        """長度少於 8 碼應回傳 False。"""
        assert validate_tax_id("1234567") is False

    def test_invalid_length_long(self):
        """長度超過 8 碼應回傳 False。"""
        assert validate_tax_id("123456789") is False

    def test_non_numeric_with_letters(self):
        """包含英文字母應回傳 False。"""
        assert validate_tax_id("1234567A") is False

    def test_non_numeric_with_symbols(self):
        """包含特殊符號應回傳 False。"""
        assert validate_tax_id("1234-678") is False

    def test_empty_string(self):
        """空字串應回傳 False。"""
        assert validate_tax_id("") is False

    def test_none_input(self):
        """None 輸入應回傳 False。"""
        assert validate_tax_id(None) is False


class TestIsCompanyTaxId:
    """公司統編比對測試。"""

    # --- 比對成功案例 ---

    def test_matching_company_tax_id(self):
        """買方統編與公司統編一致時應回傳 True。"""
        assert is_company_tax_id("04595257", "04595257") is True

    # --- 比對失敗案例 ---

    def test_different_tax_id(self):
        """買方統編與公司統編不一致時應回傳 False。"""
        assert is_company_tax_id("04595257", "22099131") is False

    def test_buyer_tax_id_invalid_format(self):
        """買方統編格式不合法時應回傳 False。"""
        assert is_company_tax_id("1234567A", "04595257") is False

    def test_company_tax_id_invalid_format(self):
        """公司統編格式不合法時應回傳 False。"""
        assert is_company_tax_id("04595257", "ABCDEFGH") is False

    def test_buyer_tax_id_invalid_checksum(self):
        """買方統編格式正確但檢查碼不通過時應回傳 False。"""
        assert is_company_tax_id("12345678", "04595257") is False

    def test_both_empty(self):
        """兩者皆為空字串時應回傳 False。"""
        assert is_company_tax_id("", "") is False

    def test_company_tax_id_empty(self):
        """公司統編未設定（空字串）時應回傳 False。"""
        assert is_company_tax_id("04595257", "") is False
