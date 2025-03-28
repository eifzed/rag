
from models.document_model import Document, UploadStatus
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import delete, and_, func
from utils.database import get_db


class DocumentRepository:
    @staticmethod
    def get_by_context_id(db:Session, context_id):
        return db.query(Document.id, Document.filename, Document.context_id, Document.content_type, Document.created_at, Document.upload_status).filter(Document.context_id == context_id).order_by(Document.created_at.desc()).all()
    
    @staticmethod
    def get_by_id(db:Session, id):
        return db.query(Document).filter(Document.id == id).first()
    
    @staticmethod
    def get_unfinished_by_id(db:Session, id):
        return db.query(Document).filter(and_(Document.id == id, Document.upload_status != UploadStatus.SUCCESS.value)).first()

    @staticmethod
    def insert(db:Session, document: Document):
        db.add(document)

    @staticmethod
    def delete_by_ids(db: Session, ids: List[str]):
        db.execute(delete(Document).where(Document.id.in_(ids)))
    
    @staticmethod
    def get_by_id_and_context_id(db:Session, id, context_id):
        return db.query(Document).filter(Document.id == id, Document.context_id == context_id).first()
    
    @staticmethod
    def get_number_of_documents_by_context_id(db:Session, context_id):
        return db.query(func.count(Document.id)).filter(Document.context_id == context_id).scalar()
    