from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from typing import List
from models.document_model import Document
from models.document_chunk_model import DocumentChunk
from utils.document_processor import DocumentProcessor
from repository.document_repository import DocumentRepository
from repository.context_repository import ContextRepository
from repository.document_chunk_repository import DocumentChunkRepository
from fastapi.responses import StreamingResponse
import io
from schemas.base_schema import BaseResponse
from utils.uuid import uuidv7





class DocumentService:
    @staticmethod
    def download_document(db:Session, document_id, context_id, owner_id):
        context = ContextRepository.get_by_id_and_owner(db, context_id, owner_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        document = DocumentRepository.get_by_id_and_context_id(db, document_id, context_id)

        response = StreamingResponse(io.BytesIO(document.file_data), media_type=document.content_type, headers={"Content-Disposition": f'attachment; filename="{document.filename}"'})
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        return document
    
    @staticmethod
    def delete_document(db:Session, document_id, context_id, owner_id):
        context = ContextRepository.get_by_id_and_owner(db, context_id, owner_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        DocumentRepository.delete_by_ids(db, [document_id])
        DocumentChunkRepository.delete_by_document_ids(db, [document_id])
        db.commit()
        return BaseResponse(status=200, message="deleted")

    @staticmethod
    async def insert_context_document(db:Session, context_id:str, files:List[UploadFile])->List[Document]:
        try:
            documents = []
            for file in files:
                file_content = await file.read()
                
                # Save document to database
                document = Document(
                    id= uuidv7(),
                    context_id=context_id,
                    filename=file.filename,
                    content_type=file.content_type,
                    file_data=file_content
                )
                DocumentRepository.insert(db, document)
                
                
                # Process document
                page_map = DocumentProcessor.extract_text_from_file(file_content, file.content_type)
                chunks = DocumentProcessor.chunk_text_with_page_tracking(page_map)
                
                # Save chunks with embeddings
                for i, chunk_text in enumerate(chunks):
                    embedding = DocumentProcessor.get_embedding(chunk_text[1])
                    chunk = DocumentChunk(
                        document_id=document.id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding,
                        source_page = chunk_text[0],
                        filename=file.filename
                    )
                    DocumentChunkRepository.insert(db, chunk)
                
                db.commit()
                db.refresh(document)
                documents.append(document)
            return documents
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))