#!/usr/bin/env python3
"""
ChatterFix Repository Cleanup Validation Script
Ensures Phase 7 Enterprise functionality is preserved after cleanup
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class CleanupValidator:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.validation_report = {
            "timestamp": "2025-10-22",
            "repository_path": str(repo_path),
            "phase7_readiness": False,
            "core_services_present": False,
            "frontend_intact": False,
            "backend_intact": False,
            "infrastructure_preserved": False,
            "documentation_complete": False,
            "git_history_intact": False,
            "essential_files_present": [],
            "missing_critical_files": [],
            "validation_errors": [],
            "recommendations": []
        }

    def validate_essential_files(self) -> bool:
        """Validate that essential Phase 7 files are present"""
        essential_files = [
            "PHASE_7_ENTERPRISE_HARDENING_MASTER_PROMPT.md",
            "ai/services/fix_it_fred_service.py",
            "ai/services/ai_brain_service.py", 
            "ai_brain_health_monitor.py",
            "ai_brain_sync.py",
            "fix_it_fred_diy.py",
            "frontend/src/App.tsx",
            "README.md",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml"
        ]
        
        present_files = []
        missing_files = []
        
        for file_path in essential_files:
            full_path = self.repo_path / file_path
            if full_path.exists():
                present_files.append(file_path)
            else:
                missing_files.append(file_path)
                
        self.validation_report["essential_files_present"] = present_files
        self.validation_report["missing_critical_files"] = missing_files
        
        return len(missing_files) == 0

    def validate_core_services(self) -> bool:
        """Validate core AI services directory structure"""
        services_dir = self.repo_path / "ai" / "services"
        
        if not services_dir.exists():
            self.validation_report["validation_errors"].append("ai/services/ directory missing")
            return False
            
        required_services = [
            "fix_it_fred_service.py",
            "ai_brain_service.py"
        ]
        
        missing_services = []
        for service in required_services:
            if not (services_dir / service).exists():
                missing_services.append(f"ai/services/{service}")
                
        if missing_services:
            self.validation_report["validation_errors"].extend(
                [f"Missing service: {service}" for service in missing_services]
            )
            return False
            
        self.validation_report["core_services_present"] = True
        return True

    def validate_frontend(self) -> bool:
        """Validate frontend structure"""
        frontend_dir = self.repo_path / "frontend"
        
        if not frontend_dir.exists():
            self.validation_report["validation_errors"].append("frontend/ directory missing")
            return False
            
        required_frontend_files = [
            "src/App.tsx",
            "src/EnterpriseLayout.tsx"
        ]
        
        missing_files = []
        for file_path in required_frontend_files:
            if not (frontend_dir / file_path).exists():
                missing_files.append(f"frontend/{file_path}")
                
        if missing_files:
            self.validation_report["validation_errors"].extend(
                [f"Missing frontend file: {file_path}" for file_path in missing_files]
            )
            return False
            
        self.validation_report["frontend_intact"] = True
        return True

    def validate_backend(self) -> bool:
        """Validate backend structure"""
        backend_dir = self.repo_path / "backend"
        
        if not backend_dir.exists():
            self.validation_report["validation_errors"].append("backend/ directory missing")
            return False
            
        self.validation_report["backend_intact"] = True
        return True

    def validate_infrastructure(self) -> bool:
        """Validate infrastructure code preservation"""
        infra_dir = self.repo_path / "infra"
        config_dir = self.repo_path / "config"
        
        if not infra_dir.exists() and not config_dir.exists():
            self.validation_report["validation_errors"].append(
                "Neither infra/ nor config/ directories found"
            )
            return False
            
        self.validation_report["infrastructure_preserved"] = True
        return True

    def validate_documentation(self) -> bool:
        """Validate documentation preservation"""
        docs_dir = self.repo_path / "docs"
        
        if not docs_dir.exists():
            self.validation_report["validation_errors"].append("docs/ directory missing")
            return False
            
        critical_docs = [
            "docs/investors",
            "docs/ai"
        ]
        
        missing_docs = []
        for doc_path in critical_docs:
            if not (self.repo_path / doc_path).exists():
                missing_docs.append(doc_path)
                
        if missing_docs:
            self.validation_report["validation_errors"].extend(
                [f"Missing documentation: {doc}" for doc in missing_docs]
            )
            return False
            
        self.validation_report["documentation_complete"] = True
        return True

    def validate_git_history(self) -> bool:
        """Validate git history preservation"""
        git_dir = self.repo_path / ".git"
        
        if not git_dir.exists():
            self.validation_report["validation_errors"].append(".git directory missing")
            return False
            
        try:
            # Check if we can access git log
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                self.validation_report["validation_errors"].append("Git history appears empty")
                return False
                
        except subprocess.CalledProcessError:
            self.validation_report["validation_errors"].append("Cannot access git history")
            return False
            
        self.validation_report["git_history_intact"] = True
        return True

    def check_file_count(self) -> Dict[str, int]:
        """Check current file count"""
        try:
            result = subprocess.run(
                ["find", str(self.repo_path), "-type", "f"],
                capture_output=True,
                text=True,
                check=True
            )
            total_files = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Check for remaining duplicates
            duplicate_result = subprocess.run([
                "find", str(self.repo_path),
                "-name", "* 2*", "-o",
                "-name", "* 3*", "-o", 
                "-name", "* 4*"
            ], capture_output=True, text=True, check=True)
            
            remaining_duplicates = len(duplicate_result.stdout.strip().split('\n')) if duplicate_result.stdout.strip() else 0
            
            return {
                "total_files": total_files,
                "remaining_duplicates": remaining_duplicates
            }
            
        except subprocess.CalledProcessError:
            return {"total_files": 0, "remaining_duplicates": 0}

    def generate_recommendations(self):
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if not self.validation_report["core_services_present"]:
            recommendations.append("Restore ai/services/ directory with core AI services")
            
        if not self.validation_report["frontend_intact"]:
            recommendations.append("Restore frontend/ directory structure")
            
        if not self.validation_report["backend_intact"]:
            recommendations.append("Restore backend/ directory")
            
        if not self.validation_report["infrastructure_preserved"]:
            recommendations.append("Restore infrastructure configuration files")
            
        if not self.validation_report["documentation_complete"]:
            recommendations.append("Restore critical documentation directories")
            
        if not self.validation_report["git_history_intact"]:
            recommendations.append("Restore .git directory and commit history")
            
        if self.validation_report["missing_critical_files"]:
            recommendations.append("Restore missing critical files from backup")
            
        self.validation_report["recommendations"] = recommendations

    def run_validation(self) -> bool:
        """Run complete validation suite"""
        print("🔍 Running Phase 7 Enterprise Cleanup Validation...")
        print("=" * 50)
        
        # Run all validation checks
        checks = [
            ("Essential Files", self.validate_essential_files),
            ("Core Services", self.validate_core_services),
            ("Frontend Structure", self.validate_frontend),
            ("Backend Structure", self.validate_backend),
            ("Infrastructure", self.validate_infrastructure),
            ("Documentation", self.validate_documentation),
            ("Git History", self.validate_git_history)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"Checking {check_name}...", end=" ")
            try:
                result = check_func()
                if result:
                    print("✅ PASS")
                else:
                    print("❌ FAIL")
                    all_passed = False
            except Exception as e:
                print(f"❌ ERROR: {e}")
                self.validation_report["validation_errors"].append(f"{check_name}: {e}")
                all_passed = False
                
        # Check file counts
        file_stats = self.check_file_count()
        print(f"\nFile Statistics:")
        print(f"  Total files: {file_stats['total_files']}")
        print(f"  Remaining duplicates: {file_stats['remaining_duplicates']}")
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Set overall readiness
        self.validation_report["phase7_readiness"] = all_passed
        
        # Print summary
        print("\n" + "=" * 50)
        if all_passed:
            print("✅ VALIDATION PASSED - Repository ready for Phase 7!")
        else:
            print("❌ VALIDATION FAILED - Issues found")
            print("\nErrors:")
            for error in self.validation_report["validation_errors"]:
                print(f"  - {error}")
                
            print("\nRecommendations:")
            for rec in self.validation_report["recommendations"]:
                print(f"  - {rec}")
        
        # Save validation report
        report_path = self.repo_path / "VALIDATION_REPORT.json"
        with open(report_path, 'w') as f:
            json.dump(self.validation_report, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_path}")
        
        return all_passed

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate ChatterFix repository after cleanup")
    parser.add_argument("--repo-path", default="/Users/fredtaylor/Desktop/Projects/ai-tools",
                       help="Path to repository")
    
    args = parser.parse_args()
    
    validator = CleanupValidator(args.repo_path)
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()