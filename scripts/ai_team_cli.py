#!/usr/bin/env python3
"""
AI Team CLI - Command Line Interface for ChatterFix AI Team
============================================================

This script provides direct access to the AI Team's autonomous building
capabilities from the command line or Claude Code.

Usage:
    # Execute a task with the AI team
    python scripts/ai_team_cli.py execute "Create a budget tracking feature"

    # Invoke the autonomous builder
    python scripts/ai_team_cli.py build "I need expense management for maintenance"

    # Request code review
    python scripts/ai_team_cli.py review path/to/file.py

    # Generate a feature
    python scripts/ai_team_cli.py generate "inventory_alerts" "Alert system for low stock"

    # Check AI team health
    python scripts/ai_team_cli.py health

    # List available AI models
    python scripts/ai_team_cli.py models
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.clients.ai_team_client import (
    AITeamHTTPClient,
    get_ai_team_client,
    execute_ai_task,
    invoke_autonomous_builder,
    ai_code_review,
    check_ai_team_health
)


async def cmd_execute(args):
    """Execute a collaborative AI task"""
    print(f"\n{'='*60}")
    print(f"AI TEAM TASK EXECUTION")
    print(f"{'='*60}")
    print(f"Task: {args.prompt}")
    print(f"{'='*60}\n")

    client = await get_ai_team_client()

    agents = args.agents.split(",") if args.agents else None

    result = await client.execute_task(
        prompt=args.prompt,
        context=args.context or "",
        required_agents=agents,
        max_iterations=args.iterations
    )

    if result.get("success"):
        print("\n" + "="*60)
        print("RESULT:")
        print("="*60)
        print(result.get("final_answer", "No answer generated"))

        if args.verbose:
            print("\n" + "-"*60)
            print("AGENT RESPONSES:")
            print("-"*60)
            for resp in result.get("agent_responses", []):
                print(f"\n[{resp.get('agent')}] ({resp.get('model_type')}):")
                print(resp.get("response", "")[:500])

        print(f"\nConfidence: {result.get('confidence_score', 0):.2%}")
        print(f"Time: {result.get('total_time', 0):.2f}s")
    else:
        print(f"\nERROR: {result.get('error', 'Unknown error')}")
        return 1

    return 0


async def cmd_build(args):
    """Invoke the Autonomous ChatterFix Builder"""
    print(f"\n{'='*60}")
    print(f"AUTONOMOUS CHATTERFIX BUILDER")
    print(f"{'='*60}")
    print(f"Request: {args.request}")
    print(f"Auto Deploy: {args.deploy}")
    print(f"{'='*60}\n")

    print("Invoking AI Team with all available models...")
    print("- CustomerRequirementAnalyzer: Analyzing requirements")
    print("- FeatureImplementer: Generating code")
    print("- DeploymentAgent: Preparing deployment")
    print("- CustomerInterface: Preparing response\n")

    client = await get_ai_team_client()
    result = await client.invoke_autonomous_builder(
        customer_request=args.request,
        auto_deploy=args.deploy
    )

    if result.get("success"):
        print("\n" + "="*60)
        print("BUILD RESULT:")
        print("="*60)
        print(result.get("final_answer", "Build completed"))

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nFull result saved to: {args.output}")
    else:
        print(f"\nBUILD FAILED: {result.get('error', 'Unknown error')}")
        return 1

    return 0


async def cmd_review(args):
    """Request AI-powered code review"""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return 1

    print(f"\n{'='*60}")
    print(f"AI CODE REVIEW")
    print(f"{'='*60}")
    print(f"File: {file_path}")
    print(f"{'='*60}\n")

    code = file_path.read_text()

    client = await get_ai_team_client()
    result = await client.code_review(code, str(file_path))

    if result.get("success"):
        print("\n" + "="*60)
        print("REVIEW RESULT:")
        print("="*60)
        print(result.get("final_answer", "No review generated"))
    else:
        print(f"\nREVIEW FAILED: {result.get('error', 'Unknown error')}")
        return 1

    return 0


async def cmd_generate(args):
    """Generate a complete feature"""
    print(f"\n{'='*60}")
    print(f"AI FEATURE GENERATION")
    print(f"{'='*60}")
    print(f"Feature: {args.name}")
    print(f"Description: {args.description}")
    print(f"Type: {args.type}")
    print(f"{'='*60}\n")

    client = await get_ai_team_client()
    result = await client.generate_feature(
        feature_name=args.name,
        description=args.description,
        feature_type=args.type
    )

    if result.get("success"):
        print("\n" + "="*60)
        print("GENERATED FEATURE:")
        print("="*60)
        print(result.get("final_answer", "No output generated"))

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nFull result saved to: {args.output}")
    else:
        print(f"\nGENERATION FAILED: {result.get('error', 'Unknown error')}")
        return 1

    return 0


async def cmd_health(args):
    """Check AI Team service health"""
    print(f"\n{'='*60}")
    print(f"AI TEAM HEALTH CHECK")
    print(f"{'='*60}\n")

    client = await get_ai_team_client()
    result = await client.health_check()

    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Service: {result.get('service', 'AI Team Service')}")
    print(f"Version: {result.get('version', 'unknown')}")
    print(f"Models Count: {result.get('ai_models_count', 0)}")
    print(f"Orchestrator: {'Ready' if result.get('orchestrator_initialized') else 'Not initialized'}")

    if result.get('error'):
        print(f"Error: {result.get('error')}")
        return 1

    return 0


async def cmd_models(args):
    """List available AI models"""
    print(f"\n{'='*60}")
    print(f"AVAILABLE AI MODELS")
    print(f"{'='*60}\n")

    client = await get_ai_team_client()
    models = await client.get_available_models()

    if models:
        for model in models:
            print(f"- {model.get('name')}")
            print(f"  Type: {model.get('model_type')}")
            print(f"  Role: {model.get('role')}")
            print(f"  Capabilities: {', '.join(model.get('capabilities', []))}")
            print(f"  Status: {model.get('status')}")
            print()
    else:
        print("No models available or service not running")
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="AI Team CLI - ChatterFix Autonomous Building Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s execute "Analyze the codebase structure"
  %(prog)s build "I need budget tracking for maintenance"
  %(prog)s review app/routers/work_orders.py
  %(prog)s generate inventory_alerts "Alert system for low stock"
  %(prog)s health
  %(prog)s models
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Execute command
    exec_parser = subparsers.add_parser("execute", help="Execute a collaborative AI task")
    exec_parser.add_argument("prompt", help="The task to execute")
    exec_parser.add_argument("-c", "--context", help="Additional context")
    exec_parser.add_argument("-a", "--agents", help="Comma-separated list of agents (claude,chatgpt,gemini,grok)")
    exec_parser.add_argument("-i", "--iterations", type=int, default=3, help="Max iterations")
    exec_parser.add_argument("-v", "--verbose", action="store_true", help="Show all agent responses")

    # Build command
    build_parser = subparsers.add_parser("build", help="Invoke the Autonomous Builder")
    build_parser.add_argument("request", help="Natural language feature request")
    build_parser.add_argument("-d", "--deploy", action="store_true", help="Auto-deploy changes")
    build_parser.add_argument("-o", "--output", help="Save result to file")

    # Review command
    review_parser = subparsers.add_parser("review", help="AI-powered code review")
    review_parser.add_argument("file", help="File to review")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a feature")
    gen_parser.add_argument("name", help="Feature name (snake_case)")
    gen_parser.add_argument("description", help="Feature description")
    gen_parser.add_argument("-t", "--type", default="crud", choices=["crud", "api", "ui", "service"])
    gen_parser.add_argument("-o", "--output", help="Save result to file")

    # Health command
    subparsers.add_parser("health", help="Check AI Team service health")

    # Models command
    subparsers.add_parser("models", help="List available AI models")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run the appropriate command
    commands = {
        "execute": cmd_execute,
        "build": cmd_build,
        "review": cmd_review,
        "generate": cmd_generate,
        "health": cmd_health,
        "models": cmd_models,
    }

    return asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    sys.exit(main())
