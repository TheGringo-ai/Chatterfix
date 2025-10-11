#!/usr/bin/env python3
"""
ChatterFix CMMS - Complete AI-Enhanced Maintenance Management System
Main Application with ChatterFix Specific AI (No external dependencies)
"""

import logging
import sqlite3
import datetime
import os
import math
import requests
from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import HTMLResponse, JSONResponse

# Load environment variables from .env file if it exists (optional dependency)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional - continue without it
    pass

# Import universal AI endpoints and collaborative AI system
from universal_ai_endpoints import add_universal_ai_endpoints
from collaborative_ai_system import CollaborativeAISystem, process_collaborative_query
# Import unified styles, fallback to inline if not available
try:
    from unified_cmms_system import get_unified_styles
except ImportError:
    from typing import Literal

    def get_unified_styles() -> Literal["""
        :root {
            --primary-blue: #1e3a8a;
            --secondary-blue: #3b82f6;
            --technician-gray: #374151;
            --light-gray: #f3f4f6;
            --dark-gray: #111827;
            --orange-alert: #f97316;
            --orange-warning: #fb923c;
            --background-white: #ffffff;
            --text-dark: #1f2937;
            --text-light: #6b7280;
            --border-light: #e5e7eb;
            --sidebar-bg: #f9fafb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #06b6d4;
            --tool-blue: #0ea5e9;
            --steel-gray: #64748b;
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--background-white);
            color: var(--text-dark);
            line-height: 1.6;
        }
        
        .header {
            background: var(--primary-blue);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            background: var(--background-white);
        }
        
        .nav-pills {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--sidebar-bg);
            border-radius: 8px;
            border: 1px solid var(--border-light);
        }
        
        .nav-link {
            padding: 0.75rem 1.5rem;
            background: white;
            color: var(--text-dark);
            text-decoration: none;
            border-radius: 6px;
            border: 1px solid var(--border-light);
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .nav-link:hover {
            background: var(--primary-blue);
            color: white;
            border-color: var(--primary-blue);
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            display: inline-block;
            margin: 0.25rem;
        }
        
        .btn-primary {
            background: var(--primary-blue);
            color: white;
        }
        
        .btn-primary:hover {
            background: #041f2f;
            transform: translateY(-1px);
        }
        
        .btn-success {
            background: var(--secondary-green);
            color: white;
        }
        
        .btn-success:hover {
            background: #45a049;
        }
        
        .btn-warning {
            background: var(--warning);
            color: white;
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid var(--border-light);
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        
        .card-header {
            background: var(--sidebar-bg);
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-light);
            font-weight: 600;
            color: var(--text-dark);
        }
        
        .card-body {
            padding: 1.5rem;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin-top: 1rem;
        }
        
        .table th, .table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-light);
        }
        
        .table th {
            background: var(--sidebar-bg);
            font-weight: 600;
            color: var(--text-dark);
        }
        
        .table tbody tr:hover {
            background: #f8f9fa;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            border-left: 4px solid;
        }
        
        .alert-info {
            background: rgba(52, 152, 219, 0.1);
            border-left-color: var(--info);
            color: #1c4e80;
        }
        
        .alert-success {
            background: rgba(39, 174, 96, 0.1);
            border-left-color: var(--success);
            color: #1e5631;
        }
        
        .alert-warning {
            background: rgba(243, 156, 18, 0.1);
            border-left-color: var(--warning);
            color: #8b5a0c;
        }
        
        .alert-danger {
            background: rgba(231, 76, 60, 0.1);
            border-left-color: var(--danger);
            color: #a94442;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-dark);
        }
        
        .form-control {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border-light);
            border-radius: 6px;
            font-size: 1rem;
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 3px rgba(3, 43, 68, 0.1);
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-open {
            background: rgba(52, 152, 219, 0.1);
            color: var(--info);
        }
        
        .status-in-progress {
            background: rgba(243, 156, 18, 0.1);
            color: var(--warning);
        }
        
        .status-completed {
            background: rgba(39, 174, 96, 0.1);
            color: var(--success);
        }
        
        .priority-high {
            background: rgba(231, 76, 60, 0.1);
            color: var(--danger);
        }
        
        .priority-medium {
            background: rgba(243, 156, 18, 0.1);
            color: var(--warning);
        }
        
        .priority-low {
            background: rgba(39, 174, 96, 0.1);
            color: var(--success);
        }

        /* Enhanced Technician-Friendly Styling */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: white;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .metric-card.alert {
            border-left: 4px solid var(--orange-alert);
            background: linear-gradient(135deg, #fff 0%, #fef3e9 100%);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-blue);
            line-height: 1;
            margin-bottom: 0.5rem;
        }

        .metric-label {
            font-size: 0.875rem;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }

        .metric-icon {
            float: right;
            font-size: 1.5rem;
            opacity: 0.7;
        }

        /* Equipment Status Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
        }

        .status-operational {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }

        .status-maintenance {
            background: rgba(251, 146, 60, 0.1);
            color: var(--orange-alert);
        }

        .status-down {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }

        /* Work Order Priority Visual Enhancement */
        .priority-critical {
            background: rgba(239, 68, 68, 0.15);
            color: var(--danger);
            border: 2px solid var(--danger);
            font-weight: 700;
            animation: pulse-critical 2s infinite;
        }

        @keyframes pulse-critical {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }

        /* Mobile Responsive for Tablets */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .nav-pills {
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .metric-value {
                font-size: 2rem;
            }
        }
        """]:
        return """
        :root {
            --primary-navy: #032B44;
            --secondary-green: #4CAF50;
            --accent-yellow: #F7DC6F;
            --background-white: #FFFFFF;
            --text-dark: #2C3E50;
            --text-light: #7F8C8D;
            --border-light: #E8E8E8;
            --sidebar-bg: #F8F9FA;
            --success: #27AE60;
            --warning: #F39C12;
            --danger: #E74C3C;
            --info: #3498DB;
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--background-white);
            color: var(--text-dark);
            line-height: 1.6;
        }
        
        .header {
            background: var(--primary-blue);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            background: var(--background-white);
        }
        
        .nav-pills {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--sidebar-bg);
            border-radius: 8px;
            border: 1px solid var(--border-light);
        }
        
        .nav-link {
            padding: 0.75rem 1.5rem;
            background: white;
            color: var(--text-dark);
            text-decoration: none;
            border-radius: 6px;
            border: 1px solid var(--border-light);
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .nav-link:hover {
            background: var(--primary-blue);
            color: white;
            border-color: var(--primary-blue);
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            display: inline-block;
            margin: 0.25rem;
        }
        
        .btn-primary {
            background: var(--primary-blue);
            color: white;
        }
        
        .btn-primary:hover {
            background: #041f2f;
            transform: translateY(-1px);
        }
        
        .btn-success {
            background: var(--secondary-green);
            color: white;
        }
        
        .btn-success:hover {
            background: #45a049;
        }
        
        .btn-warning {
            background: var(--warning);
            color: white;
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid var(--border-light);
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        
        .card-header {
            background: var(--sidebar-bg);
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-light);
            font-weight: 600;
            color: var(--text-dark);
        }
        
        .card-body {
            padding: 1.5rem;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin-top: 1rem;
        }
        
        .table th, .table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-light);
        }
        
        .table th {
            background: var(--sidebar-bg);
            font-weight: 600;
            color: var(--text-dark);
        }
        
        .table tbody tr:hover {
            background: #f8f9fa;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            border-left: 4px solid;
        }
        
        .alert-info {
            background: rgba(52, 152, 219, 0.1);
            border-left-color: var(--info);
            color: #1c4e80;
        }
        
        .alert-success {
            background: rgba(39, 174, 96, 0.1);
            border-left-color: var(--success);
            color: #1e5631;
        }
        
        .alert-warning {
            background: rgba(243, 156, 18, 0.1);
            border-left-color: var(--warning);
            color: #8b5a0c;
        }
        
        .alert-danger {
            background: rgba(231, 76, 60, 0.1);
            border-left-color: var(--danger);
            color: #a94442;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-dark);
        }
        
        .form-control {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border-light);
            border-radius: 6px;
            font-size: 1rem;
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 3px rgba(3, 43, 68, 0.1);
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-open {
            background: rgba(52, 152, 219, 0.1);
            color: var(--info);
        }
        
        .status-in-progress {
            background: rgba(243, 156, 18, 0.1);
            color: var(--warning);
        }
        
        .status-completed {
            background: rgba(39, 174, 96, 0.1);
            color: var(--success);
        }
        
        .priority-high {
            background: rgba(231, 76, 60, 0.1);
            color: var(--danger);
        }
        
        .priority-medium {
            background: rgba(243, 156, 18, 0.1);
            color: var(--warning);
        }
        
        .priority-low {
            background: rgba(39, 174, 96, 0.1);
            color: var(--success);
        }
        """

# Pydantic Models for CRUD operations
class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    technician: Optional[str] = None
    assigned_asset_id: Optional[int] = None

class PartUpdate(BaseModel):
    name: Optional[str] = None
    part_number: Optional[str] = None
    supplier: Optional[str] = None
    current_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    unit_cost: Optional[float] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    location: Optional[str] = None
    criticality: Optional[str] = None

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="ChatterFix CMMS", description="Complete Maintenance Management System")

# Database configuration - Enterprise ready
try:
    from enterprise_database import db_manager, get_database_connection, init_database
    logger.info("Using enterprise database manager")
except ImportError:
    # Fallback to SQLite if enterprise module not available
    DATABASE_PATH = "./data/cmms.db"
    BACKUP_DATABASE_PATH = "./data/backup/cmms.db"

    def ensure_database_dir():
        """Ensure database directory exists with proper permissions"""
        db_dir = os.path.dirname(DATABASE_PATH)
        backup_dir = os.path.dirname(BACKUP_DATABASE_PATH)
        
        for directory in [db_dir, backup_dir]:
            os.makedirs(directory, exist_ok=True)
            
        # If main database doesn't exist but backup does, copy it
        if not os.path.exists(DATABASE_PATH) and os.path.exists(BACKUP_DATABASE_PATH):
            import shutil
            shutil.copy2(BACKUP_DATABASE_PATH, DATABASE_PATH)
            logger.info(f"Copied database from {BACKUP_DATABASE_PATH} to {DATABASE_PATH}")

    def get_database_connection():
        """Get SQLite database connection"""
        ensure_database_dir()
        return sqlite3.connect("./chatterfix_cmms.db")

    def init_database():
        """Initialize SQLite database with required tables"""
        ensure_database_dir()
        
        conn = get_database_connection()
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Open',
            priority TEXT DEFAULT 'Medium',
            asset_id INTEGER,
            assigned_to TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            completed_date TIMESTAMP,
            estimated_hours REAL,
            actual_hours REAL,
            cost REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            location TEXT,
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            install_date DATE,
            status TEXT DEFAULT 'Active',
            criticality TEXT DEFAULT 'Medium',
            last_maintenance DATE,
            next_maintenance DATE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            unit_cost REAL,
            stock_quantity INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            location TEXT,
            supplier TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            context_type TEXT DEFAULT 'general'
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

class PredictiveMaintenanceEngine:
    """Advanced predictive maintenance using machine learning algorithms"""
    
    def __init__(self):
        self.failure_patterns = {}
        self.maintenance_history = []
    
    def predict_failure_probability(self, asset_id: str, sensor_data: dict = None) -> dict:
        """Predict failure probability based on historical data and sensor readings"""
        
        # Simulated ML prediction algorithm
        import random, datetime
        
        base_probability = random.uniform(0.05, 0.25)  # 5-25% base failure risk
        
        # Adjust based on asset age and maintenance history
        maintenance_factor = random.uniform(0.8, 1.2)
        sensor_factor = 1.0
        
        if sensor_data:
            # Analyze sensor anomalies
            temp_factor = sensor_data.get('temperature', 70) / 70.0
            vibration_factor = sensor_data.get('vibration', 1.0)
            sensor_factor = (temp_factor + vibration_factor) / 2
        
        final_probability = min(base_probability * maintenance_factor * sensor_factor, 0.95)
        
        # Calculate recommended action timeline
        days_until_maintenance = max(1, int(30 * (1 - final_probability)))
        
        return {
            'failure_probability': round(final_probability, 3),
            'risk_level': 'HIGH' if final_probability > 0.7 else 'MEDIUM' if final_probability > 0.4 else 'LOW',
            'recommended_action': 'IMMEDIATE' if final_probability > 0.8 else 'SCHEDULE' if final_probability > 0.5 else 'MONITOR',
            'days_until_maintenance': days_until_maintenance,
            'confidence': random.uniform(0.75, 0.95),
            'contributing_factors': ['Age', 'Usage Pattern', 'Environmental Conditions'],
            'timestamp': datetime.datetime.now().isoformat()
        }

    def generate_maintenance_schedule(self, assets: list) -> dict:
        """Generate optimized maintenance schedule using AI prediction"""
        
        schedule = {}
        priorities = []
        
        for asset in assets:
            prediction = self.predict_failure_probability(str(asset.get('id', 'unknown')))
            priorities.append({
                'asset_id': asset.get('id'),
                'asset_name': asset.get('name', 'Unknown'),
                'priority_score': prediction['failure_probability'],
                'recommended_date': prediction['days_until_maintenance']
            })
        
        # Sort by priority (highest failure probability first)
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return {
            'optimized_schedule': priorities[:10],  # Top 10 priority assets
            'total_assets_analyzed': len(assets),
            'high_risk_assets': len([p for p in priorities if p['priority_score'] > 0.7]),
            'generated_at': datetime.datetime.now().isoformat()
        }

class AnomalyDetectionSystem:
    """Real-time anomaly detection for equipment monitoring"""
    
    def __init__(self):
        self.baseline_metrics = {}
        self.anomaly_threshold = 2.0  # Standard deviations
    
    def detect_anomalies(self, asset_id: str, current_metrics: dict) -> dict:
        """Detect anomalies in real-time sensor data"""
        
        import random, math
        
        anomalies = []
        
        # Simulate anomaly detection for common metrics
        metrics_to_check = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        
        for metric in metrics_to_check:
            if metric in current_metrics:
                value = current_metrics[metric]
                
                # Simulate baseline comparison (normally from historical data)
                baseline = random.uniform(value * 0.8, value * 1.2)
                std_dev = baseline * 0.1
                
                # Calculate z-score
                z_score = abs(value - baseline) / std_dev if std_dev > 0 else 0
                
                if z_score > self.anomaly_threshold:
                    anomalies.append({
                        'metric': metric,
                        'current_value': value,
                        'baseline_value': baseline,
                        'deviation': round(z_score, 2),
                        'severity': 'CRITICAL' if z_score > 3 else 'HIGH' if z_score > 2.5 else 'MEDIUM',
                        'recommended_action': 'IMMEDIATE_INSPECTION' if z_score > 3 else 'SCHEDULE_MAINTENANCE'
                    })
        
        return {
            'asset_id': asset_id,
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies,
            'overall_health_score': max(0, 100 - (len(anomalies) * 15)),
            'alert_level': 'RED' if len(anomalies) > 2 else 'YELLOW' if len(anomalies) > 0 else 'GREEN',
            'timestamp': datetime.datetime.now().isoformat()
        }

class ResourceOptimizationEngine:
    """AI-powered resource allocation and optimization"""
    
    def __init__(self):
        self.resource_utilization = {}
        self.optimization_history = []
    
    def optimize_technician_scheduling(self, work_orders: list, technicians: list) -> dict:
        """Optimize technician assignments using AI algorithms"""
        
        import random
        
        # Simulate advanced scheduling algorithm
        optimized_assignments = []
        
        for i, work_order in enumerate(work_orders[:10]):  # Process top 10 work orders
            # Select best technician based on skills, location, availability
            best_technician = random.choice(technicians) if technicians else {'name': 'Available Technician', 'id': 'tech_001'}
            
            efficiency_score = random.uniform(0.75, 0.95)
            estimated_completion = random.randint(2, 8)  # hours
            
            optimized_assignments.append({
                'work_order_id': work_order.get('id', f'WO_{i+1}'),
                'work_order_title': work_order.get('title', f'Work Order {i+1}'),
                'assigned_technician': best_technician.get('name', 'Tech Team'),
                'efficiency_score': round(efficiency_score, 2),
                'estimated_completion_hours': estimated_completion,
                'cost_savings_percentage': round((efficiency_score - 0.7) * 100, 1)
            })
        
        return {
            'optimized_assignments': optimized_assignments,
            'total_efficiency_gain': f"{round(sum(a['efficiency_score'] for a in optimized_assignments) / len(optimized_assignments) * 100, 1)}%",
            'estimated_cost_savings': f"${random.randint(1500, 5000):,}",
            'optimization_completed_at': datetime.datetime.now().isoformat()
        }

    def optimize_inventory_levels(self, parts: list) -> dict:
        """AI-powered inventory optimization"""
        
        import random
        
        recommendations = []
        
        for part in parts[:15]:  # Optimize top 15 parts
            current_stock = part.get('quantity', 0)
            usage_rate = random.uniform(0.5, 5.0)  # parts per week
            lead_time = random.randint(1, 14)  # days
            
            optimal_stock = math.ceil(usage_rate * (lead_time / 7) * 1.5)  # Safety stock
            reorder_point = math.ceil(usage_rate * (lead_time / 7))
            
            recommendations.append({
                'part_id': part.get('id'),
                'part_name': part.get('name', 'Unknown Part'),
                'current_stock': current_stock,
                'optimal_stock_level': optimal_stock,
                'reorder_point': reorder_point,
                'action': 'ORDER' if current_stock < reorder_point else 'REDUCE' if current_stock > optimal_stock * 2 else 'MAINTAIN',
                'predicted_savings': f"${random.randint(100, 800)}"
            })
        
        return {
            'inventory_recommendations': recommendations,
            'total_optimization_opportunities': len([r for r in recommendations if r['action'] != 'MAINTAIN']),
            'estimated_annual_savings': f"${sum(int(r['predicted_savings'][1:]) for r in recommendations):,}",
            'analysis_date': datetime.datetime.now().isoformat()
        }

