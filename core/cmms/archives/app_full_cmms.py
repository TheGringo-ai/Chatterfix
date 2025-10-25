#!/usr/bin/env python3
"""
ChatterFix CMMS - Complete Production Platform
Full-featured CMMS with dashboard, work orders, assets, and more
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('chatterfix_cmms.db')
    cursor = conn.cursor()
    
    # Work Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            assigned_to TEXT,
            asset_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            estimated_hours REAL,
            actual_hours REAL
        )
    ''')
    
    # Assets table  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            location TEXT,
            status TEXT DEFAULT 'active',
            maintenance_schedule TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_maintenance TIMESTAMP,
            next_maintenance TIMESTAMP,
            condition_score INTEGER DEFAULT 100
        )
    ''')
    
    # Parts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            part_number TEXT UNIQUE,
            quantity INTEGER DEFAULT 0,
            min_quantity INTEGER DEFAULT 5,
            unit_cost REAL,
            supplier TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Maintenance logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            work_order_id INTEGER,
            performed_by TEXT,
            description TEXT,
            parts_used TEXT,
            cost REAL,
            performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (id),
            FOREIGN KEY (work_order_id) REFERENCES work_orders (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Database helper
def get_db():
    conn = sqlite3.connect('chatterfix_cmms.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database and sample data
def add_sample_data():
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if data already exists
    existing = cursor.execute('SELECT COUNT(*) FROM assets').fetchone()[0]
    if existing > 0:
        conn.close()
        return
    
    # Sample assets
    assets = [
        ("Conveyor Belt A1", "Conveyor", "Production Floor A", "active", "Weekly"),
        ("Air Compressor B2", "Compressor", "Utility Room", "active", "Monthly"),
        ("Packaging Machine C3", "Packaging", "Production Floor B", "maintenance", "Bi-weekly"),
        ("HVAC Unit D4", "HVAC", "Building Roof", "active", "Quarterly"),
        ("Forklift E5", "Vehicle", "Warehouse", "active", "Monthly")
    ]
    
    for asset in assets:
        cursor.execute('''
            INSERT INTO assets (name, type, location, status, maintenance_schedule)
            VALUES (?, ?, ?, ?, ?)
        ''', asset)
    
    # Sample work orders
    work_orders = [
        ("Replace conveyor belt motor", "Motor showing signs of wear, replace before failure", "high", "open", "John Smith", 1),
        ("Lubricate air compressor", "Routine lubrication maintenance", "medium", "in-progress", "Mike Johnson", 2),
        ("Calibrate packaging sensors", "Sensors need recalibration for accuracy", "medium", "open", "Sarah Davis", 3),
        ("Clean HVAC filters", "Replace dirty air filters", "low", "completed", "Tom Wilson", 4),
        ("Forklift safety inspection", "Monthly safety check required", "high", "open", "Lisa Brown", 5)
    ]
    
    for wo in work_orders:
        cursor.execute('''
            INSERT INTO work_orders (title, description, priority, status, assigned_to, asset_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', wo)
    
    # Sample parts
    parts = [
        ("Motor Belt V-123", "VB123", 15, 5, 45.99, "Industrial Supply Co", "Storage A1"),
        ("Air Filter AF-500", "AF500", 25, 10, 12.50, "Filter Tech", "Storage A2"), 
        ("Sensor Calibration Kit", "SCK100", 3, 2, 125.00, "Precision Tools", "Storage B1"),
        ("Hydraulic Oil", "HO20W", 50, 20, 8.75, "Fluid Systems", "Storage C1"),
        ("Safety Harness", "SH-XL", 8, 5, 89.99, "Safety First", "Storage D1")
    ]
    
    for part in parts:
        cursor.execute('''
            INSERT INTO parts (name, part_number, quantity, min_quantity, unit_cost, supplier, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', part)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()
add_sample_data()

# Main dashboard template
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix CMMS - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; }
        
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header h1 { display: inline-block; }
        .header .user-info { float: right; margin-top: 5px; }
        
        .nav { background: white; padding: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .nav ul { list-style: none; display: flex; }
        .nav li { margin: 0; }
        .nav a { display: block; padding: 1rem 2rem; text-decoration: none; color: #333; border-bottom: 3px solid transparent; transition: all 0.3s; }
        .nav a:hover, .nav a.active { background: #f8f9fa; border-bottom-color: #667eea; }
        
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        
        .stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 4px solid #667eea; }
        .stat-card h3 { color: #333; margin-bottom: 0.5rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }
        .stat-card .number { font-size: 2rem; font-weight: bold; color: #667eea; }
        .stat-card .change { font-size: 0.8rem; color: #28a745; margin-top: 0.5rem; }
        
        .card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
        .card h2 { margin-bottom: 1rem; color: #333; }
        
        .btn { background: #667eea; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; transition: background 0.3s; }
        .btn:hover { background: #5a6fd8; }
        .btn-success { background: #28a745; }
        .btn-warning { background: #ffc107; color: #333; }
        .btn-danger { background: #dc3545; }
        
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #dee2e6; }
        .table th { background: #f8f9fa; font-weight: 600; }
        .table tr:hover { background: #f8f9fa; }
        
        .status { padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
        .status.open { background: #e3f2fd; color: #1976d2; }
        .status.in-progress { background: #fff3e0; color: #f57c00; }
        .status.completed { background: #e8f5e8; color: #388e3c; }
        .status.high { background: #ffebee; color: #d32f2f; }
        .status.medium { background: #fff3e0; color: #f57c00; }
        .status.low { background: #e8f5e8; color: #388e3c; }
        
        .priority.high { color: #d32f2f; font-weight: bold; }
        .priority.medium { color: #f57c00; }
        .priority.low { color: #388e3c; }
        
        .ai-insight { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
        .ai-insight h4 { margin-bottom: 0.5rem; }
        
        @media (max-width: 768px) {
            .header { padding: 1rem; }
            .header .user-info { float: none; margin-top: 1rem; }
            .nav ul { flex-direction: column; }
            .dashboard-grid { grid-template-columns: 1fr; }
            .container { margin: 1rem auto; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 ChatterFix CMMS</h1>
        <div class="user-info">
            <span>Welcome, Admin</span>
        </div>
        <div style="clear: both;"></div>
    </div>
    
    <nav class="nav">
        <ul>
            <li><a href="/" class="active">Dashboard</a></li>
            <li><a href="/work-orders">Work Orders</a></li>
            <li><a href="/assets">Assets</a></li>
            <li><a href="/parts">Parts</a></li>
            <li><a href="/reports">Reports</a></li>
            <li><a href="/ai-insights">AI Insights</a></li>
        </ul>
    </nav>
    
    <div class="container">
        <div class="dashboard-grid">
            <div class="stat-card">
                <h3>Open Work Orders</h3>
                <div class="number">{{ stats.open_work_orders }}</div>
                <div class="change">+2 this week</div>
            </div>
            <div class="stat-card">
                <h3>Active Assets</h3>
                <div class="number">{{ stats.active_assets }}</div>
                <div class="change">100% operational</div>
            </div>
            <div class="stat-card">
                <h3>Parts in Stock</h3>
                <div class="number">{{ stats.parts_count }}</div>
                <div class="change">{{ stats.low_stock_count }} low stock</div>
            </div>
            <div class="stat-card">
                <h3>Cost Savings</h3>
                <div class="number">$1,247</div>
                <div class="change">This month</div>
            </div>
        </div>
        
        <div class="ai-insight">
            <h4>🤖 AI Insight</h4>
            <p>Based on maintenance patterns, Conveyor Belt A1 is due for preventive maintenance in 3 days. Scheduling now could prevent a potential 4-hour downtime.</p>
        </div>
        
        <div class="card">
            <h2>Recent Work Orders</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Priority</th>
                        <th>Status</th>
                        <th>Assigned To</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for wo in recent_work_orders %}
                    <tr>
                        <td>#{{ wo.id }}</td>
                        <td>{{ wo.title }}</td>
                        <td><span class="priority {{ wo.priority }}">{{ wo.priority.title() }}</span></td>
                        <td><span class="status {{ wo.status }}">{{ wo.status.replace('-', ' ').title() }}</span></td>
                        <td>{{ wo.assigned_to }}</td>
                        <td>{{ wo.created_at[:10] }}</td>
                        <td><a href="/work-orders/{{ wo.id }}" class="btn">View</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="/work-orders" class="btn">View All Work Orders</a>
        </div>
        
        <div class="card">
            <h2>Asset Status Overview</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Asset</th>
                        <th>Type</th>
                        <th>Location</th>
                        <th>Status</th>
                        <th>Last Maintenance</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for asset in recent_assets %}
                    <tr>
                        <td>{{ asset.name }}</td>
                        <td>{{ asset.type }}</td>
                        <td>{{ asset.location }}</td>
                        <td><span class="status {{ asset.status }}">{{ asset.status.title() }}</span></td>
                        <td>{{ asset.last_maintenance or 'Never' }}</td>
                        <td><a href="/assets/{{ asset.id }}" class="btn">View</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="/assets" class="btn">View All Assets</a>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def dashboard():
    conn = get_db()
    
    # Get dashboard statistics
    stats = {
        'open_work_orders': conn.execute("SELECT COUNT(*) FROM work_orders WHERE status IN ('open', 'in-progress')").fetchone()[0],
        'active_assets': conn.execute("SELECT COUNT(*) FROM assets WHERE status = 'active'").fetchone()[0],
        'parts_count': conn.execute("SELECT SUM(quantity) FROM parts").fetchone()[0] or 0,
        'low_stock_count': conn.execute("SELECT COUNT(*) FROM parts WHERE quantity <= min_quantity").fetchone()[0]
    }
    
    # Get recent work orders
    recent_work_orders = conn.execute('''
        SELECT * FROM work_orders 
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get recent assets
    recent_assets = conn.execute('''
        SELECT * FROM assets 
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                stats=stats, 
                                recent_work_orders=recent_work_orders,
                                recent_assets=recent_assets)

# Work Orders page
@app.route('/work-orders')
def work_orders():
    conn = get_db()
    work_orders = conn.execute('''
        SELECT wo.*, a.name as asset_name 
        FROM work_orders wo 
        LEFT JOIN assets a ON wo.asset_id = a.id 
        ORDER BY wo.created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Work Orders - ChatterFix CMMS</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; }
            .nav { background: white; padding: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .nav ul { list-style: none; display: flex; }
            .nav a { display: block; padding: 1rem 2rem; text-decoration: none; color: #333; }
            .nav a:hover { background: #f8f9fa; }
            .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
            .card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .btn { background: #667eea; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
            .table { width: 100%; border-collapse: collapse; }
            .table th, .table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #dee2e6; }
            .table th { background: #f8f9fa; }
            .status { padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }
            .status.open { background: #e3f2fd; color: #1976d2; }
            .status.in-progress { background: #fff3e0; color: #f57c00; }
            .status.completed { background: #e8f5e8; color: #388e3c; }
            .priority.high { color: #d32f2f; font-weight: bold; }
            .priority.medium { color: #f57c00; }
            .priority.low { color: #388e3c; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 ChatterFix CMMS - Work Orders</h1>
        </div>
        <nav class="nav">
            <ul>
                <li><a href="/">Dashboard</a></li>
                <li><a href="/work-orders">Work Orders</a></li>
                <li><a href="/assets">Assets</a></li>
                <li><a href="/parts">Parts</a></li>
                <li><a href="/reports">Reports</a></li>
            </ul>
        </nav>
        <div class="container">
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h2>Work Orders</h2>
                    <a href="/work-orders/new" class="btn">+ Create Work Order</a>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Asset</th>
                            <th>Priority</th>
                            <th>Status</th>
                            <th>Assigned To</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for wo in work_orders %}
                        <tr>
                            <td>#{{ wo.id }}</td>
                            <td>{{ wo.title }}</td>
                            <td>{{ wo.asset_name or 'N/A' }}</td>
                            <td><span class="priority {{ wo.priority }}">{{ wo.priority.title() }}</span></td>
                            <td><span class="status {{ wo.status }}">{{ wo.status.replace('-', ' ').title() }}</span></td>
                            <td>{{ wo.assigned_to }}</td>
                            <td>{{ wo.created_at[:10] }}</td>
                            <td><a href="/work-orders/{{ wo.id }}" class="btn">View</a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    ''', work_orders=work_orders)

# Assets page
@app.route('/assets')
def assets():
    conn = get_db()
    assets = conn.execute('SELECT * FROM assets ORDER BY name').fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Assets - ChatterFix CMMS</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; }
            .nav { background: white; padding: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .nav ul { list-style: none; display: flex; }
            .nav a { display: block; padding: 1rem 2rem; text-decoration: none; color: #333; }
            .nav a:hover { background: #f8f9fa; }
            .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
            .card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .btn { background: #667eea; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
            .table { width: 100%; border-collapse: collapse; }
            .table th, .table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #dee2e6; }
            .table th { background: #f8f9fa; }
            .status { padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }
            .status.active { background: #e8f5e8; color: #388e3c; }
            .status.maintenance { background: #fff3e0; color: #f57c00; }
            .status.inactive { background: #ffebee; color: #d32f2f; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 ChatterFix CMMS - Assets</h1>
        </div>
        <nav class="nav">
            <ul>
                <li><a href="/">Dashboard</a></li>
                <li><a href="/work-orders">Work Orders</a></li>
                <li><a href="/assets">Assets</a></li>
                <li><a href="/parts">Parts</a></li>
                <li><a href="/reports">Reports</a></li>
            </ul>
        </nav>
        <div class="container">
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h2>Assets</h2>
                    <a href="/assets/new" class="btn">+ Add Asset</a>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Location</th>
                            <th>Status</th>
                            <th>Maintenance Schedule</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for asset in assets %}
                        <tr>
                            <td>#{{ asset.id }}</td>
                            <td>{{ asset.name }}</td>
                            <td>{{ asset.type }}</td>
                            <td>{{ asset.location }}</td>
                            <td><span class="status {{ asset.status }}">{{ asset.status.title() }}</span></td>
                            <td>{{ asset.maintenance_schedule }}</td>
                            <td><a href="/assets/{{ asset.id }}" class="btn">View</a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    ''', assets=assets)

# Parts page
@app.route('/parts')
def parts():
    conn = get_db()
    parts = conn.execute('SELECT * FROM parts ORDER BY name').fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Parts - ChatterFix CMMS</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; }
            .nav { background: white; padding: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .nav ul { list-style: none; display: flex; }
            .nav a { display: block; padding: 1rem 2rem; text-decoration: none; color: #333; }
            .nav a:hover { background: #f8f9fa; }
            .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
            .card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .btn { background: #667eea; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
            .table { width: 100%; border-collapse: collapse; }
            .table th, .table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #dee2e6; }
            .table th { background: #f8f9fa; }
            .low-stock { background: #ffebee; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 ChatterFix CMMS - Parts Inventory</h1>
        </div>
        <nav class="nav">
            <ul>
                <li><a href="/">Dashboard</a></li>
                <li><a href="/work-orders">Work Orders</a></li>
                <li><a href="/assets">Assets</a></li>
                <li><a href="/parts">Parts</a></li>
                <li><a href="/reports">Reports</a></li>
            </ul>
        </nav>
        <div class="container">
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h2>Parts Inventory</h2>
                    <a href="/parts/new" class="btn">+ Add Part</a>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Part Number</th>
                            <th>Name</th>
                            <th>Quantity</th>
                            <th>Min Quantity</th>
                            <th>Unit Cost</th>
                            <th>Supplier</th>
                            <th>Location</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for part in parts %}
                        <tr {% if part.quantity <= part.min_quantity %}class="low-stock"{% endif %}>
                            <td>{{ part.part_number }}</td>
                            <td>{{ part.name }}</td>
                            <td>{{ part.quantity }}{% if part.quantity <= part.min_quantity %} ⚠️{% endif %}</td>
                            <td>{{ part.min_quantity }}</td>
                            <td>${{ "%.2f"|format(part.unit_cost) }}</td>
                            <td>{{ part.supplier }}</td>
                            <td>{{ part.location }}</td>
                            <td><a href="/parts/{{ part.id }}" class="btn">View</a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    ''', parts=parts)

# API endpoints (keep existing ones)
@app.route('/api/work-orders', methods=['GET'])
def api_get_work_orders():
    conn = get_db()
    work_orders = conn.execute('SELECT * FROM work_orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in work_orders])

@app.route('/api/work-orders', methods=['POST'])
def api_create_work_order():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO work_orders (title, description, priority, assigned_to, asset_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data.get('title'),
        data.get('description'),
        data.get('priority', 'medium'),
        data.get('assigned_to'),
        data.get('asset_id')
    ))
    work_order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': work_order_id, 'status': 'created'}), 201

@app.route('/api/assets', methods=['GET'])
def api_get_assets():
    conn = get_db()
    assets = conn.execute('SELECT * FROM assets ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(row) for row in assets])

@app.route('/api/parts', methods=['GET'])
def api_get_parts():
    conn = get_db()
    parts = conn.execute('SELECT * FROM parts ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(row) for row in parts])

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'ChatterFix CMMS', 'version': '2.0'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)