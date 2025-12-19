#!/usr/bin/env python3
"""
AI Team Pre-Commit Review Hook
Scans code changes against known mistake patterns before allowing commits.

Part of the Never-Repeat-Mistakes system from CLAUDE.md

Usage:
    python scripts/ai-precommit-review.py [--files file1.py file2.py]

Add to .git/hooks/pre-commit or use with pre-commit framework.
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Known mistake patterns from CLAUDE.md lessons
MISTAKE_PATTERNS = [
    {
        "id": 1,
        "pattern": r"body\.classList\.(add|remove)\(['\"]dark",
        "not_pattern": r"documentElement.*dark|document\.documentElement",
        "message": "Dark mode: Apply class to BOTH documentElement AND body (Lesson #1)",
        "severity": "warning",
    },
    {
        "id": 2,
        "pattern": r"datetime\.(now|utcnow)\(\)",
        "context": r"json|JSONResponse|dict|return.*\{",
        "message": "DateTime in JSON: Use .isoformat() or .strftime() for JSON serialization (Lesson #2)",
        "severity": "warning",
    },
    {
        "id": 3,
        "pattern": r"except\s*:",
        "message": "Bare except clause: Specify exception type (e.g., except Exception:)",
        "severity": "warning",
    },
    {
        "id": 4,
        "pattern": r"response\.set_cookie\(",
        "context": r"return\s+(JSONResponse|RedirectResponse|HTMLResponse)",
        "message": "Cookie issue: Set cookie on the SAME response object being returned (Lesson #6)",
        "severity": "error",
    },
    {
        "id": 5,
        "pattern": r"fetch\s*\([^)]+\)",
        "not_pattern": r"credentials\s*:\s*['\"]include['\"]",
        "context": r"auth|login|session|cookie",
        "message": "Fetch cookies: Add credentials: 'include' for cookie handling (Lesson #7)",
        "severity": "warning",
    },
    {
        "id": 6,
        "pattern": r"\.appspot\.com",
        "context": r"storageBucket|storage",
        "message": "Firebase storage: Use new format .firebasestorage.app instead of .appspot.com (Lesson #9)",
        "severity": "info",
    },
    {
        "id": 7,
        "pattern": r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
        "not_pattern": r"env|getenv|config|placeholder|example|your_",
        "message": "Potential hardcoded secret: Use environment variables instead",
        "severity": "error",
    },
    {
        "id": 8,
        "pattern": r"print\s*\(.*password|print\s*\(.*secret|print\s*\(.*api_key",
        "message": "Potential secret logging: Remove sensitive data from print statements",
        "severity": "error",
    },
    {
        "id": 9,
        "pattern": r"import\s+pyrebase",
        "message": "Pyrebase: Consider using Firebase Admin SDK for server-side (Lesson #10)",
        "severity": "info",
    },
    {
        "id": 10,
        "pattern": r"get_current_active_user|Depends\(get_current_active_user\)",
        "context": r"response_class\s*=\s*HTMLResponse|\.html",
        "message": "Auth mismatch: HTML pages should use cookie auth, not OAuth2 Bearer (Lesson #8)",
        "severity": "warning",
    },
]


class AIPreCommitReview:
    """AI-powered pre-commit code review"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.issues: List[Dict] = []
        self.warnings: List[Dict] = []
        self.infos: List[Dict] = []

    def get_staged_files(self) -> List[str]:
        """Get list of staged files for commit"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            # Filter to only Python, JavaScript, TypeScript files
            return [f for f in files if f.endswith((".py", ".js", ".ts", ".tsx", ".html"))]
        except subprocess.CalledProcessError:
            return []

    def get_file_content(self, file_path: str) -> str:
        """Get the staged content of a file"""
        try:
            result = subprocess.run(
                ["git", "show", f":{file_path}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            # Fallback to reading file directly
            try:
                with open(file_path, "r") as f:
                    return f.read()
            except Exception:
                return ""

    def check_pattern(
        self,
        content: str,
        pattern: Dict,
        file_path: str,
    ) -> List[Dict]:
        """Check content against a pattern"""
        issues = []

        # Find all matches of the main pattern
        main_pattern = pattern["pattern"]
        matches = list(re.finditer(main_pattern, content, re.IGNORECASE | re.MULTILINE))

        if not matches:
            return []

        for match in matches:
            line_num = content[:match.start()].count("\n") + 1
            line_content = content.split("\n")[line_num - 1] if line_num > 0 else ""

            # Check context pattern if specified
            if "context" in pattern:
                # Check if context pattern is nearby (within 5 lines)
                start = max(0, match.start() - 500)
                end = min(len(content), match.end() + 500)
                context_area = content[start:end]

                if not re.search(pattern["context"], context_area, re.IGNORECASE):
                    continue

            # Check not_pattern (should NOT be present)
            if "not_pattern" in pattern:
                # Check in the same line or nearby context
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                check_area = content[start:end]

                if re.search(pattern["not_pattern"], check_area, re.IGNORECASE):
                    continue

            issues.append({
                "file": file_path,
                "line": line_num,
                "line_content": line_content.strip()[:80],
                "pattern_id": pattern["id"],
                "message": pattern["message"],
                "severity": pattern["severity"],
            })

        return issues

    def review_file(self, file_path: str) -> None:
        """Review a single file"""
        content = self.get_file_content(file_path)
        if not content:
            return

        for pattern in MISTAKE_PATTERNS:
            issues = self.check_pattern(content, pattern, file_path)

            for issue in issues:
                if issue["severity"] == "error":
                    self.issues.append(issue)
                elif issue["severity"] == "warning":
                    self.warnings.append(issue)
                else:
                    self.infos.append(issue)

    def review_all(self, files: List[str] = None) -> Tuple[int, int, int]:
        """Review all staged files or specified files"""
        if files is None:
            files = self.get_staged_files()

        if not files:
            if self.verbose:
                print("No relevant files to review.")
            return 0, 0, 0

        if self.verbose:
            print(f"🔍 AI Team reviewing {len(files)} files...")

        for file_path in files:
            self.review_file(file_path)

        return len(self.issues), len(self.warnings), len(self.infos)

    def print_report(self) -> None:
        """Print the review report"""
        total = len(self.issues) + len(self.warnings) + len(self.infos)

        if total == 0:
            print("\n✅ AI Team Review: No issues found!")
            return

        print("\n" + "=" * 60)
        print("🤖 AI TEAM PRE-COMMIT REVIEW REPORT")
        print("=" * 60)

        if self.issues:
            print(f"\n🚨 ERRORS ({len(self.issues)}) - Must fix before commit:")
            for issue in self.issues:
                print(f"\n  📁 {issue['file']}:{issue['line']}")
                print(f"     {issue['message']}")
                print(f"     Code: {issue['line_content']}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}) - Should review:")
            for warning in self.warnings:
                print(f"\n  📁 {warning['file']}:{warning['line']}")
                print(f"     {warning['message']}")
                if self.verbose:
                    print(f"     Code: {warning['line_content']}")

        if self.infos and self.verbose:
            print(f"\nℹ️  INFO ({len(self.infos)}) - Suggestions:")
            for info in self.infos:
                print(f"\n  📁 {info['file']}:{info['line']}")
                print(f"     {info['message']}")

        print("\n" + "-" * 60)
        print(f"Summary: {len(self.issues)} errors, {len(self.warnings)} warnings, {len(self.infos)} info")
        print("-" * 60)

    def should_block_commit(self) -> bool:
        """Determine if commit should be blocked"""
        return len(self.issues) > 0


def main():
    parser = argparse.ArgumentParser(description="AI Team Pre-Commit Review")
    parser.add_argument("--files", nargs="*", help="Specific files to review")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-block", action="store_true", help="Don't block commit on errors")
    args = parser.parse_args()

    reviewer = AIPreCommitReview(verbose=args.verbose)
    errors, warnings, infos = reviewer.review_all(args.files)

    if errors > 0 or warnings > 0 or infos > 0 or args.verbose:
        reviewer.print_report()

    if reviewer.should_block_commit() and not args.no_block:
        print("\n🚫 COMMIT BLOCKED: Fix errors before committing.")
        print("   Use --no-block to override (not recommended)")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
