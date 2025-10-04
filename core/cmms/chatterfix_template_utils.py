"""
ChatterFix CMMS Template Utilities
Provides standardized HTML template generation for all microservices
"""

import os
from typing import Dict, List, Optional

def load_base_template() -> str:
    """Load the base ChatterFix template"""
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'chatterfix_base.html')
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback inline template if file doesn't exist
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{service_title}} - ChatterFix CMMS</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-dark: #0a0a0a;
            --secondary-dark: #16213e;
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-purple: #667eea;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --bg-gradient: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            --bg-card: rgba(255, 255, 255, 0.05);
            --font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: var(--font-family); background: var(--bg-gradient); color: var(--text-primary); min-height: 100vh; }
        .navbar { position: fixed; top: 0; left: 0; right: 0; background: rgba(10, 10, 10, 0.8); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 16px 0; z-index: 1000; }
        .navbar-content { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: center; }
        .navbar-brand { background: var(--text-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; font-size: 1.25rem; }
        .page-header { padding: 120px 0 64px; text-align: center; background: var(--bg-gradient); }
        .page-header h1 { font-size: 3rem; font-weight: 800; background: var(--text-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.2; margin: 0; }
        .page-header .subtitle { margin: 1rem 0 0 0; color: var(--text-secondary); font-size: 1.2rem; font-weight: 400; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
        .btn-primary { background: var(--gradient-primary); color: var(--text-primary); border: none; border-radius: 50px; padding: 12px 32px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; text-decoration: none; display: inline-block; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4); }
        .card { background: var(--bg-card); border-radius: 16px; padding: 24px; backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); transition: all 0.3s ease; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; margin-bottom: 48px; }
        .stat-card { background: var(--bg-card); border-radius: 16px; padding: 24px; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(20px); text-align: center; transition: all 0.3s ease; }
        .stat-number { font-size: 2.5rem; font-weight: 700; background: var(--text-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: block; margin-bottom: 8px; }
        @media (max-width: 768px) { .page-header h1 { font-size: 2.25rem; } .container { padding: 0 16px; } }
        {{custom_styles}}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="navbar-brand">ChatterFix CMMS</div>
            <div>{{navigation_links}}</div>
        </div>
    </nav>
    <div class="page-header">
        <div class="container">
            <h1>{{service_icon}} {{service_name}}</h1>
            <p class="subtitle">{{service_description}}</p>
        </div>
    </div>
    <div class="container">
        {{main_content}}
    </div>
    <script>{{custom_scripts}}</script>
</body>
</html>"""

def generate_service_dashboard(
    service_name: str,
    service_description: str,
    service_icon: str = "🔧",
    stats: Optional[List[Dict[str, str]]] = None,
    features: Optional[List[Dict[str, str]]] = None,
    api_endpoints: Optional[List[str]] = None,
    custom_content: str = "",
    custom_styles: str = "",
    custom_scripts: str = "",
    navigation_links: str = ""
) -> str:
    """
    Generate a standardized service dashboard using ChatterFix design system
    
    Args:
        service_name: Name of the service (e.g., "Work Orders Service")
        service_description: Description of the service
        service_icon: Emoji icon for the service
        stats: List of statistics to display (e.g., [{"title": "Total", "value": "24", "id": "total"}])
        features: List of features to highlight (e.g., [{"icon": "🎯", "title": "Smart", "description": "..."}])
        api_endpoints: List of API endpoints to display
        custom_content: Additional HTML content
        custom_styles: Additional CSS styles
        custom_scripts: Additional JavaScript
        navigation_links: Navigation links HTML
    
    Returns:
        Complete HTML string for the service dashboard
    """
    
    template = load_base_template()
    
    # Generate stats section
    stats_html = ""
    if stats:
        stats_html = '<div class="stats-grid">'
        for stat in stats:
            stats_html += f'''
                <div class="stat-card">
                    <span class="stat-number" id="{stat.get('id', '')}">{stat.get('value', '-')}</span>
                    <div>{stat.get('title', '')}</div>
                </div>
            '''
        stats_html += '</div>'
    
    # Generate features section
    features_html = ""
    if features:
        features_html = '<div class="features-grid">'
        for feature in features:
            features_html += f'''
                <div class="feature-card">
                    <div style="font-size: 2rem; margin-bottom: 16px; color: var(--accent-purple);">{feature.get('icon', '🔧')}</div>
                    <h3 style="font-size: 1.5rem; font-weight: 600; color: var(--text-primary); margin-bottom: 12px;">{feature.get('title', '')}</h3>
                    <p style="color: var(--text-secondary); line-height: 1.6; margin: 0;">{feature.get('description', '')}</p>
                </div>
            '''
        features_html += '</div>'
    
    # Generate API endpoints section
    api_html = ""
    if api_endpoints:
        api_html = '''
            <div class="card mt-8">
                <h3 style="font-size: 1.875rem; font-weight: 600; color: var(--text-primary); margin-bottom: 24px;">🔗 API Endpoints</h3>
        '''
        for endpoint in api_endpoints:
            api_html += f'''
                <div style="background: rgba(0, 0, 0, 0.3); padding: 16px; margin: 8px 0; border-radius: 12px; font-family: 'Fira Code', 'Monaco', monospace; font-size: 0.875rem; color: var(--text-secondary); border: 1px solid rgba(255, 255, 255, 0.1);">
                    {endpoint}
                </div>
            '''
        api_html += '</div>'
    
    # Combine all content
    main_content = f"""
        {stats_html}
        {features_html}
        {api_html}
        {custom_content}
    """
    
    # Default navigation if none provided
    if not navigation_links:
        navigation_links = f'<span style="color: var(--text-secondary);">{service_name}</span>'
    
    # Replace template variables
    html = template.replace('{{service_title}}', service_name)
    html = html.replace('{{service_name}}', service_name)
    html = html.replace('{{service_description}}', service_description)
    html = html.replace('{{service_icon}}', service_icon)
    html = html.replace('{{main_content}}', main_content)
    html = html.replace('{{custom_styles}}', custom_styles)
    html = html.replace('{{custom_scripts}}', custom_scripts)
    html = html.replace('{{navigation_links}}', navigation_links)
    
    return html

def generate_form_html(fields: List[Dict[str, str]], form_id: str = "serviceForm", submit_text: str = "Submit") -> str:
    """
    Generate standardized form HTML
    
    Args:
        fields: List of form fields with type, name, label, placeholder, etc.
        form_id: ID for the form element
        submit_text: Text for submit button
    
    Returns:
        HTML string for the form
    """
    form_html = f'<form id="{form_id}" class="card">'
    
    for field in fields:
        field_type = field.get('type', 'text')
        field_name = field.get('name', '')
        field_label = field.get('label', '')
        field_placeholder = field.get('placeholder', '')
        field_required = 'required' if field.get('required', False) else ''
        field_options = field.get('options', [])
        
        form_html += f'''
            <div class="form-group">
                <label class="form-label" for="{field_name}">{field_label}</label>
        '''
        
        if field_type == 'select':
            form_html += f'<select id="{field_name}" name="{field_name}" class="form-input" {field_required}>'
            for option in field_options:
                if isinstance(option, dict):
                    value = option.get('value', '')
                    text = option.get('text', value)
                    selected = 'selected' if option.get('selected', False) else ''
                    form_html += f'<option value="{value}" {selected}>{text}</option>'
                else:
                    form_html += f'<option value="{option}">{option}</option>'
            form_html += '</select>'
        elif field_type == 'textarea':
            rows = field.get('rows', 3)
            form_html += f'<textarea id="{field_name}" name="{field_name}" class="form-input" rows="{rows}" placeholder="{field_placeholder}" {field_required}></textarea>'
        else:
            form_html += f'<input type="{field_type}" id="{field_name}" name="{field_name}" class="form-input" placeholder="{field_placeholder}" {field_required}>'
        
        form_html += '</div>'
    
    form_html += f'''
        <button type="submit" class="btn-primary" style="width: 100%;">
            {submit_text}
        </button>
    </form>
    '''
    
    return form_html

def generate_table_html(headers: List[str], rows: List[List[str]], table_id: str = "dataTable") -> str:
    """
    Generate standardized table HTML
    
    Args:
        headers: List of table headers
        rows: List of table rows (each row is a list of cell values)
        table_id: ID for the table element
    
    Returns:
        HTML string for the table
    """
    table_html = f'''
    <div class="table-container">
        <table id="{table_id}" class="chatterfix-table">
            <thead>
                <tr>
    '''
    
    for header in headers:
        table_html += f'<th>{header}</th>'
    
    table_html += '''
                </tr>
            </thead>
            <tbody>
    '''
    
    for row in rows:
        table_html += '<tr>'
        for cell in row:
            table_html += f'<td>{cell}</td>'
        table_html += '</tr>'
    
    table_html += '''
            </tbody>
        </table>
    </div>
    '''
    
    return table_html

# Standard service configurations
SERVICE_CONFIGS = {
    'work_orders': {
        'name': 'Work Orders Service',
        'description': 'Advanced AI-Powered Work Order Management',
        'icon': '🛠️',
        'stats': [
            {'title': 'Total Work Orders', 'value': '-', 'id': 'total-orders'},
            {'title': 'Open Orders', 'value': '-', 'id': 'open-orders'},
            {'title': 'In Progress', 'value': '-', 'id': 'in-progress-orders'},
            {'title': 'Completed', 'value': '-', 'id': 'completed-orders'}
        ],
        'features': [
            {'icon': '🎯', 'title': 'Smart Prioritization', 'description': 'Advanced AI algorithms automatically prioritize work orders based on criticality, asset importance, and resource availability.'},
            {'icon': '📅', 'title': 'Intelligent Scheduling', 'description': 'AI-powered scheduling engine optimizes technician assignments and minimizes equipment downtime.'},
            {'icon': '⚡', 'title': 'Real-time Tracking', 'description': 'Live status updates and progress tracking with automated notifications and escalations.'},
            {'icon': '🔄', 'title': 'Workflow Automation', 'description': 'Automated workflow management with conditional logic and approval processes.'}
        ],
        'api_endpoints': [
            'GET /api/work-orders - List all work orders',
            'POST /api/work-orders - Create new work order',
            'GET /api/work-orders/{id} - Get specific work order',
            'PUT /api/work-orders/{id} - Update work order',
            'DELETE /api/work-orders/{id} - Delete work order',
            'GET /api/work-orders/analytics - Advanced analytics',
            'POST /api/work-orders/{id}/assign - AI-powered assignment'
        ]
    },
    'assets': {
        'name': 'Assets Management',
        'description': 'Real-time Asset Lifecycle Management with AI-powered Analytics',
        'icon': '🏭',
        'stats': [
            {'title': 'Total Assets', 'value': '24', 'id': 'total-assets'},
            {'title': 'Active Assets', 'value': '18', 'id': 'active-assets'},
            {'title': 'Maintenance Due', 'value': '3', 'id': 'maintenance-due'},
            {'title': 'Total Value', 'value': '$2.4M', 'id': 'total-value'}
        ],
        'features': [
            {'icon': '📊', 'title': 'Predictive Analytics', 'description': 'AI-powered predictive maintenance scheduling based on usage patterns and historical data.'},
            {'icon': '🔧', 'title': 'Lifecycle Management', 'description': 'Complete asset tracking from acquisition to disposal with automated depreciation calculations.'},
            {'icon': '📍', 'title': 'Real-time Monitoring', 'description': 'Live asset location tracking and performance monitoring with IoT integration.'},
            {'icon': '📈', 'title': 'Performance Insights', 'description': 'Advanced analytics and reporting on asset utilization and efficiency metrics.'}
        ],
        'api_endpoints': [
            'GET /api/assets - List all assets',
            'POST /api/assets - Create new asset',
            'GET /api/assets/{id} - Get specific asset',
            'PUT /api/assets/{id} - Update asset',
            'DELETE /api/assets/{id} - Delete asset',
            'GET /api/assets/analytics - Asset analytics',
            'GET /api/assets/maintenance-schedule - Maintenance scheduling'
        ]
    },
    'parts': {
        'name': 'Parts Inventory',
        'description': 'Smart Inventory Management with AI-powered Demand Forecasting',
        'icon': '📦',
        'stats': [
            {'title': 'Total Parts', 'value': '1,247', 'id': 'total-parts'},
            {'title': 'Low Stock', 'value': '23', 'id': 'low-stock'},
            {'title': 'On Order', 'value': '156', 'id': 'on-order'},
            {'title': 'Total Value', 'value': '$87K', 'id': 'inventory-value'}
        ],
        'features': [
            {'icon': '🤖', 'title': 'AI Demand Forecasting', 'description': 'Predictive algorithms analyze usage patterns to optimize inventory levels and prevent stockouts.'},
            {'icon': '📱', 'title': 'Barcode Scanning', 'description': 'Mobile-friendly barcode scanning for quick parts identification and inventory updates.'},
            {'icon': '🚨', 'title': 'Smart Alerts', 'description': 'Automated low-stock alerts and reorder suggestions based on lead times and usage patterns.'},
            {'icon': '📊', 'title': 'Cost Optimization', 'description': 'Advanced analytics to identify cost-saving opportunities and optimize supplier relationships.'}
        ],
        'api_endpoints': [
            'GET /api/parts - List all parts',
            'POST /api/parts - Add new part',
            'GET /api/parts/{id} - Get specific part',
            'PUT /api/parts/{id} - Update part',
            'DELETE /api/parts/{id} - Delete part',
            'GET /api/parts/low-stock - Low stock alerts',
            'POST /api/parts/bulk-update - Bulk inventory update'
        ]
    },
    'ai_brain': {
        'name': 'AI Brain Service',
        'description': 'Advanced Machine Learning and Predictive Analytics Engine',
        'icon': '🧠',
        'stats': [
            {'title': 'Active Models', 'value': '12', 'id': 'active-models'},
            {'title': 'Predictions Today', 'value': '1,847', 'id': 'predictions-today'},
            {'title': 'Accuracy Score', 'value': '94.2%', 'id': 'accuracy-score'},
            {'title': 'Processing Power', 'value': '2.4 THz', 'id': 'processing-power'}
        ],
        'features': [
            {'icon': '🔮', 'title': 'Predictive Maintenance', 'description': 'Advanced ML models predict equipment failures before they occur, reducing downtime and costs.'},
            {'icon': '🎯', 'title': 'Resource Optimization', 'description': 'AI-driven resource allocation and scheduling optimization for maximum efficiency.'},
            {'icon': '📊', 'title': 'Pattern Recognition', 'description': 'Deep learning algorithms identify complex patterns in operational data for actionable insights.'},
            {'icon': '⚡', 'title': 'Real-time Processing', 'description': 'High-performance computing infrastructure for real-time data processing and decision making.'}
        ],
        'api_endpoints': [
            'POST /api/ai/predict - Make AI predictions',
            'POST /api/ai/analysis - Custom AI analysis',
            'GET /api/ai/models - List available models',
            'POST /api/ai/train - Train new models',
            'GET /api/ai/insights - Get AI insights',
            'POST /api/ai/optimize - Resource optimization',
            'GET /api/ai/performance - Model performance metrics'
        ]
    },
    'document_intelligence': {
        'name': 'Document Intelligence',
        'description': 'AI-Powered Document Processing and Information Extraction',
        'icon': '📄',
        'stats': [
            {'title': 'Documents Processed', 'value': '15,432', 'id': 'docs-processed'},
            {'title': 'Extraction Accuracy', 'value': '97.8%', 'id': 'extraction-accuracy'},
            {'title': 'Processing Speed', 'value': '2.3s avg', 'id': 'processing-speed'},
            {'title': 'Storage Used', 'value': '45.2 GB', 'id': 'storage-used'}
        ],
        'features': [
            {'icon': '🔍', 'title': 'OCR & Text Extraction', 'description': 'Advanced optical character recognition with support for multiple languages and document types.'},
            {'icon': '🏷️', 'title': 'Smart Classification', 'description': 'AI-powered document classification and automated tagging for easy organization and retrieval.'},
            {'icon': '📋', 'title': 'Data Extraction', 'description': 'Intelligent extraction of key information from invoices, work orders, and technical documents.'},
            {'icon': '🔗', 'title': 'System Integration', 'description': 'Seamless integration with existing CMMS workflows and automated data population.'}
        ],
        'api_endpoints': [
            'POST /api/documents/upload - Upload documents',
            'POST /api/documents/process - Process documents',
            'GET /api/documents/{id} - Get document details',
            'POST /api/documents/extract - Extract data',
            'GET /api/documents/search - Search documents',
            'POST /api/documents/classify - Classify documents',
            'GET /api/documents/analytics - Document analytics'
        ]
    }
}

def get_service_dashboard(service_key: str, custom_content: str = "", custom_scripts: str = "") -> str:
    """
    Get a standardized dashboard for a specific service
    
    Args:
        service_key: Key for the service (e.g., 'work_orders', 'assets', 'parts')
        custom_content: Additional HTML content to include
        custom_scripts: Additional JavaScript to include
    
    Returns:
        Complete HTML string for the service dashboard
    """
    if service_key not in SERVICE_CONFIGS:
        raise ValueError(f"Unknown service key: {service_key}")
    
    config = SERVICE_CONFIGS[service_key]
    
    return generate_service_dashboard(
        service_name=config['name'],
        service_description=config['description'],
        service_icon=config['icon'],
        stats=config['stats'],
        features=config['features'],
        api_endpoints=config['api_endpoints'],
        custom_content=custom_content,
        custom_scripts=custom_scripts
    )