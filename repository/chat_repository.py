
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
    def get_relevant_chunk_by_context_and_query(db: Session, document_ids: List[str], query: List[float], top_k: int=3, similarity_threshold: float=0.75):
        # First attempt: Get chunks with high similarity
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id.in_(document_ids))
            .order_by(DocumentChunk.embedding.cosine_distance(query))
            .limit(top_k * 2)  # Retrieve more candidates initially
        )        
        candidates = db.execute(stmt).scalars().all()
        
        # Filter by similarity threshold if we have enough candidates
        filtered_candidates = [
            chunk for chunk in candidates 
            if 1 - DocumentChunk.embedding.cosine_distance(chunk.embedding, query) >= similarity_threshold
        ]
        
        # If we have enough chunks after filtering, return them (up to top_k)
        if len(filtered_candidates) >= top_k:
            return filtered_candidates[:top_k]
        
        # Otherwise, fall back to the original candidates
        return candidates[:top_k]
    
