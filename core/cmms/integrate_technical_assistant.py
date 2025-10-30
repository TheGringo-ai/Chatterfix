#!/usr/bin/env python3
"""
ChatterFix CMMS - Technical Assistant Integration Script
Automatically integrates technical AI assistant across all dashboard templates
"""

import os
import re
import glob
from pathlib import Path

def find_html_templates():
    """Find all HTML template files in the ChatterFix app"""
    template_dir = Path("templates")
    html_files = []
    
    if template_dir.exists():
        # Find all HTML files
        html_files.extend(glob.glob(str(template_dir / "*.html")))
        
        # Look for subdirectories
        for subdir in template_dir.iterdir():
            if subdir.is_dir():
                html_files.extend(glob.glob(str(subdir / "*.html")))
    
    # Filter out the assistant files themselves
    filtered_files = [
        f for f in html_files 
        if not any(exclude in f for exclude in [
            'technical_ai_widget.html',
            'chatterfix_sales_chat.html', 
            'universal_ai_assistant.html'
        ])
    ]
    
    return filtered_files

def read_technical_assistant_widget():
    """Read the technical assistant widget code"""
    widget_path = Path("templates/technical_ai_widget.html")
    
    if not widget_path.exists():
        return None, None, None
    
    content = widget_path.read_text()
    
    # Extract CSS, HTML widget, and JavaScript
    css_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    css_content = css_match.group(1) if css_match else ""
    
    # Extract the widget HTML (everything inside the body)
    widget_match = re.search(r'<!-- Technical AI Widget -->(.*?)<!-- Hidden file inputs -->', content, re.DOTALL)
    widget_html = widget_match.group(1) if widget_match else ""
    
    # Extract JavaScript
    js_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
    js_content = js_match.group(1) if js_match else ""
    
    return css_content, widget_html, js_content

def integrate_into_template(file_path, css_content, widget_html, js_content):
    """Integrate technical assistant into a single template file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already integrated
        if 'technical-ai-widget' in content:
            print(f"  ✓ Already integrated: {file_path}")
            return True
        
        # Add CSS to head section
        if css_content and '<head>' in content:
            css_insertion = f"""    <style>
        /* Technical AI Assistant Styles */
{css_content}
    </style>"""
            
            if '</head>' in content:
                content = content.replace('</head>', f"{css_insertion}\n</head>")
            else:
                # Insert after <head> tag
                content = content.replace('<head>', f"<head>\n{css_insertion}")
        
        # Add widget HTML before closing body tag
        if widget_html and '</body>' in content:
            widget_insertion = f"""
    <!-- ChatterFix Technical AI Assistant -->
{widget_html}
    <!-- Hidden file inputs -->
    <input type="file" id="photoInput" accept="image/*" capture="environment" style="display: none;">
    <input type="file" id="documentInput" accept=".pdf,.doc,.docx,.txt" style="display: none;">
    <input type="file" id="videoInput" accept="video/*" capture="environment" style="display: none;">
