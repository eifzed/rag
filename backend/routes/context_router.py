from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from utils.database import get_db
from models.models import Context, Document, DocumentChunk
from schemas import ContextCreate, ContextResponse, BaseResponse
from sqlalchemy import delete

from routes.context_helper import insert_context_document

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
        await insert_context_document(context.id, files, db)
        
    return ContextResponse.model_validate(context)



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
    
    files = db.query(Document).filter(Document.context_id == context.id).all()

    return ContextResponse(id=context.id, created_at=context.created_at, description=context.description, files=files, name=context.name, updated_at=context.updated_at)

@router.post("/contexts/{context_id}/file", response_model=ContextResponse)
async def update_context_file(
    context_id: str, 
    files: List[UploadFile] = File(None),
    db:Session = Depends(get_db)):
    """
    Add new file to existing context
    """
    context = db.query(Context).filter(Context.id == context_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    if not files:
        raise HTTPException(status_code=403, detail="Please provide the files to be uploaded")
    await insert_context_document(context.id, files, db)

    return ContextResponse.model_validate(context)


@router.delete("/contexts/{context_id}", response_model=BaseResponse)
async def delete_context(
    context_id: str,
    db:Session = Depends(get_db)):
    """
    Delete context, documents, and document_chunk by context id
    """
    context = db.query(Context).filter(Context.id == context_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")

    documents = db.query(Document).filter(Document.context_id == context_id).all()

    doc_ids = []

    for doc in documents:
        doc_ids.append(doc.id)

    if len(doc_ids) > 0:
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id.in_ == doc_ids))
        db.execute(delete(Document).where(Document.id.in_ == doc_ids))    
    
    db.execute(delete(Context).where(Context.id == context_id))

    db.commit()
    return BaseResponse(message="deleted", status=200)

    