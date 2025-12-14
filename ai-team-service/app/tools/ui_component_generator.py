"""
UI Component Generator
======================
Generate Bootstrap 5 / Tailwind CSS components for ChatterFix CMMS.

Supports:
- Buttons, Cards, Forms, Modals, Tables, Alerts
- Responsive layouts
- Dark/Light theme variants
- Accessibility attributes built-in
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ComponentType(Enum):
    """Available UI component types"""
    BUTTON = "button"
    CARD = "card"
    FORM = "form"
    FORM_INPUT = "form_input"
    MODAL = "modal"
    TABLE = "table"
    ALERT = "alert"
    NAVBAR = "navbar"
    SIDEBAR = "sidebar"
    BADGE = "badge"
    PROGRESS = "progress"
    SPINNER = "spinner"
    TOAST = "toast"
    DROPDOWN = "dropdown"
    TABS = "tabs"
    ACCORDION = "accordion"
    BREADCRUMB = "breadcrumb"
    PAGINATION = "pagination"
    STAT_CARD = "stat_card"
    WORK_ORDER_CARD = "work_order_card"
    ASSET_CARD = "asset_card"


class ButtonVariant(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    LIGHT = "light"
    DARK = "dark"
    OUTLINE_PRIMARY = "outline-primary"
    OUTLINE_SECONDARY = "outline-secondary"


class ButtonSize(Enum):
    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"


@dataclass
class ComponentSpec:
    """Specification for generating a component"""
    component_type: ComponentType
    variant: str = "primary"
    size: str = "md"
    text: str = ""
    icon: Optional[str] = None
    disabled: bool = False
    loading: bool = False
    href: Optional[str] = None
    onclick: Optional[str] = None
    custom_class: str = ""
    aria_label: Optional[str] = None
    data_attributes: Dict[str, str] = field(default_factory=dict)
    children: List["ComponentSpec"] = field(default_factory=list)
    props: Dict[str, Any] = field(default_factory=dict)


class UIComponentGenerator:
    """
    Generate HTML/CSS components for ChatterFix CMMS.

    Usage:
        generator = UIComponentGenerator()

        # Generate a button
        html = generator.button("Save Work Order", variant="success", icon="fa-save")

        # Generate a card
        html = generator.card(
            title="Pump Maintenance",
            body="Scheduled maintenance for pump #42",
            footer_actions=[("Complete", "success"), ("Reschedule", "warning")]
        )

        # Generate a form
        html = generator.form(fields=[
            {"name": "title", "type": "text", "label": "Work Order Title", "required": True},
            {"name": "priority", "type": "select", "label": "Priority", "options": ["Low", "Medium", "High"]},
            {"name": "description", "type": "textarea", "label": "Description"}
        ])
    """

    def __init__(self, framework: str = "bootstrap"):
        self.framework = framework  # "bootstrap" or "tailwind"
        self.generated_components: List[str] = []

    # ==================== BUTTONS ====================

    def button(
        self,
        text: str,
        variant: str = "primary",
        size: str = "md",
        icon: Optional[str] = None,
        disabled: bool = False,
        loading: bool = False,
        href: Optional[str] = None,
        onclick: Optional[str] = None,
        custom_class: str = "",
        aria_label: Optional[str] = None,
        button_type: str = "button",
        full_width: bool = False,
    ) -> str:
        """Generate a button component"""

        # Build classes
        classes = [f"btn btn-{variant}"]
        if size != "md":
            classes.append(f"btn-{size}")
        if full_width:
            classes.append("w-100")
        if custom_class:
            classes.append(custom_class)

        class_str = " ".join(classes)

        # Build attributes
        attrs = [f'class="{class_str}"']
        if disabled or loading:
            attrs.append("disabled")
        if onclick and not href:
            attrs.append(f'onclick="{onclick}"')
        if aria_label:
            attrs.append(f'aria-label="{aria_label}"')
        else:
            attrs.append(f'aria-label="{text}"')

        # Icon HTML
        icon_html = ""
        if icon:
            icon_html = f'<i class="{icon} me-2"></i>'

        # Loading spinner
        if loading:
            icon_html = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>'
            text = "Loading..."

        attr_str = " ".join(attrs)

        # Generate as link or button
        if href:
            return f'<a href="{href}" {attr_str}>{icon_html}{text}</a>'
        else:
            return f'<button type="{button_type}" {attr_str}>{icon_html}{text}</button>'

    def button_group(self, buttons: List[Dict[str, Any]], vertical: bool = False) -> str:
        """Generate a button group"""
        orientation = "btn-group-vertical" if vertical else "btn-group"
        buttons_html = "\n    ".join([self.button(**btn) for btn in buttons])
        return f'''<div class="{orientation}" role="group" aria-label="Button group">
    {buttons_html}
</div>'''

    # ==================== CARDS ====================

    def card(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        body: Optional[str] = None,
        image_src: Optional[str] = None,
        image_alt: str = "",
        header: Optional[str] = None,
        footer: Optional[str] = None,
        footer_actions: Optional[List[tuple]] = None,
        custom_class: str = "",
        body_class: str = "",
        clickable: bool = False,
        href: Optional[str] = None,
    ) -> str:
        """Generate a card component"""

        classes = ["card"]
        if clickable:
            classes.append("card-hover cursor-pointer")
        if custom_class:
            classes.append(custom_class)

        parts = []

        # Image
        if image_src:
            parts.append(f'<img src="{image_src}" class="card-img-top" alt="{image_alt}">')

        # Header
        if header:
            parts.append(f'<div class="card-header">{header}</div>')

        # Body
        body_parts = []
        if title:
            body_parts.append(f'<h5 class="card-title">{title}</h5>')
        if subtitle:
            body_parts.append(f'<h6 class="card-subtitle mb-2 text-muted">{subtitle}</h6>')
        if body:
            body_parts.append(f'<p class="card-text">{body}</p>')

        if body_parts:
            body_content = "\n        ".join(body_parts)
            parts.append(f'''<div class="card-body {body_class}">
        {body_content}
    </div>''')

        # Footer
        if footer:
            parts.append(f'<div class="card-footer">{footer}</div>')
        elif footer_actions:
            actions_html = " ".join([
                self.button(text, variant=variant, size="sm")
                for text, variant in footer_actions
            ])
            parts.append(f'<div class="card-footer d-flex gap-2">{actions_html}</div>')

        content = "\n    ".join(parts)
        class_str = " ".join(classes)

        card_html = f'''<div class="{class_str}">
    {content}
</div>'''

        if href:
            return f'<a href="{href}" class="text-decoration-none">{card_html}</a>'
        return card_html

    def stat_card(
        self,
        title: str,
        value: str,
        icon: str,
        trend: Optional[str] = None,
        trend_direction: str = "up",
        color: str = "primary",
    ) -> str:
        """Generate a statistics card (dashboard widget)"""

        trend_html = ""
        if trend:
            trend_icon = "fa-arrow-up" if trend_direction == "up" else "fa-arrow-down"
            trend_color = "text-success" if trend_direction == "up" else "text-danger"
            trend_html = f'<small class="{trend_color}"><i class="fas {trend_icon}"></i> {trend}</small>'

        return f'''<div class="card border-{color} border-start border-4">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <h6 class="text-muted mb-1">{title}</h6>
                <h3 class="mb-0">{value}</h3>
                {trend_html}
            </div>
            <div class="bg-{color} bg-opacity-10 rounded-circle p-3">
                <i class="{icon} fa-2x text-{color}"></i>
            </div>
        </div>
    </div>
</div>'''

    def work_order_card(
        self,
        wo_number: str,
        title: str,
        status: str,
        priority: str,
        asset: str,
        assigned_to: str,
        due_date: str,
        description: Optional[str] = None,
    ) -> str:
        """Generate a work order card for ChatterFix CMMS"""

        # Status badge color
        status_colors = {
            "open": "primary",
            "in_progress": "warning",
            "completed": "success",
            "on_hold": "secondary",
            "cancelled": "danger",
        }
        status_color = status_colors.get(status.lower().replace(" ", "_"), "secondary")

        # Priority badge color
        priority_colors = {
            "low": "success",
            "medium": "warning",
            "high": "danger",
            "critical": "danger",
        }
        priority_color = priority_colors.get(priority.lower(), "secondary")

        desc_html = f'<p class="card-text text-muted small">{description}</p>' if description else ""

        return f'''<div class="card work-order-card mb-3" data-wo-number="{wo_number}">
    <div class="card-header d-flex justify-content-between align-items-center">
        <span class="fw-bold">#{wo_number}</span>
        <div>
            <span class="badge bg-{status_color} me-1">{status}</span>
            <span class="badge bg-{priority_color}">{priority}</span>
        </div>
    </div>
    <div class="card-body">
        <h5 class="card-title">{title}</h5>
        {desc_html}
        <div class="row small text-muted">
            <div class="col-6">
                <i class="fas fa-cog me-1"></i> {asset}
            </div>
            <div class="col-6">
                <i class="fas fa-user me-1"></i> {assigned_to}
            </div>
        </div>
    </div>
    <div class="card-footer d-flex justify-content-between align-items-center">
        <small class="text-muted"><i class="fas fa-calendar me-1"></i> Due: {due_date}</small>
        <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary" onclick="viewWorkOrder('{wo_number}')" aria-label="View work order">
                <i class="fas fa-eye"></i>
            </button>
            <button class="btn btn-outline-success" onclick="completeWorkOrder('{wo_number}')" aria-label="Complete work order">
                <i class="fas fa-check"></i>
            </button>
        </div>
    </div>
</div>'''

    # ==================== FORMS ====================

    def form_input(
        self,
        name: str,
        label: str,
        input_type: str = "text",
        placeholder: str = "",
        required: bool = False,
        disabled: bool = False,
        value: str = "",
        helper_text: Optional[str] = None,
        error_text: Optional[str] = None,
        options: Optional[List[str]] = None,
        rows: int = 3,
        custom_class: str = "",
    ) -> str:
        """Generate a form input field"""

        input_id = f"input-{name}"
        required_attr = "required" if required else ""
        disabled_attr = "disabled" if disabled else ""
        aria_describedby = f'aria-describedby="{input_id}-help"' if helper_text else ""

        # Label
        label_html = f'<label for="{input_id}" class="form-label">{label}'
        if required:
            label_html += ' <span class="text-danger">*</span>'
        label_html += '</label>'

        # Input based on type
        if input_type == "select" and options:
            options_html = "\n            ".join([
                f'<option value="{opt}">{opt}</option>' for opt in options
            ])
            input_html = f'''<select class="form-select {custom_class}" id="{input_id}" name="{name}" {required_attr} {disabled_attr} {aria_describedby}>
            <option value="">Select {label}...</option>
            {options_html}
        </select>'''
        elif input_type == "textarea":
            input_html = f'''<textarea class="form-control {custom_class}" id="{input_id}" name="{name}"
            rows="{rows}" placeholder="{placeholder}" {required_attr} {disabled_attr} {aria_describedby}>{value}</textarea>'''
        elif input_type == "checkbox":
            checked = "checked" if value else ""
            return f'''<div class="form-check {custom_class}">
        <input class="form-check-input" type="checkbox" id="{input_id}" name="{name}" {checked} {disabled_attr}>
        <label class="form-check-label" for="{input_id}">{label}</label>
    </div>'''
        elif input_type == "switch":
            checked = "checked" if value else ""
            return f'''<div class="form-check form-switch {custom_class}">
        <input class="form-check-input" type="checkbox" role="switch" id="{input_id}" name="{name}" {checked} {disabled_attr}>
        <label class="form-check-label" for="{input_id}">{label}</label>
    </div>'''
        else:
            input_html = f'''<input type="{input_type}" class="form-control {custom_class}" id="{input_id}"
            name="{name}" value="{value}" placeholder="{placeholder}" {required_attr} {disabled_attr} {aria_describedby}>'''

        # Helper text
        helper_html = ""
        if helper_text:
            helper_html = f'<div id="{input_id}-help" class="form-text">{helper_text}</div>'

        # Error text
        error_html = ""
        if error_text:
            error_html = f'<div class="invalid-feedback">{error_text}</div>'

        return f'''<div class="mb-3">
        {label_html}
        {input_html}
        {helper_html}
        {error_html}
    </div>'''

    def form(
        self,
        fields: List[Dict[str, Any]],
        action: str = "",
        method: str = "POST",
        submit_text: str = "Submit",
        cancel_text: Optional[str] = "Cancel",
        form_id: Optional[str] = None,
        enctype: Optional[str] = None,
        inline: bool = False,
    ) -> str:
        """Generate a complete form"""

        form_id_attr = f'id="{form_id}"' if form_id else ""
        enctype_attr = f'enctype="{enctype}"' if enctype else ""
        form_class = "row row-cols-lg-auto g-3 align-items-center" if inline else ""

        fields_html = "\n    ".join([
            self.form_input(**field) for field in fields
        ])

        cancel_btn = ""
        if cancel_text:
            cancel_btn = self.button(cancel_text, variant="secondary", custom_class="me-2", button_type="button")

        submit_btn = self.button(submit_text, variant="primary", button_type="submit", icon="fas fa-save")

        return f'''<form action="{action}" method="{method}" {form_id_attr} {enctype_attr} class="{form_class}">
    {fields_html}
    <div class="d-flex justify-content-end gap-2 mt-3">
        {cancel_btn}
        {submit_btn}
    </div>
</form>'''

    # ==================== MODALS ====================

    def modal(
        self,
        modal_id: str,
        title: str,
        body: str,
        footer_actions: Optional[List[Dict[str, Any]]] = None,
        size: str = "md",
        centered: bool = True,
        scrollable: bool = False,
        static_backdrop: bool = False,
    ) -> str:
        """Generate a modal dialog"""

        size_class = f"modal-{size}" if size != "md" else ""
        centered_class = "modal-dialog-centered" if centered else ""
        scrollable_class = "modal-dialog-scrollable" if scrollable else ""
        backdrop_attr = 'data-bs-backdrop="static"' if static_backdrop else ""

        dialog_classes = " ".join(filter(None, ["modal-dialog", size_class, centered_class, scrollable_class]))

        # Footer buttons
        footer_html = ""
        if footer_actions:
            buttons = " ".join([self.button(**action) for action in footer_actions])
            footer_html = f'''<div class="modal-footer">
                {buttons}
            </div>'''

        return f'''<div class="modal fade" id="{modal_id}" tabindex="-1" aria-labelledby="{modal_id}-label" aria-hidden="true" {backdrop_attr}>
    <div class="{dialog_classes}">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="{modal_id}-label">{title}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                {body}
            </div>
            {footer_html}
        </div>
    </div>
</div>'''

    # ==================== TABLES ====================

    def table(
        self,
        headers: List[str],
        rows: List[List[str]],
        striped: bool = True,
        hover: bool = True,
        bordered: bool = False,
        responsive: bool = True,
        caption: Optional[str] = None,
        sortable: bool = False,
        actions: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate a data table"""

        table_classes = ["table"]
        if striped:
            table_classes.append("table-striped")
        if hover:
            table_classes.append("table-hover")
        if bordered:
            table_classes.append("table-bordered")

        class_str = " ".join(table_classes)

        # Add actions column header if needed
        if actions:
            headers = headers + ["Actions"]

        # Header row
        sortable_attr = 'data-sortable="true"' if sortable else ""
        headers_html = "\n            ".join([
            f'<th scope="col" {sortable_attr}>{h}</th>' for h in headers
        ])

        # Data rows
        rows_html_list = []
        for row in rows:
            cells = [f"<td>{cell}</td>" for cell in row]

            # Add action buttons if specified
            if actions:
                action_buttons = " ".join([
                    f'<button class="btn btn-sm btn-{a.get("variant", "primary")}" '
                    f'onclick="{a.get("onclick", "")}" aria-label="{a.get("label", "Action")}">'
                    f'<i class="{a.get("icon", "fas fa-cog")}"></i></button>'
                    for a in actions
                ])
                cells.append(f'<td class="text-end">{action_buttons}</td>')

            rows_html_list.append(f"<tr>{''.join(cells)}</tr>")

        rows_html = "\n            ".join(rows_html_list)

        caption_html = f'<caption>{caption}</caption>' if caption else ""

        table_html = f'''<table class="{class_str}">
        {caption_html}
        <thead>
            <tr>
            {headers_html}
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>'''

        if responsive:
            return f'<div class="table-responsive">{table_html}</div>'
        return table_html

    # ==================== ALERTS & NOTIFICATIONS ====================

    def alert(
        self,
        message: str,
        variant: str = "info",
        dismissible: bool = True,
        icon: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        """Generate an alert component"""

        dismiss_class = "alert-dismissible fade show" if dismissible else ""
        dismiss_btn = ""
        if dismissible:
            dismiss_btn = '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'

        # Default icons based on variant
        default_icons = {
            "success": "fas fa-check-circle",
            "danger": "fas fa-exclamation-triangle",
            "warning": "fas fa-exclamation-circle",
            "info": "fas fa-info-circle",
            "primary": "fas fa-bell",
        }
        icon = icon or default_icons.get(variant, "fas fa-info-circle")

        title_html = f'<h5 class="alert-heading"><i class="{icon} me-2"></i>{title}</h5>' if title else f'<i class="{icon} me-2"></i>'

        return f'''<div class="alert alert-{variant} {dismiss_class}" role="alert">
    {title_html}
    {message if title else message}
    {dismiss_btn}
</div>'''

    def toast(
        self,
        title: str,
        message: str,
        variant: str = "primary",
        auto_hide: bool = True,
        delay: int = 5000,
    ) -> str:
        """Generate a toast notification"""

        auto_hide_attrs = f'data-bs-autohide="true" data-bs-delay="{delay}"' if auto_hide else 'data-bs-autohide="false"'

        return f'''<div class="toast" role="alert" aria-live="assertive" aria-atomic="true" {auto_hide_attrs}>
    <div class="toast-header bg-{variant} text-white">
        <strong class="me-auto">{title}</strong>
        <small>just now</small>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
    <div class="toast-body">
        {message}
    </div>
</div>'''

    # ==================== NAVIGATION ====================

    def breadcrumb(self, items: List[Dict[str, str]]) -> str:
        """Generate breadcrumb navigation"""

        items_html = []
        for i, item in enumerate(items):
            is_active = i == len(items) - 1
            if is_active:
                items_html.append(f'<li class="breadcrumb-item active" aria-current="page">{item["label"]}</li>')
            else:
                items_html.append(f'<li class="breadcrumb-item"><a href="{item.get("href", "#")}">{item["label"]}</a></li>')

        items_str = "\n        ".join(items_html)

        return f'''<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        {items_str}
    </ol>
</nav>'''

    def tabs(
        self,
        tabs: List[Dict[str, Any]],
        active_tab: int = 0,
        pills: bool = False,
        vertical: bool = False,
    ) -> str:
        """Generate tabbed navigation with content panels"""

        nav_class = "nav-pills" if pills else "nav-tabs"
        if vertical:
            nav_class += " flex-column"

        # Tab buttons
        tab_buttons = []
        tab_panes = []

        for i, tab in enumerate(tabs):
            is_active = i == active_tab
            active_class = "active" if is_active else ""
            show_class = "show active" if is_active else ""
            aria_selected = "true" if is_active else "false"
            tab_id = tab.get("id", f"tab-{i}")

            tab_buttons.append(
                f'<li class="nav-item" role="presentation">'
                f'<button class="nav-link {active_class}" id="{tab_id}-tab" data-bs-toggle="tab" '
                f'data-bs-target="#{tab_id}" type="button" role="tab" aria-controls="{tab_id}" '
                f'aria-selected="{aria_selected}">{tab["label"]}</button></li>'
            )

            tab_panes.append(
                f'<div class="tab-pane fade {show_class}" id="{tab_id}" role="tabpanel" '
                f'aria-labelledby="{tab_id}-tab">{tab.get("content", "")}</div>'
            )

        buttons_html = "\n        ".join(tab_buttons)
        panes_html = "\n        ".join(tab_panes)

        return f'''<ul class="nav {nav_class}" role="tablist">
        {buttons_html}
    </ul>
    <div class="tab-content mt-3">
        {panes_html}
    </div>'''

    # ==================== LOADING & PROGRESS ====================

    def spinner(self, variant: str = "primary", size: str = "md", text: Optional[str] = None) -> str:
        """Generate a loading spinner"""

        size_class = "spinner-border-sm" if size == "sm" else ""
        text_html = f'<span class="ms-2">{text}</span>' if text else ""

        return f'''<div class="d-flex align-items-center">
    <div class="spinner-border text-{variant} {size_class}" role="status">
        <span class="visually-hidden">Loading...</span>
    </div>
    {text_html}
</div>'''

    def progress(
        self,
        value: int,
        variant: str = "primary",
        striped: bool = False,
        animated: bool = False,
        label: bool = True,
        height: Optional[str] = None,
    ) -> str:
        """Generate a progress bar"""

        bar_classes = [f"progress-bar bg-{variant}"]
        if striped:
            bar_classes.append("progress-bar-striped")
        if animated:
            bar_classes.append("progress-bar-animated")

        bar_class = " ".join(bar_classes)
        label_text = f"{value}%" if label else ""
        height_style = f'style="height: {height}"' if height else ""

        return f'''<div class="progress" {height_style} role="progressbar" aria-valuenow="{value}" aria-valuemin="0" aria-valuemax="100">
    <div class="{bar_class}" style="width: {value}%">{label_text}</div>
</div>'''

    # ==================== BADGES ====================

    def badge(
        self,
        text: str,
        variant: str = "primary",
        pill: bool = False,
        icon: Optional[str] = None,
    ) -> str:
        """Generate a badge"""

        pill_class = "rounded-pill" if pill else ""
        icon_html = f'<i class="{icon} me-1"></i>' if icon else ""

        return f'<span class="badge bg-{variant} {pill_class}">{icon_html}{text}</span>'

    # ==================== UTILITY METHODS ====================

    def generate_page(
        self,
        title: str,
        components: List[str],
        include_bootstrap: bool = True,
        include_fontawesome: bool = True,
        custom_css: str = "",
        custom_js: str = "",
    ) -> str:
        """Generate a complete HTML page with components"""

        bootstrap_css = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">' if include_bootstrap else ""
        bootstrap_js = '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>' if include_bootstrap else ""
        fontawesome = '<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">' if include_fontawesome else ""

        content = "\n        ".join(components)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - ChatterFix CMMS</title>
    {bootstrap_css}
    {fontawesome}
    <style>
        {custom_css}
    </style>
</head>
<body>
    <div class="container py-4">
        {content}
    </div>
    {bootstrap_js}
    <script>
        {custom_js}
    </script>
</body>
</html>'''


# Convenience function for quick component generation
def generate_component(component_type: str, **kwargs) -> str:
    """Quick helper to generate a component"""
    generator = UIComponentGenerator()
    method = getattr(generator, component_type, None)
    if method:
        return method(**kwargs)
    raise ValueError(f"Unknown component type: {component_type}")
