#!/usr/bin/env python3
"""
ChatterFix CMMS - Complete AI-Enhanced Maintenance Management System
Main Application with ChatterFix Specific AI (No external dependencies)
"""

import logging
import sqlite3
from datetime import datetime
import os

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

# Import universal AI endpoints
from universal_ai_endpoints import add_universal_ai_endpoints
# Import unified styles, fallback to inline if not available
try:
    from unified_cmms_system import get_unified_styles
except ImportError:
    from typing import Literal

    def get_unified_styles() -> Literal["""
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #5a6fd8; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        """]:
        return """
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #5a6fd8; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .table { background: rgba(255,255,255,0.1); border-radius: 10px; padding: 20px; margin: 20px 0; }
        .card { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; margin: 10px; }
        .alert { padding: 15px; border-radius: 5px; margin: 10px 0; }
        .alert-info { background: rgba(52, 152, 219, 0.2); border-left: 4px solid #3498db; }
        .alert-warning { background: rgba(243, 156, 18, 0.2); border-left: 4px solid #f39c12; }
        .alert-danger { background: rgba(231, 76, 60, 0.2); border-left: 4px solid #e74c3c; }
        """

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="ChatterFix CMMS", description="Complete Maintenance Management System")

# Database configuration
DATABASE_PATH = "/var/lib/chatterfix/cmms.db"
BACKUP_DATABASE_PATH = "/opt/chatterfix-cmms/data/cmms.db"

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

def init_database():
    """Initialize SQLite database with required tables"""
    ensure_database_dir()
    
    conn = sqlite3.connect(DATABASE_PATH)
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

