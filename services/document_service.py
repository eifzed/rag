from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, Depends
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
from schemas.document_schema import DocumentText
from models.enums import UploadStatus
import os
from messaging.publisher import send_to_nsq_api, publish_to_nsq
from utils.database import get_db, SessionLocal
from concurrent.futures import ThreadPoolExecutor




ENABLE_BACKGROUND_EMBEDDING = os.getenv("ENABLE_BACKGROUND_EMBEDDING")

class DocumentService:
    @staticmethod
    def download_document(db:Session, document_id, context_id, owner_id):
        context = ContextRepository.get_by_id_and_owner(db, context_id, owner_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        document = DocumentRepository.get_by_id_and_context_id(db, document_id, context_id)

        if document.content_type == "text/url-scrape":
            document.content_type = "text/plain"
            document.filename = document.filename+".txt"

        response = StreamingResponse(io.BytesIO(document.file_data), media_type=document.content_type, headers={"Content-Disposition": f'attachment; filename="{document.filename}"'})
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response
    
    @staticmethod
    def delete_document(db:Session, document_id, context_id, owner_id):
        context = ContextRepository.get_by_id_and_owner(db, context_id, owner_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        DocumentChunkRepository.delete_by_document_ids(db, [document_id])
        DocumentRepository.delete_by_ids(db, [document_id])
        db.commit()
        return BaseResponse(status=200, message="deleted")

    @staticmethod
    async def insert_context_document(db:Session, context_id:str, file:UploadFile)->Document:
        try:
            documents = []
            file_content = await file.read()

            document = Document(
                context_id=context_id,
                filename=file.filename,
                content_type=file.content_type,
                file_data=file_content,
                upload_status = UploadStatus.IN_QUEUE.value
            )
            DocumentRepository.insert(db, document)
            db.commit()
            db.refresh(document)
            documents.append(document)
            
            if ENABLE_BACKGROUND_EMBEDDING == "1":
                await publish_to_nsq("embed_document", {"document_id": str(document.id)})
                return document
            
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
            
            return documents
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def insert_context_text(db:Session, context_id:str, document_text: DocumentText)->Document:
        try:
                
            # Save document to database
            document = Document(
                id= uuidv7(),
                context_id=context_id,
                filename=document_text.filename,
                content_type="text/url-scrape",
                file_data=document_text.content.encode("utf-8"),
                upload_status = UploadStatus.IN_QUEUE.value
            )
            DocumentRepository.insert(db, document)
            db.commit()
            db.refresh(document)
            
            if ENABLE_BACKGROUND_EMBEDDING == "1":
                await publish_to_nsq("embed_document", {"document_id": str(document.id)})
                return document
            
            
            # Process document
            page_map = {1: document_text.content}
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
                    filename=document_text.filename
                )
                DocumentChunkRepository.insert(db, chunk)
            
            db.commit()
            db.refresh(document)
                
            return document
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    def chunk_and_embed_document(db: Session, document: Document):
        page_map = DocumentProcessor.extract_text_from_file(document.file_data, document.content_type)
        chunks = DocumentProcessor.chunk_text_with_page_tracking(page_map)

        def process_chunk(i, chunk_text):
            """Function to process and insert a chunk (runs in a thread)"""
            embedding = DocumentProcessor.get_embedding(chunk_text[1])  # Possibly slow
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk_text,
                embedding=embedding,
                source_page=chunk_text[0],
                filename=document.filename,
            )
            return chunk

        with ThreadPoolExecutor(max_workers=4) as executor:
            chunk_objects = list(executor.map(lambda args: process_chunk(*args), enumerate(chunks)))

        DocumentChunkRepository.insert_bulk(db, chunk_objects)

        
    @staticmethod
    def process_background_document_embedding(documentdata):
        db = None
        document_id = documentdata.get("document_id")
        if not document_id:
            print("Error: No document_id provided in the message")
            return
            
        try:
            db = next(get_db())
            document = DocumentRepository.get_unfinished_by_id(db, document_id)

            if not document:
                print(f"Document {document_id} not found or already processed")
                return

            document.upload_status = UploadStatus.PROCESSING.value
            db.commit()
            db.refresh(document)
                        
            # Process the document
            DocumentService.chunk_and_embed_document(db, document)
            
            # Update status to success
            document.upload_status = UploadStatus.SUCCESS.value
            db.commit()            
        except Exception as e:
            document.upload_status = UploadStatus.FAILED.value
            db.commit()
            raise

        db.commit()



        
        
        
