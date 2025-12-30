#!/usr/bin/env python3
"""
Unified CMMS System Components
Provides consistent styling, navigation, and AI integration across all modules
"""

from navigation_component import get_navigation_html, get_navigation_styles, get_navigation_javascript, get_base_styles

def get_unified_styles() -> str:
    """
    Get unified CSS styles consistent across all CMMS modules
    Based on the preventive maintenance design with modern glassmorphism effects
    """
    return f"""
        {get_base_styles()}
        {get_navigation_styles()}
        
        /* Enhanced Unified CMMS Styling */
        .cmms-header {{ 
            background: rgba(0,0,0,0.3); 
            backdrop-filter: blur(15px);
            padding: 2rem;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 2rem;
        }}
        
        .cmms-header h1 {{ 
            font-size: 2.5rem; 
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .cmms-header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        
        /* Enhanced Cards */
        .cmms-card {{ 
            background: rgba(255,255,255,0.15); 
            border-radius: 15px; 
            padding: 2rem; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }}
        
        .cmms-card:hover {{
            transform: translateY(-5px);
            background: rgba(255,255,255,0.2);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        /* Stats and Metrics */
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 2rem; 
            margin-bottom: 2rem;
        }}
        
        .stat-card {{ 
            background: rgba(255,255,255,0.15); 
            border-radius: 12px; 
            padding: 1.5rem; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .stat-item {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin: 1rem 0; 
        }}
        
        .stat-value {{ 
            font-size: 2rem; 
            font-weight: bold; 
            text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        }}
        
        .status-operational, .status-good {{ color: #38ef7d; }}
        .status-maintenance, .status-warning {{ color: #fbbf24; }}
        .status-down, .status-critical {{ color: #ff6b6b; }}
        .status-overdue {{ color: #ff4757; }}
        .status-due {{ color: #ffa726; }}
        
        /* Enhanced Tables */
        .cmms-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 1rem; 
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            overflow: hidden;
            backdrop-filter: blur(5px);
        }}
        
        .cmms-table th, .cmms-table td {{ 
            padding: 1rem; 
            text-align: left; 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
        }}
        
        .cmms-table th {{ 
            background: rgba(0,0,0,0.3); 
            font-weight: 600; 
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }}
        
        /* Filter and Search */
        .filter-bar {{ 
            background: rgba(255,255,255,0.15); 
            backdrop-filter: blur(10px);
            padding: 1.5rem; 
            border-radius: 12px; 
            margin-bottom: 2rem; 
            display: flex; 
            flex-wrap: wrap;
            gap: 1rem; 
            align-items: center;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .filter-bar label {{
            color: white;
            font-weight: 500;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }}
        
        .filter-bar select, .filter-bar input {{ 
            padding: 0.5rem 1rem; 
            border: 1px solid rgba(255,255,255,0.3); 
            border-radius: 8px;
            background: rgba(255,255,255,0.2);
            color: white;
            backdrop-filter: blur(5px);
        }}
        
        .filter-bar select option {{
            background: #2d3748;
            color: white;
        }}
        
        .filter-bar input::placeholder {{
            color: rgba(255,255,255,0.7);
        }}
        
        /* Enhanced Buttons */
        .cmms-btn {{ 
            background: linear-gradient(135deg, #38ef7d, #11998e); 
            color: white; 
            border: none; 
            padding: 0.75rem 1.5rem; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            margin: 0.25rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            box-shadow: 0 4px 15px rgba(56,239,125,0.3);
        }}
        
        .cmms-btn:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(56,239,125,0.4);
        }}
        
        .cmms-btn-success {{ 
            background: linear-gradient(135deg, #38ef7d, #11998e);
        }}
        
        .cmms-btn-warning {{ 
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            box-shadow: 0 4px 15px rgba(251,191,36,0.3);
        }}
        
        .cmms-btn-warning:hover {{
            box-shadow: 0 6px 20px rgba(251,191,36,0.4);
        }}
        
        .cmms-btn-danger {{ 
            background: linear-gradient(135deg, #ff6b6b, #ee5a52);
            box-shadow: 0 4px 15px rgba(255,107,107,0.3);
        }}
        
        .cmms-btn-danger:hover {{
            box-shadow: 0 6px 20px rgba(255,107,107,0.4);
        }}
        
        .cmms-btn-sm {{ 
            padding: 0.5rem 1rem; 
            font-size: 0.875rem; 
        }}
        
        /* Item Cards with Priority Styling */
        .item-card {{ 
            background: rgba(255,255,255,0.15); 
            border-radius: 12px; 
            padding: 1.5rem; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }}
        
        .item-card:hover {{
            transform: translateY(-3px);
            background: rgba(255,255,255,0.2);
        }}
        
        .item-card.critical {{ 
            border-left: 4px solid #ff4757; 
            background: rgba(255,71,87,0.1);
        }}
        
        .item-card.high {{ 
            border-left: 4px solid #ffa726; 
            background: rgba(255,167,38,0.1);
        }}
        
        .item-card.medium {{ 
            border-left: 4px solid #38ef7d; 
            background: rgba(56,239,125,0.1);
        }}
        
        .item-card.low {{ 
            border-left: 4px solid #74b9ff; 
            background: rgba(116,185,255,0.1);
        }}
        
        .item-card.overdue {{ 
            border-left: 4px solid #ff4757; 
            background: rgba(255,71,87,0.15);
            animation: pulse-warning 2s infinite;
        }}
        
        .item-card.due {{ 
            border-left: 4px solid #ffa726; 
            background: rgba(255,167,38,0.15);
        }}
        
        @keyframes pulse-warning {{
            0%, 100% {{ 
                box-shadow: 0 4px 15px rgba(255,71,87,0.3); 
            }}
            50% {{ 
                box-shadow: 0 6px 25px rgba(255,71,87,0.6); 
            }}
        }}
        
        /* Progress Bars */
        .progress-bar {{ 
            width: 100%; 
            height: 8px; 
            background: rgba(255,255,255,0.2); 
            border-radius: 4px; 
            overflow: hidden; 
            margin: 0.5rem 0;
        }}
        
        .progress-fill {{ 
            height: 100%; 
            background: linear-gradient(90deg, #38ef7d, #11998e); 
            transition: width 0.3s ease; 
        }}
        
        /* Badges */
        .cmms-badge {{ 
            padding: 0.25rem 0.75rem; 
            border-radius: 12px; 
            font-size: 0.75rem; 
            font-weight: 600; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .badge-operational {{ 
            background: rgba(56,239,125,0.2); 
            color: #38ef7d; 
            border: 1px solid rgba(56,239,125,0.3);
        }}
        
        .badge-maintenance {{ 
            background: rgba(251,191,36,0.2); 
            color: #fbbf24; 
            border: 1px solid rgba(251,191,36,0.3);
        }}
        
        .badge-down {{ 
            background: rgba(255,71,87,0.2); 
            color: #ff4757; 
            border: 1px solid rgba(255,71,87,0.3);
        }}
        
        /* Mobile Responsiveness */
        @media (max-width: 768px) {{
            .cmms-header {{
                padding: 1.5rem;
            }}
            
            .cmms-header h1 {{
                font-size: 2rem;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
                gap: 1rem;
            }}
            
            .filter-bar {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .filter-bar > * {{
                width: 100%;
            }}
            
            .cmms-card {{
                padding: 1rem;
            }}
            
            .stat-card {{
                padding: 1rem;
            }}
        }}
        
        /* Loading States */
        .loading {{
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: shimmer 1.5s infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
    """

