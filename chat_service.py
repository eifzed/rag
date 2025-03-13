import os
import json
import numpy as np
import openai
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models import Context, DocumentChunk

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

class ChatService:
    @staticmethod
    def get_embedding(text):
        """Get embedding for text using OpenAI API"""
        response = openai.Embedding.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        return response["data"][0]["embedding"]

    @staticmethod
    def cosine_similarity(a, b):
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    @staticmethod
    def retrieve_relevant_chunks(db: Session, context_id: str, query_embedding, top_k=5):
        """Retrieve most relevant chunks for a given context and query"""
        chunks = db.query(DocumentChunk).join(
            DocumentChunk.document
        ).filter(
            Context.id == context_id
        ).all()
        
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
        
        # Prepare messages for the API
        messages = [
            {"role": "system", "content": f"You are a helpful assistant. Use the following context to answer the user's question. If you don't know the answer based on the context, say so.\n\nContext: {context_text}"}
        ]
        
        # Add history
        for msg in history:
            messages.append(msg)
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
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