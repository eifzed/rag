import logging
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Save logs to app.log
        logging.StreamHandler()  # Also print logs to console
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the full error with traceback
            logger.exception("Unhandled exception occurred")  # Logs full traceback
            
            # Ensure logs are written immediately
            for handler in logger.handlers:
                handler.flush()

            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "detail": str(e)}
            )