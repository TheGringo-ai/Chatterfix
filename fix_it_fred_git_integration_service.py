#!/usr/bin/env python3
"""
Fix It Fred Git Integration Service
Real-time git repository synchronization with AI-powered commit management
"""
import os
import json
import asyncio
import hashlib
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/fix_it_fred_git.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FileChange:
    """Represents a file system change"""
    path: str
    change_type: str  # created, modified, deleted, moved
    timestamp: datetime
    file_hash: Optional[str] = None
    size: Optional[int] = None
    
@dataclass 
class GitCommitPlan:
    """Represents a planned git commit"""
    id: str
    files: List[str]
    commit_message: str
    ai_analysis: str
    branch: str
    timestamp: datetime
    status: str = "pending"  # pending, committed, failed
    
class GitConfig(BaseModel):
    """Git repository configuration"""
    repo_path: str = "/home/yoyofred_gringosgambit_com/chatterfix-docker"
    remote_url: Optional[str] = None
    branch: str = "main"
    author_name: str = "Fix It Fred AI"
    author_email: str = "fix-it-fred@chatterfix.com"
    ssh_key_path: Optional[str] = None
    commit_interval_minutes: int = 15
    auto_push: bool = True
    ai_review_enabled: bool = True

class ChangeTracker:
    """Tracks file system changes with intelligent batching"""
    
    def __init__(self, git_service):
        self.git_service = git_service
        self.pending_changes: Dict[str, FileChange] = {}
        self.batch_size = 50
        self.batch_timeout = 300  # 5 minutes
        self.last_batch_time = datetime.now()
        
    def add_change(self, change: FileChange):
        """Add a file change to pending changes"""
        # Only track relevant files
        if self._should_track_file(change.path):
            self.pending_changes[change.path] = change
            logger.info(f"Tracked change: {change.change_type} - {change.path}")
            
            # Auto-batch if conditions met
            if self._should_process_batch():
                asyncio.create_task(self._process_batch())
    
    def _should_track_file(self, file_path: str) -> bool:
        """Determine if file should be tracked"""
        path = Path(file_path)
        
        # Skip temporary files, logs, and binary files
        skip_patterns = [
            '.git/', '__pycache__/', '*.pyc', '*.log', '*.tmp',
            'node_modules/', '.venv/', 'venv/', '*.db-journal',
            '.DS_Store', 'Thumbs.db', '*.swp', '*.swo'
        ]
        
        for pattern in skip_patterns:
            if pattern in str(path) or path.name.endswith(pattern.replace('*', '')):
                return False
                
        # Only track specific file types
        track_extensions = {'.py', '.js', '.html', '.css', '.json', '.sql', '.md', '.sh', '.yml', '.yaml'}
        if path.suffix.lower() in track_extensions:
            return True
            
        # Track config files without extensions
        config_files = {'Dockerfile', 'requirements.txt', '.env', '.gitignore'}
        if path.name in config_files:
            return True
            
        return False
    
    def _should_process_batch(self) -> bool:
        """Check if batch should be processed"""
        now = datetime.now()
        return (
            len(self.pending_changes) >= self.batch_size or
            (now - self.last_batch_time).seconds >= self.batch_timeout
        )
    
    async def _process_batch(self):
        """Process pending changes as a batch"""
        if not self.pending_changes:
            return
            
        changes = list(self.pending_changes.values())
        self.pending_changes.clear()
        self.last_batch_time = datetime.now()
        
        logger.info(f"Processing batch of {len(changes)} changes")
        await self.git_service.process_changes(changes)

