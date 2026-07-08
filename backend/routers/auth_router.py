"""認證路由：登入與角色驗證。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.user_schema import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """登入端點：搭配 Firebase token 驗證，回傳使用者資訊與 access token。"""
    # TODO: 驗證 Firebase token，查詢或建立使用者，回傳登入結果
    raise NotImplementedError
