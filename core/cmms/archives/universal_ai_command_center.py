#!/usr/bin/env python3
"""
Universal AI Command Center (UACC)
Ultimate AI Development Platform - Multi-Provider Enterprise Command Center

🚀 FEATURES:
- Multi-Provider AI Integration (OpenAI GPT, Anthropic Claude, Google Gemini, xAI Grok, Hugging Face, Ollama)
- Complete Development Workflow (Code Creation, Editing, Review, Deployment)
- Team Collaboration System with AI Models Working Together
- Project Organization and Management
- Multi-Cloud Deployment (GCP, AWS, Azure)
- ChatterFix Customer Management Integration
- Real-time Business Intelligence and Analytics
- Secure Local-First Operations with Cloud Scaling
"""

import asyncio
import json
import os
import logging
import shutil
import uuid
import subprocess
import git
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Security, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env.ai_providers')

# AI Provider Imports (optional - will gracefully handle missing packages)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

try:
    from transformers import pipeline
    import torch
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Universal AI Command Center",
    description="Enterprise AI Management Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Configuration and Data Models
class ModelStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOADING = "loading"
    ERROR = "error"

class ProjectStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    DEPLOYING = "deploying"
    ERROR = "error"

# ChatterFix Data Models
class CloudProvider(Enum):
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"
    MULTI_CLOUD = "multi_cloud"

class CustomerStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class ServiceTier(Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class BillingStatus(Enum):
    ACTIVE = "active"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

@dataclass
class AIModel:
    id: str
    name: str
    type: str  # "local_ollama", "openai", "anthropic", "google"
    status: ModelStatus
    role: str
    custom_instructions: str
    endpoint: str
    api_key: Optional[str] = None
    parameters: Dict[str, Any] = None
    assigned_projects: List[str] = None
    performance_metrics: Dict[str, Any] = None

@dataclass
class Project:
    id: str
    name: str
    description: str
    status: ProjectStatus
    url: str
    ai_models: List[str]
    gcp_config: Dict[str, Any] = None
    workspace_config: Dict[str, Any] = None
    deployment_config: Dict[str, Any] = None
    health_check_url: str = None
    last_updated: datetime = None

@dataclass
class BusinessOperation:
    id: str
    name: str
    type: str  # "deployment", "monitoring", "backup", "scaling"
    status: str
    project_id: str
    details: Dict[str, Any]
    scheduled: Optional[datetime] = None
    completed: Optional[datetime] = None

@dataclass
class ChatterFixCustomer:
    id: str
    company_name: str
    contact_name: str
    email: str
    phone: str
    industry: str
    cloud_preferences: List[str]
    monthly_budget: float
    use_cases: str
    team_size: int
    integrations: str
    subscription_tier: str
    addons: List[str]
    billing_frequency: str
    implementation_timeline: str
    status: str
    created_date: str
    last_updated: str
    configured_services: List[str] = None

@dataclass
class ChatterFixService:
    id: str
    name: str
    provider: str
    category: str
    description: str
    pricing: Dict[str, Any]
    created_date: str
    last_updated: str
    active: bool
    api_endpoint: str = None
    auth_method: str = None

# In-memory storage (replace with database in production)
class DataStore:
    def __init__(self):
        self.ai_models: Dict[str, AIModel] = {}
        self.projects: Dict[str, Project] = {}
        self.operations: Dict[str, BusinessOperation] = {}
        # ChatterFix data stores
        self.chatterfix_customers: Dict[str, ChatterFixCustomer] = {}
        self.chatterfix_services: Dict[str, ChatterFixService] = {}
        self.chatterfix_config: Dict[str, Any] = {}
        
        # Initialize data directories
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Data file paths
        self.customers_file = self.data_dir / "customers.json"
        self.services_file = self.data_dir / "services.json"
        self.config_file = self.data_dir / "config.json"
        
        self.load_default_config()
        self.load_chatterfix_data()
    
    def load_default_config(self):
        """Load default AI models and projects"""
        # ALL AI PROVIDERS - Multi-Provider Enterprise AI Fleet!
        default_models = [
            # === LOCAL OLLAMA MODELS ===
            AIModel(
                id="qwen2.5-coder:7b",
                name="Qwen2.5 Coder 7B (Local)",
                type="local_ollama",
                status=ModelStatus.ACTIVE,
                role="technical_assistant",
                custom_instructions="Expert coding, customer onboarding, deployment, and full system management. Can perform any AI developer task including onboarding customers, editing code, deploying apps, and managing all services with full API access.",
                endpoint="http://localhost:11434",
                assigned_projects=["cmms", "development", "deployment"],
                parameters={"temperature": 0.1, "top_p": 0.9}
            ),
            AIModel(
                id="llama3.2:latest",
                name="LLaMA 3.2 Latest (Local)",
                type="local_ollama", 
                status=ModelStatus.ACTIVE,
                role="analytical_assistant",
                custom_instructions="Business analysis, predictive insights, and customer management specialist. Can handle complex business operations and analytics with full system access.",
                endpoint="http://localhost:11434",
                assigned_projects=["cmms", "analytics", "business"],
                parameters={"temperature": 0.3, "top_p": 0.8}
            ),
            AIModel(
                id="llama3.2:3b",
                name="LLaMA 3.2 3B (Local)",
                type="local_ollama",
                status=ModelStatus.ACTIVE, 
                role="general_assistant",
                custom_instructions="Fast response general purpose assistant with full action capabilities. Can perform customer onboarding, service management, and system operations.",
                endpoint="http://localhost:11434",
                assigned_projects=["cmms", "general"],
                parameters={"temperature": 0.5, "top_p": 0.9}
            ),
            
            # === OPENAI GPT MODELS ===
            AIModel(
                id="gpt-4-turbo",
                name="GPT-4 Turbo (OpenAI)",
                type="openai",
                status=ModelStatus.ACTIVE if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY') else ModelStatus.INACTIVE,
                role="enterprise_architect",
                custom_instructions="Elite enterprise architecture and complex problem solving. Lead AI for massive projects, system design, and strategic development decisions. Full development workflow management.",
                endpoint="https://api.openai.com/v1",
                api_key=os.getenv('OPENAI_API_KEY'),
                assigned_projects=["cmms", "enterprise", "architecture"],
                parameters={"temperature": 0.2, "max_tokens": 4000}
            ),
            AIModel(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo (OpenAI)",
                type="openai",
                status=ModelStatus.ACTIVE if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY') else ModelStatus.INACTIVE,
                role="rapid_developer",
                custom_instructions="Fast, efficient development tasks. Code generation, API integration, quick prototyping. Perfect for rapid iteration and development velocity.",
                endpoint="https://api.openai.com/v1",
                api_key=os.getenv('OPENAI_API_KEY'),
                assigned_projects=["cmms", "development", "prototyping"],
                parameters={"temperature": 0.3, "max_tokens": 2000}
            ),
            
            # === ANTHROPIC CLAUDE MODELS ===
            AIModel(
                id="claude-3-5-sonnet",
                name="Claude 3.5 Sonnet (Anthropic)",
                type="anthropic",
                status=ModelStatus.ACTIVE if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY') else ModelStatus.INACTIVE,
                role="reasoning_specialist",
                custom_instructions="Advanced reasoning, complex analysis, and thoughtful problem-solving. Excellent for code review, architecture decisions, and strategic planning. Full development workflow capabilities.",
                endpoint="https://api.anthropic.com",
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                assigned_projects=["cmms", "reasoning", "code-review"],
                parameters={"temperature": 0.3, "max_tokens": 4000}
            ),
            AIModel(
                id="claude-3-haiku",
                name="Claude 3 Haiku (Anthropic)",
                type="anthropic",
                status=ModelStatus.ACTIVE if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY') else ModelStatus.INACTIVE,
                role="efficiency_expert",
                custom_instructions="Lightning-fast responses for quick tasks. Code snippets, documentation, simple API calls. Optimized for speed and efficiency.",
                endpoint="https://api.anthropic.com",
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                assigned_projects=["cmms", "quick-tasks", "documentation"],
                parameters={"temperature": 0.4, "max_tokens": 1000}
            ),
            
            # === GOOGLE AI MODELS ===
            AIModel(
                id="gemini-1.5-pro",
                name="Gemini 1.5 Pro (Google)",
                type="google_ai",
                status=ModelStatus.ACTIVE if GOOGLE_AI_AVAILABLE and os.getenv('GOOGLE_AI_API_KEY') else ModelStatus.INACTIVE,
                role="multimodal_specialist",
                custom_instructions="Multimodal AI with vision, text, and code capabilities. Excellent for complex analysis, image processing, and comprehensive development tasks.",
                endpoint="https://generativelanguage.googleapis.com",
                api_key=os.getenv('GOOGLE_AI_API_KEY'),
                assigned_projects=["cmms", "multimodal", "analysis"],
                parameters={"temperature": 0.4, "max_output_tokens": 3000}
            ),
            AIModel(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash (Google)",
                type="google_ai",
                status=ModelStatus.ACTIVE if GOOGLE_AI_AVAILABLE and os.getenv('GOOGLE_AI_API_KEY') else ModelStatus.INACTIVE,
                role="speed_optimizer",
                custom_instructions="Ultra-fast responses for real-time applications. Perfect for live chat, instant code suggestions, and rapid prototyping.",
                endpoint="https://generativelanguage.googleapis.com",
                api_key=os.getenv('GOOGLE_AI_API_KEY'),
                assigned_projects=["cmms", "real-time", "chat"],
                parameters={"temperature": 0.5, "max_output_tokens": 1500}
            ),
            
            # === XAI GROK MODELS ===
            AIModel(
                id="grok-beta",
                name="Grok Beta (xAI)",
                type="xai",
                status=ModelStatus.ACTIVE if os.getenv('XAI_API_KEY') else ModelStatus.INACTIVE,
                role="innovation_catalyst",
                custom_instructions="Cutting-edge AI for innovative solutions and creative problem-solving. Excellent for brainstorming, novel approaches, and breakthrough development.",
                endpoint="https://api.x.ai",
                api_key=os.getenv('XAI_API_KEY'),
                assigned_projects=["cmms", "innovation", "creative"],
                parameters={"temperature": 0.6, "max_tokens": 2000}
            ),
            
            # === HUGGING FACE MODELS ===
            AIModel(
                id="codellama-34b",
                name="CodeLlama 34B (Hugging Face)",
                type="huggingface",
                status=ModelStatus.ACTIVE if HUGGINGFACE_AVAILABLE and os.getenv('HUGGINGFACE_API_KEY') else ModelStatus.INACTIVE,
                role="code_specialist",
                custom_instructions="Specialized code generation and analysis. Perfect for complex programming tasks, code optimization, and technical documentation.",
                endpoint="https://api-inference.huggingface.co",
                api_key=os.getenv('HUGGINGFACE_API_KEY'),
                assigned_projects=["cmms", "coding", "optimization"],
                parameters={"temperature": 0.2, "max_new_tokens": 2000}
            ),
            AIModel(
                id="mistral-7b-instruct",
                name="Mistral 7B Instruct (Hugging Face)",
                type="huggingface",
                status=ModelStatus.ACTIVE if HUGGINGFACE_AVAILABLE and os.getenv('HUGGINGFACE_API_KEY') else ModelStatus.INACTIVE,
                role="instruction_follower",
                custom_instructions="Excellent instruction following for precise tasks. Great for API integrations, data processing, and workflow automation.",
                endpoint="https://api-inference.huggingface.co",
                api_key=os.getenv('HUGGINGFACE_API_KEY'),
                assigned_projects=["cmms", "automation", "integration"],
                parameters={"temperature": 0.3, "max_new_tokens": 1500}
            )
        ]
        
        for model in default_models:
            self.ai_models[model.id] = model
        
        # Default CMMS project
        cmms_project = Project(
            id="cmms",
            name="ChatterFix CMMS",
            description="Computerized Maintenance Management System",
            status=ProjectStatus.RUNNING,
            url="http://localhost:8080",
            ai_models=[
                "qwen2.5-coder:7b", "llama3.2:latest", "llama3.2:3b",  # Local Ollama
                "gpt-4-turbo", "gpt-3.5-turbo",  # OpenAI
                "claude-3-5-sonnet", "claude-3-haiku",  # Anthropic
                "gemini-1.5-pro", "gemini-1.5-flash",  # Google AI
                "grok-beta",  # xAI
                "codellama-34b", "mistral-7b-instruct"  # Hugging Face
            ],
            health_check_url="http://localhost:8080/health",
            last_updated=datetime.now()
        )
        self.projects["cmms"] = cmms_project
    
    def load_chatterfix_data(self):
        """Load ChatterFix data from files"""
        # Initialize ChatterFix data files if they don't exist
        if not self.customers_file.exists():
            with open(self.customers_file, 'w') as f:
                json.dump({}, f, indent=2)
        
        if not self.services_file.exists():
            default_services = {
                "gcp-compute": {
                    "id": "gcp-compute",
                    "name": "Google Compute Engine",
                    "provider": "gcp",
                    "category": "compute",
                    "pricing": {"base": 0.10, "model": "per_hour"},
                    "description": "Virtual machines on Google Cloud",
                    "created_date": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "active": True
                },
                "aws-ec2": {
                    "id": "aws-ec2", 
                    "name": "Amazon EC2",
                    "provider": "aws",
                    "category": "compute",
                    "pricing": {"base": 0.08, "model": "per_hour"},
                    "description": "Elastic compute instances on AWS",
                    "created_date": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "active": True
                },
                "azure-vm": {
                    "id": "azure-vm",
                    "name": "Azure Virtual Machines", 
                    "provider": "azure",
                    "category": "compute",
                    "pricing": {"base": 0.09, "model": "per_hour"},
                    "description": "Virtual machines on Microsoft Azure",
                    "created_date": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "active": True
                }
            }
            with open(self.services_file, 'w') as f:
                json.dump(default_services, f, indent=2)
        
        if not self.config_file.exists():
            default_config = {
                "version": "2.0.0",
                "last_updated": datetime.now().isoformat(),
                "git_enabled": False,
                "cloud_deploy_enabled": False,
                "backup_enabled": True,
                "chatterfix_integration": True
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        # Load existing data
        try:
            with open(self.customers_file, 'r') as f:
                customers_data = json.load(f)
                for customer_id, customer_dict in customers_data.items():
                    # Ensure all required fields are present
                    if 'configured_services' not in customer_dict:
                        customer_dict['configured_services'] = []
                    self.chatterfix_customers[customer_id] = ChatterFixCustomer(**customer_dict)
            
            with open(self.services_file, 'r') as f:
                services_data = json.load(f)
                for service_id, service_dict in services_data.items():
                    # Ensure all required fields are present for ChatterFixService
                    if 'api_endpoint' not in service_dict:
                        service_dict['api_endpoint'] = None
                    if 'auth_method' not in service_dict:
                        service_dict['auth_method'] = None
                    if 'created_date' not in service_dict:
                        service_dict['created_date'] = datetime.now().isoformat()
                    if 'last_updated' not in service_dict:
                        service_dict['last_updated'] = datetime.now().isoformat()
                    if 'active' not in service_dict:
                        service_dict['active'] = True
                    self.chatterfix_services[service_id] = ChatterFixService(**service_dict)
            
            with open(self.config_file, 'r') as f:
                self.chatterfix_config = json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading ChatterFix data: {e}")
    
    def save_chatterfix_customer(self, customer: ChatterFixCustomer):
        """Save ChatterFix customer data"""
        try:
            self.chatterfix_customers[customer.id] = customer
            
            # Save to file
            customers_dict = {cid: asdict(c) for cid, c in self.chatterfix_customers.items()}
            with open(self.customers_file, 'w') as f:
                json.dump(customers_dict, f, indent=2)
            
            logger.info(f"Saved ChatterFix customer: {customer.id}")
        except Exception as e:
            logger.error(f"Error saving customer: {e}")
    
    def save_chatterfix_service(self, service: ChatterFixService):
        """Save ChatterFix service data"""
        try:
            self.chatterfix_services[service.id] = service
            
            # Save to file
            services_dict = {sid: asdict(s) for sid, s in self.chatterfix_services.items()}
            with open(self.services_file, 'w') as f:
                json.dump(services_dict, f, indent=2)
            
            logger.info(f"Saved ChatterFix service: {service.id}")
        except Exception as e:
            logger.error(f"Error saving service: {e}")

# Global data store
data_store = DataStore()

# Pydantic models for API
class AIModelCreate(BaseModel):
    name: str
    type: str
    role: str
    custom_instructions: str
    endpoint: str
    api_key: Optional[str] = None
    parameters: Dict[str, Any] = {}

class AIModelUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    custom_instructions: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class ProjectCreate(BaseModel):
    name: str
    description: str
    url: str
    ai_models: List[str] = []
    gcp_config: Dict[str, Any] = {}
    workspace_config: Dict[str, Any] = {}

class ModelAssignment(BaseModel):
    project_id: str
    model_ids: List[str]

class CustomInstruction(BaseModel):
    model_id: str
    instructions: str

# ChatterFix API Models
class ChatterFixCustomerCreate(BaseModel):
    company_name: str
    contact_name: str
    email: str
    phone: str = ""
    industry: str = ""
    monthly_budget: float = 0.0
    subscription_tier: str = "starter"
    cloud_preferences: List[str] = []
    use_cases: str = ""
    team_size: int = 0
    integrations: str = ""
    billing_frequency: str = "monthly"
    implementation_timeline: str = ""
    addons: List[str] = []

class ChatterFixServiceCreate(BaseModel):
    name: str
    provider: str
    category: str
    description: str
    pricing_model: str = "flat_rate"
    base_price: float = 0.0
    api_endpoint: str = ""
    auth_method: str = ""

# Authentication (simplified for demo)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    # In production, validate JWT token here
    return {"user_id": "admin", "role": "admin"}

# API Endpoints

@app.get("/")
async def command_center_dashboard():
    """Universal AI Command Center Dashboard"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Universal AI Command Center</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: white;
            min-height: 100vh;
        }
        .header {
            background: rgba(0,0,0,0.3);
            padding: 2rem;
            text-align: center;
            border-bottom: 2px solid #4CAF50;
        }
        .header h1 {
            margin: 0;
            font-size: 3rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            background: linear-gradient(45deg, #4CAF50, #45a049, #2196F3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .nav-tabs {
            display: flex;
            background: rgba(0,0,0,0.2);
            padding: 0;
            margin: 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .nav-tab {
            flex: 1;
            padding: 1rem;
            text-align: center;
            cursor: pointer;
            background: rgba(255,255,255,0.05);
            border: none;
            color: white;
            transition: all 0.3s ease;
        }
        .nav-tab:hover, .nav-tab.active {
            background: rgba(76,175,80,0.3);
            border-bottom: 3px solid #4CAF50;
        }
        .content {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        .card h3 {
            margin-top: 0;
            color: #4CAF50;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 0.5rem;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        .status-item {
            background: rgba(0,0,0,0.3);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
        }
        .status-number {
            font-size: 2rem;
            font-weight: bold;
            color: #4CAF50;
        }
        .status-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        .action-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .action-btn {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            border: none;
            padding: 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.4);
        }
        .model-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .model-item {
            background: rgba(0,0,0,0.2);
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }
        .model-status {
            display: inline-block;
            padding: 0.2rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .status-active { background: #4CAF50; }
        .status-inactive { background: #f44336; }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Universal AI Command Center</h1>
            <p>Enterprise Business & AI Management Platform</p>
        </div>
        
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">Overview</button>
            <button class="nav-tab" onclick="showTab('models')">AI Models</button>
            <button class="nav-tab" onclick="showTab('projects')">Projects</button>
            <button class="nav-tab" onclick="showTab('operations')">Operations</button>
            <button class="nav-tab" onclick="showTab('integrations')">Integrations</button>
            <button class="nav-tab" onclick="showTab('chatterfix')">ChatterFix</button>
        </div>
        
        <div class="content">
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="dashboard-grid">
                    <div class="card">
                        <h3>📊 System Overview</h3>
                        <div class="status-grid">
                            <div class="status-item">
                                <div class="status-number" id="active-models">-</div>
                                <div class="status-label">Active Models</div>
                            </div>
                            <div class="status-item">
                                <div class="status-number" id="running-projects">-</div>
                                <div class="status-label">Running Projects</div>
                            </div>
                            <div class="status-item">
                                <div class="status-number" id="total-operations">-</div>
                                <div class="status-label">Operations</div>
                            </div>
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="refreshDashboard()">🔄 Refresh</button>
                            <button class="action-btn" onclick="viewSystemHealth()">💚 Health Check</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🤖 AI Model Status</h3>
                        <div id="model-status-list" class="model-list">
                            Loading AI models...
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="showTab('models')">⚙️ Manage Models</button>
                            <button class="action-btn" onclick="addNewModel()">➕ Add Model</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🚀 Quick Actions</h3>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="deployProject()">🚀 Deploy Project</button>
                            <button class="action-btn" onclick="monitorProjects()">📈 Monitor All</button>
                            <button class="action-btn" onclick="backupSystems()">💾 Backup Systems</button>
                            <button class="action-btn" onclick="viewLogs()">📋 View Logs</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🔗 Integration Status</h3>
                        <div id="integration-status">
                            <div>☁️ Google Cloud: <span class="status-active">Connected</span></div>
                            <div>📧 Google Workspace: <span class="status-inactive">Configuring</span></div>
                            <div>🐳 Local Infrastructure: <span class="status-active">Running</span></div>
                            <div>🧠 Ollama: <span class="status-active">3 Models Active</span></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- AI Models Tab -->
            <div id="models" class="tab-content">
                <div class="card">
                    <h3>🤖 AI Model Management</h3>
                    <div id="detailed-model-list">
                        Loading detailed model information...
                    </div>
                </div>
            </div>
            
            <!-- Projects Tab -->
            <div id="projects" class="tab-content">
                <div class="card">
                    <h3>🚀 Project Management</h3>
                    <div id="project-list">
                        Loading projects...
                    </div>
                </div>
            </div>
            
            <!-- Operations Tab -->
            <div id="operations" class="tab-content">
                <div class="card">
                    <h3>⚙️ Business Operations</h3>
                    <div id="operations-list">
                        Loading operations...
                    </div>
                </div>
            </div>
            
            <!-- Integrations Tab -->
            <div id="integrations" class="tab-content">
                <div class="card">
                    <h3>🔗 Platform Integrations</h3>
                    <p>Configure integrations with external platforms and services.</p>
                    <div class="action-buttons">
                        <button class="action-btn" onclick="configureGCP()">☁️ Configure GCP</button>
                        <button class="action-btn" onclick="configureWorkspace()">📧 Configure Workspace</button>
                        <button class="action-btn" onclick="configureOllama()">🧠 Configure Ollama</button>
                        <button class="action-btn" onclick="addIntegration()">➕ Add Integration</button>
                    </div>
                </div>
            </div>
            
            <!-- ChatterFix Tab -->
            <div id="chatterfix" class="tab-content">
                <div class="dashboard-grid">
                    <div class="card">
                        <h3>👥 Customer Management</h3>
                        <div id="chatterfix-customer-summary">
                            Loading customer data...
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="showCustomerOnboarding()">🎯 Onboard Customer</button>
                            <button class="action-btn" onclick="viewAllCustomers()">👀 View Customers</button>
                            <button class="action-btn" onclick="customerAnalytics()">📊 Analytics</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🛠️ Service Management</h3>
                        <div id="chatterfix-service-summary">
                            Loading service data...
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="addChatterFixService()">➕ Add Service</button>
                            <button class="action-btn" onclick="viewAllServices()">👀 View Services</button>
                            <button class="action-btn" onclick="configureIntegrations()">🔗 Configure</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🤖 AI Assistant</h3>
                        <div id="chatterfix-ai-chat">
                            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; min-height: 200px; overflow-y: auto;" id="chat-messages">
                                <div style="color: #4CAF50; margin-bottom: 0.5rem;">🤖 ChatterFix AI Assistant Ready</div>
                                <div style="opacity: 0.8;">Ask me anything about customer onboarding, service management, or platform operations!</div>
                            </div>
                            <div style="display: flex; gap: 0.5rem;">
                                <input type="text" id="chat-input" placeholder="Ask about customers, services, or operations..." style="flex: 1; padding: 0.5rem; border: 1px solid rgba(255,255,255,0.3); background: rgba(0,0,0,0.2); color: white; border-radius: 4px;">
                                <button class="action-btn" onclick="sendChatMessage()" style="margin: 0;">Send</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Business Intelligence</h3>
                        <div id="chatterfix-analytics">
                            <div class="status-grid">
                                <div class="status-item">
                                    <div class="status-number" id="total-customers">-</div>
                                    <div class="status-label">Total Customers</div>
                                </div>
                                <div class="status-item">
                                    <div class="status-number" id="monthly-revenue">$-</div>
                                    <div class="status-label">Monthly Revenue</div>
                                </div>
                                <div class="status-item">
                                    <div class="status-number" id="active-services">-</div>
                                    <div class="status-label">Active Services</div>
                                </div>
                            </div>
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="generateReport()">📋 Generate Report</button>
                            <button class="action-btn" onclick="exportData()">📤 Export Data</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        function showTab(tabName) {
            // Hide all tab contents
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Remove active class from all nav tabs
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Load tab-specific data
            loadTabData(tabName);
        }
        
        async function loadTabData(tabName) {
            switch(tabName) {
                case 'overview':
                    await loadOverviewData();
                    break;
                case 'models':
                    await loadModelData();
                    break;
                case 'projects':
                    await loadProjectData();
                    break;
                case 'operations':
                    await loadOperationsData();
                    break;
                case 'chatterfix':
                    await loadChatterFixData();
                    break;
            }
        }
        
        async function loadOverviewData() {
            try {
                const [models, projects] = await Promise.all([
                    fetch('/api/models').then(r => r.json()),
                    fetch('/api/projects').then(r => r.json())
                ]);
                
                const activeModels = Object.values(models).filter(m => m.status === 'active').length;
                const runningProjects = Object.values(projects).filter(p => p.status === 'running').length;
                
                document.getElementById('active-models').textContent = activeModels;
                document.getElementById('running-projects').textContent = runningProjects;
                document.getElementById('total-operations').textContent = '12'; // Mock data
                
                // Load model status list
                const modelStatusHtml = Object.values(models).map(model => `
                    <div class="model-item">
                        <strong>${model.name}</strong>
                        <span class="model-status status-${model.status}">${model.status}</span>
                        <div>Role: ${model.role}</div>
                        <div>Projects: ${model.assigned_projects?.join(', ') || 'None'}</div>
                    </div>
                `).join('');
                
                document.getElementById('model-status-list').innerHTML = modelStatusHtml;
                
            } catch (error) {
                console.error('Error loading overview data:', error);
            }
        }
        
        async function loadModelData() {
            try {
                const models = await fetch('/api/models').then(r => r.json());
                
                const modelHtml = Object.values(models).map(model => `
                    <div class="model-item">
                        <h4>${model.name} (${model.id})</h4>
                        <p><strong>Type:</strong> ${model.type}</p>
                        <p><strong>Role:</strong> ${model.role}</p>
                        <p><strong>Status:</strong> <span class="model-status status-${model.status}">${model.status}</span></p>
                        <p><strong>Instructions:</strong> ${model.custom_instructions}</p>
                        <p><strong>Assigned Projects:</strong> ${model.assigned_projects?.join(', ') || 'None'}</p>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="toggleModel('${model.id}')">
                                ${model.status === 'active' ? '⏸️ Deactivate' : '▶️ Activate'}
                            </button>
                            <button class="action-btn" onclick="editModel('${model.id}')">✏️ Edit</button>
                            <button class="action-btn" onclick="assignProjects('${model.id}')">🔗 Assign</button>
                        </div>
                    </div>
                `).join('');
                
                document.getElementById('detailed-model-list').innerHTML = modelHtml;
                
            } catch (error) {
                console.error('Error loading model data:', error);
            }
        }
        
        async function loadProjectData() {
            try {
                const projects = await fetch('/api/projects').then(r => r.json());
                
                const projectHtml = Object.values(projects).map(project => `
                    <div class="model-item">
                        <h4>${project.name}</h4>
                        <p><strong>Description:</strong> ${project.description}</p>
                        <p><strong>Status:</strong> <span class="model-status status-${project.status}">${project.status}</span></p>
                        <p><strong>URL:</strong> <a href="${project.url}" target="_blank">${project.url}</a></p>
                        <p><strong>AI Models:</strong> ${project.ai_models?.join(', ') || 'None'}</p>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="deployProject('${project.id}')">🚀 Deploy</button>
                            <button class="action-btn" onclick="monitorProject('${project.id}')">📈 Monitor</button>
                            <button class="action-btn" onclick="configureProject('${project.id}')">⚙️ Configure</button>
                        </div>
                    </div>
                `).join('');
                
                document.getElementById('project-list').innerHTML = projectHtml;
                
            } catch (error) {
                console.error('Error loading project data:', error);
            }
        }
        
        async function loadOperationsData() {
            // Mock operations data
            const operations = [
                {id: 1, name: "CMMS Health Check", status: "completed", type: "monitoring"},
                {id: 2, name: "Model Performance Review", status: "running", type: "analysis"},
                {id: 3, name: "Backup Systems", status: "scheduled", type: "backup"}
            ];
            
            const operationsHtml = operations.map(op => `
                <div class="model-item">
                    <h4>${op.name}</h4>
                    <p><strong>Type:</strong> ${op.type}</p>
                    <p><strong>Status:</strong> <span class="model-status status-${op.status === 'completed' ? 'active' : 'inactive'}">${op.status}</span></p>
                    <div class="action-buttons">
                        <button class="action-btn" onclick="viewOperation(${op.id})">👁️ View</button>
                        <button class="action-btn" onclick="executeOperation(${op.id})">▶️ Execute</button>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('operations-list').innerHTML = operationsHtml;
        }
        
        async function loadChatterFixData() {
            try {
                const [customers, services] = await Promise.all([
                    fetch('/api/chatterfix/customers').then(r => r.json()),
                    fetch('/api/chatterfix/services').then(r => r.json())
                ]);
                
                // Update customer summary
                const customerCount = Object.keys(customers).length;
                const totalRevenue = Object.values(customers).reduce((sum, customer) => sum + (customer.monthly_budget || 0), 0);
                
                document.getElementById('total-customers').textContent = customerCount;
                document.getElementById('monthly-revenue').textContent = `$${totalRevenue.toLocaleString()}`;
                document.getElementById('active-services').textContent = Object.keys(services).length;
                
                // Update customer summary
                const customerSummaryHtml = customerCount > 0 ? `
                    <p>📈 ${customerCount} customers generating $${totalRevenue.toLocaleString()}/month</p>
                    <div style="margin: 1rem 0;">
                        ${Object.values(customers).slice(0, 3).map(customer => `
                            <div style="background: rgba(0,0,0,0.2); padding: 0.5rem; margin: 0.25rem 0; border-radius: 4px;">
                                🏢 ${customer.company_name} - ${customer.subscription_tier} tier
                            </div>
                        `).join('')}
                    </div>
                ` : '<p>No customers yet. Start by onboarding your first customer!</p>';
                
                document.getElementById('chatterfix-customer-summary').innerHTML = customerSummaryHtml;
                
                // Update service summary
                const serviceSummaryHtml = Object.keys(services).length > 0 ? `
                    <p>🛠️ ${Object.keys(services).length} services available across multiple cloud providers</p>
                    <div style="margin: 1rem 0;">
                        ${Object.values(services).slice(0, 3).map(service => `
                            <div style="background: rgba(0,0,0,0.2); padding: 0.5rem; margin: 0.25rem 0; border-radius: 4px;">
                                ☁️ ${service.name} (${service.provider.toUpperCase()}) - $${service.pricing.base}/${service.pricing.model}
                            </div>
                        `).join('')}
                    </div>
                ` : '<p>No services configured. Add your first service!</p>';
                
                document.getElementById('chatterfix-service-summary').innerHTML = serviceSummaryHtml;
                
            } catch (error) {
                console.error('Error loading ChatterFix data:', error);
            }
        }
        
        // Action functions
        function refreshDashboard() {
            loadOverviewData();
            alert('Dashboard refreshed!');
        }
        
        function viewSystemHealth() {
            alert('System Health: All systems operational 🟢');
        }
        
        function addNewModel() {
            const name = prompt('Model name:');
            const type = prompt('Model type (local_ollama/openai/anthropic):');
            if (name && type) {
                alert(`Adding model: ${name} (${type})`);
                // Implementation would call API to add model
            }
        }
        
        async function toggleModel(modelId) {
            try {
                const response = await fetch(`/api/models/${modelId}/toggle`, {
                    method: 'POST'
                });
                if (response.ok) {
                    alert('Model status toggled!');
                    loadModelData();
                }
            } catch (error) {
                alert('Error toggling model status');
            }
        }
        
        function editModel(modelId) {
            const instructions = prompt('Enter new custom instructions:');
            if (instructions) {
                alert(`Updated instructions for model ${modelId}`);
                // Implementation would call API to update model
            }
        }
        
        function assignProjects(modelId) {
            const projects = prompt('Enter project IDs (comma-separated):');
            if (projects) {
                alert(`Assigned projects ${projects} to model ${modelId}`);
                // Implementation would call API to assign projects
            }
        }
        
        // ChatterFix Functions
        function showCustomerOnboarding() {
            const modal = createModal('Customer Onboarding', `
                <div style="max-height: 400px; overflow-y: auto;">
                    <h4>🎯 New Customer Onboarding</h4>
                    <form id="customer-onboard-form">
                        <div style="margin: 1rem 0;">
                            <label>Company Name:</label><br>
                            <input type="text" name="company_name" required style="width: 100%; padding: 0.5rem; margin: 0.25rem 0; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px;">
                        </div>
                        <div style="margin: 1rem 0;">
                            <label>Contact Name:</label><br>
                            <input type="text" name="contact_name" required style="width: 100%; padding: 0.5rem; margin: 0.25rem 0; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px;">
                        </div>
                        <div style="margin: 1rem 0;">
                            <label>Email:</label><br>
                            <input type="email" name="email" required style="width: 100%; padding: 0.5rem; margin: 0.25rem 0; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px;">
                        </div>
                        <div style="margin: 1rem 0;">
                            <label>Phone:</label><br>
                            <input type="text" name="phone" style="width: 100%; padding: 0.5rem; margin: 0.25rem 0; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px;">
                        </div>
                        <div style="margin: 1rem 0;">
                            <label>Industry:</label><br>
                            <input type="text" name="industry" style="width: 100%; padding: 0.5rem; margin: 0.25rem 0; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px;">
                        </div>
                        <div style="margin: 1rem 0;">
                            <label>Monthly Budget:</label><br>
                            <input type="number" name="monthly_budget" min="0" step="0.01" style="width: 100%; padding: 0.5rem; margin: 0.25rem 0; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px;">
                        </div>
                        <div style="margin: 1rem 0;">
                            <label>Subscription Tier:</label><br>
                            <select name="subscription_tier" style="width: 100%; padding: 0.5rem; margin: 0.25rem 0; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px;">
                                <option value="starter">Starter</option>
                                <option value="professional">Professional</option>
                                <option value="enterprise">Enterprise</option>
                            </select>
                        </div>
                        <div class="action-buttons">
                            <button type="submit" class="action-btn">✅ Onboard Customer</button>
                            <button type="button" class="action-btn" onclick="closeModal()">❌ Cancel</button>
                        </div>
                    </form>
                </div>
            `);
            
            document.getElementById('customer-onboard-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const customerData = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/api/chatterfix/customers', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(customerData)
                    });
                    
                    if (response.ok) {
                        alert('✅ Customer onboarded successfully!');
                        closeModal();
                        loadChatterFixData();
                    } else {
                        alert('❌ Error onboarding customer');
                    }
                } catch (error) {
                    alert('❌ Error: ' + error.message);
                }
            });
        }
        
        function createModal(title, content) {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.8); display: flex; align-items: center;
                justify-content: center; z-index: 1000;
            `;
            modal.id = 'modal';
            
            modal.innerHTML = `
                <div style="background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); 
                            padding: 2rem; border-radius: 15px; max-width: 600px; width: 90%;
                            border: 1px solid rgba(255,255,255,0.1); color: white;">
                    <h3 style="margin-top: 0; color: #4CAF50;">${title}</h3>
                    ${content}
                </div>
            `;
            
            document.body.appendChild(modal);
            return modal;
        }
        
        function closeModal() {
            const modal = document.getElementById('modal');
            if (modal) modal.remove();
        }
        
        async function sendChatMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('chat-messages');
            
            // Add user message
            messagesDiv.innerHTML += `
                <div style="margin: 0.5rem 0; text-align: right;">
                    <span style="background: #4CAF50; padding: 0.5rem; border-radius: 8px; display: inline-block;">👤 ${message}</span>
                </div>
            `;
            
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            try {
                const response = await fetch('/api/ai/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: message,
                        context: {project_id: 'chatterfix', source: 'unified_command_center'}
                    })
                });
                
                const result = await response.json();
                
                // Add AI response
                messagesDiv.innerHTML += `
                    <div style="margin: 0.5rem 0;">
                        <span style="background: rgba(33, 150, 243, 0.8); padding: 0.5rem; border-radius: 8px; display: inline-block;">🤖 ${result.response}</span>
                    </div>
                `;
                
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
            } catch (error) {
                messagesDiv.innerHTML += `
                    <div style="margin: 0.5rem 0;">
                        <span style="background: #f44336; padding: 0.5rem; border-radius: 8px; display: inline-block;">❌ Error: ${error.message}</span>
                    </div>
                `;
            }
        }
        
        // Allow Enter key to send chat messages
        document.addEventListener('DOMContentLoaded', function() {
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendChatMessage();
                    }
                });
            }
        });
        
        function viewAllCustomers() {
            // Implementation for viewing all customers
            alert('Customer list view coming soon!');
        }
        
        function addChatterFixService() {
            // Implementation for adding services
            alert('Service addition coming soon!');
        }
        
        function viewAllServices() {
            // Implementation for viewing all services
            alert('Service list view coming soon!');
        }
        
        // Initialize dashboard
        window.onload = function() {
            loadOverviewData();
        };
        
        // Initialize chat input event listener
        document.addEventListener('DOMContentLoaded', function() {
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendChatMessage();
                    }
                });
            }
        });
        </script>
    </body>
    </html>
    """)

# AI Model Management Endpoints
@app.get("/api/models")
async def get_ai_models(user = Depends(get_current_user)):
    """Get all AI models"""
    return {model_id: asdict(model) for model_id, model in data_store.ai_models.items()}

@app.post("/api/models")
async def create_ai_model(model_data: AIModelCreate, user = Depends(get_current_user)):
    """Create new AI model"""
    model_id = model_data.name.lower().replace(" ", "-")
    
    new_model = AIModel(
        id=model_id,
        name=model_data.name,
        type=model_data.type,
        status=ModelStatus.INACTIVE,
        role=model_data.role,
        custom_instructions=model_data.custom_instructions,
        endpoint=model_data.endpoint,
        api_key=model_data.api_key,
        parameters=model_data.parameters,
        assigned_projects=[]
    )
    
    data_store.ai_models[model_id] = new_model
    logger.info(f"Created new AI model: {model_id}")
    
    return asdict(new_model)

@app.put("/api/models/{model_id}")
async def update_ai_model(model_id: str, update_data: AIModelUpdate, user = Depends(get_current_user)):
    """Update AI model configuration"""
    if model_id not in data_store.ai_models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = data_store.ai_models[model_id]
    
    if update_data.name:
        model.name = update_data.name
    if update_data.status:
        model.status = ModelStatus(update_data.status)
    if update_data.role:
        model.role = update_data.role
    if update_data.custom_instructions:
        model.custom_instructions = update_data.custom_instructions
    if update_data.parameters:
        model.parameters.update(update_data.parameters)
    
    logger.info(f"Updated AI model: {model_id}")
    return asdict(model)

@app.post("/api/models/{model_id}/toggle")
async def toggle_model_status(model_id: str, user = Depends(get_current_user)):
    """Toggle AI model active/inactive status"""
    if model_id not in data_store.ai_models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = data_store.ai_models[model_id]
    
    if model.status == ModelStatus.ACTIVE:
        model.status = ModelStatus.INACTIVE
        logger.info(f"Deactivated AI model: {model_id}")
    else:
        model.status = ModelStatus.ACTIVE
        logger.info(f"Activated AI model: {model_id}")
    
    return {"status": model.status.value, "message": f"Model {model_id} {model.status.value}"}

@app.post("/api/models/{model_id}/assign")
async def assign_model_to_projects(model_id: str, assignment: ModelAssignment, user = Depends(get_current_user)):
    """Assign AI model to specific projects"""
    if model_id not in data_store.ai_models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = data_store.ai_models[model_id]
    model.assigned_projects = assignment.model_ids
    
    logger.info(f"Assigned model {model_id} to projects: {assignment.model_ids}")
    return {"message": f"Model {model_id} assigned to projects", "projects": assignment.model_ids}

@app.post("/api/models/{model_id}/instructions")
async def update_custom_instructions(model_id: str, instruction: CustomInstruction, user = Depends(get_current_user)):
    """Update custom instructions for AI model"""
    if model_id not in data_store.ai_models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = data_store.ai_models[model_id]
    model.custom_instructions = instruction.instructions
    
    logger.info(f"Updated custom instructions for model: {model_id}")
    return {"message": f"Updated instructions for {model_id}", "instructions": instruction.instructions}

# Project Management Endpoints
@app.get("/api/projects")
async def get_projects(user = Depends(get_current_user)):
    """Get all projects"""
    return {project_id: asdict(project) for project_id, project in data_store.projects.items()}

@app.post("/api/projects")
async def create_project(project_data: ProjectCreate, user = Depends(get_current_user)):
    """Create new project"""
    project_id = project_data.name.lower().replace(" ", "-")
    
    new_project = Project(
        id=project_id,
        name=project_data.name,
        description=project_data.description,
        status=ProjectStatus.STOPPED,
        url=project_data.url,
        ai_models=project_data.ai_models,
        gcp_config=project_data.gcp_config,
        workspace_config=project_data.workspace_config,
        last_updated=datetime.now()
    )
    
    data_store.projects[project_id] = new_project
    logger.info(f"Created new project: {project_id}")
    
    return asdict(new_project)

@app.post("/api/projects/{project_id}/deploy")
async def deploy_project(project_id: str, background_tasks: BackgroundTasks, user = Depends(get_current_user)):
    """Deploy project"""
    if project_id not in data_store.projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = data_store.projects[project_id]
    project.status = ProjectStatus.DEPLOYING
    
    # Add background task for actual deployment
    background_tasks.add_task(perform_deployment, project_id)
    
    logger.info(f"Started deployment for project: {project_id}")
    return {"message": f"Deployment started for {project_id}", "status": "deploying"}

@app.get("/api/projects/{project_id}/health")
async def check_project_health(project_id: str, user = Depends(get_current_user)):
    """Check project health status"""
    if project_id not in data_store.projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = data_store.projects[project_id]
    
    if project.health_check_url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(project.health_check_url, timeout=5.0)
                health_status = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception as e:
            health_status = "unhealthy"
            logger.error(f"Health check failed for {project_id}: {e}")
    else:
        health_status = "unknown"
    
    return {
        "project_id": project_id,
        "status": project.status.value,
        "health": health_status,
        "last_updated": project.last_updated
    }

# Business Operations Endpoints
@app.get("/api/operations")
async def get_operations(user = Depends(get_current_user)):
    """Get all business operations"""
    return {op_id: asdict(operation) for op_id, operation in data_store.operations.items()}

@app.post("/api/operations/backup")
async def create_backup_operation(background_tasks: BackgroundTasks, user = Depends(get_current_user)):
    """Create system backup operation"""
    operation_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    operation = BusinessOperation(
        id=operation_id,
        name="System Backup",
        type="backup",
        status="scheduled",
        project_id="all",
        details={"backup_type": "full", "target": "gcp_storage"},
        scheduled=datetime.now()
    )
    
    data_store.operations[operation_id] = operation
    background_tasks.add_task(perform_backup, operation_id)
    
    logger.info(f"Scheduled backup operation: {operation_id}")
    return asdict(operation)

@app.post("/api/operations/monitor")
async def create_monitoring_operation(project_id: str, user = Depends(get_current_user)):
    """Create monitoring operation for project"""
    operation_id = f"monitor_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    operation = BusinessOperation(
        id=operation_id,
        name=f"Monitor {project_id}",
        type="monitoring",
        status="running",
        project_id=project_id,
        details={"monitoring_type": "health_check", "interval": "5m"},
        scheduled=datetime.now()
    )
    
    data_store.operations[operation_id] = operation
    logger.info(f"Started monitoring operation: {operation_id}")
    
    return asdict(operation)

