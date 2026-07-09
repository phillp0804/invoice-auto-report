"""總務後台路由：儀表板、審核、報表匯出。

只負責接收請求、呼叫對應 service、回傳結果，不寫商業邏輯。
所有端點皆須總務（admin）權限，於後端用 require_role("admin") 驗證
（core rule 6：角色權限驗證不能只靠前端隱藏畫面）。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth_middleware import require_role
from models.invoice import Invoice
from models.user import User
from schemas.invoice_schema import InvoiceListResponse, InvoiceResponse
from schemas.report_schema import DashboardResponse
from services.report_service import ReportService

router = APIRouter()

_PENDING_STATUS = "待審核"
_CONFIRMED_STATUS = "已確認"
_REJECTED_STATUS = "已退回"


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    year: int | None = None,
    month: int | None = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """總務彙整儀表板：總金額、依類別/員工/部門分組。"""
    return ReportService().get_dashboard_data(db, year=year, month=month)


@router.get("/invoices/pending", response_model=InvoiceListResponse)
def get_pending_invoices(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """取得待審核的例外項目清單（統編驗證失敗、疑似重複等）。"""
    invoices = (
        db.query(Invoice)
        .filter(Invoice.status == _PENDING_STATUS)
        .order_by(Invoice.created_at.asc())
        .all()
    )
    return InvoiceListResponse(invoices=invoices, total=len(invoices))


@router.post("/invoices/{invoice_id}/approve", response_model=InvoiceResponse)
def approve_invoice(
    invoice_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """總務確認（核准）某筆發票。"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="找不到指定的發票")
    if invoice.status != _PENDING_STATUS:
        raise HTTPException(status_code=400, detail="此發票已完成審核，無法重複處理")

    invoice.status = _CONFIRMED_STATUS
    db.commit()
    db.refresh(invoice)

    return invoice


@router.post("/invoices/{invoice_id}/reject", response_model=InvoiceResponse)
def reject_invoice(
    invoice_id: int,
    reject_reason: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """總務退回某筆發票（需帶 reject_reason）。"""
    if not reject_reason.strip():
        # core rule 10：狀態為「已退回」時 reject_reason 不可為空，n8n 會用這個原因通知員工
        raise HTTPException(status_code=422, detail="退回發票必須填寫退回原因")

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="找不到指定的發票")
    if invoice.status != _PENDING_STATUS:
        raise HTTPException(status_code=400, detail="此發票已完成審核，無法重複處理")

    invoice.status = _REJECTED_STATUS
    invoice.reject_reason = reject_reason
    db.commit()
    db.refresh(invoice)

    # TODO: 觸發 n8n webhook（N8N_WEBHOOK_URL）通知員工發票被退回及原因，
    # 對外呼叫 n8n 尚未實作，目前僅更新資料庫狀態。

    return invoice


@router.get("/reports/export")
def export_report(
    year: int,
    month: int,
    group_by: str = "department",
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """匯出 Excel 報表（依部門/員工/類別分組）。"""
    try:
        buffer = ReportService().export_excel(
            db, year=year, month=month, group_by=group_by
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = f"invoice_report_{year}{month:02d}_{group_by}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
