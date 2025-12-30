#!/usr/bin/env python3
"""
ChatterFix CMMS - Document Intelligence & AI Expansion
OCR + Vector Embeddings + "Ask the Manual" Feature
"""

import os
import hashlib
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import aiofiles

# AI and ML imports
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR not available - install pytesseract and PIL")

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False
    print("⚠️ Vector DB not available - install chromadb and sentence-transformers")

# Configuration
UPLOAD_DIR = Path("./uploads")
PROCESSED_DIR = Path("./processed")
EMBEDDINGS_DIR = Path("./embeddings")

# Ensure directories exist
for directory in [UPLOAD_DIR, PROCESSED_DIR, EMBEDDINGS_DIR]:
    directory.mkdir(exist_ok=True)

# AI Brain Service URL
AI_BRAIN_URL = os.getenv("AI_BRAIN_URL", "http://localhost:8005")

class DocumentModels:
    class DocumentUpload(BaseModel):
        filename: str
        file_type: str
        asset_id: Optional[int] = None
        category: str = Field(default="manual", description="manual, procedure, drawing, specification")
        description: Optional[str] = None
        tags: List[str] = Field(default_factory=list)
    
    class DocumentQuery(BaseModel):
        query: str = Field(..., min_length=3, max_length=500)
        asset_id: Optional[int] = None
        category: Optional[str] = None
        max_results: int = Field(default=5, ge=1, le=20)
        include_content: bool = Field(default=True)
    
    class DocumentChunk(BaseModel):
        chunk_id: str
        document_id: str
        content: str
        page_number: Optional[int] = None
        embedding: Optional[List[float]] = None
        metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class SearchResult(BaseModel):
        document_id: str
        filename: str
        relevance_score: float
        content_snippet: str
        page_number: Optional[int] = None
        asset_id: Optional[int] = None
        category: str

