"""總務後台路由：儀表板、審核、報表匯出。"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from schemas.invoice_schema import InvoiceListResponse, InvoiceResponse
from schemas.report_schema import DashboardResponse, ReportExportRequest

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
):
    """總務彙整儀表板：總金額、依類別/員工/部門分組。"""
    # TODO: 查詢指定月份資料，依各維度彙整並回傳
    raise NotImplementedError


@router.get("/invoices/pending", response_model=InvoiceListResponse)
def get_pending_invoices(db: Session = Depends(get_db)):
    """取得待審核的例外項目清單（統編驗證失敗、疑似重複等）。"""
    # TODO: 查詢 status="待審核" 的發票紀錄
    raise NotImplementedError


@router.post("/invoices/{invoice_id}/approve", response_model=InvoiceResponse)
def approve_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    """總務確認（核准）某筆發票。"""
    # TODO: 更新發票狀態為「已確認」
    raise NotImplementedError


@router.post("/invoices/{invoice_id}/reject", response_model=InvoiceResponse)
def reject_invoice(
    invoice_id: int,
    reject_reason: str,
    db: Session = Depends(get_db),
):
    """總務退回某筆發票（需帶 reject_reason）。"""
    # TODO: 更新發票狀態為「已退回」，記錄退回原因，觸發 n8n 通知
    raise NotImplementedError


@router.get("/reports/export")
def export_report(
    year: int,
    month: int,
    group_by: str = "department",
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """匯出 Excel 報表（依部門/員工/類別分組）。"""
    # TODO: 呼叫 report_service 產出 Excel 檔並回傳 StreamingResponse
    raise NotImplementedError
