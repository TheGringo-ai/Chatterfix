#!/usr/bin/env python3
"""
ChatterFix CMMS - RAG Memory System
Advanced memory and retrieval system for AI team with vector embeddings
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
import os
import logging
import sqlite3
import numpy as np
import httpx
import asyncio
import uuid
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix RAG Memory System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Memory Models
class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    memory_type: str = "conversation"  # conversation, knowledge, pattern, technical
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    relevance_score: float = 1.0
    embedding: Optional[List[float]] = None

class MemoryQuery(BaseModel):
    query: str
    memory_types: List[str] = ["conversation", "knowledge", "pattern", "technical"]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    limit: int = 5
    min_similarity: float = 0.7

class RAGMemorySystem:
    def __init__(self):
        self.embedding_model = None
        self.vector_index = None
        self.memory_db = "rag_memory.db"
        self.vector_storage = "memory_vectors.faiss"
        self.memory_mapping = "memory_mapping.pkl"
        self.initialize_system()
    
    def initialize_system(self):
        """Initialize RAG memory system"""
        try:
            # Load embedding model
            print("🧠 Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize database
            self.init_database()
            
            # Load or create vector index
            self.load_vector_index()
            
            print("✅ RAG Memory System initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize RAG system: {e}")
            # Fallback to simple text storage
            self.embedding_model = None
    
    def init_database(self):
        """Initialize SQLite database for memory storage"""
        conn = sqlite3.connect(self.memory_db)
        cursor = conn.cursor()
        
        # Create memory table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_entries (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            memory_type TEXT DEFAULT 'conversation',
            user_id TEXT,
            session_id TEXT,
            relevance_score REAL DEFAULT 1.0,
            embedding_index INTEGER
        )
        ''')
        
        # Create indexes for fast retrieval
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON memory_entries(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON memory_entries(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_entries(timestamp)')
        
        conn.commit()
        conn.close()
    
    def load_vector_index(self):
        """Load or create FAISS vector index"""
        try:
            if os.path.exists(self.vector_storage) and os.path.exists(self.memory_mapping):
                # Load existing index
                self.vector_index = faiss.read_index(self.vector_storage)
                with open(self.memory_mapping, 'rb') as f:
                    self.id_mapping = pickle.load(f)
                print(f"📚 Loaded existing vector index with {self.vector_index.ntotal} entries")
            else:
                # Create new index (384 dimensions for all-MiniLM-L6-v2)
                self.vector_index = faiss.IndexFlatIP(384)  # Inner product for cosine similarity
                self.id_mapping = {}
                print("🆕 Created new vector index")
                
        except Exception as e:
            print(f"⚠️ Error with vector index: {e}")
            self.vector_index = faiss.IndexFlatIP(384)
            self.id_mapping = {}
    
    def save_vector_index(self):
        """Save vector index to disk"""
        try:
            faiss.write_index(self.vector_index, self.vector_storage)
            with open(self.memory_mapping, 'wb') as f:
                pickle.dump(self.id_mapping, f)
        except Exception as e:
            print(f"⚠️ Error saving vector index: {e}")
    
    def add_memory(self, memory: MemoryEntry) -> bool:
        """Add memory entry to system"""
        try:
            # Generate embedding if model available
            embedding = None
            embedding_index = None
            
            if self.embedding_model:
                embedding = self.embedding_model.encode(memory.content)
                # Add to vector index
                embedding_normalized = embedding / np.linalg.norm(embedding)
                self.vector_index.add(np.array([embedding_normalized]))
                embedding_index = self.vector_index.ntotal - 1
                self.id_mapping[embedding_index] = memory.id
                self.save_vector_index()
            
            # Store in database
            conn = sqlite3.connect(self.memory_db)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO memory_entries 
            (id, content, metadata, timestamp, memory_type, user_id, session_id, relevance_score, embedding_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.id,
                memory.content,
                json.dumps(memory.metadata),
                memory.timestamp.isoformat(),
                memory.memory_type,
                memory.user_id,
                memory.session_id,
                memory.relevance_score,
                embedding_index
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    def search_memories(self, query: MemoryQuery) -> List[Dict]:
        """Search memories using semantic similarity"""
        try:
            memories = []
            
            if self.embedding_model and self.vector_index.ntotal > 0:
                # Semantic search
                query_embedding = self.embedding_model.encode(query.query)
                query_normalized = query_embedding / np.linalg.norm(query_embedding)
                
                # Search vector index
                similarities, indices = self.vector_index.search(
                    np.array([query_normalized]), 
                    min(query.limit * 2, self.vector_index.ntotal)
                )
                
                # Get memory IDs from similarities
                memory_ids = []
                for i, (similarity, index) in enumerate(zip(similarities[0], indices[0])):
                    if similarity >= query.min_similarity and index in self.id_mapping:
                        memory_ids.append((self.id_mapping[index], similarity))
                
                # Fetch from database
                if memory_ids:
                    conn = sqlite3.connect(self.memory_db)
                    cursor = conn.cursor()
                    
                    placeholders = ','.join('?' * len(memory_ids))
                    ids_only = [mid[0] for mid in memory_ids]
                    
                    query_sql = f'''
                    SELECT id, content, metadata, timestamp, memory_type, user_id, session_id, relevance_score
                    FROM memory_entries 
                    WHERE id IN ({placeholders})
                    '''
                    
                    # Add filters
                    filters = []
                    params = ids_only.copy()
                    
                    if query.memory_types:
                        type_placeholders = ','.join('?' * len(query.memory_types))
                        filters.append(f"memory_type IN ({type_placeholders})")
                        params.extend(query.memory_types)
                    
                    if query.user_id:
                        filters.append("user_id = ?")
                        params.append(query.user_id)
                    
                    if query.session_id:
                        filters.append("session_id = ?")
                        params.append(query.session_id)
                    
                    if filters:
                        query_sql += " AND " + " AND ".join(filters)
                    
                    query_sql += " ORDER BY relevance_score DESC LIMIT ?"
                    params.append(query.limit)
                    
                    cursor.execute(query_sql, params)
                    results = cursor.fetchall()
                    
                    # Combine with similarity scores
                    similarity_map = {mid[0]: mid[1] for mid in memory_ids}
                    
                    for row in results:
                        memory_id = row[0]
                        memories.append({
                            "id": memory_id,
                            "content": row[1],
                            "metadata": json.loads(row[2] or "{}"),
                            "timestamp": row[3],
                            "memory_type": row[4],
                            "user_id": row[5],
                            "session_id": row[6],
                            "relevance_score": float(row[7]),
                            "similarity_score": float(similarity_map.get(memory_id, 0.0))
                        })
                    
                    conn.close()
            
            else:
                # Fallback to text search
                memories = self.text_search_fallback(query)
            
            return memories[:query.limit]
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    def text_search_fallback(self, query: MemoryQuery) -> List[Dict]:
        """Fallback text search when vector search unavailable"""
        try:
            conn = sqlite3.connect(self.memory_db)
            cursor = conn.cursor()
            
            # Simple text search
            search_terms = query.query.lower().split()
            like_conditions = []
            params = []
            
            for term in search_terms:
                like_conditions.append("LOWER(content) LIKE ?")
                params.append(f"%{term}%")
            
            where_clause = " OR ".join(like_conditions)
            
            query_sql = f"SELECT * FROM memory_entries WHERE ({where_clause})"
            
            # Add filters
            if query.memory_types:
                type_placeholders = ','.join('?' * len(query.memory_types))
                query_sql += f" AND memory_type IN ({type_placeholders})"
                params.extend(query.memory_types)
            
            if query.user_id:
                query_sql += " AND user_id = ?"
                params.append(query.user_id)
            
            if query.session_id:
                query_sql += " AND session_id = ?"
                params.append(query.session_id)
            
            query_sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(query.limit)
            
            cursor.execute(query_sql, params)
            results = cursor.fetchall()
            
            memories = []
            for row in results:
                memories.append({
                    "id": row[0],
                    "content": row[1],
                    "metadata": json.loads(row[2] or "{}"),
                    "timestamp": row[3],
                    "memory_type": row[4],
                    "user_id": row[5],
                    "session_id": row[6],
                    "relevance_score": float(row[7]),
                    "similarity_score": 0.5  # Default for text search
                })
            
            conn.close()
            return memories
            
        except Exception as e:
            logger.error(f"Error in text search fallback: {e}")
            return []

# Initialize RAG system
rag_system = RAGMemorySystem()

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "ChatterFix RAG Memory System",
        "status": "active",
        "features": ["semantic_search", "vector_embeddings", "conversation_memory", "knowledge_base"],
        "memory_count": rag_system.vector_index.ntotal if rag_system.vector_index else 0
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "RAG Memory System",
        "embedding_model": "all-MiniLM-L6-v2" if rag_system.embedding_model else "text_only",
        "memory_count": rag_system.vector_index.ntotal if rag_system.vector_index else 0,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/memory/add")
async def add_memory(memory: MemoryEntry):
    """Add new memory entry"""
    success = rag_system.add_memory(memory)
    if success:
        return {
            "status": "added", 
            "memory_id": memory.id,
            "memory_count": rag_system.vector_index.ntotal if rag_system.vector_index else 0
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to add memory")

@app.post("/memory/search")
async def search_memories(query: MemoryQuery):
    """Search memories using semantic similarity"""
    memories = rag_system.search_memories(query)
    return {
        "query": query.query,
        "results_count": len(memories),
        "memories": memories,
        "search_type": "semantic" if rag_system.embedding_model else "text"
    }

@app.post("/memory/conversation")
async def add_conversation_memory(request: Dict[str, Any]):
    """Add conversation to memory"""
    user_message = request.get("user_message", "")
    ai_response = request.get("ai_response", "")
    context = request.get("context", {})
    
    # Create memory entries
    memories_added = []
    
    if user_message:
        user_memory = MemoryEntry(
            content=f"User: {user_message}",
            metadata={"type": "user_input", **context},
            memory_type="conversation",
            user_id=context.get("user_id"),
            session_id=context.get("session_id")
        )
        if rag_system.add_memory(user_memory):
            memories_added.append(user_memory.id)
    
    if ai_response:
        ai_memory = MemoryEntry(
            content=f"AI: {ai_response}",
            metadata={"type": "ai_response", **context},
            memory_type="conversation",
            user_id=context.get("user_id"),
            session_id=context.get("session_id")
        )
        if rag_system.add_memory(ai_memory):
            memories_added.append(ai_memory.id)
    
    return {
        "status": "conversation_stored",
        "memories_added": len(memories_added),
        "memory_ids": memories_added
    }

@app.get("/memory/stats")
async def memory_stats():
    """Get memory system statistics"""
    try:
        conn = sqlite3.connect(rag_system.memory_db)
        cursor = conn.cursor()
        
        # Get counts by type
        cursor.execute("SELECT memory_type, COUNT(*) FROM memory_entries GROUP BY memory_type")
        type_counts = dict(cursor.fetchall())
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM memory_entries")
        total_count = cursor.fetchone()[0]
        
        # Get recent activity
        cursor.execute("SELECT COUNT(*) FROM memory_entries WHERE timestamp > datetime('now', '-1 hour')")
        recent_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_memories": total_count,
            "memory_by_type": type_counts,
            "recent_activity": recent_count,
            "vector_count": rag_system.vector_index.ntotal if rag_system.vector_index else 0,
            "embedding_model": "all-MiniLM-L6-v2" if rag_system.embedding_model else "none"
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8014))
    print(f"🧠 Starting ChatterFix RAG Memory System on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)