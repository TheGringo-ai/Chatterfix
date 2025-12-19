# ChatterFix CMMS - Complete Platform Documentation

> **The Most Advanced AI-Powered Technician-First CMMS Platform**

## Executive Summary

ChatterFix is a comprehensive Computerized Maintenance Management System (CMMS) built **FOR THE TECHNICIAN on the floor**. It eliminates manual data entry through voice commands, OCR document scanning, part recognition, and natural AI conversations while providing enterprise-level features for managers, analysts, and executives.

### Core Philosophy
- **Hands-Free Operation**: Voice commands, OCR scanning, part recognition
- **Multi-Model AI Team**: Claude, ChatGPT, Gemini, and Grok working collaboratively
- **Never Repeat Mistakes**: Comprehensive memory system that learns from every interaction
- **AR/Smart Glasses Ready**: Future-ready for augmented reality maintenance workflows

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [API Endpoints & Routers](#2-api-endpoints--routers)
3. [Data Models & Database](#3-data-models--database)
4. [AI Team Capabilities](#4-ai-team-capabilities)
5. [Frontend & User Interface](#5-frontend--user-interface)
6. [Microservices Architecture](#6-microservices-architecture)
7. [Feature Catalog](#7-feature-catalog)
8. [Integration Guide](#8-integration-guide)

---

## 1. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│     Web Browser  │  Mobile App  │  Voice Interface  │  AR/Smart Glasses     │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────────────┐
│                         CORE WEB SERVICE (Port 8080)                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                          FastAPI Application                             ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  ││
│  │  │ 36       │ │ Auth &   │ │ Template │ │ Static   │ │ Service      │  ││
│  │  │ Routers  │ │ Session  │ │ Engine   │ │ Files    │ │ Clients      │  ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌────────▼────────┐    ┌─────────▼─────────┐    ┌────────▼────────┐
│  OCR SERVICE    │    │  AI TEAM SERVICE  │    │     REDIS       │
│  (Port 8081)    │    │   (Port 8082)     │    │  (Port 6379)    │
│                 │    │                   │    │                 │
│ • Tesseract     │    │ • Claude          │    │ • Sessions      │
│ • EasyOCR       │    │ • ChatGPT         │    │ • Caching       │
│ • OpenCV        │    │ • Gemini          │    │ • Real-time     │
│ • QR/Barcode    │    │ • Grok            │    │                 │
└─────────────────┘    │ • AutoGen         │    └─────────────────┘
                       │ • Memory System   │
                       └───────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                         GOOGLE FIRESTORE                                     │
│                    30+ Collections, NoSQL Document DB                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic |
| **Database** | Google Firestore (NoSQL), Redis |
| **AI/ML** | Anthropic Claude, OpenAI GPT-4O, Google Gemini, xAI Grok, AutoGen |
| **Vision** | Tesseract OCR, EasyOCR, OpenCV, Pyzbar |
| **Frontend** | Jinja2 Templates, Bootstrap 5, Alpine.js, GSAP |
| **Infrastructure** | Docker, Google Cloud Run, Nginx |
| **Auth** | Firebase Authentication, JWT Tokens |

---

## 2. API Endpoints & Routers

### Router Summary

ChatterFix includes **36 active routers** with **200+ endpoints** covering all aspects of maintenance management.

### Core Routers

#### AI & Intelligence (`/ai`, `/ai-team`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/chat` | General AI conversation |
| POST | `/ai/voice-command` | Process voice commands |
| POST | `/ai/recognize-part` | AI-powered part recognition |
| POST | `/ai/analyze-condition` | Asset condition analysis |
| POST | `/ai/emergency-workflow` | Complete emergency workflow |
| GET | `/ai/memory/stats` | AI memory statistics |
| POST | `/ai-team/execute` | Execute collaborative AI task |
| POST | `/ai-team/stream` | Stream AI responses (SSE) |

#### Work Order Management (`/work-orders`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/work-orders/` | List all work orders |
| POST | `/work-orders/` | Create work order |
| GET | `/work-orders/{id}` | Get work order details |
| PUT | `/work-orders/{id}` | Update work order |
| POST | `/work-orders/{id}/assign` | Assign technician |
| POST | `/work-orders/{id}/complete` | Complete work order |
| POST | `/work-orders/bulk-assign` | Bulk assignment |

#### Asset Management (`/assets`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/assets/` | List all assets |
| POST | `/assets/` | Create new asset |
| GET | `/assets/{id}` | Asset details |
| POST | `/assets/{id}/media` | Upload asset media |
| GET | `/assets/{id}/ai-health` | AI health analysis |
| POST | `/assets/scan-barcode` | Barcode scanning |
| GET | `/assets/{id}/generate-qr` | Generate QR code |

#### Analytics & Reporting (`/analytics`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/kpi/summary` | KPI summary |
| GET | `/analytics/kpi/mttr` | Mean Time To Repair |
| GET | `/analytics/kpi/mtbf` | Mean Time Between Failures |
| GET | `/analytics/roi-dashboard` | ROI Dashboard |
| POST | `/analytics/export` | Export reports (JSON/CSV/Excel/PDF) |
| GET | `/analytics/charts/{type}` | Chart data (Chart.js format) |

#### Quality Management (`/quality`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/quality/inspections` | List quality inspections |
| POST | `/quality/inspections` | Create inspection |
| GET | `/quality/non-conformances` | Non-conformance records |
| GET | `/quality/supplier-audits` | Supplier audit history |
| GET | `/quality/product-tests` | Product test results |

#### Safety Management (`/safety`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/safety/incidents` | Safety incident list |
| POST | `/safety/incidents` | Report incident |
| GET | `/safety/inspections` | Safety inspections |
| GET | `/safety/violations` | Regulatory violations |
| GET | `/safety/lab-results` | Environmental testing |

#### Training & LineSmart (`/training`, `/linesmart`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/training/modules` | Training modules |
| POST | `/training/assignments` | Assign training |
| GET | `/linesmart/skill-gaps` | Skill gap analysis |
| POST | `/linesmart/micro-learning/start` | Start micro-learning |
| GET | `/linesmart/ar-training/{asset_id}` | AR training content |

#### Inventory & Purchasing (`/inventory`, `/purchasing`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inventory/` | Parts inventory |
| POST | `/inventory/` | Add inventory item |
| GET | `/inventory/low-stock` | Low stock alerts |
| POST | `/purchasing/orders` | Create purchase order |
| POST | `/purchasing/approve` | Approve purchase |

#### Autonomous Features (`/autonomous`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/autonomous/request` | Request feature implementation |
| POST | `/autonomous/simple` | Simple feature request |
| GET | `/autonomous/examples` | Request examples |

#### Geolocation (`/geolocation`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/geolocation/update` | Update location |
| GET | `/geolocation/team` | Team locations |
| GET | `/geolocation/nearby-work-orders` | Nearby work orders |
| POST | `/geolocation/boundary` | Set property boundary |

#### IoT & Sensors (`/iot`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/iot/sensors` | Register sensor |
| GET | `/iot/sensors/{id}/data` | Get sensor data |
| GET | `/iot/alerts` | IoT alerts |
| POST | `/iot/thresholds` | Set alert thresholds |

### Authentication (`/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/logout` | User logout |
| GET | `/auth/me` | Get current user |
| POST | `/auth/firebase/verify` | Verify Firebase token |

---

## 3. Data Models & Database

### Firestore Collections (30+)

#### Core Collections

| Collection | Purpose | Key Fields |
|-----------|---------|------------|
| `users` | User accounts | email, role, department, employee_id |
| `work_orders` | Maintenance tasks | title, asset_id, status, priority, assigned_to |
| `assets` | Equipment inventory | name, asset_tag, type, location, criticality |
| `parts` | Parts master data | part_number, supplier_id, cost, quantity |
| `maintenance_history` | Maintenance records | asset_id, maintenance_date, technician_id |

#### Quality & Safety Collections

| Collection | Purpose | Key Fields |
|-----------|---------|------------|
| `quality_inspections` | QC records | quality_score, defects_found, status |
| `non_conformances` | NCR tracking | severity, disposition, cost_impact |
| `safety_incidents` | Incident reports | incident_type, severity, investigation_status |
| `safety_violations` | Regulatory citations | regulatory_standard, penalty_amount |

#### AI & Memory Collections

| Collection | Purpose | Key Fields |
|-----------|---------|------------|
| `ai_conversations` | AI interaction history | ai_models_involved, outcome_rating, lessons_learned |
| `mistake_patterns` | Mistake tracking | mistake_type, resolution_steps, prevention_strategy |
| `solution_knowledge_base` | Proven solutions | problem_pattern, solution_steps, success_rate |

### Pydantic Models (36+)

#### User Models
```python
UserBase: username, email, full_name, is_active
UserInDB: + password_hash, role, department, employee_id
UserResponse: Excludes password_hash
Token: access_token, token_type, user_id, role
```

#### Work Order Models
```python
WorkOrderCreate: title, description, priority, asset_id
WorkOrderUpdate: status, assigned_to, scheduled_date
WorkOrderResponse: + id, created_date, completed_date
```

#### Quality Models
```python
QualityInspection: inspection_type, quality_score (0-100), defects_found
NonConformanceRecord: severity (Minor/Major/Critical), disposition
SupplierAudit: quality_score, delivery_score, certification_status
```

#### Safety Models
```python
SafetyIncident: incident_type, severity, corrective_actions[]
SafetyInspection: violations_found[], overall_score
LabResult: parameter_tested, result_value, compliance_status
```

### Role-Based Access Control (RBAC)

| Role | Key Permissions |
|------|-----------------|
| **Technician** | ASSET_READ, WORK_ORDER_CREATE/COMPLETE, INVENTORY_VIEW |
| **Supervisor** | ASSET_WRITE, WORK_ORDER_ASSIGN/APPROVE, INVENTORY_UPDATE |
| **Auditor** | FULL_AUDIT_ACCESS, REPORTING_EXPORT |
| **Admin** | ALL PERMISSIONS |

---

## 4. AI Team Capabilities

### Multi-Model AI Architecture

ChatterFix uses **5 AI models** working collaboratively through AutoGen:

| Model | Role | Specialization |
|-------|------|----------------|
| **Claude (Anthropic)** | Lead Architect | Analysis, reasoning, planning |
| **ChatGPT (OpenAI)** | Senior Developer | Coding, debugging, architecture |
| **Gemini (Google)** | Creative Director | Innovation, UI/UX, design |
| **Grok (xAI)** | Strategic Reasoner | Analysis, strategy |
| **Grok Code Fast** | Speed Coder | Fast coding, optimization |

### Autonomous Builder

The **AutonomousChatterFixBuilder** uses AutoGen GroupChat with specialized agents:

1. **CustomerRequirementAnalyzer**: Breaks down natural language requests
2. **FeatureImplementer**: Generates production-ready code
3. **DeploymentAgent**: Tests and deploys changes
4. **CustomerInterfaceAgent**: Communicates with users

```python
# Example usage
await autonomous_builder.request_feature(
    "I need budget tracking for maintenance costs"
)
```

### AI Tools Suite

| Tool | Purpose | Output |
|------|---------|--------|
| **FullStackGenerator** | Complete feature generation | Models, services, routers, templates |
| **CodeReviewer** | Security & quality analysis | Score 0-100, issues by severity |
| **TestGenerator** | pytest suite creation | Unit, integration, e2e tests |
| **DatabaseGenerator** | Firestore schema design | Collections, indexes, rules |
| **UIComponentGenerator** | Bootstrap/Tailwind components | 21+ component types |
| **AccessibilityChecker** | WCAG compliance validation | Accessibility report |
| **GitTools** | Version control automation | Commits, branches, PRs |

### Memory System (Never Repeat Mistakes)

**Four Firestore Collections:**

1. **ai_conversations**: Every AI interaction with outcome ratings
2. **code_changes**: All modifications with before/after diffs
3. **mistake_patterns**: Categorized mistakes with prevention strategies
4. **solution_knowledge_base**: Proven solutions with success rates

**Mistake Types:**
- CODE_ERROR
- ARCHITECTURE_FLAW
- PERFORMANCE_ISSUE
- SECURITY_VULNERABILITY
- DEPLOYMENT_FAILURE
- LOGIC_ERROR
- INTEGRATION_ISSUE
- USER_EXPERIENCE_PROBLEM

---

## 5. Frontend & User Interface

### Template Inventory (67 HTML Pages)

#### Core Pages
- `base.html` - Master template with responsive layout
- `dashboard.html` - AI Command Center
- `login.html` - Authentication
- `landing.html` - Public marketing page

#### Work Management
- `work_orders.html` - Work order creation/management
- `work_order_detail.html` - Individual work order view
- `assets.html` / `asset_detail.html` - Asset management
- `inventory/*.html` - Parts inventory

#### Manager Dashboards
- `manager_dashboard.html` - Operations command center
- `manager_technicians.html` - Team management
- `manager_performance.html` - Performance analytics

#### Training & LineSmart
- `training_center.html` - Training hub
- `training_module_interactive.html` - Interactive training
- `guided_training_module.html` - AI-guided learning

#### AR/Smart Glasses (Future)
- `ar/dashboard.html` - AR command center HUD
- `ar/work_orders.html` - AR work order display

### Design System

#### Glass Morphism Theme
```css
--glass-light: rgba(255,255,255,0.1)
--glass-medium: rgba(255,255,255,0.15)
--backdrop-blur: blur(20px)
```

#### Responsive Breakpoints
| Breakpoint | Width | Layout |
|------------|-------|--------|
| Desktop | ≥1024px | 3-column grid |
| Tablet | 768-1023px | 2-column grid |
| Mobile | <768px | Single column + bottom nav |
| Small | ≤375px | Compact optimization |

#### Dark Mode
- Full CSS variable override
- localStorage persistence
- System preference detection

### Persona System

| Persona | Device | Primary Features |
|---------|--------|-----------------|
| **Jake Thompson** | Mobile | Voice commands, QR scanning, offline mode |
| **Anna Kowalski** | Tablet | Touch analytics, swipe navigation |
| **Sam Martinez** | Desktop | Complex dashboards, multi-screen |
| **Maria Rodriguez** | Hybrid | Barcode scanning, inventory alerts |

### PWA Features
- Service Worker for offline support
- Install prompt with custom UI
- Standalone app mode
- Persona-based shortcuts in manifest

---

## 6. Microservices Architecture

### Service Overview

| Service | Port | Purpose | Resources |
|---------|------|---------|-----------|
| **Core Web** | 8080 | Main application | 2GB RAM, 2 CPU |
| **OCR Service** | 8081 | Document scanning | 2GB RAM, 1 CPU |
| **AI Team Service** | 8082 | Multi-model AI | 4GB RAM, 2 CPU |
| **Redis** | 6379 | Sessions/cache | 512MB RAM |
| **Nginx** | 80/443 | Reverse proxy | Production only |

### Docker Compose Network

```yaml
chatterfix-network (172.20.0.0/24)
├── core-web (172.20.0.2:8080)
├── ocr-service (172.20.0.3:8081)
├── ai-team-service (172.20.0.4:8082)
└── redis (172.20.0.5:6379)
```

### Service Communication

**Core Web → OCR Service**
```python
client = OCRHTTPClient(base_url="http://ocr-service:8081")
result = await client.extract_text_tesseract(image_data)
```

**Core Web → AI Team Service**
```python
client = AITeamHTTPClient(base_url="http://ai-team-service:8082")
result = await client.execute_task(prompt, context)
```

### Health Check Dependencies

```yaml
core-web:
  depends_on:
    redis: service_healthy
    ocr-service: service_healthy
    ai-team-service: service_healthy
```

---

## 7. Feature Catalog

### Voice Command System

**Supported Commands:**
- "Create work order for [description]"
- "Check out [part name]"
- "Go to dashboard"
- "Show me the status of [asset]"
- "Ask AI team about [question]"

**Integration:**
- Web Speech API
- Visual feedback (animated microphone)
- Command history display
- Settings control

### OCR Document Scanning

**Capabilities:**
- Tesseract OCR (text extraction)
- EasyOCR (AI-powered recognition)
- QR/Barcode scanning (Pyzbar)
- Part number recognition
- Work order form scanning

### Part Recognition

**Features:**
- Camera-based part identification
- AI visual analysis (Gemini)
- Inventory lookup integration
- Automatic checkout suggestions

### Predictive Maintenance

**Metrics:**
- Asset health scoring (0-100%)
- Risk level prediction (low/medium/high/critical)
- Failure probability estimation
- Maintenance recommendations

### Quality Management System

**Components:**
- Quality inspections with scoring
- Non-conformance tracking
- Supplier audits and ratings
- Product testing results
- CAPA (Corrective Action) management

### Safety Management System

**Components:**
- Incident reporting and investigation
- Safety inspections with checklists
- Environmental/lab testing
- Regulatory violation tracking
- OSHA/ISO compliance

### Training & LineSmart Integration

**Features:**
- Training module library
- Interactive learning paths
- Skill gap analysis
- AR training content
- Micro-learning sessions
- Team challenges (gamification)

### IoT Sensor Integration

**Capabilities:**
- Sensor registration and configuration
- Real-time data collection
- Alert threshold management
- Predictive analytics integration

### Geolocation Features

**Capabilities:**
- Team location tracking
- Nearby work order discovery
- Property boundary management
- Privacy settings control

---

## 8. Integration Guide

### MCP Server (Claude Code)

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "ai-team": {
      "command": "python",
      "args": ["/path/to/ChatterFix/mcp_servers/ai_team_mcp.py"],
      "env": {
        "AI_TEAM_SERVICE_URL": "http://localhost:8082",
        "AI_TEAM_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Available MCP Tools:**
- `ai_team_execute` - Collaborative AI task
- `ai_team_build` - Autonomous feature building
- `ai_team_review` - AI code review
- `ai_team_generate` - Feature generation
- `ai_team_health` - Health check

### CLI Tool

```bash
# Execute collaborative task
python scripts/ai_team_cli.py execute "Analyze performance issues"

# Build a feature
python scripts/ai_team_cli.py build "Add expense tracking"

# Code review
python scripts/ai_team_cli.py review app/routers/work_orders.py

# Generate feature
python scripts/ai_team_cli.py generate inventory_alerts "Low stock alerts"
```

### Python API

```python
from app.clients import (
    execute_ai_task,
    invoke_autonomous_builder,
    ai_code_review,
    check_ai_team_health
)

# Execute task
result = await execute_ai_task(
    "Optimize database queries",
    context="Focus on N+1 problems"
)

# Build feature
result = await invoke_autonomous_builder(
    "Add calendar view for maintenance"
)
```

### Direct HTTP API

```bash
# Health check
curl http://localhost:8082/health

# Execute task
curl -X POST http://localhost:8082/api/v1/execute \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze codebase", "required_agents": ["claude", "chatgpt"]}'

# Stream responses
curl -X POST http://localhost:8082/api/v1/stream \
  -H "Authorization: Bearer your-api-key" \
  -d '{"prompt": "Generate feature"}'
```

---

## Environment Variables

```bash
# Core Application
ENVIRONMENT=production
PORT=8080
REDIS_URL=redis://localhost:6379

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
XAI_API_KEY=...

# Microservices
OCR_SERVICE_URL=http://localhost:8081
AI_TEAM_SERVICE_URL=http://localhost:8082
AI_TEAM_API_KEY=your-api-key

# Firebase
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
USE_FIRESTORE=true
```

---

## Quick Start

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check health
curl http://localhost:8080/health

# View logs
docker-compose logs -f core-web
```

### Direct Python (Development)

```bash
# Install dependencies
pip install -r requirements-full.txt

# Start application
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### AI Team Service

```bash
# Start AI Team
cd ai-team-service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8082
```

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **API Routers** | 36 |
| **API Endpoints** | 200+ |
| **Pydantic Models** | 36+ |
| **Firestore Collections** | 30+ |
| **HTML Templates** | 67 |
| **AI Models** | 5 |
| **AI Tools** | 10+ |
| **User Roles** | 4 |
| **Persona Types** | 4 |
| **Microservices** | 4 |

---

## CEO Vision Statement

> "ChatterFix was developed FOR THE TECHNICIAN - the person on the floor. It captures all the data that people hate to manually enter, through voice commands, OCR document scanning, and part recognition. This enables natural conversation with AI for work order creation, part checkout, and department insights. The future includes smart glasses and full AR experiences for training and maintenance. This is a completely hands-free, natural conversation experience - built from the ground up for the technician."

---

*Generated by the ChatterFix AI Team*
*Version: 1.0*
*Last Updated: December 2025*
