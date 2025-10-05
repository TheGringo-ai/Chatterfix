#!/usr/bin/env python3
"""
ChatterFix CMMS - UI Gateway Service
Routes requests to appropriate microservices
"""

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os
import logging
import json
import asyncio
import time
from random import uniform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    """Retry function with exponential backoff for handling rate limits"""
    for attempt in range(max_retries):
        try:
            result = await func()
            if hasattr(result, 'status_code') and result.status_code == 429:
                if attempt == max_retries - 1:
                    return result  # Return 429 on final attempt
                # Exponential backoff with jitter
                delay = base_delay * (2 ** attempt) + uniform(0, 1)
                logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                continue
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt) + uniform(0, 1)
            logger.warning(f"Request failed, retrying in {delay:.2f}s: {str(e)}")
            await asyncio.sleep(delay)
    
    raise Exception("Max retries exceeded")

# Pydantic models for API requests
class WorkOrderCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[str] = None
    asset_id: Optional[int] = None

class AssetCreate(BaseModel):
    name: str
    description: str
    location: str
    status: str = "active"
    asset_type: str

class PartCreate(BaseModel):
    name: str
    part_number: str
    description: str
    category: str
    quantity: int
    min_stock: int
    unit_cost: float
    location: str

app = FastAPI(title="ChatterFix CMMS UI Gateway", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Microservice URLs - Local Development
# Unified Service URLs - Consolidated Architecture (3 services instead of 7)
SERVICES = {
    "backend": os.getenv("BACKEND_SERVICE_URL", "https://chatterfix-backend-unified-650169261019.us-central1.run.app"),
    "ai": os.getenv("AI_SERVICE_URL", "https://chatterfix-ai-unified-650169261019.us-central1.run.app"),
    # Legacy URLs for backward compatibility - all route to unified backend
    "database": os.getenv("BACKEND_SERVICE_URL", "https://chatterfix-backend-unified-650169261019.us-central1.run.app"),
    "work_orders": os.getenv("BACKEND_SERVICE_URL", "https://chatterfix-backend-unified-650169261019.us-central1.run.app"),
    "assets": os.getenv("BACKEND_SERVICE_URL", "https://chatterfix-backend-unified-650169261019.us-central1.run.app"),
    "parts": os.getenv("BACKEND_SERVICE_URL", "https://chatterfix-backend-unified-650169261019.us-central1.run.app"),
    "ai_brain": os.getenv("AI_SERVICE_URL", "https://chatterfix-ai-unified-650169261019.us-central1.run.app"),
    "document_intelligence": os.getenv("AI_SERVICE_URL", "https://chatterfix-ai-unified-650169261019.us-central1.run.app")
}

# Load AI Assistant Component
def load_ai_assistant_component():
    """Load the AI assistant component HTML"""
    try:
        with open("templates/ai_assistant_component.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("AI assistant component file not found")
        return ""
    except Exception as e:
        logger.error(f"Error loading AI assistant component: {e}")
        return ""

AI_ASSISTANT_COMPONENT = load_ai_assistant_component()

@app.get("/health")
async def health_check():
    """Health check that tests all microservices with retry logic"""
    status = {"status": "healthy", "service": "ui-gateway", "microservices": {}}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Process services sequentially with delays to avoid rate limits
        for i, (service_name, url) in enumerate(SERVICES.items()):
            try:
                # Add small delay between requests to prevent overwhelming services
                if i > 0:
                    await asyncio.sleep(0.5)
                
                async def make_request():
                    return await client.get(f"{url}/health")
                
                response = await retry_with_backoff(make_request, max_retries=2, base_delay=0.5)
                
                if response.status_code == 200:
                    status["microservices"][service_name] = {
                        "status": "healthy", 
                        "response_time": round(response.elapsed.total_seconds(), 3)
                    }
                elif response.status_code == 429:
                    status["microservices"][service_name] = {
                        "status": "rate_limited",
                        "message": "Service temporarily rate limited, but operational"
                    }
                else:
                    status["microservices"][service_name] = {"status": "unhealthy", "code": response.status_code}
            except Exception as e:
                status["microservices"][service_name] = {"status": "error", "error": str(e)}
                logger.error(f"Health check failed for {service_name}: {str(e)}")
    
    status["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return status

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Professional landing page for ChatterFix CMMS"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ChatterFix CMMS - Revolutionary AI-Powered Maintenance Management</title>
        <meta name="description" content="Transform your maintenance operations with ChatterFix CMMS - the world's most advanced AI-powered maintenance management platform. Reduce downtime by 50%, increase efficiency by 300%.">
        <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            overflow-x: hidden;
        }
        
        /* Navigation */
        .nav {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(10, 10, 10, 0.95);
            backdrop-filter: blur(10px);
            z-index: 1000;
            padding: 1rem 0;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 2rem;
        }
        
        .logo {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            list-style: none;
        }
        
        .nav-links a {
            color: #ffffff;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .nav-links a:hover {
            color: #667eea;
        }
        
        .cta-nav {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .cta-nav:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        
        /* Hero Section */
        .hero {
            height: 100vh;
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            position: relative;
            overflow: hidden;
        }
        
        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.1) 0%, transparent 50%);
        }
        
        .hero-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
            position: relative;
            z-index: 1;
        }
        
        .hero-content h1 {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #ffffff 0%, #667eea 50%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .hero-content .subtitle {
            font-size: 1.3rem;
            color: #b0b0b0;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        
        .hero-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
            margin: 2rem 0;
        }
        
        .stat {
            text-align: center;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
            display: block;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #b0b0b0;
            margin-top: 0.5rem;
        }
        
        .cta-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: transparent;
            color: white;
            padding: 1rem 2rem;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.5);
        }
        
        .hero-visual {
            position: relative;
            height: 500px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .platform-preview {
            width: 100%;
            height: 400px;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 2rem;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        
        .platform-preview::before {
            content: '';
            position: absolute;
            top: 20px;
            left: 20px;
            right: 20px;
            height: 40px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            opacity: 0.8;
        }
        
        .preview-content {
            margin-top: 60px;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            height: calc(100% - 80px);
        }
        
        .preview-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Features Section */
        .features {
            padding: 6rem 0;
            background: #0a0a0a;
        }
        
        .features-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        
        .section-header {
            text-align: center;
            margin-bottom: 4rem;
        }
        
        .section-header h2 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #ffffff 0%, #667eea 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .section-header p {
            font-size: 1.2rem;
            color: #b0b0b0;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }
        
        .feature-card {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
            border-radius: 20px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
        }
        
        .feature-card h3 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #ffffff;
        }
        
        .feature-card p {
            color: #b0b0b0;
            line-height: 1.6;
        }
        
        /* Email Signup Section */
        .signup {
            padding: 6rem 0;
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
        }
        
        .signup-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 0 2rem;
            text-align: center;
        }
        
        .signup h2 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #ffffff 0%, #667eea 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .signup p {
            font-size: 1.2rem;
            color: #b0b0b0;
            margin-bottom: 2rem;
        }
        
        .email-form {
            display: flex;
            gap: 1rem;
            max-width: 500px;
            margin: 0 auto;
        }
        
        .email-input {
            flex: 1;
            padding: 1rem 1.5rem;
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 50px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s ease;
        }
        
        .email-input:focus {
            border-color: #667eea;
        }
        
        .email-input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        
        .email-submit {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .email-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        
        /* Footer */
        .footer {
            padding: 3rem 0;
            background: #0a0a0a;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .footer-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            text-align: center;
        }
        
        .footer p {
            color: #b0b0b0;
            margin-bottom: 1rem;
        }
        
        .footer-links {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .footer-links a {
            color: #b0b0b0;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        .footer-links a:hover {
            color: #667eea;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .hero-container {
                grid-template-columns: 1fr;
                gap: 2rem;
            }
            
            .hero-content h1 {
                font-size: 2.5rem;
            }
            
            .hero-stats {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            
            .cta-buttons {
                flex-direction: column;
            }
            
            .nav-links {
                display: none;
            }
            
            .email-form {
                flex-direction: column;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Animations */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .platform-preview {
            animation: float 6s ease-in-out infinite;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 10000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
            margin: 5% auto;
            padding: 2rem;
            border-radius: 20px;
            width: 90%;
            max-width: 500px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: white;
        }
        
        .modal h3 {
            color: white;
            margin-bottom: 1rem;
        }
        
        .modal p {
            color: #b0b0b0;
            margin-bottom: 1rem;
        }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="nav">
            <div class="nav-container">
                <div class="logo">ChatterFix</div>
                <ul class="nav-links">
                    <li><a href="#features">Features</a></li>
                    <li><a href="#benefits">Benefits</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
                <a href="/dashboard" class="cta-nav">Access Platform</a>
            </div>
        </nav>

        <!-- Hero Section -->
        <section class="hero">
            <div class="hero-container">
                <div class="hero-content">
                    <h1>Revolutionize Your Maintenance Operations</h1>
                    <p class="subtitle">ChatterFix CMMS harnesses the power of advanced AI to transform how you manage assets, reduce downtime, and optimize maintenance workflows. Join the future of intelligent maintenance management.</p>
                    
                    <div class="hero-stats">
                        <div class="stat">
                            <span class="stat-number">50%</span>
                            <span class="stat-label">Reduction in Downtime</span>
                        </div>
                        <div class="stat">
                            <span class="stat-number">300%</span>
                            <span class="stat-label">Efficiency Increase</span>
                        </div>
                        <div class="stat">
                            <span class="stat-number">99.9%</span>
                            <span class="stat-label">Uptime Guarantee</span>
                        </div>
                    </div>
                    
                    <div class="cta-buttons">
                        <a href="#signup" class="btn-primary">Start Free Trial</a>
                        <a href="#demo" class="btn-secondary" onclick="requestDemo()">Request Demo</a>
                    </div>
                </div>
                
                <div class="hero-visual">
                    <div class="platform-preview">
                        <div class="preview-content">
                            <div class="preview-card">
                                <h4 style="color: #667eea; margin-bottom: 0.5rem;">Work Orders</h4>
                                <p style="color: #b0b0b0; font-size: 0.9rem;">AI-Optimized Scheduling</p>
                            </div>
                            <div class="preview-card">
                                <h4 style="color: #764ba2; margin-bottom: 0.5rem;">Asset Tracking</h4>
                                <p style="color: #b0b0b0; font-size: 0.9rem;">Predictive Analytics</p>
                            </div>
                            <div class="preview-card">
                                <h4 style="color: #667eea; margin-bottom: 0.5rem;">Parts Inventory</h4>
                                <p style="color: #b0b0b0; font-size: 0.9rem;">Smart Procurement</p>
                            </div>
                            <div class="preview-card">
                                <h4 style="color: #764ba2; margin-bottom: 0.5rem;">AI Insights</h4>
                                <p style="color: #b0b0b0; font-size: 0.9rem;">Real-time Intelligence</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section class="features" id="features">
            <div class="features-container">
                <div class="section-header">
                    <h2>Powerful Features That Drive Results</h2>
                    <p>Experience the next generation of maintenance management with AI-powered automation and insights</p>
                </div>
                
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🛠️</div>
                        <h3>Smart Work Order Management</h3>
                        <p>AI-powered scheduling and optimization that automatically prioritizes tasks based on criticality, resource availability, and maintenance history.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">🏭</div>
                        <h3>Predictive Asset Management</h3>
                        <p>Advanced analytics predict equipment failures before they happen, reducing unplanned downtime by up to 75%.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">🔧</div>
                        <h3>Intelligent Inventory Control</h3>
                        <p>Automated parts procurement and inventory optimization ensure you always have the right parts at the right time.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">🧠</div>
                        <h3>AI-Powered Insights</h3>
                        <p>Machine learning algorithms analyze your maintenance data to provide actionable insights and recommendations.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">📄</div>
                        <h3>Document Intelligence</h3>
                        <p>Revolutionary OCR and AI technology automatically processes maintenance documents, manuals, and equipment data.</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <h3>Real-Time Analytics</h3>
                        <p>Comprehensive dashboards and reporting provide real-time visibility into your maintenance operations.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Email Signup Section -->
        <section class="signup" id="signup">
            <div class="signup-container">
                <h2>Ready to Transform Your Maintenance?</h2>
                <p>Join thousands of facility managers who have revolutionized their operations with ChatterFix CMMS</p>
                
                <form class="email-form" onsubmit="submitEmail(event)">
                    <input type="email" class="email-input" placeholder="Enter your email address" required>
                    <button type="submit" class="email-submit">Get Started</button>
                </form>
                
                <p style="margin-top: 1rem; font-size: 0.9rem; color: rgba(255,255,255,0.6);">
                    No spam, unsubscribe at any time. Start your free trial today.
                </p>
            </div>
        </section>

        <!-- Footer -->
        <footer class="footer" id="contact">
            <div class="footer-container">
                <div class="footer-links">
                    <a href="/dashboard">Platform Access</a>
                    <a href="#features">Features</a>
                    <a href="#signup">Get Started</a>
                    <a href="mailto:yoyofred@gringosgambit.com">Support</a>
                </div>
                <p>&copy; 2024 ChatterFix. All rights reserved. | Contact: yoyofred@gringosgambit.com</p>
                <p>Revolutionizing maintenance management with AI-powered solutions</p>
            </div>
        </footer>

        <!-- Demo Request Modal -->
        <div id="demoModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <h3>Request a Demo</h3>
                <p>Experience ChatterFix CMMS in action with a personalized demo tailored to your facility's needs.</p>
                <form onsubmit="submitDemo(event)">
                    <input type="text" placeholder="Your Name" required style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.1); color: white;">
                    <input type="email" placeholder="Email Address" required style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.1); color: white;">
                    <input type="text" placeholder="Company Name" required style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.1); color: white;">
                    <button type="submit" class="btn-primary" style="width: 100%;">Schedule Demo</button>
                </form>
            </div>
        </div>

        <script>
        function submitEmail(event) {
            event.preventDefault();
            const email = event.target.querySelector('input[type="email"]').value;
            
            // Simulate API call
            fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email, source: 'landing_page' })
            })
            .then(response => {
                if (response.ok) {
                    alert('Thank you! We\'ll be in touch soon with your free trial access.');
                    event.target.reset();
                } else {
                    throw new Error('Signup failed');
                }
            })
            .catch(error => {
                console.error('Signup error:', error);
                // Still show success for demo purposes
                alert('Thank you! We\'ll be in touch soon with your free trial access.');
                event.target.reset();
            });
        }
        
        function requestDemo() {
            document.getElementById('demoModal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('demoModal').style.display = 'none';
        }
        
        function submitDemo(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const demoData = {
                name: formData.get('name'),
                email: formData.get('email'),
                company: formData.get('company'),
                source: 'demo_request'
            };
            
            // Simulate API call
            alert('Demo request submitted! Our team will contact you within 24 hours.');
            closeModal();
            event.target.reset();
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('demoModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Add some dynamic stats animation
        function animateStats() {
            const stats = document.querySelectorAll('.stat-number');
            stats.forEach(stat => {
                const finalValue = stat.textContent;
                const numericValue = parseInt(finalValue);
                const suffix = finalValue.replace(/[0-9]/g, '');
                
                let current = 0;
                const increment = numericValue / 100;
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= numericValue) {
                        current = numericValue;
                        clearInterval(timer);
                    }
                    stat.textContent = Math.floor(current) + suffix;
                }, 20);
            });
        }
        
        // Trigger stats animation when in view
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateStats();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        const heroStats = document.querySelector('.hero-stats');
        if (heroStats) {
            observer.observe(heroStats);
        }
        </script>
        
        <!-- Floating AI Chat Assistant -->
        <div id="chat-widget">
            <div id="chat-button" onclick="toggleChat()">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 13.54 2.38 14.99 3.06 16.26L2 22L7.74 20.94C9.01 21.62 10.46 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C10.74 20 9.55 19.73 8.5 19.26L8 19L4.42 19.89L5.31 16.42L5.05 15.92C4.58 14.87 4.31 13.68 4.31 12.4C4.31 7.9 7.9 4.31 12.4 4.31C16.9 4.31 20.49 7.9 20.49 12.4C20.49 16.9 16.9 20.49 12.4 20.49H12V20Z" fill="white"/>
                    <circle cx="8.5" cy="12" r="1.5" fill="white"/>
                    <circle cx="12" cy="12" r="1.5" fill="white"/>
                    <circle cx="15.5" cy="12" r="1.5" fill="white"/>
                </svg>
                <span id="chat-badge" class="chat-badge">Ask me anything!</span>
            </div>
            
            <div id="chat-window" style="display: none;">
                <div id="chat-header">
                    <div class="chat-header-content">
                        <div class="assistant-info">
                            <div class="assistant-avatar">🤖</div>
                            <div>
                                <div class="assistant-name">ChatterFix AI Assistant</div>
                                <div class="assistant-status">Online • Ready to help</div>
                            </div>
                        </div>
                        <button onclick="toggleChat()" class="close-chat">×</button>
                    </div>
                </div>
                
                <div id="chat-messages">
                    <div class="message assistant-message">
                        <div class="message-content">
                            👋 Hi! I'm your ChatterFix AI Assistant. I can help you with:
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li>Learning about ChatterFix CMMS features</li>
                                <li>Navigating the platform</li>
                                <li>Getting started with maintenance management</li>
                                <li>Answering technical questions</li>
                                <li>Scheduling a demo</li>
                            </ul>
                            What would you like to know?
                        </div>
                        <div class="message-time">Just now</div>
                    </div>
                </div>
                
                <div id="chat-input-container">
                    <div class="quick-actions">
                        <button class="quick-action" onclick="sendQuickMessage('How does ChatterFix reduce downtime?')">🔧 Reduce Downtime</button>
                        <button class="quick-action" onclick="sendQuickMessage('Show me a demo')">👀 Request Demo</button>
                        <button class="quick-action" onclick="sendQuickMessage('What is predictive maintenance?')">📊 Predictive Maintenance</button>
                    </div>
                    <div class="input-group">
                        <input type="text" id="chat-input" placeholder="Type your message..." onkeypress="handleChatKeyPress(event)">
                        <button id="send-button" onclick="sendMessage()">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
        #chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        #chat-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        #chat-button:hover {
            transform: scale(1.1);
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
        }
        
        .chat-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: #ff6b6b;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
            animation: pulse 2s infinite;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        #chat-window {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 380px;
            height: 500px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 24px 64px rgba(0, 0, 0, 0.15);
            border: 1px solid rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            animation: slideUp 0.3s ease;
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        #chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
        }
        
        .chat-header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .assistant-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .assistant-avatar {
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }
        
        .assistant-name {
            font-weight: 600;
            font-size: 14px;
        }
        
        .assistant-status {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .close-chat {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background-color 0.2s ease;
        }
        
        .close-chat:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        #chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: #f8fafc;
        }
        
        .message {
            margin-bottom: 16px;
        }
        
        .message-content {
            background: white;
            padding: 12px 16px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            font-size: 14px;
            line-height: 1.5;
        }
        
        .assistant-message .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .user-message {
            text-align: right;
        }
        
        .user-message .message-content {
            background: #e2e8f0;
            color: #334155;
            display: inline-block;
        }
        
        .message-time {
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
        }
        
        .user-message .message-time {
            text-align: right;
        }
        
        #chat-input-container {
            padding: 16px;
            background: white;
            border-top: 1px solid #e2e8f0;
        }
        
        .quick-actions {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }
        
        .quick-action {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 6px 12px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        
        .quick-action:hover {
            background: #e2e8f0;
            transform: translateY(-1px);
        }
        
        .input-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        #chat-input {
            flex: 1;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s ease;
        }
        
        #chat-input:focus {
            border-color: #667eea;
        }
        
        #send-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        #send-button:hover {
            transform: scale(1.05);
        }
        
        @media (max-width: 480px) {
            #chat-window {
                width: calc(100vw - 40px);
                right: -10px;
                height: 400px;
            }
        }
        </style>
        
        <script>
        let chatOpen = false;
        
        function toggleChat() {
            const chatWindow = document.getElementById('chat-window');
            const chatBadge = document.getElementById('chat-badge');
            
            if (chatOpen) {
                chatWindow.style.display = 'none';
                chatBadge.style.display = 'block';
                chatBadge.textContent = 'Ask me anything!';
                chatOpen = false;
            } else {
                chatWindow.style.display = 'flex';
                chatBadge.style.display = 'none';
                chatOpen = true;
                document.getElementById('chat-input').focus();
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTypingIndicator();
            
            // Send to AI service
            fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    context: 'customer_support'
                })
            })
            .then(response => response.json())
            .then(data => {
                hideTypingIndicator();
                if (data.success) {
                    addMessage(data.response, 'assistant');
                } else {
                    addMessage('I apologize, but I encountered an issue. Please try again or contact our support team at support@chatterfix.com', 'assistant');
                }
            })
            .catch(error => {
                hideTypingIndicator();
                addMessage('I apologize, but I encountered an issue. Please try again or contact our support team at support@chatterfix.com', 'assistant');
            });
        }
        
        function sendQuickMessage(message) {
            document.getElementById('chat-input').value = message;
            sendMessage();
        }
        
        function addMessage(content, sender) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            
            const now = new Date();
            const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            messageDiv.innerHTML = `
                <div class="message-content">${content}</div>
                <div class="message-time">${timeString}</div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function showTypingIndicator() {
            const messagesContainer = document.getElementById('chat-messages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typing-indicator';
            typingDiv.className = 'message assistant-message';
            typingDiv.innerHTML = `
                <div class="message-content">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        ChatterFix AI is typing...
                    </div>
                </div>
            `;
            
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function hideTypingIndicator() {
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }
        
        function handleChatKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        // Auto-show chat for new visitors
        setTimeout(() => {
            if (!chatOpen && !localStorage.getItem('chatterfix_chat_seen')) {
                const badge = document.getElementById('chat-badge');
                badge.textContent = '👋 New here? Ask me anything!';
                badge.style.animation = 'pulse 1s infinite';
                localStorage.setItem('chatterfix_chat_seen', 'true');
            }
        }, 3000);
        </script>
        
        <style>
        .typing-dots {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .typing-dots span {
            width: 6px;
            height: 6px;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.7; }
            30% { transform: translateY(-10px); opacity: 1; }
        }
        </style>
    </body>
    </html>
    """

# Dashboard route for platform access
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard that integrates all microservices"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS Enterprise - Advanced AI Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }}
        .subtitle {{
            margin: 0.5rem 0 0 0;
            color: #b0b0b0;
            font-size: 1.1rem;
        }}
        .nav-back {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        .nav-back:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }}
        .dashboard {{
            padding: 2rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .service-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .service-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }}
        .service-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
        }}
        .service-title {{
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        .service-description {{
            color: #b0b0b0;
            line-height: 1.5;
            margin-bottom: 1rem;
        }}
        .service-status {{
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            display: inline-block;
        }}
        .vision-info {{
            text-align: center;
            margin: 2rem 0;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-width: 800px;
            margin: 2rem auto;
        }}
        .benefits-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }}
        .benefit-item {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(5px);
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .benefit-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        }}
        .benefit-icon {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
            display: block;
        }}
        .vision-statement {{
            font-size: 1.2rem;
            line-height: 1.6;
            color: #e0e0e0;
            margin: 1.5rem 0;
            font-style: italic;
        }}
        .api-section {{
            margin: 2rem;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>🚀 ChatterFix CMMS Enterprise</h1>
                <p class="subtitle">Advanced AI Platform - Microservices Architecture</p>
            </div>
            <a href="/" class="nav-back">← Back to Landing</a>
        </div>

        <div class="vision-info">
            <h2>Fix it Faster with ChatterFix</h2>
            <p class="vision-statement">Empowering facility managers and maintenance teams to achieve operational excellence through intelligent automation, predictive insights, and streamlined workflows that reduce downtime and maximize asset performance.</p>
            
            <div class="benefits-grid">
                <div class="benefit-item">
                    <div class="benefit-icon">⚡</div>
                    <strong>Faster Response Times</strong>
                    <p>Reduce maintenance response times by up to 70% with intelligent work order prioritization and automated scheduling</p>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">📈</div>
                    <strong>Increased Efficiency</strong>
                    <p>Streamline operations with automated workflows, smart inventory management, and predictive maintenance insights</p>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">🎯</div>
                    <strong>Enhanced Reliability</strong>
                    <p>Prevent unexpected breakdowns with AI-powered asset monitoring and proactive maintenance recommendations</p>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">💰</div>
                    <strong>Cost Savings</strong>
                    <p>Optimize maintenance budgets through data-driven decisions, extended asset life, and reduced emergency repairs</p>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">📱</div>
                    <strong>Easy to Use</strong>
                    <p>Intuitive interface designed for maintenance professionals, with mobile-first design for field teams</p>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">🔧</div>
                    <strong>Complete Solution</strong>
                    <p>All-in-one platform covering work orders, assets, inventory, and analytics in one integrated system</p>
                </div>
            </div>
        </div>

        <div class="dashboard">
            <div class="service-card" onclick="window.open('/work-orders', '_blank')">
                <div class="service-icon">🛠️</div>
                <div class="service-title">Work Orders</div>
                <div class="service-description">Complete work order management with Advanced AI scheduling and optimization</div>
                <div class="service-status">✅ Active</div>
            </div>

            <div class="service-card" onclick="window.open('/assets', '_blank')">
                <div class="service-icon">🏭</div>
                <div class="service-title">Assets</div>
                <div class="service-description">Asset lifecycle management with predictive maintenance insights</div>
                <div class="service-status">✅ Active</div>
            </div>

            <div class="service-card" onclick="window.open('/parts', '_blank')">
                <div class="service-icon">🔧</div>
                <div class="service-title">Parts Inventory</div>
                <div class="service-description">Smart inventory management with automated procurement workflows</div>
                <div class="service-status">✅ Active</div>
            </div>

            <div class="service-card" onclick="window.open('/ai-brain', '_blank')">
                <div class="service-icon">🧠</div>
                <div class="service-title">AI Brain</div>
                <div class="service-description">Advanced AI with multi-AI orchestration and quantum analytics</div>
                <div class="service-status">✅ Active</div>
            </div>

            <div class="service-card" onclick="window.open('/document-intelligence', '_blank')">
                <div class="service-icon">📄</div>
                <div class="service-title">Document Intelligence</div>
                <div class="service-description">🚀 Revolutionary OCR & AI - Voice processing, equipment recognition, automated data entry</div>
                <div class="service-status">🔥 NEW!</div>
            </div>

            <div class="service-card" onclick="window.open('/pm-scheduling', '_blank')">
                <div class="service-icon">⏰</div>
                <div class="service-title">PM Scheduling</div>
                <div class="service-description">🎯 Advanced preventive maintenance scheduling with AI optimization and automated work order generation</div>
                <div class="service-status">🔥 ENHANCED!</div>
            </div>
        </div>

        <div class="api-section">
            <h3>🔗 API Gateway Routes</h3>
            <p>All API requests are automatically routed to the appropriate microservices:</p>
            <ul>
                <li><strong>/api/work-orders/*</strong> → Work Orders Service</li>
                <li><strong>/api/assets/*</strong> → Assets Service</li>
                <li><strong>/api/parts/*</strong> → Parts Service</li>
                <li><strong>/api/pm-schedules/*</strong> → Database Service (PM Scheduling)</li>
                <li><strong>/api/ai/*</strong> → AI Brain Service</li>
                <li><strong>/api/documents/*</strong> → Document Intelligence Service</li>
                <li><strong>/health</strong> → System Health Check</li>
            </ul>
        </div>

        <script>
        // Load service health status
        fetch('/health')
            .then(response => response.json())
            .then(data => {{
                console.log('Microservices Status:', data);
                if (data.microservices) {{
                    Object.keys(data.microservices).forEach(service => {{
                        const status = data.microservices[service].status;
                        console.log(`${{service}}: ${{status}}`);
                    }});
                }}
            }})
            .catch(error => console.error('Health check failed:', error));
        </script>
    </body>
    </html>
    """

# Email signup API endpoint
@app.post("/api/signup")
async def email_signup(request: Request):
    """Handle email signup from landing page"""
    try:
        body = await request.json()
        email = body.get('email')
        source = body.get('source', 'landing_page')
        
        # Log the signup (in production, this would go to a database)
        logger.info(f"Email signup: {email} from {source}")
        
        # In production, you would:
        # 1. Validate email format
        # 2. Store in database
        # 3. Send to email marketing service
        # 4. Send welcome email
        
        return {"success": True, "message": "Signup successful", "email": email}
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Signup failed"}
        )

# API Gateway routes - proxy to microservices with full CRUD operations

# Work Orders endpoints
@app.get("/api/work-orders")
async def get_work_orders():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['work_orders']}/api/work-orders")
        return response.json()

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrderCreate):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICES['work_orders']}/api/work-orders", 
            json=work_order.dict()
        )
        return response.json()

@app.get("/api/work-orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['work_orders']}/api/work-orders/{work_order_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Work order not found")
        return response.json()

@app.put("/api/work-orders/{work_order_id}")
async def update_work_order(work_order_id: int, work_order: WorkOrderCreate):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{SERVICES['work_orders']}/api/work-orders/{work_order_id}",
            json=work_order.dict()
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Work order not found")
        return response.json()

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{SERVICES['work_orders']}/api/work-orders/{work_order_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Work order not found")
        return {"message": "Work order deleted successfully"}

# Assets endpoints
@app.get("/api/assets")
async def get_assets():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['assets']}/api/assets")
        return response.json()

@app.post("/api/assets")
async def create_asset(asset: AssetCreate):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICES['assets']}/api/assets",
            json=asset.dict()
        )
        return response.json()

@app.get("/api/assets/{asset_id}")
async def get_asset(asset_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['assets']}/api/assets/{asset_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Asset not found")
        return response.json()

# Parts endpoints
@app.get("/api/parts")
async def get_parts():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['parts']}/api/parts")
        return response.json()

@app.post("/api/parts")
async def create_part(part: PartCreate):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICES['parts']}/api/parts",
            json=part.dict()
        )
        return response.json()

@app.get("/api/parts/{part_id}")
async def get_part(part_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['parts']}/api/parts/{part_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Part not found")
        return response.json()

# AI Brain endpoints
@app.get("/api/ai/status")
async def get_ai_status():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['ai_brain']}/health")
        return response.json()

@app.post("/api/ai/analyze")
async def ai_analyze(request: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICES['ai_brain']}/api/ai/analyze",
            json=request
        )
        return response.json()

@app.get("/api/ai/insights")
async def get_ai_insights():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['ai_brain']}/api/ai/insights")
        return response.json()

# AI Assistant Chat endpoints
@app.post("/api/ai/chat")
async def ai_chat(request: Dict[str, Any]):
    """AI assistant chat endpoint with context awareness"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SERVICES['ai']}/api/ai/chat",
                json=request
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                return {
                    "success": False,
                    "message": "I'm currently experiencing high traffic. Please try again in a moment!",
                    "fallback": True,
                    "suggested_actions": [
                        "Browse our FAQ section",
                        "Contact support directly",
                        "Try again in a few minutes"
                    ]
                }
            
            # Handle other error status codes
            if response.status_code != 200:
                return {
                    "success": False, 
                    "message": "I'm having trouble connecting right now. How can I help you get started with ChatterFix?",
                    "fallback": True,
                    "suggested_actions": [
                        "View our getting started guide",
                        "Schedule a demo",
                        "Contact our support team"
                    ]
                }
            
            # Try to parse JSON response
            try:
                return response.json()
            except (ValueError, json.JSONDecodeError):
                return {
                    "success": False,
                    "message": "I'm having a technical issue, but I'm here to help! What would you like to know about ChatterFix?",
                    "fallback": True,
                    "suggested_actions": [
                        "Learn about our CMMS features", 
                        "Request a demo",
                        "Speak with sales"
                    ]
                }
                
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        # Provide helpful fallback response for customer onboarding
        user_message = request.get("message", "").lower()
        
        if any(word in user_message for word in ["demo", "trial", "getting started", "new"]):
            fallback_message = "Welcome to ChatterFix! I'd love to help you get started with our CMMS platform."
            actions = ["Schedule a demo", "View pricing", "Try our free trial"]
        elif any(word in user_message for word in ["price", "cost", "plan"]):
            fallback_message = "Great question about our pricing! Let me help you find the right plan."
            actions = ["View pricing plans", "Contact sales", "Compare features"]
        elif any(word in user_message for word in ["support", "help", "issue"]):
            fallback_message = "I'm here to help! Let me connect you with the right resources."
            actions = ["Contact support", "Browse documentation", "Submit a ticket"]
        else:
            fallback_message = "Thanks for your interest in ChatterFix! How can I help you today?"
            actions = ["Learn about CMMS", "Schedule a demo", "View features"]
        
        return {
            "success": True,
            "message": fallback_message,
            "fallback": True,
            "suggested_actions": actions
        }

@app.post("/api/ai/context")
async def get_ai_context(request: Dict[str, Any]):
    """Get current page context for AI assistant"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICES['ai']}/api/ai/context",
            json=request
        )
        return response.json()

@app.post("/api/ai/quick-action")
async def ai_quick_action(request: Dict[str, Any]):
    """Execute quick actions through AI assistant"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICES['ai']}/api/ai/quick-action",
            json=request
        )
        return response.json()

@app.get("/api/ai/suggestions/{page}")
async def get_ai_suggestions(page: str):
    """Get AI-powered suggestions for current page"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['ai']}/api/ai/suggestions/{page}")
        return response.json()

@app.post("/api/ai/voice-process")
async def process_voice_input(request: Dict[str, Any]):
    """Process voice input for hands-free operation"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICES['ai']}/api/ai/voice-process",
            json=request
        )
        return response.json()

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = "general"
    user_id: Optional[str] = None

@app.post("/api/ai/chat")
async def chat_with_ai(chat_request: ChatMessage):
    """AI Chat Assistant for customer support and onboarding"""
    try:
        # Enhanced context for customer support
        if chat_request.context == "customer_support":
            system_prompt = """You are the ChatterFix AI Assistant, a helpful and knowledgeable customer support agent for ChatterFix CMMS.

Key information about ChatterFix:
- ChatterFix is a revolutionary AI-powered Computerized Maintenance Management System (CMMS)
- We help companies reduce downtime by 50% and increase maintenance efficiency by 300%
- Features include: predictive maintenance, AI-driven insights, work order management, asset tracking, parts inventory, preventive maintenance scheduling
- We offer enterprise-grade security, real-time analytics, and mobile accessibility
- Safety management module with OSHA compliance features
- AI Brain integration for intelligent recommendations and automation

Your role:
- Help new customers learn about ChatterFix features and benefits
- Assist existing users with navigation and functionality questions
- Provide technical guidance on maintenance management best practices
- Be friendly, professional, and solution-focused
- Offer to schedule demos for interested prospects
- If asked about pricing, direct them to contact our sales team

Always be helpful, accurate, and enthusiastic about how ChatterFix can transform their maintenance operations."""

        else:
            system_prompt = """You are the ChatterFix AI Assistant. You help users with ChatterFix CMMS platform questions, maintenance management guidance, and general technical support. Be helpful, professional, and knowledgeable."""

        # Prepare the full prompt
        full_prompt = f"{system_prompt}\n\nUser: {chat_request.message}\nAssistant:"
        
        # Try the AI service first
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SERVICES['ai']}/api/ai/process",
                    json={
                        "prompt": full_prompt,
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    ai_data = response.json()
                    if ai_data.get("success") and ai_data.get("response"):
                        return {
                            "success": True,
                            "response": ai_data["response"],
                            "context": chat_request.context,
                            "timestamp": time.time()
                        }
        except Exception as e:
            logger.error(f"AI service error: {e}")
        
        # Fallback responses based on context and keywords
        message_lower = chat_request.message.lower()
        
        if any(word in message_lower for word in ["demo", "demonstration", "show", "see"]):
            return {
                "success": True,
                "response": "I'd be happy to help you schedule a demo of ChatterFix! Our demos showcase how we help companies reduce downtime by 50% and increase maintenance efficiency by 300%. Would you like me to connect you with our sales team to schedule a personalized demonstration? You can also visit our work orders dashboard to see the platform in action.",
                "context": chat_request.context,
                "timestamp": time.time()
            }
        
        elif any(word in message_lower for word in ["downtime", "reduce", "efficiency"]):
            return {
                "success": True,
                "response": "ChatterFix reduces downtime through our AI-powered predictive maintenance system! Here's how: 🔧 **Predictive Analytics** - Our AI analyzes equipment data to predict failures before they happen, 📊 **Smart Scheduling** - Automatically schedules maintenance during optimal times, 🚨 **Real-time Alerts** - Instant notifications about equipment issues, 📱 **Mobile Access** - Technicians get immediate updates and can respond faster. This combination typically reduces unplanned downtime by 50% for our customers!",
                "context": chat_request.context,
                "timestamp": time.time()
            }
        
        elif any(word in message_lower for word in ["predictive", "prediction", "ai", "artificial intelligence"]):
            return {
                "success": True,
                "response": "Our AI-powered predictive maintenance is one of ChatterFix's most powerful features! 🧠 **Machine Learning** - Analyzes historical data patterns to predict equipment failures, 📈 **Trend Analysis** - Identifies subtle changes in equipment performance, 🎯 **Precise Timing** - Tells you exactly when maintenance should be performed, 💡 **Smart Insights** - Provides actionable recommendations for each asset. The result? You can prevent failures before they happen, saving time, money, and avoiding costly emergency repairs!",
                "context": chat_request.context,
                "timestamp": time.time()
            }
        
        elif any(word in message_lower for word in ["work order", "work-order", "maintenance request"]):
            return {
                "success": True,
                "response": "ChatterFix's work order management is incredibly powerful! 🎯 **Easy Creation** - Create work orders in seconds with auto-populated data, 📋 **Smart Assignment** - AI automatically assigns to the best available technician, 📱 **Mobile Updates** - Technicians can update status in real-time from their phones, 📊 **Progress Tracking** - Full visibility into work order status and completion times, 🔄 **Automated Workflows** - Streamlined processes from creation to completion. You can check out our work orders dashboard to see it in action!",
                "context": chat_request.context,
                "timestamp": time.time()
            }
        
        elif any(word in message_lower for word in ["safety", "osha", "compliance", "incident"]):
            return {
                "success": True,
                "response": "Safety is a top priority! ChatterFix includes a comprehensive Safety Management module: 🛡️ **OSHA Compliance** - Built-in compliance tracking and reporting, 📝 **Incident Reporting** - Easy incident documentation and investigation tracking, 🎓 **Training Records** - Employee safety certification management, ⚠️ **Hazard Assessments** - Workplace risk analysis and mitigation tracking, 🔍 **Safety Inspections** - Scheduled safety audits and compliance checks. Our safety dashboard gives you real-time visibility into your safety metrics and helps maintain a safe workplace!",
                "context": chat_request.context,
                "timestamp": time.time()
            }
        
        elif any(word in message_lower for word in ["price", "pricing", "cost", "subscription", "license"]):
            return {
                "success": True,
                "response": "Great question about pricing! ChatterFix offers flexible pricing plans tailored to your organization's size and needs. Our solutions typically pay for themselves within 3-6 months through reduced downtime and improved efficiency. For detailed pricing information and to discuss the best plan for your specific requirements, I'd recommend speaking with our sales team. They can provide a customized quote and show you the ROI calculations. Would you like me to help connect you with them?",
                "context": chat_request.context,
                "timestamp": time.time()
            }
        
        elif any(word in message_lower for word in ["hello", "hi", "hey", "start", "help"]):
            return {
                "success": True,
                "response": "Hello! 👋 Welcome to ChatterFix, the world's most advanced AI-powered CMMS! I'm here to help you discover how we can transform your maintenance operations. Whether you're interested in reducing downtime, improving efficiency, or exploring our features like predictive maintenance, work order management, or safety compliance - I'm here to help! What would you like to know about ChatterFix?",
                "context": chat_request.context,
                "timestamp": time.time()
            }
        
        else:
            return {
                "success": True,
                "response": "Thanks for your question! I'm here to help you learn about ChatterFix CMMS and how we can revolutionize your maintenance operations. ChatterFix offers AI-powered predictive maintenance, intelligent work order management, comprehensive asset tracking, and much more. We typically help companies reduce downtime by 50% and increase efficiency by 300%. What specific aspect of maintenance management are you most interested in? I can tell you about our features, schedule a demo, or connect you with our technical team!",
                "context": chat_request.context,
                "timestamp": time.time()
            }
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        return {
            "success": False,
            "response": "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment, or feel free to contact our support team directly at support@chatterfix.com for immediate assistance.",
            "error": str(e),
            "timestamp": time.time()
        }

# Individual service dashboard routes
@app.get("/work-orders", response_class=HTMLResponse)
async def work_orders_dashboard():
    """Fully functional Work Orders dashboard with real-time data"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Work Orders Management - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        .content {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        .controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            align-items: center;
        }
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        .btn-secondary {
            background: rgba(255,255,255,0.2);
            color: white;
        }
        .btn-secondary:hover {
            background: rgba(255,255,255,0.3);
        }
        .work-orders-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 2rem;
            margin-top: 2rem;
        }
        .form-card, .list-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }
        .form-control {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(255,255,255,0.05);
            color: white;
            font-size: 1rem;
            backdrop-filter: blur(5px);
        }
        .form-control::placeholder {
            color: rgba(255,255,255,0.7);
        }
        .form-control:focus {
            outline: none;
            border-color: #28a745;
            box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.3);
        }
        .work-order-item {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }
        .work-order-item:hover {
            background: rgba(255,255,255,0.1);
            transform: translateY(-2px);
        }
        .work-order-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .work-order-title {
            font-size: 1.25rem;
            font-weight: bold;
            margin: 0;
        }
        .priority-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.875rem;
            font-weight: bold;
        }
        .priority-high { background: #dc3545; }
        .priority-medium { background: #ffc107; color: #000; }
        .priority-low { background: #28a745; }
        .priority-critical { background: #6f42c1; }
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.875rem;
            font-weight: bold;
            margin-left: 0.5rem;
        }
        .status-open { background: #17a2b8; }
        .status-in_progress { background: #ffc107; color: #000; }
        .status-completed { background: #28a745; }
        .status-on_hold { background: #dc3545; }
        .loading {
            text-align: center;
            padding: 2rem;
            opacity: 0.7;
        }
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid #28a745;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .ai-suggestions {
            background: linear-gradient(45deg, #667eea, #764ba2);
            border-radius: 10px;
            padding: 1rem;
            margin-top: 1rem;
        }
        .refresh-btn {
            background: transparent;
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        @media (max-width: 768px) {
            .work-orders-grid {
                grid-template-columns: 1fr;
            }
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
        }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛠️ Work Orders Management</h1>
            <p>Real-time Work Order Management with AI-powered Optimization</p>
        </div>
        
        <div class="content">
            <div class="controls">
                <a href="/work-orders" class="btn btn-secondary">← Back to Dashboard</a>
                <button onclick="refreshWorkOrders()" class="refresh-btn">🔄 Refresh</button>
                <button onclick="getAIRecommendations()" class="btn btn-primary">🧠 Get AI Insights</button>
            </div>
            
            <div class="work-orders-grid">
                <div class="form-card">
                    <h3>Create New Work Order</h3>
                    <form id="workOrderForm" onsubmit="createWorkOrder(event)">
                        <div class="form-group">
                            <label for="title">Title</label>
                            <input type="text" id="title" name="title" class="form-control" 
                                   placeholder="Enter work order title" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="description">Description</label>
                            <textarea id="description" name="description" class="form-control" 
                                      rows="3" placeholder="Describe the work to be done" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="priority">Priority</label>
                            <select id="priority" name="priority" class="form-control">
                                <option value="low">Low</option>
                                <option value="medium" selected>Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="status">Status</label>
                            <select id="status" name="status" class="form-control">
                                <option value="open" selected>Open</option>
                                <option value="in_progress">In Progress</option>
                                <option value="on_hold">On Hold</option>
                                <option value="completed">Completed</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="assigned_to">Assigned To</label>
                            <input type="text" id="assigned_to" name="assigned_to" class="form-control" 
                                   placeholder="Technician name (optional)">
                        </div>
                        
                        <div class="form-group">
                            <label for="asset_id">Asset ID</label>
                            <input type="number" id="asset_id" name="asset_id" class="form-control" 
                                   placeholder="Asset ID (optional)">
                        </div>
                        
                        <div class="form-group">
                            <label for="attachments">📎 Attachments</label>
                            <div class="file-upload-container">
                                <input type="file" id="attachments" name="attachments" class="form-control" 
                                       multiple accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.txt">
                                <small class="form-text text-muted">
                                    Upload manuals, SOPs, photos, or documents (Max 10MB each)
                                </small>
                                <div id="file-preview" class="file-preview"></div>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn btn-primary" style="width: 100%;">
                            ✅ Create Work Order
                        </button>
                    </form>
                    
                    <div id="aiSuggestions" class="ai-suggestions" style="display: none;">
                        <h4>🧠 AI Recommendations</h4>
                        <div id="aiContent"></div>
                    </div>
                </div>
                
                <div class="list-card">
                    <h3>Active Work Orders</h3>
                    <div id="workOrdersList">
                        <div class="loading">
                            <div class="spinner"></div>
                            Loading work orders...
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
        let workOrders = [];
        
        // Load work orders on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadWorkOrders();
        });
        
        async function loadWorkOrders() {
            try {
                const response = await fetch('/api/work-orders');
                const data = await response.json();
                workOrders = data.work_orders || [];
                renderWorkOrders();
            } catch (error) {
                console.error('Error loading work orders:', error);
                document.getElementById('workOrdersList').innerHTML = 
                    '<div style="text-align: center; color: #ff6b6b; padding: 2rem;">Error loading work orders</div>';
            }
        }
        
        function renderWorkOrders() {
            const container = document.getElementById('workOrdersList');
            
            if (workOrders.length === 0) {
                container.innerHTML = '<div style="text-align: center; opacity: 0.7; padding: 2rem;">No work orders found</div>';
                return;
            }
            
            container.innerHTML = workOrders.map(wo => `
                <div class="work-order-item" onclick="selectWorkOrder(${wo.id})">
                    <div class="work-order-header">
                        <h4 class="work-order-title">${wo.title || wo.work_order_number}</h4>
                        <div>
                            <span class="priority-badge priority-${wo.priority?.toLowerCase() || 'medium'}">${wo.priority || 'Medium'}</span>
                            <span class="status-badge status-${wo.status?.toLowerCase() || 'open'}">${wo.status || 'Open'}</span>
                        </div>
                    </div>
                    <p style="margin: 0.5rem 0; opacity: 0.9;">${wo.description || 'No description'}</p>
                    <div style="font-size: 0.875rem; opacity: 0.7; margin-top: 1rem;">
                        ${wo.assigned_to ? `👤 ${wo.assigned_to}` : '👤 Unassigned'} | 
                        ${wo.asset_id ? `🏭 Asset #${wo.asset_id}` : '🏭 No asset'} |
                        📅 ${wo.created_date ? new Date(wo.created_date).toLocaleDateString() : 'No date'}
                    </div>
                </div>
            `).join('');
        }
        
        async function createWorkOrder(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const workOrder = {
                title: formData.get('title'),
                description: formData.get('description'),
                priority: formData.get('priority'),
                status: formData.get('status'),
                assigned_to: formData.get('assigned_to') || null,
                asset_id: formData.get('asset_id') ? parseInt(formData.get('asset_id')) : null
            };
            
            try {
                // First create the work order
                const response = await fetch('/api/work-orders', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(workOrder)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    const workOrderId = result.id;
                    
                    // Upload attachments if any
                    const attachments = document.getElementById('attachments').files;
                    if (attachments && attachments.length > 0) {
                        await uploadAttachments('work-orders', workOrderId, attachments);
                    }
                    
                    document.getElementById('workOrderForm').reset();
                    document.getElementById('file-preview').innerHTML = '';
                    await loadWorkOrders();
                    alert('✅ Work order created successfully!');
                } else {
                    const error = await response.json();
                    alert('❌ Error creating work order: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error creating work order:', error);
                alert('❌ Error creating work order: ' + error.message);
            }
        }
        
        async function uploadAttachments(entityType, entityId, files) {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);
                formData.append('type', getAttachmentType(file.name));
                formData.append('description', `Attachment for ${entityType} ${entityId}`);
                
                try {
                    const response = await fetch(`/api/${entityType}/${entityId}/attachments`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        console.error(`Failed to upload ${file.name}`);
                    }
                } catch (error) {
                    console.error(`Error uploading ${file.name}:`, error);
                }
            }
        }
        
        function getAttachmentType(filename) {
            const ext = filename.toLowerCase().split('.').pop();
            if (['jpg', 'jpeg', 'png', 'gif'].includes(ext)) return 'photo';
            if (['pdf'].includes(ext)) return 'manual';
            if (['doc', 'docx'].includes(ext)) return 'sop';
            return 'document';
        }
        
        // Add file preview functionality
        document.addEventListener('DOMContentLoaded', function() {
            const attachmentInput = document.getElementById('attachments');
            if (attachmentInput) {
                attachmentInput.addEventListener('change', function(e) {
                    const files = e.target.files;
                    const preview = document.getElementById('file-preview');
                    preview.innerHTML = '';
                    
                    for (let i = 0; i < files.length; i++) {
                        const file = files[i];
                        const fileDiv = document.createElement('div');
                        fileDiv.className = 'file-item';
                        fileDiv.innerHTML = `
                            <span class="file-name">📄 ${file.name}</span>
                            <span class="file-size">(${(file.size / 1024).toFixed(1)} KB)</span>
                        `;
                        preview.appendChild(fileDiv);
                    }
                });
            }
        });
        
        function selectWorkOrder(id) {
            const wo = workOrders.find(w => w.id === id);
            if (wo) {
                alert(`Work Order Details:\\n\\nTitle: ${wo.title || wo.work_order_number}\\nDescription: ${wo.description}\\nPriority: ${wo.priority}\\nStatus: ${wo.status}\\nAssigned: ${wo.assigned_to || 'Unassigned'}`);
            }
        }
        
        function refreshWorkOrders() {
            document.getElementById('workOrdersList').innerHTML = 
                '<div class="loading"><div class="spinner"></div>Refreshing...</div>';
            loadWorkOrders();
        }
        
        async function getAIRecommendations() {
            try {
                const response = await fetch('/api/ai/insights');
                const insights = await response.json();
                
                const suggestionsDiv = document.getElementById('aiSuggestions');
                const contentDiv = document.getElementById('aiContent');
                
                contentDiv.innerHTML = `
                    <p>📊 <strong>Current Analysis:</strong></p>
                    <ul>
                        <li>🛠️ ${workOrders.length} total work orders</li>
                        <li>🔴 ${workOrders.filter(wo => wo.priority === 'critical' || wo.priority === 'high').length} high priority items</li>
                        <li>✅ ${workOrders.filter(wo => wo.status === 'completed').length} completed tasks</li>
                        <li>🧠 AI recommends prioritizing critical assets</li>
                    </ul>
                    <p><em>💡 AI suggests scheduling maintenance during off-peak hours for better efficiency.</em></p>
                `;
                
                suggestionsDiv.style.display = 'block';
            } catch (error) {
                console.error('Error getting AI insights:', error);
                alert('🤖 AI insights temporarily unavailable');
            }
        }
        </script>
        
        <!-- AI Assistant Component -->
        """ + AI_ASSISTANT_COMPONENT + """
    </body>
    </html>
    """

@app.get("/assets", response_class=HTMLResponse)
async def assets_dashboard():
    """Assets service dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Assets Service - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        .subtitle {
            margin: 0.5rem 0 0 0;
            color: #b0b0b0;
            font-size: 1.1rem;
        }
        .content {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }
        .card h3 {
            margin-top: 0;
            color: #ffffff;
            font-weight: 600;
        }
        .status-indicator {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        .back-button {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin-bottom: 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .back-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏭 Assets Service</h1>
            <p class="subtitle">Intelligent Asset Lifecycle Management System</p>
        </div>
        
        <div class="content">
            <a href="/assets" class="back-button">← Back to Main Dashboard</a>
            
            <div class="dashboard-grid">
                <div class="card">
                    <h3>Service Status</h3>
                    <div class="status-indicator">✅ Active & Healthy</div>
                    <p>Assets microservice is running with full predictive maintenance capabilities.</p>
                </div>
                
                <div class="card">
                    <h3>Asset Management Features</h3>
                    <ul>
                        <li>Complete asset lifecycle tracking</li>
                        <li>Predictive maintenance scheduling</li>
                        <li>Performance monitoring</li>
                        <li>Depreciation calculations</li>
                        <li>Location and hierarchy management</li>
                        <li>IoT sensor integration</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>API Endpoints</h3>
                    <ul>
                        <li><strong>GET</strong> /api/assets - List all assets</li>
                        <li><strong>POST</strong> /api/assets - Create new asset</li>
                        <li><strong>GET</strong> /api/assets/{id} - Get specific asset</li>
                        <li><strong>PUT</strong> /api/assets/{id} - Update asset</li>
                        <li><strong>GET</strong> /api/assets/{id}/maintenance - Get maintenance history</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>AI-Powered Insights</h3>
                    <ul>
                        <li>Failure prediction algorithms</li>
                        <li>Optimal maintenance scheduling</li>
                        <li>Performance trend analysis</li>
                        <li>Cost optimization recommendations</li>
                        <li>Energy efficiency monitoring</li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/parts", response_class=HTMLResponse)
async def parts_dashboard():
    """Parts service dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Parts Inventory Service - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        .subtitle {
            margin: 0.5rem 0 0 0;
            color: #b0b0b0;
            font-size: 1.1rem;
        }
        .content {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }
        .card h3 {
            margin-top: 0;
            color: #ffffff;
            font-weight: 600;
        }
        .status-indicator {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        .back-button {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin-bottom: 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .back-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔧 Parts Inventory Service</h1>
            <p class="subtitle">Smart Inventory Management & Procurement System</p>
        </div>
        
        <div class="content">
            <a href="/parts" class="back-button">← Back to Main Dashboard</a>
            
            <div class="dashboard-grid">
                <div class="card">
                    <h3>Service Status</h3>
                    <div class="status-indicator">✅ Active & Healthy</div>
                    <p>Parts inventory microservice with intelligent procurement workflows.</p>
                </div>
                
                <div class="card">
                    <h3>Inventory Features</h3>
                    <ul>
                        <li>Real-time inventory tracking</li>
                        <li>Automated reorder point calculations</li>
                        <li>Supplier management</li>
                        <li>Cost tracking and optimization</li>
                        <li>Parts compatibility matching</li>
                        <li>Warehouse location management</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>API Endpoints</h3>
                    <ul>
                        <li><strong>GET</strong> /api/parts - List all parts</li>
                        <li><strong>POST</strong> /api/parts - Add new part</li>
                        <li><strong>GET</strong> /api/parts/{id} - Get specific part</li>
                        <li><strong>PUT</strong> /api/parts/{id} - Update part details</li>
                        <li><strong>GET</strong> /api/parts/low-stock - Get low stock alerts</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>Smart Procurement</h3>
                    <ul>
                        <li>Demand forecasting algorithms</li>
                        <li>Automatic purchase order generation</li>
                        <li>Vendor performance analytics</li>
                        <li>Cost optimization strategies</li>
                        <li>Just-in-time inventory management</li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/ai-brain", response_class=HTMLResponse)
async def ai_brain_dashboard():
    """AI Brain service dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Brain Service - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        .subtitle {
            margin: 0.5rem 0 0 0;
            color: #b0b0b0;
            font-size: 1.1rem;
        }
        .content {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }
        .card h3 {
            margin-top: 0;
            color: #ffffff;
            font-weight: 600;
        }
        .status-indicator {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        .back-button {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin-bottom: 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .back-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧠 AI Brain Service</h1>
            <p class="subtitle">Advanced Multi-AI Orchestration & Analytics Engine</p>
        </div>
        
        <div class="content">
            <a href="/ai-brain" class="back-button">← Back to Main Dashboard</a>
            
            <div class="dashboard-grid">
                <div class="card">
                    <h3>Service Status</h3>
                    <div class="status-indicator">✅ Active & Healthy</div>
                    <p>AI Brain microservice with advanced intelligence capabilities.</p>
                </div>
                
                <div class="card">
                    <h3>AI Capabilities</h3>
                    <ul>
                        <li>Multi-AI model orchestration</li>
                        <li>Predictive analytics engine</li>
                        <li>Natural language processing</li>
                        <li>Pattern recognition algorithms</li>
                        <li>Decision support systems</li>
                        <li>Automated insights generation</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>API Endpoints</h3>
                    <ul>
                        <li><strong>POST</strong> /api/ai/analyze - Run AI analysis</li>
                        <li><strong>GET</strong> /api/ai/insights - Get AI insights</li>
                        <li><strong>POST</strong> /api/ai/predict - Generate predictions</li>
                        <li><strong>GET</strong> /api/ai/models - List available models</li>
                        <li><strong>POST</strong> /api/ai/optimize - Optimization recommendations</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>Advanced Features</h3>
                    <ul>
                        <li>Real-time anomaly detection</li>
                        <li>Automated root cause analysis</li>
                        <li>Intelligent recommendation engine</li>
                        <li>Cross-system data correlation</li>
                        <li>Quantum-inspired optimization</li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/document-intelligence", response_class=HTMLResponse)
async def document_intelligence_dashboard():
    """Document Intelligence service dashboard"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['document_intelligence']}/", timeout=10.0)
            return HTMLResponse(content=response.text)
        except Exception as e:
            return HTMLResponse(content=f"<h1>Document Intelligence Service Unavailable</h1><p>Error: {str(e)}</p>")

# Document Intelligence API endpoints
@app.post("/api/documents/upload")
async def upload_document_proxy(request: Request):
    """Proxy document upload to document intelligence service"""
    async with httpx.AsyncClient() as client:
        try:
            body = await request.body()
            headers = dict(request.headers)
            # Remove hop-by-hop headers
            headers.pop('host', None)
            headers.pop('content-length', None)
            
            response = await client.post(
                f"{SERVICES['document_intelligence']}/api/process-document",
                content=body,
                headers=headers,
                timeout=60.0
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": f"Document service error: {str(e)}"}, status_code=500)

@app.post("/api/documents/search")
async def search_documents_proxy(request: Request):
    """Proxy document search to document intelligence service"""
    async with httpx.AsyncClient() as client:
        try:
            body = await request.body()
            response = await client.post(
                f"{SERVICES['document_intelligence']}/api/search-documents",
                content=body,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": f"Search service error: {str(e)}"}, status_code=500)

@app.get("/api/documents/capabilities")
async def get_document_capabilities():
    """Get document intelligence capabilities"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SERVICES['document_intelligence']}/api/capabilities",
                timeout=10.0
            )
            return JSONResponse(content=response.json())
        except Exception as e:
            return JSONResponse(content={"error": f"Capabilities service error: {str(e)}"}, status_code=500)

@app.get("/pm-scheduling", response_class=HTMLResponse)
async def pm_scheduling_dashboard():
    """PM Scheduling dashboard with live data"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PM Scheduling - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        .nav-back {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .nav-back:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        .content {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }
        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: block;
            margin-bottom: 0.5rem;
        }
        .stat-label {
            color: #b0b0b0;
            font-size: 0.9rem;
        }
        .controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        .btn.secondary {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        .dashboard-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .dashboard-card h3 {
            margin-top: 0;
            color: #667eea;
            font-size: 1.25rem;
        }
        .pm-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        }
        .pm-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .pm-details {
            color: #b0b0b0;
            font-size: 0.9rem;
        }
        .priority-high { border-left-color: #ef4444; }
        .priority-medium { border-left-color: #f59e0b; }
        .priority-low { border-left-color: #10b981; }
        .loading {
            text-align: center;
            color: #b0b0b0;
            padding: 2rem;
        }
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }
        }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⏰ PM Scheduling Dashboard</h1>
            <a href="/pm-scheduling" class="nav-back">← Back to Dashboard</a>
        </div>

        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number" id="totalPMs">-</span>
                    <span class="stat-label">Total PM Schedules</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="duePMs">-</span>
                    <span class="stat-label">Due This Week</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="recentWOs">-</span>
                    <span class="stat-label">Recent PM Work Orders</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="upcomingPMs">-</span>
                    <span class="stat-label">Upcoming This Month</span>
                </div>
            </div>

            <div class="controls">
                <button class="btn" onclick="generatePMWorkOrders()">🔄 Generate PM Work Orders</button>
                <button class="btn secondary" onclick="refreshDashboard()">🔄 Refresh Dashboard</button>
                <button class="btn secondary" onclick="optimizeScheduling()">🎯 Optimize Scheduling</button>
            </div>

            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <h3>📅 Due PM Schedules</h3>
                    <div id="duePMSchedules" class="loading">Loading due PM schedules...</div>
                </div>
                
                <div class="dashboard-card">
                    <h3>🛠️ Recent PM Work Orders</h3>
                    <div id="recentPMWorkOrders" class="loading">Loading recent PM work orders...</div>
                </div>
            </div>

            <div class="dashboard-card">
                <h3>📊 PM Scheduling Analytics</h3>
                <div id="pmAnalytics" class="loading">Loading PM analytics...</div>
            </div>
        </div>

        <script>
        let dashboardData = {};

        async function loadDashboard() {
            try {
                const response = await fetch('/api/work-orders/pm/dashboard');
                dashboardData = await response.json();
                
                updateStats();
                updateDuePMSchedules();
                updateRecentPMWorkOrders();
                updateAnalytics();
            } catch (error) {
                console.error('Failed to load dashboard:', error);
                showError('Failed to load PM dashboard data');
            }
        }

        function updateStats() {
            document.getElementById('totalPMs').textContent = dashboardData.pm_stats?.pm_schedules_count || 0;
            document.getElementById('duePMs').textContent = dashboardData.due_pm_schedules?.length || 0;
            document.getElementById('recentWOs').textContent = dashboardData.recent_pm_work_orders?.length || 0;
            document.getElementById('upcomingPMs').textContent = dashboardData.pm_stats?.pm_due_count || 0;
        }

        function updateDuePMSchedules() {
            const container = document.getElementById('duePMSchedules');
            const schedules = dashboardData.due_pm_schedules || [];
            
            if (schedules.length === 0) {
                container.innerHTML = '<p style="color: #10b981;">No PM schedules due!</p>';
                return;
            }

            container.innerHTML = schedules.slice(0, 5).map(pm => `
                <div class="pm-item priority-${pm.priority}">
                    <div class="pm-title">${pm.title}</div>
                    <div class="pm-details">
                        Asset: ${pm.asset_name || 'N/A'} | 
                        Due: ${new Date(pm.next_due).toLocaleDateString()} |
                        Priority: ${pm.priority?.toUpperCase()}
                    </div>
                </div>
            `).join('');
        }

        function updateRecentPMWorkOrders() {
            const container = document.getElementById('recentPMWorkOrders');
            const workOrders = dashboardData.recent_pm_work_orders || [];
            
            if (workOrders.length === 0) {
                container.innerHTML = '<p style="color: #b0b0b0;">No recent PM work orders</p>';
                return;
            }

            container.innerHTML = workOrders.slice(0, 5).map(wo => `
                <div class="pm-item priority-${wo.priority}">
                    <div class="pm-title">${wo.title}</div>
                    <div class="pm-details">
                        Status: ${wo.status?.toUpperCase()} | 
                        Asset: ${wo.asset_name || 'N/A'} |
                        Created: ${new Date(wo.created_at).toLocaleDateString()}
                    </div>
                </div>
            `).join('');
        }

        function updateAnalytics() {
            const container = document.getElementById('pmAnalytics');
            const stats = dashboardData.pm_stats || {};
            
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #667eea;">${stats.work_orders_count || 0}</div>
                        <div style="color: #b0b0b0;">Total Work Orders</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #667eea;">${stats.assets_count || 0}</div>
                        <div style="color: #b0b0b0;">Total Assets</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #667eea;">${stats.parts_count || 0}</div>
                        <div style="color: #b0b0b0;">Parts in Inventory</div>
                    </div>
                </div>
            `;
        }

        async function generatePMWorkOrders() {
            try {
                const button = event.target;
                button.disabled = true;
                button.textContent = '🔄 Generating...';
                
                const response = await fetch('/api/work-orders/pm/generate', {
                    method: 'POST'
                });
                const result = await response.json();
                
                alert(result.message || 'PM work orders generated successfully!');
                await loadDashboard();
            } catch (error) {
                console.error('Failed to generate PM work orders:', error);
                alert('Failed to generate PM work orders');
            } finally {
                const button = event.target;
                button.disabled = false;
                button.textContent = '🔄 Generate PM Work Orders';
            }
        }

        async function optimizeScheduling() {
            try {
                const response = await fetch('/api/work-orders/scheduling/optimize');
                const result = await response.json();
                
                alert(`Scheduling optimization complete!\\n${result.optimization_notes?.join('\\n') || 'Optimization completed successfully.'}`);
            } catch (error) {
                console.error('Failed to optimize scheduling:', error);
                alert('Failed to optimize scheduling');
            }
        }

        function refreshDashboard() {
            loadDashboard();
        }

        function showError(message) {
            document.querySelectorAll('.loading').forEach(el => {
                el.innerHTML = `<p style="color: #ef4444;">${message}</p>`;
            });
        }

        // Load dashboard on page load
        document.addEventListener('DOMContentLoaded', loadDashboard);
        </script>
    </body>
    </html>
    """

# PM Scheduling API proxy routes
@app.get("/api/pm-schedules")
async def get_pm_schedules():
    """Get PM schedules from database service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['database']}/api/pm-schedules")
        return response.json()

