from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path
from sqlalchemy.orm import Session
from typing import List

from utils.database import get_db
from models.models import Context, Document, DocumentChunk
from schemas import DocumentResponse
from utils.document_processor import DocumentProcessor

router = APIRouter()

@router.post("/contexts/{context_id}/documents", response_model=DocumentResponse)
async def add_document(
    context_id: str = Path(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Add a new document to a context
    """
    # Check if context exists
    context = db.query(Context).filter(Context.id == context_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Check file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read file content
    file_content = await file.read()
    
    # Save document to database
    document = Document(
        context_id=context_id,
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
    
    return document

@router.get("/contexts/{context_id}/documents", response_model=List[DocumentResponse])
def get_documents_by_context(
    context_id: str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Get list of documents for a specific context
    """
    # Check if context exists
    context = db.query(Context).filter(Context.id == context_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    documents = db.query(Document).filter(Document.context_id == context_id).all()
    return documents

@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Delete a document and its chunks
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete document (cascade will delete chunks)
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}