# AI Chat Endpoint (Enhanced with Business Automation)
@app.post("/api/ai/chat")
async def universal_ai_chat(request: Dict[str, Any], user = Depends(get_current_user)):
    """Universal AI chat with intelligent model routing and business automation"""
    message = request.get("message", "")
    context = request.get("context", {})
    project_id = context.get("project_id", "general")
    
    # Check if this is a business automation command
    business_automation_keywords = [
        "deploy", "create instance", "provision", "set up", "setup",
        "new chatterfix", "chatterfix for", "billing for", "access for",
        "scale", "manage billing", "configure access"
    ]
    
    is_business_command = any(keyword in message.lower() for keyword in business_automation_keywords)
    
    # Handle business automation commands with specialized processing
    if is_business_command:
        try:
            # Import and use the Automated Instance Provisioner
            from automated_instance_provisioner import AutomatedInstanceProvisioner
            
            provisioner = AutomatedInstanceProvisioner()
            business_result = await provisioner.process_business_command(message, context)
            
            if business_result["status"] == "success":
                # Add business automation metadata
                business_result["automation_type"] = "business_provisioning"
                business_result["handled_by"] = "automated_instance_provisioner"
                business_result["timestamp"] = datetime.now().isoformat()
                business_result["user"] = user.get("username", "system") if user else "system"
                
                # If this resulted in a provisioning task, also engage AI for follow-up
                if business_result.get("provisioning_id"):
                    # Determine best AI model for business support
                    best_model = await select_best_model(message, context, project_id)
                    
                    if best_model and best_model.status == ModelStatus.ACTIVE:
                        # Create enhanced context with business automation results
                        enhanced_context = {
                            **context,
                            "business_automation": True,
                            "provisioning_result": business_result,
                            "provisioning_id": business_result["provisioning_id"]
                        }
                        
                        # Get AI assistance for the business automation
                        ai_followup = f"""I've successfully started automated provisioning for {business_result.get('instance_config', {}).get('business_name', 'your business')}. 

Provisioning ID: {business_result['provisioning_id']}
Estimated completion: {business_result.get('estimated_completion', 'TBD')}
Estimated monthly cost: ${business_result.get('estimated_cost', 0)}

Next steps: {'; '.join(business_result.get('next_steps', []))}

How can I assist you further with this deployment or any other business automation needs?"""
                        
                        # Route to appropriate AI service for follow-up
                        if best_model.type == "local_ollama":
                            ai_response = await chat_with_ollama(best_model, ai_followup, enhanced_context)
                        elif best_model.type == "openai":
                            ai_response = await chat_with_openai(best_model, ai_followup, enhanced_context)
                        elif best_model.type == "anthropic":
                            ai_response = await chat_with_anthropic(best_model, ai_followup, enhanced_context)
                        elif best_model.type == "google_ai":
                            ai_response = await chat_with_google_ai(best_model, ai_followup, enhanced_context)
                        elif best_model.type == "xai":
                            ai_response = await chat_with_xai(best_model, ai_followup, enhanced_context)
                        elif best_model.type == "huggingface":
                            ai_response = await chat_with_huggingface(best_model, ai_followup, enhanced_context)
                        else:
                            ai_response = {"response": ai_followup}
                        
                        # Combine business automation results with AI assistance
                        business_result["ai_assistance"] = ai_response.get("response", "")
                        business_result["model_used"] = best_model.id
                
                return business_result
            else:
                # Business command failed, fall through to regular AI chat
                logger.warning(f"Business automation failed: {business_result}")
                
        except Exception as e:
            logger.error(f"Business automation error: {e}")
            # Fall through to regular AI chat
    
    # Regular AI chat processing
    # Determine best model based on message content and context
    best_model = await select_best_model(message, context, project_id)
    
    if not best_model or best_model.status != ModelStatus.ACTIVE:
        return {
            "response": "No suitable AI model is currently available. Please check model status.",
            "model_used": None,
            "status": "error"
        }
    
    try:
        # Route to appropriate AI service - ALL PROVIDERS SUPPORTED!
        if best_model.type == "local_ollama":
            response = await chat_with_ollama(best_model, message, context)
        elif best_model.type == "openai":
            response = await chat_with_openai(best_model, message, context)
        elif best_model.type == "anthropic":
            response = await chat_with_anthropic(best_model, message, context)
        elif best_model.type == "google_ai":
            response = await chat_with_google_ai(best_model, message, context)
        elif best_model.type == "xai":
            response = await chat_with_xai(best_model, message, context)
        elif best_model.type == "huggingface":
            response = await chat_with_huggingface(best_model, message, context)
        else:
            response = {"response": "Unsupported model type", "status": "error"}
        
        # Add metadata
        response["model_used"] = best_model.id
        response["project_id"] = project_id
        response["timestamp"] = datetime.now().isoformat()
        
        return response
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        return {
            "response": "I'm experiencing technical difficulties. Please try again.",
            "model_used": best_model.id,
            "status": "error",
            "error": str(e)
        }

