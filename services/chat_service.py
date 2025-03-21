import os
import json
import numpy as np
import openai
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models.document_chunk_model import DocumentChunk
from models.document_model import Document
from sqlalchemy import select
from schemas.chat_schema import ChatRequest, ChatResponse
from repository.chat_repository import ChatRepository
from repository.context_repository import ContextRepository
from repository.document_repository import DocumentRepository
from fastapi import HTTPException


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
client = openai.OpenAI()

class ChatService:
    @staticmethod
    def get_embedding(text):
        """Get embedding for text using OpenAI API"""
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding

    @staticmethod
    def cosine_similarity(a, b):
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    @staticmethod
    def retrieve_relevant_chunks(db: Session, context_id: str, query_embedding, top_k=5):
        """Retrieve most relevant chunks for a given context and query"""

        chunks = ChatRepository.get_document_chunk_by_context_id(db, context_id)
        
        if not chunks:
            return []
        
        # Calculate similarity scores
        chunk_scores = []
        for chunk in chunks:
            chunk_embedding = json.loads(chunk.embedding)
            similarity = ChatService.cosine_similarity(query_embedding, chunk_embedding)
            chunk_scores.append((chunk, similarity))
        
        # Sort by similarity and get top_k
        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        return chunk_scores[:top_k]

    @staticmethod
    def generate_response(query, context_chunks, history=None):
        """Generate response using OpenAI API with retrieved context"""
        if history is None:
            history = []
        
        # Prepare context from chunks
        context_text = "\n\n".join([chunk.content for chunk, _ in context_chunks])
        
        messages = [
            {"role": "system", "content": f"You are a helpful assistant. Use the following context to answer the user's question. If you don't know the answer based on the context, say so.\n\nContext: {context_text}"}
        ]
        
        # Add history
        for msg in history:
            messages.append(msg)
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Get sources
        sources = [f"{chunk.document.filename} (Chunk {chunk.chunk_index})" for chunk, _ in context_chunks]
        
        return {
            "response": response.choices[0].message.content,
            "sources": sources
        }
    @staticmethod
    def chat_with_context(db: Session, chat_request: ChatRequest, user_id):
        context = ContextRepository.get_by_id_and_owner(db, chat_request.context_id, user_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        documents = DocumentRepository.get_by_context_id(db, context_id=context.id)
        if not documents:
            raise HTTPException(status_code=404, detail="You need to upload a doucment first before starting to chat")
        
        query_embedding = ChatService.get_embedding(chat_request.message)

        relevant_chunks = ChatService.retrieve_relevant_chunks(
            db=db, 
            context_id=chat_request.context_id, 
            query_embedding=query_embedding
        )

        if not relevant_chunks:
            return ChatResponse(
                response="I don't have enough information to answer that question based on the available documents.",
                sources=[]
            )
        response_data = ChatService.generate_response(
            query=chat_request.message,
            context_chunks=relevant_chunks,
            history=chat_request.history
        )
    
        return ChatResponse(
            response=response_data["response"],
            sources=response_data["sources"]
        )

