# routers/auth.py
"""
Authentication endpoints for the AFCARE platform.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.schemas import UserCreate, User, Token
from backend.crud import create_user, get_user_by_username, authenticate_user
from backend.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **username**: Unique username (3-50 characters)
    - **password**: Password (min 8 chars, must include uppercase, lowercase, and digit)
    - **role**: User role (investor, sponsor, analyst)
    """
    # Check if username already exists
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create the user
    db_user = create_user(db, user)
    return db_user


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login.

    Returns an access token for valid credentials.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Alternative login endpoint (alias for /token).
    """
    return login_for_access_token(form_data, db)
