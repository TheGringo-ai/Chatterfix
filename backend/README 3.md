# ChatterFix Backend

FastAPI microservices backend for ChatterFix CMMS platform.

## Structure
- `app/main.py` - Application entry point
- `app/api/` - FastAPI endpoints (work orders, assets, parts, etc.)
- `app/services/` - Business logic services
- `app/database/` - Database operations and schemas
- `app/utils/` - Shared utilities

## Getting Started
```bash
pip install -r requirements.txt
python app/main.py
```

## Health Check
http://localhost:8000/health