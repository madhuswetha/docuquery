# DocuQuery AI - RAG System for Document Q&A
# Day 1: Basic FastAPI setup with health check

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
import shutil
import PyPDF2
from typing import Dict, Any, List

# Create FastAPI app instance
# This is your main application object
app = FastAPI(
    title="DocuQuery",
    description="A RAG-powered document Q&A system",
    version="1.0.0"
)

# Add CORS middleware (allows frontend to connect later)
# CORS = Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def extract_text_from_pdf(pdf_path: Path)-> Dict[str, Any]:
    """
    Extract text from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing:
        - full_text: Complete extracted text
        - num_pages: Number of pages in PDF
        - num_words: Approximate word count
        - num_chars: Character count
    """

    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            num_pages = len(pdf_reader.pages)

            full_text = ""

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]

                page_text = page.extract_text()

                full_text+= f"\n----Page {page_num+1}----\n"
                full_text+= page_text

            num_chars = len(full_text)
            num_words = len(full_text.split())

            return {
                "full_text": full_text,
                "num_pages": num_pages,
                "num_words": num_words,
                "num_chars": num_chars
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting text from PDF: {str(e)}"
        )

def chunk_text(text: str, chunk_size: int = 500, overlap: int=50) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks
    
    Args:
        text: The full text to chunk
        chunk_size: Maximum characters per chunk (default: 500)
        overlap: Number of characters to overlap between chunks (default: 50)
        
    Returns:
        List of dictionaries, each containing:
        - chunk_id: Unique identifier for the chunk
        - text: The chunk text
        - start_char: Starting character position in original text
        - end_char: Ending character position in original text
        - num_chars: Number of characters in chunk
    """
    chunks =[]
    start = 0
    chunk_id=0

    while start< len(text):
        end = start+chunk_size
        chunk_text = text[start:end]
        chunk = {
            "chunk_id": chunk_id,
            "text": chunk_text,
            "start_char": start,
            "end_char": end if end<len(text) else len(text),
            "num_chars": len(chunk_text)
        }
        chunks.append(chunk)
        start = end-overlap
        chunk_id+=1

    return chunks
    


@app.get("/")
def read_root():
    """
    Root endpoint - returns welcome message
    This is like the homepage of your API
    """
    return {
        "message": "Welcome to DocuQuery AI!",
        "status": "API is running",
        "endpoints": {
            "docs": "/docs",  # Auto-generated API documentation
            "health": "/health",
            "upload": "/upload",
            "extract": "/extract/{filename}"
        }
    }

# Health check endpoint
# Used to verify the API is working correctly
@app.get("/health")
def health_check():
    """
    Health check endpoint - confirms API is operational
    Returns status and basic info
    """
    return {
        "status": "healthy",
        "service": "DocuQuery",
        "version": "1.0.0"
    }

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and extract its text
    
    This endpoint:
    1. Receives a PDF file from user
    2. Validates it's a PDF
    3. Saves it to the uploads/ folder
    4. Extracts text from the PDF
    5. Returns file info + extracted text preview
    """

    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed. Please upload a .pdf file."
        )
    
    if file.size == 0:
        raise HTTPException(
            status_code = 400,
            detail="Empty file uploaded. Please upload a valid PDF."
        )
    
    try:
        safe_filename = file.filename.replace(" ", "_")
        file_path = UPLOAD_DIR/safe_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extraction_result = extract_text_from_pdf(file_path)

        file_size_kb = os.path.getsize(file_path)/1024

        text_preview = extraction_result["full_text"][:500]
        if len(extraction_result["full_text"])>500:
            text_preview+="..."

        return {
            "message": "PDF uploaded and processed successfully!",
            "filename": safe_filename,
            "size_kb": round(file_size_kb, 2),
            "saved_path": str(file_path),
            "extraction": {
                "num_pages": extraction_result["num_pages"],
                "num_words": extraction_result["num_words"],
                "num_chars": extraction_result["num_chars"],
                "text_preview": text_preview
            },
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail=f"Error uploading file: {str(e)}"
        )
    
    finally:
        file.file.close()

@app.get("/extract/{filename}")
def extract_text(filename: str):
    """
    Extract text from a previously uploaded PDF
    
    Args:
        filename: Name of the PDF file in uploads/ folder
        
    Returns:
        Full extracted text and statistics
    """

    # Build file path
    file_path = UPLOAD_DIR / filename
    
    # Check if file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found. Please upload it first."
        )
    
    # Check if it's a PDF
    if not filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF."
        )
    
    # Extract text
    extraction_result = extract_text_from_pdf(file_path)
    
    return {
        "filename": filename,
        "extraction": extraction_result,
        "status": "success"
    }


@app.get("/chunk/{filename}")
def chunk_pdf(filename: str, chunk_size: int =500, overlap: int =50):
    """
    Extract text from a PDF and split it into chunks
    
    Args:
        filename: Name of the PDF file in uploads/ folder
        chunk_size: Maximum characters per chunk (default: 500)
        overlap: Characters to overlap between chunks (default: 50)
        
    Returns:
        List of text chunks with metadata
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found. Please upload it first."
        )
    
    # Check if it's a PDF
    if not filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF."
        )
    
    extraction_result = extract_text_from_pdf(file_path)
    full_text = extraction_result["full_text"]

    chunks = chunk_text(full_text, chunk_size=chunk_size, overlap=overlap)
    return {
        "filename": filename,
        "total_chunks": len(chunks),
        "chunk_size": chunk_size,
        "overlap": overlap,
        "original_length": extraction_result["num_chars"],
        "chunks": chunks,
        "status": "success"
    }
# To run this:
# 1. Make sure venv is activated: venv\Scripts\activate
# 2. Run: uvicorn main:app --reload
# 3. Open browser: http://localhost:8000
# 4. See auto docs: http://localhost:8000/docs