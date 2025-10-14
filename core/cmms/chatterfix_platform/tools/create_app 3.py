#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - App Generator
Interactive wizard for creating new apps with templates
"""

import os
import json
import yaml
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

class AppTemplate:
    """Base class for app templates"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.files = {}
        self.variables = {}
    
    def add_file(self, path: str, content: str):
        """Add a file template"""
        self.files[path] = content
    
    def add_variable(self, name: str, description: str, default: Any = None, required: bool = True):
        """Add a template variable"""
        self.variables[name] = {
            "description": description,
            "default": default,
            "required": required
        }
    
    def render_file(self, content: str, variables: Dict[str, Any]) -> str:
        """Render file content with variables"""
        for var_name, var_value in variables.items():
            content = content.replace(f"{{{{ {var_name} }}}}", str(var_value))
        return content
    
    def generate_app(self, app_name: str, output_dir: Path, variables: Dict[str, Any]):
        """Generate app from template"""
        app_dir = output_dir / app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Add app_name to variables
        variables["app_name"] = app_name
        variables["app_name_lower"] = app_name.lower()
        variables["app_name_upper"] = app_name.upper()
        variables["created_at"] = datetime.now().isoformat()
        variables["uuid"] = str(uuid.uuid4())
        
        # Generate files
        for file_path, file_content in self.files.items():
            # Render file path
            rendered_path = self.render_file(file_path, variables)
            full_path = app_dir / rendered_path
            
            # Create directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Render and write content
            rendered_content = self.render_file(file_content, variables)
            with open(full_path, 'w') as f:
                f.write(rendered_content)
        
        print(f"✅ Generated {self.name} app: {app_name} in {app_dir}")