"""
            content = content.replace('</body>', f"{widget_insertion}\n</body>")
        
        # Add JavaScript before closing body tag
        if js_content and '</body>' in content:
            js_insertion = f"""
    <script>
{js_content}
    </script>"""
            content = content.replace('</body>', f"{js_insertion}\n</body>")
        
        # Write the updated content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ Integrated: {file_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error integrating {file_path}: {str(e)}")
        return False

def add_role_detection_script():
    """Add role detection script to main app.py"""
    app_path = Path("app.py")
    
    if not app_path.exists():
        print("  ❌ app.py not found")
        return False
    
    try:
        content = app_path.read_text()
        
        # Skip if already added
        if 'technical-assistant-integration' in content:
            print("  ✓ Role detection already integrated in app.py")
            return True
        
        # Add role detection endpoint
        role_detection_code = '''
# Technical Assistant Integration
@app.route('/api/technical-assistant/user-role')
def get_user_role():
    """Detect user role for technical assistant"""
    # Try to get role from session, headers, or URL
    user_role = (
        session.get('user_role') or 
        request.headers.get('X-User-Role') or 
        request.args.get('role') or 
        'technician'  # Default role
    )
    
    return jsonify({
        'role': user_role,
        'capabilities': {
            'technician': ['photo_analysis', 'video_diagnostics', 'document_reading'],
            'maintenance_worker': ['photo_documentation', 'checklist_assistance'],
            'field_engineer': ['technical_drawing_analysis', 'performance_data_analysis'],
            'supervisor': ['team_coordination', 'progress_monitoring'],
            'inspector': ['defect_detection', 'compliance_checking'],
            'safety_officer': ['hazard_detection', 'safety_assessment']
        }.get(user_role, ['photo_analysis', 'document_reading'])
    })

# Add technical assistant context to all templates
@app.context_processor
def inject_technical_assistant_context():
    """Add technical assistant context to all templates"""
    return {
        'technical_assistant_enabled': True,
        'technical_assistant_service_url': 'http://localhost:8012',
        'user_role': session.get('user_role', 'technician')
    }
'''
        
        # Find a good place to insert (after imports, before routes)
        if '# Routes' in content:
            content = content.replace('# Routes', f'# Technical Assistant Integration{role_detection_code}\n\n# Routes')
        elif '@app.route' in content:
            # Insert before first route
            first_route = content.find('@app.route')
            content = content[:first_route] + f'# Technical Assistant Integration{role_detection_code}\n\n' + content[first_route:]
        else:
            # Append to end
            content += f'\n{role_detection_code}'
        
        app_path.write_text(content)
        print("  ✅ Role detection integrated in app.py")
        return True
        
    except Exception as e:
        print(f"  ❌ Error integrating role detection: {str(e)}")
        return False

def main():
    """Main integration function"""
    print("🔧 ChatterFix Technical AI Assistant - Dashboard Integration")
    print("=" * 60)
    
    # Read the technical assistant widget
    print("📖 Reading technical assistant widget...")
    css_content, widget_html, js_content = read_technical_assistant_widget()
    
    if not css_content or not widget_html or not js_content:
        print("❌ Could not read technical assistant widget files")
        return False
    
    print("✅ Technical assistant widget loaded successfully")
    
    # Find all HTML templates
    print("\n🔍 Finding HTML template files...")
    html_files = find_html_templates()
    
    if not html_files:
        print("❌ No HTML template files found")
        return False
    
    print(f"📁 Found {len(html_files)} template files:")
    for file in html_files:
        print(f"  - {file}")
    
    # Integrate into each template
    print(f"\n🚀 Integrating technical assistant into {len(html_files)} templates...")
    success_count = 0
    
    for file_path in html_files:
        if integrate_into_template(file_path, css_content, widget_html, js_content):
            success_count += 1
    
    # Add role detection to main app
    print(f"\n⚙️ Adding role detection to main app...")
    add_role_detection_script()
    
    # Summary
    print(f"\n📊 Integration Summary:")
    print(f"  ✅ Successfully integrated: {success_count}/{len(html_files)} templates")
    print(f"  🔧 Technical assistant service: http://localhost:8012")
    print(f"  📱 Widget appears on all dashboard pages")
    print(f"  🎯 Role-based AI personalities enabled")
    
    print(f"\n🎉 Technical AI Assistant Integration Complete!")
    print(f"📸 Features available on all dashboards:")
    print(f"  - Photo analysis and equipment inspection")
    print(f"  - Voice commands and speech-to-text")
    print(f"  - Document analysis and procedure lookup")
    print(f"  - Video processing and diagnostics")
    print(f"  - Role-based AI expertise (6 specialized roles)")
    print(f"  - Safety alerts and recommendations")
    
    return True

if __name__ == "__main__":
    main()