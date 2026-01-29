"""
ChatterFix Code Reviewer
========================
AI-powered code review for generated and modified code.

Features:
- Security vulnerability detection
- Code quality analysis
- Best practices validation
- Performance suggestions
- ChatterFix pattern compliance
"""

import ast
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(Enum):
    """Issue categories"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    STYLE = "style"
    BEST_PRACTICE = "best_practice"
    ACCESSIBILITY = "accessibility"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ERROR_HANDLING = "error_handling"
    CHATTERFIX_PATTERN = "chatterfix_pattern"


@dataclass
class ReviewIssue:
    """A single code review issue"""
    severity: Severity
    category: Category
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    rule_id: Optional[str] = None


@dataclass
class ReviewResult:
    """Complete code review result"""
    passed: bool
    issues: List[ReviewIssue]
    summary: Dict[str, int]
    score: float  # 0.0 to 100.0
    recommendations: List[str]


class CodeReviewer:
    """
    AI-powered code review for ChatterFix codebase.

    Checks for:
    - Security vulnerabilities (SQL injection, XSS, etc.)
    - Code quality issues
    - Performance problems
    - Best practice violations
    - ChatterFix-specific patterns
    - Accessibility concerns
    """

    # Security patterns to detect
    SECURITY_PATTERNS = [
        (r"eval\s*\(", "SEC001", "Use of eval() is dangerous", Severity.CRITICAL),
        (r"exec\s*\(", "SEC002", "Use of exec() is dangerous", Severity.CRITICAL),
        (r"subprocess\..*shell\s*=\s*True", "SEC003", "Shell injection risk", Severity.CRITICAL),
        (r"os\.system\s*\(", "SEC004", "Use subprocess instead of os.system", Severity.HIGH),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "SEC005", "Hardcoded password detected", Severity.CRITICAL),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "SEC006", "Hardcoded API key detected", Severity.CRITICAL),
        (r"\.format\s*\(.*user", "SEC007", "Potential format string injection", Severity.MEDIUM),
        (r"cursor\.execute\s*\([^,]+%", "SEC008", "Potential SQL injection", Severity.CRITICAL),
        (r"innerHTML\s*=", "SEC009", "Potential XSS via innerHTML", Severity.HIGH),
        (r"dangerouslySetInnerHTML", "SEC010", "Dangerous HTML setting", Severity.HIGH),
    ]

    # Quality patterns to detect
    QUALITY_PATTERNS = [
        (r"except:\s*$", "QUA001", "Bare except clause catches all exceptions", Severity.MEDIUM),
        (r"except\s+Exception:", "QUA002", "Catching broad Exception", Severity.LOW),
        (r"# TODO", "QUA003", "TODO comment found", Severity.INFO),
        (r"# FIXME", "QUA004", "FIXME comment found", Severity.LOW),
        (r"# HACK", "QUA005", "HACK comment found", Severity.MEDIUM),
        (r"print\s*\(", "QUA006", "Print statement (use logging)", Severity.LOW),
        (r"import \*", "QUA007", "Wildcard import", Severity.MEDIUM),
        (r"\.sleep\s*\(\s*\d+\s*\)", "QUA008", "Magic number in sleep", Severity.LOW),
        (r"==\s*True", "QUA009", "Redundant == True comparison", Severity.INFO),
        (r"==\s*False", "QUA010", "Redundant == False comparison", Severity.INFO),
    ]

    # Performance patterns
    PERFORMANCE_PATTERNS = [
        (r"for .* in .*\.items\(\):", "PER001", "Consider if you need both key and value", Severity.INFO),
        (r"\+\s*=.*\+\s*=.*\+\s*=", "PER002", "Multiple string concatenations (use join)", Severity.LOW),
        (r"\.append\(.*\) for .* in", "PER003", "Consider list comprehension", Severity.INFO),
        (r"await.*for .* in", "PER004", "Sequential awaits (consider gather)", Severity.MEDIUM),
        (r"\.get\(.*\)\.get\(", "PER005", "Nested dict.get() calls", Severity.INFO),
    ]

    # ChatterFix-specific patterns
    CHATTERFIX_PATTERNS = [
        (r"datetime\.utcnow\(\)", "CF001", "Use datetime.now(timezone.utc) instead of deprecated utcnow()", Severity.MEDIUM),
        (r"\.strftime\s*\([^)]*%[^Y]", "CF002", "Non-standard date format", Severity.INFO),
        (r"async def.*:\s*\n\s*return", "CF003", "Async function with immediate return", Severity.INFO),
        (r"response\.json\(\)", "CF004", "Check for response.ok before .json()", Severity.MEDIUM),
    ]

    # Documentation patterns
    DOC_PATTERNS = [
        (r"^def [^_].*\):\s*\n\s*[^\"']", "DOC001", "Public function missing docstring", Severity.LOW),
        (r"^class [^_].*:\s*\n\s*[^\"']", "DOC002", "Public class missing docstring", Severity.LOW),
    ]

    def __init__(self):
        self.all_patterns = (
            [(p, Category.SECURITY) for p in self.SECURITY_PATTERNS] +
            [(p, Category.QUALITY) for p in self.QUALITY_PATTERNS] +
            [(p, Category.PERFORMANCE) for p in self.PERFORMANCE_PATTERNS] +
            [(p, Category.CHATTERFIX_PATTERN) for p in self.CHATTERFIX_PATTERNS] +
            [(p, Category.DOCUMENTATION) for p in self.DOC_PATTERNS]
        )

    def review_code(self, code: str, filename: Optional[str] = None) -> ReviewResult:
        """
        Review code for issues.

        Args:
            code: Source code to review
            filename: Optional filename for context

        Returns:
            ReviewResult with all findings
        """
        issues = []

        # Run pattern-based checks
        issues.extend(self._check_patterns(code, filename))

        # Run AST-based checks for Python
        if filename is None or filename.endswith(".py"):
            issues.extend(self._check_ast(code, filename))

        # Run structural checks
        issues.extend(self._check_structure(code, filename))

        # Calculate summary
        summary = {
            "critical": len([i for i in issues if i.severity == Severity.CRITICAL]),
            "high": len([i for i in issues if i.severity == Severity.HIGH]),
            "medium": len([i for i in issues if i.severity == Severity.MEDIUM]),
            "low": len([i for i in issues if i.severity == Severity.LOW]),
            "info": len([i for i in issues if i.severity == Severity.INFO]),
        }

        # Calculate score (100 - weighted issues)
        score = 100.0
        score -= summary["critical"] * 20
        score -= summary["high"] * 10
        score -= summary["medium"] * 5
        score -= summary["low"] * 2
        score -= summary["info"] * 0.5
        score = max(0.0, score)

        # Determine if passed
        passed = summary["critical"] == 0 and summary["high"] <= 2

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        return ReviewResult(
            passed=passed,
            issues=issues,
            summary=summary,
            score=score,
            recommendations=recommendations,
        )

    def _check_patterns(self, code: str, filename: Optional[str]) -> List[ReviewIssue]:
        """Check code against regex patterns"""
        issues = []
        lines = code.split("\n")

        for (pattern, rule_id, message, severity), category in self.all_patterns:
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(ReviewIssue(
                        severity=severity,
                        category=category,
                        message=message,
                        file=filename,
                        line=line_num,
                        code_snippet=line.strip()[:100],
                        rule_id=rule_id,
                    ))

        return issues

    def _check_ast(self, code: str, filename: Optional[str]) -> List[ReviewIssue]:
        """Check code using AST analysis"""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(ReviewIssue(
                severity=Severity.CRITICAL,
                category=Category.QUALITY,
                message=f"Syntax error: {e.msg}",
                file=filename,
                line=e.lineno,
                rule_id="SYN001",
            ))
            return issues

        # Check for various AST patterns
        for node in ast.walk(tree):
            # Check for too many arguments
            if isinstance(node, ast.FunctionDef):
                if len(node.args.args) > 7:
                    issues.append(ReviewIssue(
                        severity=Severity.MEDIUM,
                        category=Category.QUALITY,
                        message=f"Function '{node.name}' has too many arguments ({len(node.args.args)})",
                        file=filename,
                        line=node.lineno,
                        suggestion="Consider using a dataclass or dict for parameters",
                        rule_id="AST001",
                    ))

                # Check for too long functions
                func_length = node.end_lineno - node.lineno if node.end_lineno else 0
                if func_length > 50:
                    issues.append(ReviewIssue(
                        severity=Severity.LOW,
                        category=Category.QUALITY,
                        message=f"Function '{node.name}' is too long ({func_length} lines)",
                        file=filename,
                        line=node.lineno,
                        suggestion="Consider breaking into smaller functions",
                        rule_id="AST002",
                    ))

            # Check for nested functions (complexity)
            if isinstance(node, ast.FunctionDef):
                nested_funcs = sum(1 for n in ast.walk(node) if isinstance(n, ast.FunctionDef))
                if nested_funcs > 3:
                    issues.append(ReviewIssue(
                        severity=Severity.LOW,
                        category=Category.QUALITY,
                        message=f"Too many nested functions in '{node.name}'",
                        file=filename,
                        line=node.lineno,
                        rule_id="AST003",
                    ))

            # Check for global usage
            if isinstance(node, ast.Global):
                issues.append(ReviewIssue(
                    severity=Severity.MEDIUM,
                    category=Category.QUALITY,
                    message="Use of global variable",
                    file=filename,
                    line=node.lineno,
                    suggestion="Consider passing as parameter or using a class",
                    rule_id="AST004",
                ))

        return issues

    def _check_structure(self, code: str, filename: Optional[str]) -> List[ReviewIssue]:
        """Check code structure and organization"""
        issues = []
        lines = code.split("\n")

        # Check line length
        for line_num, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(ReviewIssue(
                    severity=Severity.INFO,
                    category=Category.STYLE,
                    message=f"Line exceeds 120 characters ({len(line)})",
                    file=filename,
                    line=line_num,
                    rule_id="STY001",
                ))

        # Check for imports organization
        import_lines = [i for i, l in enumerate(lines) if l.startswith("import ") or l.startswith("from ")]
        if import_lines:
            # Check for imports not at top
            first_import = import_lines[0]
            non_import_before = any(
                lines[i].strip() and not lines[i].startswith("#") and not lines[i].startswith('"""')
                for i in range(first_import)
            )
            if non_import_before:
                issues.append(ReviewIssue(
                    severity=Severity.LOW,
                    category=Category.STYLE,
                    message="Imports should be at the top of the file",
                    file=filename,
                    line=first_import + 1,
                    rule_id="STY002",
                ))

        # Check file length
        if len(lines) > 500:
            issues.append(ReviewIssue(
                severity=Severity.LOW,
                category=Category.QUALITY,
                message=f"File is too long ({len(lines)} lines)",
                file=filename,
                suggestion="Consider splitting into multiple modules",
                rule_id="STY003",
            ))

        return issues

    def _generate_recommendations(self, issues: List[ReviewIssue]) -> List[str]:
        """Generate recommendations based on issues found"""
        recommendations = []

        # Group issues by category
        categories = {}
        for issue in issues:
            cat = issue.category.value
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        # Generate recommendations
        if categories.get("security", 0) > 0:
            recommendations.append("🔒 Address all security issues before deployment")

        if categories.get("performance", 0) > 2:
            recommendations.append("⚡ Review performance patterns for optimization opportunities")

        if categories.get("documentation", 0) > 3:
            recommendations.append("📚 Add docstrings to public functions and classes")

        if categories.get("error_handling", 0) > 0:
            recommendations.append("🛡️ Improve error handling with specific exception types")

        if categories.get("quality", 0) > 5:
            recommendations.append("✨ Consider refactoring to improve code quality")

        if categories.get("chatterfix_pattern", 0) > 0:
            recommendations.append("📐 Follow ChatterFix patterns for consistency")

        if not recommendations:
            recommendations.append("✅ Code looks good! No major issues found.")

        return recommendations

    def review_feature(
        self,
        models_code: str,
        service_code: str,
        router_code: str,
        feature_name: str
    ) -> Dict[str, ReviewResult]:
        """Review a complete feature (models, service, router)"""

        return {
            "models": self.review_code(models_code, f"{feature_name}/models.py"),
            "service": self.review_code(service_code, f"{feature_name}/service.py"),
            "router": self.review_code(router_code, f"{feature_name}/router.py"),
        }

    def generate_report(self, result: ReviewResult) -> str:
        """Generate a human-readable review report"""

        report = f"""
# Code Review Report

## Summary
- **Score:** {result.score:.1f}/100
- **Status:** {"✅ PASSED" if result.passed else "❌ FAILED"}

## Issue Counts
- Critical: {result.summary['critical']}
- High: {result.summary['high']}
- Medium: {result.summary['medium']}
- Low: {result.summary['low']}
- Info: {result.summary['info']}

## Recommendations
"""
        for rec in result.recommendations:
            report += f"- {rec}\n"

        if result.issues:
            report += "\n## Issues\n\n"

            # Group by severity
            for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
                severity_issues = [i for i in result.issues if i.severity == severity]
                if severity_issues:
                    report += f"### {severity.value.upper()}\n\n"
                    for issue in severity_issues[:10]:  # Limit to 10 per severity
                        report += f"- **[{issue.rule_id or 'N/A'}]** {issue.message}"
                        if issue.line:
                            report += f" (line {issue.line})"
                        report += "\n"
                        if issue.suggestion:
                            report += f"  - 💡 {issue.suggestion}\n"
                    report += "\n"

        return report


def get_code_reviewer() -> CodeReviewer:
    """Get a CodeReviewer instance"""
    return CodeReviewer()