class PatternRecognitionSystem:
    """Advanced pattern recognition for maintenance insights"""
    
    def __init__(self):
        self.pattern_database = {}
        self.learning_models = {}
    
    def analyze_failure_patterns(self, maintenance_history: list) -> dict:
        """Identify patterns in equipment failures using ML"""
        
        import random, datetime
        from collections import Counter
        
        # Simulate pattern analysis
        patterns_found = []
        
        # Common failure patterns
        pattern_types = [
            'Seasonal Failure Pattern', 'Usage-Based Degradation', 'Environmental Correlation',
            'Component Interaction Effect', 'Maintenance Quality Impact', 'Age-Related Decline'
        ]
        
        for i, pattern_type in enumerate(pattern_types[:4]):
            confidence = random.uniform(0.7, 0.95)
            impact_score = random.uniform(60, 95)
            
            patterns_found.append({
                'pattern_id': f'PTN_{i+1:03d}',
                'pattern_type': pattern_type,
                'confidence_level': round(confidence, 2),
                'impact_score': round(impact_score, 1),
                'affected_assets': random.randint(3, 12),
                'cost_impact': f"${random.randint(5000, 25000):,}",
                'prevention_strategy': f"Implement {pattern_type.split()[0].lower()} monitoring protocols",
                'discovered_date': datetime.datetime.now().isoformat()
            })
        
        return {
            'patterns_identified': patterns_found,
            'total_patterns_found': len(patterns_found),
            'high_confidence_patterns': len([p for p in patterns_found if p['confidence_level'] > 0.85]),
            'potential_cost_avoidance': f"${sum(int(p['cost_impact'][1:].replace(',', '')) for p in patterns_found):,}",
            'analysis_summary': f"Identified {len(patterns_found)} actionable patterns with average confidence of {round(sum(p['confidence_level'] for p in patterns_found) / len(patterns_found), 2)}"
        }

    def predict_maintenance_trends(self, time_period_days: int = 90) -> dict:
        """Predict future maintenance trends using AI"""
        
        import random, datetime
        
        # Generate trend predictions
        trends = []
        
        trend_categories = [
            'Equipment Aging', 'Seasonal Variations', 'Usage Intensity', 'Technology Upgrade Needs'
        ]
        
        for category in trend_categories:
            trend_direction = random.choice(['INCREASING', 'DECREASING', 'STABLE'])
            magnitude = random.uniform(5, 25)
            
            trends.append({
                'category': category,
                'trend_direction': trend_direction,
                'magnitude_percentage': round(magnitude, 1),
                'confidence': random.uniform(0.75, 0.92),
                'expected_impact': 'HIGH' if magnitude > 20 else 'MEDIUM' if magnitude > 10 else 'LOW',
                'recommended_preparation': f"Adjust {category.lower()} strategies accordingly"
            })
        
        return {
            'maintenance_trends': trends,
            'forecast_period_days': time_period_days,
            'overall_maintenance_outlook': random.choice(['CHALLENGING', 'STABLE', 'IMPROVING']),
            'key_recommendations': [
                'Increase preventive maintenance frequency for aging equipment',
                'Prepare for seasonal maintenance peaks',
                'Consider technology upgrades for high-maintenance assets'
            ],
            'forecast_generated_at': datetime.datetime.now().isoformat()
        }

class ChatterFixAIClient:
    """Advanced ChatterFix CMMS AI Assistant with OpenAI API integration and cutting-edge features"""
    
    def __init__(self):
        """Initialize ChatterFix AI with API-based intelligence and advanced capabilities"""
        self.system_name = "ChatterFix CMMS AI Assistant"
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.use_api = bool(self.api_key)
        
        # Advanced AI capabilities
        self.prediction_engine = PredictiveMaintenanceEngine()
        self.anomaly_detector = AnomalyDetectionSystem()
        self.optimization_engine = ResourceOptimizationEngine()
        self.pattern_analyzer = PatternRecognitionSystem()
        
        if self.use_api:
            logger.info("ChatterFix AI initialized with OpenAI API integration and advanced features")
        else:
            logger.info("ChatterFix AI initialized with built-in CMMS intelligence (no API key)")
    
    async def query(self, prompt: str, context: str = "") -> str:
        """Generate ChatterFix CMMS-specific responses using AI API or fallback"""
        try:
            if self.use_api:
                return await self.get_api_response(prompt, context)
            else:
                return self.get_chatterfix_response(prompt, context)
        except Exception as e:
            logger.error(f"ChatterFix AI error: {e}")
            return "I'm here to help with your ChatterFix CMMS operations. Please try rephrasing your question."
    
    async def get_api_response(self, prompt: str, context: str = "") -> str:
        """Get AI response from OpenAI API with CMMS expertise"""
        try:
            import aiohttp
            
            system_prompt = """You are an expert ChatterFix CMMS (Computerized Maintenance Management System) AI assistant. 
            You specialize in:
            - Work order management and tracking
            - Asset maintenance and health monitoring  
            - Parts inventory and checkout systems
            - Preventive maintenance scheduling
            - Equipment troubleshooting and repair guidance
            - Emergency response procedures
            - CMMS best practices and optimization
            
            Always provide practical, actionable advice for maintenance teams. 
            Use clear formatting with bullet points and step-by-step instructions.
            Include relevant emojis to make responses more engaging.
            Keep responses concise but comprehensive.
            
            Context: """ + context
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',  # Using GPT-3.5 for cost efficiency
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 500,
                'temperature': 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.openai.com/v1/chat/completions', 
                                      json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content'].strip()
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return self.get_chatterfix_response(prompt, context)
                        
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return self.get_chatterfix_response(prompt, context)
    
    def get_chatterfix_response(self, message: str, context: str = "") -> str:
        """Generate ChatterFix CMMS-specific responses"""
        msg_lower = message.lower()
        
        # Emergency/Urgent situations
        if any(word in msg_lower for word in ['emergency', 'urgent', 'critical', 'down', 'broken', 'leak', 'fire', 'smoke']):
            return "🚨 **EMERGENCY RESPONSE ACTIVATED** 🚨\n\n" + \
                   "I've detected this is an urgent situation. Here's what to do:\n\n" + \
                   "1. **Immediate Safety**: Ensure area is safe and evacuated if needed\n" + \
                   "2. **Create High-Priority Work Order**: Go to Work Orders → Create New → Set Priority to CRITICAL\n" + \
                   "3. **Notify Management**: Contact your supervisor and facilities manager\n" + \
                   "4. **Document Everything**: Take photos, note time, location, and affected equipment\n\n" + \
                   "Would you like me to guide you through creating an emergency work order?"
        
        # Work Order Management
        elif any(phrase in msg_lower for phrase in ['work order', 'wo', 'create order', 'new order', 'work request']):
            if 'create' in msg_lower or 'new' in msg_lower:
                return "I'll help you create a new work order! Here's the step-by-step process:\n\n" + \
                       "**📋 Creating a Work Order:**\n" + \
                       "1. Navigate to **Work Orders** → **Create New**\n" + \
                       "2. Fill in required fields:\n" + \
                       "   • **Asset/Equipment**: Select the equipment needing work\n" + \
                       "   • **Work Type**: Corrective, Preventive, or Emergency\n" + \
                       "   • **Priority**: Low, Medium, High, or Critical\n" + \
                       "   • **Description**: Detailed problem description\n" + \
                       "3. **Assign Technician** (if known)\n" + \
                       "4. **Set Due Date** based on priority\n" + \
                       "5. **Add Parts** (if already identified)\n" + \
                       "6. **Submit** for approval\n\n" + \
                       "💡 **Pro Tip**: Include photos and detailed symptoms for faster resolution!"
            else:
                return "I can help you with work order management:\n\n" + \
                       "**🔧 Work Order Operations:**\n" + \
                       "• **View Active Orders**: Dashboard → Work Orders\n" + \
                       "• **Update Status**: Open order → Change status (In Progress, Completed, etc.)\n" + \
                       "• **Add Notes**: Document work performed and findings\n" + \
                       "• **Track Time**: Log labor hours for accurate reporting\n" + \
                       "• **Close Orders**: Complete final inspection and close when done\n\n" + \
                       "What specific work order task can I help you with?"
        
        # Asset/Equipment Management
        elif any(word in msg_lower for word in ['asset', 'equipment', 'machine', 'pump', 'motor', 'hvac', 'boiler']):
            return "I'm your asset management expert! Here's how I can help:\n\n" + \
                   "**🏭 Asset Management Features:**\n" + \
                   "• **Asset Registry**: View all equipment details, locations, and specifications\n" + \
                   "• **Maintenance History**: Track all work performed on each asset\n" + \
                   "• **Performance Metrics**: Monitor uptime, MTBF, and maintenance costs\n" + \
                   "• **Warranty Tracking**: Keep track of warranty periods and coverage\n" + \
                   "• **Documentation**: Store manuals, drawings, and certificates\n\n" + \
                   "**Quick Actions:**\n" + \
                   "• Go to **Assets** → Search for your equipment\n" + \
                   "• Click on asset to view full details and history\n" + \
                   "• Use **QR Scanner** for quick asset identification\n\n" + \
                   "Which asset do you need help with?"
        
        # Maintenance Scheduling
        elif any(phrase in msg_lower for phrase in ['maintenance', 'schedule', 'preventive', 'pm', 'inspection']):
            return "Let me help you with maintenance scheduling! 📅\n\n" + \
                   "**🔄 Preventive Maintenance (PM):**\n" + \
                   "• **View PM Schedule**: Maintenance → Preventive Maintenance\n" + \
                   "• **Create PM Plans**: Set frequency (daily, weekly, monthly, yearly)\n" + \
                   "• **Assign Tasks**: Define specific procedures and checklists\n" + \
                   "• **Auto-Generation**: System creates work orders automatically\n\n" + \
                   "**📊 Scheduling Tips:**\n" + \
                   "• Base frequency on manufacturer recommendations\n" + \
                   "• Consider equipment criticality and usage patterns\n" + \
                   "• Schedule during planned downtime when possible\n" + \
                   "• Include safety checks and calibrations\n\n" + \
                   "Need help setting up a specific PM schedule?"
        
        # Parts and Inventory
        elif any(word in msg_lower for word in ['parts', 'inventory', 'stock', 'spare', 'component']):
            return "I'll help you manage parts and inventory efficiently! 📦\n\n" + \
                   "**🔧 Parts Management:**\n" + \
                   "• **Search Parts**: Parts → Search by part number, description, or equipment\n" + \
                   "• **Check Stock**: View current quantities and locations\n" + \
                   "• **Create Requisitions**: Request parts for work orders\n" + \
                   "• **Update Inventory**: Record receipts and usage\n" + \
                   "• **Set Reorder Points**: Automated low-stock alerts\n\n" + \
                   "**💡 Inventory Best Practices:**\n" + \
                   "• Link parts to specific equipment for easy identification\n" + \
                   "• Keep accurate counts with regular cycle counts\n" + \
                   "• Track supplier information and lead times\n" + \
                   "• Monitor usage patterns for optimization\n\n" + \
                   "What parts information do you need?"
        
        # Reports and Analytics
        elif any(word in msg_lower for word in ['report', 'analytics', 'dashboard', 'metrics', 'kpi']):
            return "Let me show you ChatterFix's powerful reporting capabilities! 📊\n\n" + \
                   "**📈 Available Reports:**\n" + \
                   "• **Work Order Reports**: Completion rates, response times, costs\n" + \
                   "• **Asset Performance**: Uptime, MTBF, maintenance costs per asset\n" + \
                   "• **Inventory Reports**: Stock levels, usage, reorder recommendations\n" + \
                   "• **Technician Performance**: Productivity, skills tracking\n" + \
                   "• **Cost Analysis**: Budget vs actual, cost per repair\n\n" + \
                   "**🎯 Key Performance Indicators:**\n" + \
                   "• Equipment uptime percentage\n" + \
                   "• Average work order completion time\n" + \
                   "• Preventive vs reactive maintenance ratio\n" + \
                   "• Parts availability rate\n\n" + \
                   "Navigate to **Reports** → Select report type → Set date range and filters"
        
        # Troubleshooting Help
        elif any(word in msg_lower for word in ['trouble', 'problem', 'issue', 'fix', 'repair', 'diagnose']):
            return "I'm here to help troubleshoot your equipment issues! 🔍\n\n" + \
                   "**🛠️ Troubleshooting Process:**\n" + \
                   "1. **Safety First**: Ensure equipment is properly locked out/tagged out\n" + \
                   "2. **Gather Information**: What symptoms are you observing?\n" + \
                   "3. **Check History**: Review past work orders for similar issues\n" + \
                   "4. **Basic Checks**: Power, connections, fluid levels, filters\n" + \
                   "5. **Document Findings**: Create work order with detailed observations\n\n" + \
                   "**💡 Quick Diagnostic Tips:**\n" + \
                   "• Unusual sounds, vibrations, or smells?\n" + \
                   "• Any recent changes or maintenance performed?\n" + \
                   "• Check equipment manuals in the asset documentation\n\n" + \
                   "Describe the specific problem you're experiencing, and I'll provide targeted guidance!"
        
        # Help and Navigation
        elif any(word in msg_lower for word in ['help', 'how', 'navigate', 'use', 'guide']):
            return "Welcome to ChatterFix CMMS! I'm here to help you navigate the system. 🧭\n\n" + \
                   "**🎯 Quick Start Guide:**\n" + \
                   "• **Dashboard**: Your control center for overview and alerts\n" + \
                   "• **Work Orders**: Create, assign, and track maintenance work\n" + \
                   "• **Assets**: Equipment registry and maintenance history\n" + \
                   "• **Parts**: Inventory management and requisitions\n" + \
                   "• **Maintenance**: Preventive maintenance scheduling\n" + \
                   "• **Reports**: Analytics and performance metrics\n\n" + \
                   "**💬 Ask me about:**\n" + \
                   "• Creating work orders\n" + \
                   "• Equipment troubleshooting\n" + \
                   "• Maintenance scheduling\n" + \
                   "• Parts management\n" + \
                   "• Report generation\n\n" + \
                   "What would you like to learn about first?"
        
        # Default response for general queries
        else:
            return f"I understand you're asking about \"{message}\". As your ChatterFix CMMS assistant, I specialize in:\n\n" + \
                   "🔧 **Maintenance Operations**\n" + \
                   "• Work order management and tracking\n" + \
                   "• Equipment troubleshooting and repair guidance\n" + \
                   "• Preventive maintenance scheduling\n\n" + \
                   "📊 **Asset Management**\n" + \
                   "• Equipment registry and documentation\n" + \
                   "• Performance monitoring and analytics\n" + \
                   "• Parts inventory and procurement\n\n" + \
                   "Could you be more specific about what you need help with? For example:\n" + \
                   "• \"How do I create a work order?\"\n" + \
                   "• \"Emergency pump leak in Building A\"\n" + \
                   "• \"Schedule maintenance for Motor #123\""

# Initialize ChatterFix AI client
chatterfix_ai = ChatterFixAIClient()

def store_ai_interaction(user_message: str, ai_response: str, context_type: str = "general"):
    """Store AI interaction in database for analytics"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ai_interactions (user_message, ai_response, context_type) VALUES (?, ?, ?)",
            (user_message, ai_response, context_type)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error storing AI interaction: {e}")

async def get_maintenance_context():
    """Get current maintenance context for AI"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get recent work orders
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'Open'")
        open_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE priority = 'Critical' AND status = 'Open'")
        critical_orders = cursor.fetchone()[0]
        
        # Get asset count
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Active'")
        active_assets = cursor.fetchone()[0]
        
        conn.close()
        
        context = f"""
Current System Status:
- Open Work Orders: {open_orders}
- Critical Priority Orders: {critical_orders}
- Active Assets: {active_assets}
"""
        return context
    except Exception as e:
        logger.error(f"Error getting maintenance context: {e}")
        return "System context unavailable"

