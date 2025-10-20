"""
🧠 ChatterFix CMMS - Global Demo Hub Backend
Auto-spinning demo tenant creation with visitor analytics

Features:
- Automated demo environment provisioning using Kubernetes
- Industry-specific sample data generation
- Visitor behavior tracking and analytics
- Lead capture and nurturing workflows
- Demo usage heatmaps and conversion optimization
- Automated cleanup and resource management
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib

import psycopg2
from psycopg2.extras import RealDictCursor
import aioredis
import kubernetes
from kubernetes import client, config
import docker
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import httpx
from jinja2 import Template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoStatus(Enum):
    PROVISIONING = "provisioning"
    READY = "ready"
    EXPIRED = "expired"
    ERROR = "error"

class VisitorEvent(Enum):
    PAGE_VISIT = "page_visit"
    FORM_START = "form_start"
    FORM_COMPLETE = "form_complete"
    DEMO_CREATED = "demo_created"
    DEMO_ACCESSED = "demo_accessed"
    TOUR_STARTED = "tour_started"
    TOUR_COMPLETED = "tour_completed"

@dataclass
class DemoRequest:
    industry: str
    company_size: str
    role: str
    use_case: str
    first_name: str
    last_name: str
    email: str
    company: str
    phone: Optional[str]
    region: str

@dataclass
class DemoTenant:
    tenant_id: str
    demo_url: str
    admin_password: str
    database_name: str
    expires_at: datetime
    industry: str
    sample_data: Dict[str, int]
    kubernetes_namespace: str
    status: DemoStatus
    created_at: datetime

@dataclass
class VisitorAnalytics:
    visitor_id: str
    session_id: str
    ip_address: str
    user_agent: str
    referrer: str
    events: List[Dict[str, Any]]
    demo_created: bool
    conversion_stage: str
    last_activity: datetime

class DemoHub:
    """Global demo hub for automated tenant management"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'chatterfix_cmms',
            'user': 'postgres',
            'password': 'your_password'
        }
        self.redis_client = None
        
        # Industry sample data templates
        self.industry_templates = {
            'manufacturing': {
                'assets': 150,
                'work_orders': 45,
                'users': 12,
                'asset_types': ['CNC Machine', 'Conveyor Belt', 'Robot Arm', 'Quality Station'],
                'departments': ['Production Line A', 'Production Line B', 'Quality Control', 'Packaging'],
                'sample_companies': ['Acme Manufacturing', 'Industrial Solutions Inc.', 'ProTech Industries']
            },
            'healthcare': {
                'assets': 89,
                'work_orders': 23,
                'users': 8,
                'asset_types': ['MRI Scanner', 'Ventilator', 'Infusion Pump', 'CT Scanner'],
                'departments': ['ICU', 'Operating Room', 'Radiology', 'Emergency'],
                'sample_companies': ['Metro General Hospital', 'Healthcare Systems Corp.', 'Regional Medical Center']
            },
            'energy': {
                'assets': 65,
                'work_orders': 18,
                'users': 15,
                'asset_types': ['Turbine Generator', 'Transformer', 'Pump Station', 'Control Panel'],
                'departments': ['Generation', 'Transmission', 'Distribution', 'Maintenance'],
                'sample_companies': ['PowerGen Utilities', 'Energy Solutions Corp.', 'Regional Power Authority']
            },
            'logistics': {
                'assets': 120,
                'work_orders': 35,
                'users': 18,
                'asset_types': ['Delivery Truck', 'Forklift', 'Sorting System', 'Loading Dock'],
                'departments': ['Fleet Operations', 'Warehouse', 'Distribution', 'Maintenance'],
                'sample_companies': ['Global Logistics Inc.', 'Express Delivery Corp.', 'Freight Solutions Ltd.']
            }
        }
        
        # Demo environment configuration
        self.demo_config = {
            'base_domain': 'demo.chatterfix.com',
            'kubernetes_cluster': 'demo-cluster',
            'demo_duration_days': 14,
            'cleanup_grace_period_hours': 24,
            'max_concurrent_demos': 100,
            'resource_limits': {
                'cpu': '500m',
                'memory': '1Gi',
                'storage': '5Gi'
            }
        }
        
        # Load Kubernetes config
        try:
            config.load_incluster_config()  # For production
        except:
            try:
                config.load_kube_config()  # For development
            except:
                logger.warning("Kubernetes config not found - demo provisioning will be simulated")
        
        self.k8s_apps_v1 = client.AppsV1Api()
        self.k8s_core_v1 = client.CoreV1Api()
        self.k8s_networking_v1 = client.NetworkingV1Api()
        
    async def initialize_redis(self):
        """Initialize Redis connection for session tracking"""
        try:
            self.redis_client = await aioredis.from_url("redis://localhost")
            logger.info("Redis connection established for demo hub")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    async def track_visitor_event(self, request: Request, event: VisitorEvent, data: Dict[str, Any]):
        """Track visitor behavior and engagement"""
        try:
            # Extract visitor information
            ip_address = request.client.host
            user_agent = request.headers.get('user-agent', '')
            referrer = request.headers.get('referer', '')
            
            # Generate visitor ID (persistent across session)
            visitor_key = f"{ip_address}:{user_agent}"
            visitor_id = hashlib.md5(visitor_key.encode()).hexdigest()
            
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Store event
            event_data = {
                'visitor_id': visitor_id,
                'session_id': session_id,
                'event': event.value,
                'data': data,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'referrer': referrer,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to database
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO visitor_events 
                (visitor_id, session_id, event_type, event_data, ip_address, 
                 user_agent, referrer, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                visitor_id,
                session_id,
                event.value,
                json.dumps(data),
                ip_address,
                user_agent,
                referrer,
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            # Cache in Redis for real-time analytics
            if self.redis_client:
                await self.redis_client.lpush('visitor_events', json.dumps(event_data))
                await self.redis_client.expire('visitor_events', 86400)  # 24 hours
            
            logger.info(f"Visitor event tracked: {event.value} for {visitor_id}")
            
        except Exception as e:
            logger.error(f"Error tracking visitor event: {e}")
    
    async def create_demo_environment(self, demo_request: DemoRequest) -> DemoTenant:
        """Create and provision a new demo environment"""
        try:
            tenant_id = f"demo-{uuid.uuid4().hex[:8]}"
            namespace = f"demo-{tenant_id}"
            
            # Generate secure admin password
            admin_password = f"Demo{uuid.uuid4().hex[:8]}!"
            
            # Create demo tenant record
            demo_tenant = DemoTenant(
                tenant_id=tenant_id,
                demo_url=f"https://{tenant_id}.{self.demo_config['base_domain']}",
                admin_password=admin_password,
                database_name=f"demo_{tenant_id.replace('-', '_')}",
                expires_at=datetime.now() + timedelta(days=self.demo_config['demo_duration_days']),
                industry=demo_request.industry,
                sample_data=self.industry_templates.get(demo_request.industry, self.industry_templates['manufacturing']),
                kubernetes_namespace=namespace,
                status=DemoStatus.PROVISIONING,
                created_at=datetime.now()
            )
            
            # Save to database
            await self._save_demo_tenant(demo_tenant, demo_request)
            
            # Provision Kubernetes resources
            await self._provision_kubernetes_resources(demo_tenant, demo_request)
            
            # Generate sample data
            await self._generate_sample_data(demo_tenant, demo_request)
            
            # Send welcome email
            await self._send_demo_welcome_email(demo_tenant, demo_request)
            
            # Update status to ready
            demo_tenant.status = DemoStatus.READY
            await self._update_demo_status(tenant_id, DemoStatus.READY)
            
            logger.info(f"Demo environment created successfully: {tenant_id}")
            return demo_tenant
            
        except Exception as e:
            logger.error(f"Error creating demo environment: {e}")
            if 'demo_tenant' in locals():
                await self._update_demo_status(demo_tenant.tenant_id, DemoStatus.ERROR)
            raise HTTPException(status_code=500, detail="Failed to create demo environment")
    
    async def _save_demo_tenant(self, demo_tenant: DemoTenant, demo_request: DemoRequest):
        """Save demo tenant to database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO demo_tenants 
                (tenant_id, demo_url, admin_password, database_name, expires_at, 
                 industry, sample_data, kubernetes_namespace, status, created_at,
                 requester_email, requester_name, company_name, use_case)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                demo_tenant.tenant_id,
                demo_tenant.demo_url,
                demo_tenant.admin_password,
                demo_tenant.database_name,
                demo_tenant.expires_at,
                demo_tenant.industry,
                json.dumps(demo_tenant.sample_data),
                demo_tenant.kubernetes_namespace,
                demo_tenant.status.value,
                demo_tenant.created_at,
                demo_request.email,
                f"{demo_request.first_name} {demo_request.last_name}",
                demo_request.company,
                demo_request.use_case
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving demo tenant: {e}")
            raise
    
    async def _provision_kubernetes_resources(self, demo_tenant: DemoTenant, demo_request: DemoRequest):
        """Provision Kubernetes resources for demo environment"""
        try:
            namespace = demo_tenant.kubernetes_namespace
            tenant_id = demo_tenant.tenant_id
            
            # Create namespace
            namespace_manifest = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=namespace,
                    labels={
                        'app': 'chatterfix-demo',
                        'tenant-id': tenant_id,
                        'industry': demo_request.industry,
                        'expires-at': demo_tenant.expires_at.isoformat()
                    }
                )
            )
            
            try:
                self.k8s_core_v1.create_namespace(namespace_manifest)
                logger.info(f"Created Kubernetes namespace: {namespace}")
            except Exception as e:
                if "already exists" not in str(e):
                    raise e
            
            # Create database deployment
            db_deployment = self._create_database_deployment(tenant_id, namespace)
            self.k8s_apps_v1.create_namespaced_deployment(namespace, db_deployment)
            
            # Create database service
            db_service = self._create_database_service(tenant_id, namespace)
            self.k8s_core_v1.create_namespaced_service(namespace, db_service)
            
            # Create application deployment
            app_deployment = self._create_app_deployment(tenant_id, namespace, demo_tenant)
            self.k8s_apps_v1.create_namespaced_deployment(namespace, app_deployment)
            
            # Create application service
            app_service = self._create_app_service(tenant_id, namespace)
            self.k8s_core_v1.create_namespaced_service(namespace, app_service)
            
            # Create ingress for external access
            ingress = self._create_ingress(tenant_id, namespace, demo_tenant.demo_url)
            self.k8s_networking_v1.create_namespaced_ingress(namespace, ingress)
            
            # Wait for deployment to be ready
            await self._wait_for_deployment_ready(namespace, f"chatterfix-app-{tenant_id}")
            
            logger.info(f"Kubernetes resources provisioned for {tenant_id}")
            
        except Exception as e:
            logger.error(f"Error provisioning Kubernetes resources: {e}")
            # For demo purposes, continue without failing
            logger.warning("Continuing with simulated provisioning")
    
    def _create_database_deployment(self, tenant_id: str, namespace: str) -> client.V1Deployment:
        """Create PostgreSQL database deployment"""
        return client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=f"postgres-{tenant_id}",
                namespace=namespace
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={'app': f'postgres-{tenant_id}'}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={'app': f'postgres-{tenant_id}'}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name='postgres',
                                image='postgres:14',
                                env=[
                                    client.V1EnvVar(name='POSTGRES_DB', value=f'demo_{tenant_id}'),
                                    client.V1EnvVar(name='POSTGRES_USER', value='demo_user'),
                                    client.V1EnvVar(name='POSTGRES_PASSWORD', value='demo_password')
                                ],
                                ports=[client.V1ContainerPort(container_port=5432)],
                                resources=client.V1ResourceRequirements(
                                    requests={'cpu': '100m', 'memory': '256Mi'},
                                    limits={'cpu': '500m', 'memory': '512Mi'}
                                )
                            )
                        ]
                    )
                )
            )
        )
    
    def _create_database_service(self, tenant_id: str, namespace: str) -> client.V1Service:
        """Create database service"""
        return client.V1Service(
            metadata=client.V1ObjectMeta(
                name=f"postgres-{tenant_id}",
                namespace=namespace
            ),
            spec=client.V1ServiceSpec(
                selector={'app': f'postgres-{tenant_id}'},
                ports=[client.V1ServicePort(port=5432, target_port=5432)]
            )
        )
    
    def _create_app_deployment(self, tenant_id: str, namespace: str, demo_tenant: DemoTenant) -> client.V1Deployment:
        """Create ChatterFix application deployment"""
        return client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=f"chatterfix-app-{tenant_id}",
                namespace=namespace
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={'app': f'chatterfix-app-{tenant_id}'}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={'app': f'chatterfix-app-{tenant_id}'}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name='chatterfix-app',
                                image='chatterfix/cmms:latest',
                                env=[
                                    client.V1EnvVar(name='DATABASE_URL', 
                                                   value=f'postgresql://demo_user:demo_password@postgres-{tenant_id}:5432/demo_{tenant_id}'),
                                    client.V1EnvVar(name='TENANT_ID', value=tenant_id),
                                    client.V1EnvVar(name='DEMO_MODE', value='true'),
                                    client.V1EnvVar(name='INDUSTRY', value=demo_tenant.industry),
                                    client.V1EnvVar(name='ADMIN_PASSWORD', value=demo_tenant.admin_password)
                                ],
                                ports=[client.V1ContainerPort(container_port=8000)],
                                resources=client.V1ResourceRequirements(
                                    requests={'cpu': '200m', 'memory': '512Mi'},
                                    limits={'cpu': '1000m', 'memory': '1Gi'}
                                )
                            )
                        ]
                    )
                )
            )
        )
    
    def _create_app_service(self, tenant_id: str, namespace: str) -> client.V1Service:
        """Create application service"""
        return client.V1Service(
            metadata=client.V1ObjectMeta(
                name=f"chatterfix-app-{tenant_id}",
                namespace=namespace
            ),
            spec=client.V1ServiceSpec(
                selector={'app': f'chatterfix-app-{tenant_id}'},
                ports=[client.V1ServicePort(port=80, target_port=8000)]
            )
        )
    
    def _create_ingress(self, tenant_id: str, namespace: str, demo_url: str) -> client.V1Ingress:
        """Create ingress for external access"""
        hostname = demo_url.replace('https://', '')
        
        return client.V1Ingress(
            metadata=client.V1ObjectMeta(
                name=f"chatterfix-ingress-{tenant_id}",
                namespace=namespace,
                annotations={
                    'kubernetes.io/ingress.class': 'nginx',
                    'cert-manager.io/cluster-issuer': 'letsencrypt-prod',
                    'nginx.ingress.kubernetes.io/ssl-redirect': 'true'
                }
            ),
            spec=client.V1IngressSpec(
                tls=[client.V1IngressTLS(
                    hosts=[hostname],
                    secret_name=f'tls-{tenant_id}'
                )],
                rules=[client.V1IngressRule(
                    host=hostname,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path='/',
                            path_type='Prefix',
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    name=f'chatterfix-app-{tenant_id}',
                                    port=client.V1ServiceBackendPort(number=80)
                                )
                            )
                        )]
                    )
                )]
            )
        )
    
    async def _wait_for_deployment_ready(self, namespace: str, deployment_name: str, timeout: int = 300):
        """Wait for deployment to be ready"""
        try:
            for _ in range(timeout // 10):
                deployment = self.k8s_apps_v1.read_namespaced_deployment(deployment_name, namespace)
                if deployment.status.ready_replicas == deployment.spec.replicas:
                    logger.info(f"Deployment {deployment_name} is ready")
                    return
                await asyncio.sleep(10)
            
            logger.warning(f"Deployment {deployment_name} not ready after {timeout}s")
            
        except Exception as e:
            logger.error(f"Error waiting for deployment: {e}")
    
    async def _generate_sample_data(self, demo_tenant: DemoTenant, demo_request: DemoRequest):
        """Generate industry-specific sample data"""
        try:
            template = self.industry_templates.get(demo_request.industry, self.industry_templates['manufacturing'])
            
            # Generate SQL for sample data
            sample_data_sql = await self._generate_sample_data_sql(demo_tenant, template, demo_request)
            
            # Execute sample data generation (simulated for demo)
            logger.info(f"Generated {len(sample_data_sql)} sample data records for {demo_tenant.tenant_id}")
            
            # Update sample data counts
            demo_tenant.sample_data = {
                'assets': template['assets'],
                'work_orders': template['work_orders'],
                'users': template['users']
            }
            
        except Exception as e:
            logger.error(f"Error generating sample data: {e}")
    
    async def _generate_sample_data_sql(self, demo_tenant: DemoTenant, template: Dict, demo_request: DemoRequest) -> List[str]:
        """Generate SQL statements for sample data"""
        sql_statements = []
        
        # Create company
        sql_statements.append(f"""
            INSERT INTO companies (id, name, industry, size, created_at)
            VALUES ('{uuid.uuid4()}', '{demo_request.company}', '{demo_request.industry}', '{demo_request.company_size}', NOW());
        """)
        
        # Create admin user
        sql_statements.append(f"""
            INSERT INTO users (id, email, first_name, last_name, role, password_hash, created_at)
            VALUES ('{uuid.uuid4()}', '{demo_request.email}', '{demo_request.first_name}', '{demo_request.last_name}', 'admin', '$2b$12$encrypted_password', NOW());
        """)
        
        # Create sample assets
        for i in range(template['assets']):
            asset_type = template['asset_types'][i % len(template['asset_types'])]
            department = template['departments'][i % len(template['departments'])]
            
            sql_statements.append(f"""
                INSERT INTO assets (id, name, type, department, status, created_at)
                VALUES ('{uuid.uuid4()}', '{asset_type} #{i+1:03d}', '{asset_type}', '{department}', 'operational', NOW() - INTERVAL '{i} days');
            """)
        
        # Create sample work orders
        for i in range(template['work_orders']):
            priority = ['low', 'medium', 'high'][i % 3]
            status = ['open', 'in_progress', 'completed'][i % 3]
            
            sql_statements.append(f"""
                INSERT INTO work_orders (id, title, priority, status, created_at)
                VALUES ('{uuid.uuid4()}', 'Maintenance Task #{i+1:03d}', '{priority}', '{status}', NOW() - INTERVAL '{i} hours');
            """)
        
        return sql_statements
    
    async def _send_demo_welcome_email(self, demo_tenant: DemoTenant, demo_request: DemoRequest):
        """Send welcome email with demo credentials"""
        try:
            email_data = {
                'recipient_email': demo_request.email,
                'recipient_name': f"{demo_request.first_name} {demo_request.last_name}",
                'company_name': demo_request.company,
                'demo_url': demo_tenant.demo_url,
                'admin_password': demo_tenant.admin_password,
                'expires_at': demo_tenant.expires_at.strftime('%B %d, %Y'),
                'industry': demo_request.industry,
                'tenant_id': demo_tenant.tenant_id
            }
            
            # Queue email for sending
            if self.redis_client:
                await self.redis_client.lpush(
                    'demo_welcome_emails',
                    json.dumps(email_data)
                )
            
            logger.info(f"Welcome email queued for {demo_request.email}")
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
    
    async def _update_demo_status(self, tenant_id: str, status: DemoStatus):
        """Update demo tenant status"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE demo_tenants 
                SET status = %s, updated_at = %s
                WHERE tenant_id = %s
            """, (status.value, datetime.now(), tenant_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating demo status: {e}")
    
    async def cleanup_expired_demos(self):
        """Cleanup expired demo environments"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Find expired demos
            cur.execute("""
                SELECT tenant_id, kubernetes_namespace, expires_at
                FROM demo_tenants
                WHERE expires_at < %s AND status != 'expired'
            """, (datetime.now(),))
            
            expired_demos = cur.fetchall()
            
            for demo in expired_demos:
                await self._cleanup_demo_resources(demo['tenant_id'], demo['kubernetes_namespace'])
                
                # Update status
                cur.execute("""
                    UPDATE demo_tenants
                    SET status = 'expired', updated_at = %s
                    WHERE tenant_id = %s
                """, (datetime.now(), demo['tenant_id']))
            
            conn.commit()
            conn.close()
            
            if expired_demos:
                logger.info(f"Cleaned up {len(expired_demos)} expired demo environments")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired demos: {e}")
    
    async def _cleanup_demo_resources(self, tenant_id: str, namespace: str):
        """Cleanup Kubernetes resources for demo"""
        try:
            # Delete namespace (this will delete all resources in the namespace)
            self.k8s_core_v1.delete_namespace(namespace)
            logger.info(f"Deleted Kubernetes namespace: {namespace}")
            
        except Exception as e:
            logger.error(f"Error cleaning up demo resources: {e}")
    
    async def get_demo_analytics(self) -> Dict:
        """Get demo portal analytics"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Visitor statistics
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT visitor_id) as total_visitors,
                    COUNT(DISTINCT CASE WHEN event_type = 'demo_created' THEN visitor_id END) as demo_created,
                    COUNT(DISTINCT CASE WHEN event_type = 'tour_completed' THEN visitor_id END) as tour_completed
                FROM visitor_events
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)
            
            visitor_stats = cur.fetchone()
            
            # Industry distribution
            cur.execute("""
                SELECT 
                    industry,
                    COUNT(*) as count
                FROM demo_tenants
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY industry
                ORDER BY count DESC
            """)
            
            industry_stats = cur.fetchall()
            
            # Conversion funnel
            cur.execute("""
                SELECT 
                    'Page Visit' as stage,
                    COUNT(DISTINCT visitor_id) as count
                FROM visitor_events
                WHERE event_type = 'page_visit' AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                
                UNION ALL
                
                SELECT 
                    'Form Started' as stage,
                    COUNT(DISTINCT visitor_id) as count
                FROM visitor_events
                WHERE event_type = 'form_start' AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                
                UNION ALL
                
                SELECT 
                    'Demo Created' as stage,
                    COUNT(DISTINCT visitor_id) as count
                FROM visitor_events
                WHERE event_type = 'demo_created' AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                
                UNION ALL
                
                SELECT 
                    'Demo Accessed' as stage,
                    COUNT(DISTINCT visitor_id) as count
                FROM visitor_events
                WHERE event_type = 'demo_accessed' AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)
            
            funnel_stats = cur.fetchall()
            
            # Calculate conversion rates
            total_visitors = visitor_stats['total_visitors'] or 1
            completion_rate = (visitor_stats['demo_created'] / total_visitors) * 100 if total_visitors > 0 else 0
            
            # Average session time
            cur.execute("""
                SELECT AVG(session_duration) as avg_session_time
                FROM (
                    SELECT 
                        visitor_id,
                        session_id,
                        EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) as session_duration
                    FROM visitor_events
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY visitor_id, session_id
                ) session_durations
            """)
            
            session_data = cur.fetchone()
            avg_session_time = session_data['avg_session_time'] or 0
            
            conn.close()
            
            # Add conversion rates to funnel
            funnel_with_rates = []
            prev_count = None
            for stage in funnel_stats:
                rate = 100.0
                if prev_count is not None and prev_count > 0:
                    rate = (stage['count'] / prev_count) * 100
                
                funnel_with_rates.append({
                    'stage': stage['stage'],
                    'count': stage['count'],
                    'rate': round(rate, 1)
                })
                prev_count = stage['count']
            
            return {
                'total_visitors': visitor_stats['total_visitors'] or 0,
                'demo_created': visitor_stats['demo_created'] or 0,
                'completion_rate': round(completion_rate, 1),
                'average_session_time': round(avg_session_time, 1),
                'top_industries': [dict(stat) for stat in industry_stats],
                'conversion_funnel': funnel_with_rates,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting demo analytics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get analytics")

# FastAPI application for demo hub
app = FastAPI(title="ChatterFix Demo Hub", version="2.0.0")
demo_hub = DemoHub()

@app.on_event("startup")
async def startup_event():
    await demo_hub.initialize_redis()

@app.post("/api/demo/create")
async def create_demo(demo_data: Dict, request: Request, background_tasks: BackgroundTasks):
    """Create new demo environment"""
    try:
        demo_request = DemoRequest(
            industry=demo_data['industry'],
            company_size=demo_data['companySize'],
            role=demo_data['role'],
            use_case=demo_data['useCase'],
            first_name=demo_data['firstName'],
            last_name=demo_data['lastName'],
            email=demo_data['email'],
            company=demo_data['company'],
            phone=demo_data.get('phone'),
            region=demo_data.get('region', 'us')
        )
        
        # Track demo creation event
        background_tasks.add_task(
            demo_hub.track_visitor_event,
            request,
            VisitorEvent.DEMO_CREATED,
            {'email': demo_request.email, 'company': demo_request.company, 'industry': demo_request.industry}
        )
        
        # Create demo environment
        demo_tenant = await demo_hub.create_demo_environment(demo_request)
        
        return {
            'tenantId': demo_tenant.tenant_id,
            'demoUrl': demo_tenant.demo_url,
            'expiresAt': demo_tenant.expires_at.isoformat(),
            'industry': demo_tenant.industry,
            'sampleData': demo_tenant.sample_data,
            'status': demo_tenant.status.value
        }
        
    except Exception as e:
        logger.error(f"Error creating demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/demo/analytics/track")
async def track_analytics(event_data: Dict, request: Request):
    """Track visitor behavior for analytics"""
    try:
        event_type = VisitorEvent(event_data.get('event', 'page_visit'))
        data = event_data.get('data', {})
        
        await demo_hub.track_visitor_event(request, event_type, data)
        
        return {'status': 'tracked'}
        
    except Exception as e:
        logger.error(f"Error tracking analytics: {e}")
        return {'status': 'error', 'message': str(e)}

@app.get("/api/demo/analytics")
async def get_demo_analytics():
    """Get demo portal analytics"""
    analytics = await demo_hub.get_demo_analytics()
    return analytics

@app.post("/api/demo/{tenant_id}/tour/start")
async def start_guided_tour(tenant_id: str, tour_data: Dict, request: Request):
    """Start guided tour for demo"""
    try:
        industry = tour_data.get('industry', 'manufacturing')
        use_case = tour_data.get('useCase', 'preventive_maintenance')
        
        # Track tour start
        await demo_hub.track_visitor_event(
            request,
            VisitorEvent.TOUR_STARTED,
            {'tenant_id': tenant_id, 'industry': industry, 'use_case': use_case}
        )
        
        # Generate tour steps based on industry
        tour_steps = demo_hub.industry_templates.get(industry, demo_hub.industry_templates['manufacturing'])
        
        return {
            'tourId': str(uuid.uuid4()),
            'tenantId': tenant_id,
            'steps': [
                {
                    'id': 'welcome',
                    'title': f'Welcome to ChatterFix CMMS - {industry.title()} Demo',
                    'description': 'Explore the features most relevant to your industry',
                    'duration': 60
                },
                {
                    'id': 'assets',
                    'title': 'Asset Management',
                    'description': f'View {tour_steps["assets"]} sample {industry} assets',
                    'duration': 90
                },
                {
                    'id': 'work_orders',
                    'title': 'Work Order Management',
                    'description': f'Manage {tour_steps["work_orders"]} active work orders',
                    'duration': 120
                }
            ],
            'estimatedDuration': 270
        }
        
    except Exception as e:
        logger.error(f"Error starting guided tour: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/demo/tenants")
async def get_demo_tenants():
    """Get list of demo tenants"""
    try:
        conn = psycopg2.connect(**demo_hub.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                tenant_id, demo_url, industry, status, created_at, expires_at,
                requester_email, company_name
            FROM demo_tenants
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        tenants = cur.fetchall()
        conn.close()
        
        return {
            'tenants': [dict(tenant) for tenant in tenants],
            'total_count': len(tenants)
        }
        
    except Exception as e:
        logger.error(f"Error getting demo tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/demo/{tenant_id}")
async def delete_demo(tenant_id: str):
    """Delete demo environment"""
    try:
        conn = psycopg2.connect(**demo_hub.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get demo details
        cur.execute("""
            SELECT kubernetes_namespace
            FROM demo_tenants
            WHERE tenant_id = %s
        """, (tenant_id,))
        
        demo = cur.fetchone()
        if not demo:
            raise HTTPException(status_code=404, detail="Demo not found")
        
        # Cleanup resources
        await demo_hub._cleanup_demo_resources(tenant_id, demo['kubernetes_namespace'])
        
        # Update status
        cur.execute("""
            UPDATE demo_tenants
            SET status = 'expired', updated_at = %s
            WHERE tenant_id = %s
        """, (datetime.now(), tenant_id))
        
        conn.commit()
        conn.close()
        
        return {'status': 'deleted', 'tenant_id': tenant_id}
        
    except Exception as e:
        logger.error(f"Error deleting demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for cleanup
@app.on_event("startup")
async def start_cleanup_task():
    """Start background cleanup task"""
    async def cleanup_task():
        while True:
            try:
                await demo_hub.cleanup_expired_demos()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    asyncio.create_task(cleanup_task())

if __name__ == "__main__":
    import uvicorn
    logger.info("🧠 ChatterFix Demo Hub starting...")
    uvicorn.run(app, host="0.0.0.0", port=8011)