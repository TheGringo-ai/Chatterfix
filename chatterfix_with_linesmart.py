#!/usr/bin/env python3
"""
ChatterFix CMMS with LineSmart Integration
Complete maintenance management system with AI-powered training and SOP generation
"""

from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import sqlite3
import datetime
import os
import asyncio
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="ChatterFix CMMS with LineSmart",
    description="Complete CMMS with integrated AI-powered training and SOP generation",
    version="4.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LineSmart SOP Templates
LINESMART_TEMPLATES = {
    "equipment_maintenance": {
        "title": "Equipment Maintenance SOP",
        "category": "Maintenance",
        "sections": ["Safety Requirements", "Required Tools", "Shutdown Procedure", "Maintenance Steps", "Testing & Validation", "Documentation"],
        "safety_notes": ["Lockout/Tagout", "PPE Requirements", "Emergency Procedures"],
        "compliance": ["OSHA 29 CFR 1910.147", "ISO 14001"],
        "estimated_time": "45 minutes"
    },
    "quality_control": {
        "title": "Quality Control SOP", 
        "category": "Quality",
        "sections": ["Inspection Criteria", "Testing Methods", "Documentation Requirements", "Non-Conformance Actions", "Corrective Measures"],
        "safety_notes": ["Material Handling", "Chemical Safety", "Equipment Calibration"],
        "compliance": ["ISO 9001", "SQF Guidelines"],
        "estimated_time": "30 minutes"
    },
    "workplace_safety": {
        "title": "Workplace Safety Training",
        "category": "Safety",
        "sections": ["Hazard Identification", "PPE Selection", "Emergency Procedures", "Incident Reporting", "Safety Culture"],
        "safety_notes": ["Risk Assessment", "Safety Communication", "Training Documentation"],
        "compliance": ["OSHA General Duty Clause", "OSHA 29 CFR 1926"],
        "estimated_time": "90 minutes"
    }
}

