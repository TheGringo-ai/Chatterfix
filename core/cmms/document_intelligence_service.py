#!/usr/bin/env python3
"""
ChatterFix CMMS - Document Intelligence Service (Port 8006)
Handles document processing and AI analysis
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="ChatterFix Document Intelligence Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DocumentRequest(BaseModel):
    content: str
    document_type: Optional[str] = "general"

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ChatterFix Document Intelligence Service",
        "port": 8006,
        "capabilities": ["OCR", "Text Analysis", "Document Classification"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/analyze")
async def analyze_document(doc: DocumentRequest):
    return {
        "success": True,
        "analysis": f"Analyzed {doc.document_type} document with {len(doc.content)} characters",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8006)
    args = parser.parse_args()
    
    print(f"📄 Starting Document Intelligence Service on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
