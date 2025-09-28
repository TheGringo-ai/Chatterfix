#!/usr/bin/env python3
"""
Enterprise Reporting System for ChatterFix CMMS
Comprehensive analytics, reports, and data visualization
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import io
import base64

class ReportingManager:
    def __init__(self, database_path: str):
        self.database_path = database_path
    
    def generate_work_order_report(self, start_date: str = None, end_date: str = None) -> Dict:
        """Generate comprehensive work order analytics"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Date filtering
        date_filter = ""
        params = []
        if start_date and end_date:
            date_filter = "WHERE created_date BETWEEN ? AND ?"
            params = [start_date, end_date]
        
        report = {
            "title": "Work Order Analytics Report",
            "generated_at": datetime.now().isoformat(),
            "period": f"{start_date} to {end_date}" if start_date and end_date else "All Time"
        }
        
        # Summary statistics
        cursor.execute(f"SELECT COUNT(*) FROM work_orders {date_filter}", params)
        report["total_work_orders"] = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM work_orders WHERE status = 'Completed' {date_filter}", params)
        report["completed_work_orders"] = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM work_orders WHERE status != 'Completed' {date_filter}", params)
        report["open_work_orders"] = cursor.fetchone()[0]
        
        # Completion rate
        if report["total_work_orders"] > 0:
            report["completion_rate"] = round((report["completed_work_orders"] / report["total_work_orders"]) * 100, 2)
        else:
            report["completion_rate"] = 0
        
        # Status breakdown
        cursor.execute(f"""
            SELECT status, COUNT(*) 
            FROM work_orders {date_filter}
            GROUP BY status
        """, params)
        report["status_breakdown"] = dict(cursor.fetchall())
        
        # Priority breakdown
        cursor.execute(f"""
            SELECT priority, COUNT(*) 
            FROM work_orders {date_filter}
            GROUP BY priority
        """, params)
        report["priority_breakdown"] = dict(cursor.fetchall())
        
        # Average completion time (in days)
        cursor.execute(f"""
            SELECT AVG(JULIANDAY(completed_date) - JULIANDAY(created_date))
            FROM work_orders 
            WHERE status = 'Completed' AND completed_date IS NOT NULL {date_filter}
        """, params)
        avg_completion = cursor.fetchone()[0]
        report["avg_completion_days"] = round(avg_completion or 0, 2)
        
        # Top 10 most common work order types (by title keywords)
        cursor.execute(f"""
            SELECT title, COUNT(*) as count
            FROM work_orders {date_filter}
            GROUP BY LOWER(title)
            ORDER BY count DESC
            LIMIT 10
        """, params)
        report["common_issues"] = [{"title": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Monthly trend (last 12 months)
        monthly_data = []
        for i in range(12):
            month_start = (datetime.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            month_end = month_start.replace(month=month_start.month % 12 + 1, day=1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1, day=1)
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM work_orders 
                WHERE created_date >= ? AND created_date < ?
            """, (month_start, month_end))
            
            count = cursor.fetchone()[0]
            monthly_data.append({
                "month": month_start.strftime("%Y-%m"),
                "month_name": month_start.strftime("%b %Y"),
                "work_orders": count
            })
        
        report["monthly_trend"] = list(reversed(monthly_data))
        
        conn.close()
        return report
    
    def generate_asset_report(self) -> Dict:
        """Generate asset performance and maintenance report"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        report = {
            "title": "Asset Performance Report",
            "generated_at": datetime.now().isoformat()
        }
        
        # Asset summary
        cursor.execute("SELECT COUNT(*) FROM assets")
        report["total_assets"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Active'")
        report["active_assets"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Maintenance'")
        report["assets_in_maintenance"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets WHERE criticality = 'Critical'")
        report["critical_assets"] = cursor.fetchone()[0]
        
        # Status breakdown
        cursor.execute("SELECT status, COUNT(*) FROM assets GROUP BY status")
        report["status_breakdown"] = dict(cursor.fetchall())
        
        # Criticality breakdown
        cursor.execute("SELECT criticality, COUNT(*) FROM assets GROUP BY criticality")
        report["criticality_breakdown"] = dict(cursor.fetchall())
        
        # Type breakdown
        cursor.execute("SELECT type, COUNT(*) FROM assets GROUP BY type")
        report["type_breakdown"] = dict(cursor.fetchall())
        
        # Assets needing maintenance (no maintenance in last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        cursor.execute("""
            SELECT id, name, last_maintenance, criticality
            FROM assets 
            WHERE last_maintenance IS NULL OR last_maintenance < ?
            ORDER BY criticality DESC, last_maintenance ASC NULLS FIRST
            LIMIT 20
        """, (thirty_days_ago,))
        
        report["assets_needing_maintenance"] = [
            {
                "id": row[0], "name": row[1], 
                "last_maintenance": row[2], "criticality": row[3]
            } 
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return report
    
    def generate_parts_report(self) -> Dict:
        """Generate parts inventory and usage report"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        report = {
            "title": "Parts Inventory Report",
            "generated_at": datetime.now().isoformat()
        }
        
        # Inventory summary
        cursor.execute("SELECT COUNT(*) FROM parts")
        report["total_parts"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM parts WHERE stock_quantity <= min_stock")
        report["low_stock_parts"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM parts WHERE stock_quantity = 0")
        report["out_of_stock_parts"] = cursor.fetchone()[0]
        
        # Total inventory value
        cursor.execute("SELECT SUM(stock_quantity * unit_cost) FROM parts WHERE unit_cost IS NOT NULL")
        total_value = cursor.fetchone()[0]
        report["total_inventory_value"] = round(total_value or 0, 2)
        
        # Low stock items
        cursor.execute("""
            SELECT part_number, name, stock_quantity, min_stock, unit_cost
            FROM parts 
            WHERE stock_quantity <= min_stock
            ORDER BY (stock_quantity / NULLIF(min_stock, 0)) ASC
            LIMIT 20
        """)
        
        report["low_stock_items"] = [
            {
                "part_number": row[0], "name": row[1], 
                "stock": row[2], "min_stock": row[3], "unit_cost": row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # Most valuable parts
        cursor.execute("""
            SELECT part_number, name, stock_quantity, unit_cost, 
                   (stock_quantity * unit_cost) as total_value
            FROM parts 
            WHERE unit_cost IS NOT NULL
            ORDER BY total_value DESC
            LIMIT 10
        """)
        
        report["most_valuable_parts"] = [
            {
                "part_number": row[0], "name": row[1], 
                "stock": row[2], "unit_cost": row[3], "total_value": row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # Category breakdown
        cursor.execute("SELECT category, COUNT(*) FROM parts GROUP BY category")
        report["category_breakdown"] = dict(cursor.fetchall())
        
        conn.close()
        return report
    
    def generate_maintenance_efficiency_report(self) -> Dict:
        """Generate maintenance efficiency and KPI report"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        report = {
            "title": "Maintenance Efficiency Report",
            "generated_at": datetime.now().isoformat()
        }
        
        # Time-based metrics
        thirty_days_ago = datetime.now() - timedelta(days=30)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Work orders created vs completed (last 30 days)
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE created_date >= ?", (thirty_days_ago,))
        orders_created_30d = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE completed_date >= ?", (thirty_days_ago,))
        orders_completed_30d = cursor.fetchone()[0]
        
        report["last_30_days"] = {
            "created": orders_created_30d,
            "completed": orders_completed_30d,
            "completion_rate": round((orders_completed_30d / max(orders_created_30d, 1)) * 100, 2)
        }
        
        # Response times by priority
        priority_metrics = {}
        for priority in ['Critical', 'High', 'Medium', 'Low']:
            cursor.execute("""
                SELECT AVG(JULIANDAY(completed_date) - JULIANDAY(created_date)) * 24
                FROM work_orders 
                WHERE priority = ? AND status = 'Completed'
                AND completed_date IS NOT NULL
            """, (priority,))
            
            avg_hours = cursor.fetchone()[0]
            priority_metrics[priority] = {
                "avg_response_hours": round(avg_hours or 0, 2)
            }
        
        report["response_times"] = priority_metrics
        
        # Overdue work orders
        cursor.execute("""
            SELECT COUNT(*) FROM work_orders 
            WHERE due_date < ? AND status != 'Completed'
        """, (datetime.now().date(),))
        report["overdue_orders"] = cursor.fetchone()[0]
        
        # Backlog analysis
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'Open'")
        open_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'In Progress'")
        in_progress_orders = cursor.fetchone()[0]
        
        report["backlog"] = {
            "open": open_orders,
            "in_progress": in_progress_orders,
            "total_backlog": open_orders + in_progress_orders
        }
        
        # Asset utilization (rough estimate based on work orders)
        cursor.execute("""
            SELECT a.name, COUNT(wo.id) as work_order_count
            FROM assets a
            LEFT JOIN work_orders wo ON wo.asset_id = a.id
            WHERE wo.created_date >= ?
            GROUP BY a.id, a.name
            ORDER BY work_order_count DESC
            LIMIT 10
        """, (thirty_days_ago,))
        
        report["high_maintenance_assets"] = [
            {"asset": row[0], "work_orders": row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return report
    
    def export_to_csv(self, report_type: str, data: Dict) -> str:
        """Export report data to CSV format"""
        import csv
        from io import StringIO
        
        output = StringIO()
        
        if report_type == "work_orders":
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Work Orders", data.get("total_work_orders", 0)])
            writer.writerow(["Completed Work Orders", data.get("completed_work_orders", 0)])
            writer.writerow(["Completion Rate %", data.get("completion_rate", 0)])
            writer.writerow(["Average Completion Days", data.get("avg_completion_days", 0)])
            
            # Status breakdown
            writer.writerow([])
            writer.writerow(["Status Breakdown"])
            writer.writerow(["Status", "Count"])
            for status, count in data.get("status_breakdown", {}).items():
                writer.writerow([status, count])
                
        elif report_type == "assets":
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Assets", data.get("total_assets", 0)])
            writer.writerow(["Active Assets", data.get("active_assets", 0)])
            writer.writerow(["Critical Assets", data.get("critical_assets", 0)])
            
        elif report_type == "parts":
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Parts", data.get("total_parts", 0)])
            writer.writerow(["Low Stock Parts", data.get("low_stock_parts", 0)])
            writer.writerow(["Total Inventory Value", f"${data.get('total_inventory_value', 0):.2f}"])
        
        return output.getvalue()
    
    def generate_dashboard_widgets(self, user_role: str) -> List[Dict]:
        """Generate dashboard widgets based on user role"""
        widgets = []
        
        # Common widgets for all roles
        widgets.extend([
            {
                "id": "critical_alerts",
                "title": "Critical Alerts",
                "type": "alert_list",
                "priority": 1,
                "data": self._get_critical_alerts()
            },
            {
                "id": "work_order_summary",
                "title": "Work Orders Status",
                "type": "chart",
                "chart_type": "doughnut",
                "priority": 2,
                "data": self._get_work_order_status_chart()
            }
        ])
        
        # Manager/Admin specific widgets
        if user_role in ['admin', 'manager']:
            widgets.extend([
                {
                    "id": "monthly_trends",
                    "title": "Monthly Trends",
                    "type": "chart",
                    "chart_type": "line",
                    "priority": 3,
                    "data": self._get_monthly_trend_data()
                },
                {
                    "id": "asset_health",
                    "title": "Asset Health Overview",
                    "type": "metrics",
                    "priority": 4,
                    "data": self._get_asset_health_metrics()
                },
                {
                    "id": "maintenance_efficiency",
                    "title": "Maintenance Efficiency",
                    "type": "kpi_cards",
                    "priority": 5,
                    "data": self._get_efficiency_metrics()
                }
            ])
        
        return sorted(widgets, key=lambda x: x["priority"])
    
    def _get_critical_alerts(self) -> List[Dict]:
        """Get critical system alerts"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        alerts = []
        
        # Overdue critical work orders
        cursor.execute("""
            SELECT id, title, due_date
            FROM work_orders 
            WHERE priority = 'Critical' AND due_date < ? AND status != 'Completed'
            ORDER BY due_date ASC
            LIMIT 5
        """, (datetime.now().date(),))
        
        for row in cursor.fetchall():
            alerts.append({
                "type": "overdue_critical",
                "message": f"Critical work order #{row[0]} is overdue",
                "details": row[1],
                "due_date": row[2]
            })
        
        # Critical assets down
        cursor.execute("""
            SELECT id, name
            FROM assets 
            WHERE criticality = 'Critical' AND status != 'Active'
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            alerts.append({
                "type": "critical_asset_down",
                "message": f"Critical asset '{row[1]}' is not active",
                "asset_id": row[0]
            })
        
        conn.close()
        return alerts
    
    def _get_work_order_status_chart(self) -> Dict:
        """Get work order status data for charts"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT status, COUNT(*) FROM work_orders GROUP BY status")
        data = dict(cursor.fetchall())
        
        conn.close()
        return {
            "labels": list(data.keys()),
            "values": list(data.values()),
            "colors": ["#ff6b6b", "#ffa726", "#42a5f5", "#66bb6a"]
        }
    
    def _get_monthly_trend_data(self) -> Dict:
        """Get monthly work order trend data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        months = []
        values = []
        
        for i in range(6):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=31)
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM work_orders 
                WHERE created_date >= ? AND created_date < ?
            """, (month_start, month_end))
            
            count = cursor.fetchone()[0]
            months.append(month_start.strftime("%b"))
            values.append(count)
        
        conn.close()
        return {
            "labels": list(reversed(months)),
            "values": list(reversed(values))
        }
    
    def _get_asset_health_metrics(self) -> Dict:
        """Get asset health overview metrics"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Active'")
        active = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Maintenance'")
        maintenance = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Inactive'")
        inactive = cursor.fetchone()[0]
        
        total = active + maintenance + inactive
        
        conn.close()
        return {
            "total_assets": total,
            "active_percentage": round((active / max(total, 1)) * 100, 1),
            "maintenance_percentage": round((maintenance / max(total, 1)) * 100, 1),
            "inactive_percentage": round((inactive / max(total, 1)) * 100, 1)
        }
    
    def _get_efficiency_metrics(self) -> Dict:
        """Get maintenance efficiency KPIs"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Average completion time
        cursor.execute("""
            SELECT AVG(JULIANDAY(completed_date) - JULIANDAY(created_date))
            FROM work_orders 
            WHERE status = 'Completed' AND completed_date IS NOT NULL
        """)
        avg_completion = cursor.fetchone()[0] or 0
        
        # First-time fix rate (simplified - assuming completed without reopening)
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'Completed'")
        completed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM work_orders")
        total = cursor.fetchone()[0]
        
        fix_rate = (completed / max(total, 1)) * 100
        
        conn.close()
        return {
            "avg_completion_days": round(avg_completion, 1),
            "first_time_fix_rate": round(fix_rate, 1),
            "completed_orders": completed,
            "total_orders": total
        }