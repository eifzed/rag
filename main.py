import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Fix the imports to use the correct file paths
from context_router import router as context_router
from document_router import router as document_router
from chat_router import router as chat_router
from database import create_tables

app = FastAPI(title="RAG LLM System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(context_router, prefix="/api", tags=["contexts"])
app.include_router(document_router, prefix="/api", tags=["documents"])
app.include_router(chat_router, prefix="/api", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
def read_root():
    return {"message": "Welcome to RAG LLM System"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)