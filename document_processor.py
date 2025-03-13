import os
import json
import PyPDF2
from io import BytesIO
import openai
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

class DocumentProcessor:
    @staticmethod
    def extract_text_from_pdf(file_data):
        """Extract text from PDF file"""
        pdf_file = BytesIO(file_data)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text

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
    def get_embedding(text):
        """Get embedding for text using OpenAI API"""
        response = openai.Embedding.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        return json.dumps(response["data"][0]["embedding"])