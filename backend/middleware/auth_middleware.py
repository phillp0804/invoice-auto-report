"""角色權限驗證中介層。

驗證使用者的 Firebase token，並依 users 資料表中的 role 欄位
決定是否有權限存取該 API 端點。
"""

import firebase_admin
from fastapi import Depends, HTTPException, Request
from firebase_admin import credentials
from firebase_admin import auth as firebase_auth
from firebase_admin import exceptions as firebase_exceptions
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models.user import User

_firebase_app: firebase_admin.App | None = None


def get_firebase_app() -> firebase_admin.App:
    """取得 Firebase Admin App 單例，第一次呼叫時才初始化。

    整個後端共用同一個 Firebase App 實例（例如 auth_router.py 的登入端點
    也會呼叫這個函式）：firebase_admin.initialize_app() 對同一個 app name
    重複呼叫會拋出例外，所以初始化邏輯只能有這一份。
    """
    global _firebase_app
    if _firebase_app is None:
        settings = get_settings()
        cred = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "client_email": settings.firebase_client_email,
                # .env 中的換行通常會被跳脫成 "\n" 字面字串，需還原成真正換行
                "private_key": settings.firebase_private_key.replace("\\n", "\n"),
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """從請求中取得當前登入的使用者。

    從 Authorization header 取得 Firebase token，
    驗證後查詢使用者資料。

    Args:
        request: FastAPI Request 物件。
        db: 資料庫 session。

    Returns:
        使用者 ORM 物件。

    Raises:
        HTTPException: token 缺失、格式錯誤、驗證失敗，或使用者不存在。
    """
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401, detail="缺少或格式錯誤的 Authorization header"
        )

    try:
        decoded_token = firebase_auth.verify_id_token(token, app=get_firebase_app())
    except (firebase_exceptions.FirebaseError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Firebase token 無效") from exc

    email = decoded_token.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token 缺少 email 欄位")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="使用者不存在，請聯繫總務建立帳號")

    return user


def require_role(required_role: str):
    """角色權限驗證裝飾器。

    Args:
        required_role: 需要的角色（"employee" 或 "admin"）。

    Returns:
        依賴注入函式，驗證使用者角色是否符合。
    """

    def role_checker(current_user=Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail=f"需要 {required_role} 權限",
            )
        return current_user

    return role_checker
