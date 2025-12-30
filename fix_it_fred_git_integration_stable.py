#!/usr/bin/env python3
"""
Fix It Fred Git Integration - Production Stable Version
Resource-aware, multi-provider AI support, crash-resistant
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
import subprocess
import threading
import logging
import psutil
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager

import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import schedule

# Resource Management Configuration
@dataclass
class ResourceLimits:
    max_memory_mb: int = 512  # Maximum memory usage
    max_cpu_percent: float = 25.0  # Maximum CPU usage
    max_file_queue: int = 100  # Maximum files in processing queue
    batch_size: int = 20  # Files per batch
    batch_timeout: int = 180  # Seconds to wait for batch
    health_check_interval: int = 30  # Health check frequency

class ResourceMonitor:
    """Monitors and manages system resource usage"""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.process = psutil.Process()
        self.logger = logging.getLogger(__name__)
        self.is_healthy = True
        self.last_check = time.time()
        
    def check_resources(self) -> Dict[str, Any]:
        """Check current resource usage"""
        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent()
            
            status = {
                'memory_mb': round(memory_mb, 2),
                'cpu_percent': round(cpu_percent, 2),
                'memory_limit': self.limits.max_memory_mb,
                'cpu_limit': self.limits.max_cpu_percent,
                'healthy': True,
                'timestamp': datetime.now().isoformat()
            }
            
            # Check limits
            if memory_mb > self.limits.max_memory_mb:
                status['healthy'] = False
                status['warning'] = f"Memory usage {memory_mb}MB exceeds limit {self.limits.max_memory_mb}MB"
                
            if cpu_percent > self.limits.max_cpu_percent:
                status['healthy'] = False
                status['warning'] = f"CPU usage {cpu_percent}% exceeds limit {self.limits.max_cpu_percent}%"
                
            self.is_healthy = status['healthy']
            return status
            
        except Exception as e:
            self.logger.error(f"Resource check failed: {e}")
            return {'healthy': False, 'error': str(e)}
    
    def should_throttle(self) -> bool:
        """Check if operations should be throttled"""
        return not self.is_healthy or (time.time() - self.last_check) > self.limits.health_check_interval

class MultiProviderAI:
    """Multi-provider AI integration with fallback support"""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "ai_providers.json"
        self.providers = {}
        self.logger = logging.getLogger(__name__)
        self._load_config()
        
    def _load_config(self):
        """Load AI provider configurations"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.providers = config.get('providers', {})
            else:
                # Create default config
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load AI config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default AI provider configuration"""
        default_config = {
            "providers": {
                "ollama": {
                    "enabled": True,
                    "url": "http://localhost:11434/api/generate",
                    "model": "llama3.2:1b",
                    "priority": 1,
                    "timeout": 30
                },
                "openai": {
                    "enabled": False,
                    "api_key": "",
                    "model": "gpt-3.5-turbo",
                    "priority": 2,
                    "timeout": 30
                },
                "anthropic": {
                    "enabled": False,
                    "api_key": "",
                    "model": "claude-3-haiku-20240307",
                    "priority": 3,
                    "timeout": 30
                },
                "google": {
                    "enabled": False,
                    "api_key": "",
                    "model": "gemini-pro",
                    "priority": 4,
                    "timeout": 30
                },
                "xai": {
                    "enabled": False,
                    "api_key": "",
                    "model": "grok-beta",
                    "priority": 5,
                    "timeout": 30
                }
            }
        }
        
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        self.providers = default_config['providers']
    
    def add_api_key(self, provider: str, api_key: str) -> bool:
        """Add or update API key for a provider"""
        try:
            if provider in self.providers:
                self.providers[provider]['api_key'] = api_key
                self.providers[provider]['enabled'] = True
                self._save_config()
                self.logger.info(f"API key added for {provider}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to add API key for {provider}: {e}")
            return False
    
    def _save_config(self):
        """Save current configuration"""
        config = {"providers": self.providers}
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def generate_commit_message(self, diff: str, files: List[str]) -> Dict[str, Any]:
        """Generate commit message using available AI providers"""
        prompt = f"""
Analyze this git diff and generate a conventional commit message.

Files changed: {', '.join(files)}

Diff:
{diff[:2000]}  # Limit for performance

