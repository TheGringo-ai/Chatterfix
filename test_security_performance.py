#!/usr/bin/env python3
"""Security and Performance Tests for ChatterFix CMMS"""

import os
import re
import time
import subprocess
import sys
from pathlib import Path


def test_security_patterns():
    """Test for common security issues in code"""
    print("🔐 Testing Security Patterns...")

    security_issues = []

    # Patterns to look for
    dangerous_patterns = {
        "SQL Injection": r"(execute\s*\(\s*['\"].*%.*['\"]|cursor\.execute.*%)",
        "Hardcoded Secrets": r"(password\s*=\s*['\"][^'\"]+['\"]|api_key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"])",
        "Debug Mode": r"(debug\s*=\s*True|DEBUG\s*=\s*True)",
        "Unsafe Imports": r"(import\s+pickle|import\s+marshal|exec\s*\(|eval\s*\()",
        "Command Injection": r"(os\.system\s*\(|subprocess.*shell\s*=\s*True)",
    }

    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip virtual environments and other non-source directories
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".")
            and d not in ["venv", "node_modules", "__pycache__"]
        ]
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    total_files_checked = 0
    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            total_files_checked += 1
            for issue_type, pattern in dangerous_patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    security_issues.append(
                        {
                            "file": file_path,
                            "issue": issue_type,
                            "matches": len(matches),
                        }
                    )

        except Exception as e:
            print(f"⚠️ Could not check {file_path}: {e}")

    if security_issues:
        print(f"⚠️ Found {len(security_issues)} potential security issues:")
        for issue in security_issues[:5]:  # Show first 5 issues
            print(
                f"   - {issue['file']}: {issue['issue']} ({issue['matches']} matches)"
            )
        if len(security_issues) > 5:
            print(f"   ... and {len(security_issues) - 5} more")
        return False
    else:
        print(
            f"✅ No obvious security issues found in {total_files_checked} Python files"
        )
        return True


def test_file_permissions():
    """Test file permissions for security"""
    print("📋 Testing File Permissions...")

    sensitive_files = [
        ".env",
        "secrets.json",
        "private_key.pem",
        "config/production.py",
    ]

    issues = []
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            # Check if file is readable by others (world-readable)
            if stat.st_mode & 0o004:
                issues.append(f"{file_path} is world-readable")

    if issues:
        print("⚠️ Permission issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ No sensitive files with bad permissions found")
        return True


def test_dependency_security():
    """Test for known security vulnerabilities in dependencies"""
    print("📦 Testing Dependency Security...")

    requirements_files = ["requirements.txt", "requirements-dev.txt"]

    for req_file in requirements_files:
        if os.path.exists(req_file):
            print(f"📋 Checking {req_file}...")
            try:
                with open(req_file, "r") as f:
                    content = f.read()

                # Check for pinned versions (security best practice)
                lines = [
                    line.strip()
                    for line in content.split("\n")
                    if line.strip() and not line.startswith("#")
                ]
                unpinned = []

                for line in lines:
                    if "==" not in line and ">=" not in line and line.strip():
                        unpinned.append(line)

                if unpinned:
                    print(f"⚠️ {req_file} has unpinned dependencies: {unpinned[:3]}...")
                else:
                    print(f"✅ {req_file} has properly pinned dependencies")

            except Exception as e:
                print(f"❌ Error reading {req_file}: {e}")
                return False

    return True


def test_performance_basics():
    """Test basic performance characteristics"""
    print("⚡ Testing Performance Basics...")

    # Test static file sizes
    large_files = []
    total_size = 0

    static_dirs = ["app/static", "app/templates"]
    for static_dir in static_dirs:
        if os.path.isdir(static_dir):
            for root, dirs, files in os.walk(static_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        total_size += size

                        # Flag files larger than 1MB
                        if size > 1024 * 1024:
                            large_files.append(f"{file_path}: {size/1024/1024:.1f}MB")
                    except Exception:
                        pass

    print(f"📊 Total static assets size: {total_size/1024:.1f}KB")

    if large_files:
        print(f"⚠️ Large files found:")
        for large_file in large_files[:3]:
            print(f"   - {large_file}")
        return False
    else:
        print("✅ No unusually large static files found")
        return True


def test_code_quality_metrics():
    """Test basic code quality metrics"""
    print("📏 Testing Code Quality Metrics...")

    python_files = []
    total_lines = 0
    long_files = []

    for root, dirs, files in os.walk("app"):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        lines = len(f.readlines())

                    total_lines += lines
                    python_files.append(file_path)

                    # Flag very long files (>500 lines)
                    if lines > 500:
                        long_files.append(f"{file_path}: {lines} lines")

                except Exception:
                    pass

    avg_lines = total_lines / len(python_files) if python_files else 0

    print(f"📊 Code metrics:")
    print(f"   - {len(python_files)} Python files")
    print(f"   - {total_lines} total lines of code")
    print(f"   - {avg_lines:.1f} average lines per file")

    if long_files:
        print(f"⚠️ Files that might need refactoring:")
        for long_file in long_files[:3]:
            print(f"   - {long_file}")

    return (
        len(long_files) < len(python_files) * 0.2
    )  # Less than 20% of files are too long


def test_docker_configuration():
    """Test Docker configuration if present"""
    print("🐳 Testing Docker Configuration...")

    docker_files = ["Dockerfile", "docker-compose.yml", ".dockerignore"]
    docker_config_found = False

    for docker_file in docker_files:
        if os.path.exists(docker_file):
            docker_config_found = True
            try:
                with open(docker_file, "r") as f:
                    content = f.read()

                # Basic Docker security checks
                if docker_file == "Dockerfile":
                    if "USER root" in content and "USER " not in content.replace(
                        "USER root", ""
                    ):
                        print(f"⚠️ {docker_file}: Running as root user")
                    elif "FROM python:" in content:
                        print(f"✅ {docker_file}: Python-based container")

                print(f"✅ Found {docker_file}")

            except Exception as e:
                print(f"❌ Error reading {docker_file}: {e}")
                return False

    if not docker_config_found:
        print("ℹ️ No Docker configuration found")

    return True


def main():
    """Run all security and performance tests"""
    print("🧪 ChatterFix Security & Performance Tests")
    print("=" * 60)

    test_results = {
        "Security Patterns": test_security_patterns(),
        "File Permissions": test_file_permissions(),
        "Dependency Security": test_dependency_security(),
        "Performance Basics": test_performance_basics(),
        "Code Quality": test_code_quality_metrics(),
        "Docker Configuration": test_docker_configuration(),
    }

    # Print summary
    print("\n" + "=" * 60)
    print("🧪 SECURITY & PERFORMANCE SUMMARY")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "⚠️ REVIEW"
        print(f"{status} {test_name}")

    print("-" * 60)
    print(
        f"Total: {total_tests} | Passed: {passed_tests} | Need Review: {total_tests - passed_tests}"
    )
    print(f"Score: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests >= total_tests * 0.8:
        print("🎉 Overall: GOOD - Application appears secure and well-optimized")
    elif passed_tests >= total_tests * 0.6:
        print("⚠️ Overall: NEEDS ATTENTION - Some issues should be addressed")
    else:
        print("❌ Overall: NEEDS WORK - Multiple issues require immediate attention")

    print("=" * 60)

    return passed_tests >= total_tests * 0.8


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
