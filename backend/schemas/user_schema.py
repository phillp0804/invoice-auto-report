"""使用者相關的 Pydantic schema。"""

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """使用者基底 schema。"""
    name: str
    email: str
    role: str  # "employee" 或 "admin"
    department_id: int | None = None


class UserCreate(UserBase):
    """建立使用者時的輸入 schema。"""
    pass


class UserResponse(UserBase):
    """使用者回傳 schema。"""
    id: int

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """登入請求 schema（搭配 Firebase token）。"""
    firebase_token: str


class LoginResponse(BaseModel):
    """登入回傳 schema。"""
    access_token: str
    user: UserResponse
