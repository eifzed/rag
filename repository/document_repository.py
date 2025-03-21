
from models.document_model import Document
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import delete


class DocumentRepository:
    @staticmethod
    def get_by_context_id(db:Session, context_id):
        return db.query(Document).filter(Document.context_id == context_id).all()
    
    @staticmethod
    def insert(db:Session, document: Document):
        db.add(document)

    @staticmethod
    def delete_by_ids(db: Session, ids: List[str]):
        db.execute(delete(Document).where(Document.id.in_(ids)))
    
    @staticmethod
    def get_by_id_and_context_id(db:Session, id, context_id):
        return db.query(Document).filter(Document.id == id, Document.context_id == context_id).first()
    