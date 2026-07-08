"""驗證服務：統編檢查碼、公司統編比對、民國年轉換、重複發票偵測。

此層為確定性邏輯，不使用 AI 判斷，方便寫單元測試保證正確性。
"""

from datetime import date

from sqlalchemy.orm import Session

from utils.date_converter import convert_roc_to_ad
from utils.tax_id_checksum import is_company_tax_id, validate_tax_id


class ValidatorService:
    """發票資料驗證服務。"""

    def validate_tax_id(self, tax_id: str) -> bool:
        """驗證統一編號是否合法。

        Args:
            tax_id: 八位數統一編號字串。

        Returns:
            True 表示合法，False 表示不合法。
        """
        return validate_tax_id(tax_id)

    def check_company_tax_id(
        self, buyer_tax_id: str, company_tax_id: str
    ) -> bool:
        """比對發票上的買方統編是否為本公司統編。

        用於判斷員工上傳的發票是否確實開立給本公司，
        避免個人消費發票混入報帳流程。

        Args:
            buyer_tax_id: 發票上的買方統編。
            company_tax_id: 系統設定的公司統編（來自 config）。

        Returns:
            True 表示為本公司發票，False 表示非本公司發票。
        """
        return is_company_tax_id(buyer_tax_id, company_tax_id)

    def convert_date(self, date_str: str) -> date:
        """將民國年日期字串轉換為西元年 date 物件。

        Args:
            date_str: 民國年日期字串（例如 "113/07/08"）。

        Returns:
            轉換後的 Python date 物件。
        """
        # TODO: 呼叫 utils/date_converter.py
        raise NotImplementedError

    def check_duplicate(self, invoice_number: str, db: Session) -> bool:
        """檢查發票號碼是否在全公司範圍內重複。

        Args:
            invoice_number: 發票號碼。
            db: 資料庫 session。

        Returns:
            True 表示已存在（重複），False 表示不重複。
        """
        # TODO: 查詢 invoices 資料表，比對 invoice_number
        raise NotImplementedError
