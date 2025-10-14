# AI LOOK 🤖
## Complete Development Reference for ChatterFix CMMS & Fix It Fred AI Platform

> **Professional AI Model Reference Guide**
> 
> This document provides comprehensive platform architecture, development patterns, and implementation guidelines for the ChatterFix CMMS and Fix It Fred AI ecosystem. Use this as your complete reference when developing, maintaining, or extending the platform.

---

## 📋 TABLE OF CONTENTS

1. [Platform Overview](#platform-overview)
2. [Architecture Map](#architecture-map)
3. [Database Schemas](#database-schemas)
4. [API Reference](#api-reference)
5. [Frontend Components](#frontend-components)
6. [Styling Guide](#styling-guide)
7. [AI Integration](#ai-integration)
8. [Development Workflows](#development-workflows)
9. [Deployment Guide](#deployment-guide)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ PLATFORM OVERVIEW

### Core Systems
- **ChatterFix CMMS**: Complete maintenance management system
- **Fix It Fred AI**: Advanced AI assistant for maintenance operations
- **Microservices Architecture**: Scalable, containerized services
- **Real-time Analytics**: Live performance monitoring and insights

### Technology Stack
```yaml
Backend:
  - Python 3.13+ (FastAPI, SQLAlchemy, Pydantic)
  - PostgreSQL (Primary database)
  - SQLite (Development/Testing)
  - Redis (Caching & Sessions)
  - Docker (Containerization)

Frontend:
  - HTML5/CSS3/JavaScript (ES6+)
  - Bootstrap 5.3+ (UI Framework)
  - Chart.js (Analytics visualization)
  - Progressive Web App (PWA) capabilities

AI/ML:
  - Ollama (Local AI models)
  - OpenAI GPT-4/GPT-3.5-turbo
  - Anthropic Claude
  - Google Gemini
  - xAI Grok

Infrastructure:
  - Google Cloud Run (Production)
  - Docker Compose (Development)
  - GitHub Actions (CI/CD)
  - Nginx (Reverse proxy)
```

---

## 🏛️ ARCHITECTURE MAP

### Service Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    ChatterFix CMMS Platform                │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Port 8000)                                      │
│  ├── UI Gateway Service                                    │
│  ├── Static Assets                                         │
│  └── Progressive Web App                                   │
├─────────────────────────────────────────────────────────────┤
│  Core Microservices                                        │
│  ├── Database Service (Port 8001)                         │
│  ├── Work Orders Service (Port 8002)                      │
│  ├── Assets Service (Port 8003)                           │
│  ├── Parts Service (Port 8004)                            │
│  ├── Fix It Fred AI Service (Port 8005)                   │
│  ├── Document Intelligence (Port 8006)                    │
│  ├── Enterprise Security (Port 8007)                      │
│  └── AI Development Team (Port 8008)                      │
├─────────────────────────────────────────────────────────────┤
│  External Integrations                                     │
│  ├── Ollama (Port 11434)                                  │
│  ├── OpenAI API                                           │
│  ├── Anthropic API                                        │
│  └── Cloud Storage                                        │
└─────────────────────────────────────────────────────────────┘
```

### File Structure
```
ai-tools/
├── core/
│   └── cmms/
│       ├── platform_gateway.py          # Main gateway service
│       ├── ai_brain_service.py           # AI orchestration
│       ├── database_service.py           # Database operations
│       ├── work_orders_service.py        # Work order management
│       ├── assets_service.py             # Asset tracking
│       ├── parts_service.py              # Inventory management
│       ├── templates/                    # HTML templates
│       │   ├── dashboard.html
│       │   ├── work_orders.html
│       │   ├── assets.html
│       │   └── analytics.html
│       └── static/                       # CSS/JS assets
│           ├── css/
│           └── js/
├── fix_it_fred_ai_service.py            # Main AI service
├── fix_it_fred_chatterfix_integration.js # Frontend integration
├── cmms_schema.sql                      # Database schema
├── docker-compose.yml                   # Container orchestration
└── deploy-chatterfix-production.sh     # Production deployment
```

---

## 🗄️ DATABASE SCHEMAS

### Core Tables

#### 1. Work Orders
```sql
CREATE TABLE work_orders (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    asset_id INTEGER REFERENCES assets(id),
    assigned_to VARCHAR(100),
    priority work_order_priority DEFAULT 'medium',
    status work_order_status DEFAULT 'open',
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    parts_cost DECIMAL(10,2),
    labor_cost DECIMAL(10,2),
    completion_notes TEXT,
    safety_notes TEXT
);
```

#### 2. Assets
```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    asset_tag VARCHAR(100) UNIQUE,
    description TEXT,
    location VARCHAR(255),
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    serial_number VARCHAR(255),
    purchase_date DATE,
    purchase_cost DECIMAL(12,2),
    current_value DECIMAL(12,2),
    status asset_status DEFAULT 'active',
    maintenance_schedule maintenance_frequency,
    last_maintenance_date TIMESTAMP,
    next_maintenance_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. Parts Inventory
```sql
CREATE TABLE parts (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    manufacturer VARCHAR(255),
    supplier VARCHAR(255),
    current_stock INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 0,
    max_stock_level INTEGER DEFAULT 100,
    unit_cost DECIMAL(10,2),
    location VARCHAR(255),
    last_ordered TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. AI Chat Sessions
```sql
CREATE TABLE ai_chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    context VARCHAR(100),
    messages JSONB,
    ai_provider VARCHAR(50),
    model_used VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_tokens INTEGER,
    cost DECIMAL(10,4)
);
```

### Database Connection Patterns
```python
# Standard connection pattern
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost/chatterfix_cmms"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 🔌 API REFERENCE

### Authentication
All APIs use Bearer token authentication:
```
Authorization: Bearer <jwt_token>
```

### Core Endpoints

#### Platform Gateway (Port 8000)
```python
# Health Check
GET /health
Response: {"status": "healthy", "gateway": "ChatterFix Platform Gateway"}

# Dashboard
GET /dashboard
Response: HTML dashboard interface

# API Proxy
POST /api/{service}/{endpoint}
Headers: {"Authorization": "Bearer <token>"}
```

#### Database Service (Port 8001)
```python
# Database Health
GET /health
Response: {"status": "healthy", "database_type": "postgresql", "tables": 25}

# Execute Query
POST /api/query
Body: {"query": "SELECT * FROM work_orders", "params": {}}
Response: {"success": true, "data": [...], "count": 150}

# Bulk Operations
POST /api/bulk
Body: {"operation": "insert", "table": "parts", "data": [...]}
```

#### Work Orders Service (Port 8002)
```python
# List Work Orders
GET /api/work-orders
Query: ?status=open&priority=high&limit=50
Response: {"work_orders": [...], "total": 150, "page": 1}

# Create Work Order
POST /api/work-orders
Body: {
    "title": "Replace motor bearings",
    "asset_id": 123,
    "priority": "high",
    "assigned_to": "john_smith",
    "due_date": "2025-10-20T14:00:00Z"
}

# Update Work Order
PUT /api/work-orders/{id}
Body: {"status": "in_progress", "actual_hours": 3.5}

# AI Optimization
POST /api/work-orders/optimize
Body: {"optimization_type": "schedule", "timeframe": "week"}
```

#### Assets Service (Port 8003)
```python
# Asset Dashboard
GET /api/assets/dashboard
Response: {
    "total_assets": 500,
    "active_assets": 450,
    "maintenance_due": 25,
    "critical_alerts": 3
}

# Asset Details
GET /api/assets/{id}
Response: {
    "asset": {...},
    "maintenance_history": [...],
    "upcoming_maintenance": [...],
    "performance_metrics": {...}
}

# Predictive Analytics
POST /api/assets/predict-failure
Body: {"asset_id": 123, "prediction_window": "30_days"}
```

#### Parts Service (Port 8004)
```python
# Inventory Status
GET /api/parts/inventory
Response: {
    "total_parts": 1500,
    "low_stock_alerts": 25,
    "out_of_stock": 5,
    "pending_orders": 10
}

# Smart Reordering
POST /api/parts/auto-reorder
Body: {"approval_required": true, "budget_limit": 5000}

# Parts Lookup
GET /api/parts/search
Query: ?q=bearing&category=mechanical&in_stock=true
```

#### Fix It Fred AI Service (Port 8005)
```python
# AI Chat
POST /api/chat
Body: {
    "message": "How do I troubleshoot a pump failure?",
    "context": "maintenance",
    "provider": "ollama",
    "model": "mistral:7b"
}
Response: {
    "success": true,
    "response": "Here's how to troubleshoot pump failure...",
    "provider": "ollama",
    "model": "mistral:7b",
    "timestamp": "2025-10-14T10:30:00Z"
}

# Provider Configuration
POST /api/providers/{provider}/configure
Body: {"api_key": "sk-...", "enabled": true}

# Cache Statistics
GET /api/cache/stats
Response: {
    "cache_hits": 150,
    "cache_misses": 50,
    "hit_rate_percent": 75.0
}
```

---

## 🎨 FRONTEND COMPONENTS

### Core UI Components

#### 1. Dashboard Layout
```html
<div class="dashboard-container">
    <header class="dashboard-header">
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">
                    <i class="fas fa-wrench"></i> ChatterFix CMMS
                </a>
                <div class="navbar-nav ms-auto">
                    <span class="nav-text">Welcome, {user}</span>
                    <a class="nav-link" href="/logout">Logout</a>
                </div>
            </div>
        </nav>
    </header>
    
    <div class="dashboard-content">
        <aside class="sidebar">
            <nav class="nav flex-column">
                <a class="nav-link active" href="/dashboard">
                    <i class="fas fa-tachometer-alt"></i> Dashboard
                </a>
                <a class="nav-link" href="/work-orders">
                    <i class="fas fa-clipboard-list"></i> Work Orders
                </a>
                <a class="nav-link" href="/assets">
                    <i class="fas fa-industry"></i> Assets
                </a>
                <a class="nav-link" href="/parts">
                    <i class="fas fa-cogs"></i> Parts
                </a>
                <a class="nav-link" href="/analytics">
                    <i class="fas fa-chart-bar"></i> Analytics
                </a>
            </nav>
        </aside>
        
        <main class="main-content">
            <div id="content-area">
                <!-- Dynamic content loaded here -->
            </div>
        </main>
    </div>
</div>
```

#### 2. Work Order Card Component
```html
<div class="work-order-card" data-priority="{priority}">
    <div class="card-header">
        <div class="work-order-title">
            <h5>{title}</h5>
            <span class="badge badge-{priority}">{priority}</span>
        </div>
        <div class="work-order-meta">
            <span class="asset-tag">Asset: {asset_tag}</span>
            <span class="due-date">Due: {due_date}</span>
        </div>
    </div>
    
    <div class="card-body">
        <p class="description">{description}</p>
        <div class="assignment-info">
            <span class="assigned-to">Assigned: {assigned_to}</span>
            <span class="estimated-hours">{estimated_hours}h estimated</span>
        </div>
    </div>
    
    <div class="card-footer">
        <div class="action-buttons">
            <button class="btn btn-primary btn-sm" onclick="startWorkOrder({id})">
                Start Work
            </button>
            <button class="btn btn-outline-secondary btn-sm" onclick="viewDetails({id})">
                Details
            </button>
            <button class="btn btn-success btn-sm" onclick="completeWorkOrder({id})">
                Complete
            </button>
        </div>
    </div>
</div>
```

#### 3. AI Chat Widget
```html
<div id="ai-chat-widget" class="chat-widget">
    <div class="chat-header">
        <div class="chat-title">
            <i class="fas fa-robot"></i>
            <span>Fix It Fred AI</span>
        </div>
        <button class="chat-toggle" onclick="toggleChat()">
            <i class="fas fa-comment"></i>
        </button>
    </div>
    
    <div class="chat-body" id="chat-messages">
        <div class="message assistant-message">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>Hi! I'm Fix It Fred, your AI maintenance assistant. How can I help you today?</p>
            </div>
        </div>
    </div>
    
    <div class="chat-footer">
        <div class="input-group">
            <input type="text" id="chat-input" class="form-control" 
                   placeholder="Ask about maintenance, safety, or equipment..."
                   onkeypress="handleChatEnter(event)">
            <button class="btn btn-primary" onclick="sendChatMessage()">
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
    </div>
</div>
```

---

## 🎨 STYLING GUIDE

### Color Palette
```css
:root {
    /* Primary Brand Colors */
    --primary-blue: #006fee;
    --primary-blue-dark: #0056b3;
    --primary-blue-light: #4285f4;
    
    /* Secondary Colors */
    --success-green: #28a745;
    --warning-orange: #fd7e14;
    --danger-red: #dc3545;
    --info-blue: #17a2b8;
    
    /* Neutral Colors */
    --gray-100: #f8f9fa;
    --gray-200: #e9ecef;
    --gray-300: #dee2e6;
    --gray-400: #ced4da;
    --gray-500: #adb5bd;
    --gray-600: #6c757d;
    --gray-700: #495057;
    --gray-800: #343a40;
    --gray-900: #212529;
    
    /* Status Colors */
    --status-open: #17a2b8;
    --status-in-progress: #fd7e14;
    --status-completed: #28a745;
    --status-cancelled: #6c757d;
    
    /* Priority Colors */
    --priority-low: #28a745;
    --priority-medium: #ffc107;
    --priority-high: #fd7e14;
    --priority-critical: #dc3545;
}
```

### Typography
```css
/* Base Typography */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    color: var(--gray-800);
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    color: var(--gray-900);
    margin-bottom: 0.5rem;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.75rem; }
h4 { font-size: 1.5rem; }
h5 { font-size: 1.25rem; }
h6 { font-size: 1rem; }

/* Text Utilities */
.text-primary { color: var(--primary-blue) !important; }
.text-success { color: var(--success-green) !important; }
.text-warning { color: var(--warning-orange) !important; }
.text-danger { color: var(--danger-red) !important; }
```

### Component Styles

#### Buttons
```css
.btn {
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    font-weight: 500;
    text-decoration: none;
    border: 1px solid transparent;
    transition: all 0.15s ease-in-out;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light));
    border-color: var(--primary-blue);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 111, 238, 0.3);
}

.btn-success {
    background: linear-gradient(135deg, var(--success-green), #20c997);
    border-color: var(--success-green);
    color: white;
}
```

#### Cards
```css
.card {
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: box-shadow 0.15s ease-in-out;
}

.card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
    padding: 1rem;
    border-bottom: 1px solid var(--gray-200);
    background: var(--gray-100);
    border-radius: 0.5rem 0.5rem 0 0;
}

.card-body {
    padding: 1rem;
}

.card-footer {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--gray-200);
    background: var(--gray-50);
}
```

#### Status Badges
```css
.badge {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 0.375rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-open { background: var(--status-open); color: white; }
.badge-in-progress { background: var(--status-in-progress); color: white; }
.badge-completed { background: var(--status-completed); color: white; }
.badge-cancelled { background: var(--status-cancelled); color: white; }

.badge-low { background: var(--priority-low); color: white; }
.badge-medium { background: var(--priority-medium); color: var(--gray-800); }
.badge-high { background: var(--priority-high); color: white; }
.badge-critical { background: var(--priority-critical); color: white; }
```

---

## 🤖 AI INTEGRATION

### Fix It Fred AI Architecture

#### Core AI Service Configuration
```python
# AI Provider Settings
AI_PROVIDERS = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "models": ["mistral:7b", "llama3:8b", "codellama:7b"],
        "enabled": True,
        "local": True
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
        "enabled": False,
        "api_key_required": True
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "enabled": False,
        "api_key_required": True
    }
}

# Fix It Fred Personality Prompt
FRED_SYSTEM_PROMPT = """
You are Fix It Fred, an expert CMMS maintenance assistant with deep knowledge of:
- Industrial equipment troubleshooting
- Preventive and predictive maintenance
- Safety protocols and OSHA compliance
- Parts identification and inventory management
- Cost-effective maintenance strategies

Always provide:
1. Safety-first recommendations
2. Clear, actionable steps
3. Cost considerations
4. Preventive measures
5. Reference to ChatterFix CMMS features when relevant

Keep responses concise but comprehensive.
"""
```

#### AI Chat Integration Pattern
```javascript
class FixItFredAI {
    constructor() {
        this.apiBase = 'http://localhost:8005';
        this.defaultProvider = 'ollama';
        this.contextMemory = [];
    }

    async sendMessage(message, context = 'maintenance') {
        // Build context from conversation history
        const conversationContext = this.buildContext(message, context);
        
        try {
            const response = await fetch(`${this.apiBase}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: conversationContext,
                    context: context,
                    provider: this.defaultProvider,
                    temperature: 0.7,
                    max_tokens: 1000
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateContextMemory(message, data.response);
                return this.formatResponse(data);
            }
        } catch (error) {
            return this.handleError(error, message);
        }
    }

    buildContext(message, context) {
        const recentHistory = this.contextMemory.slice(-3);
        const contextPrefix = `Context: ${context}\nRecent conversation:\n${
            recentHistory.map(h => `User: ${h.user}\nFred: ${h.assistant}`).join('\n')
        }\n\nCurrent question: ${message}`;
        
        return contextPrefix;
    }
}
```

---

## ⚙️ DEVELOPMENT WORKFLOWS

### 1. Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd ai-tools

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python3 core/cmms/database_service.py --init-db

# Start development services
docker-compose up -d  # For external services (PostgreSQL, Redis)
python3 core/cmms/platform_gateway.py  # Main gateway
python3 fix_it_fred_ai_service.py      # AI service
```

### 2. Adding New Features

#### Backend Service Pattern
```python
# New service template
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import logging

app = FastAPI(title="New Service", version="1.0.0")
logger = logging.getLogger(__name__)

class RequestModel(BaseModel):
    field1: str
    field2: Optional[int] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "new-service"}

@app.post("/api/endpoint")
async def new_endpoint(request: RequestModel):
    try:
        # Business logic here
        result = process_request(request)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8009))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

#### Frontend Component Pattern
```javascript
// Component class template
class NewComponent {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.apiBase = '/api/new-service';
        this.init();
    }

    async init() {
        await this.loadData();
        this.render();
        this.attachEventListeners();
    }

    async loadData() {
        try {
            const response = await fetch(`${this.apiBase}/data`);
            this.data = await response.json();
        } catch (error) {
            console.error('Failed to load data:', error);
            this.showError('Failed to load data');
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="component-header">
                <h3>New Component</h3>
            </div>
            <div class="component-body">
                ${this.renderContent()}
            </div>
        `;
    }

    renderContent() {
        return this.data.map(item => `
            <div class="item-card" data-id="${item.id}">
                <h5>${item.title}</h5>
                <p>${item.description}</p>
            </div>
        `).join('');
    }

    attachEventListeners() {
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('item-card')) {
                this.handleItemClick(e.target.dataset.id);
            }
        });
    }
}
```

### 3. Database Migration Pattern
```python
# Migration script template
import psycopg2
from datetime import datetime

def run_migration(connection_string):
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    
    try:
        # Migration SQL
        migration_sql = """
        -- Add new column
        ALTER TABLE work_orders 
        ADD COLUMN new_field VARCHAR(255);
        
        -- Create index
        CREATE INDEX idx_work_orders_new_field 
        ON work_orders(new_field);
        
        -- Update migration log
        INSERT INTO schema_migrations (version, applied_at) 
        VALUES ('20251014_add_new_field', CURRENT_TIMESTAMP);
        """
        
        cursor.execute(migration_sql)
        conn.commit()
        print(f"Migration completed successfully at {datetime.now()}")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
```

---

## 🚀 DEPLOYMENT GUIDE

### Production Deployment (Google Cloud Run)

#### 1. Docker Configuration
```dockerfile
# Dockerfile template
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Run application
CMD ["python", "core/cmms/platform_gateway.py"]
```

#### 2. Cloud Run Deployment Script
```bash
#!/bin/bash
# deploy-production.sh

set -e

PROJECT_ID="chatterfix-cmms"
SERVICE_NAME="chatterfix-platform"
REGION="us-central1"

echo "🚀 Deploying ChatterFix CMMS to Google Cloud Run..."

# Build and push container
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars "DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL" \
    --port 8080

echo "✅ Deployment completed!"
echo "🌐 Service URL: $(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')"
```

### 3. Environment Configuration
```bash
# Production .env template
# Database
DATABASE_URL=postgresql://user:password@host:5432/chatterfix_prod
REDIS_URL=redis://redis-host:6379

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=claude_api_key
GOOGLE_API_KEY=google_api_key

# Security
JWT_SECRET_KEY=your-secret-key
ADMIN_PASSWORD=secure-admin-password

# External Services
OLLAMA_URL=http://ollama-service:11434
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Feature Flags
ENABLE_AI_FEATURES=true
ENABLE_PREDICTIVE_ANALYTICS=true
ENABLE_DOCUMENT_INTELLIGENCE=false
```

---

## 🛠️ TROUBLESHOOTING

### Common Issues and Solutions

#### 1. Database Connection Issues
```python
# Check database connectivity
import psycopg2
import os

def test_db_connection():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connected: {version[0]}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

# Troubleshooting steps:
# 1. Verify DATABASE_URL environment variable
# 2. Check network connectivity
# 3. Validate credentials
# 4. Ensure database exists
```

#### 2. AI Service Connection Issues
```python
# AI service health check
async def check_ai_services():
    services = [
        ("Fix It Fred AI", "http://localhost:8005/health"),
        ("Ollama", "http://localhost:11434/api/tags"),
        ("AI Team", "http://localhost:8008/health")
    ]
    
    for name, url in services:
        try:
            response = await httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                print(f"✅ {name}: Healthy")
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {e}")
```

#### 3. Performance Optimization
```python
# Database query optimization
def optimize_work_orders_query():
    # Use proper indexing
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);",
        "CREATE INDEX IF NOT EXISTS idx_work_orders_priority ON work_orders(priority);",
        "CREATE INDEX IF NOT EXISTS idx_work_orders_assigned ON work_orders(assigned_to);",
        "CREATE INDEX IF NOT EXISTS idx_work_orders_due_date ON work_orders(due_date);"
    ]
    
    # Use query optimization
    optimized_query = """
    SELECT wo.*, a.name as asset_name, a.location
    FROM work_orders wo
    LEFT JOIN assets a ON wo.asset_id = a.id
    WHERE wo.status = %s 
    AND wo.due_date >= CURRENT_DATE
    ORDER BY wo.priority DESC, wo.due_date ASC
    LIMIT %s OFFSET %s;
    """
    
# Frontend performance
function optimizeRendering() {
    // Use virtual scrolling for large lists
    // Implement lazy loading for images
    // Debounce search inputs
    // Cache API responses
}
```

#### 4. Logging and Monitoring
```python
# Structured logging setup
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "chatterfix-cmms",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        return json.dumps(log_entry)

# Setup logging
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

---

## 📚 BEST PRACTICES

### Code Quality
- Use type hints in Python
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Implement proper error handling
- Use async/await for I/O operations

### Security
- Validate all input data
- Use parameterized queries
- Implement proper authentication
- Log security events
- Regular dependency updates

### Performance
- Implement caching strategies
- Use database indexing
- Optimize API responses
- Monitor resource usage
- Implement rate limiting

### Maintenance
- Regular backups
- Monitor application health
- Update dependencies
- Performance profiling
- Security audits

---

## 📖 QUICK REFERENCE

### Essential Commands
```bash
# Start development environment
./start-dev.sh

# Run tests
python -m pytest tests/

# Database migration
python migrate.py

# Deploy to production
./deploy-production.sh

# Check service health
curl http://localhost:8000/health
```

### Key URLs
- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs
- AI Chat: http://localhost:8005/docs
- Database Admin: http://localhost:8001/admin

---

**Last Updated:** October 14, 2025
**Version:** 3.0
**Maintainer:** AI Development Team

> This AI Look reference guide is a living document. Update it as the platform evolves to ensure accuracy for all AI model references.