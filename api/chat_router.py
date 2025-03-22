from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.orm import Session

from utils.database import get_db
from schemas.chat_schema import ChatRequest, ChatResponse
from services.chat_service import ChatService

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_with_context(
    request: Request,
    chat_request: ChatRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Chat with the assistant based on a specific context
    """
    return ChatService.chat_with_context(db, chat_request, request.state.user.get("id"))

   

