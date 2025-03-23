import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from messaging.embed_document import start_nsq_consumer, close_consumer_conn
from services.document_service import DocumentService
import threading
import tornado.ioloop





# Fix the imports to use the correct file paths
from api.context_router import router as context_router
from api.document_router import router as document_router
from api.chat_router import router as chat_router
from api.auth_router import router as auth_router
from api.scrape_router import router as scrape_router
from utils.database import create_tables
from middleware.auth_middleware import AuthMiddleware
from middleware.log_middleware import LoggingMiddleware
from dotenv import load_dotenv

load_dotenv()

def run_nsq_consumers():
    # Start the NSQ consumers in a separate thread
    tornado.ioloop.IOLoop.instance().start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=======lifespan======")
    start_nsq_consumer("embed_document", "embed_document_worker", DocumentService.process_background_document_embedding)
    nsq_thread = threading.Thread(target=run_nsq_consumers, daemon=True)
    nsq_thread.start()

    yield  # Hand over control to the application
    await close_consumer_conn()
    print("Shutting down...")

app = FastAPI(title="RAG LLM System", lifespan=lifespan)

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

app.add_middleware(AuthMiddleware)


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