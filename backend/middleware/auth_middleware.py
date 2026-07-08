"""角色權限驗證中介層。

驗證使用者的 Firebase token，並依 users 資料表中的 role 欄位
決定是否有權限存取該 API 端點。
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """從請求中取得當前登入的使用者。

    從 Authorization header 取得 Firebase token，
    驗證後查詢使用者資料。

    Args:
        request: FastAPI Request 物件。
        db: 資料庫 session。

    Returns:
        使用者 ORM 物件。

    Raises:
        HTTPException: token 無效或使用者不存在。
    """
    # TODO: 驗證 Authorization header 中的 Firebase token
    # TODO: 從 token 取得 email，查詢 users 資料表
    raise NotImplementedError


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
