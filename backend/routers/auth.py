# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.schemas import UserCreate, User, Token, UserRegister, UserResponse
from backend.crud import authenticate_user
from backend.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
import uuid
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user with email."""
    # Check if email already exists
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password
    password = user_data.password[:72] if user_data.password else ""
    hashed_password = get_password_hash(password)

    # Create user
    db_user = models.User(
        uuid=str(uuid.uuid4()),
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        is_email_verified=False,
        is_phone_verified=False,
        status='active',
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name
    )


@router.post("/users/", response_model=User)
def create_user_route(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user with hashed password (legacy endpoint)."""
    password = user.password[:72] if user.password else ""
    hashed_password = get_password_hash(password)
    db_user = models.User(
        uuid=str(uuid.uuid4()),
        email=user.username,  # Use username as email for legacy support
        password_hash=hashed_password,
        full_name=user.username,
        is_email_verified=False,
        is_phone_verified=False,
        status='active',
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User(
        id=db_user.id,
        username=db_user.email,
        role=user.role
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
