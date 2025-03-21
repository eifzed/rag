from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List

from utils.database import get_db
from models.document_model import Document
from schemas.context_schema import ContextCreate, ContextResponse
from services.context_service import ContextService
from schemas.base_schema import BaseResponse

from utils.user import get_user_id_from_req

router = APIRouter()

@router.post("/contexts", response_model=ContextResponse)
async def create_context(
    request: Request,
    context_req: ContextCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new context with optional files
    """
    return ContextService.create_context(db, context_req, get_user_id_from_req(request))


@router.get("/contexts", response_model=List[ContextResponse])
def get_contexts(request: Request, name: str = None, db: Session = Depends(get_db)):
    """
    Get list of all contexts by user
    """

    return ContextService.get_context_list(db, name, get_user_id_from_req(request))

@router.get("/contexts/{context_id}", response_model=ContextResponse)
def get_context(request: Request, context_id: str, db: Session = Depends(get_db)):
    """
    Get a specific context by ID
    """
    return ContextService.get_detail(db, context_id, get_user_id_from_req(request))



@router.delete("/contexts/{context_id}", response_model=BaseResponse)
async def delete_context(
    context_id: str,
    db:Session = Depends(get_db)):
    """
    Delete context, documents, and document_chunk by context id
    """
    return ContextService.delete(db, context_id)

    