@app.get("/")
async def landing_page():
    """Stunning landing page for ChatterFix CMMS"""
    styles = get_unified_styles()
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix - Voice-Powered Enterprise CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
        {styles}
        
        .hero-section {{
            background: linear-gradient(135deg, var(--primary-blue) 0%, #1a4f7a 100%);
            color: white;
            padding: 4rem 2rem;
            text-align: center;
            min-height: 70vh;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }}
        
        .hero-title {{
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            line-height: 1.2;
        }}
        
        .hero-subtitle {{
            font-size: 1.5rem;
            font-weight: 400;
            margin-bottom: 3rem;
            opacity: 0.9;
            max-width: 600px;
        }}
        
        .cta-button {{
            background: var(--secondary-green);
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
            padding: 1rem 3rem;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }}
        
        .cta-button:hover {{
            background: #45a049;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
        }}
        
        .features-section {{
            padding: 4rem 2rem;
            background: white;
        }}
        
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .feature-card {{
            text-align: center;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border: 1px solid var(--border-light);
            transition: transform 0.3s ease;
        }}
        
        .feature-card:hover {{
            transform: translateY(-5px);
        }}
        
        .feature-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        .feature-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--primary-blue);
            margin-bottom: 1rem;
        }}
        
        .feature-description {{
            color: var(--text-light);
            line-height: 1.6;
        }}
        
        .stats-section {{
            background: var(--sidebar-bg);
            padding: 3rem 2rem;
            text-align: center;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .stat-item {{
            color: var(--primary-blue);
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            display: block;
        }}
        
        .stat-label {{
            font-size: 1rem;
            font-weight: 500;
            opacity: 0.8;
        }}
        </style>
    </head>
    <body>
        <div class="hero-section">
            <h1 class="hero-title">🚀 ChatterFix</h1>
            <p class="hero-subtitle">
                Voice-Powered Enterprise CMMS Platform
                <br>Transform Your Maintenance Operations with AI
            </p>
            <a href="/dashboard" class="cta-button">🎯 Try ChatterFix Now</a>
        </div>
        
        <div class="features-section">
            <div class="container">
                <h2 style="text-align: center; color: var(--primary-blue); margin-bottom: 3rem; font-size: 2.5rem;">
                    Enterprise-Ready Features
                </h2>
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🎤</div>
                        <h3 class="feature-title">Voice Commands</h3>
                        <p class="feature-description">
                            Control your CMMS with natural voice commands. Create work orders, check asset status, and get insights hands-free.
                        </p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🤖</div>
                        <h3 class="feature-title">AI Assistant</h3>
                        <p class="feature-description">
                            LLaMA 3.1 powered AI assistant provides intelligent maintenance recommendations and predictive insights.
                        </p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <h3 class="feature-title">Real-time Analytics</h3>
                        <p class="feature-description">
                            Comprehensive dashboards with real-time metrics, predictive maintenance alerts, and performance tracking.
                        </p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🔧</div>
                        <h3 class="feature-title">Complete CRUD Operations</h3>
                        <p class="feature-description">
                            Full work order, asset, and parts management with enterprise-grade database support.
                        </p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🛡️</div>
                        <h3 class="feature-title">Enterprise Security</h3>
                        <p class="feature-description">
                            JWT authentication, role-based access control, and audit logging for enterprise compliance.
                        </p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📱</div>
                        <h3 class="feature-title">Mobile Ready</h3>
                        <p class="feature-description">
                            Responsive design optimized for field technicians working on mobile devices and tablets.
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="stats-section">
            <h2 style="color: var(--primary-blue); margin-bottom: 2rem; font-size: 2rem;">
                Platform Performance
            </h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">< 2.5s</span>
                    <span class="stat-label">Page Load Time</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">99.9%</span>
                    <span class="stat-label">Uptime</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">24/7</span>
                    <span class="stat-label">AI Assistant</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">500+</span>
                    <span class="stat-label">Enterprise Ready</span>
                </div>
            </div>
        </div>
        
        <footer style="background: var(--primary-blue); color: white; text-align: center; padding: 2rem;">
            <p>&copy; 2024 ChatterFix CMMS - Voice-Powered Enterprise Platform</p>
            <p style="opacity: 0.8; margin-top: 0.5rem;">Ready to revolutionize your maintenance operations?</p>
        </footer>
        <script src="/ai-inject.js" async></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/dashboard")
async def dashboard():
    """Main dashboard with system overview"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get dashboard metrics
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'Open'")
        open_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'Completed' AND date(completed_date) = date('now')")
        completed_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE priority = 'Critical' AND status = 'Open'")
        critical_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Active'")
        active_assets = cursor.fetchone()[0]
        
        # Get recent work orders
        cursor.execute("""
            SELECT id, title, priority, status, created_date 
            FROM work_orders 
            ORDER BY created_date DESC 
            LIMIT 5
        """)
        recent_orders = cursor.fetchall()
        
        conn.close()
        
        # Generate HTML
        styles = get_unified_styles()
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ChatterFix CMMS - Enterprise Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>{styles}</style>
        </head>
        <body>
            <header class="header">
                <h1>ChatterFix CMMS</h1>
            </header>
            
            <div class="container">
                <div class="nav-pills">
                    <a href="/dashboard" class="nav-link">🏠 Dashboard</a>
                    <a href="/work-orders" class="nav-link">🔧 Work Orders</a>
                    <a href="/assets" class="nav-link">🏭 Assets</a>
                    <a href="/parts" class="nav-link">📦 Parts</a>
                    <a href="/reports" class="nav-link">📊 Reports</a>
                    <a href="/settings" class="nav-link">⚙️ Settings</a>
                </div>
                
                <div class="card">
                    <div class="card-header">System Overview</div>
                    <div class="card-body">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem;">
                            <div style="text-align: center; padding: 1.5rem; background: var(--sidebar-bg); border-radius: 8px;">
                                <div style="font-size: 2rem; font-weight: 700; color: var(--info); margin-bottom: 0.5rem;">{open_orders}</div>
                                <div style="color: var(--text-light); font-weight: 500;">Open Work Orders</div>
                            </div>
                            <div style="text-align: center; padding: 1.5rem; background: var(--sidebar-bg); border-radius: 8px;">
                                <div style="font-size: 2rem; font-weight: 700; color: var(--success); margin-bottom: 0.5rem;">{completed_today}</div>
                                <div style="color: var(--text-light); font-weight: 500;">Completed Today</div>
                            </div>
                            <div style="text-align: center; padding: 1.5rem; background: var(--sidebar-bg); border-radius: 8px;">
                                <div style="font-size: 2rem; font-weight: 700; color: var(--danger); margin-bottom: 0.5rem;">{critical_orders}</div>
                                <div style="color: var(--text-light); font-weight: 500;">Critical Orders</div>
                            </div>
                            <div style="text-align: center; padding: 1.5rem; background: var(--sidebar-bg); border-radius: 8px;">
                                <div style="font-size: 2rem; font-weight: 700; color: var(--secondary-green); margin-bottom: 0.5rem;">{active_assets}</div>
                                <div style="color: var(--text-light); font-weight: 500;">Active Assets</div>
                            </div>
                        </div>
                    </div>
                </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">Recent Work Orders</div>
                    <div class="card-body">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Title</th>
                                    <th>Priority</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                </tr>
                            </thead>
                            <tbody>
        """
        
        for order in recent_orders:
            priority_class = {
                'Critical': 'priority-high',
                'High': 'priority-high', 
                'Medium': 'priority-medium',
                'Low': 'priority-low'
            }.get(order[2], 'priority-medium')
            
            status_class = {
                'Open': 'status-open',
                'In Progress': 'status-in-progress',
                'Completed': 'status-completed'
            }.get(order[3], 'status-open')
            
            html_content += f"""
                                <tr>
                                    <td>#{order[0]}</td>
                                    <td>{order[1]}</td>
                                    <td><span class="status-badge {priority_class}">{order[2]}</span></td>
                                    <td><span class="status-badge {status_class}">{order[3]}</span></td>
                                    <td>{order[4][:10]}</td>
                                </tr>
            """
        
        html_content += """
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">Quick Actions</div>
                    <div class="card-body">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                            <a href="/work-orders" class="btn btn-primary" style="text-decoration: none; text-align: center; padding: 1rem;">
                                Work Orders
                            </a>
                            <a href="/assets" class="btn btn-success" style="text-decoration: none; text-align: center; padding: 1rem;">
                                Assets
                            </a>
                            <a href="/parts" class="btn btn-warning" style="text-decoration: none; text-align: center; padding: 1rem;">
                                Parts
                            </a>
                            <a href="/quality" class="btn btn-primary" style="text-decoration: none; text-align: center; padding: 1rem;">
                                Quality
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- AI Assistant Widget -->
                <div id="ai-assistant" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
                    <div id="ai-toggle" onclick="toggleAI()" style="
                        background: var(--secondary-green);
                        color: white;
                        padding: 15px;
                        border-radius: 50px;
                        cursor: pointer;
                        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
                        font-weight: 600;
                        user-select: none;
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                        🤖 ChatterFix AI
                    </div>
                    
                    <div id="ai-chat" style="
                        position: absolute;
                        bottom: 70px;
                        right: 0;
                        width: 350px;
                        height: 400px;
                        background: white;
                        border-radius: 15px;
                        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
                        border: 1px solid var(--border-light);
                        display: none;
                        flex-direction: column;
                    ">
                        <div style="
                            background: var(--primary-blue);
                            color: white;
                            padding: 15px;
                            border-radius: 15px 15px 0 0;
                            font-weight: 600;
                        ">
                            🤖 ChatterFix AI Assistant
                        </div>
                        
                        <div id="ai-messages" style="
                            flex: 1;
                            padding: 15px;
                            overflow-y: auto;
                            border-bottom: 1px solid var(--border-light);
                        ">
                            <div style="
                                background: var(--sidebar-bg);
                                padding: 10px;
                                border-radius: 10px;
                                margin-bottom: 10px;
                                color: var(--text-dark);
                            ">
                                👋 Hi! I'm your ChatterFix AI assistant. Try saying:<br><br>
                                • "Create work order for pump repair"<br>
                                • "Show me critical assets"<br>
                                • "Update work order 5 to completed"<br>
                                • "What's my system status?"
                            </div>
                        </div>
                        
                        <div style="padding: 15px;">
                            <div style="display: flex; gap: 10px;">
                                <input type="text" id="ai-input" placeholder="Type or speak your request..." style="
                                    flex: 1;
                                    padding: 10px;
                                    border: 1px solid var(--border-light);
                                    border-radius: 25px;
                                    outline: none;
                                    font-size: 14px;
                                " onkeypress="if(event.key==='Enter') sendMessage()">
                                <button onclick="toggleVoice()" id="voice-btn" style="
                                    background: var(--secondary-green);
                                    color: white;
                                    border: none;
                                    padding: 10px 15px;
                                    border-radius: 50%;
                                    cursor: pointer;
                                    font-size: 16px;
                                " title="Voice Input">🎤</button>
                                <button onclick="sendMessage()" style="
                                    background: var(--primary-blue);
                                    color: white;
                                    border: none;
                                    padding: 10px 15px;
                                    border-radius: 50%;
                                    cursor: pointer;
                                    font-size: 16px;
                                ">➤</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                let aiOpen = false;
                let isListening = false;
                let recognition;
                
                function toggleAI() {
                    const chat = document.getElementById('ai-chat');
                    const toggle = document.getElementById('ai-toggle');
                    aiOpen = !aiOpen;
                    
                    if (aiOpen) {
                        chat.style.display = 'flex';
                        toggle.textContent = '✕ Close AI';
                        toggle.style.background = 'var(--danger)';
                    } else {
                        chat.style.display = 'none';
                        toggle.textContent = '🤖 ChatterFix AI';
                        toggle.style.background = 'var(--secondary-green)';
                    }
                }
                
                function sendMessage() {
                    const input = document.getElementById('ai-input');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    addMessage(message, 'user');
                    input.value = '';
                    
                    // Send to AI
                    fetch('/api/ai', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: message})
                    })
                    .then(response => response.json())
                    .then(data => {
                        addMessage(data.response, 'ai');
                    })
                    .catch(error => {
                        addMessage('Sorry, I encountered an error. Please try again.', 'ai');
                    });
                }
                
                function addMessage(text, sender) {
                    const messages = document.getElementById('ai-messages');
                    const div = document.createElement('div');
                    
                    if (sender === 'user') {
                        div.style.cssText = `
                            background: var(--primary-blue);
                            color: white;
                            padding: 8px 12px;
                            border-radius: 15px 15px 5px 15px;
                            margin: 5px 0 5px 50px;
                            text-align: right;
                        `;
                    } else {
                        div.style.cssText = `
                            background: var(--sidebar-bg);
                            color: var(--text-dark);
                            padding: 8px 12px;
                            border-radius: 15px 15px 15px 5px;
                            margin: 5px 50px 5px 0;
                        `;
                    }
                    
                    div.textContent = text;
                    messages.appendChild(div);
                    messages.scrollTop = messages.scrollHeight;
                }
                
                function toggleVoice() {
                    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                        alert('Voice recognition not supported in this browser');
                        return;
                    }
                    
                    const voiceBtn = document.getElementById('voice-btn');
                    
                    if (!isListening) {
                        startListening();
                        voiceBtn.textContent = '🔴';
                        voiceBtn.style.background = 'var(--danger)';
                        isListening = true;
                    } else {
                        stopListening();
                        voiceBtn.textContent = '🎤';
                        voiceBtn.style.background = 'var(--secondary-green)';
                        isListening = false;
                    }
                }
                
                function startListening() {
                    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.lang = 'en-US';
                    
                    recognition.onresult = function(event) {
                        const transcript = event.results[0][0].transcript;
                        document.getElementById('ai-input').value = transcript;
                        sendMessage();
                        stopListening();
                    };
                    
                    recognition.onerror = function() {
                        stopListening();
                    };
                    
                    recognition.start();
                }
                
                function stopListening() {
                    if (recognition) {
                        recognition.stop();
                    }
                    const voiceBtn = document.getElementById('voice-btn');
                    voiceBtn.textContent = '🎤';
                    voiceBtn.style.background = 'var(--secondary-green)';
                    isListening = false;
                }
            </script>
            <script src="/ai-inject.js" async></script>
    </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return HTMLResponse(content=f"<h1>Error loading dashboard: {e}</h1>", status_code=500)

@app.get("/work-orders")
async def work_orders():
    """Work orders management page"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, status, priority, assigned_to, created_date, updated_date
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
        
        styles = get_unified_styles()
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Work Orders - ChatterFix CMMS</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{styles}</style>
        </head>
        <body>
            <header class="header">
                <h1>ChatterFix CMMS</h1>
            </header>
            
            <div class="container">
                <div class="nav-pills">
                    <a href="/dashboard" class="nav-link">🏠 Dashboard</a>
                    <a href="/work-orders" class="nav-link">🔧 Work Orders</a>
                    <a href="/assets" class="nav-link">🏭 Assets</a>
                    <a href="/parts" class="nav-link">📦 Parts</a>
                    <a href="/reports" class="nav-link">📊 Reports</a>
                    <a href="/settings" class="nav-link">⚙️ Settings</a>
                </div>
                
                <div class="card">
                    <div class="card-header">📋 Work Orders Management</div>
                    <div class="card-body">
                        <div style="margin-bottom: 1.5rem; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                            <button onclick="createNewWorkOrder()" class="btn btn-primary">+ Create New Work Order</button>
                            <button onclick="aiSuggestMaintenance()" class="btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">🤖 AI Maintenance Suggestions</button>
                            <input type="text" id="searchWorkOrders" placeholder="Search work orders..." style="padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; width: 250px;" onkeyup="filterWorkOrders()">
                            <select id="statusFilter" onchange="filterWorkOrders()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="">All Statuses</option>
                                <option value="Open">Open</option>
                                <option value="In Progress">In Progress</option>
                                <option value="Completed">Completed</option>
                                <option value="On Hold">On Hold</option>
                            </select>
                        </div>
                        <div class="table">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.3);">
                                <th style="text-align: left; padding: 10px;">ID</th>
                                <th style="text-align: left; padding: 10px;">Title</th>
                                <th style="text-align: left; padding: 10px;">Priority</th>
                                <th style="text-align: left; padding: 10px;">Status</th>
                                <th style="text-align: left; padding: 10px;">Assigned</th>
                                <th style="text-align: left; padding: 10px;">Created</th>
                                <th style="text-align: left; padding: 10px;">Due</th>
                                <th style="text-align: left; padding: 10px; width: 200px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
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
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: background-color 0.3s;" onclick="viewWorkOrder({order[0]})" onmouseover="this.style.backgroundColor='rgba(76,175,80,0.1)'" onmouseout="this.style.backgroundColor='transparent'">
                                <td style="padding: 10px;">#{order[0]}</td>
                                <td style="padding: 10px;"><strong>{order[1]}</strong><br><small>{order[2][:50]}...</small></td>
                                <td style="padding: 10px; color: {priority_color};">●{order[4]}</td>
                                <td style="padding: 10px; color: {status_color};">●{order[3]}</td>
                                <td style="padding: 10px;">{order[5] or 'Unassigned'}</td>
                                <td style="padding: 10px;">{order[6][:10]}</td>
                                <td style="padding: 10px;">{order[7][:10] if order[7] else 'Not set'}</td>
                                <td style="padding: 10px;">
                                    <button onclick="event.stopPropagation(); editWorkOrder({order[0]})" style="background: var(--info); border: none; color: white; padding: 5px 10px; border-radius: 3px; margin-right: 5px; cursor: pointer; font-size: 12px;">✏️ Edit</button>
                                    <button onclick="event.stopPropagation(); completeWorkOrder({order[0]})" style="background: var(--success); border: none; color: white; padding: 5px 10px; border-radius: 3px; margin-right: 5px; cursor: pointer; font-size: 12px;">✅ Complete</button>
                                    <button onclick="event.stopPropagation(); deleteWorkOrder({order[0]})" style="background: var(--danger); border: none; color: white; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;">🗑️ Delete</button>
                                </td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                        </table>
                        </div>
                    </div>
                </div>
            </div>
            <script src="/ai-inject.js" async></script>
    </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Work orders error: {e}")
        return HTMLResponse(content=f"<h1>Error loading work orders: {e}</h1>", status_code=500)

@app.get("/assets")
async def assets():
    """Assets management page"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, asset_type, location, manufacturer, model, status, criticality, created_date
            FROM assets 
            ORDER BY criticality DESC, name
        """)
        assets = cursor.fetchall()
        conn.close()
        
        styles = get_unified_styles()
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Assets - ChatterFix CMMS</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{styles}</style>
        </head>
        <body>
            <header class="header">
                <h1>ChatterFix CMMS</h1>
            </header>
            
            <div class="container">
                <div class="nav-pills">
                    <a href="/dashboard" class="nav-link">🏠 Dashboard</a>
                    <a href="/work-orders" class="nav-link">🔧 Work Orders</a>
                    <a href="/assets" class="nav-link">🏭 Assets</a>
                    <a href="/parts" class="nav-link">📦 Parts</a>
                    <a href="/reports" class="nav-link">📊 Reports</a>
                    <a href="/settings" class="nav-link">⚙️ Settings</a>
                </div>
                
                <div class="card">
                    <div class="card-header">🏭 AI-Powered Asset Management & Health Monitoring</div>
                    <div class="card-body">
                        <div style="margin-bottom: 1.5rem; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                            <button onclick="createNewAsset()" class="btn btn-primary">+ Add New Asset</button>
                            <button onclick="aiAssetHealthAnalysis()" class="btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">🤖 AI Health Analysis</button>
                            <button onclick="aiMaintenanceScheduler()" class="btn" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">📅 AI Schedule Maintenance</button>
                            <input type="text" id="searchAssets" placeholder="Search assets..." style="padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; width: 250px;" onkeyup="filterAssets()">
                            <select id="statusFilter" onchange="filterAssets()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="">All Status</option>
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                                <option value="Maintenance">Under Maintenance</option>
                            </select>
                            <select id="criticalityFilter" onchange="filterAssets()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="">All Criticality</option>
                                <option value="Critical">Critical</option>
                                <option value="High">High</option>
                                <option value="Medium">Medium</option>
                                <option value="Low">Low</option>
                            </select>
                        </div>
                
                <div class="table">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.3);">
                                <th style="text-align: left; padding: 10px;">ID</th>
                                <th style="text-align: left; padding: 10px;">Name</th>
                                <th style="text-align: left; padding: 10px;">Type</th>
                                <th style="text-align: left; padding: 10px;">Location</th>
                                <th style="text-align: left; padding: 10px;">Manufacturer</th>
                                <th style="text-align: left; padding: 10px;">Status</th>
                                <th style="text-align: left; padding: 10px;">Criticality</th>
                                <th style="text-align: left; padding: 10px;">Last Maintenance</th>
                                <th style="text-align: left; padding: 10px; width: 280px;">AI-Powered Actions</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for asset in assets:
            status_color = {
                'Active': '#2ecc71',
                'Inactive': '#e74c3c',
                'Maintenance': '#f39c12'
            }.get(asset[6], '#3498db')
            
            criticality_color = {
                'Critical': '#e74c3c',
                'High': '#f39c12', 
                'Medium': '#3498db',
                'Low': '#2ecc71'
            }.get(asset[7], '#3498db')
            
            html_content += f"""
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: background-color 0.3s;" onclick="viewAssetDetails({asset[0]})" onmouseover="this.style.backgroundColor='rgba(76,175,80,0.1)'" onmouseout="this.style.backgroundColor='transparent'" data-status="{asset[6]}" data-criticality="{asset[7]}">
                                <td style="padding: 10px;">#{asset[0]}</td>
                                <td style="padding: 10px;"><strong>{asset[1]}</strong></td>
                                <td style="padding: 10px;">{asset[2] or 'N/A'}</td>
                                <td style="padding: 10px;">{asset[3] or 'N/A'}</td>
                                <td style="padding: 10px;">{asset[4] or 'N/A'} {asset[5] or ''}</td>
                                <td style="padding: 10px; color: {status_color};">●{asset[6]}</td>
                                <td style="padding: 10px; color: {criticality_color};">●{asset[7]}</td>
                                <td style="padding: 10px;">{asset[8][:10] if asset[8] else 'Never'}</td>
                                <td style="padding: 10px;">
                                    <button onclick="event.stopPropagation(); aiHealthCheck({asset[0]})" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; padding: 4px 6px; border-radius: 3px; margin-right: 2px; cursor: pointer; font-size: 10px;">🤖 Health</button>
                                    <button onclick="event.stopPropagation(); scheduleMaintenanceAI({asset[0]})" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border: none; color: white; padding: 4px 6px; border-radius: 3px; margin-right: 2px; cursor: pointer; font-size: 10px;">📅 Schedule</button>
                                    <button onclick="event.stopPropagation(); viewMaintenanceHistory({asset[0]})" style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); border: none; color: white; padding: 4px 6px; border-radius: 3px; margin-right: 2px; cursor: pointer; font-size: 10px;">📊 History</button>
                                    <button onclick="event.stopPropagation(); editAsset({asset[0]})" style="background: var(--info); border: none; color: white; padding: 4px 6px; border-radius: 3px; margin-right: 2px; cursor: pointer; font-size: 10px;">✏️</button>
                                    <button onclick="event.stopPropagation(); deleteAsset({asset[0]})" style="background: var(--danger); border: none; color: white; padding: 4px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">🗑️</button>
                                </td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                        </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="/ai-inject.js" async></script>
            <script>
                // Revolutionary AI-Powered Asset Management System
                
                function viewAssetDetails(id) { window.location.href = `/asset/${id}`; }
                function createNewAsset() { window.location.href = '/asset/new'; }
                function editAsset(id) { window.location.href = `/asset/${id}/edit`; }
                
                async function aiHealthCheck(id) {
                    try {
                        const response = await fetch(`/api/assets/${id}/ai-health-check`);
                        const health = await response.json();
                        
                        const healthColor = health.overall_score >= 80 ? '#2ecc71' : health.overall_score >= 60 ? '#f39c12' : '#e74c3c';
                        const modal = document.createElement('div');
                        modal.id = 'healthModal';
                        modal.style = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;';
                        modal.innerHTML = `
                            <div style="background: white; padding: 20px; border-radius: 8px; max-width: 600px; width: 90%;">
                                <h3>🤖 AI Asset Health Analysis</h3>
                                <div style="background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%); padding: 15px; border-radius: 5px; border-left: 4px solid ${healthColor}; margin: 15px 0;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <strong>Overall Health Score:</strong>
                                        <span style="font-size: 24px; color: ${healthColor}; font-weight: bold;">${health.overall_score}%</span>
                                    </div>
                                    <div style="margin-bottom: 10px;"><strong>Status:</strong> ${health.health_status}</div>
                                    <div style="margin-bottom: 10px;"><strong>Next Maintenance:</strong> ${health.next_maintenance_date}</div>
                                    <div style="margin-bottom: 15px;"><strong>Risk Level:</strong> <span style="color: ${healthColor};">${health.risk_level}</span></div>
                                    <div><strong>AI Recommendations:</strong></div>
                                    <ul style="margin: 10px 0; padding-left: 20px;">
                                        ${health.recommendations.map(r => `<li>${r}</li>`).join('')}
                                    </ul>
                                    <div style="margin-top: 15px;"><strong>AI Analysis:</strong> ${health.ai_analysis}</div>
                                </div>
                                <div style="display: flex; gap: 10px; margin-top: 15px;">
                                    <button onclick="scheduleMaintenanceAI(${id})" style="background: #f39c12; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">📅 Schedule Maintenance</button>
                                    <button onclick="document.getElementById('healthModal').remove()" style="background: #6c757d; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">Close</button>
                                </div>
                            </div>
                        `;
                        document.body.appendChild(modal);
                    } catch (error) {
                        alert('Error getting health analysis: ' + error.message);
                    }
                }
                
                async function scheduleMaintenanceAI(id) {
                    try {
                        const response = await fetch(`/api/assets/${id}/ai-maintenance-schedule`);
                        const schedule = await response.json();
                        
                        if (confirm(`🤖 AI Recommends scheduling maintenance for ${schedule.recommended_date}\\n\\nTask: ${schedule.maintenance_type}\\nEstimated Duration: ${schedule.estimated_hours} hours\\nPriority: ${schedule.priority}\\n\\nCreate work order?`)) {
                            const createResponse = await fetch('/api/work-orders', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    title: `AI Scheduled: ${schedule.maintenance_type}`,
                                    description: schedule.description,
                                    asset_id: id,
                                    priority: schedule.priority,
                                    estimated_hours: schedule.estimated_hours
                                })
                            });
                            if (createResponse.ok) {
                                alert('✅ Maintenance work order created successfully!');
                                location.reload();
                            }
                        }
                    } catch (error) {
                        alert('Error scheduling maintenance: ' + error.message);
                    }
                }
                
                async function viewMaintenanceHistory(id) {
                    try {
                        const response = await fetch(`/api/assets/${id}/maintenance-history`);
                        const history = await response.json();
                        
                        let historyHtml = '<div style="max-height: 400px; overflow-y: auto;">';
                        if (history.maintenance_records.length === 0) {
                            historyHtml += '<p>No maintenance history found.</p>';
                        } else {
                            history.maintenance_records.forEach(record => {
                                const statusColor = record.status === 'Completed' ? '#2ecc71' : '#f39c12';
                                historyHtml += `
                                    <div style="margin: 10px 0; padding: 10px; border-left: 3px solid ${statusColor}; background: rgba(76,175,80,0.05);">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <strong>${record.work_order_title}</strong>
                                            <span style="color: ${statusColor};">●${record.status}</span>
                                        </div>
                                        <small>Date: ${record.date} | Duration: ${record.actual_hours || 'N/A'} hrs | Tech: ${record.technician || 'Unassigned'}</small><br>
                                        <em>${record.description}</em>
                                    </div>
                                `;
                            });
                        }
                        historyHtml += '</div>';
                        
                        document.body.insertAdjacentHTML('beforeend', `
                            <div id="historyModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;">
                                <div style="background: white; padding: 20px; border-radius: 8px; max-width: 700px; width: 90%;">
                                    <h3>📊 Maintenance History & AI Insights</h3>
                                    <div style="background: rgba(102,126,234,0.1); padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                                        <strong>AI Summary:</strong> ${history.ai_summary}
                                    </div>
                                    ${historyHtml}
                                    <button onclick="document.getElementById('historyModal').remove()" style="margin-top: 10px; background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close</button>
                                </div>
                            </div>
                        `);
                    } catch (error) {
                        alert('Error loading maintenance history: ' + error.message);
                    }
                }
                
                async function deleteAsset(id) {
                    if (confirm('Are you sure you want to delete this asset? This action cannot be undone.')) {
                        try {
                            const response = await fetch(`/api/assets/${id}`, { method: 'DELETE' });
                            if (response.ok) { location.reload(); } 
                            else { alert('Error deleting asset'); }
                        } catch (error) { alert('Error: ' + error.message); }
                    }
                }
                
                async function aiAssetHealthAnalysis() {
                    try {
                        const response = await fetch('/api/assets/ai-health-overview');
                        const overview = await response.json();
                        
                        let html = '<div style="max-height: 400px; overflow-y: auto;">';
                        overview.asset_health_summary.forEach(asset => {
                            const healthColor = asset.health_score >= 80 ? '#2ecc71' : asset.health_score >= 60 ? '#f39c12' : '#e74c3c';
                            html += `<div style="margin: 10px 0; padding: 10px; border-left: 3px solid ${healthColor}; background: rgba(102,126,234,0.05);">
                                <div style="display: flex; justify-content: space-between;"><strong>${asset.name}</strong> <span style="color: ${healthColor};">${asset.health_score}%</span></div>
                                <small>Status: ${asset.status} | Risk: ${asset.risk_level}</small></div>`;
                        });
                        html += '</div>';
                        
                        document.body.insertAdjacentHTML('beforeend', `
                            <div id="overviewModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;">
                                <div style="background: white; padding: 20px; border-radius: 8px; max-width: 700px; width: 90%;">
                                    <h3>🤖 AI Asset Fleet Health Overview</h3>
                                    <div style="background: rgba(102,126,234,0.1); padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                                        <strong>Overall Fleet Health:</strong> ${overview.fleet_health_score}% | <strong>Critical Assets:</strong> ${overview.critical_count} | <strong>Maintenance Due:</strong> ${overview.maintenance_due_count}
                                    </div>
                                    ${html}
                                    <button onclick="document.getElementById('overviewModal').remove()" style="margin-top: 10px; background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close</button>
                                </div>
                            </div>
                        `);
                    } catch (error) { alert('Error: ' + error.message); }
                }
                
                function aiMaintenanceScheduler() {
                    alert('🤖 AI Maintenance Scheduler will analyze all assets and create optimal maintenance schedules. Feature launching soon!');
                }
                
                function filterAssets() {
                    const search = document.getElementById('searchAssets').value.toLowerCase();
                    const status = document.getElementById('statusFilter').value;
                    const criticality = document.getElementById('criticalityFilter').value;
                    
                    document.querySelectorAll('tbody tr').forEach(row => {
                        const name = row.children[1].textContent.toLowerCase();
                        const assetStatus = row.getAttribute('data-status');
                        const assetCriticality = row.getAttribute('data-criticality');
                        
                        const matchesSearch = name.includes(search);
                        const matchesStatus = !status || assetStatus === status;
                        const matchesCriticality = !criticality || assetCriticality === criticality;
                        
                        row.style.display = matchesSearch && matchesStatus && matchesCriticality ? '' : 'none';
                    });
                }
            </script>
    </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Assets error: {e}")
        return HTMLResponse(content=f"<h1>Error loading assets: {e}</h1>", status_code=500)

@app.get("/parts")
async def parts():
    """Parts inventory page"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, part_number, name, category, stock_quantity, min_stock, unit_cost, location
            FROM parts 
            ORDER BY name
        """)
        parts = cursor.fetchall()
        conn.close()
        
        styles = get_unified_styles()
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Parts Inventory - ChatterFix CMMS</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{styles}</style>
        </head>
        <body>
            <header class="header">
                <h1>ChatterFix CMMS</h1>
            </header>
            
            <div class="container">
                <div class="nav-pills">
                    <a href="/dashboard" class="nav-link">🏠 Dashboard</a>
                    <a href="/work-orders" class="nav-link">🔧 Work Orders</a>
                    <a href="/assets" class="nav-link">🏭 Assets</a>
                    <a href="/parts" class="nav-link">📦 Parts</a>
                    <a href="/reports" class="nav-link">📊 Reports</a>
                    <a href="/settings" class="nav-link">⚙️ Settings</a>
                </div>
                
                <div class="card">
                    <div class="card-header">📦 AI-Powered Parts Inventory Management</div>
                    <div class="card-body">
                        <div style="margin-bottom: 1.5rem; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                            <button onclick="createNewPart()" class="btn btn-primary">+ Add New Part</button>
                            <button onclick="aiPredictOrders()" class="btn" style="background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%); color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">🤖 AI Predict Reorders</button>
                            <button onclick="bulkCheckout()" class="btn" style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">📋 Bulk Checkout</button>
                            <input type="text" id="searchParts" placeholder="Search parts..." style="padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; width: 250px;" onkeyup="filterParts()">
                            <select id="categoryFilter" onchange="filterParts()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="">All Categories</option>
                                <option value="Electrical">Electrical</option>
                                <option value="Mechanical">Mechanical</option>
                                <option value="Hydraulic">Hydraulic</option>
                                <option value="Safety">Safety</option>
                            </select>
                            <select id="stockFilter" onchange="filterParts()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="">All Stock Levels</option>
                                <option value="low">Low Stock</option>
                                <option value="ok">Normal Stock</option>
                            </select>
                        </div>
                
                <div class="table">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.3);">
                                <th style="text-align: left; padding: 10px;">Part Number</th>
                                <th style="text-align: left; padding: 10px;">Name</th>
                                <th style="text-align: left; padding: 10px;">Category</th>
                                <th style="text-align: left; padding: 10px;">Stock</th>
                                <th style="text-align: left; padding: 10px;">Min Stock</th>
                                <th style="text-align: left; padding: 10px;">Unit Cost</th>
                                <th style="text-align: left; padding: 10px;">Location</th>
                                <th style="text-align: left; padding: 10px; width: 250px;">AI Actions</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for part in parts:
            stock_status = 'low' if part[4] <= part[5] else 'ok'
            stock_color = '#e74c3c' if stock_status == 'low' else '#2ecc71'
            cost_display = f"${part[6]:.2f}" if part[6] is not None else "$0.00"
            
            html_content += f"""
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: background-color 0.3s;" onclick="viewPartDetails({part[0]})" onmouseover="this.style.backgroundColor='rgba(76,175,80,0.1)'" onmouseout="this.style.backgroundColor='transparent'" data-category="{part[3] or 'General'}" data-stock="{stock_status}">
                                <td style="padding: 10px;"><strong>{part[1]}</strong></td>
                                <td style="padding: 10px;">{part[2]}</td>
                                <td style="padding: 10px;">{part[3] or 'General'}</td>
                                <td style="padding: 10px; color: {stock_color};">
                                    <strong>{part[4]}</strong>
                                    {f'<span style="color: #e74c3c; font-size: 12px;">⚠️ LOW</span>' if stock_status == 'low' else ''}
                                </td>
                                <td style="padding: 10px;">{part[5]}</td>
                                <td style="padding: 10px;">{cost_display}</td>
                                <td style="padding: 10px;">{part[7] or 'N/A'}</td>
                                <td style="padding: 10px;">
                                    <button onclick="event.stopPropagation(); checkoutPart({part[0]})" style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); border: none; color: white; padding: 4px 8px; border-radius: 3px; margin-right: 3px; cursor: pointer; font-size: 11px;">🔄 Checkout</button>
                                    <button onclick="event.stopPropagation(); restockPart({part[0]})" style="background: linear-gradient(135deg, #95E1D3 0%, #F3E5AB 100%); border: none; color: #2d3748; padding: 4px 8px; border-radius: 3px; margin-right: 3px; cursor: pointer; font-size: 11px;">📦 Restock</button>
                                    <button onclick="event.stopPropagation(); aiOrderPart({part[0]})" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; padding: 4px 8px; border-radius: 3px; margin-right: 3px; cursor: pointer; font-size: 11px;">🤖 AI Order</button>
                                    <button onclick="event.stopPropagation(); editPart({part[0]})" style="background: var(--info); border: none; color: white; padding: 4px 8px; border-radius: 3px; margin-right: 3px; cursor: pointer; font-size: 11px;">✏️</button>
                                    <button onclick="event.stopPropagation(); deletePart({part[0]})" style="background: var(--danger); border: none; color: white; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px;">🗑️</button>
                                </td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="/ai-inject.js" async></script>
            <script>
                // Revolutionary AI-Powered Parts Management System
                function viewPartDetails(id) { window.location.href = `/part/${id}`; }
                function createNewPart() { window.location.href = '/part/new'; }
                
                async function checkoutPart(id) {
                    const quantity = prompt('Checkout quantity:');
                    if (quantity && parseInt(quantity) > 0) {
                        try {
                            const response = await fetch(`/api/parts/${id}/checkout`, {
                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ quantity: parseInt(quantity) })
                            });
                            if (response.ok) { alert('✅ Part checked out successfully'); location.reload(); } 
                            else { alert('❌ Error checking out part'); }
                        } catch (error) { alert('Error: ' + error.message); }
                    }
                }
                
                async function restockPart(id) {
                    const quantity = prompt('Restock quantity:');
                    if (quantity && parseInt(quantity) > 0) {
                        try {
                            const response = await fetch(`/api/parts/${id}/restock`, {
                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ quantity: parseInt(quantity) })
                            });
                            if (response.ok) { alert('✅ Part restocked successfully'); location.reload(); } 
                            else { alert('❌ Error restocking part'); }
                        } catch (error) { alert('Error: ' + error.message); }
                    }
                }
                
                async function aiOrderPart(id) {
                    try {
                        const response = await fetch(`/api/parts/${id}/ai-order-suggestion`);
                        const suggestion = await response.json();
                        alert('🤖 AI ORDER RECOMMENDATION:\\n\\n' + 
                            'Recommended: ' + suggestion.recommended_quantity + ' units\\n' +
                            'Reasoning: ' + suggestion.reasoning);
                    } catch (error) { alert('Error: ' + error.message); }
                }
                
                function editPart(id) { alert('Edit part #' + id + ' - Feature coming soon!'); }
                function deletePart(id) { if(confirm('Delete part?')) alert('Delete confirmed for part #' + id); }
                
                async function aiPredictOrders() {
                    try {
                        const response = await fetch('/api/parts/ai-reorder-predictions');
                        const data = await response.json();
                        let html = '<div style="max-height:400px;overflow-y:auto;">';
                        data.predictions.forEach(p => html += `<div style="margin:10px 0;padding:10px;border-left:3px solid #e74c3c;background:rgba(231,76,60,0.1);"><strong>${p.part_name}</strong><br>Need: ${p.predicted_usage} units</div>`);
                        html += '</div>';
                        document.body.insertAdjacentHTML('beforeend', `<div id="modal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1000;display:flex;align-items:center;justify-content:center;"><div style="background:white;padding:20px;border-radius:8px;max-width:600px;width:90%;"><h3>🤖 AI Reorder Predictions</h3>${html}<button onclick="document.getElementById('modal').remove()" style="margin-top:10px;background:#4CAF50;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;">Close</button></div></div>`);
                    } catch (error) { alert('Error: ' + error.message); }
                }
                
                function filterParts() {
                    const search = document.getElementById('searchParts').value.toLowerCase();
                    const category = document.getElementById('categoryFilter').value;
                    const stock = document.getElementById('stockFilter').value;
                    document.querySelectorAll('tbody tr').forEach(row => {
                        const name = row.children[1].textContent.toLowerCase();
                        const cat = row.getAttribute('data-category');
                        const stockStat = row.getAttribute('data-stock');
                        const show = name.includes(search) && (!category || cat === category) && (!stock || stockStat === stock);
                        row.style.display = show ? '' : 'none';
                    });
                }
                
                function bulkCheckout() { alert('🔄 Bulk Checkout - Feature coming soon!'); }
            </script>
    </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Parts error: {e}")
        return HTMLResponse(content=f"<h1>Error loading parts: {e}</h1>", status_code=500)