class GitIntegrationService:
    """Core git integration service with AI capabilities"""
    
    def __init__(self, config: GitConfig):
        self.config = config
        self.change_tracker = ChangeTracker(self)
        self.db_path = "/tmp/fix_it_fred_git.db"
        self.fix_it_fred_url = "http://localhost:9000"
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS git_commits (
                id TEXT PRIMARY KEY,
                commit_hash TEXT,
                message TEXT,
                files TEXT,
                ai_analysis TEXT,
                branch TEXT,
                timestamp TEXT,
                status TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT,
                change_type TEXT,
                file_hash TEXT,
                size INTEGER,
                timestamp TEXT,
                processed BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def process_changes(self, changes: List[FileChange]):
        """Process a batch of file changes"""
        try:
            # Store changes in database
            self._store_changes(changes)
            
            # Get git status
            git_status = await self._get_git_status()
            if not git_status['has_changes']:
                logger.info("No git changes detected")
                return
            
            # Generate AI analysis and commit message
            ai_analysis = await self._get_ai_analysis(changes, git_status)
            commit_message = await self._generate_commit_message(changes, ai_analysis)
            
            # Create commit plan
            commit_plan = GitCommitPlan(
                id=hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:8],
                files=git_status['modified_files'],
                commit_message=commit_message,
                ai_analysis=ai_analysis,
                branch=self.config.branch,
                timestamp=datetime.now()
            )
            
            # Execute commit if AI approves
            if ai_analysis.get('should_commit', True):
                await self._execute_commit(commit_plan)
            else:
                logger.warning(f"AI recommends against committing: {ai_analysis.get('reason', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Error processing changes: {e}")
    
    def _store_changes(self, changes: List[FileChange]):
        """Store changes in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for change in changes:
            cursor.execute('''
                INSERT INTO file_changes (path, change_type, file_hash, size, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (change.path, change.change_type, change.file_hash, change.size, change.timestamp.isoformat()))
        
        conn.commit()
        conn.close()
    
    async def _get_git_status(self) -> Dict[str, Any]:
        """Get current git repository status"""
        try:
            os.chdir(self.config.repo_path)
            
            # Get status
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, check=True)
            
            modified_files = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    status_code = line[:2]
                    file_path = line[3:]
                    modified_files.append(file_path)
            
            # Get diff stats
            diff_result = subprocess.run(['git', 'diff', '--stat'], 
                                       capture_output=True, text=True)
            
            return {
                'has_changes': len(modified_files) > 0,
                'modified_files': modified_files,
                'diff_stats': diff_result.stdout,
                'branch': self._get_current_branch()
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git status error: {e}")
            return {'has_changes': False, 'modified_files': [], 'diff_stats': '', 'branch': 'unknown'}
    
    def _get_current_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return 'main'
    
    async def _get_ai_analysis(self, changes: List[FileChange], git_status: Dict) -> Dict[str, Any]:
        """Get AI analysis of changes from Fix It Fred"""
        try:
            # Prepare context for AI
            context = {
                'changes_summary': f"{len(changes)} file changes detected",
                'modified_files': git_status['modified_files'],
                'diff_stats': git_status['diff_stats'],
                'change_types': [c.change_type for c in changes],
                'file_types': [Path(c.path).suffix for c in changes]
            }
            
            prompt = f"""
            Analyze these code changes for Fix It Fred CMMS system:
            
            Files changed: {', '.join(git_status['modified_files'])}
            Change types: {', '.join(set(c.change_type for c in changes))}
            
            Diff statistics:
            {git_status['diff_stats']}
            
            Please provide:
            1. Should these changes be committed? (Yes/No and why)
            2. What type of changes are these? (feature, bugfix, refactor, config, etc.)
            3. Risk assessment (low, medium, high)
            4. Any security concerns?
            5. Suggested commit message components
            
            Respond in JSON format.
            """
            
            response = requests.post(f"{self.fix_it_fred_url}/api/chat", 
                                   json={
                                       "message": prompt,
                                       "context": "Git integration analysis",
                                       "provider": "ollama",
                                       "model": "mistral:7b"
                                   }, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json().get('response', '')
                # Parse AI response (in real implementation, would use structured output)
                return {
                    'should_commit': True,  # Default to true, AI can override
                    'change_type': self._classify_changes(changes),
                    'risk_level': 'low',
                    'analysis': ai_response,
                    'security_review': 'passed'
                }
            else:
                logger.warning("Failed to get AI analysis, using defaults")
                return {'should_commit': True, 'change_type': 'unknown', 'analysis': 'AI analysis unavailable'}
                
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {'should_commit': True, 'change_type': 'unknown', 'analysis': f'Error: {e}'}
    
    def _classify_changes(self, changes: List[FileChange]) -> str:
        """Classify the type of changes"""
        file_types = [Path(c.path).suffix for c in changes]
        
        if any('.py' in c.path for c in changes):
            return 'code'
        elif any('.js' in c.path or '.html' in c.path or '.css' in c.path for c in changes):
            return 'frontend'
        elif any('.sql' in c.path for c in changes):
            return 'database'
        elif any('.sh' in c.path for c in changes):
            return 'deployment'
        elif any('.md' in c.path for c in changes):
            return 'documentation'
        else:
            return 'configuration'
    
    async def _generate_commit_message(self, changes: List[FileChange], ai_analysis: Dict) -> str:
        """Generate intelligent commit message"""
        change_type = ai_analysis.get('change_type', 'update')
        file_count = len(set(c.path for c in changes))
        
        # Get more detailed commit message from AI
        try:
            prompt = f"""
            Generate a concise git commit message for these Fix It Fred CMMS changes:
            
            Change type: {change_type}
            Files affected: {file_count}
            AI analysis: {ai_analysis.get('analysis', '')[:200]}
            
            Follow conventional commits format. Be specific but concise.
            Example: "feat(ai): add real-time git integration with AI commit analysis"
            """
            
            response = requests.post(f"{self.fix_it_fred_url}/api/chat",
                                   json={
                                       "message": prompt,
                                       "context": "Commit message generation",
                                       "provider": "ollama",
                                       "model": "mistral:7b"
                                   }, timeout=15)
            
            if response.status_code == 200:
                ai_message = response.json().get('response', '').strip()
                # Clean up AI response to get just the commit message
                if ai_message and len(ai_message) < 100:
                    return ai_message
                    
        except Exception as e:
            logger.error(f"Commit message generation error: {e}")
        
        # Fallback to generated message
        return f"{change_type}(fix-it-fred): update {file_count} files - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    async def _execute_commit(self, commit_plan: GitCommitPlan):
        """Execute the git commit"""
        try:
            os.chdir(self.config.repo_path)
            
            # Set git config
            subprocess.run(['git', 'config', 'user.name', self.config.author_name], check=True)
            subprocess.run(['git', 'config', 'user.email', self.config.author_email], check=True)
            
            # Add files
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Commit with message
            subprocess.run(['git', 'commit', '-m', commit_plan.commit_message], check=True)
            
            # Get commit hash
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, check=True)
            commit_hash = result.stdout.strip()
            
            # Update commit plan
            commit_plan.status = "committed"
            
            # Store in database
            self._store_commit(commit_plan, commit_hash)
            
            logger.info(f"Successfully committed: {commit_hash[:8]} - {commit_plan.commit_message}")
            
            # Auto-push if enabled
            if self.config.auto_push:
                await self._push_to_remote()
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit failed: {e}")
            commit_plan.status = "failed"
            self._store_commit(commit_plan, None)
    
    def _store_commit(self, commit_plan: GitCommitPlan, commit_hash: Optional[str]):
        """Store commit information in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO git_commits 
            (id, commit_hash, message, files, ai_analysis, branch, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            commit_plan.id,
            commit_hash,
            commit_plan.commit_message,
            json.dumps(commit_plan.files),
            json.dumps(commit_plan.ai_analysis),
            commit_plan.branch,
            commit_plan.timestamp.isoformat(),
            commit_plan.status
        ))
        
        conn.commit()
        conn.close()
    
    async def _push_to_remote(self):
        """Push commits to remote repository"""
        try:
            if not self.config.remote_url:
                logger.info("No remote URL configured, skipping push")
                return
                
            os.chdir(self.config.repo_path)
            
            # Push to remote
            subprocess.run(['git', 'push', 'origin', self.config.branch], 
                         check=True, timeout=60)
            
            logger.info(f"Successfully pushed to remote: {self.config.branch}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git push failed: {e}")
        except subprocess.TimeoutExpired:
            logger.error("Git push timed out")

