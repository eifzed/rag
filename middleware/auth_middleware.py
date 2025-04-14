from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
import time
import os
from fastapi.responses import JSONResponse




PUBLIC_PATHS = ["/", "", "/api/auth/login", "/api/auth/signup"]
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if request.method == "OPTIONS":
            return await call_next(request)
        
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(status_code=401, content="Authorization header missing")
        
        # Check if format is "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(status_code=401, content="Invalid authorization header format")
        
        token = parts[1]
        
        try:
            payload = AuthMiddleware.decode_jwt(token)
            
            # Check if token is expired
            if "exp" in payload and payload["exp"] < time.time():
                return JSONResponse(status_code=401, content="Token expired")
                
            request.state.user = payload
            
        except JWTError:
            return JSONResponse(status_code=401, content="Invalid token")
        
        return await call_next(request)

    @staticmethod
    def decode_jwt(token):
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])