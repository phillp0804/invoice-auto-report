"""角色權限驗證中介層的單元測試（不呼叫真實 Firebase）。"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from middleware.auth_middleware import get_current_user, require_role
from models.user import User


@pytest.fixture()
def db_session():
    """提供獨立的記憶體 SQLite session。"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _request_with_header(header_value: str | None) -> MagicMock:
    headers = {"Authorization": header_value} if header_value is not None else {}
    return MagicMock(headers=headers)


class TestGetCurrentUser:
    """get_current_user() 測試。"""

    def test_missing_authorization_header_raises_401(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_request_with_header(None), db_session)

        assert exc_info.value.status_code == 401

    def test_non_bearer_scheme_raises_401(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_request_with_header("Basic abc123"), db_session)

        assert exc_info.value.status_code == 401

    def test_invalid_firebase_token_raises_401(self, db_session):
        with (
            patch("middleware.auth_middleware.get_firebase_app"),
            patch(
                "middleware.auth_middleware.firebase_auth.verify_id_token",
                side_effect=ValueError("bad token"),
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(_request_with_header("Bearer bad-token"), db_session)

        assert exc_info.value.status_code == 401

    def test_valid_token_but_user_not_found_raises_401(self, db_session):
        with (
            patch("middleware.auth_middleware.get_firebase_app"),
            patch(
                "middleware.auth_middleware.firebase_auth.verify_id_token",
                return_value={"email": "nobody@example.com"},
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(_request_with_header("Bearer valid-token"), db_session)

        assert exc_info.value.status_code == 401

    def test_valid_token_returns_matching_user(self, db_session):
        user = User(name="小明", email="ming@example.com", role="employee")
        db_session.add(user)
        db_session.commit()

        with (
            patch("middleware.auth_middleware.get_firebase_app"),
            patch(
                "middleware.auth_middleware.firebase_auth.verify_id_token",
                return_value={"email": "ming@example.com"},
            ),
        ):
            result = get_current_user(
                _request_with_header("Bearer valid-token"), db_session
            )

        assert result.email == "ming@example.com"
        assert result.role == "employee"


class TestRequireRole:
    """require_role() 測試。"""

    def test_matching_role_passes(self):
        checker = require_role("employee")
        user = MagicMock(role="employee")

        assert checker(current_user=user) is user

    def test_admin_bypasses_any_required_role(self):
        """總務（admin）應可存取員工專屬與總務專屬的 API。"""
        checker = require_role("employee")
        admin_user = MagicMock(role="admin")

        assert checker(current_user=admin_user) is admin_user

    def test_mismatched_role_raises_403(self):
        """員工不可存取總務專屬 API（core rule 6）。"""
        checker = require_role("admin")
        employee_user = MagicMock(role="employee")

        with pytest.raises(HTTPException) as exc_info:
            checker(current_user=employee_user)

        assert exc_info.value.status_code == 403