Generate a concise commit message following conventional commits format:
type(scope): description

Types: feat, fix, docs, style, refactor, perf, test, chore
Keep description under 50 characters.
"""
        
        # Try providers in priority order
        enabled_providers = [(name, config) for name, config in self.providers.items() 
                           if config.get('enabled', False)]
        enabled_providers.sort(key=lambda x: x[1].get('priority', 999))
        
        for provider_name, provider_config in enabled_providers:
            try:
                response = self._call_provider(provider_name, provider_config, prompt)
                if response.get('success'):
                    return response
            except Exception as e:
                self.logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        # Fallback to simple commit message
        return {
            'success': True,
            'message': f"chore: update {len(files)} file{'s' if len(files) > 1 else ''}",
            'provider': 'fallback',
            'analysis': 'Basic file update detected'
        }
    
    def _call_provider(self, provider_name: str, config: Dict, prompt: str) -> Dict[str, Any]:
        """Call specific AI provider"""
        timeout = config.get('timeout', 30)
        
        if provider_name == 'ollama':
            return self._call_ollama(config, prompt, timeout)
        elif provider_name == 'openai':
            return self._call_openai(config, prompt, timeout)
        elif provider_name == 'anthropic':
            return self._call_anthropic(config, prompt, timeout)
        elif provider_name == 'google':
            return self._call_google(config, prompt, timeout)
        elif provider_name == 'xai':
            return self._call_xai(config, prompt, timeout)
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
    
    def _call_ollama(self, config: Dict, prompt: str, timeout: int) -> Dict[str, Any]:
        """Call Ollama API"""
        response = requests.post(
            config['url'],
            json={
                'model': config['model'],
                'prompt': prompt,
                'stream': False
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'message': data.get('response', '').strip(),
            'provider': 'ollama',
            'model': config['model']
        }
    
    def _call_openai(self, config: Dict, prompt: str, timeout: int) -> Dict[str, Any]:
        """Call OpenAI API"""
        headers = {
            'Authorization': f"Bearer {config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json={
                'model': config['model'],
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 100,
                'temperature': 0.3
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'message': data['choices'][0]['message']['content'].strip(),
            'provider': 'openai',
            'model': config['model']
        }
    
    def _call_anthropic(self, config: Dict, prompt: str, timeout: int) -> Dict[str, Any]:
        """Call Anthropic Claude API"""
        headers = {
            'x-api-key': config['api_key'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json={
                'model': config['model'],
                'max_tokens': 100,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'message': data['content'][0]['text'].strip(),
            'provider': 'anthropic',
            'model': config['model']
        }
    
    def _call_google(self, config: Dict, prompt: str, timeout: int) -> Dict[str, Any]:
        """Call Google Gemini API"""
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{config['model']}:generateContent?key={config['api_key']}",
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {
                    'maxOutputTokens': 100,
                    'temperature': 0.3
                }
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'message': data['candidates'][0]['content']['parts'][0]['text'].strip(),
            'provider': 'google',
            'model': config['model']
        }
    
    def _call_xai(self, config: Dict, prompt: str, timeout: int) -> Dict[str, Any]:
        """Call xAI Grok API"""
        headers = {
            'Authorization': f"Bearer {config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers=headers,
            json={
                'model': config['model'],
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 100,
                'temperature': 0.3
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'message': data['choices'][0]['message']['content'].strip(),
            'provider': 'xai',
            'model': config['model']
        }

class StableGitIntegration:
    """Stable, resource-aware git integration service"""
    
    def __init__(self, repo_path: str, config_dir: str = "/tmp/fix_it_fred_git"):
        self.repo_path = Path(repo_path)
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.limits = ResourceLimits()
        self.resource_monitor = ResourceMonitor(self.limits)
        self.ai = MultiProviderAI(str(self.config_dir))
        
        # File processing
        self.file_queue = []
        self.processing_lock = threading.Lock()
        self.observer = None
        
        # Database
        self.db_path = self.config_dir / "git_integration.db"
        self._init_database()
        
        # Logging
        self._setup_logging()
        
        # Flask app
        self.app = Flask(__name__)
        self._setup_routes()
        
        # Graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self.running = True
        
    def _setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.config_dir / "git_integration.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.observer:
            self.observer.stop()
            
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_changes (
                    id INTEGER PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    commit_hash TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS commits (
                    id INTEGER PRIMARY KEY,
                    commit_hash TEXT UNIQUE NOT NULL,
                    message TEXT NOT NULL,
                    files_count INTEGER,
                    provider TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_stats (
                    id INTEGER PRIMARY KEY,
                    memory_mb REAL,
                    cpu_percent REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
    def _setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            resource_status = self.resource_monitor.check_resources()
            return jsonify({
                'status': 'healthy' if resource_status['healthy'] else 'warning',
                'service': 'Fix It Fred Git Integration',
                'resources': resource_status,
                'queue_size': len(self.file_queue),
                'ai_providers': {name: config.get('enabled', False) 
                               for name, config in self.ai.providers.items()}
            })
        
        @self.app.route('/api/git/status')
        def git_status():
            """Get current git status"""
            try:
                result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                return jsonify({
                    'success': True,
                    'status': result.stdout,
                    'clean': len(result.stdout.strip()) == 0
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/git/commits')
        def recent_commits():
            """Get recent commits"""
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        'SELECT * FROM commits ORDER BY timestamp DESC LIMIT 20'
                    )
                    commits = [dict(zip([col[0] for col in cursor.description], row)) 
                             for row in cursor.fetchall()]
                    
                return jsonify({'success': True, 'commits': commits})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/providers', methods=['GET'])
        def get_providers():
            """Get AI provider status"""
            return jsonify({
                'success': True,
                'providers': {
                    name: {
                        'enabled': config.get('enabled', False),
                        'model': config.get('model', ''),
                        'priority': config.get('priority', 999),
                        'has_api_key': bool(config.get('api_key', ''))
                    }
                    for name, config in self.ai.providers.items()
                }
            })
        
        @self.app.route('/api/providers/<provider>/key', methods=['POST'])
        def add_provider_key(provider):
            """Add API key for provider"""
            data = request.get_json()
            api_key = data.get('api_key', '').strip()
            
            if not api_key:
                return jsonify({'success': False, 'error': 'API key required'})
                
            success = self.ai.add_api_key(provider, api_key)
            return jsonify({
                'success': success,
                'message': f'API key {"added" if success else "failed"} for {provider}'
            })

class GitFileHandler(FileSystemEventHandler):
    """Handle file system events for git integration"""
    
    def __init__(self, git_integration):
        self.git_integration = git_integration
        self.logger = logging.getLogger(__name__)
        
        # File types to monitor
        self.monitored_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
            '.sql', '.md', '.json', '.yaml', '.yml', '.xml', '.sh', '.bat'
        }
        
        # Ignore patterns
        self.ignore_patterns = {
            '__pycache__', '.git', 'node_modules', '.pytest_cache',
            '.vscode', '.idea', 'dist', 'build', '*.pyc', '*.log'
        }
    
    def should_monitor_file(self, file_path: str) -> bool:
        """Check if file should be monitored"""
        path = Path(file_path)
        
        # Check extension
        if path.suffix not in self.monitored_extensions:
            return False
            
        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern in str(path):
                return False
                
        return True
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and self.should_monitor_file(event.src_path):
            self.git_integration._queue_file_change(event.src_path, 'modified')
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and self.should_monitor_file(event.src_path):
            self.git_integration._queue_file_change(event.src_path, 'created')
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory and self.should_monitor_file(event.src_path):
            self.git_integration._queue_file_change(event.src_path, 'deleted')

class GitIntegrationService(StableGitIntegration):
    """Main git integration service"""
    
    def _queue_file_change(self, file_path: str, change_type: str):
        """Queue file change for processing"""
        with self.processing_lock:
            # Check resource limits
            if len(self.file_queue) >= self.limits.max_file_queue:
                self.logger.warning("File queue full, dropping oldest changes")
                self.file_queue = self.file_queue[-self.limits.max_file_queue//2:]
            
            self.file_queue.append({
                'file_path': file_path,
                'change_type': change_type,
                'timestamp': datetime.now()
            })
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT INTO file_changes (file_path, change_type) VALUES (?, ?)',
                    (file_path, change_type)
                )
    
    def _process_file_batch(self):
        """Process batch of file changes"""
        if not self.file_queue or self.resource_monitor.should_throttle():
            return
            
        with self.processing_lock:
            # Take batch of files
            batch_size = min(len(self.file_queue), self.limits.batch_size)
            batch = self.file_queue[:batch_size]
            self.file_queue = self.file_queue[batch_size:]
            
        if not batch:
            return
            
        try:
            # Check if there are actually changes to commit
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if not result.stdout.strip():
                self.logger.info("No git changes to commit")
                return
                
            # Get diff for AI analysis
            diff_result = subprocess.run(
                ['git', 'diff', '--cached', '--unified=1'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Stage all changes
            subprocess.run(
                ['git', 'add', '.'],
                cwd=self.repo_path,
                timeout=30,
                check=True
            )
            
            # Generate commit message
            files = [change['file_path'] for change in batch]
            commit_data = self.ai.generate_commit_message(diff_result.stdout, files)
            
            if not commit_data.get('success'):
                commit_message = f"chore: update {len(files)} files"
                provider = 'fallback'
            else:
                commit_message = commit_data['message']
                provider = commit_data.get('provider', 'unknown')
            
            # Create commit
            commit_result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if commit_result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                commit_hash = hash_result.stdout.strip()
                
                # Store commit in database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        'INSERT INTO commits (commit_hash, message, files_count, provider) VALUES (?, ?, ?, ?)',
                        (commit_hash, commit_message, len(files), provider)
                    )
                
                self.logger.info(f"Committed {len(files)} files: {commit_message}")
                
                # Push to remote (if configured)
                try:
                    subprocess.run(
                        ['git', 'push'],
                        cwd=self.repo_path,
                        timeout=60,
                        check=True
                    )
                    self.logger.info("Changes pushed to remote repository")
                except subprocess.CalledProcessError as e:
                    self.logger.warning(f"Failed to push to remote: {e}")
                    
            else:
                self.logger.error(f"Git commit failed: {commit_result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error processing file batch: {e}")
    
    def _resource_monitoring_loop(self):
        """Background resource monitoring"""
        while self.running:
            try:
                status = self.resource_monitor.check_resources()
                
                # Store resource stats
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        'INSERT INTO resource_stats (memory_mb, cpu_percent) VALUES (?, ?)',
                        (status.get('memory_mb', 0), status.get('cpu_percent', 0))
                    )
                
                # Clean old stats (keep last 24 hours)
                cutoff = datetime.now() - timedelta(hours=24)
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        'DELETE FROM resource_stats WHERE timestamp < ?',
                        (cutoff,)
                    )
                
                if not status['healthy']:
                    self.logger.warning(f"Resource limit exceeded: {status}")
                    time.sleep(60)  # Throttle when unhealthy
                else:
                    time.sleep(self.limits.health_check_interval)
                    
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                time.sleep(60)
    
    def start_monitoring(self):
        """Start file system monitoring"""
        try:
            # Start resource monitoring thread
            resource_thread = threading.Thread(
                target=self._resource_monitoring_loop,
                daemon=True
            )
            resource_thread.start()
            
            # Start file processing scheduler
            schedule.every(self.limits.batch_timeout).seconds.do(self._process_file_batch)
            
            def run_scheduler():
                while self.running:
                    schedule.run_pending()
                    time.sleep(10)
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            
            # Start file system monitoring
            event_handler = GitFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.repo_path), recursive=True)
            self.observer.start()
            
            self.logger.info(f"Git integration monitoring started for {self.repo_path}")
            self.logger.info(f"Resource limits: {self.limits.max_memory_mb}MB memory, {self.limits.max_cpu_percent}% CPU")
            
            # Start Flask API
            self.app.run(host='0.0.0.0', port=9001, debug=False, threaded=True)
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            raise
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix It Fred Git Integration Service')
    parser.add_argument('--repo-path', default='/home/yoyofred_gringosgambit_com/chatterfix-docker',
                      help='Path to git repository')
    parser.add_argument('--config-dir', default='/tmp/fix_it_fred_git',
                      help='Configuration directory')
    
    args = parser.parse_args()
    
    # Initialize and start service
    service = GitIntegrationService(args.repo_path, args.config_dir)
    
    try:
        service.start_monitoring()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Service error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()