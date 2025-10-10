"""
GitHub Deployment API
Handles GitHub operations: commit, push, create PRs, trigger deployments
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import hmac
import hashlib
import json

logger = logging.getLogger(__name__)


class GitHubDeploymentAPI:
    """API for GitHub operations and deployments"""

    def __init__(self):
        self.repo_path = os.getenv('REPO_PATH', '/home/yoyofred_gringosgambit_com/chatterfix-docker/app')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.github_repo = os.getenv('GITHUB_REPO', 'fredfix/ai-tools')
        self.api_key = os.getenv('DEPLOYMENT_API_KEY', 'chatterfix-deploy-2025')

    def verify_api_key(self, provided_key: str) -> bool:
        """Verify API key for deployment requests"""
        return hmac.compare_digest(provided_key, self.api_key)

    def execute_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute shell command and return result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def git_status(self) -> Dict[str, Any]:
        """Get current git status"""
        result = self.execute_command("git status --porcelain")

        if not result["success"]:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to get git status")
            }

        changes = result["stdout"].split('\n') if result["stdout"] else []

        return {
            "success": True,
            "has_changes": len(changes) > 0 and changes[0] != '',
            "changes": [line for line in changes if line],
            "change_count": len([line for line in changes if line])
        }

    async def git_commit(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Commit changes to git"""
        logger.info(f"Committing with message: {message}")

        # Add files
        if files:
            for file in files:
                add_result = self.execute_command(f"git add {file}")
                if not add_result["success"]:
                    return {
                        "success": False,
                        "error": f"Failed to add {file}: {add_result.get('stderr')}"
                    }
        else:
            # Add all changes
            add_result = self.execute_command("git add -A")
            if not add_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to add files: {add_result.get('stderr')}"
                }

        # Commit
        commit_message = f"{message}\n\n🤖 Automated by Fix It Fred\n\nCo-Authored-By: Fix It Fred <fred@chatterfix.com>"
        commit_result = self.execute_command(f'git commit -m "{commit_message}"')

        if not commit_result["success"]:
            return {
                "success": False,
                "error": f"Commit failed: {commit_result.get('stderr')}"
            }

        return {
            "success": True,
            "message": "Changes committed successfully",
            "commit_output": commit_result["stdout"]
        }

    async def git_push(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Push changes to remote"""
        branch_cmd = f" origin {branch}" if branch else ""
        push_result = self.execute_command(f"git push{branch_cmd}")

        if not push_result["success"]:
            return {
                "success": False,
                "error": f"Push failed: {push_result.get('stderr')}"
            }

        return {
            "success": True,
            "message": "Changes pushed successfully",
            "push_output": push_result["stdout"]
        }

    async def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """Create and checkout new branch"""
        result = self.execute_command(f"git checkout -b {branch_name}")

        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to create branch: {result.get('stderr')}"
            }

        return {
            "success": True,
            "branch": branch_name,
            "message": f"Branch {branch_name} created"
        }

    async def create_pull_request(self, title: str, body: str, base: str = "main") -> Dict[str, Any]:
        """Create a pull request using GitHub CLI"""
        if not self.github_token:
            return {
                "success": False,
                "error": "GITHUB_TOKEN not configured"
            }

        # Set GitHub token for gh CLI
        os.environ['GITHUB_TOKEN'] = self.github_token

        pr_body = f"{body}\n\n🤖 Created by Fix It Fred"
        result = self.execute_command(f'gh pr create --title "{title}" --body "{pr_body}" --base {base}')

        if not result["success"]:
            return {
                "success": False,
                "error": f"PR creation failed: {result.get('stderr')}"
            }

        return {
            "success": True,
            "message": "Pull request created",
            "pr_url": result["stdout"]
        }

    async def trigger_deployment(self, environment: str = "production", command: str = "") -> Dict[str, Any]:
        """Trigger GitHub Actions deployment via git push

        Instead of requiring GITHUB_TOKEN, this pushes changes which triggers
        the workflow automatically via push event.
        """
        try:
            # Ensure we're on a branch
            branch_result = self.execute_command("git branch --show-current")
            if not branch_result["success"] or not branch_result["stdout"]:
                return {
                    "success": False,
                    "error": "Not on a valid git branch"
                }

            current_branch = branch_result["stdout"].strip()

            # Push to trigger deployment
            push_result = self.execute_command(f"git push origin {current_branch}")

            if not push_result["success"]:
                return {
                    "success": False,
                    "error": f"Push failed: {push_result.get('stderr')}",
                    "info": "Deployment trigger requires successful git push"
                }

            return {
                "success": True,
                "environment": environment,
                "branch": current_branch,
                "message": f"Pushed to {current_branch} - GitHub Actions will deploy automatically",
                "info": "Check GitHub Actions for deployment progress",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def full_deployment_flow(
        self,
        commit_message: str,
        files: Optional[List[str]] = None,
        create_pr: bool = False,
        deploy: bool = True
    ) -> Dict[str, Any]:
        """Complete deployment flow: commit, push, optionally PR, deploy"""

        results = {
            "success": True,
            "steps": [],
            "errors": []
        }

        # Check status
        status = await self.git_status()
        if not status["has_changes"]:
            return {
                "success": False,
                "error": "No changes to commit"
            }

        results["steps"].append({"step": "status_check", "changes": status["change_count"]})

        # Commit
        commit_result = await self.git_commit(commit_message, files)
        if not commit_result["success"]:
            results["success"] = False
            results["errors"].append(commit_result)
            return results

        results["steps"].append({"step": "commit", "success": True})

        # Push
        push_result = await self.git_push()
        if not push_result["success"]:
            results["success"] = False
            results["errors"].append(push_result)
            return results

        results["steps"].append({"step": "push", "success": True})

        # Create PR if requested
        if create_pr:
            pr_result = await self.create_pull_request(
                title=commit_message,
                body=f"Automated deployment\n\nChanges: {status['change_count']} files"
            )
            if pr_result["success"]:
                results["steps"].append({"step": "pull_request", "url": pr_result.get("pr_url")})
                results["pr_url"] = pr_result.get("pr_url")

        # Trigger deployment
        if deploy:
            deploy_result = await self.trigger_deployment()
            if not deploy_result["success"]:
                results["errors"].append(deploy_result)
            else:
                results["steps"].append({"step": "deployment_triggered", "success": True})

        return results


# Global instance
github_api = GitHubDeploymentAPI()
