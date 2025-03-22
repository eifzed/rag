
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Set, Optional


class ScrapingRequest(BaseModel):
    url: HttpUrl
    depth: int = 1

class ScrapingResponse(BaseModel):
    url: str
    content: str
    links: Optional[List[Dict[str, str]]] = None

    