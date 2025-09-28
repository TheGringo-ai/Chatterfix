#!/usr/bin/env python3
"""
ChatterFix CMMS - AI Development Collaboration System
Enterprise-grade AI collaboration framework for seamless multi-AI development

Solves persistent problems:
1. Context Loss between AI models
2. Deployment Issues and failures  
3. Knowledge Gaps across AI models
4. Handoff Problems between AI sessions
5. Resource Limitations and persistence

Features:
- Persistent Memory & Context System
- AI Collaboration Framework
- Development Safeguards
- ChatterFix-Specific Knowledge Base
- Resource Management
- Workflow Management
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AIModel(Enum):
    CLAUDE = "claude"
    CHATGPT = "chatgpt"
    GROK = "grok"
    LLAMA = "llama"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AISession:
    session_id: str
    ai_model: AIModel
    start_time: datetime
    end_time: Optional[datetime]
    context_data: Dict[str, Any]
    tasks_completed: List[str]
    knowledge_gained: List[str]
    issues_encountered: List[str]
    handoff_notes: str
    status: str

@dataclass
class ProjectContext:
    context_id: str
    timestamp: datetime
    system_state: Dict[str, Any]
    active_features: List[str]
    known_issues: List[str]
    recent_changes: List[str]
    deployment_status: str
    test_results: Dict[str, Any]
    technical_debt: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with JSON-serializable datetime"""
        return {
            "context_id": self.context_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "system_state": self.system_state,
            "active_features": self.active_features,
            "known_issues": self.known_issues,
            "recent_changes": self.recent_changes,
            "deployment_status": self.deployment_status,
            "test_results": self.test_results,
            "technical_debt": self.technical_debt
        }

@dataclass
class CollaborationTask:
    task_id: str
    title: str
    description: str
    assigned_ai: AIModel
    status: TaskStatus
    priority: Priority
    created_by: AIModel
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    dependencies: List[str]
    context_requirements: List[str]
    completion_criteria: List[str]
    estimated_effort: int  # hours
    actual_effort: Optional[int]
    notes: List[str]
    artifacts: List[str]  # file paths, URLs, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with JSON-serializable datetime and enum values"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "assigned_ai": self.assigned_ai.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_by": self.created_by.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "dependencies": self.dependencies,
            "context_requirements": self.context_requirements,
            "completion_criteria": self.completion_criteria,
            "estimated_effort": self.estimated_effort,
            "actual_effort": self.actual_effort,
            "notes": self.notes,
            "artifacts": self.artifacts
        }

