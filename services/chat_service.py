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

        chunks = ChatRepository.get_relevant_chunk_by_context_and_query(db, context_id, top_k)
        
        # Calculate similarity scores
        # chunk_scores = []
        # for chunk in chunks:
        #     chunk_embedding = json.loads(chunk.embedding)
        #     similarity = ChatService.cosine_similarity(query_embedding, chunk_embedding)
        #     chunk_scores.append((chunk, similarity))
        
        # # Sort by similarity and get top_k
        # chunk_scores.sort(key=lambda x: x[1], reverse=True)
        return chunks

    @staticmethod
    def generate_response(query, context_chunks, history=None):
        """Generate response using OpenAI API with retrieved context"""
        if history is None:
            history = []
        
        # Prepare context from chunks
        context_text = "\n\n".join([f"Document {i+1}: {doc.content}" for i, doc in enumerate(context_chunks)])
        
        messages = [
        {"role": "system", 
         "content": f"""
            You are a helpful assistant that answers questions **ONLY** using the given context. 
            If the answer is not in the context, reply: "I don't know based on the provided context."

            Examples:
            User: What is the capital of France?  
            Context: (contains no relevant info)  
            Assistant: I don't know based on the provided context.

            User: What is the best sorting algorithm?  
            Context: (contains details about Python syntax but nothing on sorting)  
            Assistant: I don't know based on the provided context.

            Context: {context_text}
        """}        
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

        sources = []
        for chunk in context_chunks:
            source = f"{chunk.filename} - page {chunk.source_page}"
            if source not in sources:
                sources.append(source)
        
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

        doc_ids = []

        for doc in documents:
            doc_ids.append(doc.id)

        relevant_chunks = ChatRepository.get_relevant_chunk_by_context_and_query(db, doc_ids, query_embedding)

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

