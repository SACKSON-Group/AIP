# auth.py
"""
Authentication module - re-exports from security.py for backward compatibility.
All authentication logic is centralized in security.py.
"""
from backend.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    get_current_user,
    get_current_active_user,
    get_current_admin,
    require_role,
    authenticate_user,
    oauth2_scheme,
    pwd_context,
)
from backend.config import settings

# Re-export settings for backward compatibility
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin",
    "require_role",
    "authenticate_user",
    "oauth2_scheme",
    "pwd_context",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
]
