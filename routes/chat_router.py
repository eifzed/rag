from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session

from utils.database import get_db
from models.models import Context, Document
from schemas import ChatRequest, ChatResponse
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
    # Check if context exists
    context = db.query(Context).filter(Context.id == chat_request.context_id, Context.owner_id == request.state.user.get("id")).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    context = db.query(Document).filter(Document.context_id == chat_request.context_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Get embedding for the query
    query_embedding = ChatService.get_embedding(chat_request.message)
    
    # Retrieve relevant chunks
    relevant_chunks = ChatService.retrieve_relevant_chunks(
        db=db, 
        context_id=chat_request.context_id, 
        query_embedding=query_embedding
    )
    
    if not relevant_chunks:
        return ChatResponse(
            response="I don't have enough information to answer that question based on the available documents.",
            sources=[]
        )
    
    # Generate response
    response_data = ChatService.generate_response(
        query=chat_request.message,
        context_chunks=relevant_chunks,
        history=chat_request.history
    )
    
    return ChatResponse(
        response=response_data["response"],
        sources=response_data["sources"]
    )

