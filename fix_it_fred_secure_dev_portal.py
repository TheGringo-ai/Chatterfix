#!/usr/bin/env python3
"""
Fix It Fred Secure Development Portal
Secure access port for development with passcode protection
Only allows VM changes with passcode 9973
"""

import os
import sys
import time
import json
import hashlib
import subprocess
import threading
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from functools import wraps

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, flash
import requests

# Security Configuration
@dataclass
class SecurityConfig:
    access_passcode: str = "9973"
    session_timeout_minutes: int = 30
    max_failed_attempts: int = 3
    lockout_duration_minutes: int = 15
    allowed_commands: List[str] = None
    
    def __post_init__(self):
        if self.allowed_commands is None:
            self.allowed_commands = [
                'git status', 'git log', 'git diff', 'git add', 'git commit', 'git push',
                'ls', 'cat', 'tail', 'head', 'grep', 'find',
                'systemctl status', 'systemctl restart', 'systemctl stop', 'systemctl start',
                'ps aux', 'top', 'htop', 'free', 'df', 'du',
                'python3', 'pip3', 'npm', 'node',
                'mkdir', 'touch', 'cp', 'mv', 'rm',
                'curl', 'wget', 'nano', 'vim'
            ]

class SessionManager:
    """Manage secure sessions with timeout and tracking"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.active_sessions = {}
        self.failed_attempts = {}
        self.locked_ips = {}
        self.logger = logging.getLogger(__name__)
    
    def is_locked(self, ip_address: str) -> bool:
        """Check if IP is locked due to failed attempts"""
        if ip_address in self.locked_ips:
            locked_until = self.locked_ips[ip_address]
            if datetime.now() < locked_until:
                return True
            else:
                del self.locked_ips[ip_address]
        return False
    
    def record_failed_attempt(self, ip_address: str):
        """Record failed login attempt"""
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
        
        self.failed_attempts[ip_address].append(datetime.now())
        
        # Clean old attempts (only count recent ones)
        cutoff = datetime.now() - timedelta(minutes=self.config.lockout_duration_minutes)
        self.failed_attempts[ip_address] = [
            attempt for attempt in self.failed_attempts[ip_address] 
            if attempt > cutoff
        ]
        
        # Lock if too many attempts
        if len(self.failed_attempts[ip_address]) >= self.config.max_failed_attempts:
            lockout_until = datetime.now() + timedelta(minutes=self.config.lockout_duration_minutes)
            self.locked_ips[ip_address] = lockout_until
            self.logger.warning(f"IP {ip_address} locked until {lockout_until}")
    
    def clear_failed_attempts(self, ip_address: str):
        """Clear failed attempts for successful login"""
        if ip_address in self.failed_attempts:
            del self.failed_attempts[ip_address]
    
    def create_session(self, ip_address: str) -> str:
        """Create new secure session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(minutes=self.config.session_timeout_minutes)
        
        self.active_sessions[session_id] = {
            'ip_address': ip_address,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'last_activity': datetime.now()
        }
        
        self.logger.info(f"Session created for {ip_address}: {session_id[:8]}...")
        return session_id
    
    def validate_session(self, session_id: str, ip_address: str) -> bool:
        """Validate session and update activity"""
        if not session_id or session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        
        # Check expiration
        if datetime.now() > session_data['expires_at']:
            del self.active_sessions[session_id]
            return False
        
        # Check IP match
        if session_data['ip_address'] != ip_address:
            return False
        
        # Update last activity
        session_data['last_activity'] = datetime.now()
        return True
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, data in self.active_sessions.items()
            if now > data['expires_at']
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]

class SecureCommandExecutor:
    """Execute commands securely with validation and logging"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.command_history = []
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if command is in allowed list"""
        command_parts = command.strip().split()
        if not command_parts:
            return False
        
        base_command = command_parts[0]
        
        # Check against allowed commands
        for allowed in self.config.allowed_commands:
            if base_command == allowed or command.startswith(allowed + ' '):
                return True
        
        return False
    
    def execute_command(self, command: str, session_id: str, working_dir: str = None) -> Dict[str, Any]:
        """Execute command securely with logging"""
        if not self.is_command_allowed(command):
            self.logger.warning(f"Blocked unauthorized command: {command} (session: {session_id[:8]}...)")
            return {
                'success': False,
                'error': f'Command not allowed: {command.split()[0]}',
                'stdout': '',
                'stderr': 'Security: Command blocked by security policy'
            }
        
        try:
            # Log command execution
            self.command_history.append({
                'command': command,
                'session_id': session_id[:8] + '...',
                'timestamp': datetime.now().isoformat(),
                'working_dir': working_dir or '/tmp'
            })
            
            # Keep only last 100 commands
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]
            
            self.logger.info(f"Executing: {command} (session: {session_id[:8]}...)")
            
            # Execute command with timeout
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir or '/tmp',
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': command
            }
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timeout: {command}")
            return {
                'success': False,
                'error': 'Command timed out (30s limit)',
                'stdout': '',
                'stderr': 'Timeout: Command exceeded 30 second limit'
            }
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': f'Execution error: {str(e)}'
            }

