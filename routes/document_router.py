from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path, Request
from sqlalchemy.orm import Session
from typing import List

from utils.database import get_db
from models.models import Context, Document, DocumentChunk
from schemas import DocumentResponse
from utils.document_processor import DocumentProcessor
from routes.context_helper import insert_context_document
from sqlalchemy import delete
from fastapi.responses import StreamingResponse
import io



router = APIRouter()

@router.post("/contexts/{context_id}/documents", response_model=List[DocumentResponse])
async def add_document(
    request: Request,
    context_id: str = Path(...),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Add new file to existing context
    """
    context = db.query(Context).filter(Context.id == context_id, Context.owner_id == request.state.user.get("id")).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    if not files or len(files) == 0:
        raise HTTPException(status_code=404, detail="a document must be provided")
    
    inserted_docs = await insert_context_document(context.id, files, db)

    return inserted_docs

@router.get("/contexts/{context_id}/documents", response_model=List[DocumentResponse])
def get_documents_by_context(
    request: Request,
    context_id: str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Get list of documents for a specific context
    """
    # Check if context exists
    context = db.query(Context).filter(Context.id == context_id, Context.owner_id == request.state.user.get("id")).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    documents = db.query(Document).filter(Document.context_id == context_id).all()
    return documents

@router.delete("/contexts/{context_id}/documents/{document_id}")
def delete_document(
    request: Request,
    context_id: str = Path(...),
    document_id: str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Delete a document and its chunks
    """
    context = db.query(Document).filter(Document.id == document_id, Context.owner_id == request.state.user.get("id")).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    db.execute(delete(Document).where(Document.id == document_id))    
    
    db.commit()
    
    return {"message": "Document deleted successfully"}

@router.get("/download/{document_id}")
def delete_document(
    request: Request,
    document_id: str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Download a document
    """
    user_id = request.state.user.get("id")
    context = db.query(Context).filter(Context.owner_id == user_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    document = db.query(Document).filter(Document.id == document_id, Document.context_id == context.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Context not found")
    

    response = StreamingResponse(io.BytesIO(document.file_data), media_type=document.content_type, headers={"Content-Disposition": f'attachment; filename="{document.filename}"'})
    response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
    return response