def get_unified_javascript() -> str:
    """
    Get unified JavaScript functionality for all CMMS modules
    """
    return f"""
        {get_navigation_javascript()}
        
        // Unified CMMS JavaScript Functions
        
        // Global notification system
        function showNotification(message, type = 'info') {{
            const notification = document.createElement('div');
            notification.className = `cmms-notification cmms-notification-${{type}}`;
            notification.innerHTML = `
                <span>${{message}}</span>
                <button onclick="this.parentElement.remove()" style="margin-left: 1rem; background: none; border: none; color: inherit; cursor: pointer;">×</button>
            `;
            notification.style.cssText = `
                position: fixed; top: 2rem; right: 2rem; z-index: 10000;
                background: rgba(0,0,0,0.9); color: white; padding: 1rem 1.5rem;
                border-radius: 8px; backdrop-filter: blur(10px);
                border-left: 4px solid ${{type === 'success' ? '#38ef7d' : type === 'warning' ? '#fbbf24' : type === 'error' ? '#ff4757' : '#74b9ff'}};
                animation: slideIn 0.3s ease;
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                if (notification.parentElement) {{
                    notification.remove();
                }}
            }}, 5000);
        }}
        
        // Enhanced modal system
        function showModal(title, content, actions = []) {{
            const modal = document.createElement('div');
            modal.className = 'cmms-modal';
            modal.innerHTML = `
                <div class="cmms-modal-backdrop" onclick="closeModal()">
                    <div class="cmms-modal-content" onclick="event.stopPropagation()">
                        <div class="cmms-modal-header">
                            <h3>${{title}}</h3>
                            <button onclick="closeModal()" class="cmms-modal-close">×</button>
                        </div>
                        <div class="cmms-modal-body">${{content}}</div>
                        <div class="cmms-modal-actions">
                            ${{actions.map(action => `<button class="cmms-btn ${{action.class || ''}}" onclick="${{action.onclick}}">${{action.text}}</button>`).join('')}}
                        </div>
                    </div>
                </div>
            `;
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 10001;
                display: flex; align-items: center; justify-content: center;
            `;
            document.body.appendChild(modal);
            
            // Add modal styles
            const style = document.createElement('style');
            style.textContent = `
                .cmms-modal-backdrop {{
                    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.7); backdrop-filter: blur(5px);
                }}
                .cmms-modal-content {{
                    background: rgba(255,255,255,0.15); backdrop-filter: blur(15px);
                    border-radius: 15px; border: 1px solid rgba(255,255,255,0.2);
                    max-width: 600px; width: 90%; max-height: 80%; overflow-y: auto;
                    color: white;
                }}
                .cmms-modal-header {{
                    padding: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);
                    display: flex; justify-content: space-between; align-items: center;
                }}
                .cmms-modal-header h3 {{ margin: 0; }}
                .cmms-modal-close {{
                    background: none; border: none; color: white; font-size: 1.5rem;
                    cursor: pointer; padding: 0.5rem;
                }}
                .cmms-modal-body {{ padding: 1.5rem; }}
                .cmms-modal-actions {{ 
                    padding: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1);
                    display: flex; justify-content: flex-end; gap: 1rem;
                }}
            `;
            document.head.appendChild(style);
            
            window.currentModal = modal;
        }}
        
        function closeModal() {{
            if (window.currentModal) {{
                document.body.removeChild(window.currentModal);
                window.currentModal = null;
            }}
        }}
        
        // Loading states
        function showLoading(element) {{
            element.classList.add('loading');
            element.style.pointerEvents = 'none';
        }}
        
        function hideLoading(element) {{
            element.classList.remove('loading');
            element.style.pointerEvents = 'auto';
        }}
        
        // Enhanced search and filter
        function setupUnifiedFiltering(containerId, options = {{}}) {{
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const items = container.querySelectorAll(options.itemSelector || '.item-card');
            
            function filterItems() {{
                const filters = options.filters || {{}};
                
                items.forEach(item => {{
                    let showItem = true;
                    
                    Object.keys(filters).forEach(filterKey => {{
                        const filterValue = document.getElementById(filters[filterKey])?.value?.toLowerCase();
                        const itemValue = item.dataset[filterKey]?.toLowerCase();
                        
                        if (filterValue && itemValue && !itemValue.includes(filterValue)) {{
                            showItem = false;
                        }}
                    }});
                    
                    // Text search
                    const searchInput = document.getElementById(options.searchId);
                    if (searchInput && searchInput.value) {{
                        const searchTerm = searchInput.value.toLowerCase();
                        const itemText = item.textContent.toLowerCase();
                        if (!itemText.includes(searchTerm)) {{
                            showItem = false;
                        }}
                    }}
                    
                    item.style.display = showItem ? 'block' : 'none';
                }});
                
                // Update count if counter exists
                const counter = document.getElementById(options.counterId);
                if (counter) {{
                    const visibleCount = Array.from(items).filter(item => item.style.display !== 'none').length;
                    counter.textContent = `Showing ${{visibleCount}} of ${{items.length}} items`;
                }}
            }}
            
            // Bind filter events
            Object.values(options.filters || {{}}).forEach(filterId => {{
                const element = document.getElementById(filterId);
                if (element) {{
                    element.addEventListener('change', filterItems);
                }}
            }});
            
            if (options.searchId) {{
                const searchInput = document.getElementById(options.searchId);
                if (searchInput) {{
                    searchInput.addEventListener('input', filterItems);
                }}
            }}
            
            // Initial filter
            filterItems();
        }}
        
        // Unified form handling
        function handleFormSubmit(formId, endpoint, options = {{}}) {{
            const form = document.getElementById(formId);
            if (!form) return;
            
            form.addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const submitBtn = form.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                
                try {{
                    showLoading(submitBtn);
                    submitBtn.textContent = 'Processing...';
                    
                    const formData = new FormData(form);
                    const data = Object.fromEntries(formData);
                    
                    const response = await fetch(endpoint, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    
                    if (response.ok) {{
                        showNotification(options.successMessage || 'Operation completed successfully!', 'success');
                        if (options.onSuccess) options.onSuccess(result);
                        if (options.redirect) window.location.href = options.redirect;
                        if (options.reload) location.reload();
                    }} else {{
                        throw new Error(result.message || 'Operation failed');
                    }}
                }} catch (error) {{
                    showNotification(error.message || 'An error occurred', 'error');
                    if (options.onError) options.onError(error);
                }} finally {{
                    hideLoading(submitBtn);
                    submitBtn.textContent = originalText;
                }}
            }});
        }}
        
        // Add animation styles
        const animationStyles = document.createElement('style');
        animationStyles.textContent = `
            @keyframes slideIn {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .cmms-card, .item-card, .stat-card {{
                animation: fadeIn 0.5s ease;
            }}
        `;
        document.head.appendChild(animationStyles);
    """

def create_unified_page(title: str, content: str, current_page: str = "", breadcrumbs = None) -> str:
    """
    Create a unified page layout with consistent styling and navigation
    """
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - ChatterFix CMMS</title>
        <style>
            {get_unified_styles()}
        </style>
    </head>
    <body>
        {get_navigation_html(current_page, breadcrumbs)}
        
        <div class="cmms-header">
            <h1>{title}</h1>
        </div>
        
        <div class="container">
            {content}
        </div>
        
        <script>
            {get_unified_javascript()}
        </script>
    </body>
    </html>
    """