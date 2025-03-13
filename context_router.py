from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import get_db
from models import Context, Document, DocumentChunk
from schemas import ContextCreate, ContextResponse
from document_processor import DocumentProcessor

router = APIRouter()

@router.post("/contexts", response_model=ContextResponse)
async def create_context(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Create a new context with optional files
    """
    
    # Check if context already exists
    existing_context = db.query(Context).filter(Context.name == name).first()
    if existing_context:
        raise HTTPException(status_code=400, detail="Context with this name already exists")
    
    # Create new context
    context = Context(name=name, description=description)
    db.add(context)
    db.commit()
    db.refresh(context)
    
    # Process files if provided
    if files:
        for file in files:
            if file.content_type != "application/pdf":
                continue
                
            file_content = await file.read()
            
            # Save document to database
            document = Document(
                context_id=context.id,
                filename=file.filename,
                content_type=file.content_type,
                file_data=file_content
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Process document
            text = DocumentProcessor.extract_text_from_pdf(file_content)
            chunks = DocumentProcessor.chunk_text(text)
            
            # Save chunks with embeddings
            for i, chunk_text in enumerate(chunks):
                embedding = DocumentProcessor.get_embedding(chunk_text)
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=embedding
                )
                db.add(chunk)
            
            db.commit()
    
    return context

@router.get("/contexts", response_model=List[ContextResponse])
def get_contexts(db: Session = Depends(get_db)):
    """
    Get list of all contexts
    """
    contexts = db.query(Context).all()
    return contexts

@router.get("/contexts/{context_id}", response_model=ContextResponse)
def get_context(context_id: str, db: Session = Depends(get_db)):
    """
    Get a specific context by ID
    """
    context = db.query(Context).filter(Context.id == context_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return context