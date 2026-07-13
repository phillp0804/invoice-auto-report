"""發票相關的 Pydantic schema。"""

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, computed_field

from config import get_settings
from utils.tax_id_checksum import classify_buyer_tax_id


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
    tax_id: str | None = None  # 賣方統一編號
    buyer_tax_id: str | None = None  # 買方統一編號，一般消費者發票依規範預設為 "00000000"
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
    buyer_tax_id: str | None = None
    date: dt.date | None = None
    amount: Decimal | None = None
    category: str | None = None
    recognition_method: str
    field_confidence: dict | None = None
    is_duplicate: bool = False
    status: str
    reject_reason: str | None = None
    image_url: str | None = None
    created_at: dt.datetime | None = None

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def buyer_tax_id_status(self) -> str | None:
        """買方統編狀態："missing"（未打）/ "mismatch"（非本公司）/ None（正常）。"""
        return classify_buyer_tax_id(self.buyer_tax_id, get_settings().company_tax_id)


class InvoiceListResponse(BaseModel):
    """發票清單回傳 schema。"""
    invoices: list[InvoiceResponse]
    total: int