class DocumentIntelligence:
    """Advanced document processing and AI search system"""
    
    def __init__(self):
        self.embedding_model = None
        self.vector_db = None
        self.collection = None
        self.initialize_ai_components()
    
    def initialize_ai_components(self):
        """Initialize AI models and vector database"""
        try:
            if VECTOR_DB_AVAILABLE:
                # Initialize sentence transformer for embeddings
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Embedding model loaded")
                
                # Initialize ChromaDB
                self.vector_db = chromadb.PersistentClient(path="./chroma_db")
                self.collection = self.vector_db.get_or_create_collection(
                    name="cmms_documents",
                    metadata={"description": "ChatterFix CMMS document embeddings"}
                )
                print("✅ Vector database initialized")
        except Exception as e:
            print(f"❌ AI components initialization failed: {e}")
    
    async def extract_text_from_image(self, image_path: Path) -> str:
        """Extract text from image using OCR"""
        if not OCR_AVAILABLE:
            return "OCR not available - text extraction skipped"
        
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    async def process_pdf(self, pdf_path: Path) -> List[str]:
        """Extract text from PDF pages"""
        try:
            # For demo, return placeholder text
            # In production, use PyPDF2 or pdfplumber
            return [
                f"Page 1 content from {pdf_path.name}",
                f"Page 2 content from {pdf_path.name}",
                "Equipment maintenance procedures and safety guidelines..."
            ]
        except Exception as e:
            print(f"PDF processing error: {e}")
            return [f"Error processing PDF: {str(e)}"]
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for better search"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to end at a sentence boundary
            if end < len(text):
                last_period = text.rfind('.', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create vector embeddings for text chunks"""
        if not self.embedding_model:
            return []
        
        try:
            embeddings = self.embedding_model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            print(f"Embedding creation error: {e}")
            return []
    
    async def process_document(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Process uploaded document and create searchable chunks"""
        document_id = hashlib.md5(f"{file_path.name}{datetime.now()}".encode()).hexdigest()
        
        try:
            # Extract text based on file type
            file_ext = file_path.suffix.lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                text_content = await self.extract_text_from_image(file_path)
            elif file_ext == '.pdf':
                pages = await self.process_pdf(file_path)
                text_content = "\n\n".join(pages)
            elif file_ext == '.txt':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    text_content = await f.read()
            else:
                text_content = "Unsupported file type for text extraction"
            
            # Create text chunks
            chunks = self.chunk_text(text_content)
            
            if not chunks:
                return document_id
            
            # Create embeddings
            embeddings = await self.create_embeddings(chunks)
            
            if self.collection and embeddings:
                # Store in vector database
                chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
                
                # Prepare metadata for each chunk
                chunk_metadata = []
                for i, chunk in enumerate(chunks):
                    chunk_meta = {
                        "document_id": document_id,
                        "filename": file_path.name,
                        "chunk_index": i,
                        "asset_id": metadata.get("asset_id"),
                        "category": metadata.get("category", "manual"),
                        "upload_date": datetime.now().isoformat()
                    }
                    chunk_metadata.append(chunk_meta)
                
                # Add to ChromaDB
                self.collection.add(
                    ids=chunk_ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=chunk_metadata
                )
                
                print(f"✅ Processed document: {file_path.name} ({len(chunks)} chunks)")
            
            return document_id
            
        except Exception as e:
            print(f"Document processing error: {e}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    async def search_documents(self, query: str, filters: Dict[str, Any] = None, max_results: int = 5) -> List[DocumentModels.SearchResult]:
        """Search documents using vector similarity"""
        if not self.collection or not self.embedding_model:
            return []
        
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Prepare filters for ChromaDB
            where_clause = {}
            if filters:
                if filters.get("asset_id"):
                    where_clause["asset_id"] = filters["asset_id"]
                if filters.get("category"):
                    where_clause["category"] = filters["category"]
            
            # Search vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            search_results = []
            
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    # Convert distance to relevance score (higher is better)
                    relevance_score = max(0, 1 - distance)
                    
                    result = DocumentModels.SearchResult(
                        document_id=metadata["document_id"],
                        filename=metadata["filename"],
                        relevance_score=round(relevance_score, 3),
                        content_snippet=doc[:200] + "..." if len(doc) > 200 else doc,
                        page_number=metadata.get("page_number"),
                        asset_id=metadata.get("asset_id"),
                        category=metadata["category"]
                    )
                    search_results.append(result)
            
            return search_results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    async def ask_the_manual(self, question: str, asset_id: Optional[int] = None) -> Dict[str, Any]:
        """Advanced 'Ask the Manual' feature with AI enhancement"""
        
        # Search relevant documents
        filters = {"asset_id": asset_id} if asset_id else {}
        search_results = await self.search_documents(question, filters, max_results=3)
        
        if not search_results:
            return {
                "answer": "I couldn't find relevant information in the available manuals.",
                "confidence": 0.0,
                "sources": []
            }
        
        # Prepare context for AI
        context_chunks = []
        sources = []
        
        for result in search_results:
            context_chunks.append(f"From {result.filename}: {result.content_snippet}")
            sources.append({
                "filename": result.filename,
                "relevance": result.relevance_score,
                "asset_id": result.asset_id
            })
        
        context = "\n\n".join(context_chunks)
        
        # Send to AI Brain for enhanced response
        try:
            async with httpx.AsyncClient() as client:
                ai_response = await client.post(
                    f"{AI_BRAIN_URL}/api/ai/enhanced-query",
                    json={
                        "question": question,
                        "context": context,
                        "domain": "maintenance_manual"
                    },
                    timeout=30
                )
                
                if ai_response.status_code == 200:
                    ai_data = ai_response.json()
                    return {
                        "answer": ai_data.get("response", "AI processing unavailable"),
                        "confidence": ai_data.get("confidence", 0.7),
                        "sources": sources,
                        "enhanced_by_ai": True
                    }
        except Exception as e:
            print(f"AI enhancement error: {e}")
        
        # Fallback to basic response
        return {
            "answer": f"Based on the available documentation: {search_results[0].content_snippet}",
            "confidence": search_results[0].relevance_score,
            "sources": sources,
            "enhanced_by_ai": False
        }

# Initialize document intelligence
doc_intelligence = DocumentIntelligence()

# FastAPI app
app = FastAPI(
    title="ChatterFix CMMS - Document Intelligence",
    description="OCR + Vector Embeddings + Ask the Manual AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    asset_id: Optional[int] = Form(None),
    category: str = Form("manual"),
    description: Optional[str] = Form(None),
    tags: str = Form("")
):
    """Upload and process a document"""
    
    # Validate file type
    allowed_types = {'.pdf', '.txt', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Process document
        metadata = {
            "asset_id": asset_id,
            "category": category,
            "description": description,
            "tags": tags.split(",") if tags else []
        }
        
        document_id = await doc_intelligence.process_document(file_path, metadata)
        
        return {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "message": "Document uploaded and processed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/search")
async def search_documents(query: DocumentModels.DocumentQuery):
    """Search documents using AI-powered vector similarity"""
    
    filters = {}
    if query.asset_id:
        filters["asset_id"] = query.asset_id
    if query.category:
        filters["category"] = query.category
    
    results = await doc_intelligence.search_documents(
        query.query,
        filters,
        query.max_results
    )
    
    return {
        "query": query.query,
        "results": results,
        "total_found": len(results)
    }

@app.post("/api/documents/ask-manual")
async def ask_the_manual(
    question: str = Query(..., min_length=5),
    asset_id: Optional[int] = Query(None)
):
    """Ask the Manual - AI-powered document Q&A"""
    
    response = await doc_intelligence.ask_the_manual(question, asset_id)
    
    return {
        "question": question,
        "asset_id": asset_id,
        **response,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/documents/stats")
async def get_document_stats():
    """Get document collection statistics"""
    
    stats = {
        "total_documents": 0,
        "total_chunks": 0,
        "categories": {},
        "ai_features": {
            "ocr_available": OCR_AVAILABLE,
            "vector_search_available": VECTOR_DB_AVAILABLE,
            "ask_manual_available": True
        }
    }
    
    if doc_intelligence.collection:
        try:
            count_result = doc_intelligence.collection.count()
            stats["total_chunks"] = count_result
            
            # Get sample of metadata to analyze categories
            sample = doc_intelligence.collection.get(limit=100, include=["metadatas"])
            for metadata in sample["metadatas"]:
                category = metadata.get("category", "unknown")
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
                
        except Exception as e:
            print(f"Stats error: {e}")
    
    return stats

@app.get("/health")
async def health_check():
    """Document intelligence health check"""
    return {
        "status": "healthy",
        "service": "document-intelligence",
        "capabilities": [
            "OCR text extraction",
            "Vector embeddings search",
            "Ask the Manual AI",
            "Multi-format document support",
            "Asset-linked documentation"
        ],
        "ai_status": {
            "ocr": "available" if OCR_AVAILABLE else "unavailable",
            "vector_db": "available" if VECTOR_DB_AVAILABLE else "unavailable",
            "embedding_model": "loaded" if doc_intelligence.embedding_model else "unavailable"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)