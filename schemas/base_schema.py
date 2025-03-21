from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class BaseResponse(BaseModel):
    status: int
    message: str
