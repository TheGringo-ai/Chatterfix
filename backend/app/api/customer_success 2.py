"""
🎯 ChatterFix CMMS - Customer Success Analytics & Retention System
Real-time customer health monitoring with churn prediction and automated interventions

Features:
- Customer health scoring based on usage patterns and performance metrics
- Churn prediction using machine learning models
- Automated success interventions and playbooks
- ROI calculation and demonstration for enterprise clients
- Integration with Fix It Fred diagnostics for technical health monitoring
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import aioredis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    CHURN_RISK = "churn_risk"

class InterventionType(Enum):
    TECHNICAL_SUPPORT = "technical_support"
    TRAINING_PROGRAM = "training_program"
    EXECUTIVE_REVIEW = "executive_review"
    SUCCESS_COACHING = "success_coaching"
    FEATURE_DEMO = "feature_demo"

@dataclass
class CustomerMetrics:
    customer_id: str
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    feature_adoption_rate: float
    work_orders_created: int
    work_orders_completed: int
    average_resolution_time: float
    system_uptime: float
    support_tickets: int
    last_login_days: int
    training_completion_rate: float
    api_usage_count: int
    mobile_app_usage: float
    cost_savings_achieved: float
    predicted_churn_score: float

@dataclass
class CustomerHealthScore:
    customer_id: str
    overall_score: float
    status: HealthStatus
    usage_score: float
    adoption_score: float
    satisfaction_score: float
    technical_score: float
    business_value_score: float
    risk_factors: List[str]
    recommendations: List[str]
    last_updated: datetime

class CustomerSuccessAnalytics:
    """Advanced customer success analytics with ML-powered churn prediction"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'chatterfix_cmms',
            'user': 'postgres',
            'password': 'your_password'
        }
        self.redis_client = None
        self.churn_model = None
        self.scaler = StandardScaler()
        self.intervention_playbooks = self._load_intervention_playbooks()
        
    async def initialize_redis(self):
        """Initialize Redis connection for caching"""
        try:
            self.redis_client = await aioredis.from_url("redis://localhost")
            logger.info("Redis connection established for customer success analytics")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            
    def _load_intervention_playbooks(self) -> Dict[InterventionType, Dict]:
        """Load intervention playbooks for different customer health scenarios"""
        return {
            InterventionType.TECHNICAL_SUPPORT: {
                "trigger_conditions": ["low_system_uptime", "high_support_tickets"],
                "actions": [
                    "Schedule technical health check with Fix It Fred",
                    "Assign dedicated technical success manager",
                    "Provide priority support queue access",
                    "Conduct system optimization review"
                ],
                "timeline": "24-48 hours",
                "success_criteria": "95%+ uptime restored, support tickets reduced 50%"
            },
            InterventionType.TRAINING_PROGRAM: {
                "trigger_conditions": ["low_feature_adoption", "low_training_completion"],
                "actions": [
                    "Enroll in advanced user training program",
                    "Schedule 1:1 coaching sessions",
                    "Provide custom training materials",
                    "Set up user champions program"
                ],
                "timeline": "2-4 weeks",
                "success_criteria": "80%+ feature adoption, 90%+ training completion"
            },
            InterventionType.EXECUTIVE_REVIEW: {
                "trigger_conditions": ["high_churn_risk", "declining_usage"],
                "actions": [
                    "Schedule executive business review",
                    "Present ROI analysis and value realization",
                    "Discuss strategic roadmap alignment",
                    "Negotiate contract terms if needed"
                ],
                "timeline": "1-2 weeks",
                "success_criteria": "Renewed contract commitment, usage increase 25%"
            },
            InterventionType.SUCCESS_COACHING: {
                "trigger_conditions": ["moderate_health_decline", "low_business_value"],
                "actions": [
                    "Assign customer success manager",
                    "Create custom success plan",
                    "Establish weekly check-ins",
                    "Provide best practices guidance"
                ],
                "timeline": "4-6 weeks",
                "success_criteria": "Health score improvement 20%+, measurable ROI"
            },
            InterventionType.FEATURE_DEMO: {
                "trigger_conditions": ["unused_premium_features", "low_adoption"],
                "actions": [
                    "Schedule advanced feature demonstration",
                    "Provide use case examples",
                    "Set up pilot implementation",
                    "Track feature usage post-demo"
                ],
                "timeline": "1-2 weeks",
                "success_criteria": "50%+ feature adoption within 30 days"
            }
        }
    
    async def collect_customer_metrics(self, customer_id: str) -> CustomerMetrics:
        """Collect comprehensive customer metrics from multiple data sources"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Usage metrics
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT CASE WHEN login_date >= CURRENT_DATE THEN user_id END) as daily_users,
                    COUNT(DISTINCT CASE WHEN login_date >= CURRENT_DATE - INTERVAL '7 days' THEN user_id END) as weekly_users,
                    COUNT(DISTINCT CASE WHEN login_date >= CURRENT_DATE - INTERVAL '30 days' THEN user_id END) as monthly_users
                FROM user_activity 
                WHERE customer_id = %s
            """, (customer_id,))
            usage_data = cur.fetchone()
            
            # Work order metrics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_created,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as total_completed,
                    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_resolution_hours
                FROM work_orders 
                WHERE customer_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            """, (customer_id,))
            work_order_data = cur.fetchone()
            
            # System health metrics
            cur.execute("""
                SELECT AVG(uptime_percentage) as avg_uptime
                FROM system_health 
                WHERE customer_id = %s AND recorded_at >= CURRENT_DATE - INTERVAL '30 days'
            """, (customer_id,))
            health_data = cur.fetchone()
            
            # Support metrics
            cur.execute("""
                SELECT COUNT(*) as ticket_count
                FROM support_tickets 
                WHERE customer_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            """, (customer_id,))
            support_data = cur.fetchone()
            
            # Feature adoption
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT feature_name) as features_used,
                    (SELECT COUNT(*) FROM available_features WHERE customer_tier = c.tier) as total_features
                FROM feature_usage f
                JOIN customers c ON f.customer_id = c.id
                WHERE f.customer_id = %s AND f.used_at >= CURRENT_DATE - INTERVAL '30 days'
            """, (customer_id,))
            feature_data = cur.fetchone()
            
            # Training completion
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as completion_rate
                FROM training_modules 
                WHERE customer_id = %s
            """, (customer_id,))
            training_data = cur.fetchone()
            
            # Cost savings (from Fix It Fred analytics)
            cur.execute("""
                SELECT SUM(cost_savings_amount) as total_savings
                FROM maintenance_analytics 
                WHERE customer_id = %s AND recorded_at >= CURRENT_DATE - INTERVAL '30 days'
            """, (customer_id,))
            savings_data = cur.fetchone()
            
            conn.close()
            
            # Calculate derived metrics
            adoption_rate = 0.0
            if feature_data and feature_data['total_features'] > 0:
                adoption_rate = feature_data['features_used'] / feature_data['total_features']
            
            metrics = CustomerMetrics(
                customer_id=customer_id,
                daily_active_users=usage_data['daily_users'] or 0,
                weekly_active_users=usage_data['weekly_users'] or 0,
                monthly_active_users=usage_data['monthly_users'] or 0,
                feature_adoption_rate=adoption_rate,
                work_orders_created=work_order_data['total_created'] or 0,
                work_orders_completed=work_order_data['total_completed'] or 0,
                average_resolution_time=work_order_data['avg_resolution_hours'] or 0,
                system_uptime=health_data['avg_uptime'] or 0,
                support_tickets=support_data['ticket_count'] or 0,
                last_login_days=await self._get_last_login_days(customer_id),
                training_completion_rate=training_data['completion_rate'] or 0,
                api_usage_count=await self._get_api_usage(customer_id),
                mobile_app_usage=await self._get_mobile_usage(customer_id),
                cost_savings_achieved=savings_data['total_savings'] or 0,
                predicted_churn_score=0.0  # Will be calculated separately
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting customer metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to collect customer metrics")
    
    async def _get_last_login_days(self, customer_id: str) -> int:
        """Get days since last user login for customer"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT EXTRACT(DAYS FROM CURRENT_DATE - MAX(login_date)) as days_since_login
                FROM user_activity 
                WHERE customer_id = %s
            """, (customer_id,))
            
            result = cur.fetchone()
            conn.close()
            
            return int(result[0]) if result[0] else 999
            
        except Exception as e:
            logger.error(f"Error getting last login days: {e}")
            return 999
    
    async def _get_api_usage(self, customer_id: str) -> int:
        """Get API usage count for customer in last 30 days"""
        try:
            # Check Redis cache first
            if self.redis_client:
                cached = await self.redis_client.get(f"api_usage:{customer_id}")
                if cached:
                    return int(cached)
            
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT COUNT(*) 
                FROM api_requests 
                WHERE customer_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            """, (customer_id,))
            
            result = cur.fetchone()
            conn.close()
            
            count = result[0] if result else 0
            
            # Cache for 1 hour
            if self.redis_client:
                await self.redis_client.setex(f"api_usage:{customer_id}", 3600, count)
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting API usage: {e}")
            return 0
    
    async def _get_mobile_usage(self, customer_id: str) -> float:
        """Get mobile app usage percentage for customer"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN platform = 'mobile' THEN 1 END) * 100.0 / COUNT(*) as mobile_percentage
                FROM user_sessions 
                WHERE customer_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            """, (customer_id,))
            
            result = cur.fetchone()
            conn.close()
            
            return float(result[0]) if result and result[0] else 0.0
            
        except Exception as e:
            logger.error(f"Error getting mobile usage: {e}")
            return 0.0
    
    def train_churn_prediction_model(self, historical_data: pd.DataFrame):
        """Train machine learning model for churn prediction"""
        try:
            # Prepare features for churn prediction
            features = [
                'daily_active_users', 'weekly_active_users', 'feature_adoption_rate',
                'work_orders_completed', 'average_resolution_time', 'system_uptime',
                'support_tickets', 'last_login_days', 'training_completion_rate',
                'api_usage_count', 'mobile_app_usage', 'cost_savings_achieved'
            ]
            
            X = historical_data[features]
            y = historical_data['churned']  # Binary target: 0 = retained, 1 = churned
            
            # Handle missing values
            X = X.fillna(0)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest model
            self.churn_model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            )
            self.churn_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_score = self.churn_model.score(X_train_scaled, y_train)
            test_score = self.churn_model.score(X_test_scaled, y_test)
            
            logger.info(f"Churn prediction model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
            
            # Get feature importance
            feature_importance = pd.DataFrame({
                'feature': features,
                'importance': self.churn_model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info(f"Top churn prediction features: {feature_importance.head(5).to_dict('records')}")
            
        except Exception as e:
            logger.error(f"Error training churn prediction model: {e}")
    
    async def predict_churn_score(self, metrics: CustomerMetrics) -> float:
        """Predict churn probability for customer based on metrics"""
        try:
            if not self.churn_model:
                logger.warning("Churn model not trained, returning default score")
                return 0.5
            
            # Prepare features
            features = np.array([[
                metrics.daily_active_users,
                metrics.weekly_active_users,
                metrics.feature_adoption_rate,
                metrics.work_orders_completed,
                metrics.average_resolution_time,
                metrics.system_uptime,
                metrics.support_tickets,
                metrics.last_login_days,
                metrics.training_completion_rate,
                metrics.api_usage_count,
                metrics.mobile_app_usage,
                metrics.cost_savings_achieved
            ]])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict churn probability
            churn_probability = self.churn_model.predict_proba(features_scaled)[0][1]
            
            return float(churn_probability)
            
        except Exception as e:
            logger.error(f"Error predicting churn score: {e}")
            return 0.5
    
    async def calculate_health_score(self, metrics: CustomerMetrics) -> CustomerHealthScore:
        """Calculate comprehensive customer health score with risk assessment"""
        try:
            # Update churn score
            metrics.predicted_churn_score = await self.predict_churn_score(metrics)
            
            # Calculate component scores (0-100)
            usage_score = min(100, (metrics.weekly_active_users / max(1, metrics.monthly_active_users)) * 100)
            adoption_score = metrics.feature_adoption_rate * 100
            technical_score = min(100, metrics.system_uptime)
            
            # Satisfaction proxy based on support tickets and resolution time
            satisfaction_score = max(0, 100 - (metrics.support_tickets * 10) - (metrics.average_resolution_time * 2))
            
            # Business value score based on cost savings and work order completion
            completion_rate = (metrics.work_orders_completed / max(1, metrics.work_orders_created)) * 100
            business_value_score = min(100, (metrics.cost_savings_achieved / 1000) + completion_rate / 2)
            
            # Overall weighted score
            weights = {
                'usage': 0.25,
                'adoption': 0.20,
                'technical': 0.20,
                'satisfaction': 0.20,
                'business_value': 0.15
            }
            
            overall_score = (
                usage_score * weights['usage'] +
                adoption_score * weights['adoption'] +
                technical_score * weights['technical'] +
                satisfaction_score * weights['satisfaction'] +
                business_value_score * weights['business_value']
            )
            
            # Adjust for churn risk
            churn_penalty = metrics.predicted_churn_score * 30  # Up to 30 point penalty
            overall_score = max(0, overall_score - churn_penalty)
            
            # Determine status
            if overall_score >= 85 and metrics.predicted_churn_score < 0.1:
                status = HealthStatus.EXCELLENT
            elif overall_score >= 70 and metrics.predicted_churn_score < 0.3:
                status = HealthStatus.GOOD
            elif overall_score >= 50 and metrics.predicted_churn_score < 0.5:
                status = HealthStatus.WARNING
            elif metrics.predicted_churn_score >= 0.7:
                status = HealthStatus.CHURN_RISK
            else:
                status = HealthStatus.CRITICAL
            
            # Identify risk factors
            risk_factors = []
            if metrics.last_login_days > 7:
                risk_factors.append(f"No logins in {metrics.last_login_days} days")
            if metrics.feature_adoption_rate < 0.3:
                risk_factors.append("Low feature adoption rate")
            if metrics.system_uptime < 95:
                risk_factors.append("Poor system reliability")
            if metrics.support_tickets > 10:
                risk_factors.append("High support ticket volume")
            if metrics.training_completion_rate < 50:
                risk_factors.append("Low training completion")
            if metrics.predicted_churn_score > 0.5:
                risk_factors.append("High churn probability")
            
            # Generate recommendations
            recommendations = []
            if usage_score < 60:
                recommendations.append("Increase user engagement through training")
            if adoption_score < 50:
                recommendations.append("Schedule advanced feature demonstration")
            if technical_score < 90:
                recommendations.append("Conduct technical health check")
            if satisfaction_score < 70:
                recommendations.append("Assign dedicated success manager")
            if business_value_score < 60:
                recommendations.append("Review ROI and value realization")
            
            health_score = CustomerHealthScore(
                customer_id=metrics.customer_id,
                overall_score=overall_score,
                status=status,
                usage_score=usage_score,
                adoption_score=adoption_score,
                satisfaction_score=satisfaction_score,
                technical_score=technical_score,
                business_value_score=business_value_score,
                risk_factors=risk_factors,
                recommendations=recommendations,
                last_updated=datetime.now()
            )
            
            # Cache health score
            if self.redis_client:
                cache_key = f"health_score:{metrics.customer_id}"
                cache_data = {
                    'overall_score': overall_score,
                    'status': status.value,
                    'last_updated': health_score.last_updated.isoformat(),
                    'risk_factors': risk_factors,
                    'recommendations': recommendations
                }
                await self.redis_client.setex(cache_key, 3600, json.dumps(cache_data))
            
            return health_score
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            raise HTTPException(status_code=500, detail="Failed to calculate health score")
    
    async def trigger_automated_interventions(self, health_score: CustomerHealthScore) -> List[Dict]:
        """Trigger automated interventions based on customer health score"""
        interventions = []
        
        try:
            # Determine required interventions
            if health_score.status == HealthStatus.CHURN_RISK:
                interventions.append(InterventionType.EXECUTIVE_REVIEW)
                interventions.append(InterventionType.SUCCESS_COACHING)
            
            elif health_score.status == HealthStatus.CRITICAL:
                if health_score.technical_score < 80:
                    interventions.append(InterventionType.TECHNICAL_SUPPORT)
                if health_score.adoption_score < 40:
                    interventions.append(InterventionType.TRAINING_PROGRAM)
                interventions.append(InterventionType.SUCCESS_COACHING)
            
            elif health_score.status == HealthStatus.WARNING:
                if health_score.adoption_score < 50:
                    interventions.append(InterventionType.FEATURE_DEMO)
                if health_score.satisfaction_score < 60:
                    interventions.append(InterventionType.SUCCESS_COACHING)
            
            # Execute interventions
            intervention_results = []
            for intervention_type in interventions:
                result = await self._execute_intervention(health_score.customer_id, intervention_type)
                intervention_results.append(result)
            
            return intervention_results
            
        except Exception as e:
            logger.error(f"Error triggering interventions: {e}")
            return []
    
    async def _execute_intervention(self, customer_id: str, intervention_type: InterventionType) -> Dict:
        """Execute specific intervention for customer"""
        try:
            playbook = self.intervention_playbooks[intervention_type]
            
            # Create intervention record
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO customer_interventions 
                (customer_id, intervention_type, playbook_actions, timeline, success_criteria, status, created_at)
                VALUES (%s, %s, %s, %s, %s, 'initiated', %s)
                RETURNING id
            """, (
                customer_id,
                intervention_type.value,
                json.dumps(playbook['actions']),
                playbook['timeline'],
                playbook['success_criteria'],
                datetime.now()
            ))
            
            intervention_id = cur.fetchone()[0]
            conn.commit()
            conn.close()
            
            # Log intervention
            logger.info(f"Intervention {intervention_type.value} initiated for customer {customer_id}")
            
            # Send notifications (integrate with communication systems)
            await self._send_intervention_notifications(customer_id, intervention_type, intervention_id)
            
            return {
                'intervention_id': intervention_id,
                'customer_id': customer_id,
                'type': intervention_type.value,
                'actions': playbook['actions'],
                'timeline': playbook['timeline'],
                'success_criteria': playbook['success_criteria'],
                'status': 'initiated',
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing intervention: {e}")
            return {
                'error': str(e),
                'customer_id': customer_id,
                'type': intervention_type.value,
                'status': 'failed'
            }
    
    async def _send_intervention_notifications(self, customer_id: str, intervention_type: InterventionType, intervention_id: int):
        """Send notifications for intervention initiation"""
        try:
            # Get customer details
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT company_name, primary_contact_email, success_manager_email
                FROM customers 
                WHERE id = %s
            """, (customer_id,))
            
            customer = cur.fetchone()
            conn.close()
            
            if customer:
                notification_data = {
                    'customer_id': customer_id,
                    'company_name': customer['company_name'],
                    'intervention_type': intervention_type.value,
                    'intervention_id': intervention_id,
                    'primary_contact': customer['primary_contact_email'],
                    'success_manager': customer['success_manager_email'],
                    'timestamp': datetime.now().isoformat()
                }
                
                # Queue notification for processing
                if self.redis_client:
                    await self.redis_client.lpush(
                        'intervention_notifications',
                        json.dumps(notification_data)
                    )
                
                logger.info(f"Intervention notification queued for {customer['company_name']}")
            
        except Exception as e:
            logger.error(f"Error sending intervention notifications: {e}")
    
    async def calculate_customer_roi(self, customer_id: str) -> Dict:
        """Calculate ROI metrics for customer to demonstrate value"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get customer contract and costs
            cur.execute("""
                SELECT 
                    c.annual_contract_value,
                    c.implementation_cost,
                    c.go_live_date,
                    c.industry_vertical
                FROM customers c
                WHERE c.id = %s
            """, (customer_id,))
            
            customer_data = cur.fetchone()
            
            # Calculate time since implementation
            go_live_date = customer_data['go_live_date']
            days_since_implementation = (datetime.now().date() - go_live_date).days
            months_active = max(1, days_since_implementation / 30)
            
            # Get cost savings and efficiency gains
            cur.execute("""
                SELECT 
                    SUM(downtime_prevention_savings) as downtime_savings,
                    SUM(maintenance_cost_reduction) as maintenance_savings,
                    SUM(labor_efficiency_savings) as labor_savings,
                    SUM(inventory_optimization_savings) as inventory_savings
                FROM roi_calculations 
                WHERE customer_id = %s AND calculation_date >= %s
            """, (customer_id, go_live_date))
            
            savings_data = cur.fetchone()
            
            # Get productivity metrics
            cur.execute("""
                SELECT 
                    AVG(work_order_completion_time_before) as avg_time_before,
                    AVG(work_order_completion_time_after) as avg_time_after,
                    COUNT(*) as total_work_orders
                FROM productivity_metrics 
                WHERE customer_id = %s
            """, (customer_id,))
            
            productivity_data = cur.fetchone()
            
            conn.close()
            
            # Calculate total benefits
            total_downtime_savings = savings_data['downtime_savings'] or 0
            total_maintenance_savings = savings_data['maintenance_savings'] or 0
            total_labor_savings = savings_data['labor_savings'] or 0
            total_inventory_savings = savings_data['inventory_savings'] or 0
            
            total_benefits = (
                total_downtime_savings +
                total_maintenance_savings +
                total_labor_savings +
                total_inventory_savings
            )
            
            # Calculate total costs
            annual_subscription = customer_data['annual_contract_value'] or 0
            implementation_cost = customer_data['implementation_cost'] or 0
            total_cost_to_date = implementation_cost + (annual_subscription * months_active / 12)
            
            # Calculate ROI
            roi_percentage = 0
            if total_cost_to_date > 0:
                roi_percentage = ((total_benefits - total_cost_to_date) / total_cost_to_date) * 100
            
            # Calculate productivity improvements
            time_improvement = 0
            if productivity_data['avg_time_before'] and productivity_data['avg_time_after']:
                time_improvement = (
                    (productivity_data['avg_time_before'] - productivity_data['avg_time_after']) /
                    productivity_data['avg_time_before'] * 100
                )
            
            roi_metrics = {
                'customer_id': customer_id,
                'analysis_date': datetime.now().isoformat(),
                'time_period': {
                    'go_live_date': go_live_date.isoformat(),
                    'days_active': days_since_implementation,
                    'months_active': round(months_active, 1)
                },
                'financial_metrics': {
                    'total_benefits': total_benefits,
                    'total_costs': total_cost_to_date,
                    'net_benefit': total_benefits - total_cost_to_date,
                    'roi_percentage': round(roi_percentage, 1),
                    'payback_period_months': round(total_cost_to_date / (total_benefits / months_active), 1) if total_benefits > 0 else None
                },
                'benefit_breakdown': {
                    'downtime_prevention': total_downtime_savings,
                    'maintenance_cost_reduction': total_maintenance_savings,
                    'labor_efficiency': total_labor_savings,
                    'inventory_optimization': total_inventory_savings
                },
                'productivity_improvements': {
                    'work_order_time_reduction_percent': round(time_improvement, 1),
                    'total_work_orders_processed': productivity_data['total_work_orders'] or 0
                },
                'industry_benchmark': self._get_industry_benchmark_roi(customer_data['industry_vertical']),
                'recommendations': self._generate_roi_recommendations(roi_percentage, time_improvement)
            }
            
            return roi_metrics
            
        except Exception as e:
            logger.error(f"Error calculating customer ROI: {e}")
            raise HTTPException(status_code=500, detail="Failed to calculate ROI")
    
    def _get_industry_benchmark_roi(self, industry: str) -> Dict:
        """Get industry benchmark ROI data for comparison"""
        benchmarks = {
            'manufacturing': {'typical_roi': 180, 'best_in_class': 300},
            'healthcare': {'typical_roi': 220, 'best_in_class': 400},
            'energy': {'typical_roi': 250, 'best_in_class': 500},
            'logistics': {'typical_roi': 190, 'best_in_class': 350},
            'default': {'typical_roi': 200, 'best_in_class': 350}
        }
        
        return benchmarks.get(industry.lower(), benchmarks['default'])
    
    def _generate_roi_recommendations(self, roi_percentage: float, time_improvement: float) -> List[str]:
        """Generate recommendations for improving ROI"""
        recommendations = []
        
        if roi_percentage < 100:
            recommendations.append("ROI below 100% - Review feature adoption and usage optimization")
            recommendations.append("Consider advanced training program for key users")
            
        if roi_percentage < 200:
            recommendations.append("Explore additional cost-saving opportunities through predictive maintenance")
            recommendations.append("Implement advanced analytics features for better insights")
            
        if time_improvement < 20:
            recommendations.append("Work order completion times can be improved through process optimization")
            recommendations.append("Consider mobile app adoption to reduce technician response times")
            
        if not recommendations:
            recommendations.append("Excellent ROI performance - Consider expanding to additional departments")
            recommendations.append("Share success story for case study development")
            
        return recommendations

# FastAPI application for customer success endpoints
app = FastAPI(title="ChatterFix Customer Success Analytics", version="2.0.0")
analytics = CustomerSuccessAnalytics()

@app.on_event("startup")
async def startup_event():
    await analytics.initialize_redis()

@app.get("/api/customer-success/health/{customer_id}")
async def get_customer_health(customer_id: str):
    """Get comprehensive customer health score and analysis"""
    try:
        metrics = await analytics.collect_customer_metrics(customer_id)
        health_score = await analytics.calculate_health_score(metrics)
        
        return {
            'customer_id': customer_id,
            'health_score': {
                'overall_score': health_score.overall_score,
                'status': health_score.status.value,
                'component_scores': {
                    'usage': health_score.usage_score,
                    'adoption': health_score.adoption_score,
                    'satisfaction': health_score.satisfaction_score,
                    'technical': health_score.technical_score,
                    'business_value': health_score.business_value_score
                },
                'churn_risk': metrics.predicted_churn_score,
                'risk_factors': health_score.risk_factors,
                'recommendations': health_score.recommendations,
                'last_updated': health_score.last_updated.isoformat()
            },
            'raw_metrics': {
                'daily_active_users': metrics.daily_active_users,
                'weekly_active_users': metrics.weekly_active_users,
                'monthly_active_users': metrics.monthly_active_users,
                'feature_adoption_rate': metrics.feature_adoption_rate,
                'work_orders_completed': metrics.work_orders_completed,
                'system_uptime': metrics.system_uptime,
                'cost_savings_achieved': metrics.cost_savings_achieved
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting customer health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customer-success/roi/{customer_id}")
async def get_customer_roi(customer_id: str):
    """Get detailed ROI analysis for customer"""
    roi_metrics = await analytics.calculate_customer_roi(customer_id)
    return roi_metrics

@app.post("/api/customer-success/interventions/{customer_id}")
async def trigger_interventions(customer_id: str, background_tasks: BackgroundTasks):
    """Trigger automated interventions based on customer health"""
    try:
        metrics = await analytics.collect_customer_metrics(customer_id)
        health_score = await analytics.calculate_health_score(metrics)
        
        # Trigger interventions in background
        background_tasks.add_task(analytics.trigger_automated_interventions, health_score)
        
        return {
            'customer_id': customer_id,
            'health_status': health_score.status.value,
            'interventions_triggered': True,
            'message': 'Automated interventions initiated based on customer health analysis'
        }
        
    except Exception as e:
        logger.error(f"Error triggering interventions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customer-success/dashboard")
async def get_success_dashboard():
    """Get overall customer success dashboard metrics"""
    try:
        conn = psycopg2.connect(**analytics.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get overall health distribution
        cur.execute("""
            SELECT 
                COUNT(*) as total_customers,
                COUNT(CASE WHEN last_health_score >= 85 THEN 1 END) as excellent,
                COUNT(CASE WHEN last_health_score >= 70 AND last_health_score < 85 THEN 1 END) as good,
                COUNT(CASE WHEN last_health_score >= 50 AND last_health_score < 70 THEN 1 END) as warning,
                COUNT(CASE WHEN last_health_score < 50 THEN 1 END) as critical,
                AVG(last_health_score) as avg_health_score
            FROM customers 
            WHERE status = 'active'
        """)
        
        health_distribution = cur.fetchone()
        
        # Get churn risk customers
        cur.execute("""
            SELECT 
                id, company_name, last_health_score, predicted_churn_score
            FROM customers 
            WHERE predicted_churn_score > 0.5 AND status = 'active'
            ORDER BY predicted_churn_score DESC
            LIMIT 10
        """)
        
        high_risk_customers = cur.fetchall()
        
        # Get recent interventions
        cur.execute("""
            SELECT 
                ci.customer_id, c.company_name, ci.intervention_type, ci.status, ci.created_at
            FROM customer_interventions ci
            JOIN customers c ON ci.customer_id = c.id
            WHERE ci.created_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY ci.created_at DESC
            LIMIT 10
        """)
        
        recent_interventions = cur.fetchall()
        
        conn.close()
        
        return {
            'health_distribution': {
                'total_customers': health_distribution['total_customers'],
                'excellent': health_distribution['excellent'],
                'good': health_distribution['good'],
                'warning': health_distribution['warning'],
                'critical': health_distribution['critical'],
                'average_score': round(health_distribution['avg_health_score'] or 0, 1)
            },
            'high_risk_customers': [dict(customer) for customer in high_risk_customers],
            'recent_interventions': [dict(intervention) for intervention in recent_interventions],
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting success dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("🎯 ChatterFix Customer Success Analytics starting...")
    uvicorn.run(app, host="0.0.0.0", port=8008)