class AICollaborationDatabase:
    """
    Persistent database for AI collaboration system
    Stores all AI interactions, context, and project state
    """
    
    def __init__(self, db_path: str = "ai_collaboration.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize collaboration database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # AI Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_sessions (
                session_id TEXT PRIMARY KEY,
                ai_model TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                context_data TEXT,
                tasks_completed TEXT,
                knowledge_gained TEXT,
                issues_encountered TEXT,
                handoff_notes TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Project Context table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_context (
                context_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                system_state TEXT,
                active_features TEXT,
                known_issues TEXT,
                recent_changes TEXT,
                deployment_status TEXT,
                test_results TEXT,
                technical_debt TEXT
            )
        ''')
        
        # Collaboration Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collaboration_tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                assigned_ai TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                due_date TIMESTAMP,
                dependencies TEXT,
                context_requirements TEXT,
                completion_criteria TEXT,
                estimated_effort INTEGER,
                actual_effort INTEGER,
                notes TEXT,
                artifacts TEXT
            )
        ''')
        
        # AI Knowledge Base table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_knowledge_base (
                knowledge_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                source_ai TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                confidence_score REAL DEFAULT 0.8,
                validation_status TEXT DEFAULT 'pending',
                tags TEXT
            )
        ''')
        
        # Development Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS development_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                ai_model TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                description TEXT,
                impact_level TEXT,
                affected_components TEXT,
                resolution_notes TEXT,
                metadata TEXT
            )
        ''')
        
        # Code Changes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_changes (
                change_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                change_type TEXT NOT NULL,
                ai_model TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                description TEXT,
                old_content TEXT,
                new_content TEXT,
                reasoning TEXT,
                test_status TEXT,
                rollback_data TEXT
            )
        ''')
        
        # Deployment History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployment_history (
                deployment_id TEXT PRIMARY KEY,
                environment TEXT NOT NULL,
                ai_model TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                version TEXT,
                status TEXT NOT NULL,
                logs TEXT,
                rollback_available BOOLEAN DEFAULT TRUE,
                performance_metrics TEXT
            )
        ''')
        
        # AI Handoffs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_handoffs (
                handoff_id TEXT PRIMARY KEY,
                from_ai TEXT NOT NULL,
                to_ai TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                context_snapshot TEXT,
                active_tasks TEXT,
                pending_issues TEXT,
                recommendations TEXT,
                urgency_level TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_ai_model ON ai_sessions (ai_model)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON ai_sessions (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_context_timestamp ON project_context (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_assigned_ai ON collaboration_tasks (assigned_ai)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON collaboration_tasks (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON collaboration_tasks (priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_category ON ai_knowledge_base (category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_ai_model ON development_events (ai_model)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_file_path ON code_changes (file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deployments_environment ON deployment_history (environment)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_handoffs_to_ai ON ai_handoffs (to_ai)')
        
        conn.commit()
        conn.close()
        logger.info("🗄️ AI Collaboration database initialized successfully")
    
    def save_ai_session(self, session: AISession):
        """Save AI session to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO ai_sessions 
            (session_id, ai_model, start_time, end_time, context_data, tasks_completed, 
             knowledge_gained, issues_encountered, handoff_notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.session_id,
            session.ai_model.value,
            session.start_time.isoformat(),
            session.end_time.isoformat() if session.end_time else None,
            json.dumps(session.context_data),
            json.dumps(session.tasks_completed),
            json.dumps(session.knowledge_gained),
            json.dumps(session.issues_encountered),
            session.handoff_notes,
            session.status
        ))
        
        conn.commit()
        conn.close()
    
    def save_project_context(self, context: ProjectContext):
        """Save project context snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO project_context 
            (context_id, timestamp, system_state, active_features, known_issues,
             recent_changes, deployment_status, test_results, technical_debt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            context.context_id,
            context.timestamp.isoformat(),
            json.dumps(context.system_state),
            json.dumps(context.active_features),
            json.dumps(context.known_issues),
            json.dumps(context.recent_changes),
            context.deployment_status,
            json.dumps(context.test_results),
            json.dumps(context.technical_debt)
        ))
        
        conn.commit()
        conn.close()
    
    def save_collaboration_task(self, task: CollaborationTask):
        """Save collaboration task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO collaboration_tasks 
            (task_id, title, description, assigned_ai, status, priority, created_by,
             created_at, updated_at, due_date, dependencies, context_requirements,
             completion_criteria, estimated_effort, actual_effort, notes, artifacts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.task_id,
            task.title,
            task.description,
            task.assigned_ai.value,
            task.status.value,
            task.priority.value,
            task.created_by.value,
            task.created_at.isoformat(),
            task.updated_at.isoformat(),
            task.due_date.isoformat() if task.due_date else None,
            json.dumps(task.dependencies),
            json.dumps(task.context_requirements),
            json.dumps(task.completion_criteria),
            task.estimated_effort,
            task.actual_effort,
            json.dumps(task.notes),
            json.dumps(task.artifacts)
        ))
        
        conn.commit()
        conn.close()
    
    def get_latest_context(self) -> Optional[ProjectContext]:
        """Get the most recent project context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM project_context 
            ORDER BY timestamp DESC LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ProjectContext(
                context_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                system_state=json.loads(row[2]),
                active_features=json.loads(row[3]),
                known_issues=json.loads(row[4]),
                recent_changes=json.loads(row[5]),
                deployment_status=row[6],
                test_results=json.loads(row[7]),
                technical_debt=json.loads(row[8])
            )
        return None
    
    def get_active_tasks_for_ai(self, ai_model: AIModel) -> List[CollaborationTask]:
        """Get active tasks assigned to specific AI model"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM collaboration_tasks 
            WHERE assigned_ai = ? AND status IN ('pending', 'in_progress')
            ORDER BY priority DESC, created_at ASC
        ''', (ai_model.value,))
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            task = CollaborationTask(
                task_id=row[0],
                title=row[1],
                description=row[2],
                assigned_ai=AIModel(row[3]),
                status=TaskStatus(row[4]),
                priority=Priority(row[5]),
                created_by=AIModel(row[6]),
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8]),
                due_date=datetime.fromisoformat(row[9]) if row[9] else None,
                dependencies=json.loads(row[10]),
                context_requirements=json.loads(row[11]),
                completion_criteria=json.loads(row[12]),
                estimated_effort=row[13],
                actual_effort=row[14],
                notes=json.loads(row[15]),
                artifacts=json.loads(row[16])
            )
            tasks.append(task)
        
        return tasks

class ContextManager:
    """
    Manages project context and automatic context saving/loading
    """
    
    def __init__(self, database: AICollaborationDatabase):
        self.database = database
        self.current_context: Optional[ProjectContext] = None
        self.auto_save_interval = 300  # 5 minutes
        self.last_save_time = time.time()
    
    async def capture_current_context(self) -> ProjectContext:
        """Capture comprehensive current project state"""
        context_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        # Analyze current ChatterFix system state
        system_state = await self._analyze_system_state()
        active_features = await self._get_active_features()
        known_issues = await self._scan_known_issues()
        recent_changes = await self._get_recent_changes()
        deployment_status = await self._check_deployment_status()
        test_results = await self._run_health_checks()
        technical_debt = await self._analyze_technical_debt()
        
        context = ProjectContext(
            context_id=context_id,
            timestamp=timestamp,
            system_state=system_state,
            active_features=active_features,
            known_issues=known_issues,
            recent_changes=recent_changes,
            deployment_status=deployment_status,
            test_results=test_results,
            technical_debt=technical_debt
        )
        
        self.current_context = context
        self.database.save_project_context(context)
        
        return context
    
    async def _analyze_system_state(self) -> Dict[str, Any]:
        """Analyze current ChatterFix system state"""
        try:
            # Check if app.py is running
            app_running = await self._check_process_running("python3 app.py")
            
            # Check database connectivity
            db_accessible = await self._check_database_connectivity()
            
            # Check static files
            static_files_present = await self._check_static_files()
            
            # Check API endpoints
            api_health = await self._check_api_health()
            
            return {
                "app_running": app_running,
                "database_accessible": db_accessible,
                "static_files_present": static_files_present,
                "api_health": api_health,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing system state: {e}")
            return {"error": str(e), "status": "unknown"}
    
    async def _get_active_features(self) -> List[str]:
        """Get list of currently active features"""
        features = [
            "FastAPI Backend",
            "SQLite Database",
            "Work Order Management",
            "Asset Management", 
            "Parts Inventory",
            "AI Assistant Integration",
            "Voice Commands",
            "Demo/Production Data Toggle",
            "Enterprise Mock Data",
            "Dynamic Card System",
            "Modal-based Detail Views",
            "Real-time DOM Monitoring",
            "AI-powered Recommendations"
        ]
        
        # Could enhance this to dynamically detect active features
        # by checking module imports, database tables, etc.
        
        return features
    
    async def _scan_known_issues(self) -> List[str]:
        """Scan for known issues based on recent problem patterns"""
        known_issues = []
        
        # Check for common ChatterFix issues based on your description
        try:
            # Check for ID mismatch issues
            if await self._check_static_id_issues():
                known_issues.append("Static card IDs (1-5) vs dynamic database IDs mismatch")
            
            # Check for missing click handlers
            if await self._check_click_handler_issues():
                known_issues.append("Click handlers not working due to static/dynamic ID conflicts")
            
            # Check for missing modal functions
            if await self._check_modal_function_issues():
                known_issues.append("Missing modal creation functions")
            
            # Check for database routing issues
            if await self._check_database_routing_issues():
                known_issues.append("Database routing problems between demo/production modes")
                
        except Exception as e:
            known_issues.append(f"Error scanning for issues: {e}")
        
        return known_issues
    
    async def _get_recent_changes(self) -> List[str]:
        """Get recent code/system changes"""
        changes = []
        
        try:
            # Check git log for recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "10"],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                changes.extend([f"Git commit: {commit}" for commit in commits])
        except Exception as e:
            changes.append(f"Error getting git changes: {e}")
        
        return changes
    
    async def _check_deployment_status(self) -> str:
        """Check current deployment status"""
        # Check if deployment scripts exist and recent deployment logs
        try:
            deploy_script = Path("./deploy-chatterfix.sh")
            if deploy_script.exists():
                # Check for recent deployment activity
                return "Deployment ready - script available"
            else:
                return "No deployment script found"
        except Exception as e:
            return f"Error checking deployment: {e}"
    
    async def _run_health_checks(self) -> Dict[str, Any]:
        """Run system health checks"""
        health = {}
        
        try:
            # Check if main files exist
            essential_files = [
                "./app.py",
                "./enhanced_database_schema.py",
                "./static/js/cmms-functions.js"
            ]
            
            for file_path in essential_files:
                health[f"file_exists_{Path(file_path).name}"] = Path(file_path).exists()
            
            # Could add more health checks like:
            # - API endpoint tests
            # - Database query tests  
            # - Static file serving tests
            
        except Exception as e:
            health["error"] = str(e)
        
        return health
    
    async def _analyze_technical_debt(self) -> List[str]:
        """Analyze technical debt in the system"""
        debt = []
        
        # Based on your requirements, identify common technical debt
        debt.extend([
            "Need standardized AI handoff procedures",
            "Context loss between AI model switches",
            "Incomplete automated testing coverage", 
            "Manual deployment process needs automation",
            "Inconsistent error handling across modules",
            "Need comprehensive rollback mechanisms"
        ])
        
        return debt
    
    async def _check_process_running(self, process_name: str) -> bool:
        """Check if a process is currently running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def _check_database_connectivity(self) -> bool:
        """Check if database is accessible"""
        try:
            db_path = "./data/cmms_enhanced.db"
            if Path(db_path).exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                return True
            return False
        except Exception:
            return False
    
    async def _check_static_files(self) -> bool:
        """Check if static files are present"""
        static_dir = Path("./static")
        return static_dir.exists() and len(list(static_dir.rglob("*"))) > 0
    
    async def _check_api_health(self) -> str:
        """Check API health status"""
        # Could implement actual HTTP health check
        return "Not implemented - would check HTTP endpoints"
    
    async def _check_static_id_issues(self) -> bool:
        """Check for static ID vs dynamic ID issues"""
        # This would analyze the JS files for hardcoded IDs 1-5
        return False  # Placeholder
    
    async def _check_click_handler_issues(self) -> bool:
        """Check for click handler issues"""
        return False  # Placeholder
    
    async def _check_modal_function_issues(self) -> bool:
        """Check for missing modal functions"""
        return False  # Placeholder
    
    async def _check_database_routing_issues(self) -> bool:
        """Check for database routing issues"""
        return False  # Placeholder
    
    async def auto_save_context(self):
        """Automatically save context if enough time has passed"""
        current_time = time.time()
        if current_time - self.last_save_time >= self.auto_save_interval:
            await self.capture_current_context()
            self.last_save_time = current_time

class AIHandoffManager:
    """
    Manages seamless handoffs between AI models
    """
    
    def __init__(self, database: AICollaborationDatabase, context_manager: ContextManager):
        self.database = database
        self.context_manager = context_manager
    
    async def initiate_handoff(
        self, 
        from_ai: AIModel, 
        to_ai: AIModel, 
        urgency: str = "normal",
        context_notes: str = ""
    ) -> str:
        """Initiate handoff between AI models"""
        handoff_id = str(uuid.uuid4())
        
        # Capture current context
        current_context = await self.context_manager.capture_current_context()
        
        # Get active tasks for the current AI
        active_tasks = self.database.get_active_tasks_for_ai(from_ai)
        
        # Analyze pending issues
        pending_issues = await self._analyze_pending_issues()
        
        # Generate recommendations for the receiving AI
        recommendations = await self._generate_handoff_recommendations(
            from_ai, to_ai, active_tasks, current_context
        )
        
        # Save handoff record
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_handoffs 
            (handoff_id, from_ai, to_ai, timestamp, context_snapshot, 
             active_tasks, pending_issues, recommendations, urgency_level, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            handoff_id,
            from_ai.value,
            to_ai.value,
            datetime.now(timezone.utc).isoformat(),
            json.dumps(asdict(current_context)),
            json.dumps([asdict(task) for task in active_tasks]),
            json.dumps(pending_issues),
            json.dumps(recommendations),
            urgency,
            "pending"
        ))
        
        conn.commit()
        conn.close()
        
        return handoff_id
    
    async def receive_handoff(self, handoff_id: str, receiving_ai: AIModel) -> Dict[str, Any]:
        """Process incoming handoff for an AI model"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ai_handoffs WHERE handoff_id = ?
        ''', (handoff_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return {"error": "Handoff not found"}
        
        # Update handoff status
        cursor.execute('''
            UPDATE ai_handoffs SET status = 'completed' WHERE handoff_id = ?
        ''', (handoff_id,))
        
        conn.commit()
        conn.close()
        
        # Parse handoff data
        handoff_data = {
            "handoff_id": row[0],
            "from_ai": row[1],
            "to_ai": row[2],
            "timestamp": row[3],
            "context_snapshot": json.loads(row[4]),
            "active_tasks": json.loads(row[5]),
            "pending_issues": json.loads(row[6]),
            "recommendations": json.loads(row[7]),
            "urgency_level": row[8]
        }
        
        return handoff_data
    
    async def _analyze_pending_issues(self) -> List[str]:
        """Analyze current pending issues"""
        # Get recent development events that might be issues
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT description FROM development_events 
            WHERE event_type = 'issue' AND timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    async def _generate_handoff_recommendations(
        self, 
        from_ai: AIModel, 
        to_ai: AIModel, 
        active_tasks: List[CollaborationTask],
        context: ProjectContext
    ) -> List[str]:
        """Generate intelligent recommendations for handoff"""
        recommendations = []
        
        # AI-specific recommendations based on roles
        if to_ai == AIModel.CLAUDE:
            recommendations.extend([
                "Focus on architecture and system design",
                "Review technical debt items",
                "Ensure code quality and documentation"
            ])
        elif to_ai == AIModel.CHATGPT:
            recommendations.extend([
                "Prioritize frontend development tasks",
                "Focus on user experience improvements",
                "Handle UI/UX related issues"
            ])
        elif to_ai == AIModel.GROK:
            recommendations.extend([
                "Debug any failing tests or errors",
                "Investigate performance issues",
                "Handle system troubleshooting"
            ])
        elif to_ai == AIModel.LLAMA:
            recommendations.extend([
                "Focus on data processing and analytics",
                "Handle database optimizations",
                "Work on AI/ML feature improvements"
            ])
        
        # Task-specific recommendations
        if active_tasks:
            high_priority_tasks = [t for t in active_tasks if t.priority == Priority.HIGH]
            if high_priority_tasks:
                recommendations.append(f"Priority: Complete {len(high_priority_tasks)} high-priority tasks")
        
        # Context-specific recommendations
        if context.known_issues:
            recommendations.append(f"Address {len(context.known_issues)} known issues")
        
        return recommendations

class DeploymentSafetySystem:
    """
    Automated testing and rollback system for safe deployments
    """
    
    def __init__(self, database: AICollaborationDatabase):
        self.database = database
        self.backup_dir = Path("./backups")
        self.backup_dir.mkdir(exist_ok=True, parents=True)
    
    async def create_backup(self, description: str = "") -> str:
        """Create full system backup before changes"""
        backup_id = f"backup_{int(time.time())}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        try:
            # Backup source code
            source_backup = backup_path / "source"
            subprocess.run([
                "cp", "-r", 
                ".",
                str(source_backup)
            ], check=True)
            
            # Backup database
            db_backup = backup_path / "database"
            db_backup.mkdir(exist_ok=True)
            subprocess.run([
                "cp", 
                "./data/cmms_enhanced.db",
                str(db_backup / "cmms_enhanced.db")
            ], check=True)
            
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "description": description,
                "files_backed_up": [
                    "source code",
                    "database",
                    "static files"
                ]
            }
            
            with open(backup_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"✅ Backup created: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            raise
    
    async def run_pre_deployment_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests before deployment"""
        test_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "unknown",
            "tests": {}
        }
        
        try:
            # Test 1: Syntax check
            test_results["tests"]["syntax_check"] = await self._test_syntax()
            
            # Test 2: Import check
            test_results["tests"]["import_check"] = await self._test_imports()
            
            # Test 3: Database connectivity
            test_results["tests"]["database_check"] = await self._test_database()
            
            # Test 4: Static files check
            test_results["tests"]["static_files_check"] = await self._test_static_files()
            
            # Test 5: API endpoints check
            test_results["tests"]["api_check"] = await self._test_api_endpoints()
            
            # Determine overall status
            all_passed = all(
                test["status"] == "passed" 
                for test in test_results["tests"].values()
            )
            test_results["overall_status"] = "passed" if all_passed else "failed"
            
        except Exception as e:
            test_results["overall_status"] = "error"
            test_results["error"] = str(e)
        
        return test_results
    
    async def _test_syntax(self) -> Dict[str, Any]:
        """Test Python syntax of all files"""
        try:
            result = subprocess.run([
                "python3", "-m", "py_compile", 
                "./app.py"
            ], capture_output=True, text=True)
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _test_imports(self) -> Dict[str, Any]:
        """Test that all imports work"""
        try:
            result = subprocess.run([
                "python3", "-c", 
                "import sys; sys.path.append('.'); import app"
            ], capture_output=True, text=True)
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _test_database(self) -> Dict[str, Any]:
        """Test database connectivity and basic operations"""
        try:
            db_path = "./data/cmms_enhanced.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM work_orders")
            count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "status": "passed",
                "work_orders_count": count,
                "message": "Database connection successful"
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _test_static_files(self) -> Dict[str, Any]:
        """Test that static files are accessible"""
        try:
            static_dir = Path("./static")
            if not static_dir.exists():
                return {"status": "failed", "error": "Static directory not found"}
            
            css_files = list(static_dir.glob("**/*.css"))
            js_files = list(static_dir.glob("**/*.js"))
            
            return {
                "status": "passed",
                "css_files_count": len(css_files),
                "js_files_count": len(js_files),
                "message": "Static files accessible"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _test_api_endpoints(self) -> Dict[str, Any]:
        """Test critical API endpoints"""
        # This would require running the app and making HTTP requests
        # For now, return a placeholder
        return {
            "status": "skipped",
            "message": "API endpoint testing requires running server"
        }
    
    async def rollback_deployment(self, backup_id: str) -> bool:
        """Rollback to a previous backup"""
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            logger.error(f"❌ Backup {backup_id} not found")
            return False
        
        try:
            # Restore source code
            source_backup = backup_path / "source"
            if source_backup.exists():
                subprocess.run([
                    "rm", "-rf", 
                    "."
                ], check=True)
                
                subprocess.run([
                    "cp", "-r",
                    str(source_backup),
                    "."
                ], check=True)
            
            # Restore database
            db_backup = backup_path / "database" / "cmms_enhanced.db"
            if db_backup.exists():
                subprocess.run([
                    "cp",
                    str(db_backup),
                    "./data/cmms_enhanced.db"
                ], check=True)
            
            logger.info(f"✅ Rollback completed: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False

class WorkflowManager:
    """
    Manages AI collaboration workflows and task assignments
    """
    
    def __init__(self, database: AICollaborationDatabase):
        self.database = database
        self.ai_roles = {
            AIModel.CLAUDE: "Architecture & Code Quality",
            AIModel.CHATGPT: "Frontend & User Experience", 
            AIModel.GROK: "Debugging & Performance",
            AIModel.LLAMA: "Data & Analytics"
        }
    
    async def assign_task(
        self, 
        title: str,
        description: str,
        assigned_ai: AIModel,
        priority: Priority,
        created_by: AIModel,
        estimated_effort: int = 1,
        due_date: Optional[datetime] = None,
        dependencies: List[str] = None,
        context_requirements: List[str] = None,
        completion_criteria: List[str] = None
    ) -> str:
        """Assign a new task to an AI model"""
        task_id = str(uuid.uuid4())
        
        task = CollaborationTask(
            task_id=task_id,
            title=title,
            description=description,
            assigned_ai=assigned_ai,
            status=TaskStatus.PENDING,
            priority=priority,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            due_date=due_date,
            dependencies=dependencies or [],
            context_requirements=context_requirements or [],
            completion_criteria=completion_criteria or [],
            estimated_effort=estimated_effort,
            actual_effort=None,
            notes=[],
            artifacts=[]
        )
        
        self.database.save_collaboration_task(task)
        
        # Log task assignment event
        await self._log_development_event(
            "task_assigned",
            created_by,
            f"Task '{title}' assigned to {assigned_ai.value}",
            "normal",
            [task_id]
        )
        
        return task_id
    
    async def update_task_status(
        self, 
        task_id: str, 
        new_status: TaskStatus,
        ai_model: AIModel,
        notes: str = "",
        actual_effort: Optional[int] = None,
        artifacts: List[str] = None
    ):
        """Update task status and progress"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        # Get current task
        cursor.execute('SELECT * FROM collaboration_tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Task {task_id} not found")
        
        # Update task
        current_notes = json.loads(row[15])
        current_artifacts = json.loads(row[16])
        
        if notes:
            current_notes.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ai_model": ai_model.value,
                "note": notes
            })
        
        if artifacts:
            current_artifacts.extend(artifacts)
        
        cursor.execute('''
            UPDATE collaboration_tasks 
            SET status = ?, updated_at = ?, actual_effort = ?, notes = ?, artifacts = ?
            WHERE task_id = ?
        ''', (
            new_status.value,
            datetime.now(timezone.utc).isoformat(),
            actual_effort or row[14],
            json.dumps(current_notes),
            json.dumps(current_artifacts),
            task_id
        ))
        
        conn.commit()
        conn.close()
        
        # Log status change event
        await self._log_development_event(
            "task_status_changed",
            ai_model,
            f"Task {task_id} status changed to {new_status.value}",
            "normal",
            [task_id]
        )
    
    async def get_task_recommendations(self, ai_model: AIModel) -> List[Dict[str, Any]]:
        """Get intelligent task recommendations for an AI model"""
        # Get AI's role and current tasks
        role = self.ai_roles.get(ai_model, "General")
        current_tasks = self.database.get_active_tasks_for_ai(ai_model)
        
        recommendations = []
        
        # Analyze workload
        high_priority_tasks = [t for t in current_tasks if t.priority == Priority.HIGH]
        overdue_tasks = [
            t for t in current_tasks 
            if t.due_date and t.due_date < datetime.now(timezone.utc)
        ]
        
        if high_priority_tasks:
            recommendations.append({
                "type": "priority_focus",
                "message": f"Focus on {len(high_priority_tasks)} high-priority tasks",
                "tasks": [t.task_id for t in high_priority_tasks]
            })
        
        if overdue_tasks:
            recommendations.append({
                "type": "overdue_alert",
                "message": f"Address {len(overdue_tasks)} overdue tasks",
                "tasks": [t.task_id for t in overdue_tasks]
            })
        
        # Role-specific recommendations
        if ai_model == AIModel.CLAUDE:
            recommendations.append({
                "type": "role_suggestion",
                "message": "Consider reviewing system architecture and code quality",
                "action": "architecture_review"
            })
        elif ai_model == AIModel.GROK:
            recommendations.append({
                "type": "role_suggestion", 
                "message": "Check for any system issues or debugging needs",
                "action": "system_health_check"
            })
        
        return recommendations
    
    async def _log_development_event(
        self,
        event_type: str,
        ai_model: AIModel,
        description: str,
        impact_level: str,
        affected_components: List[str]
    ):
        """Log development event for tracking"""
        event_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO development_events 
            (event_id, event_type, ai_model, timestamp, description, 
             impact_level, affected_components, resolution_notes, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_id,
            event_type,
            ai_model.value,
            datetime.now(timezone.utc).isoformat(),
            description,
            impact_level,
            json.dumps(affected_components),
            "",
            "{}"
        ))
        
        conn.commit()
        conn.close()

class ChatterFixKnowledgeBase:
    """
    Comprehensive ChatterFix-specific knowledge base
    """
    
    def __init__(self, database: AICollaborationDatabase):
        self.database = database
        self.knowledge_file = Path("./chatterfix_knowledge_base.json")
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize comprehensive ChatterFix knowledge base"""
        knowledge_base = {
            "system_architecture": {
                "overview": "ChatterFix CMMS is an AI-powered maintenance management system",
                "technology_stack": {
                    "backend": "FastAPI with Python 3",
                    "database": "SQLite with enhanced schema",
                    "frontend": "HTML/CSS/JavaScript with dynamic components",
                    "deployment": "Google Cloud Run",
                    "ai_integration": "Multiple AI models (Claude, ChatGPT, Grok, Llama)"
                },
                "key_components": [
                    "Work Order Management System",
                    "Asset Management with Health Scoring",
                    "Parts Inventory with Reorder Management",
                    "Preventive Maintenance Scheduling",
                    "AI Assistant with Voice Commands",
                    "Demo/Production Data Toggle System",
                    "Enterprise Mock Data Generator",
                    "Dynamic Card System with proper ID handling"
                ]
            },
            "current_system_state": {
                "deployment_ready": True,
                "main_application": "app.py (FastAPI backend)",
                "database_schema": "enhanced_database_schema.py",
                "frontend_architecture": "Dynamic cards with modal detail views",
                "ai_integration": "Universal AI loader with voice commands",
                "data_modes": "Demo and Production with toggle system",
                "known_features": [
                    "Dynamic card creation with proper ID extraction",
                    "Modal-based detail views for work orders",
                    "Real-time DOM monitoring with MutationObserver",
                    "AI-powered recommendations and insights",
                    "Enterprise-grade mock data for demonstrations",
                    "TechFlow Manufacturing sample company data"
                ]
            },
            "recent_issues_solved": {
                "id_mismatch_problem": {
                    "issue": "Static card IDs (1-5) conflicting with dynamic database IDs",
                    "solution": "Implemented proper ID extraction from database records",
                    "impact": "Click handlers now work correctly with dynamic data"
                },
                "click_handlers_not_working": {
                    "issue": "Click handlers failing due to static/dynamic ID conflicts",
                    "solution": "Updated event delegation and ID extraction logic",
                    "impact": "All interactive elements now function properly"
                },
                "missing_modal_functions": {
                    "issue": "Modal creation functions were not defined",
                    "solution": "Added comprehensive modal creation and management",
                    "impact": "Detail views now display correctly"
                },
                "database_routing_issues": {
                    "issue": "Routing problems between demo and production data modes",
                    "solution": "Implemented proper data toggle system with admin controls",
                    "impact": "Seamless switching between demo and production environments"
                }
            },
            "architecture_patterns": {
                "dynamic_card_creation": {
                    "pattern": "Generate cards from database records with proper ID extraction",
                    "implementation": "JavaScript functions extract database IDs for event handling",
                    "benefits": "Eliminates static/dynamic ID conflicts"
                },
                "modal_based_detail_views": {
                    "pattern": "Use modals for detailed work order, asset, and parts views",
                    "implementation": "Dynamic modal creation with proper content loading",
                    "benefits": "Clean UI without page refreshes"
                },
                "real_time_dom_monitoring": {
                    "pattern": "MutationObserver for dynamic content changes",
                    "implementation": "Monitors DOM for new elements and attaches handlers",
                    "benefits": "Handles dynamically added content automatically"
                },
                "ai_powered_recommendations": {
                    "pattern": "Integrated AI assistant across all pages",
                    "implementation": "Universal AI loader with context awareness",
                    "benefits": "Intelligent assistance throughout the application"
                }
            },
            "api_endpoints": {
                "work_orders": {
                    "/cmms/workorders/dashboard": "Work orders dashboard with filters",
                    "/cmms/workorders/create": "Create new work order form",
                    "/cmms/workorders/{id}/view": "View work order details",
                    "/cmms/workorders/{id}/edit": "Edit work order",
                    "/api/workorders": "REST API for work orders",
                    "/api/workorders/{id}": "Individual work order operations"
                },
                "assets": {
                    "/cmms/assets/dashboard": "Assets overview with health scores",
                    "/cmms/assets/create": "Add new asset",
                    "/cmms/assets/{id}/view": "Asset details and maintenance history",
                    "/api/assets": "REST API for assets",
                    "/api/assets/{id}/health": "Asset health scoring"
                },
                "parts": {
                    "/cmms/parts/dashboard": "Parts inventory overview",
                    "/cmms/parts/inventory": "Detailed inventory management",
                    "/api/parts": "REST API for parts",
                    "/api/parts/reorder-alerts": "Low stock alerts"
                },
                "ai_integration": {
                    "/api/ai/chat": "AI assistant chat endpoint",
                    "/api/ai/voice": "Voice command processing",
                    "/api/ai/recommendations": "AI-powered recommendations"
                }
            },
            "database_schema": {
                "core_tables": [
                    "users - User management and roles",
                    "assets - Equipment and machinery records",
                    "work_orders - Maintenance task tracking",
                    "parts - Inventory management",
                    "pm_schedules - Preventive maintenance scheduling",
                    "time_tracking - Work time logging",
                    "work_order_parts - Parts usage tracking",
                    "parts_transactions - Inventory movement history",
                    "work_order_updates - Comments and status changes"
                ],
                "relationships": "Foreign key relationships between work orders, assets, parts, and users",
                "indexes": "Performance indexes on frequently queried columns"
            },
            "deployment_configuration": {
                "cloud_platform": "Google Cloud Run",
                "containerization": "Docker container deployment",
                "environment_variables": [
                    "JWT_SECRET_KEY - Authentication secret",
                    "DATABASE_URL - Database connection string",
                    "AI_API_KEYS - AI service authentication"
                ],
                "deployment_script": "deploy-chatterfix.sh for automated deployment",
                "health_checks": "Built-in health monitoring endpoints"
            },
            "ai_integration_details": {
                "universal_ai_loader": {
                    "purpose": "Load AI assistant on every page",
                    "implementation": "JavaScript module for consistent AI integration",
                    "features": ["Voice commands", "Natural language processing", "Context awareness"]
                },
                "voice_commands": {
                    "supported_commands": [
                        "Create work order for [equipment]",
                        "Show asset health for [asset name]",
                        "Check parts inventory for [part]",
                        "Schedule maintenance for [equipment]",
                        "What's the status of work order [number]"
                    ],
                    "processing": "Speech-to-text with natural language understanding"
                },
                "ai_recommendations": {
                    "types": [
                        "Predictive maintenance suggestions",
                        "Parts reorder recommendations",
                        "Work order prioritization",
                        "Asset health insights"
                    ],
                    "integration": "Real-time recommendations throughout the interface"
                }
            },
            "testing_and_quality": {
                "test_structure": {
                    "unit_tests": "tests/unit/ directory with API endpoint tests",
                    "performance_tests": "tests/performance/ with Locust load testing",
                    "integration_tests": "Comprehensive system integration testing"
                },
                "quality_assurance": [
                    "Automated syntax checking",
                    "Import validation",
                    "Database connectivity tests",
                    "Static file validation",
                    "API endpoint health checks"
                ]
            },
            "common_workflows": {
                "create_work_order": [
                    "Navigate to /cmms/workorders/dashboard",
                    "Click 'Create Work Order' button",
                    "Select asset from dropdown",
                    "Set priority (Low/Medium/High/Critical)",
                    "Describe the maintenance issue",
                    "Assign to technician",
                    "Set due date and estimated hours",
                    "Submit and track progress"
                ],
                "manage_assets": [
                    "Access /cmms/assets/dashboard",
                    "View asset health scores",
                    "Check maintenance history",
                    "Schedule preventive maintenance",
                    "Update asset information",
                    "Monitor predictive analytics"
                ],
                "inventory_management": [
                    "Check /cmms/parts/dashboard",
                    "Review stock levels",
                    "Set reorder points",
                    "Process reorder alerts",
                    "Update part information",
                    "Track usage patterns"
                ]
            },
            "troubleshooting_guide": {
                "common_issues": {
                    "work_orders_not_loading": [
                        "Check database connectivity",
                        "Verify work order API endpoints",
                        "Check for JavaScript errors in console",
                        "Validate user permissions"
                    ],
                    "ai_assistant_not_responding": [
                        "Verify AI API keys are configured",
                        "Check network connectivity",
                        "Test microphone permissions for voice",
                        "Check browser compatibility"
                    ],
                    "modal_views_not_opening": [
                        "Check for JavaScript errors",
                        "Verify modal creation functions are loaded",
                        "Check event handler attachment",
                        "Validate data attribute extraction"
                    ],
                    "data_mode_toggle_issues": [
                        "Verify admin permissions",
                        "Check data toggle system initialization",
                        "Validate database mode switching logic",
                        "Check for permission conflicts"
                    ]
                },
                "performance_optimization": [
                    "Optimize database queries with proper indexing",
                    "Implement caching for frequently accessed data",
                    "Minimize JavaScript bundle size",
                    "Use efficient DOM manipulation techniques",
                    "Implement lazy loading for large datasets"
                ]
            },
            "best_practices": {
                "development": [
                    "Always create backups before major changes",
                    "Test thoroughly in demo mode before production",
                    "Use proper error handling and logging",
                    "Follow RESTful API design principles",
                    "Implement comprehensive input validation"
                ],
                "ai_collaboration": [
                    "Document all AI interactions and decisions",
                    "Use standardized handoff procedures",
                    "Maintain context across AI model switches",
                    "Validate AI-generated code and suggestions",
                    "Regular knowledge base updates"
                ],
                "deployment": [
                    "Run pre-deployment tests",
                    "Create deployment backups",
                    "Monitor system health post-deployment",
                    "Have rollback procedures ready",
                    "Document all deployment changes"
                ]
            }
        }
        
        # Save knowledge base to file
        with open(self.knowledge_file, "w") as f:
            json.dump(knowledge_base, f, indent=2)
        
        # Store in database for AI access
        self._store_knowledge_in_database(knowledge_base)
    
    def _store_knowledge_in_database(self, knowledge_base: Dict[str, Any]):
        """Store knowledge base entries in database for AI queries"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        def store_recursive(data, category, topic_prefix=""):
            """Recursively store knowledge entries"""
            if isinstance(data, dict):
                for key, value in data.items():
                    current_topic = f"{topic_prefix}.{key}" if topic_prefix else key
                    
                    if isinstance(value, (dict, list)):
                        store_recursive(value, category, current_topic)
                    else:
                        # Store individual knowledge entry
                        knowledge_id = str(uuid.uuid4())
                        cursor.execute('''
                            INSERT OR REPLACE INTO ai_knowledge_base
                            (knowledge_id, category, topic, content, source_ai, 
                             created_at, updated_at, confidence_score, validation_status, tags)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            knowledge_id,
                            category,
                            current_topic,
                            str(value),
                            "system",
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat(),
                            1.0,  # System knowledge has high confidence
                            "validated",
                            json.dumps(["chatterfix", "system", category])
                        ))
            elif isinstance(data, list):
                # Store list as single entry
                knowledge_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_knowledge_base
                    (knowledge_id, category, topic, content, source_ai, 
                     created_at, updated_at, confidence_score, validation_status, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_id,
                    category,
                    topic_prefix,
                    json.dumps(data),
                    "system",
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                    1.0,
                    "validated",
                    json.dumps(["chatterfix", "system", category])
                ))
        
        # Store each top-level category
        for category, content in knowledge_base.items():
            store_recursive(content, category)
        
        conn.commit()
        conn.close()
    
    async def query_knowledge(self, query: str, ai_model: AIModel) -> List[Dict[str, Any]]:
        """Query knowledge base for relevant information"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        # Simple keyword-based search (could be enhanced with vector search)
        search_terms = query.lower().split()
        
        # Build search query
        search_conditions = []
        search_params = []
        
        for term in search_terms:
            search_conditions.append('''
                (LOWER(topic) LIKE ? OR LOWER(content) LIKE ? OR LOWER(tags) LIKE ?)
            ''')
            search_params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        
        search_query = f'''
            SELECT * FROM ai_knowledge_base 
            WHERE {" OR ".join(search_conditions)}
            ORDER BY confidence_score DESC, updated_at DESC
            LIMIT 10
        '''
        
        cursor.execute(search_query, search_params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "knowledge_id": row[0],
                "category": row[1],
                "topic": row[2],
                "content": row[3],
                "source_ai": row[4],
                "created_at": row[5],
                "confidence_score": row[7],
                "validation_status": row[8]
            })
        
        return results
    
    async def add_knowledge(
        self, 
        category: str, 
        topic: str, 
        content: str, 
        source_ai: AIModel,
        confidence_score: float = 0.8,
        tags: List[str] = None
    ) -> str:
        """Add new knowledge to the base"""
        knowledge_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_knowledge_base
            (knowledge_id, category, topic, content, source_ai, 
             created_at, updated_at, confidence_score, validation_status, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            knowledge_id,
            category,
            topic,
            content,
            source_ai.value,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            confidence_score,
            "pending",
            json.dumps(tags or [])
        ))
        
        conn.commit()
        conn.close()
        
        return knowledge_id

class AICollaborationSystem:
    """
    Main AI Collaboration System that orchestrates all components
    """
    
    def __init__(self):
        self.database = AICollaborationDatabase()
        self.context_manager = ContextManager(self.database)
        self.handoff_manager = AIHandoffManager(self.database, self.context_manager)
        self.deployment_safety = DeploymentSafetySystem(self.database)
        self.workflow_manager = WorkflowManager(self.database)
        self.knowledge_base = ChatterFixKnowledgeBase(self.database)
        
        logger.info("🚀 AI Collaboration System initialized successfully")
    
    async def start_ai_session(self, ai_model: AIModel, context_notes: str = "") -> str:
        """Start a new AI collaboration session"""
        session_id = str(uuid.uuid4())
        
        # Capture current context
        current_context = await self.context_manager.capture_current_context()
        
        # Get pending handoffs for this AI
        pending_handoffs = await self._get_pending_handoffs(ai_model)
        
        # Get active tasks
        active_tasks = self.database.get_active_tasks_for_ai(ai_model)
        
        # Create session
        session = AISession(
            session_id=session_id,
            ai_model=ai_model,
            start_time=datetime.now(timezone.utc),
            end_time=None,
            context_data={
                "current_context": current_context.to_dict(),
                "pending_handoffs": pending_handoffs,
                "active_tasks": [task.to_dict() for task in active_tasks],
                "session_notes": context_notes
            },
            tasks_completed=[],
            knowledge_gained=[],
            issues_encountered=[],
            handoff_notes="",
            status="active"
        )
        
        self.database.save_ai_session(session)
        
        # Get task recommendations
        recommendations = await self.workflow_manager.get_task_recommendations(ai_model)
        
        logger.info(f"✅ AI session started for {ai_model.value}: {session_id}")
        
        return session_id, {
            "session_id": session_id,
            "current_context": asdict(current_context),
            "active_tasks": [asdict(task) for task in active_tasks],
            "recommendations": recommendations,
            "pending_handoffs": pending_handoffs
        }
    
    async def end_ai_session(
        self, 
        session_id: str, 
        handoff_notes: str = "",
        next_ai: Optional[AIModel] = None
    ) -> Dict[str, Any]:
        """End AI session and optionally initiate handoff"""
        # Update session end time
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ai_sessions 
            SET end_time = ?, handoff_notes = ?, status = 'completed'
            WHERE session_id = ?
        ''', (
            datetime.now(timezone.utc).isoformat(),
            handoff_notes,
            session_id
        ))
        
        # Get session data
        cursor.execute('SELECT * FROM ai_sessions WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if not row:
            return {"error": "Session not found"}
        
        session_summary = {
            "session_id": session_id,
            "ai_model": row[1],
            "duration": "Session completed",
            "tasks_completed": json.loads(row[4]),
            "knowledge_gained": json.loads(row[5]),
            "issues_encountered": json.loads(row[6]),
            "handoff_notes": handoff_notes
        }
        
        # Initiate handoff if next AI specified
        if next_ai:
            handoff_id = await self.handoff_manager.initiate_handoff(
                AIModel(row[1]), next_ai, "normal", handoff_notes
            )
            session_summary["handoff_initiated"] = handoff_id
        
        logger.info(f"✅ AI session ended: {session_id}")
        
        return session_summary
    
    async def create_task(
        self,
        title: str,
        description: str,
        assigned_ai: AIModel,
        priority: Priority,
        created_by: AIModel,
        estimated_effort: int = 1,
        due_date: Optional[datetime] = None
    ) -> str:
        """Create a new collaboration task"""
        task_id = await self.workflow_manager.assign_task(
            title=title,
            description=description,
            assigned_ai=assigned_ai,
            priority=priority,
            created_by=created_by,
            estimated_effort=estimated_effort,
            due_date=due_date
        )
        
        logger.info(f"✅ Task created: {task_id} assigned to {assigned_ai.value}")
        return task_id
    
    async def complete_task(
        self,
        task_id: str,
        ai_model: AIModel,
        completion_notes: str = "",
        artifacts: List[str] = None
    ):
        """Mark task as completed"""
        await self.workflow_manager.update_task_status(
            task_id=task_id,
            new_status=TaskStatus.COMPLETED,
            ai_model=ai_model,
            notes=completion_notes,
            artifacts=artifacts
        )
        
        logger.info(f"✅ Task completed: {task_id} by {ai_model.value}")
    
    async def deploy_with_safety(self, ai_model: AIModel, description: str = "") -> Dict[str, Any]:
        """Deploy changes with full safety checks and rollback capability"""
        # Create backup
        backup_id = await self.deployment_safety.create_backup(
            f"Pre-deployment backup by {ai_model.value}: {description}"
        )
        
        # Run pre-deployment tests
        test_results = await self.deployment_safety.run_pre_deployment_tests()
        
        deployment_result = {
            "backup_id": backup_id,
            "test_results": test_results,
            "deployment_status": "ready" if test_results["overall_status"] == "passed" else "blocked",
            "ai_model": ai_model.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if test_results["overall_status"] != "passed":
            deployment_result["message"] = "Deployment blocked due to test failures"
            deployment_result["required_actions"] = [
                "Fix failing tests",
                "Address identified issues",
                "Re-run safety checks"
            ]
        else:
            deployment_result["message"] = "Deployment ready - all safety checks passed"
            deployment_result["rollback_available"] = backup_id
        
        logger.info(f"🚀 Deployment safety check completed by {ai_model.value}")
        
        return deployment_result
    
    async def query_knowledge(self, query: str, ai_model: AIModel) -> List[Dict[str, Any]]:
        """Query the ChatterFix knowledge base"""
        results = await self.knowledge_base.query_knowledge(query, ai_model)
        
        logger.info(f"📚 Knowledge query by {ai_model.value}: {query}")
        
        return results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        current_context = await self.context_manager.capture_current_context()
        
        # Get active sessions
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT ai_model, COUNT(*) FROM ai_sessions WHERE status = "active" GROUP BY ai_model')
        active_sessions = dict(cursor.fetchall())
        
        cursor.execute('SELECT status, COUNT(*) FROM collaboration_tasks GROUP BY status')
        task_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM ai_handoffs WHERE status = "pending"')
        pending_handoffs = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_health": asdict(current_context),
            "active_sessions": active_sessions,
            "task_summary": task_counts,
            "pending_handoffs": pending_handoffs,
            "knowledge_base_entries": await self._count_knowledge_entries(),
            "recent_deployments": await self._get_recent_deployments()
        }
    
    async def _get_pending_handoffs(self, ai_model: AIModel) -> List[Dict[str, Any]]:
        """Get pending handoffs for an AI model"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ai_handoffs 
            WHERE to_ai = ? AND status = 'pending'
            ORDER BY timestamp DESC
        ''', (ai_model.value,))
        
        rows = cursor.fetchall()
        conn.close()
        
        handoffs = []
        for row in rows:
            handoffs.append({
                "handoff_id": row[0],
                "from_ai": row[1],
                "timestamp": row[3],
                "recommendations": json.loads(row[7]),
                "urgency_level": row[8]
            })
        
        return handoffs
    
    async def _count_knowledge_entries(self) -> int:
        """Count total knowledge base entries"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ai_knowledge_base')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    async def _get_recent_deployments(self) -> List[Dict[str, Any]]:
        """Get recent deployment history"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM deployment_history 
            ORDER BY timestamp DESC LIMIT 5
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        deployments = []
        for row in rows:
            deployments.append({
                "deployment_id": row[0],
                "environment": row[1],
                "ai_model": row[2],
                "timestamp": row[3],
                "status": row[5]
            })
        
        return deployments

# Global collaboration system instance
collaboration_system = AICollaborationSystem()

async def initialize_ai_collaboration():
    """Initialize the AI collaboration system"""
    logger.info("🚀 Initializing ChatterFix AI Collaboration System...")
    
    # Capture initial system state
    await collaboration_system.context_manager.capture_current_context()
    
    logger.info("✅ AI Collaboration System ready for multi-AI development")
    
    return collaboration_system

if __name__ == "__main__":
    # Initialize the system
    asyncio.run(initialize_ai_collaboration())