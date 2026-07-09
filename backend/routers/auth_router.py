"""認證路由：登入與角色驗證。"""

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import auth as firebase_auth
from firebase_admin import exceptions as firebase_exceptions
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth_middleware import get_firebase_app
from models.user import User
from schemas.user_schema import LoginRequest, LoginResponse, UserResponse

router = APIRouter()

# 首次登入自動建立的帳號一律為員工，避免任何人透過登入自我授予總務權限；
# 升級為總務須由既有管理流程另外調整資料庫的 role 欄位。
_DEFAULT_ROLE = "employee"


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """登入端點：搭配 Firebase token 驗證，回傳使用者資訊與 access token。"""
    try:
        decoded_token = firebase_auth.verify_id_token(
            request.firebase_token, app=get_firebase_app()
        )
    except (firebase_exceptions.FirebaseError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Firebase token 無效") from exc

    email = decoded_token.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token 缺少 email 欄位")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            name=decoded_token.get("name") or email.split("@")[0],
            email=email,
            role=_DEFAULT_ROLE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return LoginResponse(
        access_token=request.firebase_token,
        user=UserResponse.model_validate(user),
    )
