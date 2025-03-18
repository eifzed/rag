from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class ContextBase(BaseModel):
    name: str
    description: Optional[str] = None

class ContextCreate(ContextBase):
    pass



class DocumentBase(BaseModel):
    filename: str
    content_type: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: uuid.UUID
    context_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    context_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None


class ContextResponse(ContextBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    files: Optional[List[DocumentResponse]] = None

    class Config:
        from_attributes = True

class BaseResponse(BaseModel):
    status: int
    message: str


class UserBase(BaseModel):
    email: EmailStr

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
