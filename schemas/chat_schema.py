from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    context_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None