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

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 5)) * 1024 * 1024
MAX_TEXT_SIZE = int(os.getenv("MAX_TEXT_CHAR_COUNT", 10000))

@router.post("/contexts/{context_id}/documents", response_model=List[DocumentResponse])
async def update_context_file(
    request: Request,
    context_id: str = Path(...), 
    files: List[UploadFile] = File(None),
    db:Session = Depends(get_db)):
    """
    Add new file to existing context
    """
    
    if not files:
        raise HTTPException(status_code=403, detail="Please provide the files to be uploaded")
    real_file_size = 0

    for chunk in files.file:
        real_file_size += len(chunk)
        if real_file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too large")
        
    documents = await ContextService.upload_context_file(db, context_id, get_user_id_from_req(request), files)
    return documents


@router.post("/contexts/{context_id}/text", response_model=List[DocumentResponse])
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
    
    documents = await ContextService.upload_context_text(db, context_id, get_user_id_from_req(request), text_data)
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