"""發票路由（invoice_router）的單元測試。

直接呼叫路由函式（不透過 TestClient），QrService / OcrService /
ClassifierService 全程 mock，避免真的解碼圖片或呼叫 Claude API。
save_invoice_image 也全程 mock，避免測試時真的寫檔到 uploads/。
ValidatorService 使用真實實作，因為它是純函式邏輯，值得順帶驗證整合行為。
"""

import asyncio
import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.invoice import Invoice
from models.user import User
from routers.invoice_router import confirm_invoice, get_my_invoices, upload_invoice
from schemas.invoice_schema import FieldConfidence, InvoiceConfirmRequest, InvoiceRecognitionResult


def _jpeg_upload_file(filename: str = "invoice.jpg") -> UploadFile:
    buffer = io.BytesIO()
    Image.new("RGB", (100, 100)).save(buffer, format="JPEG")
    buffer.seek(0)
    return UploadFile(file=buffer, filename=filename)


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
def employee(db_session):
    user = User(name="小明", email="ming@example.com", role="employee")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(autouse=True)
def mock_storage():
    """全部測試都避免真的寫檔到 uploads/；儲存邏輯本身已在 test_storage_service.py 驗證。"""
    with patch(
        "routers.invoice_router.save_invoice_image", return_value="uploads/mock.jpg"
    ) as mock_save:
        yield mock_save


def _qr_recognition() -> InvoiceRecognitionResult:
    return InvoiceRecognitionResult(
        invoice_number="AB12345678",
        tax_id="04595257",  # 合法統編
        date="113/07/08",
        amount=1050.0,
        items=["午餐"],
        recognition_method="qr_code",
        field_confidence=None,
    )


class TestUploadInvoice:
    """upload_invoice() 測試。"""

    def test_qr_path_saves_invoice_with_high_trust_no_confidence(
        self, db_session, employee
    ):
        with (
            patch("routers.invoice_router.QrService") as mock_qr_cls,
            patch("routers.invoice_router.OcrService") as mock_ocr_cls,
            patch("routers.invoice_router.ClassifierService") as mock_classifier_cls,
        ):
            mock_qr_cls.return_value.detect_and_decode.return_value = _qr_recognition()
            mock_classifier_cls.return_value.classify.return_value = "餐飲"

            invoice = asyncio.run(
                upload_invoice(
                    file=_jpeg_upload_file(),
                    current_user=employee,
                    db=db_session,
                )
            )

            mock_ocr_cls.return_value.recognize.assert_not_called()

        assert invoice.invoice_number == "AB12345678"
        assert invoice.tax_id_valid is True
        assert invoice.recognition_method == "qr_code"
        assert invoice.field_confidence is None
        assert invoice.category == "餐飲"
        assert invoice.status == "待審核"
        assert invoice.is_duplicate is False
        assert invoice.image_url == "uploads/mock.jpg"

    def test_falls_back_to_ocr_when_no_qr_code(self, db_session, employee):
        ai_result = InvoiceRecognitionResult(
            invoice_number="CD87654321",
            tax_id="12345678",  # 不合法統編
            date="113/07/08",
            amount=500.0,
            items=["文具"],
            recognition_method="ai_vision",
            field_confidence=FieldConfidence(
                invoice_number="high", tax_id="medium", date="high", amount="high", items="low"
            ),
        )
        with (
            patch("routers.invoice_router.QrService") as mock_qr_cls,
            patch("routers.invoice_router.OcrService") as mock_ocr_cls,
            patch("routers.invoice_router.ClassifierService") as mock_classifier_cls,
        ):
            mock_qr_cls.return_value.detect_and_decode.return_value = None
            mock_ocr_cls.return_value.recognize.return_value = ai_result
            mock_classifier_cls.return_value.classify.return_value = "辦公用品"

            invoice = asyncio.run(
                upload_invoice(
                    file=_jpeg_upload_file(),
                    current_user=employee,
                    db=db_session,
                )
            )

        assert invoice.recognition_method == "ai_vision"
        assert invoice.tax_id_valid is False
        assert invoice.field_confidence["items"] == "low"

    def test_missing_invoice_number_raises_422(self, db_session, employee):
        no_number = InvoiceRecognitionResult(
            invoice_number=None,
            tax_id=None,
            date=None,
            amount=None,
            items=None,
            recognition_method="ai_vision",
            field_confidence=None,
        )
        with (
            patch("routers.invoice_router.QrService") as mock_qr_cls,
            patch("routers.invoice_router.OcrService") as mock_ocr_cls,
        ):
            mock_qr_cls.return_value.detect_and_decode.return_value = None
            mock_ocr_cls.return_value.recognize.return_value = no_number

            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(
                    upload_invoice(
                        file=_jpeg_upload_file(),
                        current_user=employee,
                        db=db_session,
                    )
                )

        assert exc_info.value.status_code == 422

    def test_invalid_image_raises_400(self, db_session, employee):
        bad_file = UploadFile(file=io.BytesIO(b"not an image"), filename="bad.jpg")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                upload_invoice(file=bad_file, current_user=employee, db=db_session)
            )

        assert exc_info.value.status_code == 400

    def test_second_upload_with_same_invoice_number_flags_duplicate(
        self, db_session, employee
    ):
        """同一張發票號碼被上傳第二次時，應存入但標記 is_duplicate，交給總務審核。"""
        with (
            patch("routers.invoice_router.QrService") as mock_qr_cls,
            patch("routers.invoice_router.ClassifierService") as mock_classifier_cls,
        ):
            mock_qr_cls.return_value.detect_and_decode.return_value = _qr_recognition()
            mock_classifier_cls.return_value.classify.return_value = "餐飲"

            first = asyncio.run(
                upload_invoice(file=_jpeg_upload_file(), current_user=employee, db=db_session)
            )
            second = asyncio.run(
                upload_invoice(file=_jpeg_upload_file(), current_user=employee, db=db_session)
            )

        assert first.is_duplicate is False
        assert second.is_duplicate is True
        assert second.invoice_number == first.invoice_number


