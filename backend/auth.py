# auth.py - supports both Supabase JWTs and internal AIP JWTs
import os
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from backend.models import User as UserModel
from backend.database import get_db
from backend.schemas import Token, User as UserSchema

# Internal AIP JWT secret (legacy)
SECRET_KEY = os.environ.get("SECRET_KEY", "aip-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Supabase JWT secret for verifying frontend tokens
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
http_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash using bcrypt directly."""
    truncated = (plain_password[:72] if plain_password else "").encode('utf-8')
    return bcrypt.checkpw(truncated, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly."""
    truncated = (password[:72] if password else "").encode('utf-8')
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials

    # 1. Try Supabase JWT first (frontend sends these)
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=[ALGORITHM],
                options={"verify_aud": False}
            )
            email = payload.get("email")
            sub = payload.get("sub")

            if email or sub:
                # Try to find local user by email
                user = None
                if email:
                    user = db.query(UserModel).filter(UserModel.email == email).first()

                if user:
                    return user

                # User authenticated via Supabase but not in local DB yet
                # Create a transient user object so endpoint can proceed
                transient_user = UserModel()
                transient_user.email = email or sub
                transient_user.role = "user"
                return transient_user

        except JWTError:
            pass  # Fall through to try internal JWT

    # 2. Try internal AIP JWT (legacy / server-issued tokens)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        user = db.query(UserModel).filter(UserModel.id == int(username)).first()
    except (ValueError, TypeError):
        user = db.query(UserModel).filter(UserModel.email == username).first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
