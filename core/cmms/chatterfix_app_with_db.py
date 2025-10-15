#!/usr/bin/env python3
"""
ChatterFix CMMS - Production App with PostgreSQL Integration
Enhanced maintenance management system with real database backend
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
from datetime import datetime
import logging

# Import our database module
from chatterfix_database import db

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# AI Service Configuration
AI_SERVICE_URL = "http://localhost:9000"
AI_TIMEOUT = 90

@app.route('/')
def dashboard():
    """Main dashboard with real data"""
    try:
        work_orders = db.get_work_orders()
        assets = db.get_assets() 
        low_stock = db.get_low_stock_parts()
        
        # Dashboard stats
        stats = {
            'total_work_orders': len(work_orders),
            'open_work_orders': len([wo for wo in work_orders if wo['status'] == 'open']),
            'total_assets': len(assets),
            'low_stock_parts': len(low_stock)
        }
        
        return render_template('dashboard.html', 
                             work_orders=work_orders[:5],  # Show recent 5
                             assets=assets[:5],
                             low_stock=low_stock,
                             stats=stats)
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', 
                             work_orders=[], assets=[], low_stock=[], 
                             stats={'total_work_orders': 0, 'open_work_orders': 0, 'total_assets': 0, 'low_stock_parts': 0})

@app.route('/work-orders')
def work_orders():
    """Work orders page"""
    orders = db.get_work_orders()
    return render_template('work_orders.html', work_orders=orders)

@app.route('/work-orders/create', methods=['GET', 'POST'])
def create_work_order():
    """Create new work order"""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            asset_tag = request.form.get('asset_tag')
            priority = request.form.get('priority', 'medium')
            assigned_to = request.form.get('assigned_to')
            
            work_order = db.create_work_order(title, description, asset_tag, priority, assigned_to)
            
            if work_order:
                return redirect(url_for('work_orders'))
            else:
                return jsonify({'success': False, 'error': 'Failed to create work order'}), 500
                
        except Exception as e:
            logging.error(f"Work order creation error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # GET request - show form
    assets = db.get_assets()
    return render_template('create_work_order.html', assets=assets)

@app.route('/assets')
def assets():
    """Assets management page"""
    assets_list = db.get_assets()
    return render_template('assets.html', assets=assets_list)

@app.route('/parts')
def parts():
    """Parts inventory page"""
    parts_list = db.get_parts_inventory()
    low_stock = db.get_low_stock_parts()
    return render_template('parts.html', parts=parts_list, low_stock=low_stock)

@app.route('/api/work-orders/<int:work_order_id>/status', methods=['POST'])
def update_work_order_status(work_order_id):
    """Update work order status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if db.update_work_order_status(work_order_id, status):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Work order not found'}), 404
            
    except Exception as e:
        logging.error(f"Status update error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI Chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        user_role = data.get('user_role', 'technician')
        context = data.get('context', 'ChatterFix CMMS')
        
        # Add CMMS context to the message
        work_orders = db.get_work_orders()
        assets = db.get_assets()
        low_stock = db.get_low_stock_parts()
        
        enhanced_context = f"""
        CMMS Context:
        - Active Work Orders: {len([wo for wo in work_orders if wo['status'] == 'open'])}
        - Total Assets: {len(assets)}
        - Low Stock Parts: {len(low_stock)}
        
        User Role: {user_role}
        Original Context: {context}
        """
        
        # Call AI service
        ai_response = requests.post(
            f"{AI_SERVICE_URL}/api/chat",
            json={
                'message': message,
                'user_role': user_role,
                'context': enhanced_context,
                'provider': 'ollama',
                'model': 'llama3.2:1b'
            },
            timeout=AI_TIMEOUT
        )
        
        if ai_response.status_code == 200:
            return ai_response.json()
        else:
            return {
                'success': True,
                'response': f"Hi! I'm your ChatterFix AI assistant. I can help with work orders, asset management, and parts inventory. What can I help you with today?",
                'provider': 'fallback',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return {
            'success': True,
            'response': "I'm your ChatterFix AI assistant. I can help with maintenance tasks, work orders, and parts management. How can I assist you?",
            'provider': 'fallback',
            'timestamp': datetime.now().isoformat()
        }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting ChatterFix CMMS on port {port}...")
    print(f"📊 Database: {'PostgreSQL' if os.getenv('USE_POSTGRESQL') == 'true' else 'File Storage (Fallback)'}")
    app.run(host='0.0.0.0', port=port, debug=False)
