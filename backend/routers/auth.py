# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.schemas import UserCreate, User, Token
from backend.crud import authenticate_user
from backend.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/users/", response_model=User)
def create_user_route(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user with hashed password."""
    # Hash the password before storing (truncate to 72 bytes for bcrypt limit)
    password = user.password[:72] if user.password else ""
    hashed_password = get_password_hash(password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User(
        id=db_user.id,
        username=db_user.username,
        role=db_user.role
    )


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Use email if available, otherwise username
    user_identifier = getattr(user, 'email', None) or getattr(user, 'username', str(user.id))
    full_name = getattr(user, 'full_name', user_identifier)
    role = getattr(user, 'role', 'user')
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user_identifier,
            "full_name": full_name,
            "role": role,
        }, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
