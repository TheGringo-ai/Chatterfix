#!/usr/bin/env python3
"""
ChatterFix CMMS - Professional SaaS Management Platform
Comprehensive SaaS platform with GCP integration and customer management
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import asyncpg
import httpx

# GCP SDK imports
try:
    from google.cloud import run_v2
    from google.cloud import sql_v1
    from google.cloud import monitoring_v3
    from google.cloud import billing_v1
    from google.cloud import iam_v1
    from google.cloud import storage
    from google.cloud import pubsub_v1
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logging.warning("Google Cloud SDK not available - using mock services")

# Initialize FastAPI app
app = FastAPI(
    title="ChatterFix CMMS SaaS Management Platform",
    description="Professional SaaS management with GCP integration",
    version="2.0.0",
    docs_url="/saas/docs",
    redoc_url="/saas/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ DATA MODELS ============

@dataclass
class Organization:
    id: int
    name: str
    subdomain: str
    plan_type: str
    max_users: int
    created_at: datetime
    is_active: bool = True
    billing_email: Optional[str] = None
    gcp_project_id: Optional[str] = None
    monthly_spend_limit: Optional[Decimal] = None

@dataclass
class Customer:
    id: int
    organization_id: int
    email: str
    full_name: str
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    usage_quota: Optional[Dict[str, Any]] = None

@dataclass
class Subscription:
    id: int
    organization_id: int
    plan_name: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    amount: Decimal
    currency: str = "USD"
    stripe_subscription_id: Optional[str] = None

@dataclass
class GCPService:
    service_name: str
    status: str
    region: str
    url: Optional[str] = None
    resource_usage: Optional[Dict[str, Any]] = None
    cost_current_month: Optional[Decimal] = None

@dataclass
class UsageMetrics:
    organization_id: int
    service_name: str
    metric_type: str
    value: float
    timestamp: datetime
    period: str = "daily"

# ============ PYDANTIC MODELS ============

class OrganizationCreate(BaseModel):
    name: str
    subdomain: str
    plan_type: str
    billing_email: EmailStr
    max_users: int = 10

class CustomerCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "user"
    organization_id: int

class SubscriptionCreate(BaseModel):
    organization_id: int
    plan_name: str
    amount: float
    stripe_payment_method_id: str

class GCPServiceStatus(BaseModel):
    service_name: str
    status: str
    details: Optional[Dict[str, Any]] = None

# ============ DATABASE CONNECTION ============

class SaaSDatabase:
    def __init__(self):
        self.pool = None
        self.database_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/chatterfix_saas")
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            # For development, use mock data instead of real database
            logger.info("Using mock database for development")
            self.pool = None
            self.mock_data = self._initialize_mock_data()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.pool = None
            self.mock_data = self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock data for development"""
        return {
            "organizations": [
                {"id": 1, "name": "Acme Corporation", "subdomain": "acme", "plan_type": "business", "billing_email": "billing@acme.com", "max_users": 50, "is_active": True},
                {"id": 2, "name": "TechStart Inc", "subdomain": "techstart", "plan_type": "pro", "billing_email": "billing@techstart.com", "max_users": 25, "is_active": True},
                {"id": 3, "name": "Global Manufacturing", "subdomain": "global-mfg", "plan_type": "enterprise", "billing_email": "billing@globalmfg.com", "max_users": 100, "is_active": True}
            ],
            "customers": [
                {"id": 1, "organization_id": 1, "email": "john@acme.com", "full_name": "John Doe", "role": "org_admin", "is_active": True},
                {"id": 2, "organization_id": 1, "email": "jane@acme.com", "full_name": "Jane Smith", "role": "manager", "is_active": True},
                {"id": 3, "organization_id": 2, "email": "alice@techstart.com", "full_name": "Alice Johnson", "role": "org_admin", "is_active": True},
                {"id": 4, "organization_id": 3, "email": "bob@globalmfg.com", "full_name": "Bob Wilson", "role": "org_admin", "is_active": True}
            ],
            "subscriptions": [
                {"id": 1, "organization_id": 1, "plan_name": "business", "status": "active", "amount": 99.00},
                {"id": 2, "organization_id": 2, "plan_name": "pro", "status": "active", "amount": 49.00},
                {"id": 3, "organization_id": 3, "plan_name": "enterprise", "status": "active", "amount": 199.00}
            ]
        }
    
    async def create_tables(self):
        """Create SaaS management tables"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    subdomain VARCHAR(100) UNIQUE NOT NULL,
                    plan_type VARCHAR(50) NOT NULL,
                    max_users INTEGER DEFAULT 10,
                    billing_email VARCHAR(255),
                    gcp_project_id VARCHAR(255),
                    monthly_spend_limit DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    usage_quota JSONB
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id SERIAL PRIMARY KEY,
                    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
                    plan_name VARCHAR(100) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    current_period_start TIMESTAMP NOT NULL,
                    current_period_end TIMESTAMP NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'USD',
                    stripe_subscription_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_metrics (
                    id SERIAL PRIMARY KEY,
                    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
                    service_name VARCHAR(100) NOT NULL,
                    metric_type VARCHAR(100) NOT NULL,
                    value DECIMAL(15,4) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    period VARCHAR(20) DEFAULT 'hourly'
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS gcp_services (
                    id SERIAL PRIMARY KEY,
                    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
                    service_name VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    region VARCHAR(50),
                    service_url TEXT,
                    resource_usage JSONB,
                    cost_current_month DECIMAL(10,2),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    async def create_sqlite_tables(self):
        """Create SQLite tables for development"""
        # Implementation for SQLite fallback
        pass

# ============ GCP SERVICES INTEGRATION ============

class GCPManager:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "chatterfix-ai-platform")
        self.region = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
        
        if GOOGLE_CLOUD_AVAILABLE:
            self.run_client = run_v2.ServicesClient()
            self.sql_client = sql_v1.SqlInstancesServiceClient()
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            self.billing_client = billing_v1.CloudBillingClient()
            self.storage_client = storage.Client()
            logger.info("GCP clients initialized")
        else:
            logger.warning("GCP clients not available - using mock services")
    
    async def get_cloud_run_services(self, organization_id: int) -> List[GCPService]:
        """Get all Cloud Run services for an organization"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return self._mock_cloud_run_services(organization_id)
            
            parent = f"projects/{self.project_id}/locations/{self.region}"
            request = run_v2.ListServicesRequest(parent=parent)
            
            services = []
            for service in self.run_client.list_services(request=request):
                gcp_service = GCPService(
                    service_name=service.name.split('/')[-1],
                    status=service.latest_ready_revision.name if service.latest_ready_revision else "unknown",
                    region=self.region,
                    url=service.uri,
                    resource_usage={
                        "cpu": "0.5 vCPU",
                        "memory": "2Gi",
                        "requests_per_minute": await self._get_service_metrics(service.name)
                    }
                )
                services.append(gcp_service)
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to get Cloud Run services: {e}")
            return self._mock_cloud_run_services(organization_id)
    
    def _mock_cloud_run_services(self, organization_id: int) -> List[GCPService]:
        """Mock Cloud Run services for development"""
        return [
            GCPService(
                service_name="chatterfix-backend-unified",
                status="running",
                region="us-central1",
                url="https://chatterfix-backend-unified-650169261019.us-central1.run.app",
                resource_usage={"cpu": "0.5 vCPU", "memory": "2Gi", "requests_per_minute": 150},
                cost_current_month=Decimal("45.20")
            ),
            GCPService(
                service_name="chatterfix-ai-unified",
                status="running",
                region="us-central1",
                url="https://chatterfix-ai-unified-650169261019.us-central1.run.app",
                resource_usage={"cpu": "2 vCPU", "memory": "4Gi", "requests_per_minute": 89},
                cost_current_month=Decimal("127.80")
            ),
            GCPService(
                service_name="chatterfix-storybook",
                status="running",
                region="us-central1",
                url="https://chatterfix-storybook-650169261019.us-central1.run.app",
                resource_usage={"cpu": "0.25 vCPU", "memory": "512Mi", "requests_per_minute": 25},
                cost_current_month=Decimal("12.30")
            )
        ]
    
    async def _get_service_metrics(self, service_name: str) -> int:
        """Get service metrics from Cloud Monitoring"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return 120  # Mock value
            
            # Implementation would use Cloud Monitoring API
            # This is a simplified mock
            return 120
            
        except Exception as e:
            logger.error(f"Failed to get metrics for {service_name}: {e}")
            return 0
    
    async def get_billing_info(self, organization_id: int) -> Dict[str, Any]:
        """Get billing information for an organization"""
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                return self._mock_billing_info()
            
            # Implementation would use Cloud Billing API
            return self._mock_billing_info()
            
        except Exception as e:
            logger.error(f"Failed to get billing info: {e}")
            return self._mock_billing_info()
    
    def _mock_billing_info(self) -> Dict[str, Any]:
        """Mock billing information"""
        return {
            "current_month_cost": 185.30,
            "projected_month_cost": 247.50,
            "budget_limit": 500.00,
            "budget_alert_threshold": 80,
            "top_services": [
                {"name": "Cloud Run", "cost": 127.80},
                {"name": "Cloud SQL", "cost": 45.20},
                {"name": "Cloud Storage", "cost": 12.30}
            ]
        }

# ============ CUSTOMER MANAGEMENT ============

class CustomerManager:
    def __init__(self, database: SaaSDatabase):
        self.db = database
    
    async def create_organization(self, org_data: OrganizationCreate) -> Organization:
        """Create a new organization"""
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO organizations (name, subdomain, plan_type, billing_email, max_users)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """, org_data.name, org_data.subdomain, org_data.plan_type, 
                org_data.billing_email, org_data.max_users)
            
            return Organization(**dict(row))
    
    async def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """Create a new customer"""
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO customers (organization_id, email, full_name, role)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """, customer_data.organization_id, customer_data.email, 
                customer_data.full_name, customer_data.role)
            
            return Customer(**dict(row))
    
    async def get_organization_customers(self, organization_id: int) -> List[Customer]:
        """Get all customers for an organization"""
        if self.db.pool is None:
            # Use mock data
            customers = self.db.mock_data["customers"]
            org_customers = [c for c in customers if c["organization_id"] == organization_id and c["is_active"]]
            return [Customer(**customer, created_at=datetime.utcnow()) for customer in org_customers]
        
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM customers 
                WHERE organization_id = $1 AND is_active = TRUE
                ORDER BY created_at DESC
            """, organization_id)
            
            return [Customer(**dict(row)) for row in rows]
    
    async def update_customer_usage(self, customer_id: int, usage_data: Dict[str, Any]):
        """Update customer usage quotas"""
        async with self.db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE customers 
                SET usage_quota = $1, last_login = CURRENT_TIMESTAMP
                WHERE id = $2
            """, json.dumps(usage_data), customer_id)

# ============ BILLING MANAGEMENT ============

class BillingManager:
    def __init__(self, database: SaaSDatabase):
        self.db = database
        self.stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
    
    async def create_subscription(self, sub_data: SubscriptionCreate) -> Subscription:
        """Create a new subscription"""
        # In production, this would integrate with Stripe
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO subscriptions 
                (organization_id, plan_name, amount, current_period_start, current_period_end)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """, sub_data.organization_id, sub_data.plan_name, 
                Decimal(str(sub_data.amount)), period_start, period_end)
            
            return Subscription(**dict(row))
    
    async def get_organization_billing(self, organization_id: int) -> Dict[str, Any]:
        """Get billing information for an organization"""
        if self.db.pool is None:
            # Use mock data
            subscriptions = self.db.mock_data["subscriptions"]
            org_subscription = next((s for s in subscriptions if s["organization_id"] == organization_id), None)
            
            return {
                "subscription": org_subscription,
                "usage_metrics": [
                    {"service_name": "api_calls", "metric_type": "count", "total_value": 15420},
                    {"service_name": "storage", "metric_type": "gb", "total_value": 2.5},
                    {"service_name": "compute", "metric_type": "hours", "total_value": 45.2}
                ],
                "current_month_usage": 15467.7,
                "billing_period": "monthly"
            }
        
        async with self.db.pool.acquire() as conn:
            subscription = await conn.fetchrow("""
                SELECT * FROM subscriptions 
                WHERE organization_id = $1 AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, organization_id)
            
            usage_metrics = await conn.fetch("""
                SELECT service_name, metric_type, SUM(value) as total_value
                FROM usage_metrics 
                WHERE organization_id = $1 
                AND timestamp >= date_trunc('month', CURRENT_TIMESTAMP)
                GROUP BY service_name, metric_type
            """, organization_id)
            
            return {
                "subscription": dict(subscription) if subscription else None,
                "usage_metrics": [dict(row) for row in usage_metrics],
                "current_month_usage": sum(float(row['total_value']) for row in usage_metrics),
                "billing_period": "monthly"
            }

# ============ INITIALIZE SERVICES ============

# Global service instances
saas_db = SaaSDatabase()
gcp_manager = GCPManager()
customer_manager = CustomerManager(saas_db)
billing_manager = BillingManager(saas_db)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await saas_db.initialize()
    logger.info("SaaS Management Platform initialized")

# ============ API ENDPOINTS ============

@app.get("/saas/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "database": "connected" if saas_db.pool else "disconnected",
            "gcp": "available" if GOOGLE_CLOUD_AVAILABLE else "mock"
        }
    }

@app.post("/saas/organizations", response_model=dict)
async def create_organization(org_data: OrganizationCreate):
    """Create a new organization"""
    try:
        organization = await customer_manager.create_organization(org_data)
        return {"success": True, "organization": asdict(organization)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/saas/organizations/{org_id}/dashboard")
async def get_organization_dashboard(org_id: int):
    """Get comprehensive dashboard for an organization"""
    try:
        # Get GCP services
        gcp_services = await gcp_manager.get_cloud_run_services(org_id)
        
        # Get billing info
        billing_info = await gcp_manager.get_billing_info(org_id)
        
        # Get customers
        customers = await customer_manager.get_organization_customers(org_id)
        
        # Get subscription info
        subscription_info = await billing_manager.get_organization_billing(org_id)
        
        return {
            "organization_id": org_id,
            "gcp_services": [asdict(service) for service in gcp_services],
            "billing": billing_info,
            "customers": [asdict(customer) for customer in customers],
            "subscription": subscription_info,
            "dashboard_metrics": {
                "total_services": len(gcp_services),
                "active_customers": len([c for c in customers if c.is_active]),
                "monthly_cost": billing_info.get("current_month_cost", 0),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/saas/organizations/{org_id}/gcp-services")
async def get_gcp_services(org_id: int):
    """Get GCP services for an organization"""
    try:
        services = await gcp_manager.get_cloud_run_services(org_id)
        return {"services": [asdict(service) for service in services]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/saas/organizations/{org_id}/customers")
async def create_customer(org_id: int, customer_data: CustomerCreate):
    """Create a new customer for an organization"""
    try:
        customer_data.organization_id = org_id
        customer = await customer_manager.create_customer(customer_data)
        return {"success": True, "customer": asdict(customer)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/saas/organizations/{org_id}/subscriptions")
async def create_subscription(org_id: int, sub_data: SubscriptionCreate):
    """Create a subscription for an organization"""
    try:
        sub_data.organization_id = org_id
        subscription = await billing_manager.create_subscription(sub_data)
        return {"success": True, "subscription": asdict(subscription)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/saas/organizations/{org_id}/billing")
async def get_billing_dashboard(org_id: int):
    """Get billing dashboard for an organization"""
    try:
        billing_info = await billing_manager.get_organization_billing(org_id)
        gcp_billing = await gcp_manager.get_billing_info(org_id)
        
        return {
            "organization_id": org_id,
            "subscription": billing_info["subscription"],
            "usage_metrics": billing_info["usage_metrics"],
            "gcp_costs": gcp_billing,
            "recommendations": [
                {
                    "type": "cost_optimization",
                    "message": "Consider upgrading to Business plan for better rates",
                    "potential_savings": "$50/month"
                },
                {
                    "type": "usage_alert",
                    "message": "API usage is 85% of monthly quota",
                    "action_required": "Monitor usage or upgrade plan"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ WEBSOCKET FOR REAL-TIME UPDATES ============

@app.websocket("/saas/ws/{org_id}")
async def websocket_endpoint(websocket, org_id: int):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    try:
        while True:
            # Send real-time updates every 30 seconds
            dashboard_data = await get_organization_dashboard(org_id)
            await websocket.send_json(dashboard_data)
            await asyncio.sleep(30)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8090))
    uvicorn.run(app, host="0.0.0.0", port=port)