#!/usr/bin/env python3
"""
Navigation Component for ChatterFix CMMS
Provides consistent navigation across all modules
"""

def get_base_styles():
    """Base styles for the CMMS system"""
    return """
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .btn { 
            padding: 10px 20px; 
            background: #667eea; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            text-decoration: none;
            display: inline-block;
            margin: 5px;
        }
        .btn:hover { background: #5a6fd8; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    """

def get_navigation_styles():
    """Navigation specific styles"""
    return """
        .cmms-nav {
            background: rgba(0,0,0,0.3);
            backdrop-filter: blur(15px);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav-brand {
            font-size: 1.5rem;
            font-weight: bold;
            color: #38ef7d;
        }
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: background 0.3s ease;
        }
        .nav-link:hover {
            background: rgba(255,255,255,0.1);
        }
        .nav-link.active {
            background: rgba(56,239,125,0.2);
            color: #38ef7d;
        }
    """

def get_navigation_html(current_page="", breadcrumbs=None):
    """Generate navigation HTML"""
    nav_items = [
        ("Dashboard", "/"),
        ("Work Orders", "/work-orders"), 
        ("Assets", "/assets"),
        ("Parts", "/parts"),
        ("Reports", "/reports"),
        ("AI Dashboard", "/ai-dashboard")
    ]
    
    nav_links_html = ""
    for name, url in nav_items:
        active_class = "active" if current_page == url else ""
        nav_links_html += f'<a href="{url}" class="nav-link {active_class}">{name}</a>'
    
    breadcrumb_html = ""
    if breadcrumbs:
        breadcrumb_html = f"""
        <div class="breadcrumbs" style="padding: 0.5rem 2rem; background: rgba(0,0,0,0.2); font-size: 0.9rem;">
            {' > '.join(breadcrumbs)}
        </div>
        """
    
    return f"""
    <nav class="cmms-nav">
        <div class="nav-brand">🔧 ChatterFix CMMS</div>
        <div class="nav-links">
            {nav_links_html}
        </div>
    </nav>
    {breadcrumb_html}
    """

def get_navigation_javascript():
    """Navigation specific JavaScript"""
    return """
        // Navigation active state management
        document.addEventListener('DOMContentLoaded', function() {
            const currentPath = window.location.pathname;
            const navLinks = document.querySelectorAll('.nav-link');
            
            navLinks.forEach(link => {
                if (link.getAttribute('href') === currentPath) {
                    link.classList.add('active');
                }
            });
        });
    """