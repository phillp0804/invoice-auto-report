"""環境變數讀取與設定管理。"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用程式設定，從 .env 檔案或環境變數讀取。"""

    # AI API
    anthropic_api_key: str = ""

    # Firebase
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""

    # 資料庫
    database_url: str = "sqlite:///./invoices.db"

    # 發票圖片備份儲存目錄
    upload_dir: str = "uploads"

    # 公司統編（用於比對發票買方統編是否為本公司）
    company_tax_id: str = ""

    # n8n webhook
    n8n_webhook_url: str = ""
    n8n_webhook_secret: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


def get_settings() -> Settings:
    """取得應用程式設定的單例。"""
    return Settings()
