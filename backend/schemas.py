from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

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
    id: str
    context_id: str
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
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    files: Optional[List[DocumentResponse]] = None

    class Config:
        from_attributes = True