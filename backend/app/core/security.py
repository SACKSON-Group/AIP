"""Authentication and security utilities."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt  # PyJWT
import bcrypt
from .config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Handle bcrypt 72-byte limit
    truncated = (plain_password[:72] if plain_password else "").encode('utf-8')
    return bcrypt.checkpw(truncated, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    # Handle bcrypt 72-byte limit
    truncated = (password[:72] if password else "").encode('utf-8')
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt())
    return hashed.decode('utf-8')


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_EXPIRATION_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None
