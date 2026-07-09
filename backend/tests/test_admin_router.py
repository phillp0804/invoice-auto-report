"""總務後台路由（admin_router）的單元測試。

直接呼叫路由函式（不透過 TestClient）。ReportService 在 dashboard/export
測試中會被 mock，以隔離 admin_router 本身的邏輯（例如錯誤處理、狀態檢查）；
report_service 自身的彙整/匯出邏輯已在 test_report_service.py 驗證。
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from database import Base
from models.invoice import Invoice
from models.user import User
from routers.admin_router import (
    approve_invoice,
    export_report,
    get_dashboard,
    get_pending_invoices,
    reject_invoice,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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
def admin_user(db_session):
    user = User(name="總務", email="admin@example.com", role="admin")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def employee(db_session):
    user = User(name="小明", email="ming@example.com", role="employee")
    db_session.add(user)
    db_session.commit()
    return user


class TestGetDashboard:
    """get_dashboard() 測試。"""

    def test_delegates_to_report_service(self, db_session, admin_user):
        with patch("routers.admin_router.ReportService") as mock_service_cls:
            mock_service_cls.return_value.get_dashboard_data.return_value = "dashboard-result"

            result = get_dashboard(
                year=2024, month=7, current_user=admin_user, db=db_session
            )

        mock_service_cls.return_value.get_dashboard_data.assert_called_once_with(
            db_session, year=2024, month=7
        )
        assert result == "dashboard-result"


class TestGetPendingInvoices:
    """get_pending_invoices() 測試。"""

    def test_only_returns_pending_status(self, db_session, admin_user, employee):
        db_session.add_all(
            [
                Invoice(
                    user_id=employee.id,
                    invoice_number="AB00000001",
                    recognition_method="qr_code",
                    status="待審核",
                ),
                Invoice(
                    user_id=employee.id,
                    invoice_number="AB00000002",
                    recognition_method="qr_code",
                    status="已確認",
                ),
                Invoice(
                    user_id=employee.id,
                    invoice_number="AB00000003",
                    recognition_method="qr_code",
                    status="已退回",
                    reject_reason="重複",
                ),
            ]
        )
        db_session.commit()

        result = get_pending_invoices(current_user=admin_user, db=db_session)

        assert result.total == 1
        assert result.invoices[0].invoice_number == "AB00000001"


class TestApproveInvoice:
    """approve_invoice() 測試。"""

    def test_marks_invoice_as_confirmed(self, db_session, admin_user, employee):
        invoice = Invoice(
            user_id=employee.id,
            invoice_number="AB00000001",
            recognition_method="qr_code",
            status="待審核",
        )
        db_session.add(invoice)
        db_session.commit()

        result = approve_invoice(
            invoice_id=invoice.id, current_user=admin_user, db=db_session
        )

        assert result.status == "已確認"

    def test_not_found_raises_404(self, db_session, admin_user):
        with pytest.raises(HTTPException) as exc_info:
            approve_invoice(invoice_id=999, current_user=admin_user, db=db_session)

        assert exc_info.value.status_code == 404

    def test_already_processed_raises_400(self, db_session, admin_user, employee):
        invoice = Invoice(
            user_id=employee.id,
            invoice_number="AB00000001",
            recognition_method="qr_code",
            status="已確認",
        )
        db_session.add(invoice)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            approve_invoice(
                invoice_id=invoice.id, current_user=admin_user, db=db_session
            )

        assert exc_info.value.status_code == 400


class TestRejectInvoice:
    """reject_invoice() 測試。"""

    def test_marks_invoice_as_rejected_with_reason(self, db_session, admin_user, employee):
        invoice = Invoice(
            user_id=employee.id,
            invoice_number="AB00000001",
            recognition_method="qr_code",
            status="待審核",
        )
        db_session.add(invoice)
        db_session.commit()

        result = reject_invoice(
            invoice_id=invoice.id,
            reject_reason="發票號碼與歷史紀錄重複",
            current_user=admin_user,
            db=db_session,
        )

        assert result.status == "已退回"
        assert result.reject_reason == "發票號碼與歷史紀錄重複"

    def test_empty_reason_raises_422(self, db_session, admin_user, employee):
        invoice = Invoice(
            user_id=employee.id,
            invoice_number="AB00000001",
            recognition_method="qr_code",
            status="待審核",
        )
        db_session.add(invoice)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            reject_invoice(
                invoice_id=invoice.id,
                reject_reason="   ",
                current_user=admin_user,
                db=db_session,
            )

        assert exc_info.value.status_code == 422

    def test_not_found_raises_404(self, db_session, admin_user):
        with pytest.raises(HTTPException) as exc_info:
            reject_invoice(
                invoice_id=999,
                reject_reason="理由",
                current_user=admin_user,
                db=db_session,
            )

        assert exc_info.value.status_code == 404

    def test_already_processed_raises_400(self, db_session, admin_user, employee):
        invoice = Invoice(
            user_id=employee.id,
            invoice_number="AB00000001",
            recognition_method="qr_code",
            status="已退回",
            reject_reason="先前理由",
        )
        db_session.add(invoice)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            reject_invoice(
                invoice_id=invoice.id,
                reject_reason="新理由",
                current_user=admin_user,
                db=db_session,
            )

        assert exc_info.value.status_code == 400


class TestExportReport:
    """export_report() 測試。"""

    def test_returns_streaming_response_with_attachment_headers(
        self, db_session, admin_user
    ):
        with patch("routers.admin_router.ReportService") as mock_service_cls:
            mock_service_cls.return_value.export_excel.return_value = MagicMock()

            response = export_report(
                year=2024,
                month=7,
                group_by="department",
                current_user=admin_user,
                db=db_session,
            )

        assert "attachment" in response.headers["Content-Disposition"]
        assert "invoice_report_202407_department.xlsx" in response.headers["Content-Disposition"]
        assert response.media_type == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_invalid_group_by_raises_422(self, db_session, admin_user):
        with patch("routers.admin_router.ReportService") as mock_service_cls:
            mock_service_cls.return_value.export_excel.side_effect = ValueError(
                "不支援的分組方式：foo"
            )

            with pytest.raises(HTTPException) as exc_info:
                export_report(
                    year=2024,
                    month=7,
                    group_by="foo",
                    current_user=admin_user,
                    db=db_session,
                )

        assert exc_info.value.status_code == 422
