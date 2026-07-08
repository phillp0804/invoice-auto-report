"""發票紀錄 ORM 模型。"""

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from database import Base


class Invoice(Base):
    """發票紀錄資料表，對應 invoices。"""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上傳的員工")
    invoice_number = Column(String, nullable=False, index=True, comment="發票號碼（用於重複偵測）")
    tax_id = Column(String, nullable=True, comment="統一編號")
    tax_id_valid = Column(Boolean, nullable=True, comment="統編檢查碼驗證結果")
    date = Column(Date, nullable=True, comment="發票日期（已轉西元年）")
    amount = Column(Numeric(10, 2), nullable=True, comment="金額")
    category = Column(String, nullable=True, comment="AI 判斷的支出類別")
    recognition_method = Column(String, nullable=False, comment="辨識方式：qr_code 或 ai_vision")
    field_confidence = Column(JSON, nullable=True, comment="AI 辨識時各欄位信心分數，QR 解碼則為 null")
    status = Column(String, nullable=False, default="待審核", comment="狀態：待審核 / 已確認 / 已退回")
    reject_reason = Column(String, nullable=True, comment="總務退回時填寫的原因")
    image_url = Column(String, nullable=True, comment="圖片路徑")
    created_at = Column(DateTime, server_default=func.now(), comment="上傳時間")

    # 關聯
    user = relationship("User", back_populates="invoices")
