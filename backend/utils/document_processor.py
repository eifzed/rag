import os
import json
import PyPDF2
from io import BytesIO
import openai
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
embeddings = OpenAIEmbeddings()
client = openai.OpenAI()

class DocumentProcessor:
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
    def get_embedding(text):
        """Get embedding for text using OpenAI API"""
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        return json.dumps(response.data[0].embedding)

    @staticmethod
    def get_vectorspace(textChunks):
        return Chroma.from_texts(texts=textChunks, embedding=embeddings, persist_directory=EMBEDDING_DB)