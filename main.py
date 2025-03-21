import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


# Fix the imports to use the correct file paths
from api.context_router import router as context_router
from api.document_router import router as document_router
from api.chat_router import router as chat_router
from api.auth_router import router as auth_router
from utils.database import create_tables
from middleware.auth_middleware import AuthMiddleware

app = FastAPI(title="RAG LLM System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Add JWT middleware separately
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(context_router, prefix="/api", tags=["contexts"])
app.include_router(document_router, prefix="/api", tags=["documents"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(auth_router, prefix="/api", tags=["auth"])

# @app.on_event("startup")
# async def startup_event():
#     create_tables()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()  # Run on startup
    yield  # Hand over control to the application
    print("Shutting down...")  # Cleanup (optional)

@app.get("/")
def read_root():
    return {"message": "Welcome to RAG LLM System"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)