from sqlalchemy.orm import Session
from models.models import User

from fastapi import APIRouter, HTTPException, Depends, status, Header
import jwt
from schemas import UserCreateRequest, Token, UserResponse, LoginRequest
from utils.database import get_db
from services.auth_service import AuthService



router = APIRouter()



@router.post("/auth/signup", response_model=Token)
async def signup(user: UserCreateRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = AuthService.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = AuthService.create_user(db, user)
    
    # Create access token
    access_token = AuthService.create_access_token(
        data={"email": user.email, "id": user.id, "avatar_url": user.avatar_url}, expires_delta=AuthService.get_token_expire_minutes()
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/auth/login", response_model=Token)
async def login(user: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, user.email, user.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(
        data={"email": user.email, "id": user.id, "avatar_url": user.avatar_url}, expires_delta=AuthService.get_token_expire_minutes()
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(AuthService.get_current_user)):
    return current_user