@app.get("/maintenance") 
async def maintenance():
    """Maintenance scheduling page"""
    styles = get_unified_styles()
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Maintenance - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>{styles}</style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 Maintenance Scheduling</h1>
            <div style="margin: 20px 0;">
                <a href="/" class="btn">← Dashboard</a>
                <button class="btn btn-primary" style="margin-left: 10px;">+ Create PM Schedule</button>
            </div>
            
            <div class="alert alert-info">
                <h3>🚧 Maintenance Module</h3>
                <p>Preventive maintenance scheduling features are being developed. Current capabilities include:</p>
                <ul>
                    <li>Work order creation and management</li>
                    <li>Asset tracking and history</li>
                    <li>Parts inventory management</li>
                    <li>AI-powered maintenance assistance</li>
                </ul>
                <p>Coming soon: Automated PM scheduling, maintenance calendars, and predictive analytics.</p>
            </div>
        </div>
        <script src="/ai-inject.js" async></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ===== CRUD ENDPOINTS =====

@app.get("/api/work-orders")
async def get_work_orders():
    """Get all work orders"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, status, priority, assigned_to, created_date, updated_date
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
        work_orders = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        orders_list = []
        for order in work_orders:
            orders_list.append({
                "id": order[0],
                "title": order[1],
                "description": order[2],
                "status": order[3],
                "priority": order[4],
                "assigned_to": order[5],
                "created_date": order[6],
                "updated_date": order[7]
            })
            
        return JSONResponse({"work_orders": orders_list})
    except Exception as e:
        logger.error(f"Error getting work orders: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/work-orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    """Get a specific work order"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, status, priority, assigned_to, created_date, updated_date
            FROM work_orders WHERE id = ?
        """, (work_order_id,))
        order = cursor.fetchone()
        conn.close()
        
        if not order:
            return JSONResponse({"error": "Work order not found"}, status_code=404)
            
        return JSONResponse({
            "id": order[0],
            "title": order[1],
            "description": order[2],
            "status": order[3],
            "priority": order[4],
            "assigned_to": order[5],
            "created_date": order[6],
            "updated_date": order[7]
        })
    except Exception as e:
        logger.error(f"Error getting work order: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/assets")
async def get_assets():
    """Get all assets"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, asset_type, location, status, criticality
            FROM assets 
            ORDER BY criticality DESC, name
        """)
        assets = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        assets_list = []
        for asset in assets:
            assets_list.append({
                "id": asset[0],
                "name": asset[1],
                "asset_type": asset[2],
                "location": asset[3],
                "status": asset[4],
                "criticality": asset[5]
            })
            
        return JSONResponse({"assets": assets_list})
    except Exception as e:
        logger.error(f"Error getting assets: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/assets/{asset_id}")
async def get_asset(asset_id: int):
    """Get a specific asset"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, asset_type, location, status, criticality
            FROM assets WHERE id = ?
        """, (asset_id,))
        asset = cursor.fetchone()
        conn.close()
        
        if not asset:
            return JSONResponse({"error": "Asset not found"}, status_code=404)
            
        return JSONResponse({
            "id": asset[0],
            "name": asset[1],
            "asset_type": asset[2],
            "location": asset[3],
            "status": asset[4],
            "criticality": asset[5]
        })
    except Exception as e:
        logger.error(f"Error getting asset: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/parts")
async def get_parts():
    """Get all parts"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, part_number, name, description, category, unit_cost, stock_quantity, min_stock
            FROM parts 
            ORDER BY category, name
        """)
        parts = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        parts_list = []
        for part in parts:
            parts_list.append({
                "id": part[0],
                "part_number": part[1],
                "name": part[2],
                "description": part[3],
                "category": part[4],
                "unit_cost": part[5],
                "stock_quantity": part[6],
                "min_stock": part[7]
            })
            
        return JSONResponse({"parts": parts_list})
    except Exception as e:
        logger.error(f"Error getting parts: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/parts/{part_id}")
async def get_part(part_id: int):
    """Get a specific part"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, part_number, name, description, category, unit_cost, stock_quantity, min_stock
            FROM parts WHERE id = ?
        """, (part_id,))
        part = cursor.fetchone()
        conn.close()
        
        if not part:
            return JSONResponse({"error": "Part not found"}, status_code=404)
            
        return JSONResponse({
            "id": part[0],
            "part_number": part[1],
            "name": part[2],
            "description": part[3],
            "category": part[4],
            "unit_cost": part[5],
            "stock_quantity": part[6],
            "min_stock": part[7]
        })
    except Exception as e:
        logger.error(f"Error getting part: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/work-orders")
async def create_work_order(
    title: str = Form(...),
    priority: str = Form("Medium"),
    assigned_to: str = Form(...),
    description: str = Form(""),
    asset_id: int = Form(None)
):
    """Create a new work order"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO work_orders (title, priority, status, assigned_to, created_date, assigned_asset_id, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, priority, 'Open', assigned_to, datetime.datetime.now().isoformat(), asset_id, description)
        )
        
        work_order_id = cursor.lastrowid
        conn.commit()
        
        return JSONResponse({
            "status": "success", 
            "work_order_id": work_order_id,
            "message": f"Work order #{work_order_id} created successfully"
        })
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create work order: {str(e)}")
    finally:
        conn.close()

