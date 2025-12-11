"""
Advanced Knowledge Search and Indexing System
Searchable knowledge base with semantic search capabilities
Never lose any development knowledge - Everything is searchable and retrievable
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import firebase_admin
from firebase_admin import firestore
from .memory_system import get_memory_system, ComprehensiveMemorySystem

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    item_id: str
    item_type: str  # 'conversation', 'mistake', 'solution', 'code_change'
    relevance_score: float
    content_preview: str
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class KnowledgeIndex:
    index_id: str
    content_type: str
    text_content: str
    keywords: List[str]
    embeddings: Optional[List[float]]
    metadata: Dict[str, Any]
    last_updated: datetime

class AdvancedKnowledgeSearch:
    """Advanced search system with semantic understanding and indexing"""
    
    def __init__(self):
        self.memory_system = get_memory_system()
        self.db = self.memory_system.db
        self.index_collection = "knowledge_index"
        self.search_cache = {}
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 3),  # Include unigrams, bigrams, and trigrams
            max_df=0.95,
            min_df=2
        )
        self.document_vectors = None
        self.document_metadata = []
        
    async def build_searchable_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Build comprehensive searchable index from all knowledge sources"""
        try:
            logger.info("🔍 Building comprehensive knowledge index...")
            
            # Check if index needs rebuilding
            if not force_rebuild and await self._index_is_current():
                logger.info("📚 Knowledge index is current, skipping rebuild")
                return {"status": "current", "message": "Index is up to date"}
            
            # Clear existing index if rebuilding
            if force_rebuild:
                await self._clear_index()
            
            # Collect all searchable content
            searchable_content = []
            
            # Index conversations
            conversations_indexed = await self._index_conversations(searchable_content)
            
            # Index mistakes
            mistakes_indexed = await self._index_mistakes(searchable_content)
            
            # Index solutions
            solutions_indexed = await self._index_solutions(searchable_content)
            
            # Index code changes
            code_changes_indexed = await self._index_code_changes(searchable_content)
            
            # Build TF-IDF vectors for semantic search
            if searchable_content:
                await self._build_semantic_vectors(searchable_content)
            
            # Store index metadata
            index_metadata = {
                "total_items_indexed": len(searchable_content),
                "conversations": conversations_indexed,
                "mistakes": mistakes_indexed,
                "solutions": solutions_indexed,
                "code_changes": code_changes_indexed,
                "last_updated": datetime.now(timezone.utc),
                "index_version": "2.0"
            }
            
            await self._store_index_metadata(index_metadata)
            
            logger.info(f"✅ Knowledge index built successfully: {len(searchable_content)} items indexed")
            return {
                "status": "success",
                "message": f"Index built with {len(searchable_content)} items",
                "metadata": index_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to build knowledge index: {e}")
            return {"status": "error", "error": str(e)}
    
    async def search_knowledge(self, 
                             query: str, 
                             content_types: Optional[List[str]] = None,
                             project_context: Optional[str] = None,
                             date_range: Optional[Tuple[datetime, datetime]] = None,
                             limit: int = 20) -> List[SearchResult]:
        """Advanced search with semantic understanding"""
        try:
            if not query.strip():
                return []
            
            # Ensure index exists
            if not await self._index_exists():
                await self.build_searchable_index()
            
            # Multi-strategy search approach
            results = []
            
            # 1. Exact keyword search
            exact_results = await self._keyword_search(query, content_types, project_context, date_range)
            results.extend(exact_results)
            
            # 2. Semantic similarity search
            semantic_results = await self._semantic_search(query, content_types, project_context, date_range)
            results.extend(semantic_results)
            
            # 3. Fuzzy pattern matching
            pattern_results = await self._pattern_search(query, content_types, project_context, date_range)
            results.extend(pattern_results)
            
            # Deduplicate and rank results
            unique_results = await self._deduplicate_and_rank(results, query)
            
            # Apply limit
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    async def suggest_related_knowledge(self, 
                                      current_context: Dict[str, Any], 
                                      limit: int = 5) -> List[SearchResult]:
        """Suggest related knowledge based on current development context"""
        try:
            # Extract keywords from current context
            context_text = json.dumps(current_context, default=str)
            keywords = await self._extract_keywords(context_text)
            
            if not keywords:
                return []
            
            # Search for related content
            query = " ".join(keywords[:10])  # Use top 10 keywords
            results = await self.search_knowledge(query, limit=limit)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to suggest related knowledge: {e}")
            return []
    
    async def find_solution_patterns(self, 
                                   problem_description: str,
                                   similarity_threshold: float = 0.3) -> List[SearchResult]:
        """Find solution patterns for similar problems"""
        try:
            # Search specifically for solutions
            results = await self.search_knowledge(
                query=problem_description,
                content_types=['solution'],
                limit=10
            )
            
            # Filter by similarity threshold
            filtered_results = [r for r in results if r.relevance_score >= similarity_threshold]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to find solution patterns: {e}")
            return []
    
    async def find_mistake_patterns(self, 
                                  action_description: str,
                                  risk_threshold: float = 0.4) -> List[SearchResult]:
        """Find mistake patterns that might be relevant to current action"""
        try:
            # Search specifically for mistakes
            results = await self.search_knowledge(
                query=action_description,
                content_types=['mistake'],
                limit=10
            )
            
            # Filter by risk threshold
            risky_patterns = [r for r in results if r.relevance_score >= risk_threshold]
            
            return risky_patterns
            
        except Exception as e:
            logger.error(f"Failed to find mistake patterns: {e}")
            return []
    
    async def _index_conversations(self, searchable_content: List[KnowledgeIndex]) -> int:
        """Index all conversations for search"""
        try:
            conversations_ref = self.db.collection("ai_conversations")
            docs = conversations_ref.limit(1000).stream()  # Process in batches
            
            count = 0
            for doc in docs:
                conv_data = doc.to_dict()
                
                # Create searchable text
                searchable_text = f"{conv_data.get('user_prompt', '')} "
                
                # Add AI responses
                for response in conv_data.get('ai_responses', []):
                    searchable_text += f"{response.get('response', '')} "
                
                # Add lessons learned
                searchable_text += " ".join(conv_data.get('lessons_learned', []))
                
                # Extract keywords
                keywords = await self._extract_keywords(searchable_text)
                
                index_item = KnowledgeIndex(
                    index_id=doc.id,
                    content_type="conversation",
                    text_content=searchable_text.strip(),
                    keywords=keywords,
                    embeddings=None,  # Will be computed later
                    metadata={
                        "project_context": conv_data.get('project_context', ''),
                        "ai_models": conv_data.get('ai_models_involved', []),
                        "outcome_rating": conv_data.get('outcome_rating', 0),
                        "timestamp": conv_data.get('timestamp')
                    },
                    last_updated=datetime.now(timezone.utc)
                )
                
                searchable_content.append(index_item)
                count += 1
            
            logger.info(f"📝 Indexed {count} conversations")
            return count
            
        except Exception as e:
            logger.error(f"Failed to index conversations: {e}")
            return 0
    
    async def _index_mistakes(self, searchable_content: List[KnowledgeIndex]) -> int:
        """Index all mistake patterns for search"""
        try:
            mistakes_ref = self.db.collection("mistake_patterns")
            docs = mistakes_ref.limit(1000).stream()
            
            count = 0
            for doc in docs:
                mistake_data = doc.to_dict()
                
                # Create searchable text
                searchable_text = (
                    f"{mistake_data.get('description', '')} "
                    f"{mistake_data.get('prevention_strategy', '')} "
                    f"{' '.join(mistake_data.get('resolution_steps', []))}"
                )
                
                keywords = await self._extract_keywords(searchable_text)
                
                index_item = KnowledgeIndex(
                    index_id=doc.id,
                    content_type="mistake",
                    text_content=searchable_text.strip(),
                    keywords=keywords,
                    embeddings=None,
                    metadata={
                        "mistake_type": mistake_data.get('mistake_type', ''),
                        "impact_severity": mistake_data.get('impact_severity', ''),
                        "how_detected": mistake_data.get('how_detected', ''),
                        "timestamp": mistake_data.get('when_occurred')
                    },
                    last_updated=datetime.now(timezone.utc)
                )
                
                searchable_content.append(index_item)
                count += 1
            
            logger.info(f"🚨 Indexed {count} mistake patterns")
            return count
            
        except Exception as e:
            logger.error(f"Failed to index mistakes: {e}")
            return 0
    
    async def _index_solutions(self, searchable_content: List[KnowledgeIndex]) -> int:
        """Index all solution patterns for search"""
        try:
            solutions_ref = self.db.collection("solution_knowledge_base")
            docs = solutions_ref.limit(1000).stream()
            
            count = 0
            for doc in docs:
                solution_data = doc.to_dict()
                
                # Create searchable text
                searchable_text = (
                    f"{solution_data.get('problem_pattern', '')} "
                    f"{' '.join(solution_data.get('solution_steps', []))} "
                    f"{' '.join(solution_data.get('best_practices', []))}"
                )
                
                keywords = await self._extract_keywords(searchable_text)
                
                index_item = KnowledgeIndex(
                    index_id=doc.id,
                    content_type="solution",
                    text_content=searchable_text.strip(),
                    keywords=keywords,
                    embeddings=None,
                    metadata={
                        "success_rate": solution_data.get('success_rate', 0),
                        "applications": solution_data.get('applications_used_in', []),
                        "performance_metrics": solution_data.get('performance_metrics', {}),
                        "timestamp": datetime.now(timezone.utc)  # Solutions don't have creation time
                    },
                    last_updated=datetime.now(timezone.utc)
                )
                
                searchable_content.append(index_item)
                count += 1
            
            logger.info(f"✅ Indexed {count} solution patterns")
            return count
            
        except Exception as e:
            logger.error(f"Failed to index solutions: {e}")
            return 0
    
    async def _index_code_changes(self, searchable_content: List[KnowledgeIndex]) -> int:
        """Index all code changes for search"""
        try:
            code_changes_ref = self.db.collection("code_changes")
            docs = code_changes_ref.limit(1000).stream()
            
            count = 0
            for doc in docs:
                change_data = doc.to_dict()
                
                # Create searchable text
                searchable_text = (
                    f"{change_data.get('change_description', '')} "
                    f"{change_data.get('ai_reasoning', '')} "
                    f"{' '.join(change_data.get('files_modified', []))}"
                )
                
                keywords = await self._extract_keywords(searchable_text)
                
                index_item = KnowledgeIndex(
                    index_id=doc.id,
                    content_type="code_change",
                    text_content=searchable_text.strip(),
                    keywords=keywords,
                    embeddings=None,
                    metadata={
                        "files_modified": change_data.get('files_modified', []),
                        "test_results": change_data.get('test_results', {}),
                        "performance_impact": change_data.get('performance_impact', {}),
                        "timestamp": change_data.get('timestamp')
                    },
                    last_updated=datetime.now(timezone.utc)
                )
                
                searchable_content.append(index_item)
                count += 1
            
            logger.info(f"🔧 Indexed {count} code changes")
            return count
            
        except Exception as e:
            logger.error(f"Failed to index code changes: {e}")
            return 0
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        try:
            # Clean and normalize text
            text = re.sub(r'[^\w\s]', ' ', text.lower())
            text = ' '.join(text.split())  # Normalize whitespace
            
            # Split into words and filter
            words = text.split()
            
            # Filter out common stop words and short words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                         'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                         'should', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                         'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            
            keywords = []
            for word in words:
                if len(word) > 2 and word not in stop_words:
                    keywords.append(word)
            
            # Return unique keywords, prioritizing longer ones
            unique_keywords = list(set(keywords))
            unique_keywords.sort(key=len, reverse=True)
            
            return unique_keywords[:20]  # Limit to top 20 keywords
            
        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []
    
    async def _build_semantic_vectors(self, searchable_content: List[KnowledgeIndex]):
        """Build semantic vectors for similarity search"""
        try:
            if not searchable_content:
                return
            
            # Prepare documents for vectorization
            documents = [item.text_content for item in searchable_content]
            
            # Build TF-IDF vectors
            self.document_vectors = self.vectorizer.fit_transform(documents)
            
            # Store document metadata for lookup
            self.document_metadata = [
                {
                    "index_id": item.index_id,
                    "content_type": item.content_type,
                    "metadata": item.metadata
                }
                for item in searchable_content
            ]
            
            logger.info(f"🧠 Built semantic vectors for {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to build semantic vectors: {e}")
    
    async def _keyword_search(self, 
                            query: str, 
                            content_types: Optional[List[str]] = None,
                            project_context: Optional[str] = None,
                            date_range: Optional[Tuple[datetime, datetime]] = None) -> List[SearchResult]:
        """Perform exact keyword search"""
        try:
            results = []
            query_lower = query.lower()
            
            # Search in all indexed content
            index_ref = self.db.collection(self.index_collection)
            docs = index_ref.limit(100).stream()
            
            for doc in docs:
                index_data = doc.to_dict()
                
                # Apply content type filter
                if content_types and index_data.get('content_type') not in content_types:
                    continue
                
                # Apply project context filter
                if project_context and index_data.get('metadata', {}).get('project_context') != project_context:
                    continue
                
                # Check if query keywords match
                text_content = index_data.get('text_content', '').lower()
                keywords = index_data.get('keywords', [])
                
                # Calculate relevance score
                relevance_score = 0
                
                # Exact phrase match (highest score)
                if query_lower in text_content:
                    relevance_score += 1.0
                
                # Keyword matches
                query_words = query_lower.split()
                matching_keywords = sum(1 for word in query_words if word in keywords)
                if len(query_words) > 0:
                    relevance_score += (matching_keywords / len(query_words)) * 0.8
                
                if relevance_score > 0.3:  # Minimum threshold
                    result = SearchResult(
                        item_id=index_data['index_id'],
                        item_type=index_data['content_type'],
                        relevance_score=relevance_score,
                        content_preview=text_content[:200] + "..." if len(text_content) > 200 else text_content,
                        metadata=index_data.get('metadata', {}),
                        timestamp=index_data.get('metadata', {}).get('timestamp', datetime.now(timezone.utc))
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    async def _semantic_search(self, 
                             query: str,
                             content_types: Optional[List[str]] = None,
                             project_context: Optional[str] = None,
                             date_range: Optional[Tuple[datetime, datetime]] = None) -> List[SearchResult]:
        """Perform semantic similarity search"""
        try:
            if self.document_vectors is None or len(self.document_metadata) == 0:
                return []
            
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarity scores
            similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
            
            results = []
            for i, similarity_score in enumerate(similarities):
                if similarity_score > 0.2:  # Minimum similarity threshold
                    metadata = self.document_metadata[i]
                    
                    # Apply filters
                    if content_types and metadata['content_type'] not in content_types:
                        continue
                    
                    if project_context and metadata['metadata'].get('project_context') != project_context:
                        continue
                    
                    result = SearchResult(
                        item_id=metadata['index_id'],
                        item_type=metadata['content_type'],
                        relevance_score=float(similarity_score),
                        content_preview=f"Semantic match (score: {similarity_score:.3f})",
                        metadata=metadata['metadata'],
                        timestamp=metadata['metadata'].get('timestamp', datetime.now(timezone.utc))
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def _pattern_search(self, 
                            query: str,
                            content_types: Optional[List[str]] = None,
                            project_context: Optional[str] = None,
                            date_range: Optional[Tuple[datetime, datetime]] = None) -> List[SearchResult]:
        """Perform fuzzy pattern matching search"""
        try:
            # This is a simplified pattern search - can be enhanced with fuzzy matching libraries
            results = []
            
            # Extract patterns from query
            patterns = [word.strip() for word in query.split() if len(word.strip()) > 3]
            
            if not patterns:
                return []
            
            # Search with pattern matching logic
            # For now, this is similar to keyword search but with more flexible matching
            return await self._keyword_search(query, content_types, project_context, date_range)
            
        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return []
    
    async def _deduplicate_and_rank(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Remove duplicates and rank results by relevance"""
        try:
            # Remove duplicates by item_id
            seen_ids = set()
            unique_results = []
            
            for result in results:
                if result.item_id not in seen_ids:
                    seen_ids.add(result.item_id)
                    unique_results.append(result)
            
            # Sort by relevance score (highest first)
            unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Failed to deduplicate and rank results: {e}")
            return results
    
    async def _index_is_current(self) -> bool:
        """Check if the search index is current"""
        try:
            metadata_ref = self.db.collection("system_metadata").document("knowledge_index")
            doc = metadata_ref.get()
            
            if not doc.exists:
                return False
            
            metadata = doc.to_dict()
            last_updated = metadata.get('last_updated')
            
            if not last_updated:
                return False
            
            # Check if index is less than 1 day old
            if isinstance(last_updated, datetime):
                age = datetime.now(timezone.utc) - last_updated
                return age < timedelta(days=1)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check index currency: {e}")
            return False
    
    async def _index_exists(self) -> bool:
        """Check if search index exists"""
        try:
            metadata_ref = self.db.collection("system_metadata").document("knowledge_index")
            doc = metadata_ref.get()
            return doc.exists
            
        except Exception as e:
            logger.error(f"Failed to check index existence: {e}")
            return False
    
    async def _clear_index(self):
        """Clear existing search index"""
        try:
            # Clear index collection
            index_ref = self.db.collection(self.index_collection)
            docs = index_ref.limit(100).stream()
            
            for doc in docs:
                doc.reference.delete()
            
            logger.info("🗑️ Cleared existing knowledge index")
            
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
    
    async def _store_index_metadata(self, metadata: Dict[str, Any]):
        """Store index metadata"""
        try:
            metadata_ref = self.db.collection("system_metadata").document("knowledge_index")
            metadata_ref.set(metadata)
            
            # Also store individual index items
            for i, doc_meta in enumerate(self.document_metadata):
                index_ref = self.db.collection(self.index_collection).document(f"item_{i}")
                index_ref.set({
                    "index_id": doc_meta["index_id"],
                    "content_type": doc_meta["content_type"],
                    "metadata": doc_meta["metadata"],
                    "text_content": "",  # Don't store full content in index
                    "keywords": [],
                    "last_updated": datetime.now(timezone.utc)
                })
            
        except Exception as e:
            logger.error(f"Failed to store index metadata: {e}")

# Global knowledge search instance
_knowledge_search = None

def get_knowledge_search() -> AdvancedKnowledgeSearch:
    """Get the global knowledge search instance"""
    global _knowledge_search
    if _knowledge_search is None:
        _knowledge_search = AdvancedKnowledgeSearch()
    return _knowledge_search