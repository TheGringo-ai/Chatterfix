#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - Enhanced API Endpoints
Competitive features that outclass Maximo, Fiix, and UpKeep
"""

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime, timedelta
import io
import pandas as pd

# Import our advanced modules
try:
    from enhanced_database import init_enhanced_database
    from file_management import FileManager
    from predictive_maintenance_ai import PredictiveMaintenanceAI
except ImportError:
    print("⚠️  Enhanced modules not found - ensure all files are in the same directory")

def add_enhanced_endpoints(app: FastAPI):
    """Add all enhanced endpoints to the main FastAPI app"""
    
    file_manager = FileManager()
    predictive_ai = PredictiveMaintenanceAI()
    
    # ==================== FILE IMPORT/EXPORT ENDPOINTS ====================
    
    @app.post("/api/import/assets")
    async def import_assets(
        file: UploadFile = File(...),
        mapping: str = Form(default="{}")
    ):
        """Import assets from CSV, Excel, JSON, or XML files"""
        try:
            file_data = await file.read()
            file_format = file.filename.split('.')[-1] if file.filename else 'csv'
            field_mapping = json.loads(mapping) if mapping != "{}" else None
            
            result = file_manager.import_assets(file_data, file_format, field_mapping)
            return JSONResponse(content=result)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/import/work-orders")
    async def import_work_orders(
        file: UploadFile = File(...),
        mapping: str = Form(default="{}")
    ):
        """Import work orders from various file formats"""
        try:
            file_data = await file.read()
            file_format = file.filename.split('.')[-1] if file.filename else 'csv'
            field_mapping = json.loads(mapping) if mapping != "{}" else None
            
            result = file_manager.import_work_orders(file_data, file_format, field_mapping)
            return JSONResponse(content=result)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/import/parts")
    async def import_parts(
        file: UploadFile = File(...),
        mapping: str = Form(default="{}")
    ):
        """Import parts inventory from various file formats"""
        try:
            file_data = await file.read()
            file_format = file.filename.split('.')[-1] if file.filename else 'csv'
            field_mapping = json.loads(mapping) if mapping != "{}" else None
            
            result = file_manager.import_parts_inventory(file_data, file_format, field_mapping)
            return JSONResponse(content=result)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/export/assets")
    async def export_assets(
        format: str = "csv",
        location_id: Optional[int] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ):
        """Export assets in specified format with filtering"""
        try:
            filters = {}
            if location_id:
                filters['location_id'] = location_id
            if category:
                filters['category'] = category
            if status:
                filters['status'] = status
            
            file_data = file_manager.export_assets(format, filters)
            
            media_type = {
                'csv': 'text/csv',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'json': 'application/json',
                'xml': 'application/xml'
            }.get(format, 'text/csv')
            
            filename = f"assets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/export/work-orders")
    async def export_work_orders(
        format: str = "csv",
        status: Optional[str] = None,
        priority: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ):
        """Export work orders with advanced filtering"""
        try:
            filters = {}
            if status:
                filters['status'] = status
            if priority:
                filters['priority'] = priority
            if date_from:
                filters['date_from'] = date_from
            if date_to:
                filters['date_to'] = date_to
            
            file_data = file_manager.export_work_orders(format, filters)
            
            media_type = {
                'csv': 'text/csv',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'json': 'application/json',
                'xml': 'application/xml'
            }.get(format, 'text/csv')
            
            filename = f"work_orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/export/maintenance-report")
    async def export_maintenance_report(
        format: str = "csv",
        date_from: str = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        date_to: str = datetime.now().strftime('%Y-%m-%d')
    ):
        """Generate comprehensive maintenance report"""
        try:
            file_data = file_manager.export_maintenance_report(format, date_from, date_to)
            
            media_type = {
                'csv': 'text/csv',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'json': 'application/json',
                'xml': 'application/xml'
            }.get(format, 'text/csv')
            
            filename = f"maintenance_report_{date_from}_to_{date_to}.{format}"
            
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/import/template/{data_type}")
    async def get_import_template(data_type: str, format: str = "csv"):
        """Download import template files"""
        try:
            template_data = file_manager.get_import_template(data_type, format)
            
            media_type = {
                'csv': 'text/csv',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'json': 'application/json'
            }.get(format, 'text/csv')
            
            filename = f"{data_type}_import_template.{format}"
            
            return StreamingResponse(
                io.BytesIO(template_data),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # ==================== PREDICTIVE MAINTENANCE ENDPOINTS ====================
    
    @app.post("/api/predictive/run-analysis")
    async def run_predictive_analysis():
        """Run AI-powered predictive maintenance analysis"""
        try:
            predictions = await predictive_ai.run_predictive_analysis()
            
            return {
                "success": True,
                "predictions_count": len(predictions),
                "high_priority_count": len([p for p in predictions if p.urgency_level in ['Critical', 'High']]),
                "predictions": [
                    {
                        "asset_id": p.asset_id,
                        "prediction_type": p.prediction_type,
                        "confidence_score": p.confidence_score,
                        "predicted_failure_date": p.predicted_failure_date.isoformat() if p.predicted_failure_date else None,
                        "recommended_action": p.recommended_action,
                        "urgency_level": p.urgency_level,
                        "estimated_cost": p.estimated_cost,
                        "ai_provider": p.ai_provider
                    } for p in predictions
                ]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/predictive/predictions")
    async def get_active_predictions():
        """Get active AI predictions"""
        try:
            conn = predictive_ai.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ap.*, a.name as asset_name, a.criticality
                FROM ai_predictions ap
                JOIN assets a ON ap.target_id = a.id
                WHERE ap.target_type = 'asset' 
                AND ap.expiry_date > datetime('now')
                ORDER BY ap.confidence_score DESC, ap.prediction_date DESC
            """)
            
            predictions = []
            for row in cursor.fetchall():
                prediction_data = json.loads(row['prediction_data'])
                predictions.append({
                    "id": row['id'],
                    "asset_id": row['target_id'],
                    "asset_name": row['asset_name'],
                    "asset_criticality": row['criticality'],
                    "prediction_type": row['prediction_type'],
                    "confidence_score": row['confidence_score'],
                    "prediction_date": row['prediction_date'],
                    "provider": row['provider'],
                    **prediction_data
                })
            
            conn.close()
            
            return {"predictions": predictions}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== ADVANCED ANALYTICS ENDPOINTS ====================
    
    @app.get("/api/analytics/dashboard")
    async def get_dashboard_analytics():
        """Get comprehensive dashboard analytics"""
        try:
            conn = predictive_ai.get_db_connection()
            cursor = conn.cursor()
            
            # Key Performance Indicators
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_assets,
                    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_assets,
                    SUM(CASE WHEN condition_rating <= 2 THEN 1 ELSE 0 END) as critical_condition_assets,
                    AVG(condition_rating) as avg_condition_rating,
                    SUM(CASE WHEN criticality = 'Critical' THEN 1 ELSE 0 END) as critical_assets
                FROM assets
            """)
            asset_stats = dict(cursor.fetchone())
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_work_orders,
                    SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_work_orders,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_work_orders,
                    SUM(CASE WHEN priority = 'Critical' THEN 1 ELSE 0 END) as critical_work_orders,
                    SUM(CASE WHEN due_date < datetime('now') AND status != 'Completed' THEN 1 ELSE 0 END) as overdue_work_orders,
                    AVG(actual_cost) as avg_work_order_cost,
                    SUM(actual_cost) as total_maintenance_cost
                FROM work_orders
                WHERE created_date >= datetime('now', '-30 days')
            """)
            wo_stats = dict(cursor.fetchone())
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_parts,
                    SUM(CASE WHEN stock_quantity <= min_stock_level THEN 1 ELSE 0 END) as low_stock_parts,
                    SUM(stock_quantity * unit_cost) as total_inventory_value,
                    AVG(stock_quantity) as avg_stock_level
                FROM parts
            """)
            parts_stats = dict(cursor.fetchone())
            
            # Recent predictions
            cursor.execute("""
                SELECT COUNT(*) as active_predictions,
                       SUM(CASE WHEN JSON_EXTRACT(prediction_data, '$.urgency_level') = 'Critical' THEN 1 ELSE 0 END) as critical_predictions
                FROM ai_predictions 
                WHERE expiry_date > datetime('now')
            """)
            prediction_stats = dict(cursor.fetchone())
            
            # Work order trends (last 30 days)
            cursor.execute("""
                SELECT DATE(created_date) as date, COUNT(*) as count
                FROM work_orders 
                WHERE created_date >= datetime('now', '-30 days')
                GROUP BY DATE(created_date)
                ORDER BY date
            """)
            wo_trends = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "kpis": {
                    "assets": asset_stats,
                    "work_orders": wo_stats,
                    "parts": parts_stats,
                    "predictions": prediction_stats
                },
                "trends": {
                    "work_orders": wo_trends
                },
                "alerts": {
                    "critical_assets": asset_stats.get('critical_condition_assets', 0),
                    "overdue_work_orders": wo_stats.get('overdue_work_orders', 0),
                    "low_stock_parts": parts_stats.get('low_stock_parts', 0),
                    "critical_predictions": prediction_stats.get('critical_predictions', 0)
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== IOT INTEGRATION ENDPOINTS ====================
    
    @app.post("/api/iot/sensor-data")
    async def receive_sensor_data(request: Request):
        """Receive IoT sensor data"""
        try:
            data = await request.json()
            
            conn = predictive_ai.get_db_connection()
            cursor = conn.cursor()
            
            # Insert sensor reading
            cursor.execute("""
                INSERT INTO sensor_readings (
                    asset_id, sensor_type, sensor_value, unit, alert_triggered, alert_level
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.get('asset_id'),
                data.get('sensor_type'),
                data.get('value'),
                data.get('unit', ''),
                data.get('alert', False),
                data.get('alert_level', '')
            ))
            
            conn.commit()
            conn.close()
            
            # Trigger real-time analysis if alert
            if data.get('alert', False):
                # This could trigger immediate predictive analysis
                pass
            
            return {"success": True, "message": "Sensor data received"}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/iot/sensor-data/{asset_id}")
    async def get_sensor_data(asset_id: int, hours: int = 24):
        """Get recent sensor data for an asset"""
        try:
            conn = predictive_ai.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sensor_readings 
                WHERE asset_id = ? AND reading_timestamp >= datetime('now', '-{} hours')
                ORDER BY reading_timestamp DESC
            """.format(hours), (asset_id,))
            
            readings = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {"sensor_readings": readings}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== ADVANCED SEARCH ENDPOINTS ====================
    
    @app.get("/api/search/global")
    async def global_search(q: str, limit: int = 50):
        """Global search across all CMMS entities"""
        try:
            conn = predictive_ai.get_db_connection()
            cursor = conn.cursor()
            
            results = {"assets": [], "work_orders": [], "parts": []}
            
            # Search assets
            cursor.execute("""
                SELECT id, asset_tag, name, category, status
                FROM assets 
                WHERE name LIKE ? OR asset_tag LIKE ? OR category LIKE ?
                LIMIT ?
            """, (f"%{q}%", f"%{q}%", f"%{q}%", limit//3))
            results["assets"] = [dict(row) for row in cursor.fetchall()]
            
            # Search work orders
            cursor.execute("""
                SELECT id, wo_number, title, status, priority
                FROM work_orders 
                WHERE title LIKE ? OR wo_number LIKE ? OR description LIKE ?
                LIMIT ?
            """, (f"%{q}%", f"%{q}%", f"%{q}%", limit//3))
            results["work_orders"] = [dict(row) for row in cursor.fetchall()]
            
            # Search parts
            cursor.execute("""
                SELECT id, part_number, name, category, stock_quantity
                FROM parts 
                WHERE name LIKE ? OR part_number LIKE ? OR category LIKE ?
                LIMIT ?
            """, (f"%{q}%", f"%{q}%", f"%{q}%", limit//3))
            results["parts"] = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== MOBILE API ENDPOINTS ====================
    
    @app.get("/api/mobile/technician-dashboard/{user_id}")
    async def get_technician_mobile_dashboard(user_id: int):
        """Get mobile dashboard for technicians"""
        try:
            conn = predictive_ai.get_db_connection()
            cursor = conn.cursor()
            
            # Get assigned work orders
            cursor.execute("""
                SELECT wo.*, a.name as asset_name, a.location_id
                FROM work_orders wo
                LEFT JOIN assets a ON wo.asset_id = a.id
                WHERE wo.assigned_to = ? AND wo.status IN ('Open', 'In Progress')
                ORDER BY wo.priority DESC, wo.created_date ASC
                LIMIT 10
            """, (user_id,))
            assigned_work_orders = [dict(row) for row in cursor.fetchall()]
            
            # Get recent completions
            cursor.execute("""
                SELECT COUNT(*) as completed_today
                FROM work_orders 
                WHERE assigned_to = ? AND status = 'Completed' 
                AND DATE(completion_date) = DATE('now')
            """, (user_id,))
            completed_today = cursor.fetchone()['completed_today']
            
            conn.close()
            
            return {
                "assigned_work_orders": assigned_work_orders,
                "completed_today": completed_today,
                "pending_count": len([wo for wo in assigned_work_orders if wo['status'] == 'Open']),
                "in_progress_count": len([wo for wo in assigned_work_orders if wo['status'] == 'In Progress'])
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    print("✅ Enhanced API endpoints added successfully!")

# This function will be called from the main app
def setup_enhanced_features(app: FastAPI):
    """Setup all enhanced features"""
    try:
        # Initialize enhanced database
        init_enhanced_database()
        print("✅ Enhanced database initialized")
        
        # Add enhanced endpoints
        add_enhanced_endpoints(app)
        print("✅ Enhanced API endpoints configured")
        
        return True
    except Exception as e:
        print(f"❌ Enhanced features setup failed: {e}")
        return False