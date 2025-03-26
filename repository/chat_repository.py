
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.document_chunk_model import DocumentChunk
from models.document_model import Document
from typing import List
import numpy as np

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
        # First get candidates from database
        candidates = ChatRepository._fetch_candidate_chunks(db, document_ids, query, top_k)
        
        # Then filter and score them
        return ChatRepository._filter_chunks_by_similarity(candidates, query, top_k, similarity_threshold)
    
    @staticmethod
    def _fetch_candidate_chunks(db: Session, document_ids: List[str], query: List[float], top_k: int):
        """Fetch candidate chunks from the database ordered by vector similarity"""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id.in_(document_ids))
            .order_by(DocumentChunk.embedding.cosine_distance(query))
            .limit(top_k * 2)  # Retrieve more candidates initially
        )        
        return db.execute(stmt).scalars().all()
    
    @staticmethod
    def _filter_chunks_by_similarity(candidates, query: List[float], top_k: int, similarity_threshold: float):
        """Filter chunks by similarity threshold and return top_k most relevant"""
        candidates_with_scores = []
        
        for chunk in candidates:
            # Calculate cosine similarity manually
            chunk_embedding = np.array(chunk.embedding)
            query_embedding = np.array(query)
            
            norm_chunk = np.linalg.norm(chunk_embedding)
            norm_query = np.linalg.norm(query_embedding)
            
            if norm_chunk > 0 and norm_query > 0:
                cosine_similarity = np.dot(chunk_embedding, query_embedding) / (norm_chunk * norm_query)
                candidates_with_scores.append((chunk, cosine_similarity))
        
        # Filter by similarity threshold
        filtered_candidates = [chunk for chunk, score in candidates_with_scores if score >= similarity_threshold]
        
        # If we have enough chunks after filtering, return them (up to top_k)
        if len(filtered_candidates) >= top_k:
            return filtered_candidates[:top_k]
        
        # Otherwise, fall back to the original candidates (already sorted by the database)
        return [chunk for chunk, _ in candidates_with_scores][:top_k]
    
