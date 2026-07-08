"""資料庫連線與 session 管理。"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 專用
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有 ORM 模型的基底類別。"""
    pass


def get_db():
    """FastAPI 依賴注入用：提供資料庫 session，結束時自動關閉。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建立所有資料表（開發用）。"""
    Base.metadata.create_all(bind=engine)
