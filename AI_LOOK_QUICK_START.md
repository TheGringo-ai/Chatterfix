# AI LOOK - QUICK START GUIDE 🚀
## Instant Reference for ChatterFix & Fix It Fred AI Development

> **30-Second Platform Overview**
> 
> This is your instant reference for developing with the ChatterFix CMMS and Fix It Fred AI platform. Use this for rapid onboarding and quick lookups.

---

## ⚡ INSTANT SETUP

### 1. Clone & Start (2 minutes)
```bash
# Get the code
git clone <repo-url> && cd ai-tools

# Quick start all services
./start-all-services.sh
```

### 2. Access Points
- **ChatterFix Dashboard**: http://localhost:8000
- **Fix It Fred AI**: http://localhost:8005
- **API Documentation**: http://localhost:8000/docs

### 3. Test Integration
```bash
# Test Fix It Fred
curl http://localhost:8005/health

# Test ChatterFix
curl http://localhost:8000/health
```

---

## 🎯 CORE CONCEPTS (60 seconds)

### Platform Components
```
ChatterFix CMMS (8000) ←→ Fix It Fred AI (8005)
        ↓                          ↓
   Microservices              AI Providers
   (8001-8008)               (Ollama, OpenAI, etc.)
```

### Key Services
- **8000**: Main UI Gateway
- **8001**: Database Operations  
- **8002**: Work Orders
- **8003**: Assets Management
- **8004**: Parts Inventory
- **8005**: Fix It Fred AI
- **8008**: AI Development Team

### Database Tables
- `work_orders` - All maintenance tasks
- `assets` - Equipment/machinery
- `parts` - Inventory items
- `ai_chat_sessions` - AI conversations
- `users` - System users

---

## 🔧 COMMON DEVELOPMENT PATTERNS

### 1. Add New Microservice
```python
# Template: new_service.py
from fastapi import FastAPI
app = FastAPI(title="New Service")

@app.get("/health")
async def health(): return {"status": "healthy"}

@app.post("/api/endpoint")  
async def endpoint(data: dict): return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8009)
```

### 2. Database Query Pattern
```python
# Standard query pattern
async def get_work_orders(status: str = None):
    query = "SELECT * FROM work_orders"
    params = {}
    if status:
        query += " WHERE status = :status"
        params["status"] = status
    return await database.fetch_all(query, params)
```

### 3. AI Integration Pattern
```javascript
// Frontend AI chat
async function askFred(message) {
    const response = await fetch('http://localhost:8005/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message, provider: 'ollama'})
    });
    return await response.json();
}
```

---

## 🎨 UI COMPONENT PATTERNS

### Standard Card
```html
<div class="card">
    <div class="card-header">
        <h5>{title}</h5>
        <span class="badge badge-{status}">{status}</span>
    </div>
    <div class="card-body">{content}</div>
    <div class="card-footer">{actions}</div>
</div>
```

### CSS Classes
```css
/* Status indicators */
.badge-open { background: #17a2b8; }
.badge-completed { background: #28a745; }
.badge-high { background: #fd7e14; }
.badge-critical { background: #dc3545; }

/* Common utilities */
.text-primary { color: #006fee; }
.btn-primary { background: linear-gradient(135deg, #006fee, #4285f4); }
```

---

## 📊 DATABASE QUICK REFERENCE

### Essential Queries
```sql
-- Dashboard metrics
SELECT status, COUNT(*) FROM work_orders GROUP BY status;

-- Overdue work orders  
SELECT * FROM work_orders WHERE due_date < NOW() AND status != 'completed';

-- Low stock parts
SELECT * FROM parts WHERE current_stock <= min_stock_level;

-- Asset maintenance due
SELECT * FROM assets WHERE next_maintenance_date <= NOW() + INTERVAL '7 days';
```

### Common Joins
```sql
-- Work orders with asset info
SELECT wo.*, a.name as asset_name, a.location 
FROM work_orders wo 
LEFT JOIN assets a ON wo.asset_id = a.id;

-- Parts usage in work orders
SELECT p.name, SUM(wop.quantity_used) as total_used
FROM parts p
JOIN work_order_parts wop ON p.id = wop.part_id
GROUP BY p.id, p.name;
```

---

## 🤖 AI INTEGRATION CHEAT SHEET

### Fix It Fred Endpoints
```bash
# Health check
GET /health

# Chat with AI
POST /api/chat
{
  "message": "How do I fix a pump?",
  "context": "maintenance", 
  "provider": "ollama"
}

# Configure AI provider
POST /api/providers/openai/configure
{"api_key": "sk-...", "enabled": true}
```

### AI Providers
- **Ollama**: Local AI (default) - `ollama`
- **OpenAI**: GPT models - `openai`  
- **Anthropic**: Claude models - `anthropic`
- **Google**: Gemini models - `google`
- **xAI**: Grok models - `xai`

