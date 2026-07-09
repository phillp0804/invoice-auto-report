"""發票路由：員工上傳、確認修正、查詢紀錄。

只負責接收請求、呼叫對應 service、回傳結果，不寫商業邏輯。
"""

import io
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from middleware.auth_middleware import require_role
from models.invoice import Invoice
from models.user import User
from schemas.invoice_schema import (
    InvoiceConfirmRequest,
    InvoiceListResponse,
    InvoiceResponse,
)
from services.ai_client import create_ai_client
from services.classifier_service import ClassifierService
from services.ocr_service import OcrService
from services.qr_service import QrService
from services.storage_service import build_invoice_filename, save_invoice_image
from services.validator_service import ValidatorService

router = APIRouter()


@router.post("/upload", response_model=InvoiceResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("employee")),
    db: Session = Depends(get_db),
):
    """員工上傳發票圖片，系統自動進行 QR Code 或 AI 辨識。"""
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
        image.load()
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="無法辨識的圖片格式") from exc

    settings = get_settings()
    ai_client = create_ai_client(settings)

    # 辨識：QR Code 優先，偵測不到才走 AI 辨識備援（core rule 11）
    recognition = QrService().detect_and_decode(image)
    if recognition is None:
        recognition = OcrService(ai_client).recognize(image)

    if not recognition.invoice_number:
        raise HTTPException(
            status_code=422, detail="無法辨識發票號碼，請確認拍攝清晰後重新上傳"
        )

    validator = ValidatorService()

    tax_id_valid = (
        validator.validate_tax_id(recognition.tax_id) if recognition.tax_id else None
    )

    invoice_date = None
    if recognition.date:
        try:
            invoice_date = validator.convert_date(recognition.date)
        except ValueError:
            invoice_date = None

    category = ClassifierService(ai_client).classify(
        items=recognition.items or [], amount=recognition.amount
    )

    # 重複發票偵測（core rule 2：確定性邏輯），存入但標記，交由總務審核決定
    is_duplicate = validator.check_duplicate(recognition.invoice_number, db)

    # 備份原始圖片（壓縮後存檔，控制占用空間），檔名依 [姓名][發票日期][發票號碼] 命名
    filename = build_invoice_filename(
        employee_name=current_user.name,
        invoice_number=recognition.invoice_number,
        invoice_date=invoice_date,
        fallback_date=date.today(),
    )
    image_url = save_invoice_image(image, filename)

    invoice = Invoice(
        user_id=current_user.id,
        invoice_number=recognition.invoice_number,
        tax_id=recognition.tax_id,
        tax_id_valid=tax_id_valid,
        date=invoice_date,
        amount=recognition.amount,
        category=category,
        recognition_method=recognition.recognition_method,
        field_confidence=(
            recognition.field_confidence.model_dump()
            if recognition.field_confidence
            else None
        ),
        is_duplicate=is_duplicate,
        image_url=image_url,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
def confirm_invoice(
    invoice_id: int,
    request: InvoiceConfirmRequest,
    current_user: User = Depends(require_role("employee")),
    db: Session = Depends(get_db),
):
    """員工確認/修正信心不足的欄位（僅在 AI 辨識信心不足時觸發）。"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="找不到指定的發票")
    if invoice.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權限修改他人上傳的發票")
    if invoice.status != "待審核":
        raise HTTPException(status_code=400, detail="此發票已完成審核，無法修改")

    validator = ValidatorService()

    if request.invoice_number is not None and request.invoice_number != invoice.invoice_number:
        # 先查重複再賦值：check_duplicate 沒有排除自己，若先改號碼、
        # session autoflush 會讓查詢比對到剛改好的自己，誤判為重複
        invoice.is_duplicate = validator.check_duplicate(request.invoice_number, db)
        invoice.invoice_number = request.invoice_number
    if request.tax_id is not None:
        invoice.tax_id = request.tax_id
        invoice.tax_id_valid = validator.validate_tax_id(request.tax_id)
    if request.date is not None:
        try:
            invoice.date = validator.convert_date(request.date)
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail=f"日期格式不合法：{request.date}"
            ) from exc
    if request.amount is not None:
        invoice.amount = request.amount

    db.commit()
    db.refresh(invoice)

    return invoice


@router.get("/my", response_model=InvoiceListResponse)
def get_my_invoices(
    current_user: User = Depends(require_role("employee")),
    db: Session = Depends(get_db),
):
    """員工查看自己的上傳紀錄與狀態。"""
    invoices = (
        db.query(Invoice)
        .filter(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
        .all()
    )
    return InvoiceListResponse(invoices=invoices, total=len(invoices))
