from sqlalchemy.orm import Session
from schemas.user_schema import UserCreateRequest
from models.user_model import User
from utils.encryption import get_password_hash


class UserRepository:
    @staticmethod
    def create_user(db: Session, user: UserCreateRequest):
        hashed_password = get_password_hash(user.password)
        db_user = User(email=user.email, hashed_password=hashed_password, avatar_url=user.avatar_url)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, id: int):
        return db.query(User).filter(User.id == id).first()