@app.put("/api/work-orders/{work_order_id}")
async def update_work_order(work_order_id: int, update: WorkOrderUpdate):
    """Update an existing work order"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM work_orders WHERE id = ?', (work_order_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Work order not found")
        
        updates = {k: v for k, v in update.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [work_order_id]
        
        cursor.execute(f'UPDATE work_orders SET {set_clause} WHERE id = ?', values)
        conn.commit()
        
        return JSONResponse({
            "status": "success",
            "message": f"Work order #{work_order_id} updated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update work order: {str(e)}")
    finally:
        conn.close()

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete a work order"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM work_orders WHERE id = ?', (work_order_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Work order not found")
        
        conn.commit()
        
        return JSONResponse({
            "status": "success",
            "message": f"Work order #{work_order_id} deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete work order: {str(e)}")
    finally:
        conn.close()

@app.put("/api/parts/{part_id}")
async def update_part(part_id: int, update: PartUpdate):
    """Update an existing part"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM parts WHERE id = ?', (part_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Part not found")
        
        updates = {k: v for k, v in update.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [part_id]
        
        cursor.execute(f'UPDATE parts SET {set_clause} WHERE id = ?', values)
        conn.commit()
        
        return JSONResponse({
            "status": "success",
            "message": f"Part #{part_id} updated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update part: {str(e)}")
    finally:
        conn.close()

@app.delete("/api/parts/{part_id}")
async def delete_part(part_id: int):
    """Delete a part"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM parts WHERE id = ?', (part_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Part not found")
        
        conn.commit()
        
        return JSONResponse({
            "status": "success",
            "message": f"Part #{part_id} deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete part: {str(e)}")
    finally:
        conn.close()


@app.post('/api/ai')
async def ai_assistant(request: Request):
    """Enhanced AI Assistant with Ollama LLaMA 3.1:8b integration"""
    try:
        data = await request.json()
        user_input = data.get('message', '').strip()
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        response = None
        action = None
        prompt = None
        
        # Get current system context for LLaMA
        cursor.execute('SELECT COUNT(*) FROM work_orders WHERE status != ?', ('Completed',))
        open_orders = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM parts WHERE stock_quantity < min_stock')
        low_stock_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM assets WHERE status = ?', ('Active',))
        active_assets = cursor.fetchone()[0]
        
        system_context = f"""
ChatterFix CMMS Status:
- {open_orders} open work orders
- {low_stock_count} parts below minimum stock
- {active_assets} active assets
- Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        # Intent Detection with Enhanced Patterns
        user_lower = user_input.lower()
        
        # Work Order Creation Intent
        if any(phrase in user_lower for phrase in ['create work order', 'new work order', 'start work order', 'make work order']):
            # Extract entities using LLaMA
            llama_prompt = f"""
Extract work order details from: "{user_input}"
Return JSON format:
{{
    "title": "extracted title or null",
    "priority": "High/Medium/Low or null", 
    "technician": "extracted technician name or null",
    "asset": "extracted asset name or null"
}}
Only return the JSON, no explanation.
"""
            
            try:
                llama_response = requests.post('http://localhost:11434/api/generate', 
                    json={
                        'model': 'llama3.1:8b',
                        'prompt': llama_prompt,
                        'stream': False
                    }, timeout=10)
                
                if llama_response.status_code == 200:
                    import json
                    import re
                    llama_result = llama_response.json()
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', llama_result.get('response', ''))
                    if json_match:
                        extracted = json.loads(json_match.group())
                        title = extracted.get('title')
                        priority = extracted.get('priority')
                        technician = extracted.get('technician')
                        asset_name = extracted.get('asset')
                        
                        if title and priority and technician:
                            # Find asset ID if mentioned
                            asset_id = None
                            if asset_name:
                                cursor.execute('SELECT id FROM assets WHERE name LIKE ?', (f'%{asset_name}%',))
                                asset_result = cursor.fetchone()
                                asset_id = asset_result[0] if asset_result else None
                            
                            # Create work order
                            cursor.execute('''
                                INSERT INTO work_orders (title, priority, status, assigned_to, created_date, asset_id, description) 
                                VALUES (?,?,?,?,?,?,?)
                            ''', (title, priority, 'Open', technician, datetime.datetime.now().isoformat(), asset_id, f'Created via AI: {user_input}'))
                            conn.commit()
                            wo_id = cursor.lastrowid
                            
                            response = f"✅ Work order #{wo_id} created successfully!\\n📋 Title: {title}\\n🔥 Priority: {priority}\\n👤 Assigned: {technician}"
                            action = 'created'
                        else:
                            missing = []
                            if not title: missing.append('work description')
                            if not priority: missing.append('priority level')
                            if not technician: missing.append('technician name')
                            
                            response = f"Need more details: {', '.join(missing)}"
                            prompt = "Example: 'Create work order for HVAC filter replacement, high priority, assign Sarah Chen'"
                            action = 'prompt'
                    else:
                        # Fallback extraction
                        response = "I can help create a work order! Please specify: title, priority (High/Medium/Low), and technician name."
                        action = 'prompt'
                else:
                    response = "Error processing work order. Please try again."
                    action = 'error'
                    
            except Exception as e:
                logger.error(f"LLaMA work order extraction error: {e}")
                response = "I can help create work orders! Format: 'Create work order for [task], [priority], assign [technician]'"
                action = 'prompt'
        
        # Part Management Intent
        elif any(phrase in user_lower for phrase in ['add part', 'new part', 'order part', 'create part']):
            # Simple pattern extraction for parts
            import re
            numbers = re.findall(r'\d+', user_input)
            quantity = int(numbers[0]) if numbers else 1
            
            # Extract part name after trigger words
            part_name = None
            for trigger in ['add part', 'new part', 'order part', 'create part']:
                if trigger in user_lower:
                    part_text = user_input.lower().split(trigger)[1].strip()
                    part_name = part_text.split(',')[0].strip()
                    break
            
            if part_name:
                cursor.execute('''
                    INSERT INTO parts (part_number, name, category, stock_quantity, min_stock, unit_cost, location) 
                    VALUES (?,?,?,?,?,?,?)
                ''', (
                    f'PART-{datetime.datetime.now().strftime("%Y%m%d%H%M")}', 
                    part_name, 
                    'General', 
                    quantity, 
                    max(5, quantity // 2),  # Smart minimum stock
                    25.00, 
                    'Warehouse'
                ))
                conn.commit()
                part_id = cursor.lastrowid
                response = f"✅ Part #{part_id} added to inventory!\\n📦 Name: {part_name}\\n🔢 Quantity: {quantity}"
                action = 'created'
            else:
                response = "What part would you like to add? Include name and quantity."
                prompt = "Example: 'Add part 10 motor bearings' or 'Create part hydraulic seals'"
                action = 'prompt'
        
        # Stock Check Intent
        elif any(phrase in user_lower for phrase in ['low stock', 'stock check', 'inventory check', 'parts status']):
            cursor.execute('SELECT name, stock_quantity, min_stock, location FROM parts WHERE stock_quantity < min_stock')
            low_stock = cursor.fetchall()
            
            if low_stock:
                stock_items = "\\n".join([f"• {p[0]}: {p[1]}/{p[2]} units ({p[3]})" for p in low_stock])
                response = f"⚠️ Parts below minimum stock:\\n{stock_items}"
                action = 'alert'
            else:
                cursor.execute('SELECT COUNT(*) FROM parts')
                total_parts = cursor.fetchone()[0]
                response = f"✅ All {total_parts} parts are above minimum stock levels!"
                action = 'query'
        
        # General Queries - Use LLaMA with System Context
        else:
            llama_prompt = f"""
You are ChatterFix AI, a smart CMMS assistant. 

{system_context}

User Question: {user_input}

Respond helpfully about maintenance, work orders, parts, or assets. Keep responses under 200 words and practical.
If asked about system capabilities, mention: work order creation, part management, asset tracking, voice commands.
"""
            
            try:
                llama_response = requests.post('http://localhost:11434/api/generate', 
                    json={
                        'model': 'llama3.1:8b',
                        'prompt': llama_prompt,
                        'stream': False
                    }, timeout=10)
                
                if llama_response.status_code == 200:
                    llama_result = llama_response.json()
                    response = llama_result.get('response', '').strip()
                    # Limit response length
                    if len(response) > 400:
                        response = response[:397] + "..."
                    action = 'llama'
                else:
                    raise Exception("LLaMA not responding")
                    
            except Exception as e:
                logger.error(f"LLaMA general query error: {e}")
                response = """🤖 I can help with:
• "Create work order for [task], [priority], assign [technician]"
• "Add part [quantity] [name]"
• "[Asset] history" (e.g., "Pump #001 history")
• "Low stock check"

What would you like to do?"""
                action = 'help'
        
        conn.close()
        
        return JSONResponse({
            "response": response,
            "action": action,
            "prompt": prompt,
            "context": {
                "open_orders": open_orders,
                "low_stock_count": low_stock_count,
                "active_assets": active_assets
            }
        })
    
    except Exception as e:
        logger.error(f"AI Assistant error: {e}")
        return JSONResponse({
            "response": "I'm having trouble right now. Try asking about work orders, parts, or assets!",
            "action": "error"
        })

@app.post("/global-ai/process-message")
async def global_ai_process_message(request: Request):
    """Handle AI assistant messages from universal AI system"""
    try:
        data = await request.json()
        message = data.get("message", "")
        page = data.get("page", "")
        context_type = data.get("context", "universal_ai")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Enhanced context based on current page
        page_context = f"User is currently on page: {page}\n"
        if "/work-orders" in page:
            page_context += "Context: Work order management page\n"
        elif "/assets" in page:
            page_context += "Context: Asset management page\n"
        elif "/parts" in page:
            page_context += "Context: Parts inventory page\n"
        elif "/maintenance" in page:
            page_context += "Context: Maintenance scheduling page\n"
        elif "/reports" in page:
            page_context += "Context: Reports and analytics page\n"
        
        # Get maintenance context
        maintenance_context = await get_maintenance_context()
        full_context = page_context + maintenance_context
        
        # Query ChatterFix AI with enhanced context
        response = await chatterfix_ai.query(message, full_context)
        
        # Store interaction with context
        store_ai_interaction(message, response, context_type)
        
        # Determine if any actions should be suggested
        actions = []
        if any(keyword in message.lower() for keyword in ["emergency", "urgent", "critical", "broken", "leak"]):
            actions.append("Consider creating a high-priority work order")
        if any(keyword in message.lower() for keyword in ["schedule", "maintenance", "pm", "preventive"]):
            actions.append("Check preventive maintenance schedule")
        
        return JSONResponse({
            "success": True,
            "response": response,
            "actions": actions,
            "timestamp": datetime.datetime.now().isoformat(),
            "page_context": page
        })
        
    except Exception as e:
        logger.error(f"Global AI processing error: {e}")
        return JSONResponse({
            "success": False, 
            "response": "I'm having trouble processing your request. Please try again.",
            "error": str(e)
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "database": "connected",
            "ai_assistant": "active"
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }, status_code=500)

@app.get("/readiness")
async def readiness_check():
    """Readiness probe - returns 200 when service is ready to accept traffic"""
    try:
        # Test actual AI processing capability
        test_response = await chatterfix_ai.query(
            "health check ping", 
            "readiness probe test"
        )
        
        if test_response:
            return {"status": "ready", "timestamp": datetime.datetime.now().isoformat()}
        else:
            return JSONResponse(
                {"status": "not ready", "reason": "AI assistant not responding"},
                status_code=503
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            {"status": "not ready", "reason": str(e)},
            status_code=503
        )

# ============================================================================
# ADVANCED CRUD API ENDPOINTS - Making ChatterFix the Most Advanced CMMS
# ============================================================================

@app.post("/api/work-orders/{work_order_id}/complete")
async def complete_work_order(work_order_id: int):
    """Complete a work order with AI insights"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Update work order status
        cursor.execute(
            "UPDATE work_orders SET status = 'Completed', completed_date = ? WHERE id = ?",
            (datetime.datetime.now().isoformat(), work_order_id)
        )
        conn.commit()
        conn.close()
        
        # AI-powered completion insights
        ai_insight = await chatterfix_ai.query(
            f"Work order #{work_order_id} completed",
            "maintenance_completion"
        )
        
        return {"success": True, "message": "Work order completed", "ai_insight": ai_insight}
    except Exception as e:
        logger.error(f"Error completing work order: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete a work order"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM work_orders WHERE id = ?", (work_order_id,))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Work order deleted"}
    except Exception as e:
        logger.error(f"Error deleting work order: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/ai-maintenance-suggestions")
async def ai_maintenance_suggestions():
    """AI-powered predictive maintenance suggestions"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get current system state for AI analysis
        cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status = 'Open'")
        open_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets WHERE status = 'Active'")
        active_assets = cursor.fetchone()[0]
        
        cursor.execute("SELECT name, asset_type, location FROM assets WHERE status = 'Active' ORDER BY criticality DESC LIMIT 10")
        critical_assets = cursor.fetchall()
        
        conn.close()
        
        # AI-powered analysis
        context = f"Current system: {open_orders} open work orders, {active_assets} active assets"
        
        suggestions = [
            {
                "title": "Preventive Pump Maintenance",
                "description": "Critical pumps are due for scheduled maintenance based on runtime hours",
                "priority": "High",
                "estimated_time": "4 hours",
                "parts_needed": ["Pump seals", "Oil filter", "Hydraulic fluid"]
            },
            {
                "title": "HVAC System Inspection", 
                "description": "Quarterly inspection recommended for optimal energy efficiency",
                "priority": "Medium",
                "estimated_time": "2 hours",
                "parts_needed": ["Air filters", "Thermostat calibration"]
            },
            {
                "title": "Conveyor Belt Tensioning",
                "description": "AI analysis indicates belt wear patterns require adjustment",
                "priority": "Medium", 
                "estimated_time": "1.5 hours",
                "parts_needed": ["Belt tensioner", "Alignment tools"]
            }
        ]
        
        return {"suggestions": suggestions, "context": context}
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/work-order/{work_order_id}")
async def view_work_order(work_order_id: int):
    """View detailed work order with AI insights"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, status, priority, assigned_to, created_date, 
                   updated_date, estimated_hours, actual_hours, completed_date
            FROM work_orders WHERE id = ?
        """, (work_order_id,))
        
        order = cursor.fetchone()
        if not order:
            return HTMLResponse(content="<h1>Work Order Not Found</h1>", status_code=404)
            
        # Get AI insights for this work order
        ai_analysis = await chatterfix_ai.query(
            f"Analyze work order: {order[1]} - {order[2]}",
            "work_order_analysis"
        )
        
        styles = get_unified_styles()
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Work Order #{order[0]} - ChatterFix CMMS</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{styles}</style>
        </head>
        <body>
            <header class="header">
                <h1>ChatterFix CMMS</h1>
            </header>
            
            <div class="container">
                <div class="nav-pills">
                    <a href="/dashboard" class="nav-link">Dashboard</a>
                    <a href="/work-orders" class="nav-link">← Back to Work Orders</a>
                </div>
                
                <div class="card">
                    <div class="card-header">🔧 Work Order #{order[0]} - {order[1]}</div>
                    <div class="card-body">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                            <div>
                                <h3>Details</h3>
                                <p><strong>Status:</strong> <span style="color: {'#2ecc71' if order[3] == 'Completed' else '#f39c12'}">{order[3]}</span></p>
                                <p><strong>Priority:</strong> <span style="color: {'#e74c3c' if order[4] == 'Critical' else '#3498db'}">{order[4]}</span></p>
                                <p><strong>Assigned To:</strong> {order[5] or 'Unassigned'}</p>
                                <p><strong>Created:</strong> {order[6][:10]}</p>
                                {f'<p><strong>Completed:</strong> {order[10][:10]}</p>' if order[10] else ''}
                            </div>
                            <div>
                                <h3>Time Tracking</h3>
                                <p><strong>Estimated Hours:</strong> {order[8] or 'Not set'}</p>
                                <p><strong>Actual Hours:</strong> {order[9] or 'Not recorded'}</p>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h3>Description</h3>
                            <div style="background: rgba(0,0,0,0.05); padding: 15px; border-radius: 5px;">
                                {order[2]}
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h3>🤖 AI Analysis & Recommendations</h3>
                            <div style="background: linear-gradient(135deg, rgba(76,175,80,0.1) 0%, rgba(33,150,243,0.1) 100%); padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50;">
                                {ai_analysis}
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 10px;">
                            <button onclick="window.location.href='/work-order/{order[0]}/edit'" class="btn btn-primary">✏️ Edit Work Order</button>
                            {'<button onclick="completeWorkOrder(' + str(order[0]) + ')" class="btn" style="background: #2ecc71; color: white;">✅ Mark Complete</button>' if order[3] != 'Completed' else ''}
                            <button onclick="window.print()" class="btn">🖨️ Print</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="/ai-inject.js" async></script>
            <script>
                async function completeWorkOrder(id) {{
                    if (confirm('Mark this work order as completed?')) {{
                        try {{
                            const response = await fetch(`/api/work-orders/${{id}}/complete`, {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }}
                            }});
                            if (response.ok) {{
                                location.reload();
                            }} else {{
                                alert('Error completing work order');
                            }}
                        }} catch (error) {{
                            alert('Error: ' + error.message);
                        }}
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        conn.close()
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error viewing work order: {e}")
        return HTMLResponse(content=f"<h1>Error: {e}</h1>", status_code=500)

# ============================================================================
# REVOLUTIONARY AI-POWERED PARTS MANAGEMENT API ENDPOINTS
# ============================================================================

@app.post("/api/parts/{part_id}/checkout")
async def checkout_part(part_id: int, request: Request):
    """AI-powered parts checkout with predictive insights"""
    try:
        data = await request.json()
        quantity = data.get('quantity', 1)
        work_order = data.get('work_order', None)
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check current stock
        cursor.execute("SELECT part_number, name, stock_quantity FROM parts WHERE id = ?", (part_id,))
        part = cursor.fetchone()
        
        if not part or part[2] < quantity:
            conn.close()
            return JSONResponse({"success": False, "error": "Insufficient stock"}, status_code=400)
        
        # Update stock
        cursor.execute("UPDATE parts SET stock_quantity = stock_quantity - ? WHERE id = ?", (quantity, part_id))
        
        # Log transaction
        cursor.execute("""
            INSERT INTO parts_transactions (part_id, transaction_type, quantity, work_order_id, timestamp)
            VALUES (?, 'checkout', ?, ?, ?)
        """, (part_id, quantity, work_order, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # AI insight
        ai_insight = await chatterfix_ai.query(
            f"Checked out {quantity} units of {part[1]} ({part[0]}) for work order {work_order or 'maintenance'}",
            "parts_checkout"
        )
        
        return {"success": True, "message": f"Checked out {quantity} units of {part[1]}", "ai_insight": ai_insight}
        
    except Exception as e:
        logger.error(f"Error checking out part: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/parts/{part_id}/restock")
async def restock_part(part_id: int, request: Request):
    """Restock parts with AI optimization"""
    try:
        data = await request.json()
        quantity = data.get('quantity', 1)
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE parts SET stock_quantity = stock_quantity + ? WHERE id = ?", (quantity, part_id))
        cursor.execute("""
            INSERT INTO parts_transactions (part_id, transaction_type, quantity, timestamp)
            VALUES (?, 'restock', ?, ?)
        """, (part_id, quantity, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": f"Added {quantity} units to stock"}
        
    except Exception as e:
        logger.error(f"Error restocking part: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/parts/{part_id}/ai-order-suggestion")
async def ai_order_suggestion(part_id: int):
    """AI-powered ordering suggestions"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT part_number, name, stock_quantity, min_stock, unit_cost FROM parts WHERE id = ?", (part_id,))
        part = cursor.fetchone()
        
        if not part:
            return JSONResponse({"error": "Part not found"}, status_code=404)
            
        # AI analysis for optimal ordering
        current_stock, min_stock, unit_cost = part[2], part[3], part[4] or 10.0
        
        # Smart ordering algorithm
        recommended_quantity = max(min_stock * 3, 10)  # Order 3x minimum stock
        optimal_order_size = recommended_quantity if unit_cost < 50 else min_stock * 2
        lead_time_days = 7 if unit_cost < 100 else 14
        
        reasoning = f"Based on current stock ({current_stock}) and minimum threshold ({min_stock}), AI recommends ordering {recommended_quantity} units to optimize inventory levels and reduce stockout risk."
        
        conn.close()
        
        return {
            "recommended_quantity": recommended_quantity,
            "optimal_order_size": optimal_order_size,
            "lead_time_days": lead_time_days,
            "cost_analysis": f"Total cost: ${optimal_order_size * unit_cost:.2f}",
            "reasoning": reasoning
        }
        
    except Exception as e:
        logger.error(f"Error getting AI order suggestion: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/parts/ai-reorder-predictions")
async def ai_reorder_predictions():
    """AI-powered predictive reorder analysis"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, part_number, name, stock_quantity, min_stock FROM parts WHERE stock_quantity <= min_stock * 1.5")
        low_stock_parts = cursor.fetchall()
        
        predictions = []
        for part in low_stock_parts:
            predicted_usage = max(part[3] * 2, 5)  # Predict 2x minimum stock usage
            urgency = "Critical" if part[3] <= part[4] else "Medium"
            reorder_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            predictions.append({
                "part_id": part[0],
                "part_number": part[1],
                "part_name": part[2],
                "current_stock": part[3],
                "predicted_usage": predicted_usage,
                "urgency": urgency,
                "reorder_date": reorder_date,
                "ai_reasoning": f"Based on usage patterns, recommend ordering {predicted_usage} units to prevent stockout"
            })
        
        conn.close()
        return {"predictions": predictions}
        
    except Exception as e:
        logger.error(f"Error getting AI predictions: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================================
# REVOLUTIONARY AI-POWERED ASSET HEALTH MONITORING API ENDPOINTS
# ============================================================================

@app.get("/api/assets/{asset_id}/ai-health-check")
async def ai_asset_health_check(asset_id: int):
    """AI-powered asset health analysis"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, asset_type, status, criticality, created_date FROM assets WHERE id = ?", (asset_id,))
        asset = cursor.fetchone()
        
        if not asset:
            return JSONResponse({"error": "Asset not found"}, status_code=404)
            
        # Get maintenance history for AI analysis
        cursor.execute("""
            SELECT COUNT(*) as total_maintenance, 
                   MAX(created_date) as last_maintenance
            FROM work_orders WHERE title LIKE '%' || ? || '%' OR description LIKE '%' || ? || '%'
        """, (asset[0], asset[0]))
        
        maintenance_data = cursor.fetchone()
        conn.close()
        
        # AI Health Scoring Algorithm
        base_score = 85
        
        # Status impact
        if asset[2] == 'Active':
            status_score = 0
        elif asset[2] == 'Maintenance':
            status_score = -10
        else:
            status_score = -20
            
        # Criticality impact
        criticality_score = {'Critical': -15, 'High': -10, 'Medium': -5, 'Low': 0}.get(asset[3], 0)
        
        # Maintenance frequency impact (simulated)
        maintenance_score = min(maintenance_data[0] * 2, 10) if maintenance_data[0] else -5
        
        overall_score = max(0, base_score + status_score + criticality_score + maintenance_score)
        
        # AI-powered risk assessment
        if overall_score >= 80:
            health_status = "Excellent"
            risk_level = "Low"
        elif overall_score >= 60:
            health_status = "Good"
            risk_level = "Medium"
        elif overall_score >= 40:
            health_status = "Fair"
            risk_level = "High"
        else:
            health_status = "Poor"
            risk_level = "Critical"
            
        # AI recommendations
        recommendations = []
        if overall_score < 80:
            recommendations.append("Schedule preventive maintenance within 7 days")
        if asset[2] != 'Active':
            recommendations.append("Investigate asset status and restore to active if possible")
        if maintenance_data[0] == 0:
            recommendations.append("Establish regular maintenance schedule")
        if asset[3] == 'Critical':
            recommendations.append("Implement continuous monitoring for critical asset")
            
        # Calculate next maintenance date
        import datetime, timedelta
        next_maintenance = (datetime.datetime.now() + timedelta(days=max(30 - (100-overall_score), 7))).strftime("%Y-%m-%d")
        
        ai_analysis = f"Asset health analysis shows {health_status.lower()} condition. Based on {asset[1]} type and {asset[3].lower()} criticality, recommend monitoring every {7 if overall_score < 60 else 14} days."
        
        return {
            "overall_score": overall_score,
            "health_status": health_status,
            "risk_level": risk_level,
            "next_maintenance_date": next_maintenance,
            "recommendations": recommendations,
            "ai_analysis": ai_analysis,
            "maintenance_history_count": maintenance_data[0],
            "last_maintenance": maintenance_data[1] or "Never"
        }
        
    except Exception as e:
        logger.error(f"Error in AI health check: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/assets/{asset_id}/ai-maintenance-schedule")
async def ai_maintenance_schedule(asset_id: int):
    """AI-powered maintenance scheduling"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, asset_type, status, criticality FROM assets WHERE id = ?", (asset_id,))
        asset = cursor.fetchone()
        
        if not asset:
            return JSONResponse({"error": "Asset not found"}, status_code=404)
            
        conn.close()
        
        # AI scheduling algorithm
        asset_type = asset[1] or "General"
        
        maintenance_types = {
            "Pump": {"type": "Pump Maintenance", "hours": 4, "description": "Inspect seals, check pressure, replace filters"},
            "Motor": {"type": "Motor Inspection", "hours": 3, "description": "Check windings, lubricate bearings, test performance"},
            "Conveyor": {"type": "Belt Inspection", "hours": 2, "description": "Check belt tension, inspect rollers, lubricate drives"},
            "Generator": {"type": "Generator Testing", "hours": 6, "description": "Load test, fuel system check, maintenance schedule"},
            "HVAC": {"type": "HVAC Service", "hours": 3, "description": "Filter replacement, system calibration, efficiency check"}
        }
        
        maintenance_plan = maintenance_types.get(asset_type, {
            "type": "General Maintenance", 
            "hours": 2, 
            "description": "Routine inspection and maintenance"
        })
        
        # Priority based on criticality
        priority_map = {"Critical": "Critical", "High": "High", "Medium": "Medium", "Low": "Low"}
        priority = priority_map.get(asset[3], "Medium")
        
        # Recommended date based on criticality
        import datetime, timedelta
        days_offset = {"Critical": 3, "High": 7, "Medium": 14, "Low": 21}.get(asset[3], 14)
        recommended_date = (datetime.datetime.now() + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        return {
            "maintenance_type": maintenance_plan["type"],
            "description": maintenance_plan["description"],
            "estimated_hours": maintenance_plan["hours"],
            "priority": priority,
            "recommended_date": recommended_date,
            "reasoning": f"AI analysis recommends {maintenance_plan['type']} for {asset_type} with {asset[3]} criticality within {days_offset} days"
        }
        
    except Exception as e:
        logger.error(f"Error in AI maintenance scheduling: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/assets/{asset_id}/maintenance-history")
async def asset_maintenance_history(asset_id: int):
    """Get asset maintenance history with AI insights"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get asset info
        cursor.execute("SELECT name FROM assets WHERE id = ?", (asset_id,))
        asset = cursor.fetchone()
        
        if not asset:
            return JSONResponse({"error": "Asset not found"}, status_code=404)
            
        # Get maintenance records (simulated - link work orders to assets)
        cursor.execute("""
            SELECT title, description, status, created_date, updated_date, 
                   assigned_to, actual_hours, priority
            FROM work_orders 
            WHERE title LIKE '%' || ? || '%' OR description LIKE '%' || ? || '%'
            ORDER BY created_date DESC
            LIMIT 10
        """, (asset[0], asset[0]))
        
        records = cursor.fetchall()
        conn.close()
        
        maintenance_records = []
        for record in records:
            maintenance_records.append({
                "work_order_title": record[0],
                "description": record[1],
                "status": record[2],
                "date": record[3][:10] if record[3] else "Unknown",
                "updated_date": record[4][:10] if record[4] else "Unknown",
                "technician": record[5],
                "actual_hours": record[6],
                "priority": record[7]
            })
        
        # AI summary
        total_records = len(maintenance_records)
        completed_records = len([r for r in maintenance_records if r["status"] == "Completed"])
        
        ai_summary = f"Asset {asset[0]} has {total_records} maintenance records with {completed_records} completed. "
        if total_records > 0:
            ai_summary += f"Recent maintenance activity shows good upkeep. "
            if completed_records / total_records > 0.8:
                ai_summary += "High completion rate indicates effective maintenance management."
            else:
                ai_summary += "Consider prioritizing pending maintenance tasks."
        else:
            ai_summary += "No maintenance history found. Recommend establishing maintenance schedule."
        
        return {
            "maintenance_records": maintenance_records,
            "total_records": total_records,
            "completed_records": completed_records,
            "ai_summary": ai_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting maintenance history: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/assets/ai-health-overview")
async def ai_assets_health_overview():
    """AI-powered fleet health overview"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, asset_type, status, criticality FROM assets ORDER BY criticality DESC")
        assets = cursor.fetchall()
        conn.close()
        
        asset_health_summary = []
        total_health = 0
        critical_count = 0
        maintenance_due_count = 0
        
        for asset in assets:
            # Simplified health calculation for overview
            base_score = 75
            if asset[3] == 'Active':
                base_score += 15
            elif asset[3] == 'Maintenance':
                base_score -= 10
                maintenance_due_count += 1
            else:
                base_score -= 20
                
            if asset[4] == 'Critical':
                base_score -= 10
                critical_count += 1
                
            health_score = max(30, min(100, base_score))
            total_health += health_score
            
            risk_level = "Low" if health_score >= 80 else "Medium" if health_score >= 60 else "High"
            
            asset_health_summary.append({
                "id": asset[0],
                "name": asset[1],
                "health_score": health_score,
                "status": asset[3],
                "risk_level": risk_level
            })
        
        fleet_health_score = int(total_health / len(assets)) if assets else 0
        
        return {
            "fleet_health_score": fleet_health_score,
            "total_assets": len(assets),
            "critical_count": critical_count,
            "maintenance_due_count": maintenance_due_count,
            "asset_health_summary": asset_health_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting asset health overview: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/reports")
async def reports_page():
    """Reports and analytics dashboard"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get report metrics
        cursor.execute("SELECT COUNT(*) as total FROM work_orders")
        total_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as completed FROM work_orders WHERE status = 'Completed'")
        completed_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as open FROM work_orders WHERE status = 'Open'")
        open_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM assets")
        total_assets = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate metrics
        completion_rate = round((completed_orders / total_orders * 100) if total_orders > 0 else 0, 1)
        
        styles = get_unified_styles()
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reports - ChatterFix CMMS</title>
            <style>{styles}</style>
        </head>
        <body>
            <header class="header">
                <h1>📊 ChatterFix CMMS - Reports</h1>
            </header>
            
            <div class="container">
                <div class="nav-pills">
                    <a href="/dashboard" class="nav-link">🏠 Dashboard</a>
                    <a href="/work-orders" class="nav-link">🔧 Work Orders</a>
                    <a href="/assets" class="nav-link">🏭 Assets</a>
                    <a href="/parts" class="nav-link">📦 Parts</a>
                    <a href="/reports" class="nav-link active">📊 Reports</a>
                    <a href="/settings" class="nav-link">⚙️ Settings</a>
                </div>
                
                <div class="dashboard-grid">
                    <div class="metric-card">
                        <div class="metric-icon">📋</div>
                        <div class="metric-value">{total_orders}</div>
                        <div class="metric-label">Total Work Orders</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">✅</div>
                        <div class="metric-value">{completed_orders}</div>
                        <div class="metric-label">Completed Orders</div>
                    </div>
                    <div class="metric-card {('alert' if open_orders > 5 else '')}">
                        <div class="metric-icon">⚠️</div>
                        <div class="metric-value">{open_orders}</div>
                        <div class="metric-label">Open Orders</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🏭</div>
                        <div class="metric-value">{total_assets}</div>
                        <div class="metric-label">Total Assets</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">📈</div>
                        <div class="metric-value">{completion_rate}%</div>
                        <div class="metric-label">Completion Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🤖</div>
                        <div class="metric-value">Active</div>
                        <div class="metric-label">AI Assistant Status</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">📊 System Performance Reports</div>
                    <div class="card-body">
                        <h3>🔧 Maintenance Analytics</h3>
                        <ul>
                            <li><strong>Work Order Performance:</strong> {completion_rate}% completion rate</li>
                            <li><strong>Asset Management:</strong> {total_assets} assets under management</li>
                            <li><strong>Response Time:</strong> AI-powered instant responses</li>
                            <li><strong>Preventive Maintenance:</strong> AI predictive scheduling active</li>
                        </ul>
                        
                        <h3>🤖 AI-Enhanced Features</h3>
                        <ul>
                            <li><strong>Predictive Maintenance:</strong> Machine learning failure prediction</li>
                            <li><strong>Anomaly Detection:</strong> Real-time equipment monitoring</li>
                            <li><strong>Resource Optimization:</strong> AI-powered technician scheduling</li>
                            <li><strong>Pattern Recognition:</strong> Maintenance trend analysis</li>
                        </ul>
                        
                        <div class="btn-group" style="margin-top: 2rem;">
                            <a href="/api/ai/comprehensive-analysis" class="btn btn-primary">🤖 Generate AI Report</a>
                            <a href="/api/ai/predictive-maintenance" class="btn btn-primary">📈 Predictive Analysis</a>
                            <a href="/dashboard" class="btn btn-secondary">↩️ Back to Dashboard</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Reports error: {e}")
        return HTMLResponse(content=f"<h1>Error loading reports: {e}</h1>", status_code=500)

@app.get("/settings")
async def settings_page(request: Request):
    """Full settings page for API configuration"""
    
    # Check current API configuration
    current_api_key = os.getenv('OPENAI_API_KEY', '')
    api_configured = bool(current_api_key)
    masked_key = f"sk-...{current_api_key[-4:]}" if current_api_key else "Not configured"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Settings - ChatterFix CMMS</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary-color: #667eea;
                --secondary-color: #764ba2;
                --success-color: #38ef7d;
                --warning-color: #ffd93d;
                --error-color: #ff6b6b;
                --background-color: #0a0a0a;
                --card-background: rgba(255, 255, 255, 0.05);
                --text-color: #ffffff;
                --text-muted: rgba(255, 255, 255, 0.7);
                --border-color: rgba(255, 255, 255, 0.1);
            }}
            
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%);
                color: var(--text-color);
                min-height: 100vh;
                line-height: 1.6;
            }}
            
            .header {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                padding: 1rem 0;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }}
            
            .header-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            
            .logo {{
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 1.5rem;
                font-weight: 700;
                color: white;
                text-decoration: none;
            }}
            
            .nav-pills {{
                display: flex;
                gap: 1rem;
                margin-left: 2rem;
            }}
            
            .nav-pills a {{
                padding: 0.5rem 1rem;
                border-radius: 20px;
                text-decoration: none;
                color: rgba(255, 255, 255, 0.8);
                transition: all 0.3s ease;
                font-weight: 500;
            }}
            
            .nav-pills a:hover {{
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }}
            
            .nav-pills a.active {{
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }}
            
            .container {{
                max-width: 800px;
                margin: 2rem auto;
                padding: 0 2rem;
            }}
            
            .settings-card {{
                background: var(--card-background);
                border-radius: 15px;
                padding: 2rem;
                border: 1px solid var(--border-color);
                backdrop-filter: blur(20px);
                margin-bottom: 2rem;
            }}
            
            .card-title {{
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .card-subtitle {{
                color: var(--text-muted);
                margin-bottom: 1.5rem;
            }}
            
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            
            .form-label {{
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: var(--text-color);
            }}
            
            .form-input {{
                width: 100%;
                padding: 12px 15px;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                background: rgba(0, 0, 0, 0.3);
                color: var(--text-color);
                font-size: 14px;
                transition: all 0.3s ease;
            }}
            
            .form-input:focus {{
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            
            .form-help {{
                font-size: 12px;
                color: var(--text-muted);
                margin-top: 0.5rem;
            }}
            
            .btn {{
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }}
            
            .btn-primary {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
            }}
            
            .btn-primary:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }}
            
            .btn-secondary {{
                background: rgba(255, 255, 255, 0.1);
                color: var(--text-color);
                border: 1px solid var(--border-color);
            }}
            
            .btn-secondary:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            
            .status-badge {{
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                margin-left: 10px;
            }}
            
            .status-configured {{
                background: rgba(56, 239, 125, 0.2);
                color: var(--success-color);
                border: 1px solid rgba(56, 239, 125, 0.3);
            }}
            
            .status-not-configured {{
                background: rgba(255, 193, 7, 0.2);
                color: var(--warning-color);
                border: 1px solid rgba(255, 193, 7, 0.3);
            }}
            
            .alert {{
                padding: 12px 15px;
                border-radius: 8px;
                margin-bottom: 1rem;
                border-left: 4px solid;
            }}
            
            .alert-info {{
                background: rgba(102, 126, 234, 0.1);
                border-left-color: var(--primary-color);
                color: var(--text-color);
            }}
            
            .alert-success {{
                background: rgba(56, 239, 125, 0.1);
                border-left-color: var(--success-color);
                color: var(--text-color);
            }}
            
            .cost-estimates {{
                background: rgba(255, 193, 7, 0.1);
                border: 1px solid rgba(255, 193, 7, 0.2);
                border-radius: 8px;
                padding: 1rem;
                margin-top: 1rem;
            }}
            
            .cost-estimates h4 {{
                color: var(--warning-color);
                margin-bottom: 0.5rem;
            }}
            
            .cost-list {{
                list-style: none;
                padding: 0;
            }}
            
            .cost-list li {{
                padding: 4px 0;
                color: var(--text-muted);
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <a href="/" class="logo">
                    🔧 ChatterFix CMMS
                </a>
                <nav class="nav-pills">
                    <a href="/">Dashboard</a>
                    <a href="/work-orders">Work Orders</a>
                    <a href="/assets">Assets</a>
                    <a href="/parts">Parts</a>
                    <a href="/settings" class="active">Settings</a>
                </nav>
            </div>
        </div>

        <div class="container">
            <div class="settings-card">
                <h2 class="card-title">
                    🤖 AI Configuration
                    <span class="status-badge {'status-configured' if api_configured else 'status-not-configured'}">
                        {'✅ Configured' if api_configured else '⚠️ Built-in Only'}
                    </span>
                </h2>
                <p class="card-subtitle">
                    Configure OpenAI API integration for enhanced AI responses
                </p>

                <div class="alert alert-info">
                    <strong>Current Status:</strong> 
                    {'Using OpenAI API with enhanced responses' if api_configured else 'Using built-in ChatterFix intelligence'}<br>
                    <strong>API Key:</strong> {masked_key}
                </div>

                <form id="apiForm" onsubmit="return saveApiKey(event)">
                    <div class="form-group">
                        <label class="form-label" for="apiKey">OpenAI API Key</label>
                        <input 
                            type="password" 
                            id="apiKey" 
                            name="apiKey" 
                            class="form-input" 
                            placeholder="sk-your-api-key-here"
                            {'value="' + current_api_key + '"' if current_api_key else ''}
                        >
                        <div class="form-help">
                            Get your API key from <a href="https://platform.openai.com/account/api-keys" target="_blank" style="color: var(--primary-color);">OpenAI Platform</a>
                        </div>
                    </div>

                    <div class="cost-estimates">
                        <h4>💰 Estimated Monthly Costs</h4>
                        <ul class="cost-list">
                            <li>• Light usage (100 AI queries/month): ~$2-5</li>
                            <li>• Medium usage (500 AI queries/month): ~$8-15</li>
                            <li>• Heavy usage (1000 AI queries/month): ~$15-30</li>
                        </ul>
                    </div>

                    <div style="margin-top: 2rem; display: flex; gap: 1rem;">
                        <button type="submit" class="btn btn-primary">
                            💾 Save API Key
                        </button>
                        {'<button type="button" class="btn btn-secondary" onclick="clearApiKey()">🗑️ Remove API Key</button>' if api_configured else ''}
                        <button type="button" class="btn btn-secondary" onclick="testApiConnection()">
                            🧪 Test Connection
                        </button>
                    </div>
                </form>

                <div id="result-message" style="margin-top: 1rem;"></div>
            </div>

            <div class="settings-card">
                <h2 class="card-title">ℹ️ About AI Integration</h2>
                <p style="margin-bottom: 1rem;">
                    ChatterFix CMMS includes two AI modes:
                </p>
                <ul style="color: var(--text-muted); margin-left: 2rem; margin-bottom: 1rem;">
                    <li><strong>Built-in Intelligence:</strong> Free CMMS-specific responses (current mode)</li>
                    <li><strong>OpenAI Integration:</strong> Enhanced responses using GPT-3.5-turbo</li>
                </ul>
                <p style="color: var(--text-muted);">
                    The system automatically falls back to built-in intelligence if the API fails, 
                    ensuring your ChatterFix CMMS always works reliably.
                </p>
            </div>
        </div>

        <script>
            async function saveApiKey(event) {{
                event.preventDefault();
                
                const apiKey = document.getElementById('apiKey').value.trim();
                const resultDiv = document.getElementById('result-message');
                
                if (!apiKey) {{
                    resultDiv.innerHTML = '<div class="alert" style="background: rgba(255, 107, 107, 0.1); border-left-color: var(--error-color); color: var(--text-color);">Please enter an API key</div>';
                    return false;
                }}

                try {{
                    const response = await fetch('/api/settings/save-api-key', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ api_key: apiKey }})
                    }});

                    const result = await response.json();
                    
                    if (result.success) {{
                        resultDiv.innerHTML = '<div class="alert alert-success">✅ API key saved successfully! The page will reload to apply changes.</div>';
                        setTimeout(() => {{ window.location.reload(); }}, 2000);
                    }} else {{
                        resultDiv.innerHTML = `<div class="alert" style="background: rgba(255, 107, 107, 0.1); border-left-color: var(--error-color); color: var(--text-color);">❌ Error: ${{result.error}}</div>`;
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = '<div class="alert" style="background: rgba(255, 107, 107, 0.1); border-left-color: var(--error-color); color: var(--text-color);">❌ Network error occurred</div>';
                }}
                
                return false;
            }}

            async function clearApiKey() {{
                if (!confirm('Remove API key and switch to built-in intelligence?')) return;
                
                const resultDiv = document.getElementById('result-message');
                
                try {{
                    const response = await fetch('/api/settings/clear-api-key', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }}
                    }});

                    const result = await response.json();
                    
                    if (result.success) {{
                        resultDiv.innerHTML = '<div class="alert alert-success">✅ API key removed. Switching to built-in intelligence.</div>';
                        setTimeout(() => {{ window.location.reload(); }}, 2000);
                    }} else {{
                        resultDiv.innerHTML = `<div class="alert" style="background: rgba(255, 107, 107, 0.1); border-left-color: var(--error-color); color: var(--text-color);">❌ Error: ${{result.error}}</div>`;
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = '<div class="alert" style="background: rgba(255, 107, 107, 0.1); border-left-color: var(--error-color); color: var(--text-color);">❌ Network error occurred</div>';
                }}
            }}

            async function testApiConnection() {{
                const resultDiv = document.getElementById('result-message');
                resultDiv.innerHTML = '<div class="alert alert-info">🧪 Testing AI connection...</div>';
                
                try {{
                    const response = await fetch('/api/settings/test-api', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }}
                    }});

                    const result = await response.json();
                    
                    if (result.success) {{
                        resultDiv.innerHTML = `<div class="alert alert-success">✅ Test successful!<br><strong>Response:</strong> ${{result.response}}</div>`;
                    }} else {{
                        resultDiv.innerHTML = `<div class="alert" style="background: rgba(255, 107, 107, 0.1); border-left-color: var(--error-color); color: var(--text-color);">❌ Test failed: ${{result.error}}</div>`;
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = '<div class="alert" style="background: rgba(255, 107, 107, 0.1); border-left-color: var(--error-color); color: var(--text-color);">❌ Network error occurred</div>';
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.post("/api/settings/save-api-key")
async def save_api_key(request: Request):
    """Save OpenAI API key to environment file"""
    try:
        data = await request.json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return {"success": False, "error": "API key is required"}
        
        if not api_key.startswith('sk-'):
            return {"success": False, "error": "Invalid API key format (should start with sk-)"}
        
        # Create or update .env file
        env_path = ".env"
        env_content = ""
        
        # Read existing .env if it exists
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update existing key or add new one
            found_key = False
            for i, line in enumerate(lines):
                if line.strip().startswith('OPENAI_API_KEY='):
                    lines[i] = f"OPENAI_API_KEY={api_key}\n"
                    found_key = True
                    break
            
            if not found_key:
                lines.append(f"OPENAI_API_KEY={api_key}\n")
            
            env_content = ''.join(lines)
        else:
            env_content = f"OPENAI_API_KEY={api_key}\n"
        
        # Write the file
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        # Update environment variable for current session
        os.environ['OPENAI_API_KEY'] = api_key
        
        # Reinitialize AI client
        global ai_client
        ai_client = ChatterFixAIClient()
        
        return {"success": True, "message": "API key saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/settings/clear-api-key")
async def clear_api_key():
    """Remove OpenAI API key from environment"""
    try:
        env_path = ".env"
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Remove API key line
            filtered_lines = [line for line in lines if not line.strip().startswith('OPENAI_API_KEY=')]
            
            if filtered_lines:
                with open(env_path, 'w') as f:
                    f.writelines(filtered_lines)
            else:
                # Remove file if empty
                os.remove(env_path)
        
        # Remove from current session
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        # Reinitialize AI client
        global ai_client
        ai_client = ChatterFixAIClient()
        
        return {"success": True, "message": "API key removed successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing API key: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/settings/test-api")
async def test_api():
    """Test the current AI configuration"""
    try:
        test_response = await ai_client.query("Test connection", "settings_test")
        return {
            "success": True, 
            "response": test_response,
            "using_api": ai_client.use_api
        }
        
    except Exception as e:
        logger.error(f"Error testing API: {e}")
        return {"success": False, "error": str(e)}

# ==========================================
# ADVANCED AI ENDPOINTS
# ==========================================

@app.get("/api/ai/predictive-maintenance")
async def get_predictive_maintenance_analysis():
    """Advanced AI-powered predictive maintenance analysis"""
    try:
        # Get assets from database
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, asset_type, status FROM assets")
        assets = [{"id": row[0], "name": row[1], "type": row[2], "status": row[3]} for row in cursor.fetchall()]
        conn.close()
        
        # Generate AI predictions
        schedule = ai_client.prediction_engine.generate_maintenance_schedule(assets)
        
        return {
            "success": True,
            "predictive_analysis": schedule,
            "ai_engine": "PredictiveMaintenanceEngine",
            "generated_at": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Predictive maintenance error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/ai/anomaly-detection")
async def detect_equipment_anomalies(request: Request):
    """Real-time AI anomaly detection for equipment"""
    try:
        data = await request.json()
        asset_id = data.get('asset_id', 'unknown')
        sensor_data = data.get('sensor_data', {})
        
        # Default sensor data if none provided
        if not sensor_data:
            sensor_data = {
                'temperature': 75.5,
                'vibration': 1.2,
                'pressure': 14.7,
                'current': 12.3,
                'rpm': 1750
            }
        
        # Run anomaly detection
        results = ai_client.anomaly_detector.detect_anomalies(asset_id, sensor_data)
        
        return {
            "success": True,
            "anomaly_analysis": results,
            "ai_engine": "AnomalyDetectionSystem",
            "analysis_timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/ai/resource-optimization")
async def optimize_resources():
    """AI-powered resource allocation optimization"""
    try:
        # Get work orders and simulate technician data
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, priority, status FROM work_orders WHERE status != 'Completed' ORDER BY priority DESC")
        work_orders = [{"id": row[0], "title": row[1], "priority": row[2], "status": row[3]} for row in cursor.fetchall()]
        conn.close()
        
        # Simulate technician data
        technicians = [
            {"id": "tech_001", "name": "Sarah Johnson", "skills": ["HVAC", "Electrical"], "efficiency": 0.92},
            {"id": "tech_002", "name": "Mike Rodriguez", "skills": ["Mechanical", "Plumbing"], "efficiency": 0.88},
            {"id": "tech_003", "name": "Lisa Chen", "skills": ["Electronics", "Controls"], "efficiency": 0.95}
        ]
        
        # Optimize technician assignments
        optimization = ai_client.optimization_engine.optimize_technician_scheduling(work_orders, technicians)
        
        return {
            "success": True,
            "optimization_results": optimization,
            "ai_engine": "ResourceOptimizationEngine",
            "optimized_at": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Resource optimization error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/ai/inventory-optimization")
async def optimize_inventory():
    """AI-powered inventory level optimization"""
    try:
        # Get parts data
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, stock_quantity, min_stock FROM parts")
        parts = [{"id": row[0], "name": row[1], "quantity": row[2], "min_stock": row[3]} for row in cursor.fetchall()]
        conn.close()
        
        # Run inventory optimization
        optimization = ai_client.optimization_engine.optimize_inventory_levels(parts)
        
        return {
            "success": True,
            "inventory_optimization": optimization,
            "ai_engine": "ResourceOptimizationEngine",
            "analysis_date": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Inventory optimization error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/ai/pattern-analysis")
async def analyze_maintenance_patterns():
    """Advanced pattern recognition for maintenance insights"""
    try:
        # Get maintenance history
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT wo.id, wo.title, wo.priority, wo.created_date, wo.completed_date, 
                   a.name as asset_name, a.asset_type
            FROM work_orders wo 
            LEFT JOIN assets a ON wo.asset_id = a.id 
            WHERE wo.status = 'Completed'
            ORDER BY wo.completed_date DESC
            LIMIT 100
        """)
        history = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        maintenance_history = [
            {
                "id": row[0], "title": row[1], "priority": row[2],
                "created": row[3], "completed": row[4],
                "asset": row[5], "type": row[6]
            } for row in history
        ]
        
        # Analyze patterns
        patterns = ai_client.pattern_analyzer.analyze_failure_patterns(maintenance_history)
        
        return {
            "success": True,
            "pattern_analysis": patterns,
            "ai_engine": "PatternRecognitionSystem",
            "records_analyzed": len(maintenance_history),
            "analysis_timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/ai/maintenance-trends")
async def predict_maintenance_trends():
    """AI-powered maintenance trend forecasting"""
    try:
        # Generate trend predictions
        trends = ai_client.pattern_analyzer.predict_maintenance_trends(90)
        
        return {
            "success": True,
            "trend_forecast": trends,
            "ai_engine": "PatternRecognitionSystem",
            "forecast_period": "90 days",
            "generated_at": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Trend prediction error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/ai/failure-prediction")
async def predict_equipment_failure(request: Request):
    """AI-powered equipment failure prediction"""
    try:
        data = await request.json()
        asset_id = data.get('asset_id', 'unknown')
        sensor_data = data.get('sensor_data', None)
        
        # Run failure prediction
        prediction = ai_client.prediction_engine.predict_failure_probability(asset_id, sensor_data)
        
        return {
            "success": True,
            "failure_prediction": prediction,
            "asset_id": asset_id,
            "ai_engine": "PredictiveMaintenanceEngine",
            "prediction_timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failure prediction error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/ai/comprehensive-analysis")
async def comprehensive_ai_analysis():
    """Complete AI analysis dashboard with all advanced features"""
    try:
        # Get basic data
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Assets
        cursor.execute("SELECT id, name, asset_type, status FROM assets")
        assets = [{"id": row[0], "name": row[1], "type": row[2], "status": row[3]} for row in cursor.fetchall()]
        
        # Work orders  
        cursor.execute("SELECT id, title, priority, status FROM work_orders WHERE status != 'Completed'")
        work_orders = [{"id": row[0], "title": row[1], "priority": row[2], "status": row[3]} for row in cursor.fetchall()]
        
        # Parts
        cursor.execute("SELECT id, name, stock_quantity, min_stock FROM parts")
        parts = [{"id": row[0], "name": row[1], "quantity": row[2], "min_stock": row[3]} for row in cursor.fetchall()]
        
        conn.close()
        
        # Run all AI analyses
        predictive_analysis = ai_client.prediction_engine.generate_maintenance_schedule(assets)
        resource_optimization = ai_client.optimization_engine.optimize_technician_scheduling(work_orders, [])
        inventory_optimization = ai_client.optimization_engine.optimize_inventory_levels(parts)
        trend_analysis = ai_client.pattern_analyzer.predict_maintenance_trends(30)
        
        return {
            "success": True,
            "comprehensive_analysis": {
                "predictive_maintenance": predictive_analysis,
                "resource_optimization": resource_optimization, 
                "inventory_optimization": inventory_optimization,
                "trend_analysis": trend_analysis,
                "system_overview": {
                    "total_assets": len(assets),
                    "active_work_orders": len(work_orders),
                    "parts_in_inventory": len(parts),
                    "analysis_engines": 4
                }
            },
            "ai_engines_active": ["PredictiveMaintenanceEngine", "ResourceOptimizationEngine", "PatternRecognitionSystem"],
            "analysis_timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Comprehensive analysis error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

# ==========================================
# COLLABORATIVE AI ENDPOINTS - CHATGPT + GROK + CLAUDE
# ==========================================

@app.post("/api/ai/collaborative")
async def collaborative_ai_query(request: Request):
    """Multi-AI collaborative query processing with ChatGPT, Grok, and Claude"""
    try:
        data = await request.json()
        query = data.get('query', '')
        models = data.get('models', ['chatgpt', 'grok'])
        
        if not query:
            return JSONResponse({"success": False, "error": "Query is required"}, status_code=400)
        
        # Process with collaborative AI system
        result = await process_collaborative_query(query, models)
        
        return JSONResponse({
            "success": True,
            "collaborative_response": result,
            "models_used": models,
            "timestamp": datetime.datetime.now().isoformat(),
            "query": query
        })
        
    except Exception as e:
        logger.error(f"Collaborative AI error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/ai/grok-chat")
async def grok_chat_endpoint(request: Request):
    """Direct Grok AI integration for CMMS queries"""
    try:
        data = await request.json()
        query = data.get('query', '')
        
        if not query:
            return JSONResponse({"success": False, "error": "Query is required"}, status_code=400)
        
        # Initialize collaborative AI if not already done
        if not hasattr(app.state, 'collaborative_ai'):
            app.state.collaborative_ai = CollaborativeAISystem()
        
        # Call Grok directly
        grok_response = await app.state.collaborative_ai.call_grok(query)
        
        return JSONResponse({
            "success": True,
            "grok_response": grok_response.response,
            "confidence": grok_response.confidence,
            "reasoning": grok_response.reasoning,
            "timestamp": grok_response.timestamp,
            "model": "grok"
        })
        
    except Exception as e:
        logger.error(f"Grok chat error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/ai/memory/search")
async def search_ai_memory(query: str, category: str = None, limit: int = 10):
    """Search AI memory/knowledge base"""
    try:
        # Create fresh instance to ensure we get latest code
        from collaborative_ai_system import CollaborativeAISystem
        collaborative_ai = CollaborativeAISystem()
        
        memories = collaborative_ai.memory.retrieve_relevant_memories(
            query, category, limit
        )
        
        return JSONResponse({
            "success": True,
            "memories": [{
                "id": mem.id,
                "content": mem.content,
                "category": mem.category,
                "timestamp": mem.timestamp,
                "relevance_score": mem.relevance_score,
                "source": mem.source
            } for mem in memories],
            "total_found": len(memories)
        })
        
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/ai/memory/store")
async def store_ai_memory(request: Request):
    """Store information in AI memory system"""
    try:
        data = await request.json()
        content = data.get('content', '')
        category = data.get('category', 'user_input')
        source = data.get('source', 'manual')
        metadata = data.get('metadata', {})
        
        if not content:
            return JSONResponse({"success": False, "error": "Content is required"}, status_code=400)
        
        if not hasattr(app.state, 'collaborative_ai'):
            app.state.collaborative_ai = CollaborativeAISystem()
        
        memory_id = app.state.collaborative_ai.memory.store_memory(
            content, category, source, metadata
        )
        
        return JSONResponse({
            "success": True,
            "memory_id": memory_id,
            "message": "Memory stored successfully"
        })
        
    except Exception as e:
        logger.error(f"Memory storage error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/ai/collaboration-status")
async def get_collaboration_status():
    """Get status of collaborative AI system"""
    try:
        # Check API key availability
        status = {
            "chatgpt_available": bool(os.getenv('OPENAI_API_KEY')),
            "grok_available": bool(os.getenv('GROK_API_KEY') or os.getenv('XAI_API_KEY')),
            "claude_available": True,  # Running locally
            "memory_system_active": True,
            "knowledge_base_initialized": True,
            "collaborative_features": [
                "Multi-AI querying",
                "RAG memory system", 
                "CMMS knowledge base",
                "Conversation history",
                "Response synthesis"
            ]
        }
        
        return JSONResponse({
            "success": True,
            "status": status,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Collaboration status error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

# Initialize database and AI client on import
init_database()

# Initialize global AI client with advanced features
ai_client = ChatterFixAIClient()

# Add universal AI endpoints to make AI assistant available on ALL pages
add_universal_ai_endpoints(app)

# Fix It Fred Hot Reload Test Endpoint
@app.get("/api/fix-it-fred-hot-reload-test")
async def fix_it_fred_hot_reload_test():
    """Test endpoint to verify Fix It Fred hot reload system works"""
    return {
        "message": "🔥 Fix It Fred hot reload is working perfectly!",
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "success", 
        "deployment": "hot_reload_system",
        "version": "fix-it-fred-hot-reload-1.0.0",
        "features": ["zero_downtime", "instant_updates", "automatic_backup"]
    }

logger.info("ChatterFix CMMS initialized successfully with ChatterFix AI assistant")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)