class ChatterFixAIClient:
    """ChatterFix CMMS AI Assistant - No external dependencies needed"""
    
    def __init__(self):
        """Initialize ChatterFix AI with built-in CMMS intelligence"""
        self.system_name = "ChatterFix CMMS AI Assistant"
        logger.info("ChatterFix AI Assistant initialized with built-in CMMS intelligence")
    
    async def query(self, prompt: str, context: str = "") -> str:
        """Generate ChatterFix CMMS-specific responses"""
        try:
            return self.get_chatterfix_response(prompt, context)
        except Exception as e:
            logger.error(f"ChatterFix AI error: {e}")
            return "I'm here to help with your ChatterFix CMMS operations. Please try rephrasing your question."
    
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
        conn = sqlite3.connect(DATABASE_PATH)
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
        conn = sqlite3.connect(DATABASE_PATH)
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
async def dashboard():
    """Main dashboard with system overview"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
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
            <title>ChatterFix CMMS Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{styles}</style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 ChatterFix CMMS Dashboard</h1>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;">
                    <div class="card">
                        <h3>📋 Open Work Orders</h3>
                        <h2>{open_orders}</h2>
                    </div>
                    <div class="card">
                        <h3>✅ Completed Today</h3>
                        <h2>{completed_today}</h2>
                    </div>
                    <div class="card">
                        <h3>🚨 Critical Orders</h3>
                        <h2>{critical_orders}</h2>
                    </div>
                    <div class="card">
                        <h3>🏭 Active Assets</h3>
                        <h2>{active_assets}</h2>
                    </div>
                </div>
                
                <div class="table">
                    <h3>Recent Work Orders</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.3);">
                                <th style="text-align: left; padding: 10px;">ID</th>
                                <th style="text-align: left; padding: 10px;">Title</th>
                                <th style="text-align: left; padding: 10px;">Priority</th>
                                <th style="text-align: left; padding: 10px;">Status</th>
                                <th style="text-align: left; padding: 10px;">Created</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for order in recent_orders:
            priority_color = {
                'Critical': '#e74c3c',
                'High': '#f39c12', 
                'Medium': '#3498db',
                'Low': '#2ecc71'
            }.get(order[2], '#3498db')
            
            html_content += f"""
                            <tr>
                                <td style="padding: 10px;">#{order[0]}</td>
                                <td style="padding: 10px;">{order[1]}</td>
                                <td style="padding: 10px; color: {priority_color};">●{order[2]}</td>
                                <td style="padding: 10px;">{order[3]}</td>
                                <td style="padding: 10px;">{order[4][:10]}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;">
                    <a href="/work-orders" class="btn btn-primary" style="text-decoration: none; text-align: center; display: block;">
                        📋 Work Orders
                    </a>
                    <a href="/assets" class="btn btn-primary" style="text-decoration: none; text-align: center; display: block;">
                        🏭 Assets
                    </a>
                    <a href="/parts" class="btn btn-primary" style="text-decoration: none; text-align: center; display: block;">
                        📦 Parts
                    </a>
                    <a href="/maintenance" class="btn btn-primary" style="text-decoration: none; text-align: center; display: block;">
                        🔄 Maintenance
                    </a>
                </div>
            </div>
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
            <div class="container">
                <h1>📋 Work Orders Management</h1>
                <div style="margin: 20px 0;">
                    <a href="/" class="btn">← Dashboard</a>
                    <button class="btn btn-primary" style="margin-left: 10px;">+ Create New Work Order</button>
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
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <td style="padding: 10px;">#{order[0]}</td>
                                <td style="padding: 10px;"><strong>{order[1]}</strong><br><small>{order[2][:50]}...</small></td>
                                <td style="padding: 10px; color: {priority_color};">●{order[4]}</td>
                                <td style="padding: 10px; color: {status_color};">●{order[3]}</td>
                                <td style="padding: 10px;">{order[5] or 'Unassigned'}</td>
                                <td style="padding: 10px;">{order[6][:10]}</td>
                                <td style="padding: 10px;">{order[7][:10] if order[7] else 'Not set'}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
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
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, type, location, manufacturer, model, status, criticality, last_maintenance
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
            <div class="container">
                <h1>🏭 Asset Management</h1>
                <div style="margin: 20px 0;">
                    <a href="/" class="btn">← Dashboard</a>
                    <button class="btn btn-primary" style="margin-left: 10px;">+ Add New Asset</button>
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
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <td style="padding: 10px;">#{asset[0]}</td>
                                <td style="padding: 10px;"><strong>{asset[1]}</strong></td>
                                <td style="padding: 10px;">{asset[2] or 'N/A'}</td>
                                <td style="padding: 10px;">{asset[3] or 'N/A'}</td>
                                <td style="padding: 10px;">{asset[4] or 'N/A'} {asset[5] or ''}</td>
                                <td style="padding: 10px; color: {status_color};">●{asset[6]}</td>
                                <td style="padding: 10px; color: {criticality_color};">●{asset[7]}</td>
                                <td style="padding: 10px;">{asset[8][:10] if asset[8] else 'Never'}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
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
        conn = sqlite3.connect(DATABASE_PATH)
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
            <div class="container">
                <h1>📦 Parts Inventory</h1>
                <div style="margin: 20px 0;">
                    <a href="/" class="btn">← Dashboard</a>
                    <button class="btn btn-primary" style="margin-left: 10px;">+ Add New Part</button>
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
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for part in parts:
            stock_status = 'low' if part[4] <= part[5] else 'ok'
            stock_color = '#e74c3c' if stock_status == 'low' else '#2ecc71'
            
            html_content += f"""
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <td style="padding: 10px;"><strong>{part[1]}</strong></td>
                                <td style="padding: 10px;">{part[2]}</td>
                                <td style="padding: 10px;">{part[3] or 'General'}</td>
                                <td style="padding: 10px; color: {stock_color};">{part[4]}</td>
                                <td style="padding: 10px;">{part[5]}</td>
                                <td style="padding: 10px;">${part[6]:.2f if part[6] else 0.00}</td>
                                <td style="padding: 10px;">{part[7] or 'N/A'}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
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
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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
            "timestamp": datetime.now().isoformat(),
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
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "ai_assistant": "active"
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
            return {"status": "ready", "timestamp": datetime.now().isoformat()}
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

@app.get("/ready")
async def ready_check():
    """Readiness endpoint alias for service compatibility"""
    return await readiness_check()

# Initialize database and AI client on import
init_database()

# Add universal AI endpoints to make AI assistant available on ALL pages
add_universal_ai_endpoints(app)

logger.info("ChatterFix CMMS initialized successfully with ChatterFix AI assistant")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)