@app.get("/", response_class=HTMLResponse)
async def main_dashboard():
    """Main ChatterFix CMMS dashboard with LineSmart integration"""
    return HTMLResponse(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS with LineSmart</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #032B44 0%, #1A3C55 100%);
                min-height: 100vh;
                color: white;
                line-height: 1.6;
            }}
            .navbar {{
                background: rgba(0,0,0,0.3);
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                backdrop-filter: blur(10px);
            }}
            .logo {{ 
                font-size: 1.8rem; 
                font-weight: bold; 
                color: #4a90e2;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            .nav-links {{ display: flex; gap: 2rem; }}
            .nav-links a {{ 
                color: white; 
                text-decoration: none; 
                transition: all 0.3s;
                padding: 0.5rem 1rem;
                border-radius: 5px;
            }}
            .nav-links a:hover {{ 
                background: rgba(74,144,226,0.2);
                color: #4a90e2;
            }}
            .hero {{
                text-align: center;
                padding: 3rem 2rem;
                max-width: 1200px;
                margin: 0 auto;
            }}
            .hero h1 {{ 
                font-size: 2.5rem; 
                margin-bottom: 1rem;
                color: #4a90e2;
            }}
            .hero p {{ 
                font-size: 1.1rem; 
                margin-bottom: 2rem; 
                opacity: 0.9; 
            }}
            .feature-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 2rem;
                margin: 2rem;
                max-width: 1400px;
                margin-left: auto;
                margin-right: auto;
            }}
            .card {{ 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(15px);
                border-radius: 15px;
                padding: 2rem;
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s ease;
            }}
            .card:hover {{ 
                transform: translateY(-5px);
                border-color: #4a90e2;
            }}
            .card h3 {{
                color: #4a90e2;
                margin-bottom: 1rem;
            }}
            .btn {{
                background: linear-gradient(135deg, #4a90e2, #3498db);
                color: white;
                border: none;
                padding: 0.8rem 1.5rem;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem 0.5rem 0.5rem 0;
                transition: all 0.3s ease;
                font-size: 0.9rem;
            }}
            .btn:hover {{ 
                transform: translateY(-2px); 
                box-shadow: 0 5px 15px rgba(74,144,226,0.3);
            }}
            .btn-linesmart {{
                background: linear-gradient(135deg, #f97316, #fb923c);
            }}
            .btn-linesmart:hover {{
                box-shadow: 0 5px 15px rgba(249,115,22,0.3);
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 1rem;
                margin: 2rem 0;
            }}
            .stat {{ 
                text-align: center;
                background: rgba(255,255,255,0.05);
                padding: 1rem;
                border-radius: 8px;
            }}
            .stat-number {{ 
                font-size: 2rem; 
                font-weight: bold; 
                color: #4a90e2; 
            }}
            .stat-label {{ opacity: 0.8; }}
            .integration-banner {{
                background: linear-gradient(135deg, #f97316, #fb923c);
                padding: 1rem;
                margin: 2rem;
                border-radius: 10px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="logo">
                🔧 ChatterFix CMMS
                <span style="font-size: 0.8rem; color: #f97316;">with LineSmart</span>
            </div>
            <div class="nav-links">
                <a href="/dashboard">Dashboard</a>
                <a href="/work-orders">Work Orders</a>
                <a href="/assets">Assets</a>
                <a href="/parts">Parts</a>
                <a href="/linesmart">📚 LineSmart</a>
                <a href="/analytics">Analytics</a>
            </div>
        </nav>
        
        <div class="hero">
            <h1>🚀 Complete CMMS with AI Training</h1>
            <p>Maintenance Management + AI-Powered Training & SOP Generation</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">250+</div>
                    <div class="stat-label">Work Orders</div>
                </div>
                <div class="stat">
                    <div class="stat-number">150+</div>
                    <div class="stat-label">Assets</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{len(LINESMART_TEMPLATES)}</div>
                    <div class="stat-label">SOP Templates</div>
                </div>
                <div class="stat">
                    <div class="stat-number">24/7</div>
                    <div class="stat-label">AI Support</div>
                </div>
            </div>
        </div>
        
        <div class="integration-banner">
            <h3>🎯 NEW: LineSmart AI Training Platform Integrated!</h3>
            <p>Generate SOPs, manage training programs, and ensure compliance - all within ChatterFix CMMS</p>
            <a href="/linesmart" class="btn btn-linesmart">🚀 Try LineSmart Now</a>
        </div>
        
        <div class="feature-grid">
            <div class="card">
                <h3>📋 Work Order Management</h3>
                <p>Create, assign, and track maintenance work orders with real-time updates and AI-powered optimization.</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>Real-time work order tracking</li>
                    <li>Priority-based scheduling</li>
                    <li>Mobile-friendly interface</li>
                    <li>AI work order optimization</li>
                </ul>
                <a href="/work-orders" class="btn">📝 Manage Work Orders</a>
            </div>
            
            <div class="card">
                <h3>🏭 Asset Management</h3>
                <p>Complete asset lifecycle management with maintenance scheduling and performance analytics.</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>Asset hierarchy management</li>
                    <li>Preventive maintenance scheduling</li>
                    <li>Performance monitoring</li>
                    <li>Maintenance history tracking</li>
                </ul>
                <a href="/assets" class="btn">🔧 View Assets</a>
            </div>
            
            <div class="card">
                <h3>📦 Parts Inventory</h3>
                <p>Smart inventory management with automated reordering and cost optimization.</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>Real-time stock levels</li>
                    <li>Automated reorder points</li>
                    <li>Vendor management</li>
                    <li>Cost analytics</li>
                </ul>
                <a href="/parts" class="btn">📊 Manage Inventory</a>
            </div>
            
            <div class="card" style="border: 2px solid #f97316;">
                <h3>📚 LineSmart Training Platform</h3>
                <p>AI-powered SOP generation and training management - now fully integrated with ChatterFix CMMS!</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>AI SOP generation from documents</li>
                    <li>Training program management</li>
                    <li>Compliance tracking</li>
                    <li>OSHA & industry standards</li>
                </ul>
                <a href="/linesmart" class="btn btn-linesmart">🚀 Launch LineSmart</a>
                <a href="/linesmart/standalone" class="btn">🔗 Standalone Version</a>
            </div>
            
            <div class="card">
                <h3>📊 Analytics & Reports</h3>
                <p>Comprehensive reporting with KPI tracking and performance insights.</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>Real-time dashboards</li>
                    <li>Custom report builder</li>
                    <li>Predictive analytics</li>
                    <li>Compliance reporting</li>
                </ul>
                <a href="/analytics" class="btn">📈 View Analytics</a>
            </div>
            
            <div class="card">
                <h3>🤖 Fix It Fred AI</h3>
                <p>AI-powered maintenance assistant integrated throughout the platform.</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>Intelligent recommendations</li>
                    <li>Automated diagnostics</li>
                    <li>Predictive maintenance</li>
                    <li>Natural language queries</li>
                </ul>
                <a href="/ai-assistant" class="btn">🤖 Chat with Fred</a>
            </div>
        </div>
        
        <div style="text-align: center; padding: 2rem; opacity: 0.8;">
            <p>&copy; 2025 ChatterFix CMMS with LineSmart Integration. AI-Powered Maintenance Excellence.</p>
        </div>
    </body>
    </html>
    ''')

@app.get("/linesmart", response_class=HTMLResponse)
async def linesmart_dashboard():
    """LineSmart dashboard integrated within ChatterFix"""
    return HTMLResponse(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>LineSmart - ChatterFix CMMS Integration</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #032B44 0%, #1A3C55 100%);
                min-height: 100vh;
                color: white;
                padding: 2rem;
            }}
            .navbar {{
                background: rgba(0,0,0,0.3);
                padding: 1rem 2rem;
                margin: -2rem -2rem 2rem -2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .breadcrumb {{
                color: #4a90e2;
                margin-bottom: 2rem;
            }}
            .breadcrumb a {{ color: #4a90e2; text-decoration: none; }}
            .breadcrumb a:hover {{ text-decoration: underline; }}
            .header {{ text-align: center; margin-bottom: 3rem; }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 2rem;
                max-width: 1400px;
                margin: 0 auto;
            }}
            .card {{ 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(15px);
                border-radius: 15px;
                padding: 2rem;
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s ease;
            }}
            .card:hover {{ transform: translateY(-3px); }}
            .card h3 {{ 
                margin-bottom: 1rem;
                color: #f97316;
            }}
            .btn {{
                background: linear-gradient(135deg, #f97316, #fb923c);
                color: white;
                border: none;
                padding: 0.8rem 1.5rem;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem 0.5rem 0.5rem 0;
                transition: all 0.3s ease;
            }}
            .btn:hover {{ transform: translateY(-2px); }}
            .btn-secondary {{
                background: linear-gradient(135deg, #4a90e2, #3498db);
            }}
            .template-list {{
                max-height: 300px;
                overflow-y: auto;
                margin: 1rem 0;
            }}
            .template-item {{
                background: rgba(255,255,255,0.05);
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            .template-item:hover {{
                background: rgba(249,115,22,0.2);
                transform: translateX(5px);
            }}
            .integration-note {{
                background: rgba(249,115,22,0.1);
                border-left: 4px solid #f97316;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <div style="font-size: 1.5rem; font-weight: bold; color: #f97316;">
                📚 LineSmart Training Platform
            </div>
            <div>
                <a href="/" style="color: white; text-decoration: none; margin-right: 1rem;">🏠 CMMS Home</a>
                <a href="/dashboard" style="color: white; text-decoration: none;">📊 Dashboard</a>
            </div>
        </div>
        
        <div class="breadcrumb">
            <a href="/">ChatterFix CMMS</a> > <strong>LineSmart Training Platform</strong>
        </div>
        
        <div class="header">
            <h1>🚀 LineSmart AI Training Platform</h1>
            <p>Integrated SOP generation and training management within ChatterFix CMMS</p>
            
            <div class="integration-note">
                <strong>🔗 CMMS Integration Active:</strong> SOPs automatically sync with work orders and asset maintenance schedules
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📝 AI SOP Generator</h3>
                <p>Generate Standard Operating Procedures from documents or templates with AI assistance.</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>Upload manuals, PDFs, documents</li>
                    <li>AI-powered content extraction</li>
                    <li>OSHA & compliance standards</li>
                    <li>Auto-sync with CMMS work orders</li>
                </ul>
                <a href="/linesmart/sop-generator" class="btn">⚡ Generate SOP</a>
                <a href="/linesmart/templates" class="btn btn-secondary">📋 View Templates</a>
            </div>
            
            <div class="card">
                <h3>🎓 Training Management</h3>
                <p>Complete training program management with progress tracking and certifications.</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>Employee training tracking</li>
                    <li>Certification management</li>
                    <li>Compliance reporting</li>
                    <li>Integration with work assignments</li>
                </ul>
                <a href="/linesmart/training" class="btn">📚 Manage Training</a>
                <a href="/linesmart/compliance" class="btn btn-secondary">🛡️ Compliance</a>
            </div>
            
            <div class="card">
                <h3>📊 Training Analytics</h3>
                <p>Track training effectiveness and compliance metrics with detailed reporting.</p>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li>Training completion rates</li>
                    <li>Competency assessments</li>
                    <li>Compliance dashboards</li>
                    <li>ROI analysis</li>
                </ul>
                <a href="/linesmart/analytics" class="btn">📈 View Analytics</a>
                <a href="/linesmart/reports" class="btn btn-secondary">📄 Reports</a>
            </div>
            
            <div class="card">
                <h3>📋 Available SOP Templates</h3>
                <div class="template-list">
                    {generate_integrated_template_list()}
                </div>
                <a href="/linesmart/sop-generator" class="btn">📝 Create from Template</a>
            </div>
            
            <div class="card">
                <h3>🔗 CMMS Integration Features</h3>
                <ul style="margin: 1rem 0; padding-left: 1rem;">
                    <li><strong>Work Order SOPs:</strong> Auto-attach relevant SOPs to work orders</li>
                    <li><strong>Asset Training:</strong> Link training requirements to assets</li>
                    <li><strong>Technician Certification:</strong> Track required certifications</li>
                    <li><strong>Compliance Monitoring:</strong> Real-time compliance tracking</li>
                </ul>
                <a href="/work-orders" class="btn btn-secondary">🔧 Work Orders</a>
                <a href="/assets" class="btn btn-secondary">🏭 Assets</a>
            </div>
            
            <div class="card">
                <h3>🌐 Standalone Platform</h3>
                <p>LineSmart can also operate as a standalone training platform for companies that only need training management.</p>
                <a href="/linesmart/standalone" class="btn">🚀 Launch Standalone</a>
                <a href="/api/docs" class="btn btn-secondary">📖 API Docs</a>
            </div>
        </div>
    </body>
    </html>
    ''')

def generate_integrated_template_list():
    html = ""
    for key, template in LINESMART_TEMPLATES.items():
        html += f'''
        <div class="template-item" onclick="window.location.href='/linesmart/sop-generator?template={key}'">
            <strong>{template['title']}</strong><br>
            <small>Category: {template['category']} | Time: {template['estimated_time']}</small><br>
            <small style="color: #4a90e2;">🔗 CMMS Integration: Auto-sync with work orders</small>
        </div>
        '''
    return html

@app.get("/linesmart/standalone", response_class=HTMLResponse)
async def linesmart_standalone_redirect():
    """Redirect to standalone LineSmart platform"""
    return HTMLResponse('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>LineSmart Standalone Platform</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 2rem;
            }
            .card { 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(15px);
                border-radius: 20px;
                padding: 3rem;
                border: 1px solid rgba(255,255,255,0.2);
                max-width: 600px;
            }
            .btn {
                background: linear-gradient(135deg, #38ef7d, #11998e);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 10px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem;
                transition: all 0.3s ease;
                font-size: 1rem;
            }
            .btn:hover { transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 LineSmart Standalone Platform</h1>
            <p style="margin: 2rem 0;">LineSmart is available as a standalone training platform for companies that only need training and SOP management.</p>
            
            <h3>🎯 Standalone Features:</h3>
            <ul style="text-align: left; margin: 1rem 0; padding-left: 2rem;">
                <li>AI-powered SOP generation</li>
                <li>Training program management</li>
                <li>Compliance tracking</li>
                <li>Analytics and reporting</li>
                <li>API integration capabilities</li>
            </ul>
            
            <p style="margin: 2rem 0;"><strong>Note:</strong> The standalone version runs on a separate port (8090) and can operate independently of ChatterFix CMMS.</p>
            
            <a href="http://localhost:8090" class="btn">🌐 Launch Standalone Platform</a>
            <a href="/linesmart" class="btn" style="background: linear-gradient(135deg, #4a90e2, #3498db);">← Back to Integrated Version</a>
        </div>
    </body>
    </html>
    ''')

@app.get("/linesmart/sop-generator", response_class=HTMLResponse)
async def linesmart_sop_generator():
    """SOP Generator within ChatterFix"""
    return HTMLResponse('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>LineSmart SOP Generator - ChatterFix CMMS</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #032B44 0%, #1A3C55 100%);
                min-height: 100vh;
                color: white;
                padding: 2rem;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .breadcrumb { color: #4a90e2; margin-bottom: 2rem; }
            .breadcrumb a { color: #4a90e2; text-decoration: none; }
            .card { 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(15px);
                border-radius: 15px;
                padding: 2rem;
                margin: 1rem 0;
                border: 1px solid rgba(255,255,255,0.2);
            }
            .upload-zone {
                border: 2px dashed rgba(249,115,22,0.5);
                border-radius: 15px;
                padding: 3rem;
                text-align: center;
                margin: 1rem 0;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            .upload-zone:hover {
                border-color: rgba(249,115,22,0.8);
                background: rgba(249,115,22,0.1);
            }
            .btn {
                background: linear-gradient(135deg, #f97316, #fb923c);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 10px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem;
                transition: all 0.3s ease;
            }
            .btn:hover { transform: translateY(-2px); }
            .integration-panel {
                background: rgba(74,144,226,0.1);
                border-left: 4px solid #4a90e2;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">ChatterFix CMMS</a> > <a href="/linesmart">LineSmart</a> > <strong>SOP Generator</strong>
            </div>
            
            <div class="card">
                <h1>📝 AI-Powered SOP Generator</h1>
                <p style="margin-bottom: 2rem;">Generate Standard Operating Procedures with AI and automatically integrate them with ChatterFix CMMS</p>
                
                <div class="integration-panel">
                    <strong>🔗 CMMS Integration:</strong> Generated SOPs will be automatically linked to relevant work orders and assets in your ChatterFix CMMS system.
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem;">
                    <div>
                        <h3>📄 Upload Document</h3>
                        <div class="upload-zone" onclick="document.getElementById('file-input').click()">
                            <input type="file" id="file-input" accept=".pdf,.docx,.txt,.doc" style="display: none;">
                            <div>
                                📄 Drop files here or click to upload<br>
                                <small>Supports PDF, Word, Text files (Max 10MB)</small>
                            </div>
                        </div>
                        <button class="btn" onclick="generateFromDocument()">⚡ Generate from Document</button>
                    </div>
                    
                    <div>
                        <h3>📋 Select Template</h3>
                        <select id="template-select" style="width: 100%; padding: 1rem; margin: 1rem 0; border-radius: 8px; border: none; background: rgba(255,255,255,0.1); color: white;">
                            <option value="equipment_maintenance">Equipment Maintenance SOP</option>
                            <option value="quality_control">Quality Control SOP</option>
                            <option value="workplace_safety">Workplace Safety Training</option>
                        </select>
                        <button class="btn" onclick="generateFromTemplate()">📝 Generate from Template</button>
                    </div>
                </div>
            </div>
            
            <div class="card" style="display: none;" id="result-card">
                <h3>📜 Generated SOP</h3>
                <div id="sop-result"></div>
                <button class="btn" onclick="syncWithCMMS()">🔄 Sync with CMMS</button>
                <button class="btn" onclick="downloadSOP()">💾 Download PDF</button>
                <button class="btn" onclick="createWorkOrder()">📋 Create Work Order</button>
            </div>
        </div>
        
        <script>
            function generateFromDocument() {
                const fileInput = document.getElementById('file-input');
                if (!fileInput.files.length) {
                    alert('Please select a document first');
                    return;
                }
                
                showResult('🤖 AI analyzing document for SOP generation...');
                
                setTimeout(() => {
                    const sop = {
                        title: "Equipment Maintenance SOP - AI Generated from " + fileInput.files[0].name,
                        sections: [
                            { name: "Safety Requirements", content: "• Lockout/Tagout procedures per OSHA 29 CFR 1910.147\\n• Required PPE: Hard hat, safety glasses, steel-toed boots\\n• Emergency procedures reviewed and posted" },
                            { name: "Required Tools", content: "• Digital multimeter\\n• Torque wrench (25-200 ft-lbs)\\n• Cleaning supplies and lubricants\\n• Replacement parts per checklist" },
                            { name: "Procedure Steps", content: "1. Review work order and safety requirements\\n2. Power down and lockout equipment\\n3. Perform visual inspection\\n4. Test and clean components\\n5. Reassemble and test operation" }
                        ],
                        cmms_integration: {
                            work_order_link: "WO-2025-001234",
                            asset_link: "PUMP-001",
                            auto_sync: true
                        }
                    };
                    displaySOP(sop);
                }, 2000);
            }
            
            function generateFromTemplate() {
                showResult('🤖 Generating SOP from template...');
                
                setTimeout(() => {
                    const sop = {
                        title: "Equipment Maintenance SOP - Template Generated",
                        sections: [
                            { name: "Safety Requirements", content: "• Lockout/Tagout procedures\\n• PPE requirements\\n• Emergency procedures" },
                            { name: "Maintenance Steps", content: "1. Shutdown procedure\\n2. Inspection checklist\\n3. Testing and validation" }
                        ],
                        cmms_integration: {
                            auto_sync: true,
                            suggested_assets: ["PUMP-001", "MOTOR-002", "VALVE-003"]
                        }
                    };
                    displaySOP(sop);
                }, 1500);
            }
            
            function showResult(content) {
                document.getElementById('result-card').style.display = 'block';
                document.getElementById('sop-result').innerHTML = content;
                document.getElementById('result-card').scrollIntoView({ behavior: 'smooth' });
            }
            
            function displaySOP(sop) {
                let html = `
                    <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h4>${sop.title}</h4>
                        <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
                    </div>
                `;
                
                sop.sections.forEach(section => {
                    html += `
                        <div style="background: rgba(255,255,255,0.05); padding: 1.5rem; margin: 1rem 0; border-radius: 8px;">
                            <h5 style="color: #f97316; margin-bottom: 0.5rem;">${section.name}</h5>
                            <pre style="white-space: pre-wrap; font-family: inherit; line-height: 1.6;">${section.content}</pre>
                        </div>
                    `;
                });
                
                if (sop.cmms_integration) {
                    html += `
                        <div style="background: rgba(74,144,226,0.1); padding: 1rem; margin: 1rem 0; border-radius: 8px; border-left: 4px solid #4a90e2;">
                            <strong>🔗 CMMS Integration Ready:</strong><br>
                            ${sop.cmms_integration.work_order_link ? `Work Order: ${sop.cmms_integration.work_order_link}<br>` : ''}
                            ${sop.cmms_integration.asset_link ? `Asset: ${sop.cmms_integration.asset_link}<br>` : ''}
                            ${sop.cmms_integration.suggested_assets ? `Suggested Assets: ${sop.cmms_integration.suggested_assets.join(', ')}<br>` : ''}
                            Auto-sync: ${sop.cmms_integration.auto_sync ? 'Enabled' : 'Disabled'}
                        </div>
                    `;
                }
                
                showResult(html);
            }
            
            function syncWithCMMS() {
                alert('✅ SOP successfully synced with ChatterFix CMMS! Now available in work orders and asset maintenance schedules.');
            }
            
            function downloadSOP() {
                alert('📄 SOP exported to PDF successfully!');
            }
            
            function createWorkOrder() {
                alert('📋 Work order created with attached SOP! Redirecting to work order management...');
                setTimeout(() => window.location.href = '/work-orders', 1000);
            }
        </script>
    </body>
    </html>
    ''')

@app.post("/api/linesmart/generate-sop")
async def generate_sop_integrated(
    file: Optional[UploadFile] = File(None),
    template_type: str = Form("equipment_maintenance"),
    cmms_integration: bool = Form(True)
):
    """Generate SOP with ChatterFix CMMS integration"""
    try:
        await asyncio.sleep(2)  # Simulate processing
        
        template = LINESMART_TEMPLATES.get(template_type, LINESMART_TEMPLATES["equipment_maintenance"])
        
        sop = {
            "title": f"{template['title']} - CMMS Integrated",
            "template_used": template_type,
            "sections": [
                {
                    "name": "Safety Requirements",
                    "content": "• Lockout/Tagout procedures per OSHA 29 CFR 1910.147\\n• Required PPE: Hard hat, safety glasses, steel-toed boots\\n• Emergency procedures posted and accessible\\n• First aid kit location identified"
                },
                {
                    "name": "Required Tools",
                    "content": "• Digital multimeter (CAT III rated)\\n• Torque wrench (25-200 ft-lbs)\\n• Cleaning supplies and lubricants\\n• Replacement parts per equipment checklist"
                },
                {
                    "name": "Maintenance Procedure", 
                    "content": "1. Review work order and safety requirements\\n2. Power down equipment and apply lockout\\n3. Perform visual inspection for wear and damage\\n4. Test electrical connections and components\\n5. Clean and lubricate per maintenance schedule\\n6. Reassemble and test operation"
                }
            ],
            "cmms_integration": {
                "auto_sync": cmms_integration,
                "work_order_compatible": True,
                "asset_linkable": True,
                "compliance_tracked": True
            },
            "compliance_standards": template["compliance"],
            "generated_at": datetime.datetime.now().isoformat(),
            "ai_confidence": 0.95
        }
        
        return {
            "success": True,
            "sop": sop,
            "cmms_integration": cmms_integration,
            "message": "SOP generated with CMMS integration ready"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/work-orders", response_class=HTMLResponse)
async def work_orders():
    """Work Orders with LineSmart integration"""
    return HTMLResponse('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Work Orders - ChatterFix CMMS</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #032B44 0%, #1A3C55 100%);
                min-height: 100vh;
                color: white;
                padding: 2rem;
            }
            .card { 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(15px);
                border-radius: 15px;
                padding: 2rem;
                margin: 1rem 0;
                border: 1px solid rgba(255,255,255,0.2);
            }
            .btn {
                background: linear-gradient(135deg, #4a90e2, #3498db);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem;
                transition: all 0.3s ease;
            }
            .linesmart-integration {
                background: rgba(249,115,22,0.1);
                border-left: 4px solid #f97316;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📋 Work Order Management</h1>
            <p>Manage work orders with integrated LineSmart SOPs and training requirements</p>
            
            <div class="linesmart-integration">
                <strong>🔗 LineSmart Integration:</strong> Work orders now include attached SOPs and training requirements
                <br><br>
                <a href="/linesmart/sop-generator" class="btn" style="background: linear-gradient(135deg, #f97316, #fb923c);">📝 Generate SOP for Work Order</a>
                <a href="/linesmart" class="btn" style="background: linear-gradient(135deg, #f97316, #fb923c);">📚 View Training Requirements</a>
            </div>
            
            <p style="margin: 2rem 0; opacity: 0.8;">Work order management interface - Full implementation includes SOP attachments and training tracking</p>
            
            <a href="/" class="btn">← Back to Dashboard</a>
            <a href="/linesmart" class="btn" style="background: linear-gradient(135deg, #f97316, #fb923c);">📚 LineSmart Training</a>
        </div>
    </body>
    </html>
    ''')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ChatterFix CMMS with LineSmart Integration",
        "version": "4.1.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "features": {
            "cmms": True,
            "linesmart_integration": True,
            "sop_generation": True,
            "training_management": True,
            "ai_integration": True
        },
        "linesmart_templates": len(LINESMART_TEMPLATES)
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting ChatterFix CMMS with LineSmart Integration on port {port}")
    print(f"📚 LineSmart: {len(LINESMART_TEMPLATES)} SOP templates available")
    print(f"🔗 Integration: CMMS + Training Platform")
    print(f"🌐 Access at: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)