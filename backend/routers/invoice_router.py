"""發票路由：員工上傳、確認修正、查詢紀錄。"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from schemas.invoice_schema import (
    InvoiceConfirmRequest,
    InvoiceListResponse,
    InvoiceRecognitionResult,
    InvoiceResponse,
)

router = APIRouter()


@router.post("/upload", response_model=InvoiceResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """員工上傳發票圖片，系統自動進行 QR Code 或 AI 辨識。"""
    # TODO: 接收圖片 → QR 偵測 → 若無 QR 則 AI 辨識 → 驗證 → 分類 → 儲存
    raise NotImplementedError


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
def confirm_invoice(
    invoice_id: int,
    request: InvoiceConfirmRequest,
    db: Session = Depends(get_db),
):
    """員工確認/修正信心不足的欄位（僅在 AI 辨識信心不足時觸發）。"""
    # TODO: 更新指定發票的修正欄位，重新驗證統編，更新狀態
    raise NotImplementedError


@router.get("/my", response_model=InvoiceListResponse)
def get_my_invoices(db: Session = Depends(get_db)):
    """員工查看自己的上傳紀錄與狀態。"""
    # TODO: 依登入使用者 ID 查詢該員工的發票紀錄
    raise NotImplementedError
