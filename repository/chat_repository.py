
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.document_chunk_model import DocumentChunk
from models.document_model import Document
from typing import List

class ChatRepository:
    @staticmethod
    def get_document_chunk_by_context_id(db: Session, context_id: str):
        stmt = (
            select(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.context_id == context_id)
        )

        return db.scalars(stmt).all()
    
    @staticmethod
    def get_relevant_chunk_by_context_and_query(db: Session, document_ids: List[str], query: List[float], top_k: int=3):
        stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id.in_(document_ids))  # Ensure we filter by context
        .order_by(DocumentChunk.embedding.cosine_distance(query))  # Using pgvector function
        .limit(top_k)
    )        
        return db.execute(stmt).scalars().all()
    
