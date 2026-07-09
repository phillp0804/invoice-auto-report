"""認證路由（auth_router）的單元測試（不呼叫真實 Firebase）。"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.user import User
from routers.auth_router import login
from schemas.user_schema import LoginRequest


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _mock_firebase(decoded_token=None, side_effect=None):
    """回傳一組已 patch 好 get_firebase_app / verify_id_token 的 context manager 清單。"""
    kwargs = {"side_effect": side_effect} if side_effect else {"return_value": decoded_token}
    return (
        patch("routers.auth_router.get_firebase_app"),
        patch("routers.auth_router.firebase_auth.verify_id_token", **kwargs),
    )


class TestLogin:
    """login() 測試。"""

    def test_existing_user_returns_without_creating_duplicate(self, db_session):
        existing = User(name="小明", email="ming@example.com", role="admin")
        db_session.add(existing)
        db_session.commit()

        patch_app, patch_verify = _mock_firebase({"email": "ming@example.com"})
        with patch_app, patch_verify:
            result = login(LoginRequest(firebase_token="valid-token"), db_session)

        assert result.user.email == "ming@example.com"
        assert result.user.role == "admin"  # 沿用既有帳號的角色，不會被登入覆寫
        assert db_session.query(User).count() == 1

    def test_new_user_auto_created_with_employee_role(self, db_session):
        patch_app, patch_verify = _mock_firebase(
            {"email": "new@example.com", "name": "新同事"}
        )
        with patch_app, patch_verify:
            result = login(LoginRequest(firebase_token="valid-token"), db_session)

        assert result.user.email == "new@example.com"
        assert result.user.name == "新同事"
        assert result.user.role == "employee"
        assert db_session.query(User).filter(User.email == "new@example.com").count() == 1

    def test_new_user_without_name_claim_falls_back_to_email_prefix(self, db_session):
        patch_app, patch_verify = _mock_firebase({"email": "noname@example.com"})
        with patch_app, patch_verify:
            result = login(LoginRequest(firebase_token="valid-token"), db_session)

        assert result.user.name == "noname"

    def test_access_token_echoes_firebase_token(self, db_session):
        patch_app, patch_verify = _mock_firebase({"email": "ming@example.com"})
        with patch_app, patch_verify:
            result = login(LoginRequest(firebase_token="the-firebase-token"), db_session)

        assert result.access_token == "the-firebase-token"

    def test_invalid_token_raises_401(self, db_session):
        patch_app, patch_verify = _mock_firebase(side_effect=ValueError("bad token"))
        with patch_app, patch_verify:
            with pytest.raises(HTTPException) as exc_info:
                login(LoginRequest(firebase_token="bad-token"), db_session)

        assert exc_info.value.status_code == 401

    def test_token_missing_email_raises_401(self, db_session):
        patch_app, patch_verify = _mock_firebase({"uid": "abc123"})
        with patch_app, patch_verify:
            with pytest.raises(HTTPException) as exc_info:
                login(LoginRequest(firebase_token="valid-token"), db_session)

        assert exc_info.value.status_code == 401
