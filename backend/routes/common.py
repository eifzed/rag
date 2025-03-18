from fastapi import Header
from typing import Optional
from fastapi.responses import JSONResponse



async def get_token_header(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise JSONResponse(status_code=401, detail="Authorization header missing")
    
    # Check if format is "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise JSONResponse(status_code=401, detail="Invalid authorization header format")
    
    # Return just the token part
    return parts[1]