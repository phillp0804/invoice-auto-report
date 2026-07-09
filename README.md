# 📄 發票自動報帳系統

> 模擬真實企業報帳情境的雙角色自動化系統——員工只需拍照上傳，總務直接取得整理好的報表。

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Claude API](https://img.shields.io/badge/Claude_API-Multimodal-D97706?logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 專案簡介

一般公司報帳流程常見痛點：員工需自行整理發票、填寫報帳單；總務需人工核對統編、加總分類、檢查重複報帳，既耗時又容易出錯。

本系統針對這些問題，設計「**員工只需上傳、總務直接取得整理好的報表**」的自動化流程，透過 QR Code 優先辨識 + AI 備援辨識（Claude Vision）的雙軌機制，結合統編驗證、重複偵測、自動分類等確定性邏輯，降低雙方的操作負擔。

### 與「直接問 AI」的差異

| 需求 | 單次問答 AI | 本系統 |
|---|---|---|
| 多人上傳彙整成單一報表 | ❌ 無法跨使用者彙整 | ✅ 自動彙整全員工上傳資料 |
| 跨月份累積統計 | ❌ 無記憶 | ✅ 資料庫累積、依月份自動加總 |
| 統編合法性驗證 | ⚠️ 可能誤判 | ✅ 程式碼實作檢查碼演算法 |
| 重複發票偵測（跨員工） | ❌ 無法比對歷史/他人資料 | ✅ 全公司範圍比對發票號碼 |
| 角色分權 | ❌ 無角色概念 | ✅ 員工只管上傳，總務取得彙整結果 |
| 結構化報表輸出 | ❌ 純文字回覆 | ✅ 可依部門/員工/類別匯出 Excel |

---

## 🏗️ 系統架構

```
員工端 App（拍照上傳） ──▶
                        後端 API（FastAPI）
                              │
                              ▼
                    QR Code 偵測（pyzbar）
                     ├─ 有 QR → 直接解碼（準確度最高）
                     └─ 無 QR → Claude Vision 辨識 + 信心分數
                              │
                              ▼（信心不足才觸發）
                    員工確認/修正畫面
                              │
                              ▼
總務端後台（彙整/審核/匯出） ◀── 規則驗證引擎（統編/重複/年份）
                                       │
                                       ▼
                              資料庫（含角色/狀態欄位）
                                       │
                                       ▼（狀態變化觸發 webhook）
                              ┌─────────────────┐
                              │      n8n         │
                              │ - 退回通知員工     │
                              │ - 定期彙整寄送     │
                              │ - 待審核提醒       │
                              └─────────────────┘
```

---

## 🛠️ 技術選型

| 模組 | 技術 | 說明 |
|---|---|---|
| 影像辨識 | Claude API 或 Gemini API（多模態） | 無 QR Code 時的備援辨識路徑，透過 `AI_PROVIDER` 切換廠商 |
| QR Code 解碼 | pyzbar / Pillow | 優先辨識電子發票 QR Code，降低 AI 呼叫成本 |
| 後端框架 | FastAPI（Python） | 含角色權限中介層（middleware） |
| 規則引擎 | 純 Python 邏輯 | 統編檢查碼、民國年轉換、跨員工重複比對 |
| 身份驗證 | Firebase Authentication | 區分員工/總務角色 |
| 資料庫 | SQLite（開發）→ PostgreSQL（正式） | SQLAlchemy ORM |
| 報表匯出 | openpyxl / pandas | 產出 Excel 報表 |
| 自動化/通知 | n8n | 退回通知、定期彙整寄送、待審核提醒 |

---

## 📁 專案結構

```
invoice-auto-report/
├── backend/                    # FastAPI 後端
│   ├── main.py                  # 應用程式進入點（含 CORS 設定）
│   ├── config.py                # 環境變數讀取、設定管理
│   ├── database.py              # 資料庫連線與 session 管理
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/                  # 資料庫 ORM 模型
│   │   ├── user.py
│   │   ├── invoice.py
│   │   └── department.py
│   ├── schemas/                 # Pydantic 資料驗證模型
│   │   ├── user_schema.py
│   │   ├── invoice_schema.py
│   │   └── report_schema.py
│   ├── routers/                 # API 路由
│   │   ├── auth_router.py
│   │   ├── invoice_router.py
│   │   ├── admin_router.py      # 總務專屬路由
│   │   └── webhook_router.py    # n8n webhook 端點（密鑰驗證已完成，處理邏輯留給使用者接）
│   ├── services/                # 核心業務邏輯
│   │   ├── qr_service.py        # QR Code 偵測與解碼
│   │   ├── ocr_service.py       # AI Vision 辨識
│   │   ├── validator_service.py # 統編驗證、重複偵測
│   │   ├── classifier_service.py # AI 支出分類
│   │   ├── report_service.py    # 報表彙整與匯出
│   │   ├── storage_service.py   # 發票圖片壓縮備份（檔名：[姓名][日期][發票號碼]）
│   │   ├── claude_client.py     # Claude API 共用客戶端
│   │   ├── gemini_client.py     # Gemini API 共用客戶端（與 claude_client 同介面）
│   │   ├── ai_client.py         # 依 AI_PROVIDER 設定挑選 Claude/Gemini
│   │   └── prompts/             # AI Prompt 模板
│   ├── middleware/
│   │   └── auth_middleware.py   # 角色權限驗證
│   ├── utils/                   # 純函式工具
│   │   ├── tax_id_checksum.py   # 統編檢查碼演算法
│   │   ├── date_converter.py    # 民國年轉西元年
│   │   ├── qr_parser.py        # QR Code 字串解析
│   │   └── image_compressor.py  # 圖片壓縮
│   └── tests/                   # 單元測試（139 個）
├── frontend/                    # React 前端（Vite）
│   └── src/
│       ├── pages/                # LoginPage + employee/admin 六個頁面
│       ├── components/           # InvoiceCard、StatusBadge
│       ├── api/                  # invoiceApi.js（封裝所有後端呼叫）
│       └── auth/                 # firebaseConfig、AuthContext（Context API 管理登入狀態）
└── docs/                        # 專案文件
    ├── 發票自動報帳系統_專案計畫書_v2.3.md
    └── 發票自動報帳系統_程式架構文件.md
```

---

## 🚀 快速開始

### 前置需求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（Python 套件管理工具）
- Node.js 18+（前端）

### 後端安裝與設定

```bash
# 1. 複製專案
git clone https://github.com/phillp0804/invoice-auto-report.git
cd invoice-auto-report

# 2. 建立虛擬環境並安裝依賴
cd backend
uv venv
uv pip install -r requirements.txt

# 3. 設定環境變數
cp .env.example .env
# 編輯 .env 填入你的 API Key 等設定

# 4. 啟動開發伺服器
uv run uvicorn main:app --reload
```

### 後端環境變數說明

| 變數名稱 | 說明 |
|---|---|
| `AI_PROVIDER` | AI 辨識/分類要用哪個廠商：`claude` 或 `gemini`（預設 `claude`） |
| `ANTHROPIC_API_KEY` | Claude API 金鑰（`AI_PROVIDER=claude` 時使用） |
| `GEMINI_API_KEY` | Gemini API 金鑰（`AI_PROVIDER=gemini` 時使用；有免費額度） |
| `GEMINI_MODEL` | Gemini 模型名稱（預設 `gemini-2.5-flash`） |
| `FIREBASE_PROJECT_ID` | Firebase 專案 ID |
| `FIREBASE_PRIVATE_KEY` | Firebase 私鑰 |
| `FIREBASE_CLIENT_EMAIL` | Firebase 服務帳號 Email |
| `DATABASE_URL` | 資料庫連線字串（預設 SQLite） |
| `UPLOAD_DIR` | 發票圖片備份儲存目錄（預設 `uploads`） |
| `COMPANY_TAX_ID` | 本公司統一編號（比對發票買方統編用） |
| `N8N_WEBHOOK_URL` | n8n Webhook 端點 URL |
| `N8N_WEBHOOK_SECRET` | n8n Webhook 驗證密鑰 |

### 前端安裝與設定

```bash
cd frontend
npm install

cp .env.example .env
# 編輯 .env 填入 Firebase 前端設定與後端 API 位置

npm run dev
```

前端預設在 `http://localhost:5173`，後端須先啟動於 `http://localhost:8000`（已在 `main.py` 設定 CORS 允許此來源）。

### 前端環境變數說明

| 變數名稱 | 說明 |
|---|---|
| `VITE_API_BASE_URL` | 後端 API 位置（預設 `http://localhost:8000`） |
| `VITE_FIREBASE_API_KEY` | Firebase 前端設定（與後端同一個 Firebase 專案） |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase Auth Domain |
| `VITE_FIREBASE_PROJECT_ID` | Firebase 專案 ID |

---

## 📡 API 路由

| 路由 | 方法 | 說明 | 權限 |
|---|---|---|---|
| `/auth/login` | POST | 登入（Firebase token 驗證） | 公開 |
| `/invoices/upload` | POST | 員工上傳發票圖片 | 員工 |
| `/invoices/{id}/confirm` | POST | 員工確認/修正信心不足的欄位 | 員工 |
| `/invoices/my` | GET | 員工查看自己的上傳紀錄 | 員工 |
| `/admin/dashboard` | GET | 總務彙整儀表板資料 | 總務 |
| `/admin/invoices/pending` | GET | 待審核例外項目清單 | 總務 |
| `/admin/invoices/{id}/approve` | POST | 總務確認項目 | 總務 |
| `/admin/invoices/{id}/reject` | POST | 總務退回項目 | 總務 |
| `/admin/reports/export` | GET | 匯出 Excel 報表 | 總務 |
| `/webhook/n8n/invoice-status` | POST | n8n 狀態變化訂閱 | 系統內部 |

---

## 🧪 執行測試

```bash
cd backend
uv run pytest tests/ -v
```

---

## 📋 角色與流程

### 員工端

1. 開啟 App → 拍照或上傳發票
2. 系統偵測 QR Code → 有則直接解碼，無則走 AI 辨識
3. 辨識信心足夠 → 顯示「上傳成功」，員工不需額外操作
4. 信心不足 → 跳出確認/修正畫面，員工僅需修正標示欄位

### 總務端

1. 登入後台 → 查看本月彙整儀表板
2. 審核例外項目（統編驗證失敗、疑似重複發票）
3. 一鍵匯出報表（Excel，依部門/類別分組）

---

## 📝 開發狀態

本專案為 AI 課程作品集專案。目前進度：

- ✅ **後端核心邏輯全部完成**：QR/AI 雙軌辨識、統編檢查碼與重複發票偵測、AI 支出分類、
  圖片壓縮備份（依 `[姓名][日期][發票號碼]` 命名）、Firebase 登入與角色權限驗證、
  總務審核與 Excel 報表匯出，共 139 個單元測試全數通過
- ✅ **前端六個頁面全部完成**：登入、上傳發票（含信心不足確認畫面）、我的上傳紀錄、
  總務儀表板、待審核清單（核准/退回）、匯出報表，已串接後端 API
- ⏳ **n8n 自動化流程尚未串接**（退回通知、定期彙整寄送、待審核提醒），
  後端已完成 webhook 密鑰驗證，實際整合留給使用者自行接手
- ⏳ 圖片備份僅本機儲存、尚無雲端儲存與檔案清理策略；重複發票偵測只在上傳當下判斷一次

---

## 📄 授權

本專案採用 [MIT License](LICENSE) 授權。
