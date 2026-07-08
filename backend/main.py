"""發票自動報帳系統 — FastAPI 應用程式進入點。"""

from fastapi import FastAPI

from database import init_db
from routers import admin_router, auth_router, invoice_router, webhook_router

app = FastAPI(
    title="發票自動報帳系統",
    description="員工上傳發票、系統自動辨識驗證分類、總務彙整審核匯出報表",
    version="0.1.0",
)

# --- 註冊路由 ---
app.include_router(auth_router.router, prefix="/auth", tags=["認證"])
app.include_router(invoice_router.router, prefix="/invoices", tags=["發票"])
app.include_router(admin_router.router, prefix="/admin", tags=["總務後台"])
app.include_router(webhook_router.router, prefix="/webhook", tags=["Webhook"])


@app.on_event("startup")
def on_startup():
    """應用程式啟動時初始化資料庫。"""
    init_db()


@app.get("/")
def root():
    """健康檢查端點。"""
    return {"status": "ok", "message": "發票自動報帳系統 API"}
