"""Webhook 路由：供 n8n 呼叫的端點。"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db

router = APIRouter()


@router.post("/n8n/invoice-status")
def n8n_invoice_status_webhook(
    x_secret_token: str = Header(...),
    db: Session = Depends(get_db),
):
    """供 n8n 訂閱發票狀態變化的 webhook 端點。

    安全性：需驗證請求標頭中的 X-Secret-Token 與 .env 中的 N8N_WEBHOOK_SECRET 一致。
    """
    settings = get_settings()
    if x_secret_token != settings.n8n_webhook_secret:
        raise HTTPException(status_code=403, detail="無效的 webhook 密鑰")

    # TODO: 處理 n8n 的 webhook 請求（例如查詢狀態變化的發票清單）
    raise NotImplementedError
