from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from schemas.document_schema import DocumentResponse

class ContextBase(BaseModel):
    name: str
    description: Optional[str] = None

class ContextCreate(ContextBase):
    pass

class ContextResponse(ContextBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    files: Optional[List[DocumentResponse]] = None

    class Config:
        from_attributes = True


class ContextResponse(ContextBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    files: Optional[List[DocumentResponse]] = None

    class Config:
        from_attributes = True