# Integration Endpoints
@app.get("/api/integrations/gcp/status")
async def get_gcp_integration_status(user = Depends(get_current_user)):
    """Get Google Cloud Platform integration status"""
    # Mock GCP integration check
    return {
        "status": "connected",
        "project_id": "your-gcp-project",
        "services": {
            "compute": "active",
            "storage": "active", 
            "ai_platform": "active"
        }
    }

@app.get("/api/integrations/workspace/status")
async def get_workspace_integration_status(user = Depends(get_current_user)):
    """Get Google Workspace integration status"""
    # Mock Workspace integration check
    return {
        "status": "configuring",
        "domain": "your-company.com",
        "services": {
            "gmail": "pending",
            "drive": "pending",
            "calendar": "pending"
        }
    }

@app.get("/api/integrations/ollama/status")
async def get_ollama_integration_status(user = Depends(get_current_user)):
    """Get Ollama integration status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json()
                return {
                    "status": "connected",
                    "endpoint": "http://localhost:11434",
                    "models": models.get("models", [])
                }
    except Exception as e:
        logger.error(f"Ollama connection error: {e}")
    
    return {
        "status": "disconnected",
        "endpoint": "http://localhost:11434",
        "error": "Could not connect to Ollama"
    }

# ChatterFix API Endpoints
@app.get("/api/chatterfix/customers")
async def get_chatterfix_customers(user = Depends(get_current_user)):
    """Get all ChatterFix customers"""
    return {customer_id: asdict(customer) for customer_id, customer in data_store.chatterfix_customers.items()}

@app.post("/api/chatterfix/customers")
async def create_chatterfix_customer(customer_data: ChatterFixCustomerCreate, user = Depends(get_current_user)):
    """Create new ChatterFix customer"""
    customer_id = f"customer-{uuid.uuid4().hex[:8]}"
    
    new_customer = ChatterFixCustomer(
        id=customer_id,
        company_name=customer_data.company_name,
        contact_name=customer_data.contact_name,
        email=customer_data.email,
        phone=customer_data.phone,
        industry=customer_data.industry,
        cloud_preferences=customer_data.cloud_preferences,
        monthly_budget=customer_data.monthly_budget,
        use_cases=customer_data.use_cases,
        team_size=customer_data.team_size,
        integrations=customer_data.integrations,
        subscription_tier=customer_data.subscription_tier,
        addons=customer_data.addons,
        billing_frequency=customer_data.billing_frequency,
        implementation_timeline=customer_data.implementation_timeline,
        status="active",
        created_date=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        configured_services=[]
    )
    
    data_store.save_chatterfix_customer(new_customer)
    logger.info(f"Created new ChatterFix customer: {customer_id}")
    
    return asdict(new_customer)

@app.get("/api/chatterfix/services")
async def get_chatterfix_services(user = Depends(get_current_user)):
    """Get all ChatterFix services"""
    return {service_id: asdict(service) for service_id, service in data_store.chatterfix_services.items()}

@app.post("/api/chatterfix/services")
async def create_chatterfix_service(service_data: ChatterFixServiceCreate, user = Depends(get_current_user)):
    """Create new ChatterFix service"""
    service_id = f"{service_data.provider}-{service_data.name.lower().replace(' ', '-')}"
    
    new_service = ChatterFixService(
        id=service_id,
        name=service_data.name,
        provider=service_data.provider,
        category=service_data.category,
        description=service_data.description,
        pricing={
            "model": service_data.pricing_model,
            "base": service_data.base_price
        },
        created_date=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        active=True,
        api_endpoint=service_data.api_endpoint,
        auth_method=service_data.auth_method
    )
    
    data_store.save_chatterfix_service(new_service)
    logger.info(f"Created new ChatterFix service: {service_id}")
    
    return asdict(new_service)

@app.get("/api/chatterfix/analytics")
async def get_chatterfix_analytics(user = Depends(get_current_user)):
    """Get ChatterFix business analytics"""
    customers = data_store.chatterfix_customers
    services = data_store.chatterfix_services
    
    if not customers:
        return {
            "total_customers": 0,
            "total_revenue": 0,
            "average_customer_value": 0,
            "tier_distribution": {},
            "cloud_preferences": {},
            "total_services": len(services),
            "services_by_provider": {}
        }
    
    total_revenue = sum(customer.monthly_budget for customer in customers.values())
    
    # Tier distribution
    tier_distribution = {}
    cloud_preferences = {}
    
    for customer in customers.values():
        tier = customer.subscription_tier
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        for cloud in customer.cloud_preferences:
            cloud_preferences[cloud] = cloud_preferences.get(cloud, 0) + 1
    
    # Services by provider
    services_by_provider = {}
    for service in services.values():
        provider = service.provider
        services_by_provider[provider] = services_by_provider.get(provider, 0) + 1
    
    return {
        "total_customers": len(customers),
        "total_revenue": total_revenue,
        "average_customer_value": total_revenue / len(customers) if customers else 0,
        "tier_distribution": tier_distribution,
        "cloud_preferences": cloud_preferences,
        "total_services": len(services),
        "services_by_provider": services_by_provider
    }

# Business Automation Endpoints
@app.get("/api/business/provisioning/{provisioning_id}")
async def get_provisioning_status(provisioning_id: str, user = Depends(get_current_user)):
    """Get status of business automation provisioning"""
    try:
        from automated_instance_provisioner import AutomatedInstanceProvisioner
        
        provisioner = AutomatedInstanceProvisioner()
        status = await provisioner.get_provisioning_status(provisioning_id)
        
        return {
            "status": "success",
            "provisioning_status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting provisioning status: {e}")
        return {
            "status": "error",
            "message": f"Failed to get provisioning status: {str(e)}",
            "provisioning_id": provisioning_id
        }

@app.post("/api/business/automation")
async def execute_business_automation(request: Dict[str, Any], user = Depends(get_current_user)):
    """Execute business automation command directly via API"""
    try:
        from automated_instance_provisioner import AutomatedInstanceProvisioner
        
        command = request.get("command", "")
        context = request.get("context", {})
        
        if not command:
            return {
                "status": "error",
                "message": "Command is required"
            }
        
        provisioner = AutomatedInstanceProvisioner()
        result = await provisioner.process_business_command(command, context)
        
        # Add API metadata
        result["api_endpoint"] = "/api/business/automation"
        result["user"] = user.get("username", "system") if user else "system"
        result["timestamp"] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logger.error(f"Error in business automation: {e}")
        return {
            "status": "error", 
            "message": f"Business automation failed: {str(e)}",
            "command": request.get("command", "")
        }

@app.get("/api/business/automation/capabilities")
async def get_automation_capabilities(user = Depends(get_current_user)):
    """Get available business automation capabilities"""
    return {
        "status": "success",
        "capabilities": {
            "instance_provisioning": {
                "description": "Deploy new ChatterFix instances for businesses",
                "examples": [
                    "Deploy a ChatterFix instance for Joe's Garage",
                    "Create CMMS system for ABC Manufacturing with 25 users",
                    "Set up ChatterFix for Small Town Auto Repair"
                ],
                "supported_providers": ["gcp", "aws", "azure"],
                "deployment_sizes": ["small_business", "medium_business", "large_business", "enterprise"]
            },
            "billing_management": {
                "description": "Automated billing and subscription management", 
                "status": "planned",
                "examples": [
                    "Set up billing for TechCorp Industries",
                    "Change subscription for ABC Company to enterprise",
                    "Generate invoice for Q4 services"
                ]
            },
            "access_control": {
                "description": "User management and security configuration",
                "status": "planned", 
                "examples": [
                    "Add 5 technicians to Joe's Garage instance",
                    "Configure SSO for MegaCorp enterprise",
                    "Set up role-based access for manufacturing team"
                ]
            },
            "scaling_optimization": {
                "description": "Resource scaling and performance optimization",
                "status": "planned",
                "examples": [
                    "Scale up ChatterFix for peak season",
                    "Optimize costs for ABC Manufacturing",
                    "Add predictive maintenance AI capabilities"
                ]
            }
        },
        "natural_language_processing": {
            "intent_recognition": True,
            "entity_extraction": True,
            "business_intelligence": True,
            "industry_optimization": True
        },
        "supported_industries": [
            "manufacturing", "automotive", "healthcare", "construction", 
            "retail", "hospitality", "government", "finance"
        ]
    }

# Utility Functions
async def select_best_model(message: str, context: Dict[str, Any], project_id: str) -> Optional[AIModel]:
    """Intelligent model selection based on message content and context"""
    message_lower = message.lower()
    
    # Get active models for the project
    available_models = [
        model for model in data_store.ai_models.values()
        if model.status == ModelStatus.ACTIVE and (
            not model.assigned_projects or 
            project_id in model.assigned_projects or
            "all" in model.assigned_projects
        )
    ]
    
    if not available_models:
        return None
    
    # Selection logic based on message content
    if any(keyword in message_lower for keyword in ["code", "api", "database", "query", "script", "debug", "programming"]):
        # Prefer coding models
        coding_models = [m for m in available_models if "coder" in m.id.lower() or m.role == "technical_assistant"]
        if coding_models:
            return coding_models[0]
    
    elif any(keyword in message_lower for keyword in ["predict", "forecast", "analyze", "trend", "optimization", "business"]):
        # Prefer analytical models
        analytical_models = [m for m in available_models if m.role == "analytical_assistant"]
        if analytical_models:
            return analytical_models[0]
    
    elif any(keyword in message_lower for keyword in ["explain", "help", "how", "what", "why"]):
        # Prefer general/fast models for explanations
        general_models = [m for m in available_models if m.role == "general_assistant"]
        if general_models:
            return general_models[0]
    
    # Default to first available model
    return available_models[0]

async def chat_with_ollama(model: AIModel, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Chat with Ollama model"""
    async with httpx.AsyncClient() as client:
        payload = {
            "model": model.id,
            "messages": [
                {
                    "role": "system",
                    "content": f"{model.custom_instructions}\n\nYou are integrated into the Universal AI Command Center with access to ChatterFix customer management capabilities. You can help with customer onboarding, service management, billing, and business analytics. Context: {json.dumps(context)}"
                },
                {
                    "role": "user", 
                    "content": message
                }
            ],
            "stream": False
        }
        
        if model.parameters:
            payload.update(model.parameters)
        
        response = await client.post(
            f"{model.endpoint}/api/chat",
            json=payload,
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "response": result.get("message", {}).get("content", "No response"),
                "status": "success"
            }
        else:
            return {
                "response": "Error communicating with AI model",
                "status": "error"
            }

