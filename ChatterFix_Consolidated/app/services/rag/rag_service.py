"""
RAG Service - Main Entry Point
Provides document-based AI training enhancement through Retrieval-Augmented Generation.
"""

import logging
import os
import uuid
from typing import Dict, List, Any, Optional

from .document_processor import DocumentProcessor
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False


class RAGService:
    """Main RAG service for document-based training enhancement."""

    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        if GENAI_AVAILABLE and os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    async def process_and_store_document(
        self, file_content: bytes, filename: str, organization_id: str,
        mime_type: Optional[str] = None, metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process and store a document."""
        try:
            document_id = str(uuid.uuid4())
            result = await self.document_processor.process_document(file_content, filename, mime_type)

            if not result["success"]:
                return result

            doc_metadata = result["metadata"]
            if metadata:
                doc_metadata.update(metadata)

            await self.vector_store.store_document(document_id, result["chunks"], doc_metadata, organization_id)

            return {
                "success": True,
                "document_id": document_id,
                "filename": filename,
                "chunk_count": result["chunk_count"],
                "metadata": doc_metadata,
            }
        except Exception as e:
            logger.error(f"Process failed: {e}")
            return {"success": False, "error": str(e)}

    async def search_documents(self, query: str, organization_id: str, limit: int = 5) -> List[Dict]:
        """Search for relevant documents."""
        return await self.vector_store.search(query, organization_id, limit)

    async def get_training_context(self, topic: str, organization_id: str, max_length: int = 4000) -> str:
        """Get context for training generation."""
        results = await self.search_documents(topic, organization_id, 10)
        if not results:
            return ""
        context_parts = []
        current_length = 0
        for result in results:
            if current_length + len(result["text"]) > max_length:
                break
            context_parts.append(result["text"])
            current_length += len(result["text"])
        return "\n\n---\n\n".join(context_parts)

    async def answer_question_with_context(self, question: str, organization_id: str) -> Dict:
        """Answer a question using RAG context."""
        if not GENAI_AVAILABLE or not os.getenv("GEMINI_API_KEY"):
            return {"answer": "AI service not available", "sources": []}

        try:
            results = await self.search_documents(question, organization_id, 5)
            if not results:
                return {"answer": "No relevant documentation found.", "sources": []}

            context = "\n\n".join([r["text"] for r in results])
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"Answer this question using the context:\n\nQUESTION: {question}\n\nCONTEXT:\n{context}"
            response = model.generate_content(prompt)

            return {
                "answer": response.text,
                "sources": [{"document_id": r["document_id"], "similarity": r["similarity"]} for r in results],
            }
        except Exception as e:
            logger.error(f"Answer failed: {e}")
            return {"answer": f"Error: {e}", "sources": []}

    async def list_documents(self, organization_id: str, limit: int = 50) -> List[Dict]:
        """List documents."""
        return await self.vector_store.list_documents(organization_id, limit)

    async def delete_document(self, document_id: str, organization_id: str) -> bool:
        """Delete a document."""
        return await self.vector_store.delete_document(document_id, organization_id)


rag_service = RAGService()
