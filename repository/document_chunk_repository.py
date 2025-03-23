from sqlalchemy.orm import Session
from typing import List
from models.document_chunk_model import DocumentChunk
from sqlalchemy import delete


class DocumentChunkRepository:
    @staticmethod
    def delete_by_document_ids(db: Session, doc_ids: List[str]):
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id.in_(doc_ids)))

    @staticmethod
    def insert(db:Session, document_chunk: DocumentChunk):
        db.add(document_chunk)
    
    @staticmethod
    def insert_bulk(db:Session, document_chunk: List[DocumentChunk]):
        db.bulk_save_objects(document_chunk)