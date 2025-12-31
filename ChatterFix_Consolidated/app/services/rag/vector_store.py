"""
Vector Store for RAG
Handles embedding storage and similarity search using Firestore + Gemini embeddings.
"""

import logging
import os
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False


class VectorStore:
    """Vector storage and similarity search."""

    def __init__(self, collection_name: str = "rag_documents"):
        self.collection_name = collection_name
        self.embedding_model = "models/text-embedding-004"
        if GENAI_AVAILABLE and os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        if not GENAI_AVAILABLE or not os.getenv("GEMINI_API_KEY"):
            return self._simulate_embedding(text)
        try:
            result = genai.embed_content(model=self.embedding_model, content=text, task_type="retrieval_document")
            return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return self._simulate_embedding(text)

    def _simulate_embedding(self, text: str, dimensions: int = 768) -> List[float]:
        """Simulate embedding for development."""
        import hashlib
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        vector = np.random.randn(dimensions)
        return (vector / np.linalg.norm(vector)).tolist()

    async def store_document(self, document_id: str, chunks: List[Dict], metadata: Dict, organization_id: str) -> Dict:
        """Store document chunks with embeddings in Firestore."""
        from app.core.firestore_db import get_firestore_manager
        firestore_manager = get_firestore_manager()
        stored_ids = []

        try:
            doc_record = {
                "document_id": document_id,
                "organization_id": organization_id,
                "metadata": metadata,
                "chunk_count": len(chunks),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "processing",
            }
            await firestore_manager.create_document(self.collection_name, doc_record, doc_id=document_id)

            for chunk in chunks:
                embedding = await self.generate_embedding(chunk["text"])
                chunk_record = {
                    "document_id": document_id,
                    "organization_id": organization_id,
                    "chunk_id": chunk["id"],
                    "text": chunk["text"],
                    "embedding": embedding,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                chunk_id = await firestore_manager.create_document(f"{self.collection_name}_chunks", chunk_record)
                stored_ids.append(chunk_id)

            await firestore_manager.update_document(self.collection_name, document_id, {"status": "indexed"})
            return {"success": True, "document_id": document_id, "vector_ids": stored_ids}
        except Exception as e:
            logger.error(f"Store failed: {e}")
            return {"success": False, "error": str(e)}

    async def search(self, query: str, organization_id: str, limit: int = 5) -> List[Dict]:
        """Search for similar documents."""
        from app.core.firestore_db import get_firestore_manager
        firestore_manager = get_firestore_manager()

        try:
            query_embedding = await self.generate_embedding(query)
            chunks = await firestore_manager.get_collection(
                f"{self.collection_name}_chunks",
                filters=[{"field": "organization_id", "operator": "==", "value": organization_id}],
            )

            results = []
            for chunk in chunks:
                if "embedding" in chunk:
                    similarity = self._cosine_similarity(query_embedding, chunk["embedding"])
                    if similarity >= 0.5:
                        results.append({"document_id": chunk.get("document_id"), "text": chunk.get("text"), "similarity": similarity})

            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity."""
        v1, v2 = np.array(vec1), np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    async def list_documents(self, organization_id: str, limit: int = 50) -> List[Dict]:
        """List all documents for an organization."""
        from app.core.firestore_db import get_firestore_manager
        firestore_manager = get_firestore_manager()
        try:
            return await firestore_manager.get_collection(
                self.collection_name,
                filters=[{"field": "organization_id", "operator": "==", "value": organization_id}],
                limit=limit,
            )
        except Exception as e:
            logger.error(f"List failed: {e}")
            return []

    async def delete_document(self, document_id: str, organization_id: str) -> bool:
        """Delete a document and its chunks."""
        from app.core.firestore_db import get_firestore_manager
        firestore_manager = get_firestore_manager()
        try:
            doc = await firestore_manager.get_document(self.collection_name, document_id)
            if not doc or doc.get("organization_id") != organization_id:
                return False
            chunks = await firestore_manager.get_collection(
                f"{self.collection_name}_chunks",
                filters=[{"field": "document_id", "operator": "==", "value": document_id}],
            )
            for chunk in chunks:
                await firestore_manager.delete_document(f"{self.collection_name}_chunks", chunk["id"])
            await firestore_manager.delete_document(self.collection_name, document_id)
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
