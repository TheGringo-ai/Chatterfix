#!/usr/bin/env python3
"""
Work Order Enhancement Patch for ChatterFix CMMS
Adds clickable work order cards and update functionality
"""

# Additional endpoints to add to the working app.py

WORK_ORDER_ENDPOINTS = """
@app.get("/work-orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    \"\"\"Get individual work order details with clickable interface\"\"\"
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(\"\"\"
            SELECT id, title, description, status, priority, assigned_to, created_date, due_date
            FROM work_orders WHERE id = ?
        \"\"\", (work_order_id,))
        
        order = cursor.fetchone()
        conn.close()
        
        if not order:
            return HTMLResponse(content="<h1>Work order not found</h1>", status_code=404)
            
        html_content = f\"\"\"
        <!DOCTYPE html>
        <html>
        <head>
            <title>Work Order #{order[0]} - ChatterFix CMMS</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 20px;
                    margin: 0;
                }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .btn {{ 
                    padding: 10px 20px; 
                    background: #2563eb; 
                    color: white; 
                    border: none; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    text-decoration: none;
                    display: inline-block;
                    margin: 5px;
                }}
                .btn:hover {{ background: #1d4ed8; }}
                .work-order-detail {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .quick-actions {{ display: flex; gap: 10px; margin: 20px 0; }}
                .quick-btn {{
                    background: rgba(34, 197, 94, 0.2);
                    border: none;
                    border-radius: 8px;
                    padding: 8px 12px;
                    cursor: pointer;
                    color: white;
                }}
                .quick-btn:hover {{ background: rgba(34, 197, 94, 0.4); }}
                .meta-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📋 Work Order WO-{order[0]:04d}</h1>
                <div>
                    <a href="/work-orders" class="btn">← Back to Work Orders</a>
                </div>
                
                <div class="work-order-detail">
                    <h2>{order[1]}</h2>
                    <p style="color: rgba(255,255,255,0.8); margin: 15px 0;">{order[2]}</p>
                    
                    <div class="quick-actions">
                        <button class="quick-btn" onclick="quickEdit()">✏️ Quick Edit</button>
                        <button class="quick-btn" onclick="quickStatus()">🔄 Change Status</button>
                        <button class="quick-btn" onclick="quickComplete()">✅ Complete</button>
                        <button class="quick-btn" onclick="quickAssign()">👤 Assign</button>
                    </div>
                    
                    <div class="meta-grid">
                        <div><strong>Status:</strong> <span id="status">{order[3]}</span></div>
                        <div><strong>Priority:</strong> <span id="priority">{order[4]}</span></div>
                        <div><strong>Assigned to:</strong> <span id="assigned">{order[5] or 'Unassigned'}</span></div>
                        <div><strong>Created:</strong> {order[6][:10] if order[6] else 'Unknown'}</div>
                        <div><strong>Due:</strong> <span id="due">{order[7][:10] if order[7] else 'Not set'}</span></div>
                    </div>
                </div>
                
                <script>
                    const workOrderId = {order[0]};
                    
                    function quickEdit() {{
                        const title = prompt('Enter new title:', '{order[1]}');
                        if (title && title !== '{order[1]}') {{
                            updateWorkOrder({{title: title}});
                        }}
                    }}
                    
                    function quickStatus() {{
                        const statuses = ['Open', 'In Progress', 'Completed', 'On Hold'];
                        const newStatus = prompt('Select status:\\n' + statuses.join('\\n'), '{order[3]}');
                        if (newStatus && statuses.includes(newStatus)) {{
                            updateWorkOrder({{status: newStatus}});
                        }}
                    }}
                    
                    function quickComplete() {{
                        if (confirm('Mark this work order as completed?')) {{
                            updateWorkOrder({{status: 'Completed'}});
                        }}
                    }}
                    
                    function quickAssign() {{
                        const person = prompt('Assign to:', '{order[5] or ''}');
                        if (person) {{
                            updateWorkOrder({{assigned_to: person}});
                        }}
                    }}
                    
                    async function updateWorkOrder(updates) {{
                        try {{
                            const response = await fetch(`/work-orders/${{workOrderId}}/update`, {{
                                method: 'PUT',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify(updates)
                            }});
                            
                            if (response.ok) {{
                                const result = await response.json();
                                if (result.success) {{
                                    alert('Work order updated successfully!');
                                    location.reload();
                                }} else {{
                                    alert('Update failed: ' + result.error);
                                }}
                            }} else {{
                                alert('Network error occurred');
                            }}
                        }} catch (error) {{
                            alert('Error: ' + error.message);
                        }}
                    }}
                </script>
            </div>
            <script src="/ai-inject.js" async></script>
        </body>
        </html>
        \"\"\"
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading work order: {{e}}</h1>", status_code=500)

@app.put("/work-orders/{work_order_id}/update")
async def update_work_order(work_order_id: int, request: Request):
    \"\"\"Update work order with provided fields\"\"\"
    try:
        data = await request.json()
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        for field in ['title', 'description', 'status', 'priority', 'assigned_to', 'due_date']:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])
                
        if update_fields:
            values.append(work_order_id)
            query = f"UPDATE work_orders SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            
        conn.close()
        return {"success": True, "message": "Work order updated successfully"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
"""

