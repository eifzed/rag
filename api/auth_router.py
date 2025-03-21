from sqlalchemy.orm import Session
from models.user_model import User

from fastapi import APIRouter, Depends
import jwt
from schemas.user_schema import UserCreateRequest, Token, UserResponse, LoginRequest
from utils.database import get_db
from services.auth_service import AuthService



router = APIRouter()


@router.post("/auth/signup", response_model=Token)
async def signup(user: UserCreateRequest, db: Session = Depends(get_db)):
    return AuthService.register_user(db, user)


@router.post("/auth/login", response_model=Token)
async def login(user: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.login_user(db, user.email, user.password)
    


@router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(AuthService.get_current_user)):
            return current_user
