"""
ChatterFix Accessibility Checker
================================
Basic WCAG compliance validation for generated UI components.

Provides:
- Color contrast validation
- ARIA attribute checking
- Touch target size validation
- Semantic HTML validation
- Keyboard navigation checks
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class WCAGLevel(Enum):
    """WCAG conformance levels"""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class IssueType(Enum):
    """Types of accessibility issues"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class AccessibilityIssue:
    """Represents an accessibility issue found during validation"""
    issue_type: IssueType
    wcag_criterion: str
    message: str
    element: Optional[str] = None
    suggestion: Optional[str] = None


class AccessibilityChecker:
    """
    Validates HTML components for WCAG compliance.

    Usage:
        checker = AccessibilityChecker()
        issues = checker.validate_html(html_content)
        report = checker.generate_report(issues)
    """

    # Minimum contrast ratios per WCAG level
    CONTRAST_RATIOS = {
        WCAGLevel.AA: {"normal": 4.5, "large": 3.0},
        WCAGLevel.AAA: {"normal": 7.0, "large": 4.5},
    }

    # Minimum touch target sizes (px)
    MIN_TOUCH_TARGET = 44

    # Required ARIA attributes for interactive elements
    INTERACTIVE_ELEMENTS = {
        "button": ["aria-label", "aria-pressed", "aria-expanded"],
        "a": ["aria-label"],
        "input": ["aria-label", "aria-labelledby", "aria-describedby"],
        "select": ["aria-label", "aria-labelledby"],
        "dialog": ["aria-labelledby", "aria-describedby", "role"],
        "nav": ["aria-label"],
        "main": ["role"],
        "aside": ["aria-label"],
    }

    def __init__(self, level: WCAGLevel = WCAGLevel.AA):
        self.level = level

    def validate_html(self, html: str) -> List[AccessibilityIssue]:
        """
        Validate HTML content for accessibility issues.

        Args:
            html: HTML string to validate

        Returns:
            List of AccessibilityIssue objects
        """
        issues = []

        # Run all validation checks
        issues.extend(self._check_images(html))
        issues.extend(self._check_links(html))
        issues.extend(self._check_buttons(html))
        issues.extend(self._check_forms(html))
        issues.extend(self._check_headings(html))
        issues.extend(self._check_landmarks(html))
        issues.extend(self._check_tables(html))
        issues.extend(self._check_touch_targets(html))
        issues.extend(self._check_language(html))
        issues.extend(self._check_focus_indicators(html))

        return issues

    def _check_images(self, html: str) -> List[AccessibilityIssue]:
        """Check images for alt text (WCAG 1.1.1)"""
        issues = []
        img_pattern = re.compile(r'<img[^>]*>', re.IGNORECASE)

        for match in img_pattern.finditer(html):
            img_tag = match.group()
            if 'alt=' not in img_tag.lower():
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.ERROR,
                    wcag_criterion="1.1.1",
                    message="Image missing alt attribute",
                    element=img_tag[:80],
                    suggestion='Add alt="" for decorative images or descriptive alt text'
                ))
            elif 'alt=""' in img_tag and 'role="presentation"' not in img_tag:
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.WARNING,
                    wcag_criterion="1.1.1",
                    message="Empty alt text without presentation role",
                    element=img_tag[:80],
                    suggestion='Add role="presentation" for decorative images'
                ))

        return issues

    def _check_links(self, html: str) -> List[AccessibilityIssue]:
        """Check links for accessible names (WCAG 2.4.4)"""
        issues = []
        link_pattern = re.compile(r'<a[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)

        for match in link_pattern.finditer(html):
            full_tag = match.group()
            content = match.group(1).strip()

            # Check for empty links
            if not content and 'aria-label' not in full_tag.lower():
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.ERROR,
                    wcag_criterion="2.4.4",
                    message="Link has no accessible name",
                    element=full_tag[:80],
                    suggestion="Add text content or aria-label"
                ))

            # Check for generic link text
            generic_texts = ['click here', 'read more', 'learn more', 'here', 'more']
            if content.lower() in generic_texts:
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.WARNING,
                    wcag_criterion="2.4.4",
                    message=f"Generic link text '{content}'",
                    element=full_tag[:80],
                    suggestion="Use descriptive link text that makes sense out of context"
                ))

            # Check for href
            if 'href=' not in full_tag.lower():
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.ERROR,
                    wcag_criterion="2.4.4",
                    message="Link missing href attribute",
                    element=full_tag[:80],
                    suggestion="Add href or use a button if it triggers an action"
                ))

        return issues

    def _check_buttons(self, html: str) -> List[AccessibilityIssue]:
        """Check buttons for accessible names (WCAG 4.1.2)"""
        issues = []
        button_pattern = re.compile(r'<button[^>]*>(.*?)</button>', re.IGNORECASE | re.DOTALL)

        for match in button_pattern.finditer(html):
            full_tag = match.group()
            content = match.group(1).strip()

            # Remove HTML tags from content
            text_content = re.sub(r'<[^>]+>', '', content).strip()

            if not text_content and 'aria-label' not in full_tag.lower():
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.ERROR,
                    wcag_criterion="4.1.2",
                    message="Button has no accessible name",
                    element=full_tag[:80],
                    suggestion="Add text content or aria-label"
                ))

        # Check for divs/spans with onclick that should be buttons
        clickable_div_pattern = re.compile(r'<(div|span)[^>]*onclick[^>]*>', re.IGNORECASE)
        for match in clickable_div_pattern.finditer(html):
            tag = match.group()
            if 'role="button"' not in tag.lower() and 'tabindex' not in tag.lower():
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.ERROR,
                    wcag_criterion="4.1.2",
                    message="Clickable element should be a button",
                    element=tag[:80],
                    suggestion='Use <button> or add role="button" and tabindex="0"'
                ))

        return issues

    def _check_forms(self, html: str) -> List[AccessibilityIssue]:
        """Check form elements for labels (WCAG 1.3.1, 3.3.2)"""
        issues = []

        # Check inputs for labels
        input_pattern = re.compile(r'<input[^>]*>', re.IGNORECASE)
        for match in input_pattern.finditer(html):
            input_tag = match.group()

            # Skip hidden, submit, button, reset types
            if any(t in input_tag.lower() for t in ['type="hidden"', 'type="submit"', 'type="button"', 'type="reset"']):
                continue

            # Check for labeling mechanism
            has_label = any(attr in input_tag.lower() for attr in ['aria-label', 'aria-labelledby', 'id='])
            if not has_label:
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.ERROR,
                    wcag_criterion="1.3.1",
                    message="Form input missing label",
                    element=input_tag[:80],
                    suggestion="Add aria-label, aria-labelledby, or associate with <label>"
                ))

            # Check for placeholder-only labeling
            if 'placeholder=' in input_tag.lower() and 'aria-label' not in input_tag.lower():
                if 'id=' not in input_tag.lower():
                    issues.append(AccessibilityIssue(
                        issue_type=IssueType.WARNING,
                        wcag_criterion="3.3.2",
                        message="Placeholder should not be the only label",
                        element=input_tag[:80],
                        suggestion="Add a visible label or aria-label"
                    ))

        # Check select elements
        select_pattern = re.compile(r'<select[^>]*>', re.IGNORECASE)
        for match in select_pattern.finditer(html):
            select_tag = match.group()
            has_label = any(attr in select_tag.lower() for attr in ['aria-label', 'aria-labelledby', 'id='])
            if not has_label:
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.ERROR,
                    wcag_criterion="1.3.1",
                    message="Select element missing label",
                    element=select_tag[:80],
                    suggestion="Add aria-label or associate with <label>"
                ))

        return issues

    def _check_headings(self, html: str) -> List[AccessibilityIssue]:
        """Check heading hierarchy (WCAG 1.3.1)"""
        issues = []
        heading_pattern = re.compile(r'<h([1-6])[^>]*>', re.IGNORECASE)

        headings = [(int(m.group(1)), m.start()) for m in heading_pattern.finditer(html)]

        if not headings:
            return issues

        # Check for h1
        h1_count = sum(1 for h in headings if h[0] == 1)
        if h1_count == 0:
            issues.append(AccessibilityIssue(
                issue_type=IssueType.WARNING,
                wcag_criterion="1.3.1",
                message="Page should have an h1 heading",
                suggestion="Add an h1 element to identify the main content"
            ))
        elif h1_count > 1:
            issues.append(AccessibilityIssue(
                issue_type=IssueType.WARNING,
                wcag_criterion="1.3.1",
                message=f"Multiple h1 headings found ({h1_count})",
                suggestion="Consider having only one h1 per page"
            ))

        # Check for skipped levels
        prev_level = 0
        for level, _ in headings:
            if level > prev_level + 1 and prev_level > 0:
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.WARNING,
                    wcag_criterion="1.3.1",
                    message=f"Heading level skipped: h{prev_level} to h{level}",
                    suggestion="Use sequential heading levels"
                ))
            prev_level = level

        return issues

    def _check_landmarks(self, html: str) -> List[AccessibilityIssue]:
        """Check for proper landmark regions (WCAG 1.3.1)"""
        issues = []

        landmarks = {
            'main': (r'<main[^>]*>|role=["\']main["\']', "main"),
            'nav': (r'<nav[^>]*>|role=["\']navigation["\']', "navigation"),
            'header': (r'<header[^>]*>|role=["\']banner["\']', "banner"),
            'footer': (r'<footer[^>]*>|role=["\']contentinfo["\']', "contentinfo"),
        }

        for name, (pattern, role_name) in landmarks.items():
            if not re.search(pattern, html, re.IGNORECASE):
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.INFO,
                    wcag_criterion="1.3.1",
                    message=f"Consider adding {name} landmark",
                    suggestion=f'Use <{name}> or role="{role_name}"'
                ))

        return issues

    def _check_tables(self, html: str) -> List[AccessibilityIssue]:
        """Check tables for accessibility (WCAG 1.3.1)"""
        issues = []
        table_pattern = re.compile(r'<table[^>]*>.*?</table>', re.IGNORECASE | re.DOTALL)

        for match in table_pattern.finditer(html):
            table = match.group()

            # Check for headers
            if '<th' not in table.lower():
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.ERROR,
                    wcag_criterion="1.3.1",
                    message="Data table missing header cells",
                    element=table[:80],
                    suggestion="Add <th> elements to identify column/row headers"
                ))

            # Check for scope attribute on th
            th_pattern = re.compile(r'<th[^>]*>', re.IGNORECASE)
            for th_match in th_pattern.finditer(table):
                th_tag = th_match.group()
                if 'scope=' not in th_tag.lower():
                    issues.append(AccessibilityIssue(
                        issue_type=IssueType.WARNING,
                        wcag_criterion="1.3.1",
                        message="Table header missing scope attribute",
                        element=th_tag[:80],
                        suggestion='Add scope="col" or scope="row"'
                    ))
                    break  # Only report once per table

            # Check for caption or aria-labelledby
            if '<caption' not in table.lower() and 'aria-labelledby' not in table.lower():
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.WARNING,
                    wcag_criterion="1.3.1",
                    message="Table missing caption",
                    suggestion="Add <caption> to describe the table"
                ))

        return issues

    def _check_touch_targets(self, html: str) -> List[AccessibilityIssue]:
        """Check touch target sizes (WCAG 2.5.5)"""
        issues = []

        # Look for explicit small size classes
        small_patterns = [
            (r'btn-sm', "Small button may have insufficient touch target"),
            (r'form-control-sm', "Small form control may have insufficient touch target"),
        ]

        for pattern, message in small_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                issues.append(AccessibilityIssue(
                    issue_type=IssueType.WARNING,
                    wcag_criterion="2.5.5",
                    message=message,
                    suggestion=f"Ensure minimum {self.MIN_TOUCH_TARGET}x{self.MIN_TOUCH_TARGET}px touch target"
                ))

        return issues

    def _check_language(self, html: str) -> List[AccessibilityIssue]:
        """Check for language attribute (WCAG 3.1.1)"""
        issues = []

        if '<html' in html.lower() and 'lang=' not in html.lower():
            issues.append(AccessibilityIssue(
                issue_type=IssueType.ERROR,
                wcag_criterion="3.1.1",
                message="Page missing language attribute",
                suggestion='Add lang="en" (or appropriate language) to <html>'
            ))

        return issues

    def _check_focus_indicators(self, html: str) -> List[AccessibilityIssue]:
        """Check for focus indicator removal (WCAG 2.4.7)"""
        issues = []

        # Check for outline: none or outline: 0 in style attributes
        if re.search(r'outline:\s*(none|0)', html, re.IGNORECASE):
            issues.append(AccessibilityIssue(
                issue_type=IssueType.ERROR,
                wcag_criterion="2.4.7",
                message="Focus indicator removed with outline: none",
                suggestion="Provide alternative focus indicator or remove outline: none"
            ))

        return issues

    def check_color_contrast(self, foreground: str, background: str) -> Tuple[float, bool, bool]:
        """
        Calculate color contrast ratio between two colors.

        Args:
            foreground: Hex color string (e.g., "#000000")
            background: Hex color string (e.g., "#ffffff")

        Returns:
            Tuple of (contrast_ratio, passes_AA, passes_AAA)
        """
        def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def relative_luminance(rgb: Tuple[int, int, int]) -> float:
            def channel_luminance(value: int) -> float:
                v = value / 255
                return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
            r, g, b = rgb
            return 0.2126 * channel_luminance(r) + 0.7152 * channel_luminance(g) + 0.0722 * channel_luminance(b)

        l1 = relative_luminance(hex_to_rgb(foreground))
        l2 = relative_luminance(hex_to_rgb(background))

        lighter = max(l1, l2)
        darker = min(l1, l2)
        ratio = (lighter + 0.05) / (darker + 0.05)

        passes_aa = ratio >= self.CONTRAST_RATIOS[WCAGLevel.AA]["normal"]
        passes_aaa = ratio >= self.CONTRAST_RATIOS[WCAGLevel.AAA]["normal"]

        return round(ratio, 2), passes_aa, passes_aaa

    def generate_report(self, issues: List[AccessibilityIssue]) -> Dict[str, Any]:
        """
        Generate an accessibility report from validation issues.

        Args:
            issues: List of AccessibilityIssue objects

        Returns:
            Dictionary containing the report
        """
        errors = [i for i in issues if i.issue_type == IssueType.ERROR]
        warnings = [i for i in issues if i.issue_type == IssueType.WARNING]
        info = [i for i in issues if i.issue_type == IssueType.INFO]

        return {
            "summary": {
                "total_issues": len(issues),
                "errors": len(errors),
                "warnings": len(warnings),
                "info": len(info),
                "wcag_level": self.level.value,
                "passes": len(errors) == 0,
            },
            "errors": [
                {
                    "criterion": i.wcag_criterion,
                    "message": i.message,
                    "element": i.element,
                    "suggestion": i.suggestion,
                }
                for i in errors
            ],
            "warnings": [
                {
                    "criterion": i.wcag_criterion,
                    "message": i.message,
                    "element": i.element,
                    "suggestion": i.suggestion,
                }
                for i in warnings
            ],
            "info": [
                {
                    "criterion": i.wcag_criterion,
                    "message": i.message,
                    "suggestion": i.suggestion,
                }
                for i in info
            ],
        }

    def get_wcag_checklist(self) -> List[Dict[str, str]]:
        """Get a checklist of WCAG criteria covered by this checker"""
        return [
            {"criterion": "1.1.1", "name": "Non-text Content", "level": "A"},
            {"criterion": "1.3.1", "name": "Info and Relationships", "level": "A"},
            {"criterion": "2.4.4", "name": "Link Purpose", "level": "A"},
            {"criterion": "2.4.7", "name": "Focus Visible", "level": "AA"},
            {"criterion": "2.5.5", "name": "Target Size", "level": "AAA"},
            {"criterion": "3.1.1", "name": "Language of Page", "level": "A"},
            {"criterion": "3.3.2", "name": "Labels or Instructions", "level": "A"},
            {"criterion": "4.1.2", "name": "Name, Role, Value", "level": "A"},
        ]
