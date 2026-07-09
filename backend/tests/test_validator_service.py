"""驗證服務的單元測試。"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.invoice import Invoice
from services.validator_service import ValidatorService


@pytest.fixture()
def db_session():
    """提供獨立的記憶體 SQLite session，供重複偵測測試使用。"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


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

    # --- 日期轉換 ---

    def test_convert_roc_date(self):
        """民國年日期應正確轉換。"""
        assert self.service.convert_date("113/07/08") == date(2024, 7, 8)

    def test_convert_roc_date_invalid_format(self):
        """無法解析的日期格式應拋出 ValueError。"""
        with pytest.raises(ValueError):
            self.service.convert_date("not-a-date")

    # --- 重複偵測 ---

    def test_check_duplicate_found(self, db_session):
        """已存在的發票號碼應偵測為重複。"""
        db_session.add(
            Invoice(
                user_id=1,
                invoice_number="AB12345678",
                recognition_method="qr_code",
                status="待審核",
            )
        )
        db_session.commit()

        assert self.service.check_duplicate("AB12345678", db_session) is True

    def test_check_duplicate_not_found(self, db_session):
        """不存在的發票號碼應回傳非重複。"""
        assert self.service.check_duplicate("ZZ99999999", db_session) is False
