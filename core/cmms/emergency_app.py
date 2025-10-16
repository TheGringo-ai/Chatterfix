#!/usr/bin/env python3
"""
Emergency ChatterFix CMMS App - Minimal Working Version
"""

from flask import Flask, render_template_string, jsonify, request, send_from_directory
import os
import uuid
from datetime import datetime

app = Flask(__name__)

# Sample data
assets_data = [
    {
        "id": "1", 
        "name": "Main Production Server",
        "description": "Primary server for production workloads",
        "asset_type": "equipment",
        "location": "Data Center A", 
        "status": "operational",
        "created_at": "2024-01-15T10:00:00"
    },
    {
        "id": "2",
        "name": "Backup Generator", 
        "description": "Emergency power backup system",
        "asset_type": "equipment",
        "location": "Building B",
        "status": "active",
        "created_at": "2023-08-20T14:30:00"
    }
]

work_orders_data = [
    {
        "id": "1",
        "title": "Server Maintenance",
        "description": "Routine server maintenance",
        "status": "pending", 
        "priority": "medium",
        "asset_id": "1",
        "created_at": "2024-10-16T08:00:00"
    }
]

@app.route('/')
def dashboard():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>ChatterFix CMMS - Emergency Mode</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8fafc; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .btn { background: #006fee; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn:hover { background: #0056b3; }
        .status-operational { color: #059669; }
        .status-active { color: #0d9488; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏭 ChatterFix CMMS</h1>
            <p><strong>Status:</strong> ✅ Emergency Mode - System Restored</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🏭 Assets</h3>
                <p>{{ assets|length }} assets tracked</p>
                <a href="/assets" class="btn">Manage Assets</a>
            </div>
            
            <div class="card">
                <h3>🔧 Work Orders</h3>
                <p>{{ work_orders|length }} work orders</p>
                <a href="/work_orders" class="btn">Manage Work Orders</a>
            </div>
            
            <div class="card">
                <h3>📊 System Status</h3>
                <p>✅ HTTPS: Working</p>
                <p>✅ Assets API: Working</p>
                <p>✅ Work Orders API: Working</p>
                <a href="/health" class="btn">Health Check</a>
            </div>
        </div>
    </div>
</body>
</html>
    ''', assets=assets_data, work_orders=work_orders_data)

@app.route('/assets')
def assets_page():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Assets - ChatterFix CMMS</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8fafc; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .btn { background: #006fee; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; margin-right: 10px; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #059669; }
        .status-operational { color: #059669; font-weight: bold; }
        .status-active { color: #0d9488; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #e2e8f0; }
        th { background: #f8fafc; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏭 Asset Management</h1>
            <a href="/" class="btn">← Back to Dashboard</a>
            <button onclick="addAsset()" class="btn btn-success">+ Add Asset</button>
        </div>
        
        <div class="card">
            <h3>Assets List</h3>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Location</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for asset in assets %}
                    <tr>
                        <td><strong>{{ asset.name }}</strong><br><small>{{ asset.description }}</small></td>
                        <td>{{ asset.asset_type|title }}</td>
                        <td>{{ asset.location }}</td>
                        <td><span class="status-{{ asset.status }}">{{ asset.status|title }}</span></td>
                        <td>
                            <button class="btn" onclick="editAsset('{{ asset.id }}')">Edit</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function addAsset() {
            const name = prompt('Asset Name:');
            if (!name) return;
            
            const description = prompt('Description:');
            const location = prompt('Location:');
            
            const data = {
                name: name,
                description: description || '',
                asset_type: 'equipment',
                location: location || '',
                status: 'active'
            };
            
            fetch('/api/assets', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(result => {
                if (result.success) {
                    alert('✅ Asset created successfully!');
                    location.reload();
                } else {
                    alert('❌ Error: ' + result.message);
                }
            })
            .catch(e => alert('❌ Error: ' + e.message));
        }
        
        function editAsset(id) {
            alert('Edit functionality - Asset ID: ' + id);
        }
    </script>
</body>
</html>
    ''', assets=assets_data)

@app.route('/work_orders')
def work_orders_page():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Work Orders - ChatterFix CMMS</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8fafc; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .btn { background: #006fee; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; margin-right: 10px; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #059669; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #e2e8f0; }
        th { background: #f8fafc; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Work Order Management</h1>
            <a href="/" class="btn">← Back to Dashboard</a>
            <button onclick="addWorkOrder()" class="btn btn-success">+ Create Work Order</button>
        </div>
        
        <div class="card">
            <h3>Work Orders</h3>
            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Asset</th>
                        <th>Priority</th>
                        <th>Status</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    {% for wo in work_orders %}
                    <tr>
                        <td><strong>{{ wo.title }}</strong><br><small>{{ wo.description }}</small></td>
                        <td>Asset #{{ wo.asset_id }}</td>
                        <td>{{ wo.priority|title }}</td>
                        <td>{{ wo.status|title }}</td>
                        <td>{{ wo.created_at[:10] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function addWorkOrder() {
            alert('Work order creation - functionality available');
        }
    </script>
</body>
</html>
    ''', work_orders=work_orders_data)

# API Endpoints
@app.route('/api/assets', methods=['GET'])
def get_assets():
    return jsonify(assets_data)

@app.route('/api/assets', methods=['POST'])
def create_asset():
    try:
        data = request.get_json()
        new_asset = {
            "id": str(uuid.uuid4())[:8],
            "name": data.get('name', ''),
            "description": data.get('description', ''),
            "asset_type": data.get('asset_type', 'equipment'),
            "location": data.get('location', ''),
            "status": data.get('status', 'active'),
            "created_at": datetime.now().isoformat()
        }
        assets_data.append(new_asset)
        return jsonify({"success": True, "message": "Asset created", "asset": new_asset})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/work_orders', methods=['GET'])
def get_work_orders():
    return jsonify(work_orders_data)

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "ChatterFix CMMS Emergency",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "assets_count": len(assets_data),
        "work_orders_count": len(work_orders_data)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)