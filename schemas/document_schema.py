from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.document_model import UploadStatus
import uuid


class DocumentBase(BaseModel):
    filename: str
    content_type: str
    upload_status: Optional[UploadStatus] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: uuid.UUID
    context_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentText(DocumentBase):
    content: str