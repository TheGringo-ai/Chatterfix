#!/usr/bin/env python3
"""
Security Gate Check Script for CI/CD Pipeline

This script analyzes security scan reports and determines if the build should proceed.
It checks:
- Safety report for vulnerable dependencies
- Bandit report for security issues in code

Exit codes:
- 0: All security checks passed
- 1: Security issues found that block deployment
"""

import json
import sys
import os
from pathlib import Path


def load_json_report(filename: str) -> dict:
    """Load a JSON report file if it exists."""
    path = Path(filename)
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {filename}")
            return {}
    return {}


def check_safety_report(report: dict) -> tuple[bool, list[str]]:
    """
    Check the safety report for critical vulnerabilities.
    Returns (passed, issues_list)
    """
    issues = []

    if not report:
        print("Info: No safety report found - skipping dependency vulnerability check")
        return True, []

    # Safety report format varies by version
    vulnerabilities = report.get('vulnerabilities', [])
    if isinstance(report, list):
        vulnerabilities = report

    critical_count = 0
    high_count = 0

    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'unknown').lower()
        package = vuln.get('package_name', vuln.get('name', 'unknown'))
        vuln_id = vuln.get('vulnerability_id', vuln.get('id', 'unknown'))

        if severity == 'critical':
            critical_count += 1
            issues.append(f"CRITICAL: {package} - {vuln_id}")
        elif severity == 'high':
            high_count += 1
            issues.append(f"HIGH: {package} - {vuln_id}")

    # Fail on critical vulnerabilities, warn on high
    passed = critical_count == 0

    if critical_count > 0:
        print(f"Found {critical_count} critical vulnerabilities - BLOCKING")
    if high_count > 0:
        print(f"Found {high_count} high vulnerabilities - WARNING")

    return passed, issues


def check_bandit_report(report: dict) -> tuple[bool, list[str]]:
    """
    Check the bandit report for security issues.
    Returns (passed, issues_list)
    """
    issues = []

    if not report:
        print("Info: No bandit report found - skipping static security analysis")
        return True, []

    results = report.get('results', [])

    high_severity_count = 0
    high_confidence_count = 0

    for result in results:
        severity = result.get('issue_severity', 'LOW')
        confidence = result.get('issue_confidence', 'LOW')
        issue_text = result.get('issue_text', 'Unknown issue')
        filename = result.get('filename', 'unknown')
        line = result.get('line_number', 0)

        # Only block on high severity + high confidence issues
        if severity == 'HIGH' and confidence == 'HIGH':
            high_severity_count += 1
            issues.append(f"HIGH/HIGH: {filename}:{line} - {issue_text}")
        elif severity == 'HIGH':
            high_confidence_count += 1
            issues.append(f"HIGH: {filename}:{line} - {issue_text}")

    # Fail only on high severity + high confidence issues
    passed = high_severity_count == 0

    if high_severity_count > 0:
        print(f"Found {high_severity_count} high severity/high confidence issues - BLOCKING")
    if high_confidence_count > 0:
        print(f"Found {high_confidence_count} high severity issues - WARNING")

    return passed, issues


def main():
    print("=" * 60)
    print("Security Gate Check")
    print("=" * 60)
    print()

    all_passed = True
    all_issues = []

    # Check safety report
    print("Checking dependency vulnerabilities (safety)...")
    safety_report = load_json_report('safety-report.json')
    safety_passed, safety_issues = check_safety_report(safety_report)
    all_passed = all_passed and safety_passed
    all_issues.extend(safety_issues)
    print()

    # Check bandit report
    print("Checking static security analysis (bandit)...")
    bandit_report = load_json_report('bandit-report.json')
    bandit_passed, bandit_issues = check_bandit_report(bandit_report)
    all_passed = all_passed and bandit_passed
    all_issues.extend(bandit_issues)
    print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("SECURITY GATE: PASSED")
        print("All security checks passed - deployment can proceed")
        print("=" * 60)
        return 0
    else:
        print("SECURITY GATE: FAILED")
        print("Security issues found that block deployment:")
        for issue in all_issues:
            print(f"  - {issue}")
        print()
        print("Please fix these issues before deploying to production")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