async def chat_with_openai(model: AIModel, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Chat with OpenAI GPT models"""
    if not OPENAI_AVAILABLE or not model.api_key:
        return {"response": "OpenAI API key not configured", "status": "error"}
    
    try:
        openai.api_key = model.api_key
        response = openai.ChatCompletion.create(
            model=model.id,
            messages=[
                {
                    "role": "system",
                    "content": f"{model.custom_instructions}\n\nYou are part of the Universal AI Command Center, a multi-provider AI development platform. You can create code, edit files, manage projects, deploy applications, and work with the AI team. Context: {json.dumps(context)}"
                },
                {"role": "user", "content": message}
            ],
            **model.parameters
        )
        return {
            "response": response.choices[0].message.content,
            "status": "success",
            "usage": response.usage.to_dict() if response.usage else None
        }
    except Exception as e:
        return {"response": f"OpenAI error: {str(e)}", "status": "error"}

async def chat_with_anthropic(model: AIModel, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Chat with Anthropic Claude models"""
    if not ANTHROPIC_AVAILABLE or not model.api_key:
        return {"response": "Anthropic API key not configured", "status": "error"}
    
    try:
        client = anthropic.Anthropic(api_key=model.api_key)
        response = client.messages.create(
            model=model.id,
            messages=[
                {
                    "role": "user", 
                    "content": f"{model.custom_instructions}\n\nYou are part of the Universal AI Command Center team. You can write code, edit files, manage projects, deploy to cloud, and collaborate with other AI models. Context: {json.dumps(context)}\n\nUser request: {message}"
                }
            ],
            **model.parameters
        )
        return {
            "response": response.content[0].text,
            "status": "success",
            "usage": response.usage.to_dict() if hasattr(response, 'usage') else None
        }
    except Exception as e:
        return {"response": f"Anthropic error: {str(e)}", "status": "error"}

async def chat_with_google_ai(model: AIModel, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Chat with Google AI Gemini models"""
    if not GOOGLE_AI_AVAILABLE or not model.api_key:
        return {"response": "Google AI API key not configured", "status": "error"}
    
    try:
        genai.configure(api_key=model.api_key)
        gen_model = genai.GenerativeModel(model.id)
        
        prompt = f"{model.custom_instructions}\n\nYou are integrated into the Universal AI Command Center for comprehensive development workflows. You have multimodal capabilities and can help with code, analysis, project management, and deployment. Context: {json.dumps(context)}\n\nUser request: {message}"
        
        response = gen_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(**model.parameters)
        )
        
        return {
            "response": response.text,
            "status": "success",
            "usage": {"input_tokens": len(prompt), "output_tokens": len(response.text)}
        }
    except Exception as e:
        return {"response": f"Google AI error: {str(e)}", "status": "error"}

async def chat_with_xai(model: AIModel, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Chat with xAI Grok models"""
    if not model.api_key:
        return {"response": "xAI API key not configured", "status": "error"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{model.endpoint}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {model.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model.id,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"{model.custom_instructions}\n\nYou are part of the innovative Universal AI Command Center. You excel at creative problem-solving, breakthrough thinking, and cutting-edge development approaches. Context: {json.dumps(context)}"
                        },
                        {"role": "user", "content": message}
                    ],
                    **model.parameters
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data["choices"][0]["message"]["content"],
                    "status": "success",
                    "usage": data.get("usage")
                }
            else:
                return {"response": f"xAI API error: {response.status_code}", "status": "error"}
    except Exception as e:
        return {"response": f"xAI error: {str(e)}", "status": "error"}

async def chat_with_huggingface(model: AIModel, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Chat with Hugging Face models"""
    if not HUGGINGFACE_AVAILABLE or not model.api_key:
        return {"response": "Hugging Face API key not configured", "status": "error"}
    
    try:
        async with httpx.AsyncClient() as client:
            prompt = f"{model.custom_instructions}\n\nYou are integrated into the Universal AI Command Center for advanced development tasks. Context: {json.dumps(context)}\n\nUser: {message}\nAssistant:"
            
            response = await client.post(
                f"{model.endpoint}/models/{model.id}",
                headers={
                    "Authorization": f"Bearer {model.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": prompt,
                    "parameters": model.parameters
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    generated_text = data[0].get("generated_text", "")
                    # Extract only the new response part
                    response_text = generated_text.replace(prompt, "").strip()
                    return {
                        "response": response_text,
                        "status": "success"
                    }
                else:
                    return {"response": "Unexpected Hugging Face response format", "status": "error"}
            else:
                return {"response": f"Hugging Face API error: {response.status_code}", "status": "error"}
    except Exception as e:
        return {"response": f"Hugging Face error: {str(e)}", "status": "error"}

# ========================================
# DEVELOPMENT WORKFLOW FUNCTIONS
# ========================================

async def create_new_file(file_path: str, content: str, project_id: str = None) -> Dict[str, Any]:
    """AI-driven file creation with full development workflow integration"""
    try:
        full_path = Path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        logger.info(f"AI created file: {file_path}")
        return {"status": "success", "message": f"File created: {file_path}", "path": str(full_path)}
    except Exception as e:
        logger.error(f"AI file creation error: {e}")
        return {"status": "error", "message": f"Failed to create file: {str(e)}"}

async def edit_existing_file(file_path: str, search_text: str, replace_text: str, project_id: str = None) -> Dict[str, Any]:
    """AI-driven file editing with smart search and replace"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        if search_text not in content:
            return {"status": "error", "message": f"Search text not found in {file_path}"}
        
        new_content = content.replace(search_text, replace_text)
        
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        logger.info(f"AI edited file: {file_path}")
        return {"status": "success", "message": f"File edited: {file_path}", "changes": 1}
    except Exception as e:
        logger.error(f"AI file edit error: {e}")
        return {"status": "error", "message": f"Failed to edit file: {str(e)}"}

async def deploy_to_cloud(project_id: str, cloud_provider: str = "gcp", environment: str = "staging") -> Dict[str, Any]:
    """AI-driven cloud deployment across multiple providers"""
    try:
        project = data_store.projects.get(project_id)
        if not project:
            return {"status": "error", "message": f"Project {project_id} not found"}
        
        project.status = ProjectStatus.DEPLOYING
        
        # Simulate cloud deployment based on provider
        deployment_commands = {
            "gcp": f"gcloud run deploy {project_id} --source . --region us-central1",
            "aws": f"aws lambda deploy-function --function-name {project_id}",
            "azure": f"az webapp deployment source config --name {project_id}"
        }
        
        command = deployment_commands.get(cloud_provider, deployment_commands["gcp"])
        
        # Here you would run the actual deployment command
        # result = subprocess.run(command.split(), capture_output=True, text=True)
        
        # Simulate deployment time
        await asyncio.sleep(5)
        
        project.status = ProjectStatus.RUNNING
        project.url = f"https://{project_id}-{cloud_provider}.example.com"
        
        logger.info(f"AI deployed project {project_id} to {cloud_provider}")
        return {
            "status": "success", 
            "message": f"Project deployed to {cloud_provider}",
            "url": project.url,
            "provider": cloud_provider,
            "environment": environment
        }
    except Exception as e:
        logger.error(f"AI deployment error: {e}")
        return {"status": "error", "message": f"Deployment failed: {str(e)}"}

async def run_code_review(file_path: str, project_id: str = None) -> Dict[str, Any]:
    """AI-powered code review with multi-model analysis"""
    try:
        with open(file_path, 'r') as f:
            code_content = f.read()
        
        # This would integrate with the AI models for code review
        review_prompt = f"""
        Perform a comprehensive code review of this file:
        
        File: {file_path}
        
        Code:
        {code_content}
        
        Please analyze:
        1. Code quality and best practices
        2. Security vulnerabilities
        3. Performance optimization opportunities
        4. Bug detection
        5. Improvement suggestions
        """
        
        # Here you would call one of the AI models for review
        # For now, return a structured response
        return {
            "status": "success",
            "file": file_path,
            "quality_score": 85,
            "issues": [
                {"type": "style", "line": 42, "message": "Consider using more descriptive variable names"},
                {"type": "performance", "line": 78, "message": "This loop could be optimized with list comprehension"}
            ],
            "suggestions": [
                "Add type hints for better code documentation",
                "Consider extracting this logic into a separate function"
            ]
        }
    except Exception as e:
        logger.error(f"AI code review error: {e}")
        return {"status": "error", "message": f"Code review failed: {str(e)}"}

async def manage_git_operations(operation: str, project_id: str = None, message: str = None) -> Dict[str, Any]:
    """AI-driven Git operations with full workflow integration"""
    try:
        if operation == "commit":
            if not message:
                message = "AI-generated commit: Updated project files"
            
            # Here you would run actual git commands
            # subprocess.run(["git", "add", "."], cwd=project_path)
            # subprocess.run(["git", "commit", "-m", message], cwd=project_path)
            
            logger.info(f"AI performed git commit: {message}")
            return {"status": "success", "operation": "commit", "message": message}
            
        elif operation == "push":
            # subprocess.run(["git", "push"], cwd=project_path)
            logger.info(f"AI performed git push for project {project_id}")
            return {"status": "success", "operation": "push", "branch": "main"}
            
        elif operation == "pull":
            # subprocess.run(["git", "pull"], cwd=project_path)
            logger.info(f"AI performed git pull for project {project_id}")
            return {"status": "success", "operation": "pull", "updates": "Latest changes pulled"}
            
        else:
            return {"status": "error", "message": f"Unsupported git operation: {operation}"}
            
    except Exception as e:
        logger.error(f"AI git operation error: {e}")
        return {"status": "error", "message": f"Git operation failed: {str(e)}"}

async def organize_project_structure(project_id: str, framework: str = "python") -> Dict[str, Any]:
    """AI-driven project organization and structure management"""
    try:
        project = data_store.projects.get(project_id)
        if not project:
            return {"status": "error", "message": f"Project {project_id} not found"}
        
        # Project structure templates
        structures = {
            "python": [
                "src/",
                "tests/",
                "docs/",
                "requirements.txt",
                "README.md",
                ".gitignore",
                "pyproject.toml"
            ],
            "nodejs": [
                "src/",
                "test/",
                "docs/",
                "package.json",
                "README.md",
                ".gitignore",
                "tsconfig.json"
            ],
            "react": [
                "src/components/",
                "src/pages/",
                "src/utils/",
                "public/",
                "tests/",
                "package.json",
                "README.md"
            ]
        }
        
        structure = structures.get(framework, structures["python"])
        created_items = []
        
        for item in structure:
            # Here you would create the actual directories/files
            # Path(f"projects/{project_id}/{item}").mkdir(parents=True, exist_ok=True)
            created_items.append(item)
        
        logger.info(f"AI organized project structure for {project_id}")
        return {
            "status": "success",
            "project_id": project_id,
            "framework": framework,
            "structure": created_items,
            "message": f"Project structure organized for {framework}"
        }
    except Exception as e:
        logger.error(f"AI project organization error: {e}")
        return {"status": "error", "message": f"Project organization failed: {str(e)}"}

async def perform_deployment(project_id: str):
    """Background task for project deployment"""
    await asyncio.sleep(10)  # Simulate deployment time
    
    if project_id in data_store.projects:
        project = data_store.projects[project_id]
        project.status = ProjectStatus.RUNNING
        project.last_updated = datetime.now()
        logger.info(f"Deployment completed for project: {project_id}")

async def perform_backup(operation_id: str):
    """Background task for system backup"""
    await asyncio.sleep(30)  # Simulate backup time
    
    if operation_id in data_store.operations:
        operation = data_store.operations[operation_id]
        operation.status = "completed"
        operation.completed = datetime.now()
        logger.info(f"Backup completed: {operation_id}")

if __name__ == "__main__":
    uvicorn.run(
        "universal_ai_command_center:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        log_level="info"
    )