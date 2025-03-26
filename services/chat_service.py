import os
import json
import time
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
from utils.vector import cosine_distance


openai.api_key = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
DOCUCHAT_WEB_URL = os.getenv("DOCUCHAT_WEB_URL")
client = openai.OpenAI()


class ChatService:
    @staticmethod
    def get_embedding(text, retry_count=3):
        """
        Get embedding for text using OpenAI API with retry logic and error handling
        
        Args:
            text: The text to embed
            retry_count: Number of retries on failure
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or text.strip() == "":
            return [0.0] * 1536  # Return zero vector for empty text
            
        # Truncate text if it's too long (OpenAI has token limits)
        max_tokens = 8000  # Adjust based on model limits
        if len(text) > max_tokens * 4:  # Rough estimate: 4 chars per token
            text = text[:max_tokens * 4]
            
        for attempt in range(retry_count):
            try:
                response = client.embeddings.create(
                    input=text,
                    model=EMBEDDING_MODEL
                )
                return response.data[0].embedding
            except Exception as e:
                if attempt == retry_count - 1:  # Last attempt
                    print(f"Failed to get embedding after {retry_count} attempts: {str(e)}")
                    # Return a zero vector as fallback
                    return [0.0] * 1536  # Adjust dimension based on your model
                else:
                    # Exponential backoff
                    time.sleep(2 ** attempt)

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
            You are a knowledgeable assistant that provides accurate information based exclusively on the provided context and conversation history.

            CONTEXT INFORMATION:
            {context_text}

            INSTRUCTIONS:
            1. Answer questions ONLY using information from the provided context and previous conversation history.
            2. If the answer cannot be fully determined from the context or history, state: "Based on the available information, I cannot provide a complete answer to that question."
            3. Do not use prior knowledge or make assumptions beyond what is explicitly stated in the context.
            4. When citing information, refer to the specific document number (e.g., "According to Document 2...").
            5. If the user asks for clarification about a previous answer, refer to both the context and the conversation history.
            6. Provide concise, well-structured answers that directly address the user's query.
            7. If the user's question is ambiguous, ask for clarification rather than making assumptions.
            8. If the context contains conflicting information, acknowledge the discrepancy and present both viewpoints.

            Remember: Your goal is to be helpful while remaining strictly faithful to the provided information.
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
        if not chat_history:
            return f"User: {new_query}"
            
        relevant_history = []
        
        # Handle case where history might not be perfectly paired
        # Take the most recent messages up to 2*history_limit (to account for both user and assistant messages)
        recent_messages = chat_history[-2*history_limit:] if len(chat_history) > 2*history_limit else chat_history
        
        for message in recent_messages:
            # Validate message format and skip if invalid
            if not isinstance(message, dict) or "role" not in message or "content" not in message:
                continue
                
            role = message.get("role", "").lower()
            content = message.get("content", "").strip()
            
            # Skip empty messages
            if not content:
                continue
                
            # Only include user and assistant roles
            if role in ["user", "assistant"]:
                relevant_history.append(f"{role.capitalize()}: {content}")
        
        # Combine history and new query
        history_text = "\n".join(relevant_history)
        
        # Add the new query with a separator for better context distinction
        if history_text:
            return f"{history_text}\nUser: {new_query}"
        else:
            return f"User: {new_query}"
