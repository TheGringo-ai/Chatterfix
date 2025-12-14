"""
ChatterFix UI Toolkit
=====================
Unified interface for AI team to generate accessible, themed UI components.

Combines:
- UIComponentGenerator for HTML generation
- DesignSystem for consistent theming
- AccessibilityChecker for WCAG compliance
"""

from typing import Dict, List, Any, Optional
from .ui_component_generator import UIComponentGenerator, ComponentType
from .design_system import DesignSystem, ChatterFixTheme, ColorMode
from .accessibility_checker import AccessibilityChecker, WCAGLevel


class UIToolkit:
    """
    Unified UI generation toolkit for the AI team.

    Usage:
        toolkit = UIToolkit()

        # Generate a validated card
        card = toolkit.generate_validated_component(
            component_type="card",
            title="Work Order #123",
            body="Equipment maintenance required",
            variant="primary"
        )

        # Generate complete page
        page = toolkit.generate_page(
            title="Dashboard",
            components=[card1, card2, card3]
        )
    """

    def __init__(self, dark_mode: bool = False, wcag_level: WCAGLevel = WCAGLevel.AA):
        self.theme = ChatterFixTheme(ColorMode.DARK if dark_mode else ColorMode.LIGHT)
        self.design_system = DesignSystem(self.theme)
        self.generator = UIComponentGenerator()
        self.accessibility = AccessibilityChecker(wcag_level)

    def generate_validated_component(
        self,
        component_type: str,
        validate: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a UI component with optional accessibility validation.

        Args:
            component_type: Type of component (button, card, form, etc.)
            validate: Whether to validate accessibility
            **kwargs: Component-specific parameters

        Returns:
            Dict with html, issues (if validated), and metadata
        """
        # Map string to method
        generators = {
            "button": self.generator.button,
            "card": self.generator.card,
            "stat_card": self.generator.stat_card,
            "work_order_card": self.generator.work_order_card,
            "form_input": self.generator.form_input,
            "form": self.generator.form,
            "modal": self.generator.modal,
            "table": self.generator.table,
            "alert": self.generator.alert,
            "toast": self.generator.toast,
            "breadcrumb": self.generator.breadcrumb,
            "tabs": self.generator.tabs,
            "spinner": self.generator.spinner,
            "progress": self.generator.progress,
            "badge": self.generator.badge,
        }

        generator_fn = generators.get(component_type.lower())
        if not generator_fn:
            return {
                "success": False,
                "error": f"Unknown component type: {component_type}",
                "available_types": list(generators.keys())
            }

        try:
            html = generator_fn(**kwargs)

            result = {
                "success": True,
                "html": html,
                "component_type": component_type,
                "tokens": self.design_system.get_component_tokens(component_type)
            }

            if validate:
                issues = self.accessibility.validate_html(html)
                result["accessibility"] = {
                    "issues": len(issues),
                    "errors": len([i for i in issues if i.issue_type.value == "error"]),
                    "warnings": len([i for i in issues if i.issue_type.value == "warning"]),
                    "details": [
                        {
                            "type": i.issue_type.value,
                            "criterion": i.wcag_criterion,
                            "message": i.message,
                            "suggestion": i.suggestion
                        }
                        for i in issues
                    ]
                }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "component_type": component_type
            }

    def generate_work_order_ui(self, work_order: Dict[str, Any]) -> str:
        """
        Generate complete UI for a work order.

        Args:
            work_order: Work order data with fields like id, title, status, priority, etc.

        Returns:
            Complete HTML for work order display
        """
        wo_number = work_order.get("id", work_order.get("wo_number", "N/A"))
        title = work_order.get("title", "Untitled Work Order")
        status = work_order.get("status", "open")
        priority = work_order.get("priority", "medium")
        description = work_order.get("description", "")
        asset = work_order.get("asset", "")
        assigned_to = work_order.get("assigned_to", "Unassigned")
        due_date = work_order.get("due_date", "")

        # Generate work order card
        return self.generator.work_order_card(
            wo_number=wo_number,
            title=title,
            status=status,
            priority=priority,
            asset=asset,
            assigned_to=assigned_to,
            due_date=due_date,
            description=description
        )

    def generate_dashboard_stats(self, stats: List[Dict[str, Any]]) -> str:
        """
        Generate dashboard statistics display.

        Args:
            stats: List of stat dicts with value, title/label, icon, optional trend

        Returns:
            HTML for stat cards in a responsive grid
        """
        stat_cards = []
        for stat in stats:
            card = self.generator.stat_card(
                title=stat.get("title", stat.get("label", "")),
                value=str(stat.get("value", "0")),
                icon=stat.get("icon", "bi-bar-chart"),
                trend=stat.get("trend"),
                trend_direction=stat.get("trend_direction", "up"),
                color=stat.get("color", "primary")
            )
            stat_cards.append(f'<div class="col-sm-6 col-lg-3">{card}</div>')

        return f'<div class="row g-3">{"".join(stat_cards)}</div>'

    def generate_data_table(
        self,
        headers: List[str],
        rows: List[List[str]],
        actions: Optional[List[str]] = None
    ) -> str:
        """
        Generate an accessible data table.

        Args:
            headers: Column headers
            rows: Table data rows
            actions: Optional action buttons for each row

        Returns:
            HTML for data table
        """
        return self.generator.table(
            headers=headers,
            rows=rows,
            striped=True,
            hover=True,
            responsive=True
        )

    def generate_form(
        self,
        fields: List[Dict[str, Any]],
        action: str = "",
        method: str = "POST",
        submit_text: str = "Submit"
    ) -> str:
        """
        Generate an accessible form.

        Args:
            fields: List of field dicts with name, label, type/input_type, etc.
            action: Form action URL
            method: HTTP method
            submit_text: Submit button text

        Returns:
            HTML for form
        """
        # Transform field keys for generator compatibility
        transformed_fields = []
        for field in fields:
            tf = field.copy()
            # Handle type -> input_type
            if 'type' in tf and 'input_type' not in tf:
                tf['input_type'] = tf.pop('type')
            # Remove unsupported keys that might cause errors
            for key in ['min', 'max', 'minlength', 'maxlength']:
                tf.pop(key, None)
            transformed_fields.append(tf)

        return self.generator.form(
            fields=transformed_fields,
            action=action,
            method=method,
            submit_text=submit_text
        )

    def generate_page(
        self,
        title: str,
        content: str,
        include_nav: bool = True,
        scripts: Optional[List[str]] = None
    ) -> str:
        """
        Generate a complete HTML page with ChatterFix theming.

        Args:
            title: Page title
            content: Main content HTML
            include_nav: Whether to include navigation
            scripts: Additional script URLs

        Returns:
            Complete HTML page
        """
        nav_html = ""
        if include_nav:
            nav_html = """
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
                <div class="container">
                    <a class="navbar-brand" href="/">ChatterFix</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
                            data-bs-target="#navbarNav" aria-controls="navbarNav"
                            aria-expanded="false" aria-label="Toggle navigation">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                </div>
            </nav>
            """

        scripts_html = ""
        if scripts:
            scripts_html = "\n".join([f'<script src="{s}"></script>' for s in scripts])

        css_vars = self.design_system.get_css_variables()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - ChatterFix</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        {css_vars}
        {self.design_system.get_utility_classes()}
    </style>
</head>
<body>
    {nav_html}
    <main class="container" role="main">
        <h1>{title}</h1>
        {content}
    </main>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    {scripts_html}
</body>
</html>"""

    def validate_html(self, html: str) -> Dict[str, Any]:
        """
        Validate HTML for accessibility issues.

        Args:
            html: HTML content to validate

        Returns:
            Accessibility report
        """
        issues = self.accessibility.validate_html(html)
        return self.accessibility.generate_report(issues)

    def get_color_for_status(self, status: str) -> str:
        """Get appropriate Bootstrap color class for work order status."""
        return self.design_system.get_color_for_status(status)

    def get_color_for_priority(self, priority: str) -> str:
        """Get appropriate Bootstrap color class for priority level."""
        return self.design_system.get_color_for_priority(priority)

    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        self.theme.toggle_mode()
        self.design_system = DesignSystem(self.theme)

    def get_available_components(self) -> List[str]:
        """Get list of available component types."""
        return [ct.value for ct in ComponentType]

    def get_design_tokens(self) -> Dict[str, Any]:
        """Get all design tokens as dictionary."""
        return self.design_system.to_dict()


# Convenience function for AI team
def get_ui_toolkit(dark_mode: bool = False) -> UIToolkit:
    """Get a UI toolkit instance for the AI team."""
    return UIToolkit(dark_mode=dark_mode)
