from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List
from models.models import Context, Document, DocumentChunk
from utils.document_processor import DocumentProcessor


async def insert_context_document(context_id:str, files:List[UploadFile], db:Session)->List[Document]:
    try:
            documents = []
            for file in files:
                file_content = await file.read()
                
                # Save document to database
                document = Document(
                    context_id=context_id,
                    filename=file.filename,
                    content_type=file.content_type,
                    file_data=file_content
                )
                db.add(document)
                db.commit()
                db.refresh(document)

                documents.append(document)
                
                # Process document
                text = DocumentProcessor.extract_text_from_file(file_content, file.content_type)
                chunks = DocumentProcessor.chunk_text(text)
                
                # vectorspace = DocumentProcessor.get_vectorspace(chunks)
                # Save chunks with embeddings
                for i, chunk_text in enumerate(chunks):
                    embedding = DocumentProcessor.get_embedding(chunk_text)
                    chunk = DocumentChunk(
                        document_id=document.id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding
                    )
                    db.add(chunk)
                
                db.commit()
            return documents
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    