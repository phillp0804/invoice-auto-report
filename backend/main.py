"""發票自動報帳系統 — FastAPI 應用程式進入點。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import admin_router, auth_router, invoice_router, webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式啟動時初始化資料庫。"""
    init_db()
    yield


app = FastAPI(
    title="發票自動報帳系統",
    description="員工上傳發票、系統自動辨識驗證分類、總務彙整審核匯出報表",
    version="0.1.0",
    lifespan=lifespan,
)

# --- CORS（開發環境的 Vite dev server，預設埠 5173）---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 註冊路由 ---
app.include_router(auth_router.router, prefix="/auth", tags=["認證"])
app.include_router(invoice_router.router, prefix="/invoices", tags=["發票"])
app.include_router(admin_router.router, prefix="/admin", tags=["總務後台"])
app.include_router(webhook_router.router, prefix="/webhook", tags=["Webhook"])


@app.get("/")
def root():
    """健康檢查端點。"""
    return {"status": "ok", "message": "發票自動報帳系統 API"}
