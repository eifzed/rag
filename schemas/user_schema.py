from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: EmailStr
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreateRequest(UserBase):
    password: str = Field(..., min_length=8)


class LoginRequest(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None