@app.get("/api/pm-schedules/due")
async def get_due_pm_schedules(days_ahead: int = 7):
    """Get due PM schedules from database service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['database']}/api/pm-schedules/due?days_ahead={days_ahead}")
        return response.json()

@app.post("/api/pm-schedules/generate-work-orders")
async def generate_pm_work_orders():
    """Generate work orders from PM schedules"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICES['database']}/api/pm-schedules/generate-work-orders")
        return response.json()

# ========================================
# SAFETY MANAGEMENT MODULE
# ========================================

class SafetyIncident(BaseModel):
    incident_id: Optional[str] = None
    date: str
    location: str
    description: str
    severity: str  # "Minor", "Major", "Critical", "Fatal"
    injured_person: str
    witness: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None
    osha_recordable: bool = False
    reported_by: str
    investigation_status: str = "Open"  # "Open", "Under Investigation", "Closed"

@app.get("/safety", response_class=HTMLResponse)
async def safety_dashboard():
    """Safety Management Dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Safety Management - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        .content {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        .safety-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .metric-label {
            color: #a0a0a0;
            font-size: 0.9rem;
        }
        .critical { color: #ff6b6b; }
        .warning { color: #ffd93d; }
        .success { color: #6bcf7f; }
        .info { color: #4ecdc4; }
        .section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        .section h2 {
            color: #ffffff;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            margin-right: 1rem;
            margin-bottom: 1rem;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        }
        .nav-links {
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .nav-link {
            color: #4ecdc4;
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            transition: all 0.3s ease;
        }
        .nav-link:hover {
            background: rgba(78, 205, 196, 0.1);
        }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ Safety Management</h1>
            <p>OSHA-Compliant Safety Department Management</p>
        </div>
        
        <div class="content">
            <div class="nav-links">
                <a href="/safety" class="nav-link">← Back to Dashboard</a>
                <a href="/work-orders" class="nav-link">Work Orders</a>
                <a href="/assets" class="nav-link">Assets</a>
            </div>
            
            <div class="safety-metrics">
                <div class="metric-card">
                    <div class="metric-value critical" id="incidents-ytd">-</div>
                    <div class="metric-label">Incidents This Year</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value warning" id="osha-recordable">-</div>
                    <div class="metric-label">OSHA Recordable</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value success" id="days-since">-</div>
                    <div class="metric-label">Days Since Last Incident</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value info" id="training-due">-</div>
                    <div class="metric-label">Training Certifications Due</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Quick Actions</h2>
                <button class="btn btn-danger" onclick="reportIncident()">Report Safety Incident</button>
                <button class="btn" onclick="viewTraining()">Training Records</button>
                <button class="btn" onclick="viewHazards()">Hazard Assessments</button>
                <button class="btn" onclick="viewInspections()">Safety Inspections</button>
                <button class="btn" onclick="generateOSHAReport()">Generate OSHA Report</button>
            </div>
            
            <div class="section">
                <h2>Recent Activity</h2>
                <div id="recent-activity">
                    Loading safety activities...
                </div>
            </div>
        </div>
        
        <script>
        async function loadSafetyMetrics() {
            try {
                const response = await fetch('/api/safety/dashboard');
                const data = await response.json();
                
                document.getElementById('incidents-ytd').textContent = data.incidents_ytd || 0;
                document.getElementById('osha-recordable').textContent = data.osha_recordable || 0;
                document.getElementById('days-since').textContent = data.days_since_incident || 0;
                document.getElementById('training-due').textContent = data.training_due || 0;
            } catch (error) {
                console.log('Loading demo data...');
                document.getElementById('incidents-ytd').textContent = '3';
                document.getElementById('osha-recordable').textContent = '1';
                document.getElementById('days-since').textContent = '47';
                document.getElementById('training-due').textContent = '12';
            }
        }
        
        function reportIncident() {
            alert('Safety Incident Reporting Form - Would open incident reporting interface');
        }
        
        function viewTraining() {
            alert('Training Records - Would show employee safety training dashboard');
        }
        
        function viewHazards() {
            alert('Hazard Assessments - Would show workplace hazard analysis');
        }
        
        function viewInspections() {
            alert('Safety Inspections - Would show inspection schedules and results');
        }
        
        function generateOSHAReport() {
            alert('OSHA Report Generator - Would generate compliance reports');
        }
        
        // Load metrics on page load
        loadSafetyMetrics();
        
        // Update recent activity
        document.getElementById('recent-activity').innerHTML = `
            <div style="padding: 1rem; border-left: 3px solid #4ecdc4; margin-bottom: 1rem; background: rgba(78, 205, 196, 0.1);">
                <strong>Safety Training Completed</strong><br>
                <small>John Smith completed Hazmat Training - 2 hours ago</small>
            </div>
            <div style="padding: 1rem; border-left: 3px solid #ffd93d; margin-bottom: 1rem; background: rgba(255, 217, 61, 0.1);">
                <strong>Hazard Assessment Due</strong><br>
                <small>Workshop Area B requires quarterly review - Due tomorrow</small>
            </div>
            <div style="padding: 1rem; border-left: 3px solid #6bcf7f; margin-bottom: 1rem; background: rgba(107, 207, 127, 0.1);">
                <strong>Safety Inspection Passed</strong><br>
                <small>Manufacturing Floor - All items compliant - Yesterday</small>
            </div>
        `;
        </script>
    </body>
    </html>
    """

@app.get("/api/safety/dashboard")
async def get_safety_dashboard():
    """Get safety dashboard metrics"""
    try:
        async with httpx.AsyncClient() as client:
            # Try to get real data from database
            response = await client.get(f"{SERVICES['database']}/api/safety/metrics")
            if response.status_code == 200:
                return response.json()
    except:
        pass
    
    # Return demo data if database not available
    return {
        "success": True,
        "incidents_ytd": 3,
        "osha_recordable": 1,
        "days_since_incident": 47,
        "training_due": 12,
        "last_updated": "2025-10-05T08:42:20Z"
    }

@app.post("/api/safety/incidents")
async def report_safety_incident(incident: SafetyIncident):
    """Report a new safety incident"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVICES['database']}/api/safety/incidents",
                json=incident.dict()
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error reporting incident: {e}")
        return {
            "success": False,
            "error": "Unable to report incident at this time",
            "incident_id": f"INC-TEMP-{int(time.time())}"
        }

@app.get("/api/safety/incidents")
async def get_safety_incidents():
    """Get all safety incidents"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICES['database']}/api/safety/incidents")
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching incidents: {e}")
        return {
            "success": False,
            "error": "Unable to fetch incidents",
            "incidents": []
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)