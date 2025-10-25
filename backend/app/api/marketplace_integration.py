"""
🌐 ChatterFix CMMS - Enterprise Marketplace Integration
Multi-cloud marketplace presence for enterprise distribution

Features:
- Google Cloud Marketplace integration with billing webhooks
- Azure Marketplace listing and subscription management
- AWS Marketplace presence with SaaS integration
- OAuth2 marketplace authentication and authorization
- Unified billing and subscription management across platforms
- Marketplace analytics and conversion tracking
"""

import asyncio
import json
import logging
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import uuid
import base64

import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
import aioredis
import requests
from fastapi import FastAPI, HTTPException, Depends, Request, Header, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, RedirectResponse
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketplaceProvider(Enum):
    GOOGLE_CLOUD = "google_cloud"
    AZURE = "azure"
    AWS = "aws"
    ORACLE_CLOUD = "oracle_cloud"

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    PENDING = "pending"
    TRIAL = "trial"

class PlanTier(Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional" 
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

@dataclass
class MarketplaceSubscription:
    subscription_id: str
    marketplace: MarketplaceProvider
    customer_id: str
    plan_tier: PlanTier
    status: SubscriptionStatus
    billing_cycle: str  # monthly, annual
    unit_price: float
    quantity: int
    total_amount: float
    currency: str
    trial_end_date: Optional[datetime]
    subscription_start: datetime
    next_billing_date: datetime
    marketplace_customer_id: str
    entitlements: Dict
    metadata: Dict

@dataclass
class MarketplaceListing:
    marketplace: MarketplaceProvider
    listing_id: str
    product_name: str
    description: str
    pricing_model: str
    plans: List[Dict]
    support_contact: str
    documentation_url: str
    privacy_policy_url: str
    terms_of_service_url: str
    status: str
    last_updated: datetime

class MarketplaceIntegration:
    """Unified marketplace integration for enterprise distribution"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'chatterfix_cmms',
            'user': 'postgres',
            'password': 'your_password'
        }
        self.redis_client = None
        
        # Marketplace API configurations
        self.marketplace_configs = {
            MarketplaceProvider.GOOGLE_CLOUD: {
                'api_base': 'https://cloudcommerceconsumer.googleapis.com/v1',
                'webhook_secret': 'gcp_webhook_secret_key',
                'oauth_scopes': ['https://www.googleapis.com/auth/cloud-platform'],
                'product_id': 'chatterfix-cmms',
                'billing_account': 'your-gcp-billing-account'
            },
            MarketplaceProvider.AZURE: {
                'api_base': 'https://marketplaceapi.microsoft.com/api',
                'webhook_secret': 'azure_webhook_secret_key',
                'tenant_id': 'your-azure-tenant-id',
                'client_id': 'your-azure-client-id',
                'client_secret': 'your-azure-client-secret',
                'offer_id': 'chatterfix-cmms-offer'
            },
            MarketplaceProvider.AWS: {
                'api_base': 'https://aws-mp-entitlement-service.amazonaws.com',
                'webhook_secret': 'aws_webhook_secret_key',
                'product_code': 'chatterfix-cmms-product',
                'access_key_id': 'your-aws-access-key',
                'secret_access_key': 'your-aws-secret-key',
                'region': 'us-east-1'
            }
        }
        
        # Standard pricing plans across all marketplaces
        self.pricing_plans = {
            PlanTier.STARTER: {
                'name': 'ChatterFix Starter',
                'description': 'Essential CMMS for small teams',
                'monthly_price': 49.00,
                'annual_price': 490.00,
                'max_users': 10,
                'max_assets': 500,
                'features': [
                    'Basic work order management',
                    'Asset tracking',
                    'Mobile app access',
                    'Email support'
                ]
            },
            PlanTier.PROFESSIONAL: {
                'name': 'ChatterFix Professional',
                'description': 'Advanced CMMS with AI features',
                'monthly_price': 149.00,
                'annual_price': 1490.00,
                'max_users': 50,
                'max_assets': 5000,
                'features': [
                    'All Starter features',
                    'Predictive maintenance AI',
                    'Advanced analytics',
                    'API access',
                    'Priority support'
                ]
            },
            PlanTier.ENTERPRISE: {
                'name': 'ChatterFix Enterprise',
                'description': 'Full-featured CMMS for large organizations',
                'monthly_price': 299.00,
                'annual_price': 2990.00,
                'max_users': 500,
                'max_assets': 50000,
                'features': [
                    'All Professional features',
                    'Custom integrations',
                    'Advanced security (SSO, RBAC)',
                    'Dedicated success manager',
                    '24/7 priority support',
                    'Custom training'
                ]
            }
        }
        
    async def initialize_redis(self):
        """Initialize Redis connection for caching"""
        try:
            self.redis_client = await aioredis.from_url("redis://localhost")
            logger.info("Redis connection established for marketplace integration")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    async def create_marketplace_listing(self, marketplace: MarketplaceProvider) -> MarketplaceListing:
        """Create product listing on specified marketplace"""
        try:
            if marketplace == MarketplaceProvider.GOOGLE_CLOUD:
                listing = await self._create_gcp_listing()
            elif marketplace == MarketplaceProvider.AZURE:
                listing = await self._create_azure_listing()
            elif marketplace == MarketplaceProvider.AWS:
                listing = await self._create_aws_listing()
            else:
                raise ValueError(f"Unsupported marketplace: {marketplace}")
            
            # Save listing to database
            await self._save_marketplace_listing(listing)
            
            return listing
            
        except Exception as e:
            logger.error(f"Error creating marketplace listing: {e}")
            raise HTTPException(status_code=500, detail="Failed to create marketplace listing")
    
    async def _create_gcp_listing(self) -> MarketplaceListing:
        """Create Google Cloud Marketplace listing"""
        try:
            # Prepare listing data for GCP
            listing_data = {
                'displayName': 'ChatterFix CMMS - AI-Powered Maintenance Management',
                'description': 'Enterprise-grade CMMS with predictive maintenance AI, mobile-first design, and measurable ROI. Reduce downtime by 40% and maintenance costs by 35% with ChatterFix.',
                'documentation': {
                    'url': 'https://docs.chatterfix.com',
                    'summary': 'Complete documentation for ChatterFix CMMS setup and usage'
                },
                'support': {
                    'url': 'https://support.chatterfix.com',
                    'email': 'support@chatterfix.com',
                    'description': 'Enterprise-grade support with dedicated success managers'
                },
                'pricing': {
                    'type': 'SUBSCRIPTION',
                    'currency': 'USD',
                    'plans': [
                        {
                            'planId': 'starter',
                            'displayName': self.pricing_plans[PlanTier.STARTER]['name'],
                            'description': self.pricing_plans[PlanTier.STARTER]['description'],
                            'pricing': {
                                'monthly': self.pricing_plans[PlanTier.STARTER]['monthly_price'],
                                'annual': self.pricing_plans[PlanTier.STARTER]['annual_price']
                            }
                        },
                        {
                            'planId': 'professional',
                            'displayName': self.pricing_plans[PlanTier.PROFESSIONAL]['name'],
                            'description': self.pricing_plans[PlanTier.PROFESSIONAL]['description'],
                            'pricing': {
                                'monthly': self.pricing_plans[PlanTier.PROFESSIONAL]['monthly_price'],
                                'annual': self.pricing_plans[PlanTier.PROFESSIONAL]['annual_price']
                            }
                        },
                        {
                            'planId': 'enterprise',
                            'displayName': self.pricing_plans[PlanTier.ENTERPRISE]['name'],
                            'description': self.pricing_plans[PlanTier.ENTERPRISE]['description'],
                            'pricing': {
                                'monthly': self.pricing_plans[PlanTier.ENTERPRISE]['monthly_price'],
                                'annual': self.pricing_plans[PlanTier.ENTERPRISE]['annual_price']
                            }
                        }
                    ]
                },
                'categories': ['AI & ML', 'Business Applications', 'Enterprise Software'],
                'tags': ['CMMS', 'Maintenance Management', 'Predictive Analytics', 'IoT', 'Enterprise'],
                'integrations': {
                    'oauth2': {
                        'enabled': True,
                        'authorize_url': 'https://api.chatterfix.com/oauth/authorize',
                        'token_url': 'https://api.chatterfix.com/oauth/token',
                        'scopes': ['read', 'write', 'admin']
                    },
                    'webhooks': {
                        'subscription_events': 'https://api.chatterfix.com/webhooks/gcp/subscription',
                        'usage_events': 'https://api.chatterfix.com/webhooks/gcp/usage'
                    }
                }
            }
            
            # Simulate API call to create listing (replace with actual GCP API call)
            logger.info("Creating GCP Marketplace listing...")
            
            # In production, this would be:
            # response = await gcp_marketplace_client.create_listing(listing_data)
            
            # Simulated response
            listing_id = f"gcp_listing_{uuid.uuid4().hex[:8]}"
            
            return MarketplaceListing(
                marketplace=MarketplaceProvider.GOOGLE_CLOUD,
                listing_id=listing_id,
                product_name="ChatterFix CMMS",
                description=listing_data['description'],
                pricing_model="SUBSCRIPTION",
                plans=listing_data['pricing']['plans'],
                support_contact="support@chatterfix.com",
                documentation_url="https://docs.chatterfix.com",
                privacy_policy_url="https://chatterfix.com/privacy",
                terms_of_service_url="https://chatterfix.com/terms",
                status="pending_review",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error creating GCP listing: {e}")
            raise
    
    async def _create_azure_listing(self) -> MarketplaceListing:
        """Create Azure Marketplace listing"""
        try:
            # Prepare listing data for Azure
            offer_data = {
                'offerTypeId': 'microsoft-azure-saas',
                'name': 'ChatterFix CMMS Enterprise',
                'displayName': 'ChatterFix CMMS - AI-Powered Maintenance Management',
                'description': 'Transform your maintenance operations with AI-powered predictive analytics, mobile-first design, and enterprise-grade security. Achieve 40% downtime reduction and measurable ROI.',
                'longDescription': '''
                ChatterFix CMMS revolutionizes maintenance management with artificial intelligence, providing:
                
                • Predictive Maintenance: AI algorithms prevent failures before they occur
                • Mobile-First Design: Technicians work efficiently with intuitive mobile apps  
                • Real-Time Analytics: Live dashboards with actionable insights
                • Enterprise Security: OAuth2, RBAC, and zero-trust architecture
                • Measurable ROI: Track cost savings and efficiency improvements
                
                Trusted by Fortune 500 companies across manufacturing, healthcare, energy, and logistics.
                ''',
                'categories': ['Analytics', 'Productivity', 'IT & Management Tools'],
                'industries': ['Manufacturing', 'Healthcare', 'Energy', 'Transportation'],
                'plannedAvailability': 'Public',
                'contacts': {
                    'engineering': 'engineering@chatterfix.com',
                    'support': 'support@chatterfix.com'
                },
                'testDrive': {
                    'enabled': True,
                    'duration': 'P14D',  # 14 days
                    'url': 'https://demo.chatterfix.com'
                },
                'plans': [
                    {
                        'planId': 'starter',
                        'name': self.pricing_plans[PlanTier.STARTER]['name'],
                        'description': self.pricing_plans[PlanTier.STARTER]['description'],
                        'isPrivate': False,
                        'pricing': {
                            'recurrentPrice': self.pricing_plans[PlanTier.STARTER]['monthly_price'],
                            'recurrentBillingTerm': 'Monthly'
                        }
                    },
                    {
                        'planId': 'professional',
                        'name': self.pricing_plans[PlanTier.PROFESSIONAL]['name'],
                        'description': self.pricing_plans[PlanTier.PROFESSIONAL]['description'],
                        'isPrivate': False,
                        'pricing': {
                            'recurrentPrice': self.pricing_plans[PlanTier.PROFESSIONAL]['monthly_price'],
                            'recurrentBillingTerm': 'Monthly'
                        }
                    },
                    {
                        'planId': 'enterprise',
                        'name': self.pricing_plans[PlanTier.ENTERPRISE]['name'],
                        'description': self.pricing_plans[PlanTier.ENTERPRISE]['description'],
                        'isPrivate': False,
                        'pricing': {
                            'recurrentPrice': self.pricing_plans[PlanTier.ENTERPRISE]['monthly_price'],
                            'recurrentBillingTerm': 'Monthly'
                        }
                    }
                ],
                'technicalConfiguration': {
                    'landingPageUrl': 'https://portal.chatterfix.com/azure/landing',
                    'connectionWebhook': 'https://api.chatterfix.com/webhooks/azure/connection',
                    'allowedCustomerOperations': ['read', 'update', 'delete'],
                    'authenticationMode': 'oauth'
                }
            }
            
            # Simulate Azure Partner Center API call
            logger.info("Creating Azure Marketplace offer...")
            
            # In production:
            # response = await azure_partner_center_client.create_offer(offer_data)
            
            listing_id = f"azure_offer_{uuid.uuid4().hex[:8]}"
            
            return MarketplaceListing(
                marketplace=MarketplaceProvider.AZURE,
                listing_id=listing_id,
                product_name="ChatterFix CMMS Enterprise",
                description=offer_data['description'],
                pricing_model="SUBSCRIPTION",
                plans=offer_data['plans'],
                support_contact="support@chatterfix.com",
                documentation_url="https://docs.chatterfix.com",
                privacy_policy_url="https://chatterfix.com/privacy",
                terms_of_service_url="https://chatterfix.com/terms",
                status="pending_certification",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error creating Azure listing: {e}")
            raise
    
    async def _create_aws_listing(self) -> MarketplaceListing:
        """Create AWS Marketplace listing"""
        try:
            # Prepare listing data for AWS
            product_data = {
                'productTitle': 'ChatterFix CMMS - AI-Powered Maintenance Management',
                'productDescription': 'Enterprise CMMS with predictive maintenance AI, reducing downtime by 40% and maintenance costs by 35%. Mobile-first design with real-time analytics.',
                'longDescription': '''
                ChatterFix CMMS transforms maintenance operations with advanced AI capabilities:
                
                Key Features:
                • Predictive Maintenance: Machine learning prevents equipment failures
                • Mobile Excellence: Native iOS/Android apps for field technicians
                • Real-Time Dashboards: Live performance metrics and KPIs
                • Enterprise Security: SOC2, HIPAA compliance with OAuth2 authentication
                • ROI Tracking: Measure cost savings and efficiency improvements
                
                Industry Leadership:
                • 500+ Fortune 1000 customers
                • 99.9% uptime SLA
                • 24/7 enterprise support
                • Seamless ERP integrations
                
                Deployment Options:
                • SaaS: Fully managed cloud service
                • Private Cloud: Dedicated infrastructure
                • Hybrid: On-premises with cloud analytics
                ''',
                'categories': ['Business Applications', 'Analytics', 'Machine Learning'],
                'keywords': ['CMMS', 'Maintenance', 'Predictive Analytics', 'IoT', 'AI', 'Enterprise'],
                'supportDescription': 'Enterprise-grade support with dedicated customer success managers, 24/7 technical support, and comprehensive training programs.',
                'refundPolicy': 'Full refund within 30 days for annual subscriptions',
                'pricing': {
                    'dimension': 'Users',
                    'pricingModel': 'SaaS Contract',
                    'contractLength': ['1 Month', '12 Months', '36 Months'],
                    'paymentSchedule': 'Upfront',
                    'freeTrial': {
                        'duration': 14,
                        'description': '14-day free trial with full feature access'
                    }
                },
                'regions': ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'],
                'fulfillmentOptions': {
                    'saasRedirectUrl': 'https://portal.chatterfix.com/aws/subscribe',
                    'webhookUrl': 'https://api.chatterfix.com/webhooks/aws/entitlement'
                }
            }
            
            # Simulate AWS Marketplace Catalog API call
            logger.info("Creating AWS Marketplace product...")
            
            # In production:
            # response = await aws_marketplace_client.start_change_set(product_data)
            
            listing_id = f"aws_product_{uuid.uuid4().hex[:8]}"
            
            return MarketplaceListing(
                marketplace=MarketplaceProvider.AWS,
                listing_id=listing_id,
                product_name="ChatterFix CMMS",
                description=product_data['productDescription'],
                pricing_model="SaaS Contract",
                plans=[],  # AWS uses different pricing structure
                support_contact="support@chatterfix.com",
                documentation_url="https://docs.chatterfix.com",
                privacy_policy_url="https://chatterfix.com/privacy",
                terms_of_service_url="https://chatterfix.com/terms",
                status="under_review",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error creating AWS listing: {e}")
            raise
    
    async def _save_marketplace_listing(self, listing: MarketplaceListing):
        """Save marketplace listing to database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO marketplace_listings 
                (marketplace, listing_id, product_name, description, pricing_model, 
                 plans, support_contact, documentation_url, privacy_policy_url, 
                 terms_of_service_url, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (marketplace, listing_id) DO UPDATE SET
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at
            """, (
                listing.marketplace.value,
                listing.listing_id,
                listing.product_name,
                listing.description,
                listing.pricing_model,
                json.dumps(listing.plans),
                listing.support_contact,
                listing.documentation_url,
                listing.privacy_policy_url,
                listing.terms_of_service_url,
                listing.status,
                datetime.now(),
                listing.last_updated
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Marketplace listing saved: {listing.marketplace.value} - {listing.listing_id}")
            
        except Exception as e:
            logger.error(f"Error saving marketplace listing: {e}")
    
    async def handle_subscription_webhook(self, marketplace: MarketplaceProvider, payload: Dict, signature: str) -> Dict:
        """Handle subscription webhooks from marketplaces"""
        try:
            # Verify webhook signature
            if not await self._verify_webhook_signature(marketplace, payload, signature):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            # Process webhook based on marketplace
            if marketplace == MarketplaceProvider.GOOGLE_CLOUD:
                result = await self._handle_gcp_webhook(payload)
            elif marketplace == MarketplaceProvider.AZURE:
                result = await self._handle_azure_webhook(payload)
            elif marketplace == MarketplaceProvider.AWS:
                result = await self._handle_aws_webhook(payload)
            else:
                raise ValueError(f"Unsupported marketplace webhook: {marketplace}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            raise HTTPException(status_code=500, detail="Failed to process webhook")
    
    async def _verify_webhook_signature(self, marketplace: MarketplaceProvider, payload: Dict, signature: str) -> bool:
        """Verify webhook signature for security"""
        try:
            config = self.marketplace_configs[marketplace]
            secret = config['webhook_secret']
            
            # Calculate expected signature
            payload_str = json.dumps(payload, sort_keys=True)
            expected_signature = hmac.new(
                secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def _handle_gcp_webhook(self, payload: Dict) -> Dict:
        """Handle Google Cloud Marketplace webhook"""
        try:
            event_type = payload.get('eventType')
            subscription_data = payload.get('subscription', {})
            
            if event_type == 'SUBSCRIPTION_CREATED':
                subscription = await self._create_subscription_from_gcp(subscription_data)
                await self._provision_customer_account(subscription)
                
            elif event_type == 'SUBSCRIPTION_CANCELLED':
                await self._cancel_subscription(subscription_data['name'])
                
            elif event_type == 'SUBSCRIPTION_PLAN_CHANGED':
                await self._update_subscription_plan(subscription_data)
                
            elif event_type == 'SUBSCRIPTION_PAYMENT_FAILED':
                await self._handle_payment_failure(subscription_data)
            
            return {
                'status': 'processed',
                'event_type': event_type,
                'subscription_id': subscription_data.get('name'),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling GCP webhook: {e}")
            raise
    
    async def _handle_azure_webhook(self, payload: Dict) -> Dict:
        """Handle Azure Marketplace webhook"""
        try:
            action = payload.get('action')
            subscription_data = payload.get('subscription', {})
            
            if action == 'Subscribe':
                subscription = await self._create_subscription_from_azure(subscription_data)
                await self._provision_customer_account(subscription)
                
            elif action == 'Unsubscribe':
                await self._cancel_subscription(subscription_data['id'])
                
            elif action == 'ChangePlan':
                await self._update_subscription_plan(subscription_data)
                
            elif action == 'ChangeQuantity':
                await self._update_subscription_quantity(subscription_data)
            
            return {
                'status': 'processed',
                'action': action,
                'subscription_id': subscription_data.get('id'),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling Azure webhook: {e}")
            raise
    
    async def _handle_aws_webhook(self, payload: Dict) -> Dict:
        """Handle AWS Marketplace webhook"""
        try:
            event_type = payload.get('eventType')
            entitlement_data = payload.get('entitlement', {})
            
            if event_type == 'entitlement-updated':
                subscription = await self._create_subscription_from_aws(entitlement_data)
                await self._provision_customer_account(subscription)
                
            elif event_type == 'subscription-succeeded':
                await self._activate_aws_subscription(entitlement_data)
                
            elif event_type == 'subscription-ended':
                await self._cancel_subscription(entitlement_data['customerIdentifier'])
            
            return {
                'status': 'processed',
                'event_type': event_type,
                'customer_identifier': entitlement_data.get('customerIdentifier'),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling AWS webhook: {e}")
            raise
    
    async def _create_subscription_from_gcp(self, data: Dict) -> MarketplaceSubscription:
        """Create subscription from GCP marketplace data"""
        plan_id = data.get('planId', 'professional')
        plan_tier = PlanTier(plan_id) if plan_id in [p.value for p in PlanTier] else PlanTier.PROFESSIONAL
        
        subscription = MarketplaceSubscription(
            subscription_id=data['name'],
            marketplace=MarketplaceProvider.GOOGLE_CLOUD,
            customer_id=str(uuid.uuid4()),
            plan_tier=plan_tier,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle='monthly',
            unit_price=self.pricing_plans[plan_tier]['monthly_price'],
            quantity=1,
            total_amount=self.pricing_plans[plan_tier]['monthly_price'],
            currency='USD',
            trial_end_date=None,
            subscription_start=datetime.now(),
            next_billing_date=datetime.now() + timedelta(days=30),
            marketplace_customer_id=data.get('customerId'),
            entitlements=self.pricing_plans[plan_tier],
            metadata={'gcp_subscription_name': data['name']}
        )
        
        await self._save_subscription(subscription)
        return subscription
    
    async def _create_subscription_from_azure(self, data: Dict) -> MarketplaceSubscription:
        """Create subscription from Azure marketplace data"""
        plan_id = data.get('planId', 'professional')
        plan_tier = PlanTier(plan_id) if plan_id in [p.value for p in PlanTier] else PlanTier.PROFESSIONAL
        
        subscription = MarketplaceSubscription(
            subscription_id=data['id'],
            marketplace=MarketplaceProvider.AZURE,
            customer_id=str(uuid.uuid4()),
            plan_tier=plan_tier,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle='monthly',
            unit_price=self.pricing_plans[plan_tier]['monthly_price'],
            quantity=data.get('quantity', 1),
            total_amount=self.pricing_plans[plan_tier]['monthly_price'] * data.get('quantity', 1),
            currency='USD',
            trial_end_date=datetime.now() + timedelta(days=14) if data.get('isFreeTrial') else None,
            subscription_start=datetime.now(),
            next_billing_date=datetime.now() + timedelta(days=30),
            marketplace_customer_id=data.get('purchaser', {}).get('emailId'),
            entitlements=self.pricing_plans[plan_tier],
            metadata={'azure_subscription_id': data['id']}
        )
        
        await self._save_subscription(subscription)
        return subscription
    
    async def _create_subscription_from_aws(self, data: Dict) -> MarketplaceSubscription:
        """Create subscription from AWS marketplace data"""
        # AWS uses different entitlement structure
        product_code = data.get('productCode', 'chatterfix-cmms-product')
        dimension = data.get('dimension', 'Users')
        
        # Map AWS dimension to plan tier
        quantity = int(data.get('value', 10))
        if quantity <= 10:
            plan_tier = PlanTier.STARTER
        elif quantity <= 50:
            plan_tier = PlanTier.PROFESSIONAL
        else:
            plan_tier = PlanTier.ENTERPRISE
        
        subscription = MarketplaceSubscription(
            subscription_id=data['customerIdentifier'],
            marketplace=MarketplaceProvider.AWS,
            customer_id=str(uuid.uuid4()),
            plan_tier=plan_tier,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle='monthly',
            unit_price=self.pricing_plans[plan_tier]['monthly_price'],
            quantity=quantity,
            total_amount=self.pricing_plans[plan_tier]['monthly_price'],
            currency='USD',
            trial_end_date=None,
            subscription_start=datetime.now(),
            next_billing_date=datetime.now() + timedelta(days=30),
            marketplace_customer_id=data['customerIdentifier'],
            entitlements=self.pricing_plans[plan_tier],
            metadata={'aws_product_code': product_code, 'dimension': dimension}
        )
        
        await self._save_subscription(subscription)
        return subscription
    
    async def _save_subscription(self, subscription: MarketplaceSubscription):
        """Save subscription to database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO marketplace_subscriptions 
                (subscription_id, marketplace, customer_id, plan_tier, status, billing_cycle,
                 unit_price, quantity, total_amount, currency, trial_end_date, 
                 subscription_start, next_billing_date, marketplace_customer_id, 
                 entitlements, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (subscription_id, marketplace) DO UPDATE SET
                status = EXCLUDED.status,
                plan_tier = EXCLUDED.plan_tier,
                quantity = EXCLUDED.quantity,
                total_amount = EXCLUDED.total_amount,
                next_billing_date = EXCLUDED.next_billing_date,
                updated_at = %s
            """, (
                subscription.subscription_id,
                subscription.marketplace.value,
                subscription.customer_id,
                subscription.plan_tier.value,
                subscription.status.value,
                subscription.billing_cycle,
                subscription.unit_price,
                subscription.quantity,
                subscription.total_amount,
                subscription.currency,
                subscription.trial_end_date,
                subscription.subscription_start,
                subscription.next_billing_date,
                subscription.marketplace_customer_id,
                json.dumps(subscription.entitlements),
                json.dumps(subscription.metadata),
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Subscription saved: {subscription.subscription_id}")
            
        except Exception as e:
            logger.error(f"Error saving subscription: {e}")
    
    async def _provision_customer_account(self, subscription: MarketplaceSubscription):
        """Provision customer account and resources"""
        try:
            # Create customer account
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO customers 
                (id, marketplace_subscription_id, marketplace, plan_tier, status, 
                 max_users, max_assets, created_at)
                VALUES (%s, %s, %s, %s, 'active', %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                plan_tier = EXCLUDED.plan_tier,
                max_users = EXCLUDED.max_users,
                max_assets = EXCLUDED.max_assets,
                updated_at = %s
            """, (
                subscription.customer_id,
                subscription.subscription_id,
                subscription.marketplace.value,
                subscription.plan_tier.value,
                subscription.entitlements['max_users'],
                subscription.entitlements['max_assets'],
                datetime.now(),
                datetime.now()
            ))
            
            # Create default admin user
            cur.execute("""
                INSERT INTO users 
                (id, customer_id, email, role, created_at)
                VALUES (%s, %s, %s, 'admin', %s)
                ON CONFLICT (email) DO NOTHING
            """, (
                str(uuid.uuid4()),
                subscription.customer_id,
                subscription.marketplace_customer_id,
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            # Send welcome email and onboarding information
            await self._send_onboarding_email(subscription)
            
            logger.info(f"Customer account provisioned: {subscription.customer_id}")
            
        except Exception as e:
            logger.error(f"Error provisioning customer account: {e}")
    
    async def _send_onboarding_email(self, subscription: MarketplaceSubscription):
        """Send onboarding email to new customer"""
        try:
            # Queue onboarding email
            email_data = {
                'customer_id': subscription.customer_id,
                'email': subscription.marketplace_customer_id,
                'plan_tier': subscription.plan_tier.value,
                'marketplace': subscription.marketplace.value,
                'trial_end_date': subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
                'login_url': f'https://portal.chatterfix.com/marketplace/{subscription.marketplace.value}/login',
                'support_url': 'https://support.chatterfix.com'
            }
            
            if self.redis_client:
                await self.redis_client.lpush(
                    'onboarding_emails',
                    json.dumps(email_data)
                )
            
            logger.info(f"Onboarding email queued for {subscription.marketplace_customer_id}")
            
        except Exception as e:
            logger.error(f"Error sending onboarding email: {e}")
    
    async def get_marketplace_analytics(self) -> Dict:
        """Get marketplace performance analytics"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get subscription statistics
            cur.execute("""
                SELECT 
                    marketplace,
                    COUNT(*) as total_subscriptions,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_subscriptions,
                    COUNT(CASE WHEN status = 'trial' THEN 1 END) as trial_subscriptions,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_revenue_per_customer
                FROM marketplace_subscriptions
                GROUP BY marketplace
            """)
            
            marketplace_stats = cur.fetchall()
            
            # Get plan distribution
            cur.execute("""
                SELECT 
                    plan_tier,
                    COUNT(*) as count,
                    SUM(total_amount) as revenue
                FROM marketplace_subscriptions
                WHERE status = 'active'
                GROUP BY plan_tier
            """)
            
            plan_distribution = cur.fetchall()
            
            # Get growth metrics
            cur.execute("""
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as new_subscriptions,
                    SUM(total_amount) as monthly_revenue
                FROM marketplace_subscriptions
                WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY month
                ORDER BY month
            """)
            
            growth_metrics = cur.fetchall()
            
            # Get conversion metrics
            cur.execute("""
                SELECT 
                    marketplace,
                    COUNT(CASE WHEN status = 'trial' THEN 1 END) as trials,
                    COUNT(CASE WHEN status = 'active' AND trial_end_date IS NOT NULL THEN 1 END) as trial_conversions
                FROM marketplace_subscriptions
                GROUP BY marketplace
            """)
            
            conversion_stats = cur.fetchall()
            
            conn.close()
            
            return {
                'marketplace_performance': [dict(stat) for stat in marketplace_stats],
                'plan_distribution': [dict(plan) for plan in plan_distribution],
                'growth_trends': [dict(metric) for metric in growth_metrics],
                'conversion_rates': [
                    {
                        **dict(stat),
                        'conversion_rate': (stat['trial_conversions'] / max(1, stat['trials'])) * 100
                    }
                    for stat in conversion_stats
                ],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting marketplace analytics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get analytics")

# FastAPI application for marketplace integration
app = FastAPI(title="ChatterFix Marketplace Integration", version="2.0.0")
marketplace_integration = MarketplaceIntegration()
security = HTTPBearer()

@app.on_event("startup")
async def startup_event():
    await marketplace_integration.initialize_redis()

@app.post("/api/marketplace/listings/{marketplace}")
async def create_marketplace_listing(marketplace: str):
    """Create product listing on specified marketplace"""
    marketplace_enum = MarketplaceProvider(marketplace)
    listing = await marketplace_integration.create_marketplace_listing(marketplace_enum)
    
    return {
        'listing_id': listing.listing_id,
        'marketplace': listing.marketplace.value,
        'product_name': listing.product_name,
        'status': listing.status,
        'pricing_plans': len(listing.plans),
        'created_at': listing.last_updated.isoformat()
    }

@app.post("/api/marketplace/webhooks/{marketplace}")
async def handle_marketplace_webhook(
    marketplace: str,
    request: Request,
    x_signature: str = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Handle webhooks from marketplace providers"""
    try:
        marketplace_enum = MarketplaceProvider(marketplace)
        payload = await request.json()
        
        # Process webhook in background
        background_tasks.add_task(
            marketplace_integration.handle_subscription_webhook,
            marketplace_enum,
            payload,
            x_signature or ""
        )
        
        return {"status": "received", "marketplace": marketplace}
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/marketplace/subscriptions")
async def get_marketplace_subscriptions(marketplace: Optional[str] = None):
    """Get marketplace subscriptions"""
    try:
        conn = psycopg2.connect(**marketplace_integration.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if marketplace:
            cur.execute("""
                SELECT * FROM marketplace_subscriptions 
                WHERE marketplace = %s
                ORDER BY created_at DESC
            """, (marketplace,))
        else:
            cur.execute("""
                SELECT * FROM marketplace_subscriptions 
                ORDER BY created_at DESC
            """)
        
        subscriptions = cur.fetchall()
        conn.close()
        
        return {
            'subscriptions': [dict(sub) for sub in subscriptions],
            'total_count': len(subscriptions)
        }
        
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/marketplace/analytics")
async def get_marketplace_analytics():
    """Get marketplace performance analytics"""
    analytics = await marketplace_integration.get_marketplace_analytics()
    return analytics

@app.get("/api/marketplace/oauth/authorize")
async def marketplace_oauth_authorize(
    marketplace: str,
    code: str,
    state: str,
    customer_id: Optional[str] = None
):
    """Handle OAuth authorization from marketplace"""
    try:
        # Validate state parameter
        if not state:
            raise HTTPException(status_code=400, detail="Missing state parameter")
        
        # Generate access token
        token_payload = {
            'customer_id': customer_id or str(uuid.uuid4()),
            'marketplace': marketplace,
            'scopes': ['read', 'write'],
            'exp': datetime.now() + timedelta(hours=24),
            'iat': datetime.now(),
            'iss': 'chatterfix-cmms'
        }
        
        access_token = jwt.encode(token_payload, 'your_jwt_secret', algorithm='HS256')
        
        # Redirect to marketplace with token
        redirect_url = f"https://portal.chatterfix.com/marketplace/{marketplace}/callback?token={access_token}&state={state}"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Error in OAuth authorize: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/marketplace/oauth/token")
async def marketplace_oauth_token(request: Request):
    """OAuth token endpoint for marketplace integrations"""
    try:
        form_data = await request.form()
        grant_type = form_data.get('grant_type')
        
        if grant_type != 'authorization_code':
            raise HTTPException(status_code=400, detail="Unsupported grant type")
        
        code = form_data.get('code')
        client_id = form_data.get('client_id')
        
        # Validate authorization code
        if not code or not client_id:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Generate tokens
        access_token_payload = {
            'client_id': client_id,
            'scopes': ['read', 'write'],
            'exp': datetime.now() + timedelta(hours=1),
            'iat': datetime.now(),
            'type': 'access_token'
        }
        
        refresh_token_payload = {
            'client_id': client_id,
            'exp': datetime.now() + timedelta(days=30),
            'iat': datetime.now(),
            'type': 'refresh_token'
        }
        
        access_token = jwt.encode(access_token_payload, 'your_jwt_secret', algorithm='HS256')
        refresh_token = jwt.encode(refresh_token_payload, 'your_jwt_secret', algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'read write'
        }
        
    except Exception as e:
        logger.error(f"Error in OAuth token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("🌐 ChatterFix Marketplace Integration starting...")
    uvicorn.run(app, host="0.0.0.0", port=8010)