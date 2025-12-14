"""
ChatterFix Git Tools
====================
Automates git operations for the AI team.

Features:
- Auto-commit with smart messages
- Branch management
- Pull request creation
- Conflict detection
- Change analysis
"""

import asyncio
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of code changes"""
    FEATURE = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    TEST = "test"
    CHORE = "chore"
    PERF = "perf"
    BUILD = "build"
    CI = "ci"


class BranchType(Enum):
    """Types of git branches"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    HOTFIX = "hotfix"
    RELEASE = "release"
    DOCS = "docs"


@dataclass
class GitStatus:
    """Current git repository status"""
    branch: str
    is_clean: bool
    staged_files: List[str]
    modified_files: List[str]
    untracked_files: List[str]
    ahead: int = 0
    behind: int = 0
    has_conflicts: bool = False


@dataclass
class CommitInfo:
    """Information about a commit"""
    hash: str
    short_hash: str
    message: str
    author: str
    date: str
    files_changed: int = 0


@dataclass
class PullRequestInfo:
    """Pull request information"""
    title: str
    body: str
    branch: str
    base: str = "main"
    labels: List[str] = field(default_factory=list)
    reviewers: List[str] = field(default_factory=list)


class GitTools:
    """
    Automates git operations for AI-powered development.

    Provides:
    - Smart commit message generation
    - Branch creation and management
    - Change analysis
    - PR preparation
    - Conflict detection
    """

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getcwd()
        self._validate_repo()

    def _validate_repo(self):
        """Validate that we're in a git repository"""
        git_dir = os.path.join(self.repo_path, ".git")
        if not os.path.isdir(git_dir):
            logger.warning(f"Not a git repository: {self.repo_path}")

    def _run_git(self, *args, check: bool = True) -> Tuple[int, str, str]:
        """Run a git command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            return 1, "", str(e)

    def get_status(self) -> GitStatus:
        """Get current repository status"""

        # Get branch name
        _, branch, _ = self._run_git("branch", "--show-current")

        # Get status
        _, status_output, _ = self._run_git("status", "--porcelain")

        staged = []
        modified = []
        untracked = []

        for line in status_output.split("\n"):
            if not line:
                continue
            status_code = line[:2]
            filename = line[3:]

            if status_code[0] in "MADRC":
                staged.append(filename)
            if status_code[1] in "MD":
                modified.append(filename)
            if status_code == "??":
                untracked.append(filename)

        # Check ahead/behind
        _, ahead_behind, _ = self._run_git(
            "rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"
        )
        ahead, behind = 0, 0
        if ahead_behind and "\t" in ahead_behind:
            parts = ahead_behind.split("\t")
            behind, ahead = int(parts[0]), int(parts[1])

        return GitStatus(
            branch=branch,
            is_clean=len(staged) == 0 and len(modified) == 0,
            staged_files=staged,
            modified_files=modified,
            untracked_files=untracked,
            ahead=ahead,
            behind=behind,
            has_conflicts="UU" in status_output,
        )

    def get_diff_summary(self, staged_only: bool = False) -> Dict[str, Any]:
        """Get summary of changes"""

        diff_args = ["diff", "--stat"]
        if staged_only:
            diff_args.append("--cached")

        _, diff_output, _ = self._run_git(*diff_args)

        # Parse diff stats
        files_changed = 0
        insertions = 0
        deletions = 0

        lines = diff_output.split("\n")
        if lines:
            summary_line = lines[-1]
            match = re.search(r"(\d+) files? changed", summary_line)
            if match:
                files_changed = int(match.group(1))
            match = re.search(r"(\d+) insertions?", summary_line)
            if match:
                insertions = int(match.group(1))
            match = re.search(r"(\d+) deletions?", summary_line)
            if match:
                deletions = int(match.group(1))

        return {
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "diff_output": diff_output,
        }

    def analyze_changes(self) -> ChangeType:
        """Analyze changes to determine commit type"""

        status = self.get_status()
        all_files = status.staged_files + status.modified_files

        # Analyze file patterns
        has_tests = any("test" in f.lower() for f in all_files)
        has_docs = any(f.endswith(".md") or "docs" in f for f in all_files)
        has_ci = any(".github" in f or "ci" in f.lower() for f in all_files)
        has_config = any(f.endswith((".json", ".yaml", ".yml", ".toml")) for f in all_files)

        # Get diff content for analysis
        _, diff_content, _ = self._run_git("diff", "--cached")

        # Detect fix vs feature
        is_fix = any(word in diff_content.lower() for word in ["fix", "bug", "error", "issue", "patch"])

        if has_tests:
            return ChangeType.TEST
        elif has_docs:
            return ChangeType.DOCS
        elif has_ci:
            return ChangeType.CI
        elif has_config and not any(f.endswith(".py") for f in all_files):
            return ChangeType.CHORE
        elif is_fix:
            return ChangeType.FIX
        else:
            return ChangeType.FEATURE

    def generate_commit_message(
        self,
        change_type: Optional[ChangeType] = None,
        scope: Optional[str] = None,
        description: Optional[str] = None,
        ai_generated: bool = True
    ) -> str:
        """Generate a conventional commit message"""

        if change_type is None:
            change_type = self.analyze_changes()

        status = self.get_status()
        diff = self.get_diff_summary(staged_only=True)

        # Auto-generate description if not provided
        if description is None:
            files = status.staged_files
            if len(files) == 1:
                description = f"update {files[0]}"
            elif len(files) <= 3:
                description = f"update {', '.join(files)}"
            else:
                description = f"update {len(files)} files"

        # Build commit message
        prefix = change_type.value
        if scope:
            prefix = f"{prefix}({scope})"

        message = f"{prefix}: {description}"

        # Add body with stats
        body = f"\n\nFiles changed: {diff['files_changed']}"
        body += f"\nInsertions: {diff['insertions']}, Deletions: {diff['deletions']}"

        if ai_generated:
            body += "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"
            body += "\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

        return message + body

    def stage_files(self, files: Optional[List[str]] = None, all_files: bool = False) -> bool:
        """Stage files for commit"""

        if all_files:
            code, _, stderr = self._run_git("add", "-A")
        elif files:
            code, _, stderr = self._run_git("add", *files)
        else:
            return False

        if code != 0:
            logger.error(f"Failed to stage files: {stderr}")
            return False

        return True

    def commit(
        self,
        message: Optional[str] = None,
        change_type: Optional[ChangeType] = None,
        scope: Optional[str] = None
    ) -> Optional[CommitInfo]:
        """Create a commit with auto-generated or provided message"""

        if message is None:
            message = self.generate_commit_message(change_type, scope)

        code, stdout, stderr = self._run_git("commit", "-m", message)

        if code != 0:
            logger.error(f"Commit failed: {stderr}")
            return None

        # Get commit info
        _, hash_output, _ = self._run_git("rev-parse", "HEAD")
        _, short_hash, _ = self._run_git("rev-parse", "--short", "HEAD")

        return CommitInfo(
            hash=hash_output,
            short_hash=short_hash,
            message=message.split("\n")[0],
            author="AI Team",
            date=datetime.now().isoformat(),
        )

    def create_branch(
        self,
        name: str,
        branch_type: BranchType = BranchType.FEATURE,
        checkout: bool = True
    ) -> bool:
        """Create a new branch"""

        # Format branch name
        safe_name = re.sub(r"[^a-zA-Z0-9-]", "-", name.lower())
        branch_name = f"{branch_type.value}/{safe_name}"

        if checkout:
            code, _, stderr = self._run_git("checkout", "-b", branch_name)
        else:
            code, _, stderr = self._run_git("branch", branch_name)

        if code != 0:
            logger.error(f"Failed to create branch: {stderr}")
            return False

        logger.info(f"Created branch: {branch_name}")
        return True

    def checkout(self, branch: str) -> bool:
        """Checkout a branch"""
        code, _, stderr = self._run_git("checkout", branch)

        if code != 0:
            logger.error(f"Failed to checkout: {stderr}")
            return False

        return True

    def pull(self, rebase: bool = True) -> bool:
        """Pull latest changes"""
        args = ["pull"]
        if rebase:
            args.append("--rebase")

        code, _, stderr = self._run_git(*args)

        if code != 0:
            logger.error(f"Pull failed: {stderr}")
            return False

        return True

    def push(self, set_upstream: bool = False, force: bool = False) -> bool:
        """Push changes to remote"""

        args = ["push"]
        if set_upstream:
            status = self.get_status()
            args.extend(["-u", "origin", status.branch])
        if force:
            args.append("--force-with-lease")

        code, _, stderr = self._run_git(*args)

        if code != 0:
            logger.error(f"Push failed: {stderr}")
            return False

        return True

    def get_recent_commits(self, count: int = 10) -> List[CommitInfo]:
        """Get recent commits"""

        format_str = "%H|%h|%s|%an|%ai"
        _, output, _ = self._run_git("log", f"-{count}", f"--format={format_str}")

        commits = []
        for line in output.split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 5:
                commits.append(CommitInfo(
                    hash=parts[0],
                    short_hash=parts[1],
                    message=parts[2],
                    author=parts[3],
                    date=parts[4],
                ))

        return commits

    def prepare_pull_request(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> PullRequestInfo:
        """Prepare pull request information"""

        status = self.get_status()
        commits = self.get_recent_commits(10)
        diff = self.get_diff_summary()

        # Get commits since branching from main
        _, commit_log, _ = self._run_git("log", "main..HEAD", "--oneline")
        commit_messages = commit_log.split("\n") if commit_log else []

        # Auto-generate title from branch name
        if title is None:
            branch_parts = status.branch.split("/")
            if len(branch_parts) > 1:
                title = branch_parts[-1].replace("-", " ").title()
            else:
                title = status.branch.replace("-", " ").title()

        # Auto-generate body
        if description is None:
            description = "## Summary\n"
            for msg in commit_messages[:5]:
                description += f"- {msg}\n"

            description += f"\n## Changes\n"
            description += f"- Files changed: {diff['files_changed']}\n"
            description += f"- Additions: {diff['insertions']}\n"
            description += f"- Deletions: {diff['deletions']}\n"

            description += "\n## Test Plan\n- [ ] Tests pass locally\n- [ ] Manual testing complete\n"
            description += "\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"

        # Detect labels from branch type
        labels = []
        if "feature" in status.branch:
            labels.append("enhancement")
        elif "fix" in status.branch or "bug" in status.branch:
            labels.append("bug")
        elif "docs" in status.branch:
            labels.append("documentation")

        return PullRequestInfo(
            title=title,
            body=description,
            branch=status.branch,
            base="main",
            labels=labels,
        )

    def create_pull_request(self, pr_info: Optional[PullRequestInfo] = None) -> Optional[str]:
        """Create pull request using gh CLI"""

        if pr_info is None:
            pr_info = self.prepare_pull_request()

        # Check if gh is available
        code, _, _ = self._run_git("--version")  # Just to test subprocess works

        try:
            result = subprocess.run(
                [
                    "gh", "pr", "create",
                    "--title", pr_info.title,
                    "--body", pr_info.body,
                    "--base", pr_info.base,
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Extract PR URL from output
                pr_url = result.stdout.strip()
                logger.info(f"Created PR: {pr_url}")
                return pr_url
            else:
                logger.error(f"Failed to create PR: {result.stderr}")
                return None

        except FileNotFoundError:
            logger.error("gh CLI not installed")
            return None

    def generate_changelog(self, since_tag: Optional[str] = None) -> str:
        """Generate changelog from commits"""

        if since_tag:
            _, log_output, _ = self._run_git("log", f"{since_tag}..HEAD", "--oneline")
        else:
            _, log_output, _ = self._run_git("log", "-50", "--oneline")

        # Group commits by type
        features = []
        fixes = []
        others = []

        for line in log_output.split("\n"):
            if not line:
                continue
            if line.startswith(("feat", "feature")):
                features.append(line)
            elif line.startswith("fix"):
                fixes.append(line)
            else:
                others.append(line)

        changelog = f"# Changelog\n\nGenerated: {datetime.now().isoformat()}\n\n"

        if features:
            changelog += "## Features\n"
            for f in features:
                changelog += f"- {f}\n"
            changelog += "\n"

        if fixes:
            changelog += "## Bug Fixes\n"
            for f in fixes:
                changelog += f"- {f}\n"
            changelog += "\n"

        if others:
            changelog += "## Other Changes\n"
            for o in others[:10]:  # Limit others
                changelog += f"- {o}\n"

        return changelog


def get_git_tools(repo_path: Optional[str] = None) -> GitTools:
    """Get a GitTools instance"""
    return GitTools(repo_path)
