from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from fastapi import HTTPException, Depends, status
from passlib.context import CryptContext
from schemas.user_schema import UserCreateRequest
from utils.database import get_db


from utils.encryption import verify_password, create_access_token, get_jwt_payload, get_token_expire_minutes
from repository.user_repository import UserRepository


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthService:
    @staticmethod
    def login_user(db: Session, email: str, password: str):
        user = UserRepository.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = create_access_token(data={"email": user.email, "id": user.id, "avatar_url": user.avatar_url}, expires_delta=get_token_expire_minutes())
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
    
    @staticmethod
    def register_user(db: Session, user: UserCreateRequest):
        db_user = UserRepository.get_user_by_email(db, user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        created_user = UserRepository.create_user(db, user)

        token =  create_access_token( data={"email": created_user.email, "id": created_user.id, "avatar_url": created_user.avatar_url}, expires_delta=get_token_expire_minutes())
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": created_user
        }
    

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        payload = get_jwt_payload(token)
        
        user = UserRepository.get_user_by_id(db, id=payload.get("id"))
        if user is None:
            raise credentials_exception
        return user