class AIServiceTemplate(AppTemplate):
    """Template for AI services"""
    
    def __init__(self):
        super().__init__("AI Service", "AI-powered microservice with ChatterFix integration")
        
        self.add_variable("service_description", "Description of the AI service", "AI-powered service")
        self.add_variable("ai_provider", "AI provider to use", "openai", required=False)
        self.add_variable("port", "Service port", 8100, required=False)
        
        # Plugin manifest
        self.add_file("plugin.json", '''{
  "name": "{{ app_name_lower }}",
  "version": "1.0.0",
  "description": "{{ service_description }}",
  "author": "ChatterFix AI Platform",
  "app_type": "ai_service",
  "dependencies": [],
  "routes": ["/api/{{ app_name_lower }}/.*"],
  "permissions": ["ai.use"],
  "enabled": true,
  "auto_start": true,
  "port": {{ port }},
  "health_endpoint": "/health",
  "config_schema": {
    "ai_provider": {
      "type": "string",
      "default": "{{ ai_provider }}",
      "description": "AI provider to use"
    }
  },
  "created_at": "{{ created_at }}"
}''')
        
        # Main service file
        self.add_file("main.py", '''#!/usr/bin/env python3
"""
{{ app_name }} - AI Service
{{ service_description }}
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import os
import sys

# Import ChatterFix platform services
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from platform.core import shared_services, event_system, SystemEvents

logger = logging.getLogger(__name__)

# Pydantic models
class AIRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class AIResponse(BaseModel):
    response: str
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

# Create FastAPI app
app = FastAPI(
    title="{{ app_name }} AI Service",
    description="{{ service_description }}",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    """Service startup"""
    logger.info("Starting {{ app_name }} AI Service")
    
    # Emit startup event
    await event_system.emit(
        SystemEvents.PLUGIN_STARTED,
        {"plugin_name": "{{ app_name_lower }}"},
        source="{{ app_name_lower }}"
    )

@app.on_event("shutdown")
async def shutdown():
    """Service shutdown"""
    logger.info("Shutting down {{ app_name }} AI Service")
    
    # Emit shutdown event
    await event_system.emit(
        SystemEvents.PLUGIN_STOPPED,
        {"plugin_name": "{{ app_name_lower }}"},
        source="{{ app_name_lower }}"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "{{ app_name }}",
        "version": "1.0.0"
    }

@app.post("/api/{{ app_name_lower }}/process", response_model=AIResponse)
async def process_ai_request(request: AIRequest):
    """Process AI request"""
    try:
        # Use shared AI service
        result = await shared_services.ai.generate_text(
            prompt=request.prompt,
            provider="{{ ai_provider }}"
        )
        
        if result is None:
            raise HTTPException(status_code=500, detail="AI processing failed")
        
        # Emit analysis completed event
        await event_system.emit(
            SystemEvents.AI_ANALYSIS_COMPLETED,
            {
                "service": "{{ app_name_lower }}",
                "prompt_length": len(request.prompt),
                "response_length": len(result)
            },
            source="{{ app_name_lower }}"
        )
        
        return AIResponse(
            response=result,
            confidence=0.85,  # Example confidence score
            metadata={
                "provider": "{{ ai_provider }}",
                "processing_time": 1.2  # Example processing time
            }
        )
        
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/{{ app_name_lower }}/status")
async def get_service_status():
    """Get service status and metrics"""
    return {
        "service": "{{ app_name }}",
        "status": "running",
        "ai_provider": "{{ ai_provider }}",
        "requests_processed": 0,  # Track this in production
        "uptime": "N/A"  # Calculate actual uptime
    }

# Plugin lifecycle functions
async def start():
    """Start the plugin"""
    logger.info("{{ app_name }} plugin started")

async def stop():
    """Stop the plugin"""
    logger.info("{{ app_name }} plugin stopped")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", {{ port }}))
    uvicorn.run(app, host="0.0.0.0", port=port)
''')
        
        # Requirements file
        self.add_file("requirements.txt", '''fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
pydantic>=2.4.0
''')
        
        # Dockerfile
        self.add_file("Dockerfile", '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {{ port }}

CMD ["python", "main.py"]
''')
        
        # README
        self.add_file("README.md", '''# {{ app_name }} - AI Service

{{ service_description }}

## Features

- AI-powered processing using {{ ai_provider }}
- Integration with ChatterFix platform
- Event-driven architecture
- Health monitoring
- Docker containerization

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

The service will be available at http://localhost:{{ port }}

## API Endpoints

- `POST /api/{{ app_name_lower }}/process` - Process AI request
- `GET /api/{{ app_name_lower }}/status` - Get service status
- `GET /health` - Health check

## Configuration

Configure the AI provider and other settings in the plugin.json file.

## Development

This service is generated by the ChatterFix AI Development Platform.
''')

class WebAppTemplate(AppTemplate):
    """Template for web applications"""
    
    def __init__(self):
        super().__init__("Web App", "Full-stack web application with ChatterFix integration")
        
        self.add_variable("app_description", "Description of the web app", "Web application")
        self.add_variable("port", "Application port", 8200, required=False)
        self.add_variable("include_auth", "Include authentication", True, required=False)
        
        # Plugin manifest
        self.add_file("plugin.json", '''{
  "name": "{{ app_name_lower }}",
  "version": "1.0.0",
  "description": "{{ app_description }}",
  "author": "ChatterFix AI Platform",
  "app_type": "web_app",
  "dependencies": [],
  "routes": ["/{{ app_name_lower }}/.*", "/api/{{ app_name_lower }}/.*"],
  "permissions": ["web.access"],
  "enabled": true,
  "auto_start": true,
  "port": {{ port }},
  "health_endpoint": "/health",
  "config_schema": {
    "include_auth": {
      "type": "boolean",
      "default": {{ include_auth | lower }},
      "description": "Include authentication middleware"
    }
  },
  "created_at": "{{ created_at }}"
}''')
        
        # Main application
        self.add_file("main.py", '''#!/usr/bin/env python3
"""
{{ app_name }} - Web Application
{{ app_description }}
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import os
import sys

# Import ChatterFix platform services
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from platform.core import shared_services, event_system, SystemEvents

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="{{ app_name }} Web App",
    description="{{ app_description }}",
    version="1.0.0"
)

# Setup static files and templates
app.mount("/{{ app_name_lower }}/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic models
class AppData(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("Starting {{ app_name }} Web App")
    
    # Emit startup event
    await event_system.emit(
        SystemEvents.PLUGIN_STARTED,
        {"plugin_name": "{{ app_name_lower }}"},
        source="{{ app_name_lower }}"
    )

@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    logger.info("Shutting down {{ app_name }} Web App")
    
    # Emit shutdown event
    await event_system.emit(
        SystemEvents.PLUGIN_STOPPED,
        {"plugin_name": "{{ app_name_lower }}"},
        source="{{ app_name_lower }}"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": "{{ app_name }}",
        "version": "1.0.0"
    }

@app.get("/{{ app_name_lower }}", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": "{{ app_name }}",
        "description": "{{ app_description }}"
    })

@app.get("/api/{{ app_name_lower }}/data")
async def get_app_data():
    """Get application data"""
    # Example: fetch from database using shared services
    try:
        # Use shared database service
        result = await shared_services.database.execute_query(
            "SELECT 'Example data' as title, 'This is example content' as content",
            fetch="one"
        )
        
        if result.get("success"):
            data = result.get("data", {})
            return AppData(
                title=data.get("title", "No title"),
                content=data.get("content", "No content"),
                metadata={"source": "{{ app_name_lower }}"}
            )
        else:
            raise HTTPException(status_code=500, detail="Database query failed")
            
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/{{ app_name_lower }}/data")
async def create_app_data(data: AppData):
    """Create new application data"""
    try:
        # Example: save to database using shared services
        result = await shared_services.database.execute_query(
            "INSERT INTO {{ app_name_lower }}_data (title, content) VALUES (?, ?)",
            [data.title, data.content],
            fetch="none"
        )
        
        if result.get("success"):
            return {"message": "Data created successfully", "id": result.get("data")}
        else:
            raise HTTPException(status_code=500, detail="Failed to create data")
            
    except Exception as e:
        logger.error(f"Error creating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Plugin lifecycle functions
async def start():
    """Start the plugin"""
    logger.info("{{ app_name }} plugin started")

async def stop():
    """Stop the plugin"""
    logger.info("{{ app_name }} plugin stopped")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", {{ port }}))
    uvicorn.run(app, host="0.0.0.0", port=port)
''')
        
        # HTML template
        self.add_file("templates/index.html", '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 100px 0;
        }
        .feature-card {
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="#">{{ app_name }}</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/platform/status">Platform Status</a>
                <a class="nav-link" href="/docs">API Docs</a>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section text-center">
        <div class="container">
            <h1 class="display-4 fw-bold">{{ app_name }}</h1>
            <p class="lead">{{ description }}</p>
            <button class="btn btn-light btn-lg" onclick="loadData()">Get Started</button>
        </div>
    </section>

    <!-- Content Section -->
    <section class="py-5">
        <div class="container">
            <div class="row">
                <div class="col-md-8">
                    <div class="card feature-card">
                        <div class="card-body">
                            <h5 class="card-title">Application Data</h5>
                            <div id="app-content">
                                <p>Click "Load Data" to fetch content from the API.</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card feature-card">
                        <div class="card-body">
                            <h5 class="card-title">Features</h5>
                            <ul class="list-unstyled">
                                <li>✅ ChatterFix Integration</li>
                                <li>✅ Shared Services</li>
                                <li>✅ Event System</li>
                                <li>✅ Responsive Design</li>
                                <li>✅ RESTful API</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-dark text-white text-center py-4">
        <div class="container">
            <p>&copy; 2024 {{ app_name }} - Powered by ChatterFix AI Platform</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        async function loadData() {
            try {
                const response = await fetch('/api/{{ app_name_lower }}/data');
                const data = await response.json();
                
                document.getElementById('app-content').innerHTML = `
                    <h6>${data.title}</h6>
                    <p>${data.content}</p>
                    <small class="text-muted">Source: ${data.metadata?.source || 'Unknown'}</small>
                `;
            } catch (error) {
                document.getElementById('app-content').innerHTML = `
                    <div class="alert alert-danger">Error loading data: ${error.message}</div>
                `;
            }
        }
    </script>
</body>
</html>
''')
        
        # Static CSS (create directory)
        self.add_file("static/style.css", '''/* Custom styles for {{ app_name }} */

.custom-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.card-hover {
    transition: transform 0.3s ease;
}

.card-hover:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}
''')
        
        # Requirements and other files (same as AI service)
        self.add_file("requirements.txt", '''fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
pydantic>=2.4.0
jinja2>=3.1.0
python-multipart>=0.0.6
''')
        
        self.add_file("Dockerfile", '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {{ port }}

CMD ["python", "main.py"]
''')

class APITemplate(AppTemplate):
    """Template for REST APIs"""
    
    def __init__(self):
        super().__init__("REST API", "RESTful API service with ChatterFix integration")
        
        self.add_variable("api_description", "Description of the API", "RESTful API service")
        self.add_variable("resource_name", "Main resource name", "items")
        self.add_variable("port", "API port", 8300, required=False)
        
        # Similar structure but focused on API endpoints
        # Implementation would follow similar pattern to above templates

class AppGenerator:
    """Main app generator class"""
    
    def __init__(self):
        self.templates = {
            "ai_service": AIServiceTemplate(),
            "web_app": WebAppTemplate(),
            "api": APITemplate(),
            "microservice": AIServiceTemplate()  # Alias for ai_service
        }
        self.plugins_dir = Path("platform/plugins")
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
    
    def list_templates(self):
        """List available templates"""
        print("Available App Templates:")
        print("=" * 50)
        for name, template in self.templates.items():
            print(f"📱 {name:15} - {template.description}")
        print()
    
    def get_template_info(self, template_name: str):
        """Get detailed template information"""
        if template_name not in self.templates:
            print(f"❌ Template '{template_name}' not found")
            return
        
        template = self.templates[template_name]
        print(f"Template: {template.name}")
        print(f"Description: {template.description}")
        print("\nRequired Variables:")
        
        for var_name, var_info in template.variables.items():
            required = "Required" if var_info["required"] else "Optional"
            default = f" (default: {var_info['default']})" if var_info["default"] is not None else ""
            print(f"  • {var_name} - {var_info['description']} [{required}]{default}")
    
    def interactive_create(self):
        """Interactive app creation wizard"""
        print("🚀 ChatterFix AI Development Platform - App Generator")
        print("=" * 60)
        
        # List templates
        self.list_templates()
        
        # Get template choice
        template_name = input("Choose a template: ").strip().lower()
        if template_name not in self.templates:
            print(f"❌ Invalid template: {template_name}")
            return False
        
        template = self.templates[template_name]
        print(f"\n📋 Creating {template.name}")
        print(f"Description: {template.description}")
        print()
        
        # Get app name
        app_name = input("App name: ").strip()
        if not app_name:
            print("❌ App name is required")
            return False
        
        # Check if app already exists
        app_dir = self.plugins_dir / app_name
        if app_dir.exists():
            overwrite = input(f"⚠️  App '{app_name}' already exists. Overwrite? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("❌ App creation cancelled")
                return False
            shutil.rmtree(app_dir)
        
        # Collect template variables
        variables = {}
        for var_name, var_info in template.variables.items():
            prompt = f"{var_info['description']}"
            if var_info["default"] is not None:
                prompt += f" [{var_info['default']}]"
            prompt += ": "
            
            value = input(prompt).strip()
            
            if not value and var_info["default"] is not None:
                value = var_info["default"]
            elif not value and var_info["required"]:
                print(f"❌ {var_name} is required")
                return False
            
            # Type conversion
            if isinstance(var_info["default"], bool):
                value = value.lower() in ['true', 'yes', 'y', '1']
            elif isinstance(var_info["default"], int):
                try:
                    value = int(value)
                except ValueError:
                    print(f"❌ {var_name} must be a number")
                    return False
            
            variables[var_name] = value
        
        # Generate the app
        print(f"\n🔨 Generating {template.name}: {app_name}")
        template.generate_app(app_name, self.plugins_dir, variables)
        
        # Show next steps
        print(f"\n🎉 App '{app_name}' created successfully!")
        print("\nNext steps:")
        print(f"1. cd platform/plugins/{app_name}")
        print("2. pip install -r requirements.txt")
        print("3. python main.py")
        print("4. Register with platform gateway")
        print(f"\n📚 Documentation: platform/plugins/{app_name}/README.md")
        
        return True
    
    def create_app(self, template_name: str, app_name: str, variables: Dict[str, Any] = None):
        """Create app programmatically"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        
        if variables is None:
            variables = {}
        
        # Fill in defaults for missing variables
        for var_name, var_info in template.variables.items():
            if var_name not in variables:
                if var_info["default"] is not None:
                    variables[var_name] = var_info["default"]
                elif var_info["required"]:
                    raise ValueError(f"Required variable '{var_name}' not provided")
        
        template.generate_app(app_name, self.plugins_dir, variables)
        return True

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="ChatterFix App Generator")
    parser.add_argument("command", choices=["create", "list", "info"], help="Command to execute")
    parser.add_argument("--template", "-t", help="Template name")
    parser.add_argument("--name", "-n", help="App name")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    generator = AppGenerator()
    
    if args.command == "list":
        generator.list_templates()
    elif args.command == "info":
        if not args.template:
            print("❌ Template name required for info command")
            return
        generator.get_template_info(args.template)
    elif args.command == "create":
        if args.interactive or not args.template or not args.name:
            generator.interactive_create()
        else:
            generator.create_app(args.template, args.name)

if __name__ == "__main__":
    main()