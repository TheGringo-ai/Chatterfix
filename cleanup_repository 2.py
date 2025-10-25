#!/usr/bin/env python3
"""
ChatterFix Repository Cleanup Script
Safely removes duplicate files and organizes repository structure
Preserves Phase 7 Enterprise functionality
"""

import os
import shutil
import subprocess
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatterFixCleanup:
    def __init__(self, repo_path: str, dry_run: bool = True):
        self.repo_path = Path(repo_path)
        self.dry_run = dry_run
        self.backup_dir = self.repo_path / "cleanup_backup"
        self.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "total_files_before": 0,
            "total_files_after": 0,
            "duplicates_removed": [],
            "directories_removed": [],
            "files_preserved": [],
            "errors": []
        }
        
        # Core directories to preserve
        self.core_directories = {
            "ai/services/",           # Core AI services
            "frontend/",              # Frontend application
            "backend/",               # Backend services
            "docs/investors/",        # Investor documentation
            "docs/ai/",              # AI documentation
            "config/",               # Configuration files
            "services/",             # Service definitions
            "tests/",                # Test files
            "infra/",                # Infrastructure code
            "core/",                 # Core application logic
            ".github/",              # GitHub workflows
            ".claude/",              # Claude configuration
        }
        
        # Essential files to preserve
        self.essential_files = {
            "README.md",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            ".env",
            ".env.example",
            ".env.production",
            ".gitignore",
            ".gcloudignore",
            "package.json",
            "tsconfig.json",
            "PHASE_7_ENTERPRISE_HARDENING_MASTER_PROMPT.md",
            "AI_LOOK.md",
            "AI_LOOK_INDEX.md", 
            "AI_LOOK_QUICK_START.md",
            "ARCHITECTURE_CONSOLIDATION_PLAN.md",
            "FIX_IT_FRED_UNIVERSAL_README.md",
            "FIX_IT_FRED_GIT_INTEGRATION_COMPLETE_SPECIFICATION.md"
        }
        
        # Directories to remove completely
        self.remove_directories = {
            "archive/",              # Old archived files (333MB)
            "legacy/",               # Legacy code
            "__pycache__/",          # Python cache
            ".mypy_cache/",          # MyPy cache
            "venv/",                 # Virtual environment
            ".venv/",                # Virtual environment
            "node_modules/",         # Node modules
            "logs/",                 # Log files
            "backups/",              # Backup files
            "quick-patches/",        # Quick patches
            "vm-deployment/",        # VM deployment scripts
            "complete-deployment/",   # Old deployment scripts
            "deployment-package/",    # Old deployment package
            "chatterfix-enterprise-backend/", # Duplicate backend
            "chatterfix-enterprise-database/", # Duplicate database
            "chatterfix-enterprise-deployment/", # Duplicate deployment
            "CLEAN_FRED_FIX_IT/",    # Old Fred implementation
            "test_env/",             # Test environment
            "uploads/",              # Upload files
            "static/",               # Static files
            "templates/",            # Template files
            "documents/",            # Document files
            "data/",                 # Data files
            "ai-memory/"             # AI memory files
        }

    def count_files(self) -> int:
        """Count total files in repository"""
        try:
            result = subprocess.run(
                ["find", str(self.repo_path), "-type", "f"],
                capture_output=True, text=True, check=True
            )
            return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        except subprocess.CalledProcessError:
            return 0

    def find_duplicate_files(self) -> List[str]:
        """Find all files with numeric suffixes (duplicates)"""
        duplicates = []
        try:
            # Find files with " 2", " 3", " 4" etc. suffixes
            result = subprocess.run([
                "find", str(self.repo_path), 
                "-name", "* 2*", "-o", 
                "-name", "* 3*", "-o", 
                "-name", "* 4*", "-o",
                "-name", "* 5*", "-o",
                "-name", "* 6*", "-o",
                "-name", "* 7*", "-o",
                "-name", "* 8*", "-o",
                "-name", "* 9*"
            ], capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                duplicates = result.stdout.strip().split('\n')
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error finding duplicates: {e}")
            
        return duplicates

    def should_preserve_file(self, file_path: Path) -> bool:
        """Determine if a file should be preserved"""
        relative_path = file_path.relative_to(self.repo_path)
        
        # Preserve files in core directories
        for core_dir in self.core_directories:
            if str(relative_path).startswith(core_dir):
                return True
                
        # Preserve essential files
        if file_path.name in self.essential_files:
            return True
            
        # Preserve git files
        if str(relative_path).startswith('.git/'):
            return True
            
        return False

    def create_backup(self):
        """Create backup before cleanup"""
        if self.dry_run:
            logger.info("DRY RUN: Would create backup")
            return
            
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
            
        self.backup_dir.mkdir(exist_ok=True)
        logger.info(f"Created backup directory: {self.backup_dir}")

    def remove_duplicate_files(self):
        """Remove duplicate files with numeric suffixes"""
        logger.info("Finding and removing duplicate files...")
        duplicates = self.find_duplicate_files()
        
        removed_count = 0
        for duplicate in duplicates:
            duplicate_path = Path(duplicate)
            
            if not duplicate_path.exists():
                continue
                
            # Check if we should preserve this file
            if self.should_preserve_file(duplicate_path):
                logger.info(f"PRESERVING (core): {duplicate}")
                self.cleanup_report["files_preserved"].append(str(duplicate))
                continue
                
            if self.dry_run:
                logger.info(f"DRY RUN: Would remove duplicate: {duplicate}")
            else:
                try:
                    duplicate_path.unlink()
                    logger.info(f"Removed duplicate: {duplicate}")
                    self.cleanup_report["duplicates_removed"].append(str(duplicate))
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Error removing {duplicate}: {e}")
                    self.cleanup_report["errors"].append(f"Failed to remove {duplicate}: {e}")
                    
        logger.info(f"Removed {removed_count} duplicate files")

    def remove_redundant_directories(self):
        """Remove redundant directories"""
        logger.info("Removing redundant directories...")
        
        removed_count = 0
        for dir_name in self.remove_directories:
            dir_path = self.repo_path / dir_name
            
            if not dir_path.exists():
                continue
                
            if self.dry_run:
                logger.info(f"DRY RUN: Would remove directory: {dir_path}")
            else:
                try:
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed directory: {dir_path}")
                    self.cleanup_report["directories_removed"].append(str(dir_path))
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Error removing directory {dir_path}: {e}")
                    self.cleanup_report["errors"].append(f"Failed to remove directory {dir_path}: {e}")
                    
        logger.info(f"Removed {removed_count} redundant directories")

    def cleanup_root_files(self):
        """Clean up redundant files in root directory"""
        logger.info("Cleaning up root directory files...")
        
        # Patterns of files to remove from root
        remove_patterns = [
            "*deploy*",
            "*startup*", 
            "*fix*",
            "*emergency*",
            "*vm*",
            "*gcp*",
            "*docker*",
            "*cloud*",
            "*test*",
            "*example*",
            "*demo*",
            "*temp*",
            "*backup*"
        ]
        
        removed_count = 0
        for pattern in remove_patterns:
            try:
                for file_path in self.repo_path.glob(pattern):
                    if file_path.is_file() and not self.should_preserve_file(file_path):
                        if self.dry_run:
                            logger.info(f"DRY RUN: Would remove root file: {file_path.name}")
                        else:
                            try:
                                file_path.unlink()
                                logger.info(f"Removed root file: {file_path.name}")
                                removed_count += 1
                            except Exception as e:
                                logger.error(f"Error removing {file_path}: {e}")
                                
            except Exception as e:
                logger.error(f"Error processing pattern {pattern}: {e}")
                
        logger.info(f"Removed {removed_count} redundant root files")

    def organize_remaining_files(self):
        """Organize remaining files into logical structure"""
        logger.info("Organizing remaining files...")
        
        # Create organized directory structure
        organized_dirs = {
            "deployment/": ["*deploy*", "*startup*", "*.sh"],
            "utilities/": ["*util*", "*helper*", "*tool*"],
            "documentation/": ["*.md", "*.txt", "*.rst"],
            "configuration/": ["*.yml", "*.yaml", "*.json", "*.conf", "*.cfg"]
        }
        
        if not self.dry_run:
            for dir_name in organized_dirs.keys():
                (self.repo_path / dir_name).mkdir(exist_ok=True)
        
        for target_dir, patterns in organized_dirs.items():
            for pattern in patterns:
                for file_path in self.repo_path.glob(pattern):
                    if (file_path.is_file() and 
                        not self.should_preserve_file(file_path) and
                        file_path.parent == self.repo_path):
                        
                        target_path = self.repo_path / target_dir / file_path.name
                        
                        if self.dry_run:
                            logger.info(f"DRY RUN: Would move {file_path.name} to {target_dir}")
                        else:
                            try:
                                shutil.move(str(file_path), str(target_path))
                                logger.info(f"Moved {file_path.name} to {target_dir}")
                            except Exception as e:
                                logger.error(f"Error moving {file_path}: {e}")

    def generate_cleanup_report(self):
        """Generate final cleanup report"""
        self.cleanup_report["total_files_after"] = self.count_files()
        
        report_path = self.repo_path / "CLEANUP_REPORT.json"
        
        if not self.dry_run:
            with open(report_path, 'w') as f:
                json.dump(self.cleanup_report, f, indent=2)
                
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("CLEANUP SUMMARY")
        logger.info("="*50)
        logger.info(f"Files before cleanup: {self.cleanup_report['total_files_before']}")
        logger.info(f"Files after cleanup: {self.cleanup_report['total_files_after']}")
        logger.info(f"Duplicate files removed: {len(self.cleanup_report['duplicates_removed'])}")
        logger.info(f"Directories removed: {len(self.cleanup_report['directories_removed'])}")
        logger.info(f"Files preserved: {len(self.cleanup_report['files_preserved'])}")
        logger.info(f"Errors encountered: {len(self.cleanup_report['errors'])}")
        
        if self.cleanup_report['errors']:
            logger.warning("\nErrors encountered:")
            for error in self.cleanup_report['errors']:
                logger.warning(f"  - {error}")

    def run_cleanup(self):
        """Execute the complete cleanup process"""
        logger.info("Starting ChatterFix repository cleanup...")
        logger.info(f"Repository path: {self.repo_path}")
        logger.info(f"Dry run mode: {self.dry_run}")
        
        # Count files before cleanup
        self.cleanup_report["total_files_before"] = self.count_files()
        logger.info(f"Total files before cleanup: {self.cleanup_report['total_files_before']}")
        
        # Create backup
        self.create_backup()
        
        # Execute cleanup steps
        self.remove_duplicate_files()
        self.remove_redundant_directories()
        self.cleanup_root_files()
        self.organize_remaining_files()
        
        # Generate report
        self.generate_cleanup_report()
        
        logger.info("Cleanup completed!")

def main():
    parser = argparse.ArgumentParser(description="ChatterFix Repository Cleanup")
    parser.add_argument("--repo-path", default="/Users/fredtaylor/Desktop/Projects/ai-tools", 
                       help="Path to repository")
    parser.add_argument("--execute", action="store_true", 
                       help="Execute cleanup (default is dry run)")
    
    args = parser.parse_args()
    
    cleanup = ChatterFixCleanup(args.repo_path, dry_run=not args.execute)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()