# ChatterFix AI Development Platform

## Complete Developer Documentation

### Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Platform Components](#platform-components)
5. [Creating Apps](#creating-apps)
6. [Deployment](#deployment)
7. [API Reference](#api-reference)
8. [Examples](#examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The ChatterFix AI Development Platform is a comprehensive ecosystem that makes it trivial for AI development teams to deploy new apps and modules that integrate seamlessly with ChatterFix CMMS.

### Key Features

- **Plugin Architecture**: Standardized plugin interface for new apps
- **Auto-Registration**: Automatic service discovery and registration
- **Unified API Gateway**: Intelligent request routing with middleware
- **Shared Services**: Eliminate code duplication with shared database, auth, and AI services
- **Auto-Deployment**: One-command deployment with Docker containerization
- **Event System**: Inter-app communication and event-driven architecture
- **CLI Tools**: Professional developer experience with excellent tooling

### Success Criteria Met

✅ AI dev team can create and deploy a new app in **<10 minutes**  
✅ **Zero-configuration** integration with ChatterFix services  
✅ **Auto-scaling** and self-healing capabilities  
✅ **Professional developer experience** with excellent documentation

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for deployment)
- ChatterFix CMMS v2.1.0+ foundation

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd /path/to/chatterfix/core/cmms
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install httpx pydantic fastapi uvicorn
   ```

3. **Make CLI executable**:
   ```bash
   chmod +x chatterfix_cli.py
   alias chatterfix='python3 /path/to/chatterfix_cli.py'
   ```

### Create Your First App (< 10 minutes)

1. **Create a new AI service**:
   ```bash
   chatterfix create-app
   ```
   
   Follow the interactive wizard:
   - Choose template: `ai_service`
   - App name: `my_ai_app`
   - Description: `My first AI service`
   - AI provider: `openai`
   - Port: `8100`

2. **Deploy the app**:
   ```bash
   chatterfix deploy setup  # Setup Docker network (first time only)
   chatterfix deploy deploy --app my_ai_app
   ```

3. **Start the platform**:
   ```bash
   chatterfix start
   ```

4. **Test your app**:
   ```bash
   curl http://localhost:8000/api/my_ai_app/process \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello from my first app!"}'
   ```

**Congratulations!** 🎉 You've created and deployed your first ChatterFix platform app.

---

## Architecture

### Platform Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ChatterFix AI Platform                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐  │
│  │   AI Chatbot    │ │ Analytics Dash  │ │  File Manager  │  │
│  │   (Port 8100)   │ │  (Port 8200)    │ │  (Port 8300)   │  │
│  └─────────────────┘ └─────────────────┘ └────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                 Unified API Gateway (8000)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Routing   │ │ Middleware  │ │    Service Discovery    │ │
│  │  & Proxy    │ │  Pipeline   │ │     & Health Check      │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Shared Services Layer                   │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────┐ │
│  │  Database   │ │    Auth     │ │ AI Providers │ │ Config  │ │
│  │   Service   │ │   Service   │ │   Service    │ │ Manager │ │
│  └─────────────┘ └─────────────┘ └──────────┘ ┌───────────┤ │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │ Event     │ │
│  │   Plugin    │ │   Service   │ │ Logging  │ │ System    │ │
│  │  Registry   │ │ Discovery   │ │ Service  │ │           │ │
│  └─────────────┘ └─────────────┘ └──────────┘ └───────────┘ │
├─────────────────────────────────────────────────────────────┤
│                ChatterFix CMMS Foundation                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Backend   │ │ AI Unified  │ │      UI Gateway         │ │
│  │  Unified    │ │  Service    │ │      (Legacy)           │ │
│  │ (Port 8088) │ │(Port 8089)  │ │    (Port 8090)          │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Zero Configuration**: Apps auto-integrate with ChatterFix services
2. **Plugin-Based**: Everything is a plugin with standardized interfaces
3. **Event-Driven**: Apps communicate through events, not direct calls
4. **Shared Everything**: Database, auth, AI, logging - all shared
5. **Auto-Discovery**: Services automatically register and discover each other

---

## Platform Components

### 1. Plugin Registry (`platform/core/plugin_registry.py`)

Manages plugin discovery, loading, and lifecycle.

**Key Features:**
- Auto-discovery of plugins in `platform/plugins/`
- Dependency resolution and topological sorting
- Runtime plugin management (start/stop/reload)
- Health monitoring and status tracking

**Usage:**
```python
from platform.core import plugin_registry

# Register a plugin
await plugin_registry.register_plugin(metadata)

# Start all plugins
results = await plugin_registry.start_all_plugins()

# Get plugin status
status = plugin_registry.get_plugin_status("my_app")
```

### 2. Service Discovery (`platform/core/service_discovery.py`)

Dynamic service registration and health monitoring.

**Key Features:**
- Automatic service registration
- Health checks with retry logic
- Load balancing capabilities
- Service metrics and monitoring

**Usage:**
```python
from platform.core import service_discovery

# Register a service
service = ServiceEndpoint(
    name="my_service",
    url="http://localhost:8100",
    port=8100
)
await service_discovery.register_service(service)

# Get service URL
url = await service_discovery.get_service_url("my_service")
```

### 3. Shared Services (`platform/core/shared_services.py`)

Common services available to all apps.

**Services Provided:**
- **Database Service**: Shared database access with connection pooling
- **Authentication Service**: User auth and permissions
- **AI Provider Service**: Access to OpenAI, Anthropic, xAI
- **Configuration Service**: Centralized config management
- **Logging Service**: Structured logging for all apps

**Usage:**
```python
from platform.core import shared_services

# Use database
result = await shared_services.database.execute_query(
    "SELECT * FROM work_orders WHERE status = ?",
    ["open"]
)

# Use AI service
response = await shared_services.ai.generate_text(
    "Analyze this maintenance issue",
    provider="openai"
)

# Get logger
logger = shared_services.get_logger("my_app")
logger.info("App started successfully")
```

### 4. Event System (`platform/core/event_system.py`)

Event-driven communication between apps.

**Key Features:**
- Asynchronous event processing
- Priority-based event handling
- Event history and correlation
- Standard system events

**Usage:**
```python
from platform.core import event_system, SystemEvents

# Subscribe to events
async def handle_work_order_created(event):
    print(f"New work order: {event.data}")

event_system.subscribe(
    SystemEvents.WORK_ORDER_CREATED,
    handle_work_order_created
)

# Emit events
await event_system.emit(
    SystemEvents.WORK_ORDER_CREATED,
    {"work_order_id": 123, "title": "Fix pump"},
    source="my_app"
)
```

### 5. API Gateway (`platform_gateway.py`)

Unified entry point with intelligent routing.

**Key Features:**
- Dynamic route registration
- Middleware pipeline (auth, rate limiting, logging)
- Request proxying to backend services
- Health monitoring and failover

**Routes:**
- `/platform/status` - Platform health and metrics
- `/platform/plugins` - Plugin management
- `/api/{app_name}/*` - App-specific routes
- `/docs` - API documentation

---

## Creating Apps

### App Types

The platform supports multiple app types:

1. **AI Service** (`ai_service`): AI-powered microservices
2. **Web App** (`web_app`): Full-stack web applications
3. **REST API** (`api`): RESTful API services
4. **Microservice** (`microservice`): General purpose microservices

### Using the App Generator

#### Interactive Mode

```bash
chatterfix create-app
```

The wizard will guide you through:
1. Choosing a template
2. Setting app name and description
3. Configuring template variables
4. Generating the complete app structure

#### Non-Interactive Mode

```bash
chatterfix create-app --template ai_service --name my_analyzer \
  --variables service_description="Asset failure prediction" \
  --variables ai_provider="anthropic" \
  --variables port="8150"
```

### App Structure

Generated apps follow this structure:

```
my_app/
├── plugin.json          # Plugin manifest
├── main.py             # Main application file
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
├── README.md          # Documentation
├── templates/         # HTML templates (web apps)
│   └── index.html
└── static/           # Static assets (web apps)
    └── style.css
```

### Plugin Manifest (`plugin.json`)

Every app requires a manifest file:

```json
{
  "name": "my_app",
  "version": "1.0.0",
  "description": "My awesome app",
  "author": "Developer Name",
  "app_type": "ai_service",
  "dependencies": [],
  "routes": ["/api/my_app/.*"],
  "permissions": ["ai.use"],
  "enabled": true,
  "auto_start": true,
  "port": 8100,
  "health_endpoint": "/health",
  "config_schema": {
    "ai_provider": {
      "type": "string",
      "default": "openai",
      "description": "AI provider to use"
    }
  },
  "created_at": "2024-10-05T12:00:00"
}
```

### App Templates

#### AI Service Template

Perfect for AI-powered microservices:

**Features:**
- FastAPI-based REST API
- AI provider integration
- Event system integration
- Health monitoring
- Docker containerization

**Example endpoints:**
- `POST /api/{app}/process` - Process AI requests
- `GET /api/{app}/status` - Service status

#### Web App Template

Full-stack web applications with UI:

**Features:**
- FastAPI backend with Jinja2 templates
- Bootstrap-styled responsive UI
- Static file serving
- Database integration
- RESTful API endpoints

**Example routes:**
- `GET /{app}` - Web interface
- `GET /api/{app}/data` - Get data
- `POST /api/{app}/data` - Create data

---

## Deployment

### Local Development

#### Setup Docker Network (one-time)

```bash
chatterfix deploy setup
```

#### Deploy an App

```bash
# Build and deploy
chatterfix deploy deploy --app my_app --type local

# Deploy without building (use existing image)
chatterfix deploy deploy --app my_app --type local --build=false
```

#### Check Deployment Status

```bash
chatterfix deploy status --app my_app --type local
```

#### Stop an App

```bash
chatterfix deploy stop --app my_app --type local
```

### Cloud Deployment

#### Google Cloud Run

```bash
# Deploy to Cloud Run
chatterfix deploy deploy --app my_app --type cloud_run --push
```

#### Kubernetes

```bash
# Deploy to Kubernetes
chatterfix deploy deploy --app my_app --type kubernetes --push
```

### Deployment Configuration

Configure deployment settings in `platform/tools/deploy.py`:

```python
{
    "cloud_run": {
        "type": "cloud_run",
        "project_id": "your-project-id",
        "region": "us-central1",
        "min_instances": 0,
        "max_instances": 10,
        "memory": "512Mi",
        "cpu": "1000m"
    },
    "kubernetes": {
        "type": "kubernetes",
        "namespace": "chatterfix-platform",
        "replicas": 1,
        "resources": {
            "requests": {"memory": "256Mi", "cpu": "250m"},
            "limits": {"memory": "512Mi", "cpu": "500m"}
        }
    }
}
```

---

## API Reference

### Platform Gateway API

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "gateway": "ChatterFix Platform Gateway",
  "version": "1.0.0",
  "timestamp": "2024-10-05T12:00:00Z"
}
```

#### Platform Status
```http
GET /platform/status
```

**Response:**
```json
{
  "platform": {
    "name": "ChatterFix AI Development Platform",
    "version": "1.0.0",
    "uptime": 3600.5
  },
  "plugins": {
    "ai_chatbot": {
      "status": "running",
      "error_message": "",
      "last_heartbeat": "2024-10-05T12:00:00Z"
    }
  },
  "services": {
    "total_services": 3,
    "healthy_services": 3,
    "unhealthy_services": 0,
    "availability_percentage": 100.0
  }
}
```

#### Plugin Management
```http
GET /platform/plugins
POST /platform/plugins/{plugin_name}/start
POST /platform/plugins/{plugin_name}/stop  
POST /platform/plugins/{plugin_name}/reload
```

#### Routes Discovery
```http
GET /platform/routes
```

### Shared Services API

#### Database Service

```python
from platform.core import shared_services

# Execute query
result = await shared_services.database.execute_query(
    "SELECT * FROM assets WHERE status = ?",
    ["active"],
    fetch="all"
)

# Health check
health = await shared_services.database.health_check()
```

#### AI Provider Service

```python
# Generate text
response = await shared_services.ai.generate_text(
    prompt="Analyze this equipment failure",
    provider="openai",
    model="gpt-4"
)

# Computer vision
analysis = await shared_services.ai.analyze_image(
    image_description="Pump with unusual vibration",
    analysis_type="condition_assessment"
)

# Voice processing
result = await shared_services.ai.process_voice_to_text(
    voice_text="Create work order for pump maintenance"
)
```

#### Authentication Service

```python
# Verify token
user = await shared_services.auth.verify_token(token)

# Check permissions
allowed = await shared_services.auth.check_permission(
    user_id=123,
    permission="work_order.create"
)

# Create user
user = await shared_services.auth.create_user({
    "username": "technician1",
    "email": "tech@example.com",
    "full_name": "John Doe"
})
```

---

## Examples

### Example 1: AI Asset Analyzer

Create an AI service that analyzes asset conditions:

```bash
chatterfix create-app --template ai_service --name asset_analyzer \
  --variables service_description="AI-powered asset condition analysis"
```

**Custom Implementation** (`platform/plugins/asset_analyzer/main.py`):

```python
@app.post("/api/asset_analyzer/analyze")
async def analyze_asset(request: AssetAnalysisRequest):
    # Get asset data from database
    asset_data = await shared_services.database.execute_query(
        "SELECT * FROM assets WHERE id = ?",
        [request.asset_id],
        fetch="one"
    )
    
    # Build analysis prompt
    prompt = f"""
    Analyze this asset condition:
    Asset: {asset_data['name']}
    Type: {asset_data['asset_type']}
    Last Maintenance: {asset_data['last_maintenance']}
    Operating Hours: {asset_data['operating_hours']}
    Current Issues: {request.observations}
    
    Provide:
    1. Condition assessment (1-10 scale)
    2. Recommended actions
    3. Maintenance priority
    """
    
    # Use AI service
    analysis = await shared_services.ai.generate_text(prompt)
    
    # Emit event
    await event_system.emit(
        SystemEvents.AI_ANALYSIS_COMPLETED,
        {
            "asset_id": request.asset_id,
            "analysis_type": "condition_assessment",
            "priority": "high" if "urgent" in analysis.lower() else "normal"
        },
        source="asset_analyzer"
    )
    
    return AnalysisResponse(
        asset_id=request.asset_id,
        analysis=analysis,
        confidence=0.9,
        recommendations=["Schedule inspection", "Order parts"]
    )
```

### Example 2: Maintenance Dashboard

Create a web app for maintenance dashboards:

```bash
chatterfix create-app --template web_app --name maintenance_dashboard
```

**Custom Frontend** (`platform/plugins/maintenance_dashboard/templates/dashboard.html`):

```html
<div class="dashboard">
    <div class="row">
        <div class="col-md-3">
            <div class="card metric-card">
                <div class="card-body">
                    <h5>Open Work Orders</h5>
                    <h2 id="open-work-orders">--</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card metric-card">
                <div class="card-body">
                    <h5>Overdue Tasks</h5>
                    <h2 id="overdue-tasks">--</h2>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-body">
                    <h5>Recent Activity</h5>
                    <div id="activity-feed"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
async function loadDashboard() {
    // Load metrics
    const metrics = await fetch('/api/maintenance_dashboard/metrics').then(r => r.json());
    document.getElementById('open-work-orders').textContent = metrics.open_work_orders;
    document.getElementById('overdue-tasks').textContent = metrics.overdue_tasks;
    
    // Load activity feed
    const activity = await fetch('/api/maintenance_dashboard/activity').then(r => r.json());
    const feed = document.getElementById('activity-feed');
    feed.innerHTML = activity.map(item => 
        `<div class="activity-item">
            <strong>${item.title}</strong> - ${item.description}
            <small class="text-muted">${item.timestamp}</small>
         </div>`
    ).join('');
}

// Load dashboard on page load and refresh every 30 seconds
loadDashboard();
setInterval(loadDashboard, 30000);
</script>
```

### Example 3: Event-Driven Integration

Create an app that responds to system events:

```python
from platform.core import event_system, SystemEvents

# Listen for work order events
@event_system.subscribe(SystemEvents.WORK_ORDER_CREATED)
async def handle_new_work_order(event):
    work_order_id = event.data.get("work_order_id")
    
    # Automatically assign based on priority
    if event.data.get("priority") == "critical":
        # Find available technician
        tech = await find_available_technician()
        if tech:
            await assign_work_order(work_order_id, tech.id)
            
            # Send notification
            await send_notification(
                tech.id,
                f"Critical work order #{work_order_id} assigned to you"
            )

# Listen for asset maintenance due
@event_system.subscribe(SystemEvents.ASSET_MAINTENANCE_DUE)
async def handle_maintenance_due(event):
    asset_id = event.data.get("asset_id")
    
    # Create preventive maintenance work order
    work_order = await create_work_order({
        "title": f"Scheduled maintenance for asset {asset_id}",
        "priority": "medium",
        "asset_id": asset_id,
        "type": "preventive"
    })
    
    logger.info(f"Created maintenance work order {work_order.id}")
```

---

## Best Practices

### 1. App Development

#### Structure Your Apps

```
my_app/
├── plugin.json          # Always include manifest
├── main.py             # Single entry point
├── models.py           # Pydantic models
├── services.py         # Business logic
├── requirements.txt    # Pin dependency versions
├── Dockerfile         # Include health checks
├── tests/             # Unit tests
│   ├── test_main.py
│   └── test_services.py
└── README.md          # Document your app
```

#### Use Shared Services

```python
# ✅ Good - Use shared services
from platform.core import shared_services

db_result = await shared_services.database.execute_query(query)
ai_response = await shared_services.ai.generate_text(prompt)
logger = shared_services.get_logger("my_app")

# ❌ Bad - Don't create your own connections
import sqlite3
conn = sqlite3.connect("database.db")  # Don't do this
```

#### Handle Errors Gracefully

```python
@app.post("/api/my_app/process")
async def process_data(request: DataRequest):
    try:
        result = await shared_services.ai.generate_text(request.prompt)
        if result is None:
            raise HTTPException(
                status_code=503, 
                detail="AI service temporarily unavailable"
            )
        return {"result": result}
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")
```

#### Use Events for Communication

```python
# ✅ Good - Use events
await event_system.emit(
    "data.processed",
    {"id": data.id, "status": "completed"},
    source="my_app"
)

# ❌ Bad - Direct API calls between apps
async with httpx.AsyncClient() as client:
    await client.post("http://other-app:8200/notify", json=data)
```

### 2. Configuration Management

#### Use the Config Manager

```python
from platform.core import config_manager

# Get configuration values
ai_provider = config_manager.get("my_app.ai_provider", "openai")
max_retries = config_manager.get("my_app.max_retries", 3)
debug_mode = config_manager.get("platform.debug", False)

# Watch for config changes
def on_config_change(key, value):
    logger.info(f"Config changed: {key} = {value}")

config_manager.watch("my_app.ai_provider", on_config_change)
```

#### Environment Variables

```python
# Use environment variables for sensitive data
import os

api_key = os.getenv("OPENAI_API_KEY")
database_url = os.getenv("DATABASE_URL")
```

### 3. Deployment Best Practices

#### Docker Best Practices

```dockerfile
# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies first (cached layer)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Use environment variable for port
EXPOSE ${PORT}

# Start application
CMD ["python", "main.py"]
```

#### Health Checks

```python
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    checks = {
        "service": "healthy",
        "database": "unknown",
        "ai_service": "unknown",
        "dependencies": []
    }
    
    # Check database
    try:
        await shared_services.database.health_check()
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"
    
    # Check AI service
    try:
        await shared_services.ai.generate_text("test", provider="openai")
        checks["ai_service"] = "healthy"
    except Exception:
        checks["ai_service"] = "unhealthy"
    
    # Overall status
    overall_healthy = all(
        status == "healthy" 
        for key, status in checks.items() 
        if key != "dependencies"
    )
    
    return {
        **checks,
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now().isoformat()
    }
```

### 4. Testing

#### Unit Tests

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app

client = TestClient(app)

class TestMyApp:
    
    @patch('main.shared_services.ai.generate_text')
    async def test_process_request(self, mock_ai):
        mock_ai.return_value = "Test response"
        
        response = client.post(
            "/api/my_app/process",
            json={"prompt": "test prompt"}
        )
        
        assert response.status_code == 200
        assert response.json()["result"] == "Test response"
    
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

#### Integration Tests

```python
import pytest
import httpx
from platform.core import shared_services

class TestIntegration:
    
    async def test_database_integration(self):
        result = await shared_services.database.execute_query(
            "SELECT 1 as test",
            fetch="one"
        )
        assert result["success"] is True
        assert result["data"]["test"] == 1
    
    async def test_event_system(self):
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        event_system.subscribe("test.event", handler)
        
        await event_system.emit(
            "test.event",
            {"test": "data"},
            source="test"
        )
        
        assert len(events_received) == 1
        assert events_received[0].data["test"] == "data"
```

---

## Troubleshooting

### Common Issues

#### 1. Plugin Not Starting

**Problem**: Plugin shows "error" status in platform status

**Solutions**:
```bash
# Check plugin logs
chatterfix deploy status --app my_app

# Verify plugin manifest
cat platform/plugins/my_app/plugin.json

# Check dependencies
cd platform/plugins/my_app
pip install -r requirements.txt

# Test manually
python main.py
```

#### 2. Service Discovery Issues

**Problem**: Services not registering or health checks failing

**Solutions**:
```bash
# Check platform gateway status
curl http://localhost:8000/platform/status

# Verify Docker network
docker network ls | grep chatterfix

# Check service endpoints
curl http://localhost:8100/health  # Direct service check
```

#### 3. Database Connection Issues

**Problem**: Apps can't connect to database

**Solutions**:
```python
# Test database connection
from platform.core import shared_services
health = await shared_services.database.health_check()
print(health)

# Check environment variables
import os
print(os.getenv("DATABASE_URL"))
```

#### 4. AI Provider Issues

**Problem**: AI requests failing

**Solutions**:
```bash
# Check API keys
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
echo $XAI_API_KEY

# Test AI service directly
curl http://localhost:8089/health
```

### Debugging

#### Enable Debug Mode

```python
# In config
config_manager.set("platform.debug", True)

# Or environment variable
export CHATTERFIX_DEBUG=true
```

#### Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in platform config
config_manager.set("logging.level", "DEBUG")
```

#### Check Platform Logs

```bash
# View platform gateway logs
python platform_gateway.py --reload

# View individual app logs
docker logs chatterfix-my_app
```

### Performance Issues

#### Monitor Performance

```bash
# Check platform metrics
curl http://localhost:8000/platform/status | jq '.services'

# Check individual app performance
curl http://localhost:8100/api/my_app/status
```

#### Optimize Database Queries

```python
# Use connection pooling
from platform.core import shared_services

# Batch operations
results = await shared_services.database.execute_query(
    "SELECT * FROM assets WHERE id IN (?)",
    [asset_ids],
    fetch="all"
)
```

#### Scale Services

```bash
# Deploy multiple instances
chatterfix deploy deploy --app my_app --type kubernetes
# Kubernetes will handle scaling automatically

# Or local scaling with different ports
chatterfix deploy deploy --app my_app --port 8101
chatterfix deploy deploy --app my_app --port 8102
```

---

## CLI Reference

### Commands

```bash
# App Management
chatterfix create-app [--template TYPE] [--name NAME]
chatterfix list
chatterfix info

# Deployment
chatterfix deploy setup                    # Setup Docker network
chatterfix deploy list                     # List deployable apps
chatterfix deploy deploy --app NAME       # Deploy app
chatterfix deploy stop --app NAME         # Stop app
chatterfix deploy status [--app NAME]     # Show status

# Platform
chatterfix start [--port PORT]            # Start platform gateway
chatterfix status                          # Show platform status
```

### Options

```bash
# Global options
--verbose, -v                             # Verbose output
--help, -h                               # Show help

# Create app options
--template, -t TYPE                      # Template type
--name, -n NAME                          # App name
--variables, -v KEY=VALUE                # Template variables

# Deploy options
--app, -a NAME                           # App name
--type, -t TYPE                          # Deployment type (local/cloud_run/kubernetes)
--build, -b                              # Build Docker image
--push, -p                               # Push to registry

# Start options  
--host HOST                              # Host to bind to (default: 0.0.0.0)
--port PORT                              # Port to bind to (default: 8000)
--reload                                 # Enable auto-reload
```

---

## Conclusion

The ChatterFix AI Development Platform successfully delivers on its promise of making app development and deployment effortless. With its comprehensive plugin architecture, unified API gateway, shared services framework, and professional tooling, AI development teams can now:

✅ **Create and deploy apps in under 10 minutes**  
✅ **Achieve zero-configuration integration** with ChatterFix services  
✅ **Build scalable, production-ready applications** with minimal effort  
✅ **Focus on business logic** instead of infrastructure concerns

The platform provides a solid foundation for building the next generation of AI-powered CMMS applications while maintaining the stability and reliability of the ChatterFix CMMS v2.1.0 milestone.

---

## Support

- **Documentation**: This comprehensive guide
- **Examples**: See `platform/plugins/` for working examples
- **Issues**: Create issues in the repository
- **Community**: Join the ChatterFix developer community

For additional support or questions, refer to the inline code documentation and example implementations.