class FixItFredDevPortal:
    """Main development portal application"""
    
    def __init__(self, config_dir: str = "/tmp/fix_it_fred_dev"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.security_config = SecurityConfig()
        self.session_manager = SessionManager(self.security_config)
        self.command_executor = SecureCommandExecutor(self.security_config)
        
        # Setup logging
        self._setup_logging()
        
        # Flask app
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_urlsafe(32)
        
        # Setup routes
        self._setup_routes()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _setup_logging(self):
        """Setup logging"""
        log_file = self.config_dir / "dev_portal.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while True:
                try:
                    self.session_manager.cleanup_expired_sessions()
                    time.sleep(300)  # Clean every 5 minutes
                except Exception as e:
                    self.logger.error(f"Cleanup error: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def require_auth(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
            
            # Check if IP is locked
            if self.session_manager.is_locked(client_ip):
                return jsonify({
                    'success': False,
                    'error': 'IP address locked due to failed attempts',
                    'locked_until': self.session_manager.locked_ips.get(client_ip, datetime.now()).isoformat()
                }), 423
            
            # Check session
            session_id = session.get('session_id')
            if not session_id or not self.session_manager.validate_session(session_id, client_ip):
                return redirect(url_for('login'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    def _setup_routes(self):
        """Setup all Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main portal page"""
            return redirect(url_for('dashboard'))
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page with passcode protection"""
            if request.method == 'POST':
                passcode = request.form.get('passcode', '').strip()
                client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
                
                # Check if IP is locked
                if self.session_manager.is_locked(client_ip):
                    flash('IP address locked due to failed attempts', 'error')
                    return render_template_string(LOGIN_TEMPLATE, locked=True)
                
                # Validate passcode
                if passcode == self.security_config.access_passcode:
                    # Create session
                    session_id = self.session_manager.create_session(client_ip)
                    session['session_id'] = session_id
                    self.session_manager.clear_failed_attempts(client_ip)
                    
                    flash('Access granted', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    # Record failed attempt
                    self.session_manager.record_failed_attempt(client_ip)
                    self.logger.warning(f"Failed login attempt from {client_ip}")
                    flash('Invalid passcode', 'error')
            
            return render_template_string(LOGIN_TEMPLATE)
        
        @self.app.route('/logout')
        def logout():
            """Logout and clear session"""
            session.clear()
            flash('Logged out successfully', 'info')
            return redirect(url_for('login'))
        
        @self.app.route('/dashboard')
        @self.require_auth
        def dashboard():
            """Main dashboard"""
            # Get system info
            try:
                # VM status
                vm_status = self._get_vm_status()
                
                # Git status
                git_status = self._get_git_status()
                
                # Recent commands
                recent_commands = self.command_executor.command_history[-10:]
                
                return render_template_string(DASHBOARD_TEMPLATE, 
                                            vm_status=vm_status,
                                            git_status=git_status,
                                            recent_commands=recent_commands)
            except Exception as e:
                self.logger.error(f"Dashboard error: {e}")
                return f"Dashboard error: {e}", 500
        
        @self.app.route('/api/execute', methods=['POST'])
        @self.require_auth
        def execute_command():
            """Execute command API endpoint"""
            try:
                data = request.get_json()
                command = data.get('command', '').strip()
                working_dir = data.get('working_dir', '/home/yoyofred_gringosgambit_com/chatterfix-docker')
                
                if not command:
                    return jsonify({'success': False, 'error': 'No command provided'})
                
                session_id = session.get('session_id')
                result = self.command_executor.execute_command(command, session_id, working_dir)
                
                return jsonify(result)
                
            except Exception as e:
                self.logger.error(f"Command execution error: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/status')
        @self.require_auth
        def api_status():
            """Get system status"""
            return jsonify({
                'success': True,
                'vm_status': self._get_vm_status(),
                'git_status': self._get_git_status(),
                'session_info': {
                    'active_sessions': len(self.session_manager.active_sessions),
                    'locked_ips': len(self.session_manager.locked_ips)
                }
            })
        
        @self.app.route('/api/git/<action>', methods=['POST'])
        @self.require_auth
        def git_actions(action):
            """Git operations API"""
            try:
                session_id = session.get('session_id')
                working_dir = '/home/yoyofred_gringosgambit_com/chatterfix-docker'
                
                if action == 'status':
                    result = self.command_executor.execute_command('git status', session_id, working_dir)
                elif action == 'add':
                    files = request.json.get('files', '.')
                    result = self.command_executor.execute_command(f'git add {files}', session_id, working_dir)
                elif action == 'commit':
                    message = request.json.get('message', 'Update from Fix It Fred Dev Portal')
                    result = self.command_executor.execute_command(f'git commit -m "{message}"', session_id, working_dir)
                elif action == 'push':
                    result = self.command_executor.execute_command('git push', session_id, working_dir)
                else:
                    return jsonify({'success': False, 'error': f'Unknown git action: {action}'})
                
                return jsonify(result)
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'service': 'Fix It Fred Secure Development Portal',
                'active_sessions': len(self.session_manager.active_sessions),
                'locked_ips': len(self.session_manager.locked_ips),
                'allowed_commands': len(self.security_config.allowed_commands)
            })
    
    def _get_vm_status(self) -> Dict[str, Any]:
        """Get VM status information"""
        try:
            # Get basic system info
            result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
            uptime = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
            memory = result.stdout if result.returncode == 0 else 'unknown'
            
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
            disk = result.stdout if result.returncode == 0 else 'unknown'
            
            return {
                'uptime': uptime,
                'memory': memory,
                'disk': disk,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get git repository status"""
        try:
            working_dir = '/home/yoyofred_gringosgambit_com/chatterfix-docker'
            
            # Git status
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=working_dir, capture_output=True, text=True, timeout=10)
            status = result.stdout if result.returncode == 0 else 'error'
            
            # Last commit
            result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                                  cwd=working_dir, capture_output=True, text=True, timeout=10)
            last_commit = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            return {
                'status': status,
                'last_commit': last_commit,
                'clean': len(status.strip()) == 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Fix It Fred - Secure Development Portal</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .logo { text-align: center; color: #1a73e8; font-size: 24px; font-weight: bold; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="password"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        .btn:hover { background: #1557b0; }
        .alert { padding: 10px; margin-bottom: 20px; border-radius: 5px; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .security-info { font-size: 12px; color: #666; text-align: center; margin-top: 20px; }
        .locked { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔧 Fix It Fred Dev Portal</div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'error' if category == 'error' else 'success' }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% if locked %}
            <div class="alert locked">
                <strong>Access Locked</strong><br>
                Too many failed attempts. Please try again later.
            </div>
        {% else %}
            <form method="POST">
                <div class="form-group">
                    <label for="passcode">Development Access Passcode:</label>
                    <input type="password" id="passcode" name="passcode" required autofocus>
                </div>
                <button type="submit" class="btn">Access Development Portal</button>
            </form>
        {% endif %}
        
        <div class="security-info">
            🔒 Secure development access for Fix It Fred VM<br>
            Maximum 3 failed attempts before lockout
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Fix It Fred - Development Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
        .header { background: #1a73e8; color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 24px; font-weight: bold; }
        .logout-btn { background: rgba(255,255,255,0.2); color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; }
        .logout-btn:hover { background: rgba(255,255,255,0.3); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { margin-top: 0; color: #333; }
        .command-box { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .command-input { display: flex; gap: 10px; margin-bottom: 20px; }
        .command-input input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .execute-btn { padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .execute-btn:hover { background: #218838; }
        .output { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 15px; min-height: 200px; font-family: monospace; white-space: pre-wrap; overflow: auto; }
        .git-actions { display: flex; gap: 10px; margin-bottom: 10px; }
        .git-btn { padding: 8px 15px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .git-btn:hover { background: #5a6268; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .status-item { background: #f8f9fa; padding: 10px; border-radius: 4px; border-left: 4px solid #28a745; }
        .status-value { font-weight: bold; color: #495057; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow: auto; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🔧 Fix It Fred Development Portal</div>
        <a href="/logout" class="logout-btn">Logout</a>
    </div>
    
    <div class="grid">
        <div class="card">
            <h3>📊 VM Status</h3>
            <div class="status-grid">
                <div class="status-item">
                    <div>Uptime</div>
                    <div class="status-value">{{ vm_status.get('uptime', 'Unknown')[:50] }}</div>
                </div>
            </div>
            <pre>{{ vm_status.get('memory', 'Unknown') }}</pre>
        </div>
        
        <div class="card">
            <h3>📋 Git Status</h3>
            <div class="git-actions">
                <button class="git-btn" onclick="gitAction('status')">Status</button>
                <button class="git-btn" onclick="gitAction('add')">Add All</button>
                <button class="git-btn" onclick="gitCommit()">Commit</button>
                <button class="git-btn" onclick="gitAction('push')">Push</button>
            </div>
            <div class="status-item">
                <div>Repository Clean</div>
                <div class="status-value">{{ '✅ Yes' if git_status.get('clean') else '⚠️ Changes detected' }}</div>
            </div>
            <pre>Last Commit: {{ git_status.get('last_commit', 'Unknown') }}</pre>
        </div>
    </div>
    
    <div class="command-box">
        <h3>💻 Command Terminal</h3>
        <div class="command-input">
            <input type="text" id="commandInput" placeholder="Enter command (e.g., ls, git status, systemctl status fix-it-fred)" onkeypress="handleEnter(event)">
            <button class="execute-btn" onclick="executeCommand()">Execute</button>
        </div>
        <div id="commandOutput" class="output">Ready for commands...\nAllowed commands: git, ls, cat, tail, head, systemctl, ps, python3, etc.\nWorking directory: /home/yoyofred_gringosgambit_com/chatterfix-docker</div>
    </div>
    
    {% if recent_commands %}
    <div class="card">
        <h3>📝 Recent Commands</h3>
        {% for cmd in recent_commands|reverse %}
            <div style="margin-bottom: 5px; font-family: monospace; font-size: 12px;">
                <span style="color: #666;">{{ cmd.timestamp[:19] }}</span> 
                <span style="color: #007bff;">{{ cmd.command }}</span>
            </div>
        {% endfor %}
    </div>
    {% endif %}

    <script>
        function handleEnter(event) {
            if (event.key === 'Enter') {
                executeCommand();
            }
        }
        
        function executeCommand() {
            const input = document.getElementById('commandInput');
            const output = document.getElementById('commandOutput');
            const command = input.value.trim();
            
            if (!command) return;
            
            output.textContent = 'Executing: ' + command + '\\n\\nPlease wait...';
            
            fetch('/api/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            })
            .then(response => response.json())
            .then(data => {
                let result = `Command: ${command}\\n`;
                result += `Status: ${data.success ? 'SUCCESS' : 'FAILED'}\\n`;
                result += `Return Code: ${data.returncode || 'N/A'}\\n\\n`;
                
                if (data.stdout) {
                    result += 'STDOUT:\\n' + data.stdout + '\\n\\n';
                }
                
                if (data.stderr) {
                    result += 'STDERR:\\n' + data.stderr + '\\n\\n';
                }
                
                if (data.error) {
                    result += 'ERROR: ' + data.error + '\\n';
                }
                
                output.textContent = result;
                input.value = '';
            })
            .catch(error => {
                output.textContent = 'Network error: ' + error;
            });
        }
        
        function gitAction(action) {
            const output = document.getElementById('commandOutput');
            output.textContent = `Executing git ${action}...`;
            
            fetch(`/api/git/${action}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                let result = `Git ${action}:\\n`;
                result += `Status: ${data.success ? 'SUCCESS' : 'FAILED'}\\n\\n`;
                
                if (data.stdout) {
                    result += data.stdout;
                }
                
                if (data.stderr) {
                    result += '\\nSTDERR:\\n' + data.stderr;
                }
                
                output.textContent = result;
                setTimeout(() => location.reload(), 1000);
            })
            .catch(error => {
                output.textContent = 'Error: ' + error;
            });
        }
        
        function gitCommit() {
            const message = prompt('Enter commit message:', 'Update from Fix It Fred Dev Portal');
            if (!message) return;
            
            const output = document.getElementById('commandOutput');
            output.textContent = 'Creating git commit...';
            
            fetch('/api/git/commit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                let result = `Git commit:\\n`;
                result += `Status: ${data.success ? 'SUCCESS' : 'FAILED'}\\n\\n`;
                
                if (data.stdout) {
                    result += data.stdout;
                }
                
                if (data.stderr) {
                    result += '\\nSTDERR:\\n' + data.stderr;
                }
                
                output.textContent = result;
                setTimeout(() => location.reload(), 1000);
            })
            .catch(error => {
                output.textContent = 'Error: ' + error;
            });
        }
        
        // Auto-refresh status every 30 seconds
        setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    console.log('Status updated:', data);
                })
                .catch(error => console.log('Status update failed:', error));
        }, 30000);
    </script>
</body>
</html>
'''

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix It Fred Secure Development Portal')
    parser.add_argument('--port', type=int, default=9002, help='Port to run on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--config-dir', default='/tmp/fix_it_fred_dev', help='Configuration directory')
    
    args = parser.parse_args()
    
    # Initialize portal
    portal = FixItFredDevPortal(args.config_dir)
    
    try:
        print(f"🚀 Starting Fix It Fred Secure Development Portal on {args.host}:{args.port}")
        print(f"🔒 Access passcode: 9973")
        print(f"🌐 Access at: http://{args.host}:{args.port}")
        
        portal.app.run(host=args.host, port=args.port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()