# Enhanced work orders list page
WORK_ORDERS_LIST = '''
@app.get("/work-orders")
async def work_orders():
    """Enhanced work orders page with clickable cards"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, status, priority, assigned_to, created_date, due_date
            FROM work_orders 
            ORDER BY 
                CASE priority 
                    WHEN 'Critical' THEN 1 
                    WHEN 'High' THEN 2 
                    WHEN 'Medium' THEN 3 
                    WHEN 'Low' THEN 4 
                END,
                created_date DESC
        """)
        orders = cursor.fetchall()
        conn.close()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Work Orders - ChatterFix CMMS</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 20px;
                    margin: 0;
                }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .btn {{ 
                    padding: 10px 20px; 
                    background: #2563eb; 
                    color: white; 
                    border: none; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    text-decoration: none;
                    display: inline-block;
                    margin: 5px;
                }}
                .btn:hover {{ background: #1d4ed8; }}
                .work-orders-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .work-order-card {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 12px;
                    padding: 20px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    border: 1px solid rgba(255,255,255,0.2);
                }}
                .work-order-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                }}
                .wo-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 15px;
                }}
                .wo-title {{ font-size: 18px; font-weight: bold; }}
                .wo-id {{
                    background: rgba(37, 99, 235, 0.3);
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 12px;
                }}
                .wo-meta {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    font-size: 13px;
                    margin-top: 15px;
                }}
                .quick-actions {{
                    display: flex;
                    gap: 5px;
                    margin-top: 10px;
                }}
                .quick-btn {{
                    background: rgba(34, 197, 94, 0.2);
                    border: none;
                    border-radius: 4px;
                    padding: 4px 6px;
                    cursor: pointer;
                    font-size: 12px;
                    color: white;
                }}
                .quick-btn:hover {{ background: rgba(34, 197, 94, 0.4); }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📋 Work Orders Management</h1>
                <div>
                    <a href="/" class="btn">← Dashboard</a>
                    <button class="btn" onclick="createWorkOrder()">+ Create New Work Order</button>
                </div>
                
                <div class="work-orders-grid">
        """
        
        for order in orders:
            priority_color = {
                'Critical': '#e74c3c',
                'High': '#f39c12', 
                'Medium': '#3498db',
                'Low': '#2ecc71'
            }.get(order[4], '#3498db')
            
            status_color = {
                'Open': '#f39c12',
                'In Progress': '#3498db',
                'Completed': '#2ecc71',
                'On Hold': '#e74c3c'
            }.get(order[3], '#3498db')
            
            html_content += f"""
                    <div class="work-order-card" onclick="openWorkOrder({order[0]})">
                        <div class="wo-header">
                            <div class="wo-title">{order[1]}</div>
                            <div class="wo-id">WO-{order[0]:04d}</div>
                        </div>
                        
                        <div style="color: rgba(255,255,255,0.8); margin-bottom: 15px; font-size: 14px;">
                            {order[2][:100]}{'...' if len(order[2]) > 100 else ''}
                        </div>
                        
                        <div class="wo-meta">
                            <div style="display: flex; align-items: center; gap: 5px;">
                                <span style="color: {priority_color}; font-size: 16px;">●</span>
                                <span>{order[4]}</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 5px;">
                                <span style="color: {status_color}; font-size: 16px;">●</span>
                                <span>{order[3]}</span>
                            </div>
                            <div>👤 {order[5] or 'Unassigned'}</div>
                            <div>📅 {order[7][:10] if order[7] else 'No due date'}</div>
                        </div>
                        
                        <div class="quick-actions" onclick="event.stopPropagation()">
                            <button class="quick-btn" onclick="quickEdit({order[0]})" title="Quick Edit">✏️</button>
                            <button class="quick-btn" onclick="quickStatus({order[0]}, '{order[3]}')" title="Change Status">🔄</button>
                            {'<button class="quick-btn" onclick="quickComplete(' + str(order[0]) + ')" title="Complete">✅</button>' if order[3] != 'Completed' else ''}
                        </div>
                    </div>
            """
        
        html_content += """
                </div>
                
                <script>
                    function openWorkOrder(workOrderId) {
                        window.location.href = `/work-orders/${workOrderId}`;
                    }
                    
                    function quickEdit(workOrderId) {
                        const title = prompt('Enter new title:');
                        if (title) {
                            updateWorkOrder(workOrderId, {title: title});
                        }
                    }
                    
                    function quickStatus(workOrderId, currentStatus) {
                        const statuses = ['Open', 'In Progress', 'Completed', 'On Hold'];
                        const newStatus = prompt(`Current: ${currentStatus}\\nEnter new status:\\n${statuses.join(', ')}`);
                        if (newStatus && statuses.includes(newStatus)) {
                            updateWorkOrder(workOrderId, {status: newStatus});
                        }
                    }
                    
                    function quickComplete(workOrderId) {
                        if (confirm('Mark this work order as completed?')) {
                            updateWorkOrder(workOrderId, {status: 'Completed'});
                        }
                    }
                    
                    function createWorkOrder() {
                        const title = prompt('Work Order Title:');
                        const description = prompt('Description:');
                        if (title && description) {
                            // Would need a create endpoint
                            alert('Create functionality - to be implemented');
                        }
                    }
                    
                    async function updateWorkOrder(workOrderId, updates) {
                        try {
                            const response = await fetch(`/work-orders/${workOrderId}/update`, {
                                method: 'PUT',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify(updates)
                            });
                            
                            if (response.ok) {
                                const result = await response.json();
                                if (result.success) {
                                    location.reload();
                                } else {
                                    alert('Update failed: ' + result.error);
                                }
                            } else {
                                alert('Network error occurred');
                            }
                        } catch (error) {
                            alert('Error: ' + error.message);
                        }
                    }
                </script>
            </div>
            <script src="/ai-inject.js" async></script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading work orders: {e}</h1>", status_code=500)
'''

if __name__ == "__main__":
    print("Work Order Enhancement Patch Ready")
    print("Add these endpoints to your FastAPI app.py:")
    print("\n1. Enhanced work orders list:")
    print(WORK_ORDERS_LIST)
    print("\n2. Work order detail and update endpoints:")  
    print(WORK_ORDER_ENDPOINTS)