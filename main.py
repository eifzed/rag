import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import tornado.ioloop
from middleware.payload_size_middleware import PayloadSizeMiddleware


# Fix the imports to use the correct file paths
from api.context_router import router as context_router
from api.document_router import router as document_router
from api.chat_router import router as chat_router
from api.auth_router import router as auth_router
from api.scrape_router import router as scrape_router
from middleware.auth_middleware import AuthMiddleware
from middleware.log_middleware import LoggingMiddleware
from dotenv import load_dotenv

load_dotenv()

def run_nsq_consumers():
    # Start the NSQ consumers in a separate thread
    tornado.ioloop.IOLoop.instance().start()

app = FastAPI(title="RAG LLM System")

# app.add_middleware(LoggingMiddleware)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 5))

app.add_middleware(AuthMiddleware)

app.add_middleware(PayloadSizeMiddleware, max_size=MAX_FILE_SIZE_MB*1024 * 1024)

# Include routers
app.include_router(context_router, prefix="/api", tags=["contexts"])
app.include_router(document_router, prefix="/api", tags=["documents"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(scrape_router, prefix="/api", tags=["scrape"])

@app.get("/")
def read_root():
    return {"message": "Welcome to RAG LLM System"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)