import os
import json
import PyPDF2
from io import BytesIO, StringIO
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from fastapi import UploadFile
import fitz 
import pandas as pd
import filetype


openai.api_key = os.getenv("OPENAI_API_KEY")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
embeddings = OpenAIEmbeddings()
client = openai.OpenAI()

class DocumentProcessor:

    @staticmethod
    def extract_text_from_file(contents:bytes, mime_type: str):
        """
        Reads text from an uploaded file (FastAPI UploadFile), detecting type via MIME type.

        Args:
            contents (bytes): The uploaded file content.
            mime_type: file type
            
        Returns:
            str: Extracted text from the file.
        """
        
        text = {}

        if mime_type == "application/pdf":
            with fitz.open(stream=BytesIO(contents), filetype="pdf") as pdf:
                for i, page in enumerate(pdf):
                    text[i+1] = page.get_text("text") + "\n"  # Extract text from each page
        elif mime_type in ["text/markdown", "text/plain", "text/url-scrape"]:
            text[1] = contents.decode('utf-8')  # Read markdown or plain text

        else:
            raise ValueError(f"Unsupported MIME type: {mime_type}")

        return text

    @staticmethod
    def extract_text_from_pdf(file_data):
        """Extracts text from a PDF file (given bytes)."""
        text = []
        reader = PyPDF2.PdfReader(BytesIO(file_data))  # Read from memory
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    
    @staticmethod
    def extract_text_from_md(file_data):
        """Extracts text from a MD file (given bytes)."""
        return file_data.decode("utf-8")

    @staticmethod
    def chunk_text(text):
        """Split text into chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    @staticmethod
    def chunk_text_with_page_tracking(pages_dict):
        """
        Split text into chunks while tracking the source page
        
        Args:
            pages_dict: Dictionary mapping page numbers to page content {page_num: text}
        
        Returns:
            List of tuples: [(chunk_text, page_num), ...]
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        
        chunks_with_source = []
        
        for page_num, page_text in pages_dict.items():
            page_chunks = text_splitter.split_text(page_text)
            
            # Associate each chunk with its source page
            for chunk in page_chunks:
                chunks_with_source.append((page_num, chunk))
        
        return chunks_with_source

    @staticmethod
    def get_embedding(text):
        """Get embedding for text using OpenAI API"""
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding

    @staticmethod
    def get_vectorspace(textChunks):
        return Chroma.from_texts(texts=textChunks, embedding=embeddings, persist_directory=EMBEDDING_DB)