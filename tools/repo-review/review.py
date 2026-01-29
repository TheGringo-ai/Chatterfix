#!/usr/bin/env python3
"""
Repo Maintenance Review - Read-only repository analysis tool.

Analyzes public GitHub repositories and generates maintenance reports.
No code execution. No PRs. No modifications. Read-only.
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

from cloner import clone_repo, cleanup_repo
from detector import detect_stack
from analyzers import run_all_analyzers
from reporter import generate_report
from ai_review import get_ai_analysis


def main():
    parser = argparse.ArgumentParser(
        description="Read-only maintenance review for public GitHub repos"
    )
    parser.add_argument("repo_url", help="Public GitHub repository URL")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI analysis")
    parser.add_argument("--keep-clone", action="store_true", help="Don't delete cloned repo")

    args = parser.parse_args()

    print(f"[*] Repo Maintenance Review")
    print(f"[*] Target: {args.repo_url}")
    print(f"[*] Mode: READ-ONLY (no modifications)")
    print()

    # Clone repository
    print("[1/5] Cloning repository...")
    clone_path = clone_repo(args.repo_url, verbose=args.verbose)
    if not clone_path:
        print("[ERROR] Failed to clone repository")
        sys.exit(1)

    try:
        # Detect stack
        print("[2/5] Detecting stack...")
        stack_info = detect_stack(clone_path)
        if args.verbose:
            print(f"      Stack: {stack_info}")

        # Run analyzers
        print("[3/5] Running analyzers...")
        analysis_results = run_all_analyzers(clone_path, stack_info, verbose=args.verbose)

        # AI analysis (optional)
        ai_insights = None
        if not args.no_ai:
            print("[4/5] Getting AI analysis...")
            ai_insights = get_ai_analysis(clone_path, stack_info, analysis_results)
        else:
            print("[4/5] Skipping AI analysis (--no-ai)")

        # Generate report
        print("[5/5] Generating report...")
        report = generate_report(
            repo_url=args.repo_url,
            stack_info=stack_info,
            analysis_results=analysis_results,
            ai_insights=ai_insights
        )

        # Output
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(report)
            print(f"\n[*] Report saved to: {output_path}")
        else:
            print("\n" + "=" * 60)
            print(report)
            print("=" * 60)

        print("\n[*] Review complete. No modifications made.")

    finally:
        # Cleanup
        if not args.keep_clone:
            cleanup_repo(clone_path)
            if args.verbose:
                print("[*] Cleaned up temporary files")


if __name__ == "__main__":
    main()
