"""發票相關的 Pydantic schema。"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class FieldConfidence(BaseModel):
    """各欄位的 AI 辨識信心分數。"""
    invoice_number: str | None = None  # "high" / "medium" / "low"
    tax_id: str | None = None
    date: str | None = None
    amount: str | None = None
    items: str | None = None


class InvoiceRecognitionResult(BaseModel):
    """AI / QR Code 辨識結果 schema。"""
    invoice_number: str | None = None
    tax_id: str | None = None
    date: str | None = None  # 原始日期字串（可能是民國年）
    amount: float | None = None
    items: list[str] | None = None
    recognition_method: str  # "qr_code" 或 "ai_vision"
    field_confidence: FieldConfidence | None = None  # QR 解碼時為 None


class InvoiceConfirmRequest(BaseModel):
    """員工確認/修正信心不足欄位的請求 schema。"""
    invoice_number: str | None = None
    tax_id: str | None = None
    date: str | None = None
    amount: float | None = None


class InvoiceResponse(BaseModel):
    """發票紀錄回傳 schema。"""
    id: int
    user_id: int
    invoice_number: str
    tax_id: str | None = None
    tax_id_valid: bool | None = None
    date: date | None = None
    amount: Decimal | None = None
    category: str | None = None
    recognition_method: str
    field_confidence: dict | None = None
    status: str
    reject_reason: str | None = None
    image_url: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """發票清單回傳 schema。"""
    invoices: list[InvoiceResponse]
    total: int
