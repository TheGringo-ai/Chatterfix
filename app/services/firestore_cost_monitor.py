"""
Firestore Cost Monitor & Data Retention Service
Monitors collection sizes, estimates costs, and prunes old log data.

Firestore Pricing (as of 2024):
- Document reads: $0.036 per 100,000
- Document writes: $0.108 per 100,000
- Document deletes: $0.012 per 100,000
- Storage: $0.108 per GB/month

This service helps prevent runaway costs from logging.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


class RetentionPolicy(str, Enum):
    """Data retention policies for different collection types"""
    CRITICAL = "critical"      # Never auto-delete (work_orders, assets, users)
    LONG_TERM = "long_term"    # 365 days (audit_logs, safety_incidents)
    MEDIUM_TERM = "medium"     # 90 days (ai_conversations, team_messages)
    SHORT_TERM = "short"       # 30 days (voice_logs, zone_entries)
    TEMPORARY = "temporary"    # 7 days (debug logs, temp data)


@dataclass
class CollectionStats:
    """Statistics for a Firestore collection"""
    name: str
    document_count: int
    estimated_size_bytes: int
    oldest_document_date: Optional[datetime]
    retention_policy: RetentionPolicy
    estimated_monthly_cost: float


# Collection retention configuration
COLLECTION_RETENTION = {
    # Critical data - never auto-delete
    "users": RetentionPolicy.CRITICAL,
    "organizations": RetentionPolicy.CRITICAL,
    "work_orders": RetentionPolicy.CRITICAL,
    "assets": RetentionPolicy.CRITICAL,
    "parts": RetentionPolicy.CRITICAL,
    "vendors": RetentionPolicy.CRITICAL,
    "training_modules": RetentionPolicy.CRITICAL,

    # Long-term logs - 365 days
    "audit_logs": RetentionPolicy.LONG_TERM,
    "safety_incidents": RetentionPolicy.LONG_TERM,
    "mistake_patterns": RetentionPolicy.LONG_TERM,
    "solution_knowledge_base": RetentionPolicy.LONG_TERM,

    # Medium-term logs - 90 days
    "ai_conversations": RetentionPolicy.MEDIUM_TERM,
    "ai_interactions": RetentionPolicy.MEDIUM_TERM,
    "team_messages": RetentionPolicy.MEDIUM_TERM,
    "code_changes": RetentionPolicy.MEDIUM_TERM,

    # Short-term logs - 30 days
    "voice_logs": RetentionPolicy.SHORT_TERM,
    "zone_entries": RetentionPolicy.SHORT_TERM,
    "logistics_inspections": RetentionPolicy.SHORT_TERM,

    # Temporary data - 7 days
    "debug_logs": RetentionPolicy.TEMPORARY,
    "session_cache": RetentionPolicy.TEMPORARY,
}

RETENTION_DAYS = {
    RetentionPolicy.CRITICAL: None,  # Never delete
    RetentionPolicy.LONG_TERM: 365,
    RetentionPolicy.MEDIUM_TERM: 90,
    RetentionPolicy.SHORT_TERM: 30,
    RetentionPolicy.TEMPORARY: 7,
}


class FirestoreCostMonitor:
    """
    Monitors Firestore usage and costs, provides cleanup for old data.
    """

    def __init__(self):
        self.firestore = get_firestore_manager()
        self._stats_cache: Dict[str, CollectionStats] = {}
        self._cache_timestamp: Optional[datetime] = None

    async def get_collection_stats(self, collection_name: str) -> CollectionStats:
        """Get statistics for a single collection"""
        try:
            # Get document count (limited query to avoid full scan costs)
            docs = await self.firestore.get_collection(collection_name, limit=1000)
            doc_count = len(docs)

            # Estimate if more than 1000
            if doc_count == 1000:
                # This is approximate - full count would be expensive
                doc_count = await self._estimate_collection_size(collection_name)

            # Estimate storage (avg 1KB per document for logs, 2KB for entities)
            avg_doc_size = 1024 if "log" in collection_name or "conversation" in collection_name else 2048
            estimated_size = doc_count * avg_doc_size

            # Get oldest document
            oldest_date = None
            if docs:
                for doc in docs:
                    timestamp = doc.get("timestamp") or doc.get("created_at")
                    if timestamp:
                        if isinstance(timestamp, str):
                            try:
                                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            except:
                                continue
                        if oldest_date is None or timestamp < oldest_date:
                            oldest_date = timestamp

            # Get retention policy
            retention = COLLECTION_RETENTION.get(collection_name, RetentionPolicy.MEDIUM_TERM)

            # Estimate monthly cost (storage only, reads/writes depend on usage)
            storage_gb = estimated_size / (1024 * 1024 * 1024)
            monthly_cost = storage_gb * 0.108  # $0.108 per GB/month

            return CollectionStats(
                name=collection_name,
                document_count=doc_count,
                estimated_size_bytes=estimated_size,
                oldest_document_date=oldest_date,
                retention_policy=retention,
                estimated_monthly_cost=monthly_cost
            )

        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {e}")
            return CollectionStats(
                name=collection_name,
                document_count=0,
                estimated_size_bytes=0,
                oldest_document_date=None,
                retention_policy=RetentionPolicy.MEDIUM_TERM,
                estimated_monthly_cost=0.0
            )

    async def _estimate_collection_size(self, collection_name: str) -> int:
        """Estimate collection size for large collections"""
        # Use aggregation if available, otherwise estimate
        try:
            # Try getting a larger sample
            docs = await self.firestore.get_collection(collection_name, limit=5000)
            if len(docs) < 5000:
                return len(docs)
            # Estimate based on sample - this is rough
            return len(docs) * 2  # Assume 2x the sample
        except:
            return 5000  # Default estimate

    async def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all monitored collections"""
        # Check cache (refresh every 5 minutes)
        if self._cache_timestamp and (datetime.now(timezone.utc) - self._cache_timestamp).seconds < 300:
            return self._format_stats_response()

        stats = {}
        total_docs = 0
        total_size = 0
        total_cost = 0.0

        for collection_name in COLLECTION_RETENTION.keys():
            try:
                collection_stats = await self.get_collection_stats(collection_name)
                stats[collection_name] = collection_stats
                total_docs += collection_stats.document_count
                total_size += collection_stats.estimated_size_bytes
                total_cost += collection_stats.estimated_monthly_cost
            except Exception as e:
                logger.warning(f"Could not get stats for {collection_name}: {e}")

        self._stats_cache = stats
        self._cache_timestamp = datetime.now(timezone.utc)

        return {
            "timestamp": self._cache_timestamp.isoformat(),
            "summary": {
                "total_documents": total_docs,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "estimated_monthly_cost_usd": round(total_cost, 4),
                "collections_monitored": len(stats),
            },
            "collections": {
                name: {
                    "documents": s.document_count,
                    "size_mb": round(s.estimated_size_bytes / (1024 * 1024), 2),
                    "retention_policy": s.retention_policy.value,
                    "retention_days": RETENTION_DAYS.get(s.retention_policy),
                    "monthly_cost_usd": round(s.estimated_monthly_cost, 4),
                }
                for name, s in stats.items()
            },
            "cost_warnings": self._get_cost_warnings(stats, total_cost),
        }

    def _format_stats_response(self) -> Dict[str, Any]:
        """Format cached stats as response"""
        total_docs = sum(s.document_count for s in self._stats_cache.values())
        total_size = sum(s.estimated_size_bytes for s in self._stats_cache.values())
        total_cost = sum(s.estimated_monthly_cost for s in self._stats_cache.values())

        return {
            "timestamp": self._cache_timestamp.isoformat() if self._cache_timestamp else None,
            "cached": True,
            "summary": {
                "total_documents": total_docs,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "estimated_monthly_cost_usd": round(total_cost, 4),
                "collections_monitored": len(self._stats_cache),
            },
            "collections": {
                name: {
                    "documents": s.document_count,
                    "size_mb": round(s.estimated_size_bytes / (1024 * 1024), 2),
                    "retention_policy": s.retention_policy.value,
                    "retention_days": RETENTION_DAYS.get(s.retention_policy),
                    "monthly_cost_usd": round(s.estimated_monthly_cost, 4),
                }
                for name, s in self._stats_cache.items()
            },
            "cost_warnings": self._get_cost_warnings(self._stats_cache, total_cost),
        }

    def _get_cost_warnings(self, stats: Dict[str, CollectionStats], total_cost: float) -> List[str]:
        """Generate cost warnings"""
        warnings = []

        # Warn if total cost exceeds thresholds
        if total_cost > 10.0:
            warnings.append(f"⚠️ HIGH COST: Estimated ${total_cost:.2f}/month - consider pruning old data")
        elif total_cost > 5.0:
            warnings.append(f"📊 MODERATE COST: Estimated ${total_cost:.2f}/month - monitor growth")

        # Warn about large collections
        for name, s in stats.items():
            if s.document_count > 10000 and s.retention_policy != RetentionPolicy.CRITICAL:
                warnings.append(f"📈 {name}: {s.document_count:,} documents - eligible for pruning")

        return warnings

    async def prune_old_data(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Prune old data based on retention policies.

        Args:
            dry_run: If True, only report what would be deleted without actually deleting

        Returns:
            Summary of deletions (or would-be deletions)
        """
        results = {
            "dry_run": dry_run,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "collections_processed": {},
            "total_documents_deleted": 0,
            "errors": [],
        }

        for collection_name, retention in COLLECTION_RETENTION.items():
            retention_days = RETENTION_DAYS.get(retention)

            # Skip critical data
            if retention_days is None:
                results["collections_processed"][collection_name] = {
                    "status": "skipped",
                    "reason": "critical_data",
                }
                continue

            try:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
                deleted_count = await self._prune_collection(
                    collection_name, cutoff_date, dry_run
                )

                results["collections_processed"][collection_name] = {
                    "status": "success",
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                    "documents_deleted": deleted_count,
                }
                results["total_documents_deleted"] += deleted_count

            except Exception as e:
                logger.error(f"Error pruning {collection_name}: {e}")
                results["collections_processed"][collection_name] = {
                    "status": "error",
                    "error": str(e),
                }
                results["errors"].append(f"{collection_name}: {str(e)}")

        if not dry_run:
            logger.info(f"🗑️ Pruned {results['total_documents_deleted']} old documents")

        return results

    async def _prune_collection(
        self,
        collection_name: str,
        cutoff_date: datetime,
        dry_run: bool
    ) -> int:
        """Prune old documents from a collection"""
        deleted_count = 0

        try:
            # Get old documents (limit batch size to control costs)
            docs = await self.firestore.get_collection(
                collection_name,
                filters=[{
                    "field": "timestamp",
                    "operator": "<",
                    "value": cutoff_date.isoformat()
                }],
                limit=500  # Process in batches
            )

            # If timestamp field doesn't exist, try created_at
            if not docs:
                docs = await self.firestore.get_collection(
                    collection_name,
                    filters=[{
                        "field": "created_at",
                        "operator": "<",
                        "value": cutoff_date.isoformat()
                    }],
                    limit=500
                )

            for doc in docs:
                doc_id = doc.get("id")
                if doc_id and not dry_run:
                    await self.firestore.delete_document(collection_name, doc_id)
                deleted_count += 1

            return deleted_count

        except Exception as e:
            logger.warning(f"Could not prune {collection_name}: {e}")
            return 0


# Singleton instance
_cost_monitor: Optional[FirestoreCostMonitor] = None


def get_cost_monitor() -> FirestoreCostMonitor:
    """Get singleton cost monitor instance"""
    global _cost_monitor
    if _cost_monitor is None:
        _cost_monitor = FirestoreCostMonitor()
    return _cost_monitor
