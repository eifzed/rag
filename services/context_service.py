
from sqlalchemy.orm import Session
from models.context_model import Context
from fastapi import HTTPException, UploadFile
from schemas.context_schema import ContextCreate, ContextResponse
from repository.context_repository import ContextRepository
from repository.document_repository import DocumentRepository
from services.document_service import DocumentService
from repository.document_chunk_repository import DocumentChunkRepository
from typing import List
from schemas.base_schema import BaseResponse
from schemas.document_schema import DocumentText
import os

MAX_DOCUMENT_PER_CONTEXT = int(os.getenv("MAX_DOCUMENT_PER_CONTEXT", 5))

class ContextService:
    @staticmethod
    def create_context(db: Session, context_request: ContextCreate, user_id):
        existing_context = ContextRepository.get_by_owner_and_name(db, context_request.name, user_id)
        if existing_context:
            raise HTTPException(status_code=400, detail="Context with this name already exists")

        context =  ContextRepository.create(db, Context(name=context_request.name, owner_id=user_id, description=context_request.description))
        return ContextResponse.model_validate(context)
    
    @staticmethod
    def get_context_list(db: Session, name:str, user_id):
        return ContextRepository.get_by_owner(db, user_id, name)
    
    @staticmethod
    def get_detail(db: Session, context_id: str, owner_id):
        context = ContextRepository.get_by_id_and_owner(db, context_id, owner_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        documents = DocumentRepository.get_by_context_id(db, context.id)

        return ContextResponse(id=context.id, created_at=context.created_at, description=context.description, files=documents, name=context.name, updated_at=context.updated_at)
    
    @staticmethod
    async def upload_context_file(db: Session, context_id:str, owner_id, files:List[UploadFile] = None):
        context = ContextRepository.get_by_id_and_owner(db, context_id, owner_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        if DocumentRepository.get_number_of_documents_by_context_id(db, context.id) > MAX_DOCUMENT_PER_CONTEXT:
            raise HTTPException(status_code=403, detail="You have exceed the number of documents per context, delete one or more to upload")
        
        documents = await DocumentService.insert_context_document(db, context_id, files)
        return documents
    
    @staticmethod
    async def upload_context_text(db: Session, context_id:str, owner_id, document_text: DocumentText):
        context = ContextRepository.get_by_id_and_owner(db, context_id, owner_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        if DocumentRepository.get_number_of_documents_by_context_id(db, context.id) > MAX_DOCUMENT_PER_CONTEXT:
            raise HTTPException(status_code=403, detail="You have exceed the number of documents per context, delete one or more to upload")
        
        documents = await DocumentService.insert_context_text(db, context_id, document_text)
        return documents
    
    def delete(db:Session, context_id, owner_id):
        context = ContextRepository.get_by_id_and_owner(db, context_id, owner_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        documents = DocumentRepository.get_by_context_id(db, context.id)
        doc_ids = []

        for doc in documents:
            doc_ids.append(doc.id)

        if len(doc_ids) > 0:
            DocumentChunkRepository.delete_by_document_ids(db, doc_ids)
            DocumentRepository.delete_by_ids(db, doc_ids)
        
        ContextRepository.delete_by_id(db, context.id)
        db.commit()
        return BaseResponse(message="deleted", status=200)
        
    


        

    
    