class TestConfirmInvoice:
    """confirm_invoice() 測試。"""

    def _pending_invoice(self, db_session, employee) -> Invoice:
        invoice = Invoice(
            user_id=employee.id,
            invoice_number="AB12345678",
            tax_id=None,
            recognition_method="ai_vision",
            status="待審核",
        )
        db_session.add(invoice)
        db_session.commit()
        db_session.refresh(invoice)
        return invoice

    def test_updates_tax_id_and_recomputes_validity(self, db_session, employee):
        invoice = self._pending_invoice(db_session, employee)

        result = confirm_invoice(
            invoice_id=invoice.id,
            request=InvoiceConfirmRequest(tax_id="04595257"),
            current_user=employee,
            db=db_session,
        )

        assert result.tax_id == "04595257"
        assert result.tax_id_valid is True

    def test_updates_date(self, db_session, employee):
        invoice = self._pending_invoice(db_session, employee)

        result = confirm_invoice(
            invoice_id=invoice.id,
            request=InvoiceConfirmRequest(date="113/07/08"),
            current_user=employee,
            db=db_session,
        )

        assert result.date.isoformat() == "2024-07-08"

    def test_changing_invoice_number_to_existing_one_flags_duplicate(
        self, db_session, employee
    ):
        db_session.add(
            Invoice(
                user_id=employee.id,
                invoice_number="ZZ99999999",
                recognition_method="qr_code",
                status="待審核",
            )
        )
        db_session.commit()
        invoice = self._pending_invoice(db_session, employee)

        result = confirm_invoice(
            invoice_id=invoice.id,
            request=InvoiceConfirmRequest(invoice_number="ZZ99999999"),
            current_user=employee,
            db=db_session,
        )

        assert result.is_duplicate is True

    def test_changing_invoice_number_to_unique_one_stays_not_duplicate(
        self, db_session, employee
    ):
        invoice = self._pending_invoice(db_session, employee)

        result = confirm_invoice(
            invoice_id=invoice.id,
            request=InvoiceConfirmRequest(invoice_number="UNIQUE00001"),
            current_user=employee,
            db=db_session,
        )

        assert result.is_duplicate is False

    def test_invalid_date_raises_422(self, db_session, employee):
        invoice = self._pending_invoice(db_session, employee)

        with pytest.raises(HTTPException) as exc_info:
            confirm_invoice(
                invoice_id=invoice.id,
                request=InvoiceConfirmRequest(date="not-a-date"),
                current_user=employee,
                db=db_session,
            )

        assert exc_info.value.status_code == 422

    def test_invoice_not_found_raises_404(self, db_session, employee):
        with pytest.raises(HTTPException) as exc_info:
            confirm_invoice(
                invoice_id=999,
                request=InvoiceConfirmRequest(),
                current_user=employee,
                db=db_session,
            )

        assert exc_info.value.status_code == 404

    def test_other_users_invoice_raises_403(self, db_session, employee):
        other_user = User(name="小華", email="hua@example.com", role="employee")
        db_session.add(other_user)
        db_session.commit()

        invoice = self._pending_invoice(db_session, other_user)

        with pytest.raises(HTTPException) as exc_info:
            confirm_invoice(
                invoice_id=invoice.id,
                request=InvoiceConfirmRequest(amount=100),
                current_user=employee,
                db=db_session,
            )

        assert exc_info.value.status_code == 403

    def test_already_reviewed_invoice_raises_400(self, db_session, employee):
        invoice = self._pending_invoice(db_session, employee)
        invoice.status = "已確認"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            confirm_invoice(
                invoice_id=invoice.id,
                request=InvoiceConfirmRequest(amount=100),
                current_user=employee,
                db=db_session,
            )

        assert exc_info.value.status_code == 400


class TestGetMyInvoices:
    """get_my_invoices() 測試。"""

    def test_only_returns_current_users_invoices(self, db_session, employee):
        other_user = User(name="小華", email="hua@example.com", role="employee")
        db_session.add(other_user)
        db_session.commit()

        db_session.add_all(
            [
                Invoice(
                    user_id=employee.id,
                    invoice_number="AB11111111",
                    recognition_method="qr_code",
                    status="待審核",
                ),
                Invoice(
                    user_id=other_user.id,
                    invoice_number="CD22222222",
                    recognition_method="qr_code",
                    status="待審核",
                ),
            ]
        )
        db_session.commit()

        result = get_my_invoices(current_user=employee, db=db_session)

        assert result.total == 1
        assert result.invoices[0].invoice_number == "AB11111111"
