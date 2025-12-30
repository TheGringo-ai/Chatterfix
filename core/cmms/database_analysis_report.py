#!/usr/bin/env python3
"""
ChatterFix CMMS - Database Schema Analysis & Migration Planning
Analyzing current SQLite schema for errors and PostgreSQL/Firestore migration readiness
"""

import sqlite3
import json
import os
from datetime import datetime

def analyze_current_schema():
    """Analyze current SQLite database schema for issues"""
    issues = []
    recommendations = []
    
    # Check if database exists
    db_path = "chatterfix_local.db"
    if not os.path.exists(db_path):
        issues.append("❌ Local SQLite database not found")
        return {"issues": issues, "recommendations": ["Create local database first"]}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
        
        schema_analysis = {
            "tables": {},
            "foreign_keys": [],
            "indexes": [],
            "issues": [],
            "recommendations": []
        }
        
        for table in tables:
            # Get table info
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fks = cursor.fetchall()
            
            # Check for common issues
            table_issues = []
            
            # Check for missing primary key
            has_primary_key = any(col[5] for col in columns)  # col[5] is pk flag
            if not has_primary_key:
                table_issues.append(f"Missing primary key in {table}")
            
            # Check for inconsistent ID types
            id_columns = [col for col in columns if col[1].startswith('id') or col[1].endswith('_id')]
            id_types = set(col[2] for col in id_columns)
            if len(id_types) > 1:
                table_issues.append(f"Inconsistent ID types in {table}: {id_types}")
            
            # Check for missing timestamps
            timestamp_cols = [col[1] for col in columns if 'timestamp' in col[1].lower() or 'created_at' in col[1].lower()]
            if not timestamp_cols and table not in ['sqlite_sequence']:
                table_issues.append(f"Missing timestamp columns in {table}")
            
            # Store table analysis
            schema_analysis["tables"][table] = {
                "columns": [{"name": col[1], "type": col[2], "nullable": not col[3], "primary_key": bool(col[5])} for col in columns],
                "foreign_keys": fks,
                "issues": table_issues
            }
            
            issues.extend(table_issues)
        
        # Check for orphaned records (basic check)
        for table in tables:
            if table == 'sqlite_sequence':
                continue
                
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"  📋 {table}: {count} records")
                
                # Check for NULL in important fields
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_name, col_type = col[1], col[2]
                    if col_name in ['id', 'name', 'title'] and not col[3]:  # NOT NULL columns
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} IS NULL;")
                        null_count = cursor.fetchone()[0]
                        if null_count > 0:
                            issues.append(f"❌ {table}.{col_name} has {null_count} NULL values")
                            
            except Exception as e:
                issues.append(f"❌ Error checking {table}: {str(e)}")
        
        conn.close()
        
        # Generate recommendations
        if "TEXT" in str(schema_analysis) and "INTEGER" in str(schema_analysis):
            recommendations.append("🔄 Consider standardizing ID types (TEXT vs INTEGER)")
        
        recommendations.extend([
            "🚀 Migrate to PostgreSQL for better performance and scalability",
            "🧠 Add vector columns for RAG memory system",
            "📊 Add proper indexing for frequently queried columns",
            "🔐 Implement proper database connection pooling",
            "📱 Add support for JSON columns for flexible metadata"
        ])
        
        return {
            "status": "analyzed",
            "timestamp": datetime.now().isoformat(),
            "tables_count": len(tables),
            "issues": issues,
            "recommendations": recommendations,
            "schema_details": schema_analysis
        }
        
    except Exception as e:
        issues.append(f"❌ Database analysis failed: {str(e)}")
        return {"issues": issues, "recommendations": ["Fix database connectivity first"]}

def plan_postgresql_migration():
    """Plan migration to PostgreSQL"""
    return {
        "migration_plan": {
            "phase1": "Create PostgreSQL schema with improved types",
            "phase2": "Add vector columns for RAG memory",
            "phase3": "Migrate existing data",
            "phase4": "Update application connections",
            "phase5": "Add advanced indexing and optimization"
        },
        "postgresql_benefits": [
            "Better performance for complex queries",
            "Native JSON support",
            "Vector extensions for AI/RAG",
            "Better concurrency handling",
            "Advanced indexing options",
            "Cloud-native (GCP Cloud SQL)"
        ],
        "estimated_downtime": "< 30 minutes with proper planning"
    }

def plan_rag_memory_system():
    """Plan RAG-style memory system implementation"""
    return {
        "rag_architecture": {
            "vector_storage": "PostgreSQL with pgvector extension",
            "embedding_model": "OpenAI text-embedding-3-small or Sentence Transformers",
            "retrieval_method": "Semantic similarity search",
            "memory_types": [
                "User conversation history",
                "Technical knowledge base",
                "Work order patterns",
                "Asset maintenance history",
                "Parts usage patterns"
            ]
        },
        "new_tables_needed": [
            "conversation_embeddings",
            "knowledge_base_vectors", 
            "memory_clusters",
            "retrieval_logs"
        ],
        "integration_points": [
            "AI Team Coordinator",
            "Grok Connector", 
            "Technical AI Assistant",
            "Work Order Assistant"
        ]
    }

if __name__ == "__main__":
    print("🔍 ChatterFix CMMS Database Analysis")
    print("=" * 50)
    
    # Analyze current schema
    analysis = analyze_current_schema()
    
    # Plan migrations
    pg_plan = plan_postgresql_migration()
    rag_plan = plan_rag_memory_system()
    
    # Compile full report
    report = {
        "database_analysis": analysis,
        "postgresql_migration": pg_plan,
        "rag_memory_system": rag_plan,
        "next_steps": [
            "1. Review and fix current schema issues",
            "2. Plan PostgreSQL migration timeline", 
            "3. Implement RAG memory system",
            "4. Test migration in development",
            "5. Execute production migration"
        ]
    }
    
    # Save report
    with open("database_migration_plan.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n📋 ANALYSIS SUMMARY")
    print("-" * 30)
    
    if analysis.get("issues"):
        print(f"❌ Issues found: {len(analysis['issues'])}")
        for issue in analysis["issues"][:5]:  # Show first 5
            print(f"   • {issue}")
        if len(analysis["issues"]) > 5:
            print(f"   ... and {len(analysis['issues']) - 5} more")
    else:
        print("✅ No major issues found")
    
    print(f"\n🔄 Recommendations: {len(analysis.get('recommendations', []))}")
    for rec in analysis.get("recommendations", [])[:3]:
        print(f"   • {rec}")
    
    print(f"\n📊 Report saved to: database_migration_plan.json")
    print(f"🎯 Ready for PostgreSQL migration planning")