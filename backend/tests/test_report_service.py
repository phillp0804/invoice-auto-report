"""報表彙整與 Excel 匯出服務（ReportService）的單元測試。"""

from datetime import date
from decimal import Decimal

import openpyxl
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.department import Department
from models.invoice import Invoice
from models.user import User
from services.report_service import ReportService


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_db(db_session):
    """建立一份混合狀態、部門、類別的測試資料。"""
    sales_dept = Department(name="業務部")
    db_session.add(sales_dept)
    db_session.commit()

    employee_with_dept = User(
        name="小明", email="ming@example.com", role="employee", department_id=sales_dept.id
    )
    employee_without_dept = User(name="小華", email="hua@example.com", role="employee")
    db_session.add_all([employee_with_dept, employee_without_dept])
    db_session.commit()

    invoices = [
        # 已確認，2024-07，計入彙整
        Invoice(
            user_id=employee_with_dept.id,
            invoice_number="AB00000001",
            amount=Decimal("100.00"),
            category="餐飲",
            date=date(2024, 7, 5),
            recognition_method="qr_code",
            status="已確認",
        ),
        Invoice(
            user_id=employee_with_dept.id,
            invoice_number="AB00000002",
            amount=Decimal("200.00"),
            category="交通",
            date=date(2024, 7, 10),
            recognition_method="qr_code",
            status="已確認",
        ),
        # 已確認但無部門的員工
        Invoice(
            user_id=employee_without_dept.id,
            invoice_number="AB00000003",
            amount=Decimal("50.00"),
            category="餐飲",
            date=date(2024, 7, 15),
            recognition_method="qr_code",
            status="已確認",
        ),
        # 已確認但在 8 月，篩選 7 月時不應計入
        Invoice(
            user_id=employee_with_dept.id,
            invoice_number="AB00000004",
            amount=Decimal("9999.00"),
            category="設備",
            date=date(2024, 8, 1),
            recognition_method="qr_code",
            status="已確認",
        ),
        # 待審核，不計入金額彙整，但計入 pending_count
        Invoice(
            user_id=employee_with_dept.id,
            invoice_number="AB00000005",
            amount=Decimal("300.00"),
            category="住宿",
            recognition_method="ai_vision",
            status="待審核",
        ),
        # 已退回，完全不計入
        Invoice(
            user_id=employee_with_dept.id,
            invoice_number="AB00000006",
            amount=Decimal("400.00"),
            category="其他",
            recognition_method="ai_vision",
            status="已退回",
            reject_reason="重複發票",
        ),
    ]
    db_session.add_all(invoices)
    db_session.commit()

    return {
        "db": db_session,
        "department": sales_dept,
        "employee_with_dept": employee_with_dept,
        "employee_without_dept": employee_without_dept,
    }


class TestGetDashboardData:
    """get_dashboard_data() 測試。"""

    def test_only_counts_confirmed_invoices_in_totals(self, seeded_db):
        result = ReportService().get_dashboard_data(seeded_db["db"])

        # 4 筆已確認：100 + 200 + 50 + 9999
        assert result.total_count == 4
        assert result.total_amount == Decimal("10349.00")

    def test_pending_count_reflects_all_pending_regardless_of_period(self, seeded_db):
        result = ReportService().get_dashboard_data(seeded_db["db"], year=2024, month=7)

        assert result.pending_count == 1

    def test_year_month_filter_excludes_other_months(self, seeded_db):
        result = ReportService().get_dashboard_data(seeded_db["db"], year=2024, month=7)

        # 只剩 7 月的 3 筆已確認：100 + 200 + 50
        assert result.total_count == 3
        assert result.total_amount == Decimal("350.00")

    def test_groups_by_category(self, seeded_db):
        result = ReportService().get_dashboard_data(seeded_db["db"], year=2024, month=7)

        by_category = {c.category: c for c in result.by_category}
        assert by_category["餐飲"].total_amount == Decimal("150.00")
        assert by_category["餐飲"].count == 2
        assert by_category["交通"].total_amount == Decimal("200.00")

    def test_groups_by_employee(self, seeded_db):
        result = ReportService().get_dashboard_data(seeded_db["db"], year=2024, month=7)

        by_employee = {e.user_id: e for e in result.by_employee}
        assert by_employee[seeded_db["employee_with_dept"].id].total_amount == Decimal("300.00")
        assert by_employee[seeded_db["employee_with_dept"].id].user_name == "小明"
        assert by_employee[seeded_db["employee_without_dept"].id].total_amount == Decimal("50.00")

    def test_employee_without_department_excluded_from_department_summary(self, seeded_db):
        result = ReportService().get_dashboard_data(seeded_db["db"], year=2024, month=7)

        department_ids = {d.department_id for d in result.by_department}
        assert seeded_db["department"].id in department_ids
        assert len(result.by_department) == 1
        assert result.by_department[0].total_amount == Decimal("300.00")
        assert result.by_department[0].department_name == "業務部"


class TestExportExcel:
    """export_excel() 測試。"""

    def test_generates_readable_workbook(self, seeded_db):
        buffer = ReportService().export_excel(
            seeded_db["db"], year=2024, month=7, group_by="category"
        )

        workbook = openpyxl.load_workbook(buffer)
        sheet = workbook.active

        header = [cell.value for cell in sheet[1]]
        assert header == ["類別", "金額", "件數"]

        rows = [tuple(cell.value for cell in row) for row in sheet.iter_rows(min_row=2)]
        assert ("總計", 350.0, 3) in rows

    def test_invalid_group_by_raises_value_error(self, seeded_db):
        with pytest.raises(ValueError, match="不支援的分組方式"):
            ReportService().export_excel(
                seeded_db["db"], year=2024, month=7, group_by="not-a-real-option"
            )
