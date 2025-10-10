"""
Fix It Fred API Gateway
Natural language interface for deployments and service orchestration
"""

import os
import logging
from typing import Dict, Any, Optional
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class FixItFredGateway:
    """Natural language gateway for Fix It Fred operations"""

    def __init__(self, github_api, ollama_api):
        self.github_api = github_api
        self.ollama_api = ollama_api
        self.command_patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize command patterns for natural language parsing"""
        return {
            "deploy": {
                "patterns": [
                    r"deploy.*to (production|prod|staging|dev)",
                    r"push.*deploy",
                    r"build.*deploy",
                    r"ship.*to (production|prod)",
                ],
                "action": "deploy",
                "requires_commit": True
            },
            "commit": {
                "patterns": [
                    r"commit.*changes?",
                    r"save.*changes?",
                    r"git commit",
                ],
                "action": "commit",
                "requires_commit": False
            },
            "push": {
                "patterns": [
                    r"push.*to.*github",
                    r"git push",
                    r"push.*changes?",
                ],
                "action": "push",
                "requires_commit": True
            },
            "create_pr": {
                "patterns": [
                    r"create.*pull request",
                    r"make.*pr",
                    r"open.*pull request",
                ],
                "action": "create_pr",
                "requires_commit": True
            },
            "full_deploy": {
                "patterns": [
                    r"commit.*push.*deploy",
                    r"ship it",
                    r"deploy everything",
                    r"full.*deploy",
                ],
                "action": "full_deploy",
                "requires_commit": True
            },
            "status": {
                "patterns": [
                    r"git status",
                    r"check.*status",
                    r"what.*changed",
                    r"show.*changes",
                ],
                "action": "status",
                "requires_commit": False
            },
        }

    def parse_natural_language_command(self, text: str) -> Dict[str, Any]:
        """Parse natural language into structured command"""
        text_lower = text.lower()

        # Check each command pattern
        for command_name, command_config in self.command_patterns.items():
            for pattern in command_config["patterns"]:
                if re.search(pattern, text_lower):
                    # Extract environment if specified
                    env_match = re.search(r"(production|prod|staging|dev)", text_lower)
                    environment = "production"
                    if env_match:
                        env = env_match.group(1)
                        environment = "production" if env in ["prod", "production"] else env

                    # Extract commit message hint
                    message_match = re.search(r'(?:message|msg|commit)[\s:]+["\']([^"\']+)["\']', text)
                    commit_message = message_match.group(1) if message_match else None

                    return {
                        "success": True,
                        "action": command_config["action"],
                        "environment": environment,
                        "commit_message": commit_message,
                        "requires_commit": command_config["requires_commit"],
                        "original_text": text
                    }

        # No pattern matched
        return {
            "success": False,
            "error": "Command not recognized",
            "original_text": text,
            "suggestion": "Try commands like: 'deploy to production', 'commit changes', 'push to github', 'create pull request'"
        }

    async def generate_commit_message(self, context: str = "") -> str:
        """Use Ollama to generate a smart commit message based on changes"""
        try:
            # Get git diff
            diff_result = self.github_api.execute_command("git diff --staged")
            diff_text = diff_result.get("stdout", "")[:2000]  # Limit to 2000 chars

            prompt = f"""You are a commit message generator. Based on the following git diff, create a concise, professional commit message (one line, max 72 characters).

Context: {context}

Diff:
{diff_text}

Commit message (one line only):"""

            # Use Ollama to generate
            model = await self.ollama_api.select_best_model()
            if model:
                response = await self.ollama_api.generate_response(model, prompt)
                if response:
                    # Extract first line, clean it up
                    message = response.split('\n')[0].strip()
                    # Remove quotes if present
                    message = message.strip('"\'')
                    return message[:72]  # Enforce length limit

        except Exception as e:
            logger.error(f"Failed to generate commit message: {e}")

        # Fallback to timestamp-based message
        return f"Update ChatterFix CMMS - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    async def execute_command(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the parsed command"""
        action = parsed_command["action"]
        logger.info(f"Executing action: {action}")

        try:
            if action == "status":
                return await self.github_api.git_status()

            elif action == "commit":
                # Generate or use provided commit message
                commit_msg = parsed_command.get("commit_message")
                if not commit_msg:
                    commit_msg = await self.generate_commit_message(
                        parsed_command.get("original_text", "")
                    )

                return await self.github_api.git_commit(commit_msg)

            elif action == "push":
                return await self.github_api.git_push()

            elif action == "create_pr":
                commit_msg = parsed_command.get("commit_message") or "ChatterFix Update"
                return await self.github_api.create_pull_request(
                    title=commit_msg,
                    body=f"Automated PR from Fix It Fred\n\nOriginal request: {parsed_command['original_text']}"
                )

            elif action == "deploy":
                return await self.github_api.trigger_deployment(
                    environment=parsed_command.get("environment", "production")
                )

            elif action == "full_deploy":
                # Full deployment flow
                commit_msg = parsed_command.get("commit_message")
                if not commit_msg:
                    commit_msg = await self.generate_commit_message(
                        parsed_command.get("original_text", "")
                    )

                return await self.github_api.full_deployment_flow(
                    commit_message=commit_msg,
                    create_pr=False,
                    deploy=True
                )

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def process_natural_language_request(self, text: str) -> Dict[str, Any]:
        """Main entry point for natural language requests"""
        logger.info(f"Processing request: {text}")

        # Parse the command
        parsed = self.parse_natural_language_command(text)

        if not parsed["success"]:
            return parsed

        # Execute the command
        result = await self.execute_command(parsed)

        return {
            "success": result.get("success", False),
            "action": parsed["action"],
            "parsed_command": parsed,
            "execution_result": result,
            "timestamp": datetime.now().isoformat()
        }


def create_gateway(github_api, ollama_api):
    """Factory function to create gateway instance"""
    return FixItFredGateway(github_api, ollama_api)
