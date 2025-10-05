#!/usr/bin/env python3
"""
Billing and Subscription Management System
Comprehensive billing, subscription, and payment management for multi-cloud customers
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import stripe

logger = logging.getLogger(__name__)

# Enums for billing system
class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    PENDING = "pending"

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class TierType(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

# Data Models
@dataclass
class ServicePlan:
    plan_id: str
    name: str
    description: str
    cloud_provider: str  # gcp, aws, azure
    service_type: str
    tier: TierType
    base_price: float
    included_resources: Dict[str, Any]
    overage_rates: Dict[str, float]
    billing_cycle: BillingCycle
    features: List[str]
    limits: Dict[str, Any]

@dataclass
class CustomerSubscription:
    subscription_id: str
    customer_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime]
    billing_cycle: BillingCycle
    monthly_cost: float
    usage_data: Dict[str, Any]
    addons: List[str]
    custom_pricing: Optional[Dict[str, float]]
    auto_renew: bool
    payment_method_id: str
    tags: Dict[str, str]

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    subscription_ids: List[str]
    amount: float
    tax_amount: float
    total_amount: float
    billing_period_start: datetime
    billing_period_end: datetime
    due_date: datetime
    status: PaymentStatus
    line_items: List[Dict[str, Any]]
    payment_attempts: List[Dict[str, Any]]
    created_at: datetime

@dataclass
class UsageRecord:
    record_id: str
    customer_id: str
    subscription_id: str
    service_type: str
    metric_name: str
    quantity: float
    unit: str
    timestamp: datetime
    cost: float
    metadata: Dict[str, Any]

class BillingSubscriptionManager:
    def __init__(self, stripe_api_key: str, tax_rate: float = 0.08):
        self.stripe_api_key = stripe_api_key
        self.tax_rate = tax_rate
        
        # Initialize Stripe
        stripe.api_key = stripe_api_key
        
        # In-memory storage (replace with actual database)
        self.subscriptions: Dict[str, CustomerSubscription] = {}
        self.invoices: Dict[str, Invoice] = {}
        self.usage_records: Dict[str, List[UsageRecord]] = {}
        self.service_plans: Dict[str, ServicePlan] = {}
        
        # Initialize default service plans
        self._initialize_service_plans()
    
    def _initialize_service_plans(self):
        """Initialize default service plans for each cloud provider"""
        
        # GCP Service Plans
        self.service_plans.update({
            'gcp_starter': ServicePlan(
                plan_id='gcp_starter',
                name='GCP Starter',
                description='Perfect for small applications and development',
                cloud_provider='gcp',
                service_type='full_stack',
                tier=TierType.STARTER,
                base_price=25.0,
                included_resources={
                    'cloud_run_requests': 1000000,
                    'storage_gb': 10,
                    'ai_api_calls': 1000,
                    'bandwidth_gb': 100
                },
                overage_rates={
                    'cloud_run_requests': 0.0000004,  # per request
                    'storage_gb': 0.02,  # per GB
                    'ai_api_calls': 0.001,  # per call
                    'bandwidth_gb': 0.12  # per GB
                },
                billing_cycle=BillingCycle.MONTHLY,
                features=[
                    'Cloud Run deployment',
                    'Cloud Storage',
                    'Basic AI services',
                    'Email support'
                ],
                limits={
                    'max_services': 5,
                    'max_domains': 2,
                    'support_level': 'email'
                }
            ),
            'gcp_professional': ServicePlan(
                plan_id='gcp_professional',
                name='GCP Professional',
                description='For growing businesses with advanced needs',
                cloud_provider='gcp',
                service_type='full_stack',
                tier=TierType.PROFESSIONAL,
                base_price=99.0,
                included_resources={
                    'cloud_run_requests': 10000000,
                    'storage_gb': 100,
                    'ai_api_calls': 10000,
                    'bandwidth_gb': 500,
                    'sql_instances': 2
                },
                overage_rates={
                    'cloud_run_requests': 0.0000003,
                    'storage_gb': 0.015,
                    'ai_api_calls': 0.0008,
                    'bandwidth_gb': 0.10,
                    'sql_instances': 15.0
                },
                billing_cycle=BillingCycle.MONTHLY,
                features=[
                    'All Starter features',
                    'Cloud SQL databases',
                    'Advanced AI models',
                    'Custom domains',
                    'Priority support'
                ],
                limits={
                    'max_services': 20,
                    'max_domains': 10,
                    'support_level': 'priority'
                }
            ),
            'gcp_enterprise': ServicePlan(
                plan_id='gcp_enterprise',
                name='GCP Enterprise',
                description='Enterprise-grade infrastructure and support',
                cloud_provider='gcp',
                service_type='full_stack',
                tier=TierType.ENTERPRISE,
                base_price=299.0,
                included_resources={
                    'cloud_run_requests': 100000000,
                    'storage_gb': 1000,
                    'ai_api_calls': 100000,
                    'bandwidth_gb': 2000,
                    'sql_instances': 10,
                    'dedicated_support': True
                },
                overage_rates={
                    'cloud_run_requests': 0.0000002,
                    'storage_gb': 0.01,
                    'ai_api_calls': 0.0005,
                    'bandwidth_gb': 0.08,
                    'sql_instances': 12.0
                },
                billing_cycle=BillingCycle.MONTHLY,
                features=[
                    'All Professional features',
                    'Dedicated support engineer',
                    'SLA guarantees',
                    'Advanced security',
                    'Custom integrations',
                    'Multi-region deployment'
                ],
                limits={
                    'max_services': -1,  # unlimited
                    'max_domains': -1,
                    'support_level': 'dedicated'
                }
            )
        })
        
        # AWS Service Plans
        self.service_plans.update({
            'aws_starter': ServicePlan(
                plan_id='aws_starter',
                name='AWS Starter',
                description='Cost-effective AWS solutions for startups',
                cloud_provider='aws',
                service_type='full_stack',
                tier=TierType.STARTER,
                base_price=30.0,
                included_resources={
                    'lambda_requests': 1000000,
                    's3_storage_gb': 10,
                    'api_gateway_calls': 100000,
                    'rds_hours': 100
                },
                overage_rates={
                    'lambda_requests': 0.0000002,
                    's3_storage_gb': 0.023,
                    'api_gateway_calls': 0.0000035,
                    'rds_hours': 0.017
                },
                billing_cycle=BillingCycle.MONTHLY,
                features=[
                    'Lambda functions',
                    'S3 storage',
                    'API Gateway',
                    'RDS database',
                    'Basic support'
                ],
                limits={
                    'max_services': 5,
                    'max_regions': 2,
                    'support_level': 'basic'
                }
            ),
            'aws_professional': ServicePlan(
                plan_id='aws_professional',
                name='AWS Professional',
                description='Advanced AWS services for growing companies',
                cloud_provider='aws',
                service_type='full_stack',
                tier=TierType.PROFESSIONAL,
                base_price=120.0,
                included_resources={
                    'lambda_requests': 10000000,
                    's3_storage_gb': 100,
                    'api_gateway_calls': 1000000,
                    'rds_hours': 500,
                    'ecs_hours': 200,
                    'bedrock_tokens': 100000
                },
                overage_rates={
                    'lambda_requests': 0.00000015,
                    's3_storage_gb': 0.02,
                    'api_gateway_calls': 0.000003,
                    'rds_hours': 0.015,
                    'ecs_hours': 0.04,
                    'bedrock_tokens': 0.0008
                },
                billing_cycle=BillingCycle.MONTHLY,
                features=[
                    'All Starter features',
                    'ECS containers',
                    'Amazon Bedrock AI',
                    'Advanced monitoring',
                    'Developer support'
                ],
                limits={
                    'max_services': 25,
                    'max_regions': 5,
                    'support_level': 'developer'
                }
            )
        })
        
        # Azure Service Plans
        self.service_plans.update({
            'azure_starter': ServicePlan(
                plan_id='azure_starter',
                name='Azure Starter',
                description='Microsoft Azure for small to medium applications',
                cloud_provider='azure',
                service_type='full_stack',
                tier=TierType.STARTER,
                base_price=28.0,
                included_resources={
                    'app_service_hours': 744,  # 1 month
                    'storage_gb': 10,
                    'function_executions': 1000000,
                    'cognitive_api_calls': 5000
                },
                overage_rates={
                    'app_service_hours': 0.018,
                    'storage_gb': 0.025,
                    'function_executions': 0.0000002,
                    'cognitive_api_calls': 0.001
                },
                billing_cycle=BillingCycle.MONTHLY,
                features=[
                    'App Service hosting',
                    'Azure Storage',
                    'Azure Functions',
                    'Cognitive Services',
                    'Community support'
                ],
                limits={
                    'max_services': 5,
                    'max_regions': 2,
                    'support_level': 'community'
                }
            ),
            'azure_professional': ServicePlan(
                plan_id='azure_professional',
                name='Azure Professional',
                description='Full Azure stack for professional applications',
                cloud_provider='azure',
                service_type='full_stack',
                tier=TierType.PROFESSIONAL,
                base_price=110.0,
                included_resources={
                    'app_service_hours': 2000,
                    'storage_gb': 100,
                    'function_executions': 10000000,
                    'cognitive_api_calls': 50000,
                    'sql_database_hours': 744,
                    'container_hours': 200
                },
                overage_rates={
                    'app_service_hours': 0.015,
                    'storage_gb': 0.02,
                    'function_executions': 0.00000015,
                    'cognitive_api_calls': 0.0008,
                    'sql_database_hours': 0.12,
                    'container_hours': 0.04
                },
                billing_cycle=BillingCycle.MONTHLY,
                features=[
                    'All Starter features',
                    'Azure SQL Database',
                    'Container Instances',
                    'Advanced AI services',
                    'Professional support'
                ],
                limits={
                    'max_services': 20,
                    'max_regions': 5,
                    'support_level': 'professional'
                }
            )
        })
    
    async def create_subscription(self, customer_id: str, plan_id: str, 
                                  payment_method_id: str, **kwargs) -> CustomerSubscription:
        """Create a new subscription for a customer"""
        try:
            if plan_id not in self.service_plans:
                raise ValueError(f"Invalid plan ID: {plan_id}")
            
            plan = self.service_plans[plan_id]
            subscription_id = str(uuid.uuid4())
            
            # Create Stripe subscription
            stripe_subscription = await self._create_stripe_subscription(
                customer_id, plan, payment_method_id
            )
            
            subscription = CustomerSubscription(
                subscription_id=subscription_id,
                customer_id=customer_id,
                plan_id=plan_id,
                status=SubscriptionStatus.ACTIVE,
                start_date=datetime.now(),
                end_date=None,
                billing_cycle=plan.billing_cycle,
                monthly_cost=plan.base_price,
                usage_data={},
                addons=kwargs.get('addons', []),
                custom_pricing=kwargs.get('custom_pricing'),
                auto_renew=kwargs.get('auto_renew', True),
                payment_method_id=payment_method_id,
                tags=kwargs.get('tags', {})
            )
            
            self.subscriptions[subscription_id] = subscription
            
            # Initialize usage tracking
            self.usage_records[subscription_id] = []
            
            logger.info(f"Created subscription {subscription_id} for customer {customer_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise Exception(f"Failed to create subscription: {str(e)}")
    
    async def record_usage(self, subscription_id: str, service_type: str, 
                          metric_name: str, quantity: float, unit: str = "count",
                          metadata: Dict[str, Any] = None) -> UsageRecord:
        """Record usage for billing calculation"""
        try:
            if subscription_id not in self.subscriptions:
                raise ValueError(f"Subscription not found: {subscription_id}")
            
            subscription = self.subscriptions[subscription_id]
            plan = self.service_plans[subscription.plan_id]
            
            # Calculate cost based on plan
            cost = self._calculate_usage_cost(plan, metric_name, quantity)
            
            usage_record = UsageRecord(
                record_id=str(uuid.uuid4()),
                customer_id=subscription.customer_id,
                subscription_id=subscription_id,
                service_type=service_type,
                metric_name=metric_name,
                quantity=quantity,
                unit=unit,
                timestamp=datetime.now(),
                cost=cost,
                metadata=metadata or {}
            )
            
            # Store usage record
            if subscription_id not in self.usage_records:
                self.usage_records[subscription_id] = []
            self.usage_records[subscription_id].append(usage_record)
            
            # Update subscription usage data
            if metric_name not in subscription.usage_data:
                subscription.usage_data[metric_name] = 0
            subscription.usage_data[metric_name] += quantity
            
            logger.info(f"Recorded usage: {metric_name}={quantity} for subscription {subscription_id}")
            return usage_record
            
        except Exception as e:
            logger.error(f"Error recording usage: {str(e)}")
            raise Exception(f"Failed to record usage: {str(e)}")
    
    async def generate_invoice(self, customer_id: str, billing_period_start: datetime,
                              billing_period_end: datetime) -> Invoice:
        """Generate invoice for customer's subscriptions"""
        try:
            # Get all active subscriptions for customer
            customer_subscriptions = [
                sub for sub in self.subscriptions.values()
                if sub.customer_id == customer_id and sub.status == SubscriptionStatus.ACTIVE
            ]
            
            # Handle customers with no active subscriptions gracefully
            if not customer_subscriptions:
                logger.info(f"No active subscriptions found for customer {customer_id}, generating empty invoice")
            
            invoice_id = str(uuid.uuid4())
            line_items = []
            total_amount = 0.0
            
            for subscription in customer_subscriptions:
                plan = self.service_plans[subscription.plan_id]
                
                # Add base subscription cost
                line_items.append({
                    'description': f'{plan.name} - {plan.billing_cycle.value} subscription',
                    'quantity': 1,
                    'unit_price': plan.base_price,
                    'amount': plan.base_price,
                    'subscription_id': subscription.subscription_id
                })
                total_amount += plan.base_price
                
                # Add usage overages
                usage_charges = self._calculate_usage_charges(
                    subscription, billing_period_start, billing_period_end
                )
                
                for charge in usage_charges:
                    line_items.append(charge)
                    total_amount += charge['amount']
            
            # Calculate tax
            tax_amount = total_amount * self.tax_rate
            final_total = total_amount + tax_amount
            
            invoice = Invoice(
                invoice_id=invoice_id,
                customer_id=customer_id,
                subscription_ids=[sub.subscription_id for sub in customer_subscriptions],
                amount=total_amount,
                tax_amount=tax_amount,
                total_amount=final_total,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
                due_date=billing_period_end + timedelta(days=30),
                status=PaymentStatus.PENDING,
                line_items=line_items,
                payment_attempts=[],
                created_at=datetime.now()
            )
            
            self.invoices[invoice_id] = invoice
            
            # Only attempt to charge the customer if there are subscriptions with charges
            if customer_subscriptions and total_amount > 0:
                await self._process_payment(invoice)
            else:
                logger.info(f"No payment processing needed for invoice {invoice_id} (no charges or subscriptions)")
            
            logger.info(f"Generated invoice {invoice_id} for customer {customer_id}")
            return invoice
            
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            raise Exception(f"Failed to generate invoice: {str(e)}")
    
    async def get_customer_billing_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get comprehensive billing summary for a customer"""
        try:
            # Get customer subscriptions
            customer_subscriptions = [
                sub for sub in self.subscriptions.values()
                if sub.customer_id == customer_id
            ]
            
            # Get customer invoices
            customer_invoices = [
                inv for inv in self.invoices.values()
                if inv.customer_id == customer_id
            ]
            
            # Calculate current month usage and costs
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_month_usage = {}
            current_month_cost = 0.0
            
            for subscription in customer_subscriptions:
                if subscription.status == SubscriptionStatus.ACTIVE:
                    current_month_cost += subscription.monthly_cost
                    
                    # Get usage for current month
                    if subscription.subscription_id in self.usage_records:
                        for record in self.usage_records[subscription.subscription_id]:
                            if record.timestamp >= current_month_start:
                                if record.metric_name not in current_month_usage:
                                    current_month_usage[record.metric_name] = 0
                                current_month_usage[record.metric_name] += record.quantity
            
            # Calculate total spent
            total_spent = sum(inv.total_amount for inv in customer_invoices if inv.status == PaymentStatus.COMPLETED)
            
            # Get upcoming invoices
            upcoming_invoices = [
                inv for inv in customer_invoices 
                if inv.status == PaymentStatus.PENDING and inv.due_date > datetime.now()
            ]
            
            # Generate recommendations
            recommendations = self._generate_billing_recommendations(customer_subscriptions, current_month_usage)
            
            billing_summary = {
                'customer_id': customer_id,
                'current_month_cost': current_month_cost,
                'current_month_usage': current_month_usage,
                'total_spent': total_spent,
                'active_subscriptions': len([s for s in customer_subscriptions if s.status == SubscriptionStatus.ACTIVE]),
                'upcoming_charges': sum(inv.total_amount for inv in upcoming_invoices),
                'last_payment': max([inv.created_at for inv in customer_invoices if inv.status == PaymentStatus.COMPLETED], default=None),
                'subscriptions': [asdict(sub) for sub in customer_subscriptions],
                'recent_invoices': [asdict(inv) for inv in sorted(customer_invoices, key=lambda x: x.created_at, reverse=True)[:5]],
                'usage_trends': self._calculate_usage_trends(customer_id),
                'cost_breakdown': self._get_cost_breakdown(customer_subscriptions),
                'recommendations': recommendations,
                'last_updated': datetime.now().isoformat()
            }
            
            return billing_summary
            
        except Exception as e:
            logger.error(f"Error getting billing summary: {str(e)}")
            raise Exception(f"Failed to get billing summary: {str(e)}")
    
    async def modify_subscription(self, subscription_id: str, **changes) -> CustomerSubscription:
        """Modify an existing subscription"""
        try:
            if subscription_id not in self.subscriptions:
                raise ValueError(f"Subscription not found: {subscription_id}")
            
            subscription = self.subscriptions[subscription_id]
            
            # Handle plan changes
            if 'plan_id' in changes:
                new_plan_id = changes['plan_id']
                if new_plan_id not in self.service_plans:
                    raise ValueError(f"Invalid plan ID: {new_plan_id}")
                
                new_plan = self.service_plans[new_plan_id]
                subscription.plan_id = new_plan_id
                subscription.monthly_cost = new_plan.base_price
                subscription.billing_cycle = new_plan.billing_cycle
            
            # Handle other changes
            if 'addons' in changes:
                subscription.addons = changes['addons']
            
            if 'auto_renew' in changes:
                subscription.auto_renew = changes['auto_renew']
            
            if 'status' in changes:
                subscription.status = SubscriptionStatus(changes['status'])
            
            logger.info(f"Modified subscription {subscription_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error modifying subscription: {str(e)}")
            raise Exception(f"Failed to modify subscription: {str(e)}")
    
    async def cancel_subscription(self, subscription_id: str, 
                                 immediate: bool = False) -> CustomerSubscription:
        """Cancel a subscription"""
        try:
            if subscription_id not in self.subscriptions:
                raise ValueError(f"Subscription not found: {subscription_id}")
            
            subscription = self.subscriptions[subscription_id]
            
            if immediate:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.end_date = datetime.now()
            else:
                # Cancel at end of billing period
                subscription.auto_renew = False
                if subscription.billing_cycle == BillingCycle.MONTHLY:
                    subscription.end_date = datetime.now() + timedelta(days=30)
                elif subscription.billing_cycle == BillingCycle.QUARTERLY:
                    subscription.end_date = datetime.now() + timedelta(days=90)
                else:  # ANNUAL
                    subscription.end_date = datetime.now() + timedelta(days=365)
            
            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    def _calculate_usage_cost(self, plan: ServicePlan, metric_name: str, quantity: float) -> float:
        """Calculate cost for usage based on plan limits and overage rates"""
        included_amount = plan.included_resources.get(metric_name, 0)
        overage_rate = plan.overage_rates.get(metric_name, 0)
        
        if quantity <= included_amount:
            return 0.0
        
        overage_quantity = quantity - included_amount
        return overage_quantity * overage_rate
    
    def _calculate_usage_charges(self, subscription: CustomerSubscription,
                                start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Calculate usage charges for a billing period"""
        charges = []
        plan = self.service_plans[subscription.plan_id]
        
        if subscription.subscription_id not in self.usage_records:
            return charges
        
        # Aggregate usage for the billing period
        period_usage = {}
        for record in self.usage_records[subscription.subscription_id]:
            if start_date <= record.timestamp <= end_date:
                if record.metric_name not in period_usage:
                    period_usage[record.metric_name] = 0
                period_usage[record.metric_name] += record.quantity
        
        # Calculate overage charges
        for metric_name, total_usage in period_usage.items():
            included_amount = plan.included_resources.get(metric_name, 0)
            if total_usage > included_amount:
                overage_quantity = total_usage - included_amount
                overage_rate = plan.overage_rates.get(metric_name, 0)
                overage_cost = overage_quantity * overage_rate
                
                if overage_cost > 0:
                    charges.append({
                        'description': f'{metric_name} overage ({overage_quantity} units)',
                        'quantity': overage_quantity,
                        'unit_price': overage_rate,
                        'amount': overage_cost,
                        'subscription_id': subscription.subscription_id
                    })
        
        return charges
    
    async def _create_stripe_subscription(self, customer_id: str, plan: ServicePlan,
                                         payment_method_id: str) -> Any:
        """Create Stripe subscription (simplified)"""
        try:
            # In a real implementation, you would create actual Stripe subscriptions
            # For now, we'll return a mock response
            return {
                'id': f'sub_{customer_id}_{plan.plan_id}',
                'status': 'active',
                'current_period_start': datetime.now().timestamp(),
                'current_period_end': (datetime.now() + timedelta(days=30)).timestamp()
            }
        except Exception as e:
            logger.error(f"Error creating Stripe subscription: {e}")
            raise
    
    async def _process_payment(self, invoice: Invoice) -> bool:
        """Process payment for an invoice"""
        try:
            # Get customer's default payment method
            customer_subscriptions = [
                sub for sub in self.subscriptions.values()
                if sub.customer_id == invoice.customer_id and sub.status == SubscriptionStatus.ACTIVE
            ]
            
            if not customer_subscriptions:
                raise ValueError("No active subscriptions with payment methods")
            
            payment_method_id = customer_subscriptions[0].payment_method_id
            
            # Create payment attempt record
            payment_attempt = {
                'attempt_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'amount': invoice.total_amount,
                'payment_method_id': payment_method_id,
                'status': 'processing'
            }
            
            # In a real implementation, you would charge via Stripe
            # For now, we'll simulate a successful payment
            payment_attempt['status'] = 'succeeded'
            invoice.status = PaymentStatus.COMPLETED
            
            invoice.payment_attempts.append(payment_attempt)
            
            logger.info(f"Successfully processed payment for invoice {invoice.invoice_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            payment_attempt['status'] = 'failed'
            payment_attempt['error'] = str(e)
            invoice.payment_attempts.append(payment_attempt)
            invoice.status = PaymentStatus.FAILED
            return False
    
    def _generate_billing_recommendations(self, subscriptions: List[CustomerSubscription],
                                        current_usage: Dict[str, float]) -> List[str]:
        """Generate billing optimization recommendations"""
        recommendations = []
        
        # Check for unused subscriptions
        for subscription in subscriptions:
            if subscription.status == SubscriptionStatus.ACTIVE:
                plan = self.service_plans[subscription.plan_id]
                
                # Check if customer is underutilizing included resources
                underutilized = []
                for resource, included in plan.included_resources.items():
                    used = current_usage.get(resource, 0)
                    if used < included * 0.2:  # Using less than 20% of included
                        underutilized.append(resource)
                
                if len(underutilized) > 2:
                    recommendations.append(f"Consider downgrading {plan.name} plan - low usage detected")
                
                # Check for high overage costs
                high_overage = []
                for resource, used in current_usage.items():
                    included = plan.included_resources.get(resource, 0)
                    if used > included * 2:  # Using more than 2x included
                        high_overage.append(resource)
                
                if high_overage:
                    recommendations.append(f"Consider upgrading {plan.name} plan for better value on: {', '.join(high_overage)}")
        
        # Add general recommendations
        if len(subscriptions) > 3:
            recommendations.append("Consider consolidating multiple subscriptions for better pricing")
        
        return recommendations
    
    def _calculate_usage_trends(self, customer_id: str) -> Dict[str, Any]:
        """Calculate usage trends for the customer"""
        # Simplified trend calculation
        return {
            'monthly_growth': 15.5,  # percentage
            'top_growing_services': ['cloud_run_requests', 'storage_gb'],
            'cost_trend': 'increasing',
            'efficiency_score': 85
        }
    
    def _get_cost_breakdown(self, subscriptions: List[CustomerSubscription]) -> Dict[str, float]:
        """Get cost breakdown by service type"""
        breakdown = {}
        
        for subscription in subscriptions:
            if subscription.status == SubscriptionStatus.ACTIVE:
                plan = self.service_plans[subscription.plan_id]
                provider = plan.cloud_provider
                
                if provider not in breakdown:
                    breakdown[provider] = 0
                breakdown[provider] += subscription.monthly_cost
        
        return breakdown
    
    def get_available_plans(self, cloud_provider: str = None) -> List[ServicePlan]:
        """Get available service plans"""
        plans = list(self.service_plans.values())
        
        if cloud_provider:
            plans = [plan for plan in plans if plan.cloud_provider == cloud_provider]
        
        return plans
    
    def get_plan_details(self, plan_id: str) -> Optional[ServicePlan]:
        """Get details for a specific plan"""
        return self.service_plans.get(plan_id)


# Integration with FastAPI
app = FastAPI(title="Billing and Subscription Manager")

@app.get("/", response_class=HTMLResponse)
async def billing_dashboard():
    """ChatterFix Billing & Subscription Dashboard"""
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>💰 ChatterFix Billing & Subscription Manager</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {{
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
            background-attachment: fixed;
            position: relative;
            color: white;
            min-height: 100vh;
        }}
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(2px 2px at 20px 30px, #eee, transparent),
                radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.3), transparent),
                radial-gradient(1px 1px at 90px 40px, #fff, transparent),
                radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.3), transparent),
                radial-gradient(2px 2px at 160px 30px, #ddd, transparent);
            background-repeat: repeat;
            background-size: 200px 100px;
            z-index: -1;
            opacity: 0.3;
        }}
        .header {{
            background: rgba(0,0,0,0.3);
            padding: 2rem;
            text-align: center;
            border-bottom: 2px solid #4CAF50;
        }}
        .header h1 {{
            margin: 0;
            font-size: 3rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            background: linear-gradient(45deg, #4CAF50, #45a049, #2196F3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .nav-tabs {{
            display: flex;
            background: rgba(0,0,0,0.2);
            padding: 0;
            margin: 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .nav-tab {{
            flex: 1;
            padding: 1rem;
            text-align: center;
            cursor: pointer;
            background: rgba(255,255,255,0.05);
            border: none;
            color: white;
            transition: all 0.3s ease;
        }}
        .nav-tab:hover, .nav-tab.active {{
            background: rgba(76,175,80,0.3);
            border-bottom: 3px solid #4CAF50;
        }}
        .content {{
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }}
        .card h3 {{
            margin-top: 0;
            color: #4CAF50;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 0.5rem;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}
        .metric-item {{
            background: rgba(0,0,0,0.3);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
        }}
        .metric-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #4CAF50;
        }}
        .metric-label {{
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        .action-buttons {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        .action-btn {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            border: none;
            padding: 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
        }}
        .action-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.4);
        }}
        .status-badge {{
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        .status-active {{ background: #4CAF50; }}
        .status-pending {{ background: #FF9800; }}
        .status-overdue {{ background: #f44336; }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .billing-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .billing-item {{
            background: rgba(0,0,0,0.2);
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💰 ChatterFix Billing & Subscription Manager</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">Advanced billing automation for multi-cloud CMMS operations</p>
        </div>
        
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="nav-tab" onclick="showTab('subscriptions')">🔄 Subscriptions</button>
            <button class="nav-tab" onclick="showTab('billing')">💳 Billing</button>
            <button class="nav-tab" onclick="showTab('reports')">📈 Reports</button>
            <button class="nav-tab" onclick="showTab('automation')">🤖 AI Automation</button>
        </div>
        
        <div class="content">
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="dashboard-grid">
                    <div class="card">
                        <h3>💰 Revenue Metrics</h3>
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <div class="metric-number" id="total-revenue">$0</div>
                                <div class="metric-label">Total Revenue</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-number" id="monthly-recurring">$0</div>
                                <div class="metric-label">MRR</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-number" id="active-subscriptions">0</div>
                                <div class="metric-label">Active Subs</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-number" id="churn-rate">0%</div>
                                <div class="metric-label">Churn Rate</div>
                            </div>
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="refreshMetrics()">🔄 Refresh</button>
                            <button class="action-btn" onclick="generateReport()">📊 Generate Report</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🔄 Recent Subscriptions</h3>
                        <div class="billing-list" id="recent-subscriptions">
                            <div class="billing-item">
                                <strong>TechCorp Industries</strong> - Enterprise Plan
                                <span class="status-badge status-active">Active</span>
                                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">$2,500/month • 200 users</div>
                            </div>
                            <div class="billing-item">
                                <strong>Joe's Garage</strong> - Professional Plan
                                <span class="status-badge status-active">Active</span>
                                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">$400/month • 8 mechanics</div>
                            </div>
                            <div class="billing-item">
                                <strong>ABC Manufacturing</strong> - Professional Plan
                                <span class="status-badge status-pending">Pending</span>
                                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">$400/month • 50 users</div>
                            </div>
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="viewAllSubscriptions()">📋 View All</button>
                            <button class="action-btn" onclick="createSubscription()">➕ Create New</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>💳 Payment Status</h3>
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <div class="metric-number" id="pending-payments">3</div>
                                <div class="metric-label">Pending</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-number" id="overdue-payments">1</div>
                                <div class="metric-label">Overdue</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-number" id="processed-today">12</div>
                                <div class="metric-label">Processed Today</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-number" id="success-rate">98%</div>
                                <div class="metric-label">Success Rate</div>
                            </div>
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn" onclick="processPayments()">⚡ Process Pending</button>
                            <button class="action-btn" onclick="viewPaymentHistory()">📜 Payment History</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🤖 AI Billing Assistant</h3>
                        <div style="margin: 1rem 0;">
                            <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; max-height: 200px; overflow-y: auto;" id="billing-ai-messages">
                                <div style="margin: 0.5rem 0;">
                                    <span style="background: rgba(76,175,80,0.3); padding: 0.5rem; border-radius: 8px; display: inline-block;">🤖 Ready to help with billing automation, subscription management, and payment processing!</span>
                                </div>
                            </div>
                            <div style="display: flex; gap: 0.5rem;">
                                <input type="text" id="billing-ai-input" placeholder="Ask about billing, subscriptions, payments..." style="flex: 1; padding: 1rem; border-radius: 8px; border: none; background: rgba(255,255,255,0.1); color: white;">
                                <button onclick="sendBillingAIMessage()" class="action-btn">Send</button>
                            </div>
                            <div style="display: flex; gap: 0.5rem; margin-top: 1rem; flex-wrap: wrap;">
                                <button onclick="quickBillingAI('revenue')" style="background: rgba(255,255,255,0.1); border: none; padding: 0.5rem 1rem; border-radius: 15px; color: white; cursor: pointer;">💰 Revenue Analysis</button>
                                <button onclick="quickBillingAI('overdue')" style="background: rgba(255,255,255,0.1); border: none; padding: 0.5rem 1rem; border-radius: 15px; color: white; cursor: pointer;">⚠️ Overdue Payments</button>
                                <button onclick="quickBillingAI('forecast')" style="background: rgba(255,255,255,0.1); border: none; padding: 0.5rem 1rem; border-radius: 15px; color: white; cursor: pointer;">📈 Revenue Forecast</button>
                                <button onclick="quickBillingAI('automation')" style="background: rgba(255,255,255,0.1); border: none; padding: 0.5rem 1rem; border-radius: 15px; color: white; cursor: pointer;">🔄 Automate Billing</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Other tabs content would go here -->
            <div id="subscriptions" class="tab-content">
                <div class="card">
                    <h3>🔄 Subscription Management</h3>
                    <p>Subscription management interface coming soon...</p>
                </div>
            </div>
            
            <div id="billing" class="tab-content">
                <div class="card">
                    <h3>💳 Billing Management</h3>
                    <p>Billing management interface coming soon...</p>
                </div>
            </div>
            
            <div id="reports" class="tab-content">
                <div class="card">
                    <h3>📈 Financial Reports</h3>
                    <p>Financial reporting interface coming soon...</p>
                </div>
            </div>
            
            <div id="automation" class="tab-content">
                <div class="card">
                    <h3>🤖 AI Billing Automation</h3>
                    <p>AI automation configuration coming soon...</p>
                </div>
            </div>
        </div>
        
        <script>
        function showTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Load tab-specific data
            loadTabData(tabName);
        }}
        
        function loadTabData(tabName) {{
            switch(tabName) {{
                case 'overview':
                    loadOverviewData();
                    break;
                case 'subscriptions':
                    loadSubscriptionsData();
                    break;
                case 'billing':
                    loadBillingData();
                    break;
                case 'reports':
                    loadReportsData();
                    break;
                case 'automation':
                    loadAutomationData();
                    break;
            }}
        }}
        
        async function loadOverviewData() {{
            try {{
                // Mock data for now - would fetch from APIs
                document.getElementById('total-revenue').textContent = '$45,600';
                document.getElementById('monthly-recurring').textContent = '$12,400';
                document.getElementById('active-subscriptions').textContent = '23';
                document.getElementById('churn-rate').textContent = '2.1%';
                
                document.getElementById('pending-payments').textContent = '3';
                document.getElementById('overdue-payments').textContent = '1';
                document.getElementById('processed-today').textContent = '12';
                document.getElementById('success-rate').textContent = '98.5%';
                
            }} catch (error) {{
                console.error('Error loading overview data:', error);
            }}
        }}
        
        async function sendBillingAIMessage() {{
            const input = document.getElementById('billing-ai-input');
            const message = input.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('billing-ai-messages');
            
            // Add user message
            messagesDiv.innerHTML += `
                <div style="margin: 0.5rem 0; text-align: right;">
                    <span style="background: rgba(33,150,243,0.3); padding: 0.5rem; border-radius: 8px; display: inline-block;">${{message}}</span>
                </div>
            `;
            
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            try {{
                // This would integrate with the Universal AI Command Center
                const response = await fetch('http://localhost:8889/api/ai/chat', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer demo-token'
                    }},
                    body: JSON.stringify({{
                        message: message,
                        context: {{project_id: 'billing', source: 'billing_dashboard'}}
                    }})
                }});
                
                const result = await response.json();
                
                // Add AI response
                messagesDiv.innerHTML += `
                    <div style="margin: 0.5rem 0;">
                        <span style="background: rgba(76,175,80,0.3); padding: 0.5rem; border-radius: 8px; display: inline-block;">🤖 ${{result.response || result.message || 'Processing your billing request...'}}</span>
                    </div>
                `;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
            }} catch (error) {{
                messagesDiv.innerHTML += `
                    <div style="margin: 0.5rem 0;">
                        <span style="background: #f44336; padding: 0.5rem; border-radius: 8px; display: inline-block;">❌ Error: ${{error.message}}</span>
                    </div>
                `;
            }}
        }}
        
        function quickBillingAI(type) {{
            const messages = {{
                'revenue': 'Show me the revenue analysis for this month',
                'overdue': 'List all overdue payments and suggest actions',
                'forecast': 'Generate a revenue forecast for next quarter',
                'automation': 'Set up automated billing reminders for all customers'
            }};
            
            document.getElementById('billing-ai-input').value = messages[type];
            sendBillingAIMessage();
        }}
        
        // Action functions
        function refreshMetrics() {{
            loadOverviewData();
            alert('💰 Billing metrics refreshed!');
        }}
        
        function generateReport() {{
            alert('📊 Generating comprehensive billing report...');
        }}
        
        function viewAllSubscriptions() {{
            alert('📋 Opening subscription management...');
        }}
        
        function createSubscription() {{
            alert('➕ Opening new subscription wizard...');
        }}
        
        function processPayments() {{
            alert('⚡ Processing pending payments...');
        }}
        
        function viewPaymentHistory() {{
            alert('📜 Opening payment history...');
        }}
        
        // Initialize dashboard
        window.onload = function() {{
            loadOverviewData();
        }};
        
        // Allow Enter key to send messages
        document.addEventListener('DOMContentLoaded', function() {{
            const aiInput = document.getElementById('billing-ai-input');
            if (aiInput) {{
                aiInput.addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        sendBillingAIMessage();
                    }}
                }});
            }}
        }});
        </script>
    </body>
    </html>
    """)

# Initialize billing manager (in production, get from config)
billing_manager = BillingSubscriptionManager(
    stripe_api_key="sk_test_...",  # Replace with actual key
    tax_rate=0.08
)

# API Endpoints
class SubscriptionRequest(BaseModel):
    customer_id: str
    plan_id: str
    payment_method_id: str
    addons: List[str] = []
    auto_renew: bool = True
    tags: Dict[str, str] = {}

class UsageRequest(BaseModel):
    subscription_id: str
    service_type: str
    metric_name: str
    quantity: float
    unit: str = "count"
    metadata: Dict[str, Any] = {}

class InvoiceRequest(BaseModel):
    billing_period_start: str
    billing_period_end: str

@app.post("/api/subscriptions")
async def create_subscription(request: SubscriptionRequest):
    """Create a new subscription"""
    try:
        subscription = await billing_manager.create_subscription(
            customer_id=request.customer_id,
            plan_id=request.plan_id,
            payment_method_id=request.payment_method_id,
            addons=request.addons,
            auto_renew=request.auto_renew,
            tags=request.tags
        )
        return asdict(subscription)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/subscriptions")
async def get_subscriptions(customer_id: str = None):
    """Get all subscriptions or filter by customer"""
    try:
        if customer_id:
            # Filter subscriptions for specific customer
            customer_subscriptions = [
                asdict(sub) for sub in billing_manager.subscriptions.values()
                if sub.customer_id == customer_id
            ]
            return customer_subscriptions
        else:
            # Return all subscriptions
            return [asdict(sub) for sub in billing_manager.subscriptions.values()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/usage")
async def record_usage(request: UsageRequest):
    """Record usage for billing"""
    try:
        usage_record = await billing_manager.record_usage(
            subscription_id=request.subscription_id,
            service_type=request.service_type,
            metric_name=request.metric_name,
            quantity=request.quantity,
            unit=request.unit,
            metadata=request.metadata
        )
        return asdict(usage_record)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/usage")
async def get_usage_records(subscription_id: str = None, customer_id: str = None):
    """Get usage records, optionally filtered by subscription or customer"""
    try:
        if subscription_id:
            # Filter by subscription
            usage_records = [
                asdict(record) for record in billing_manager.usage_records.values()
                if record.subscription_id == subscription_id
            ]
            return usage_records
        elif customer_id:
            # Filter by customer (need to match subscription IDs first)
            customer_subscription_ids = [
                sub.subscription_id for sub in billing_manager.subscriptions.values()
                if sub.customer_id == customer_id
            ]
            usage_records = [
                asdict(record) for record in billing_manager.usage_records.values()
                if record.subscription_id in customer_subscription_ids
            ]
            return usage_records
        else:
            # Return all usage records
            return [asdict(record) for record in billing_manager.usage_records.values()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}/billing")
async def get_billing_summary(customer_id: str):
    """Get customer billing summary"""
    try:
        summary = await billing_manager.get_customer_billing_summary(customer_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/plans")
async def get_available_plans(cloud_provider: str = None):
    """Get available service plans"""
    plans = billing_manager.get_available_plans(cloud_provider)
    return [asdict(plan) for plan in plans]

@app.post("/api/invoices/generate/{customer_id}")
async def generate_invoice(customer_id: str, 
                          billing_period_start: str,
                          billing_period_end: str):
    """Generate invoice for customer"""
    try:
        start_date = datetime.fromisoformat(billing_period_start)
        end_date = datetime.fromisoformat(billing_period_end)
        
        invoice = await billing_manager.generate_invoice(
            customer_id, start_date, end_date
        )
        return asdict(invoice)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/customers/{customer_id}/invoices/generate")
async def generate_invoice_v2(customer_id: str, request: InvoiceRequest):
    """Generate invoice for customer (improved version with request body)"""
    try:
        start_date = datetime.fromisoformat(request.billing_period_start)
        end_date = datetime.fromisoformat(request.billing_period_end)
        
        invoice = await billing_manager.generate_invoice(
            customer_id, start_date, end_date
        )
        return asdict(invoice)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate invoice: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)