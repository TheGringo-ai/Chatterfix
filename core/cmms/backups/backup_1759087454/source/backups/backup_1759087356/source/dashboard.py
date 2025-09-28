#!/usr/bin/env python3
"""
Enterprise Dashboard System for ChatterFix CMMS
Role-based dashboards with KPIs, analytics, and real-time metrics
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class DashboardManager:
    def __init__(self, database_path: str):
        self.database_path = database_path
    
    def get_kpi_data(self, user_role: str, department: str = None) -> Dict:
        """Get KPI data based on user role and department"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        kpis = {}
        
        # Work Orders KPIs
        # Total open work orders
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status != 'Completed'")
        kpis["open_work_orders"] = cursor.fetchone()[0]
        
        # High priority work orders
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE priority = 'Critical' AND status != 'Completed'")
        kpis["critical_work_orders"] = cursor.fetchone()[0]
        
        # Overdue work orders
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE due_date < ? AND status != 'Completed'", 
                      (datetime.now().date(),))
        kpis["overdue_work_orders"] = cursor.fetchone()[0]
        
        # Work orders completed this week
        week_ago = datetime.now() - timedelta(days=7)
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'Completed' AND created_date >= ?", 
                      (week_ago,))
        kpis["completed_this_week"] = cursor.fetchone()[0]
        
        # Asset KPIs
        # Total assets
        cursor.execute("SELECT COUNT(*) FROM assets")
        kpis["total_assets"] = cursor.fetchone()[0]
        
        # Critical assets needing attention
        cursor.execute("SELECT COUNT(*) FROM assets WHERE criticality = 'Critical' AND status != 'Active'")
        kpis["critical_assets_down"] = cursor.fetchone()[0]
        
        # Assets in maintenance
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Maintenance'")
        kpis["assets_in_maintenance"] = cursor.fetchone()[0]
        
        # Parts KPIs
        # Parts below reorder point
        cursor.execute("SELECT COUNT(*) FROM parts WHERE stock_quantity <= min_stock")
        kpis["low_stock_parts"] = cursor.fetchone()[0]
        
        # Total parts value
        cursor.execute("SELECT SUM(stock_quantity * unit_cost) FROM parts WHERE unit_cost IS NOT NULL")
        total_value = cursor.fetchone()[0]
        kpis["total_parts_value"] = round(total_value or 0, 2)
        
        # Performance KPIs (if user has access)
        if user_role in ['admin', 'manager']:
            # Average work order completion time (in days)
            cursor.execute("""
                SELECT AVG(JULIANDAY(completed_date) - JULIANDAY(created_date))
                FROM work_orders 
                WHERE status = 'Completed' AND completed_date IS NOT NULL
                AND created_date >= ?
            """, (week_ago,))
            avg_completion = cursor.fetchone()[0]
            kpis["avg_completion_days"] = round(avg_completion or 0, 1)
            
            # Work order completion rate
            cursor.execute("SELECT COUNT(*) FROM work_orders WHERE created_date >= ?", (week_ago,))
            total_created = cursor.fetchone()[0]
            if total_created > 0:
                kpis["completion_rate"] = round((kpis["completed_this_week"] / total_created) * 100, 1)
            else:
                kpis["completion_rate"] = 0
        
        conn.close()
        return kpis
    
    def get_recent_activities(self, user_role: str, limit: int = 10) -> List[Dict]:
        """Get recent activities based on user role"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        activities = []
        
        # Recent work orders
        cursor.execute("""
            SELECT id, title, status, priority, created_date, 'work_order' as type
            FROM work_orders 
            ORDER BY created_date DESC 
            LIMIT ?
        """, (limit // 2,))
        
        for row in cursor.fetchall():
            activities.append({
                "id": row[0],
                "title": row[1],
                "status": row[2],
                "priority": row[3],
                "date": row[4],
                "type": row[5],
                "icon": "🔧"
            })
        
        # Recent asset updates (if user has access)
        if user_role in ['admin', 'manager', 'technician']:
            cursor.execute("""
                SELECT id, name, status, criticality, last_maintenance, 'asset' as type
                FROM assets 
                WHERE last_maintenance IS NOT NULL
                ORDER BY last_maintenance DESC 
                LIMIT ?
            """, (limit // 2,))
            
            for row in cursor.fetchall():
                activities.append({
                    "id": row[0],
                    "title": f"Maintenance on {row[1]}",
                    "status": row[2],
                    "priority": row[3],
                    "date": row[4],
                    "type": row[5],
                    "icon": "🏭"
                })
        
        # Sort by date
        activities.sort(key=lambda x: x["date"], reverse=True)
        
        conn.close()
        return activities[:limit]
    
    def get_chart_data(self, chart_type: str, user_role: str) -> Dict:
        """Get data for dashboard charts"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        if chart_type == "work_orders_by_status":
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM work_orders 
                GROUP BY status
            """)
            data = dict(cursor.fetchall())
            
            return {
                "labels": list(data.keys()),
                "values": list(data.values()),
                "type": "doughnut"
            }
        
        elif chart_type == "work_orders_by_priority":
            cursor.execute("""
                SELECT priority, COUNT(*) 
                FROM work_orders 
                WHERE status != 'Completed'
                GROUP BY priority
            """)
            data = dict(cursor.fetchall())
            
            return {
                "labels": list(data.keys()),
                "values": list(data.values()),
                "type": "bar"
            }
        
        elif chart_type == "monthly_completion_trend" and user_role in ['admin', 'manager']:
            # Get last 6 months of completion data
            months = []
            values = []
            
            for i in range(6):
                month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
                month_end = month_start + timedelta(days=31)
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM work_orders 
                    WHERE status = 'Completed' 
                    AND created_date >= ? AND created_date < ?
                """, (month_start, month_end))
                
                count = cursor.fetchone()[0]
                months.append(month_start.strftime("%b %Y"))
                values.append(count)
            
            return {
                "labels": list(reversed(months)),
                "values": list(reversed(values)),
                "type": "line"
            }
        
        conn.close()
        return {}
    
    def get_upcoming_maintenance(self, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming maintenance schedules"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # This would need a maintenance_schedules table in a full implementation
        # For now, we'll simulate with work orders due soon
        future_date = datetime.now() + timedelta(days=days_ahead)
        
        cursor.execute("""
            SELECT wo.id, wo.title, wo.due_date, wo.priority, a.name as asset_name
            FROM work_orders wo
            LEFT JOIN assets a ON wo.asset_id = a.id
            WHERE wo.due_date BETWEEN ? AND ? 
            AND wo.status != 'Completed'
            ORDER BY wo.due_date ASC
        """, (datetime.now().date(), future_date.date()))
        
        maintenance_items = []
        for row in cursor.fetchall():
            maintenance_items.append({
                "work_order_id": row[0],
                "title": row[1],
                "due_date": row[2],
                "priority": row[3],
                "asset_name": row[4] or "N/A"
            })
        
        conn.close()
        return maintenance_items

def generate_dashboard_html(user_data: Dict, kpis: Dict, activities: List[Dict], 
                          charts: Dict, maintenance: List[Dict]) -> str:
    """Generate role-based dashboard HTML"""
    
    user_role = user_data["role"]
    user_name = user_data.get("full_name", user_data["username"])
    
    # Role-based welcome message
    role_messages = {
        "admin": "System Administrator Dashboard - Full Control Center",
        "manager": "Management Dashboard - Operations Overview",
        "technician": "Technician Dashboard - Your Work Queue",
        "viewer": "Overview Dashboard - System Status"
    }
    
    welcome_message = role_messages.get(user_role, "Dashboard")
    
    # KPI Cards HTML
    kpi_cards = ""
    
    # Common KPIs for all roles
    kpi_cards += f"""
        <div class="kpi-card urgent" onclick="window.location.href='/work-orders'">
            <div class="kpi-value">{kpis.get('critical_work_orders', 0)}</div>
            <div class="kpi-label">Critical Work Orders</div>
            <div class="kpi-icon">🚨</div>
        </div>
        
        <div class="kpi-card warning" onclick="window.location.href='/work-orders'">
            <div class="kpi-value">{kpis.get('overdue_work_orders', 0)}</div>
            <div class="kpi-label">Overdue Tasks</div>
            <div class="kpi-icon">⏰</div>
        </div>
        
        <div class="kpi-card info" onclick="window.location.href='/work-orders'">
            <div class="kpi-value">{kpis.get('open_work_orders', 0)}</div>
            <div class="kpi-label">Open Work Orders</div>
            <div class="kpi-icon">📋</div>
        </div>
        
        <div class="kpi-card success" onclick="window.location.href='/work-orders'">
            <div class="kpi-value">{kpis.get('completed_this_week', 0)}</div>
            <div class="kpi-label">Completed This Week</div>
            <div class="kpi-icon">✅</div>
        </div>
    """
    
    # Additional KPIs for managers and admins
    if user_role in ['admin', 'manager']:
        kpi_cards += f"""
            <div class="kpi-card info" onclick="window.location.href='/assets'">
                <div class="kpi-value">{kpis.get('total_assets', 0)}</div>
                <div class="kpi-label">Total Assets</div>
                <div class="kpi-icon">🏭</div>
            </div>
            
            <div class="kpi-card warning" onclick="window.location.href='/parts'">
                <div class="kpi-value">{kpis.get('low_stock_parts', 0)}</div>
                <div class="kpi-label">Low Stock Parts</div>
                <div class="kpi-icon">📦</div>
            </div>
            
            <div class="kpi-card info">
                <div class="kpi-value">${kpis.get('total_parts_value', 0):,.2f}</div>
                <div class="kpi-label">Parts Inventory Value</div>
                <div class="kpi-icon">💰</div>
            </div>
            
            <div class="kpi-card performance">
                <div class="kpi-value">{kpis.get('avg_completion_days', 0)}</div>
                <div class="kpi-label">Avg Days to Complete</div>
                <div class="kpi-icon">📊</div>
            </div>
        """
    
    # Recent activities HTML
    activities_html = ""
    for activity in activities[:5]:
        status_class = {
            'Completed': 'success',
            'In Progress': 'info',
            'Open': 'warning',
            'Critical': 'urgent'
        }.get(activity.get('status', ''), 'info')
        
        activities_html += f"""
            <div class="activity-item {status_class}">
                <div class="activity-icon">{activity.get('icon', '📋')}</div>
                <div class="activity-content">
                    <div class="activity-title">{activity['title']}</div>
                    <div class="activity-meta">{activity.get('status', '')} • {activity.get('date', '')}</div>
                </div>
            </div>
        """
    
    # Upcoming maintenance HTML
    maintenance_html = ""
    for item in maintenance[:5]:
        priority_class = {
            'Critical': 'urgent',
            'High': 'warning',
            'Medium': 'info',
            'Low': 'success'
        }.get(item.get('priority', ''), 'info')
        
        maintenance_html += f"""
            <div class="maintenance-item {priority_class}">
                <div class="maintenance-date">{item.get('due_date', '')}</div>
                <div class="maintenance-content">
                    <div class="maintenance-title">{item['title']}</div>
                    <div class="maintenance-asset">Asset: {item.get('asset_name', 'N/A')}</div>
                </div>
                <div class="maintenance-priority">{item.get('priority', '')}</div>
            </div>
        """
    
    return f"""
    <div class="dashboard-header">
        <h1>👋 Welcome back, {user_name}</h1>
        <p class="dashboard-subtitle">{welcome_message}</p>
    </div>
    
    <div class="kpi-grid">
        {kpi_cards}
    </div>
    
    <div class="dashboard-content">
        <div class="dashboard-section">
            <h2>📊 Quick Actions</h2>
            <div class="quick-actions">
                <button class="quick-action-btn primary" onclick="createWorkOrder()">
                    🔧 Create Work Order
                </button>
                <button class="quick-action-btn secondary" onclick="emergencyResponse()">
                    🚨 Emergency Response
                </button>
                <button class="quick-action-btn tertiary" onclick="window.location.href='/parts'">
                    📦 Check Inventory
                </button>
                <button class="quick-action-btn tertiary" onclick="window.location.href='/reports'">
                    📈 View Reports
                </button>
            </div>
        </div>
        
        <div class="dashboard-row">
            <div class="dashboard-card">
                <h3>🔄 Recent Activity</h3>
                <div class="activities-list">
                    {activities_html}
                </div>
                <a href="/activity" class="card-footer-link">View All Activity →</a>
            </div>
            
            <div class="dashboard-card">
                <h3>🗓️ Upcoming Maintenance</h3>
                <div class="maintenance-list">
                    {maintenance_html}
                </div>
                <a href="/maintenance" class="card-footer-link">View Full Schedule →</a>
            </div>
        </div>
        
        {"<div class='dashboard-row'><div class='dashboard-card full-width'><h3>📊 Performance Charts</h3><div class='charts-container'><canvas id='statusChart'></canvas><canvas id='priorityChart'></canvas></div></div></div>" if user_role in ['admin', 'manager'] else ""}
    </div>
    
    <script>
        function createWorkOrder() {{
            window.location.href = '/work-orders/new';
        }}
        
        function emergencyResponse() {{
            if (confirm('Initiate Emergency Response Protocol?')) {{
                window.location.href = '/emergency';
            }}
        }}
        
        // Load charts for managers/admins
        {"window.loadDashboardCharts = true;" if user_role in ['admin', 'manager'] else ""}
    </script>
    """