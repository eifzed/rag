from fastapi import FastAPI, Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from typing import List, Optional
import time
from dotenv import load_dotenv
import os
from fastapi.responses import JSONResponse




PUBLIC_PATHS = ["/api/auth/login", "/api/auth/signup"]
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

load_dotenv()

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check if the path should be excluded from authentication
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(status_code=401, content="Authorization header missing")
        
        # Check if format is "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(status_code=401, content="Invalid authorization header format")
        
        token = parts[1]
        
        try:
            # Decode and verify the JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check if token is expired
            if "exp" in payload and payload["exp"] < time.time():
                return JSONResponse(status_code=401, content="Token expired")
                
            # You can add the payload to the request state for later use in endpoints
            request.state.user = payload
            
        except JWTError:
            return JSONResponse(status_code=401, content="Invalid token")
        
        # Continue processing the request
        return await call_next(request)