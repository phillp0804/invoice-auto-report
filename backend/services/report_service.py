"""報表彙整與 Excel 匯出服務。"""

from io import BytesIO

from sqlalchemy.orm import Session

from schemas.report_schema import DashboardResponse


class ReportService:
    """報表彙整與匯出服務。"""

    def get_dashboard_data(
        self,
        db: Session,
        year: int | None = None,
        month: int | None = None,
    ) -> DashboardResponse:
        """取得儀表板彙整資料。

        Args:
            db: 資料庫 session。
            year: 篩選年份（可選）。
            month: 篩選月份（可選）。

        Returns:
            依類別/員工/部門彙整的儀表板資料。
        """
        # TODO: 查詢指定月份的已確認發票，依各維度彙整
        raise NotImplementedError

    def export_excel(
        self,
        db: Session,
        year: int,
        month: int,
        group_by: str = "department",
    ) -> BytesIO:
        """匯出 Excel 報表。

        Args:
            db: 資料庫 session。
            year: 報表年份。
            month: 報表月份。
            group_by: 分組方式（"department" / "employee" / "category"）。

        Returns:
            Excel 檔案的 BytesIO 物件。
        """
        # TODO: 使用 openpyxl 或 pandas 產出 Excel 檔案
        raise NotImplementedError
