
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.document_chunk_model import DocumentChunk
from models.document_model import Document

class ChatRepository:
    @staticmethod
    def get_document_chunk_by_context_id(db: Session, context_id: str):
        stmt = (
            select(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.context_id == context_id)
        )

        return db.scalars(stmt).all()
    
