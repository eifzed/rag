from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.models import User

from fastapi import HTTPException, Depends, status
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from typing import Optional
from schemas import UserCreateRequest
from utils.database import get_db
from dotenv import load_dotenv
import os



load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthService:
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, id: int):
        return db.query(User).filter(User.id == id).first()
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return False
        if not AuthService.verify_password(password, user.hashed_password):
            return False
        return user

    @staticmethod
    def create_user(db: Session, user: UserCreateRequest):
        hashed_password = AuthService.get_password_hash(user.password)
        db_user = User(email=user.email, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        user_id = None
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("id")
            if user_id is None:
                raise credentials_exception
        except jwt.PyJWTError:
            raise credentials_exception
        
        user = AuthService.get_user_by_id(db, id=user_id)
        if user is None:
            raise credentials_exception
        return user
    
    @staticmethod
    def get_token_expire_minutes() -> timedelta:
        return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)