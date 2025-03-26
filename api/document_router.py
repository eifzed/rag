from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path, Request, status
from sqlalchemy.orm import Session
from typing import List

from utils.database import get_db
from schemas.document_schema import DocumentResponse, DocumentText
from services.context_service import ContextService
from utils.user import get_user_id_from_req

from services.document_service import DocumentService
import os

router = APIRouter()

MAX_TEXT_SIZE = int(os.getenv("MAX_TEXT_CHAR_COUNT", 10000))

@router.post("/contexts/{context_id}/documents", response_model=DocumentResponse)
async def update_context_file(
    request: Request,
    context_id: str = Path(...), 
    file: UploadFile = File(...),
    db:Session = Depends(get_db)):
    """
    Add new file to existing context
    """
    
    if not file:
        raise HTTPException(status_code=403, detail="Please provide the files to be uploaded")
    

    document = await ContextService.upload_context_file(db, context_id, get_user_id_from_req(request), file)
    return document


@router.post("/contexts/{context_id}/text", response_model=DocumentResponse)
async def update_context_text(
    request: Request,
    context_id: str = Path(...), 
    text_data: DocumentText = None,
    db:Session = Depends(get_db)):
    """
    Add new file to existing context
    """
    
    if not text_data.content or not text_data.filename:
        raise HTTPException(status_code=403, detail="Please provide the name and content to be uploaded")
    
    if len(text_data.content) > MAX_TEXT_SIZE:
        raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too large")
    
    document = await ContextService.upload_context_text(db, context_id, get_user_id_from_req(request), text_data)
    return document


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
    
    return DocumentService.delete_document(db, document_id, context_id, get_user_id_from_req(request))

@router.get("/download/{context_id}/{document_id}")
def download_document(
    request: Request,
    document_id: str = Path(...),
    context_id:str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Download a document
    """
    
    return DocumentService.download_document(db, document_id, context_id, get_user_id_from_req(request))