### Context Types
- `maintenance` - General maintenance
- `safety` - Safety protocols
- `troubleshooting` - Problem diagnosis
- `parts` - Inventory questions
- `planning` - Maintenance planning

---

## 🔑 AUTHENTICATION PATTERNS

### JWT Token Usage
```python
# Create token
token = create_access_token({"sub": user_id, "role": role})

# Verify token
@jwt_required
async def protected_endpoint(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}
```

### Role Permissions
```python
ROLES = {
    'admin': ['*'],
    'manager': ['work_orders:*', 'assets:*', 'parts:*'],
    'technician': ['work_orders:read', 'work_orders:update'],
    'viewer': ['work_orders:read', 'assets:read']
}
```

---

## 🚀 DEPLOYMENT SHORTCUTS

### Local Development
```bash
# Start database
docker-compose up -d postgres redis

# Start all services
./start-dev.sh

# Run tests
pytest tests/ -v
```

### Production Deploy
```bash
# Build and deploy
./deploy-production.sh

# Health check all services
./health-check-all.sh

# View logs
./logs.sh [service-name]
```

---

## 🔍 DEBUGGING QUICK COMMANDS

### Service Status
```bash
# Check all ports
lsof -i :8000-8008

# Service health
for port in {8000..8008}; do
  curl -s http://localhost:$port/health || echo "Port $port down"
done
```

### Database Debug
```bash
# Connect to DB
psql $DATABASE_URL

# Check tables
\dt

# Query work orders
SELECT id, title, status, due_date FROM work_orders LIMIT 5;
```

### AI Service Debug
```bash
# Test Fix It Fred
curl -X POST http://localhost:8005/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "provider": "ollama"}'

# Check AI providers
curl http://localhost:8005/api/providers
```

---

## 📱 FRONTEND INTEGRATION

### Add Chat Widget
```html
<!-- Include Fix It Fred integration -->
<script src="fix_it_fred_chatterfix_integration.js"></script>

<!-- Chat widget will auto-initialize -->
<div id="ai-chat-widget"></div>
```

### Custom Components
```javascript
// Create new dashboard widget
class CustomWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.apiBase = '/api';
        this.init();
    }
    
    async init() {
        const data = await this.loadData();
        this.render(data);
    }
    
    async loadData() {
        const response = await fetch(`${this.apiBase}/endpoint`);
        return await response.json();
    }
    
    render(data) {
        this.container.innerHTML = `
            <div class="widget">
                <h4>Custom Widget</h4>
                <div class="widget-content">
                    ${data.map(item => `<div>${item.name}</div>`).join('')}
                </div>
            </div>
        `;
    }
}
```

---

## ⚠️ COMMON ISSUES & FIXES

### Port Conflicts
```bash
# Kill service on port
lsof -ti:8000 | xargs kill -9

# Change port
PORT=8010 python service.py
```

### Database Connection
```bash
# Test connection
pg_isready -h localhost -p 5432

# Reset connection
export DATABASE_URL="postgresql://user:pass@localhost/db"
```

### AI Service Down
```bash
# Restart Ollama
ollama serve

# Check AI service
python3 fix_it_fred_ai_service.py
```

---

## 📚 REFERENCE LINKS

### Documentation
- **Main Guide**: [AI_LOOK.md](AI_LOOK.md)
- **Technical Details**: [AI_LOOK_TECHNICAL_ADDENDUM.md](AI_LOOK_TECHNICAL_ADDENDUM.md)
- **API Docs**: http://localhost:8000/docs

### Key Files
- **Platform Gateway**: `core/cmms/platform_gateway.py`
- **AI Service**: `fix_it_fred_ai_service.py`
- **Database Schema**: `cmms_schema.sql`
- **Integration Script**: `fix_it_fred_chatterfix_integration.js`

---

## 🎯 DEVELOPMENT WORKFLOW

### 1. New Feature Process
1. **Plan**: Update AI_LOOK.md with new feature docs
2. **Backend**: Add service endpoint + tests
3. **Frontend**: Create UI component + integration  
4. **AI**: Update Fix It Fred prompts if needed
5. **Test**: Run full test suite
6. **Deploy**: Use CI/CD pipeline

### 2. Bug Fix Process
1. **Reproduce**: Create test case
2. **Debug**: Use logging + health checks
3. **Fix**: Minimal change approach
4. **Test**: Verify fix + regression tests
5. **Deploy**: Hotfix deployment if critical

### 3. Performance Optimization
1. **Profile**: Use database EXPLAIN, API timing
2. **Cache**: Add Redis caching for slow queries
3. **Index**: Add database indexes for common queries
4. **Scale**: Horizontal scaling with load balancer

---

**⚡ EMERGENCY CONTACTS**
- **System Down**: Check health endpoints first
- **Data Issues**: Check audit_log table
- **AI Problems**: Verify Ollama + API keys
- **Performance**: Check database connections + Redis

---

**Last Updated**: October 14, 2025  
**Version**: 3.0 Quick Start  
**Purpose**: Instant developer reference