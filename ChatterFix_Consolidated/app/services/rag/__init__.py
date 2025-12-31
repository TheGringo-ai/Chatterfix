"""
RAG (Retrieval-Augmented Generation) Service
Provides document processing, embedding generation, and semantic search
for the ChatterFix training module system.
"""

from .rag_service import RAGService, rag_service
from .document_processor import DocumentProcessor
from .vector_store import VectorStore

__all__ = ["RAGService", "rag_service", "DocumentProcessor", "VectorStore"]
