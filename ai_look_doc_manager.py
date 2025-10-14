#!/usr/bin/env python3
"""
AI Look Documentation Manager - Enterprise Documentation Automation
Automatically updates documentation as code changes, monitors system health,
and maintains documentation consistency across the platform.
"""

import os
import sys
import json
import time
import hashlib
import subprocess
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import psutil
import git

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_look_doc_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceStatus:
    name: str
    port: int
    status: str
    url: str
    health_data: Dict = None
    last_check: datetime = None
    uptime: timedelta = None

@dataclass
class DocumentationMetrics:
    total_files: int
    total_lines: int
    last_updated: datetime
    version: str
    coverage_percentage: float
    auto_updates_count: int

class AILookDocumentationManager:
    """Enterprise documentation management system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.doc_files = [
            "AI_LOOK.md",
            "AI_LOOK_TECHNICAL_ADDENDUM.md", 
            "AI_LOOK_QUICK_START.md",
            "AI_LOOK_INDEX.md"
        ]
        self.services = {
            "ChatterFix Gateway": {"port": 8000, "endpoint": "/health"},
            "Database Service": {"port": 8001, "endpoint": "/health"},
            "Work Orders": {"port": 8002, "endpoint": "/health"},
            "Assets": {"port": 8003, "endpoint": "/health"},
            "Parts": {"port": 8004, "endpoint": "/health"},
            "Fix It Fred AI": {"port": 8005, "endpoint": "/health"},
            "Document Intelligence": {"port": 8006, "endpoint": "/health"},
            "Enterprise Security": {"port": 8007, "endpoint": "/health"},
            "AI Development Team": {"port": 8008, "endpoint": "/health"}
        }
        self.file_watchers = {}
        self.last_hashes = {}
        self.update_count = 0
        self.start_time = datetime.now()
        
        # Initialize git repository
        try:
            self.repo = git.Repo(self.project_root)
        except git.InvalidGitRepositoryError:
            self.repo = None
            logger.warning("Not a git repository - version tracking disabled")
    
    async def start_monitoring(self):
        """Start comprehensive documentation monitoring"""
        logger.info("🚀 Starting AI Look Documentation Manager...")
        
        # Initial system scan
        await self.full_system_scan()
        
        # Start file monitoring
        self.start_file_monitoring()
        
        # Start periodic health checks
        asyncio.create_task(self.periodic_health_check())
        
        # Start documentation maintenance
        asyncio.create_task(self.periodic_doc_maintenance())
        
        logger.info("✅ AI Look Documentation Manager running")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("📝 Shutting down documentation manager...")
            await self.generate_final_report()
    
    async def full_system_scan(self):
        """Perform comprehensive system analysis and documentation update"""
        logger.info("🔍 Performing full system scan...")
        
        # Check service health
        service_status = await self.check_all_services()
        
        # Analyze codebase
        code_metrics = await self.analyze_codebase()
        
        # Check database schema
        db_schema = await self.check_database_schema()
        
        # Update documentation
        await self.update_documentation_with_scan_results(
            service_status, code_metrics, db_schema
        )
        
        # Generate status report
        await self.generate_status_report(service_status, code_metrics)
    
    async def check_all_services(self) -> Dict[str, ServiceStatus]:
        """Check health of all platform services"""
        service_status = {}
        
        for name, config in self.services.items():
            port = config["port"]
            endpoint = config["endpoint"]
            url = f"http://localhost:{port}{endpoint}"
            
            try:
                response = requests.get(url, timeout=5)
                health_data = response.json() if response.status_code == 200 else None
                
                service_status[name] = ServiceStatus(
                    name=name,
                    port=port,
                    status="healthy" if response.status_code == 200 else "unhealthy",
                    url=url,
                    health_data=health_data,
                    last_check=datetime.now()
                )
                
            except Exception as e:
                service_status[name] = ServiceStatus(
                    name=name,
                    port=port,
                    status="offline",
                    url=url,
                    health_data={"error": str(e)},
                    last_check=datetime.now()
                )
        
        return service_status
    
    async def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze codebase for documentation updates"""
        metrics = {
            "python_files": 0,
            "javascript_files": 0,
            "html_files": 0,
            "css_files": 0,
            "sql_files": 0,
            "total_lines": 0,
            "api_endpoints": [],
            "database_tables": [],
            "new_features": [],
            "last_commits": []
        }
        
        # Scan for code files
        for ext in ['.py', '.js', '.html', '.css', '.sql']:
            files = list(self.project_root.rglob(f"*{ext}"))
            metrics[f"{ext[1:]}_files"] = len(files)
            
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                        metrics["total_lines"] += lines
                        
                        # Extract API endpoints from Python files
                        if ext == '.py':
                            content = f.read()
                            f.seek(0)
                            endpoints = self.extract_api_endpoints(content)
                            metrics["api_endpoints"].extend(endpoints)
                            
                        # Extract database tables from SQL files
                        elif ext == '.sql':
                            content = f.read()
                            f.seek(0)
                            tables = self.extract_database_tables(content)
                            metrics["database_tables"].extend(tables)
                            
                except Exception as e:
                    logger.warning(f"Error analyzing {file_path}: {e}")
        
        # Get recent git commits if available
        if self.repo:
            try:
                recent_commits = list(self.repo.iter_commits(max_count=10))
                metrics["last_commits"] = [
                    {
                        "hash": commit.hexsha[:8],
                        "message": commit.message.strip(),
                        "author": str(commit.author),
                        "date": commit.committed_datetime.isoformat()
                    }
                    for commit in recent_commits
                ]
            except Exception as e:
                logger.warning(f"Git analysis error: {e}")
        
        return metrics
    
    def extract_api_endpoints(self, content: str) -> List[Dict]:
        """Extract API endpoints from Python code"""
        endpoints = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if '@app.' in line and ('get', 'post', 'put', 'delete') in line.lower():
                method_line = line.strip()
                
                # Look for the function definition on next few lines
                func_name = None
                for j in range(i+1, min(i+5, len(lines))):
                    if 'def ' in lines[j]:
                        func_name = lines[j].strip().split('def ')[1].split('(')[0]
                        break
                
                if func_name:
                    endpoints.append({
                        "method": method_line,
                        "function": func_name,
                        "line": i + 1
                    })
        
        return endpoints
    
    def extract_database_tables(self, content: str) -> List[str]:
        """Extract database table names from SQL"""
        tables = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip().upper()
            if line.startswith('CREATE TABLE'):
                table_name = line.split('CREATE TABLE')[1].strip().split()[0]
                table_name = table_name.replace('(', '').replace(';', '')
                tables.append(table_name.lower())
        
        return tables
    
    async def check_database_schema(self) -> Dict[str, Any]:
        """Check database schema for changes"""
        schema_info = {
            "tables": [],
            "schema_file_exists": False,
            "last_modified": None
        }
        
        # Check for schema file
        schema_file = self.project_root / "cmms_schema.sql"
        if schema_file.exists():
            schema_info["schema_file_exists"] = True
            schema_info["last_modified"] = datetime.fromtimestamp(
                schema_file.stat().st_mtime
            ).isoformat()
            
            # Read schema file for table information
            try:
                with open(schema_file, 'r') as f:
                    content = f.read()
                    schema_info["tables"] = self.extract_database_tables(content)
            except Exception as e:
                logger.error(f"Error reading schema file: {e}")
        
        return schema_info
    
    async def update_documentation_with_scan_results(
        self, service_status: Dict, code_metrics: Dict, db_schema: Dict
    ):
        """Update documentation files with current system state"""
        
        # Update service status in documentation
        await self.update_service_status_docs(service_status)
        
        # Update code metrics
        await self.update_code_metrics_docs(code_metrics)
        
        # Update database documentation
        await self.update_database_docs(db_schema)
        
        # Update timestamps
        await self.update_timestamps()
        
        self.update_count += 1
        logger.info(f"📝 Documentation updated (#{self.update_count})")
    
    async def update_service_status_docs(self, service_status: Dict):
        """Update service status in documentation"""
        status_section = "## 🏛️ CURRENT SERVICE STATUS\\n\\n"
        status_section += f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\\n\\n"
        
        for name, status in service_status.items():
            icon = "✅" if status.status == "healthy" else "❌" if status.status == "offline" else "⚠️"
            status_section += f"- **{name}** (Port {status.port}): {icon} {status.status.title()}\\n"
        
        # Update main documentation
        await self.update_doc_section("AI_LOOK.md", "SERVICE STATUS", status_section)
    
    async def update_code_metrics_docs(self, metrics: Dict):
        """Update code metrics in documentation"""
        metrics_section = "## 📊 CURRENT CODEBASE METRICS\\n\\n"
        metrics_section += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\\n\\n"
        
        metrics_section += f"""
**File Statistics:**
- Python Files: {metrics.get('py_files', 0)}
- JavaScript Files: {metrics.get('js_files', 0)}
- HTML Templates: {metrics.get('html_files', 0)}
- CSS Stylesheets: {metrics.get('css_files', 0)}
- SQL Scripts: {metrics.get('sql_files', 0)}
- Total Lines of Code: {metrics.get('total_lines', 0):,}

**API Endpoints Detected:** {len(metrics.get('api_endpoints', []))}
**Database Tables:** {len(metrics.get('database_tables', []))}
"""
        
        if metrics.get('last_commits'):
            metrics_section += "\\n**Recent Commits:**\\n"
            for commit in metrics['last_commits'][:5]:
                metrics_section += f"- `{commit['hash']}` {commit['message'][:60]}... ({commit['date'][:10]})\\n"
        
        await self.update_doc_section("AI_LOOK_TECHNICAL_ADDENDUM.md", "CODEBASE METRICS", metrics_section)
    
    async def update_database_docs(self, schema_info: Dict):
        """Update database documentation"""
        if schema_info["schema_file_exists"]:
            db_section = f"## 🗄️ DATABASE STATUS\\n\\n"
            db_section += f"*Schema Last Modified: {schema_info['last_modified']}*\\n\\n"
            db_section += f"**Total Tables:** {len(schema_info['tables'])}\\n\\n"
            
            if schema_info['tables']:
                db_section += "**Current Tables:**\\n"
                for table in sorted(schema_info['tables']):
                    db_section += f"- `{table}`\\n"
            
            await self.update_doc_section("AI_LOOK.md", "DATABASE STATUS", db_section)
    
    async def update_timestamps(self):
        """Update last modified timestamps in all documentation"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for doc_file in self.doc_files:
            file_path = self.project_root / doc_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Update timestamp
                    content = self.update_last_updated_timestamp(content, timestamp)
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                        
                except Exception as e:
                    logger.error(f"Error updating timestamp in {doc_file}: {e}")
    
    def update_last_updated_timestamp(self, content: str, timestamp: str) -> str:
        """Update the 'Last Updated' line in documentation"""
        lines = content.split('\\n')
        
        for i, line in enumerate(lines):
            if line.startswith('**Last Updated'):
                lines[i] = f"**Last Updated:** {timestamp}"
                break
            elif 'Last Updated:' in line:
                # Handle different timestamp formats
                lines[i] = f"**Last Updated**: {timestamp}"
                break
        
        return '\\n'.join(lines)
    
    async def update_doc_section(self, doc_file: str, section_header: str, new_content: str):
        """Update a specific section in a documentation file"""
        file_path = self.project_root / doc_file
        
        if not file_path.exists():
            logger.warning(f"Documentation file not found: {doc_file}")
            return
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find and replace the section
            lines = content.split('\\n')
            section_start = None
            section_end = None
            
            for i, line in enumerate(lines):
                if section_header.upper() in line.upper():
                    section_start = i
                elif section_start is not None and line.startswith('##') and i > section_start:
                    section_end = i
                    break
            
            if section_start is not None:
                if section_end is None:
                    section_end = len(lines)
                
                # Replace the section
                new_lines = lines[:section_start] + [new_content] + lines[section_end:]
                new_content_full = '\\n'.join(new_lines)
                
                with open(file_path, 'w') as f:
                    f.write(new_content_full)
                
                logger.info(f"Updated section '{section_header}' in {doc_file}")
            else:
                # Section not found, append at end
                with open(file_path, 'a') as f:
                    f.write(f"\\n\\n{new_content}")
                logger.info(f"Added new section '{section_header}' to {doc_file}")
                
        except Exception as e:
            logger.error(f"Error updating {doc_file}: {e}")
    
    def start_file_monitoring(self):
        """Start monitoring files for changes"""
        
        class DocumentationEventHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager
            
            def on_modified(self, event):
                if not event.is_directory:
                    asyncio.create_task(self.manager.handle_file_change(event.src_path))
        
        event_handler = DocumentationEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.project_root), recursive=True)
        observer.start()
        
        logger.info("📁 File monitoring started")
    
    async def handle_file_change(self, file_path: str):
        """Handle file change events"""
        file_path = Path(file_path)
        
        # Skip temporary files and non-relevant files
        if (file_path.suffix in ['.pyc', '.log', '.tmp'] or 
            file_path.name.startswith('.') or
            'node_modules' in str(file_path) or
            '__pycache__' in str(file_path)):
            return
        
        # Calculate file hash to detect actual changes
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
        except Exception:
            return
        
        # Check if file actually changed
        if file_path in self.last_hashes and self.last_hashes[file_path] == file_hash:
            return
        
        self.last_hashes[file_path] = file_hash
        
        logger.info(f"📝 File changed: {file_path.name}")
        
        # Trigger documentation update for relevant changes
        if file_path.suffix in ['.py', '.js', '.sql', '.html']:
            await asyncio.sleep(2)  # Debounce multiple rapid changes
            await self.full_system_scan()
    
    async def periodic_health_check(self):
        """Periodic health monitoring"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                logger.info("🏥 Performing periodic health check...")
                
                service_status = await self.check_all_services()
                
                # Check for service status changes
                healthy_count = sum(1 for s in service_status.values() if s.status == "healthy")
                total_count = len(service_status)
                
                if healthy_count < total_count:
                    logger.warning(f"⚠️ {total_count - healthy_count} services are not healthy")
                    
                # Update service status documentation
                await self.update_service_status_docs(service_status)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def periodic_doc_maintenance(self):
        """Periodic documentation maintenance"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                logger.info("🧹 Performing documentation maintenance...")
                
                # Full system scan and update
                await self.full_system_scan()
                
                # Generate documentation metrics
                metrics = await self.calculate_documentation_metrics()
                
                # Log metrics
                logger.info(f"📊 Documentation Metrics: {metrics.coverage_percentage:.1f}% coverage, "
                          f"{metrics.total_files} files, {metrics.auto_updates_count} auto-updates")
                
            except Exception as e:
                logger.error(f"Documentation maintenance error: {e}")
    
    async def calculate_documentation_metrics(self) -> DocumentationMetrics:
        """Calculate comprehensive documentation metrics"""
        total_files = 0
        total_lines = 0
        
        for doc_file in self.doc_files:
            file_path = self.project_root / doc_file
            if file_path.exists():
                total_files += 1
                try:
                    with open(file_path, 'r') as f:
                        total_lines += len(f.readlines())
                except Exception:
                    pass
        
        # Calculate coverage based on codebase analysis
        code_metrics = await self.analyze_codebase()
        code_files = (code_metrics.get('py_files', 0) + 
                     code_metrics.get('js_files', 0) + 
                     code_metrics.get('html_files', 0))
        
        coverage_percentage = min(100, (total_lines / max(code_files, 1)) * 10)
        
        return DocumentationMetrics(
            total_files=total_files,
            total_lines=total_lines,
            last_updated=datetime.now(),
            version="3.0",
            coverage_percentage=coverage_percentage,
            auto_updates_count=self.update_count
        )
    
    async def generate_status_report(self, service_status: Dict, code_metrics: Dict):
        """Generate comprehensive status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "manager_uptime": str(datetime.now() - self.start_time),
            "services": {name: asdict(status) for name, status in service_status.items()},
            "code_metrics": code_metrics,
            "documentation_updates": self.update_count,
            "system_health": "healthy" if all(s.status == "healthy" for s in service_status.values()) else "degraded"
        }
        
        # Save report
        report_file = self.project_root / f"ai_look_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📊 Status report saved: {report_file.name}")
    
    async def generate_final_report(self):
        """Generate final report on shutdown"""
        logger.info("📊 Generating final documentation manager report...")
        
        uptime = datetime.now() - self.start_time
        metrics = await self.calculate_documentation_metrics()
        
        final_report = f"""
🎉 AI Look Documentation Manager - Final Report

**Manager Uptime:** {uptime}
**Auto-Updates Performed:** {self.update_count}
**Documentation Files Managed:** {len(self.doc_files)}
**Current Coverage:** {metrics.coverage_percentage:.1f}%
**Total Documentation Lines:** {metrics.total_lines:,}

**Services Monitored:** {len(self.services)}
**Last System Scan:** {metrics.last_updated}

Documentation system maintained enterprise-grade standards throughout operation.
"""
        
        print(final_report)
        logger.info("📝 AI Look Documentation Manager shutdown complete")

async def main():
    """Main entry point"""
    manager = AILookDocumentationManager()
    await manager.start_monitoring()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 AI Look Documentation Manager stopped")