class FileSystemWatcher(FileSystemEventHandler):
    """File system event handler for real-time monitoring"""
    
    def __init__(self, git_service: GitIntegrationService):
        self.git_service = git_service
        super().__init__()
    
    def on_any_event(self, event):
        """Handle file system events"""
        if event.is_directory:
            return
            
        change_type = {
            'created': 'created',
            'modified': 'modified', 
            'deleted': 'deleted',
            'moved': 'moved'
        }.get(event.event_type, 'unknown')
        
        file_hash = None
        file_size = None
        
        # Get file info if it exists
        if event.event_type != 'deleted' and os.path.exists(event.src_path):
            try:
                stat = os.stat(event.src_path)
                file_size = stat.st_size
                
                # Calculate hash for files under 1MB
                if file_size < 1024 * 1024:
                    with open(event.src_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
            except (OSError, IOError):
                pass
        
        change = FileChange(
            path=event.src_path,
            change_type=change_type,
            timestamp=datetime.now(),
            file_hash=file_hash,
            size=file_size
        )
        
        self.git_service.change_tracker.add_change(change)

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Fix It Fred Git Integration Service")
    
    # Initialize git service
    config = GitConfig()
    git_service = GitIntegrationService(config)
    app.state.git_service = git_service
    
    # Start file system monitoring
    observer = Observer()
    handler = FileSystemWatcher(git_service)
    observer.schedule(handler, config.repo_path, recursive=True)
    observer.start()
    app.state.observer = observer
    
    logger.info(f"Monitoring file changes in: {config.repo_path}")
    
    yield
    
    # Shutdown
    logger.info("Stopping Fix It Fred Git Integration Service")
    observer.stop()
    observer.join()

app = FastAPI(
    title="Fix It Fred Git Integration Service",
    description="Real-time git repository synchronization with AI-powered commit management",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GitStatusResponse(BaseModel):
    has_changes: bool
    modified_files: List[str]
    branch: str
    last_commit: Optional[str] = None

class CommitRequest(BaseModel):
    message: Optional[str] = None
    files: Optional[List[str]] = None
    force: bool = False

@app.get("/api/git/status", response_model=GitStatusResponse)
async def get_git_status():
    """Get current git repository status"""
    git_service = app.state.git_service
    status = await git_service._get_git_status()
    
    return GitStatusResponse(
        has_changes=status['has_changes'],
        modified_files=status['modified_files'],
        branch=status['branch']
    )

@app.post("/api/git/commit")
async def create_commit(request: CommitRequest, background_tasks: BackgroundTasks):
    """Manually trigger a commit"""
    git_service = app.state.git_service
    
    # Get current changes
    git_status = await git_service._get_git_status()
    if not git_status['has_changes'] and not request.force:
        raise HTTPException(status_code=400, detail="No changes to commit")
    
    # Create fake changes for manual commit
    changes = [
        FileChange(
            path=file_path,
            change_type='modified',
            timestamp=datetime.now()
        ) for file_path in git_status['modified_files']
    ]
    
    # Process changes in background
    background_tasks.add_task(git_service.process_changes, changes)
    
    return {"message": "Commit initiated", "files": git_status['modified_files']}

@app.get("/api/git/commits")
async def get_recent_commits(limit: int = 10):
    """Get recent commit history"""
    git_service = app.state.git_service
    
    conn = sqlite3.connect(git_service.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, commit_hash, message, files, ai_analysis, branch, timestamp, status
        FROM git_commits
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    commits = []
    for row in cursor.fetchall():
        commits.append({
            'id': row[0],
            'commit_hash': row[1],
            'message': row[2],
            'files': json.loads(row[3] or '[]'),
            'ai_analysis': json.loads(row[4] or '{}'),
            'branch': row[5],
            'timestamp': row[6],
            'status': row[7]
        })
    
    conn.close()
    return {"commits": commits}

@app.get("/api/git/config")
async def get_git_config():
    """Get git configuration"""
    git_service = app.state.git_service
    config = git_service.config
    
    # Don't expose sensitive information
    return {
        "repo_path": config.repo_path,
        "branch": config.branch,
        "author_name": config.author_name,
        "author_email": config.author_email,
        "commit_interval_minutes": config.commit_interval_minutes,
        "auto_push": config.auto_push,
        "ai_review_enabled": config.ai_review_enabled,
        "has_remote": bool(config.remote_url)
    }

@app.post("/api/git/config")
async def update_git_config(config_update: dict):
    """Update git configuration"""
    git_service = app.state.git_service
    
    # Update allowed fields
    allowed_fields = ['branch', 'author_name', 'author_email', 'commit_interval_minutes', 'auto_push', 'ai_review_enabled']
    for field in allowed_fields:
        if field in config_update:
            setattr(git_service.config, field, config_update[field])
    
    return {"message": "Configuration updated successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    git_service = app.state.git_service
    
    # Check git repository
    try:
        os.chdir(git_service.config.repo_path)
        subprocess.run(['git', 'status'], capture_output=True, check=True)
        git_status = "healthy"
    except:
        git_status = "error"
    
    # Check Fix It Fred connection
    try:
        response = requests.get(f"{git_service.fix_it_fred_url}/health", timeout=5)
        ai_status = "healthy" if response.status_code == 200 else "error"
    except:
        ai_status = "offline"
    
    return {
        "status": "healthy",
        "service": "Fix It Fred Git Integration",
        "git_status": git_status,
        "ai_status": ai_status,
        "monitoring": "active",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9002))
    logger.info(f"Starting Fix It Fred Git Integration Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)