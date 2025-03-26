import os
import json
import numpy as np
import openai
from sqlalchemy.orm import Session
from models.document_chunk_model import DocumentChunk
from models.document_model import Document
from sqlalchemy import select
from schemas.chat_schema import ChatRequest, ChatResponse
from repository.chat_repository import ChatRepository
from repository.context_repository import ContextRepository
from repository.document_repository import DocumentRepository
from fastapi import HTTPException


openai.api_key = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
DOCUCHAT_WEB_URL = os.getenv("DOCUCHAT_WEB_URL")
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
    def retrieve_relevant_chunks(db: Session, context_id: str, query_embedding, top_k=5):
        """Retrieve most relevant chunks for a given context and query"""
        return ChatRepository.get_relevant_chunk_by_context_and_query(db, context_id, top_k)

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
            You are a helpful assistant that answers questions **ONLY** using the given context and message history. 
            If the answer is not in the context or message history, reply: "I don't know based on the provided context."

            Examples:
            User: What is the capital of France?  
            Context: (contains no relevant info)  
            Assistant: I don't know based on the provided context.

            User: What is the best sorting algorithm?  
            Context: (contains details about Python syntax but nothing on sorting)  
            Assistant: I don't know based on the provided context.

            User: How many employment types are there?  
            Context: (contains relevant info)  
            Assistant: There are two types of employment: full-time and contract
            User: can you expand on the first one?
            Context: (contains relevant info about full-time eployement)
            Assistant: (explain full-time employment based on context)

            Context: {context_text}
        """}        
        ]
        
        # Format chat history
        formatted_query = ChatService.format_chat_for_vector_search(history, query)
        
        # Add formatted history as separate messages instead of combining with query
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current query as the final user message
        messages.append({"role": "user", "content": query})
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        sources = list(set(f"{chunk.filename} - page {chunk.source_page}" for chunk in context_chunks))
        
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
            return ChatResponse(
                response=f"You have not added any documents to the context. Go to [this page]({DOCUCHAT_WEB_URL}/contexts/{context.id}) to add"
            )
        
        # Create a more comprehensive query by combining history and current message
        query = ChatService.format_chat_for_vector_search(chat_request.history, chat_request.message)
        query_embedding = ChatService.get_embedding(query)
        
        doc_ids = [doc.id for doc in documents]
        
        # Adjust top_k based on query complexity
        query_words = len(query.split())
        dynamic_top_k = min(max(3, query_words // 10), 8)  # Between 3-8 based on query length
        
        # Get relevant chunks with dynamic top_k
        relevant_chunks = ChatRepository.get_relevant_chunk_by_context_and_query(
            db, 
            doc_ids, 
            query_embedding,
            top_k=dynamic_top_k
        )
        
        # If we don't have enough relevant chunks, try to get more context
        if len(relevant_chunks) < 2 and not chat_request.history:
            # Try with a more lenient threshold
            relevant_chunks = ChatRepository.get_relevant_chunk_by_context_and_query(
                db, doc_ids, query_embedding, top_k=dynamic_top_k, similarity_threshold=0.5
            )
        
        if not relevant_chunks and not chat_request.history:
            return ChatResponse(
                response="I don't have enough information to answer that question based on the available documents.",
                sources=[]
            )
        
        # Sort chunks by relevance for better context organization
        relevant_chunks.sort(key=lambda x: DocumentChunk.embedding.cosine_distance(x.embedding, query_embedding))
        
        response_data = ChatService.generate_response(
            query=chat_request.message,
            context_chunks=relevant_chunks,
            history=chat_request.history
        )
    
        return ChatResponse(
            response=response_data["response"],
            sources=response_data["sources"]
        )
    
    @staticmethod
    def format_chat_for_vector_search(chat_history: list, new_query: str, history_limit: int = 2) -> str:
        """
        Formats chat history and the new user query into a search-friendly string for vector retrieval.
        
        Parameters:
            chat_history (list): List of previous chat messages in format [{"role": "user"/"assistant", "content": "..."}]
            new_query (str): The latest user query.
            history_limit (int): Number of past user-assistant exchanges to include.
        
        Returns:
            str: A formatted string combining relevant chat history and the new query.
        """
        relevant_history = []
        
        # Extract last `history_limit` user-assistant exchanges
        exchanges = [chat_history[i:i+2] for i in range(0, len(chat_history)-1, 2)]
        recent_exchanges = exchanges[-history_limit:]
        
        for exchange in recent_exchanges:
            for message in exchange:
                role = message["role"]
                content = message["content"]
                relevant_history.append(f"{role.capitalize()}: {content}")
        
        # Combine history and new query
        history_text = "\n".join(relevant_history)
        return f"{history_text}\nUser: {new_query}" if history_text else f"User: {new_query}"
