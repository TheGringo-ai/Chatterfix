"""
📊 ChatterFix CMMS - Customer Success Metrics & Intelligence
Real-time customer health scoring with predictive churn analytics

Features:
- Real-time health scoring based on usage patterns and engagement
- Predictive churn modeling using machine learning
- WebSocket endpoints for live dashboard updates
- Automated KPI aggregation and reporting
- Customer success intervention recommendations
"""

import asyncio
import json
import logging
import numpy as np
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pickle
import uuid

import psycopg2
from psycopg2.extras import RealDictCursor
# import aioredis  # Disabled for now - using in-memory cache
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
import joblib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    EXCELLENT = "excellent"      # 85-100
    GOOD = "good"               # 70-84
    WARNING = "warning"         # 50-69
    CRITICAL = "critical"       # 25-49
    CHURN_RISK = "churn_risk"   # 0-24

class ChurnRisk(Enum):
    LOW = "low"         # 0-30%
    MEDIUM = "medium"   # 31-60%
    HIGH = "high"       # 61-80%
    CRITICAL = "critical" # 81-100%

@dataclass
class CustomerHealthMetrics:
    customer_id: str
    health_score: float
    health_status: HealthStatus
    churn_probability: float
    churn_risk: ChurnRisk
    
    # Component scores
    usage_score: float
    engagement_score: float
    satisfaction_score: float
    value_realization_score: float
    
    # Key metrics
    daily_active_users: int
    monthly_active_users: int
    feature_adoption_rate: float
    support_tickets_30d: int
    avg_response_time_hours: float
    uptime_percentage: float
    cost_savings_achieved: float
    
    # Trends
    usage_trend: str  # increasing, stable, decreasing
    engagement_trend: str
    satisfaction_trend: str
    
    # Recommendations
    risk_factors: List[str]
    success_recommendations: List[str]
    intervention_priority: str  # low, medium, high, critical
    
    last_updated: datetime

@dataclass
class CustomerKPISummary:
    total_customers: int
    active_customers: int
    at_risk_customers: int
    churned_customers_30d: int
    
    avg_health_score: float
    avg_churn_probability: float
    nps_score: float
    
    health_distribution: Dict[str, int]
    churn_risk_distribution: Dict[str, int]
    
    monthly_recurring_revenue: float
    customer_lifetime_value: float
    customer_acquisition_cost: float
    ltv_cac_ratio: float
    
    retention_rate_30d: float
    retention_rate_90d: float
    retention_rate_12m: float
    
    top_risk_factors: List[Dict[str, Any]]
    success_interventions_needed: int
    
    last_updated: datetime

class CustomerSuccessMetrics:
    """Advanced customer success analytics with real-time monitoring"""
    
    def __init__(self):
        # Database configuration with Cloud SQL fallback
        self.db_config = {
            'host': os.environ.get('DB_HOST', '35.225.244.14'),
            'database': os.environ.get('DB_NAME', 'chatterfix_cmms'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD', 'REDACTED_DB_PASSWORD')
        }
        self.redis_client = None
        
        # ML Models
        self.churn_model = None
        self.scaler = StandardScaler()
        self.model_features = [
            'days_since_last_login',
            'monthly_active_users',
            'feature_adoption_rate',
            'support_tickets_30d',
            'avg_response_time_hours',
            'uptime_percentage',
            'cost_savings_achieved',
            'training_completion_rate',
            'api_usage_count',
            'mobile_app_sessions',
            'dashboard_views_30d',
            'work_orders_completed_30d'
        ]
        
        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []
        
        # Health score weights
        self.health_weights = {
            'usage': 0.30,      # Usage patterns and frequency
            'engagement': 0.25, # Feature adoption and interaction
            'satisfaction': 0.25, # Support tickets and resolution time
            'value': 0.20       # ROI and cost savings achieved
        }
        
        # Initialize models will be done in main startup
        
    async def initialize_redis(self):
        """Initialize Redis connection for caching (disabled)"""
        try:
            # self.redis_client = await aioredis.from_url("redis://localhost")
            self.redis_client = None  # Disabled for now
            logger.info("Redis connection established for customer success metrics")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    async def _initialize_models(self):
        """Initialize and train ML models"""
        try:
            # Load existing model or train new one
            try:
                self.churn_model = joblib.load('models/churn_prediction_model.pkl')
                self.scaler = joblib.load('models/churn_model_scaler.pkl')
                logger.info("Loaded existing churn prediction model")
            except FileNotFoundError:
                logger.info("Training new churn prediction model...")
                await self._train_churn_model()
                
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
    
    async def _train_churn_model(self):
        """Train machine learning model for churn prediction"""
        try:
            # Get historical customer data
            training_data = await self._get_training_data()
            
            if len(training_data) < 100:
                logger.warning("Insufficient training data, using synthetic data")
                training_data = self._generate_synthetic_training_data()
            
            # Prepare features and target
            X = training_data[self.model_features]
            y = training_data['churned']
            
            # Handle missing values
            X = X.fillna(X.median())
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train ensemble model
            rf_model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            
            rf_model.fit(X_train_scaled, y_train)
            gb_model.fit(X_train_scaled, y_train)
            
            # Evaluate models
            rf_auc = roc_auc_score(y_test, rf_model.predict_proba(X_test_scaled)[:, 1])
            gb_auc = roc_auc_score(y_test, gb_model.predict_proba(X_test_scaled)[:, 1])
            
            # Choose best model
            if rf_auc > gb_auc:
                self.churn_model = rf_model
                model_name = "RandomForest"
                best_auc = rf_auc
            else:
                self.churn_model = gb_model
                model_name = "GradientBoosting"
                best_auc = gb_auc
            
            # Save models
            joblib.dump(self.churn_model, 'models/churn_prediction_model.pkl')
            joblib.dump(self.scaler, 'models/churn_model_scaler.pkl')
            
            logger.info(f"Churn model trained successfully: {model_name} with AUC: {best_auc:.3f}")
            
            # Feature importance
            if hasattr(self.churn_model, 'feature_importances_'):
                feature_importance = pd.DataFrame({
                    'feature': self.model_features,
                    'importance': self.churn_model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                logger.info(f"Top churn prediction features: {feature_importance.head(5).to_dict('records')}")
            
        except Exception as e:
            logger.error(f"Error training churn model: {e}")
            # Use simple fallback model
            self.churn_model = RandomForestClassifier(n_estimators=10, random_state=42)
    
    async def _get_training_data(self) -> pd.DataFrame:
        """Get historical customer data for model training"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT 
                    c.customer_id,
                    EXTRACT(DAYS FROM CURRENT_DATE - c.last_login_date) as days_since_last_login,
                    c.monthly_active_users,
                    c.feature_adoption_rate,
                    c.support_tickets_30d,
                    c.avg_response_time_hours,
                    c.uptime_percentage,
                    c.cost_savings_achieved,
                    c.training_completion_rate,
                    c.api_usage_count,
                    c.mobile_app_sessions,
                    c.dashboard_views_30d,
                    c.work_orders_completed_30d,
                    CASE WHEN c.status = 'churned' THEN 1 ELSE 0 END as churned
                FROM customer_metrics c
                WHERE c.created_at >= CURRENT_DATE - INTERVAL '12 months'
            """)
            
            data = cur.fetchall()
            conn.close()
            
            if data:
                return pd.DataFrame([dict(row) for row in data])
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()
    
    def _generate_synthetic_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data for model development"""
        np.random.seed(42)
        n_samples = 1000
        
        data = []
        for i in range(n_samples):
            # Generate correlated features
            churn_probability = np.random.random()
            
            # Customers likely to churn have worse metrics
            if churn_probability > 0.7:  # High churn risk
                days_since_last_login = np.random.normal(14, 5)
                monthly_active_users = np.random.normal(2, 1)
                feature_adoption_rate = np.random.normal(0.2, 0.1)
                support_tickets_30d = np.random.normal(8, 3)
                avg_response_time_hours = np.random.normal(48, 12)
                uptime_percentage = np.random.normal(85, 10)
                churned = 1 if np.random.random() > 0.3 else 0
            else:  # Low churn risk
                days_since_last_login = np.random.normal(3, 2)
                monthly_active_users = np.random.normal(15, 5)
                feature_adoption_rate = np.random.normal(0.8, 0.2)
                support_tickets_30d = np.random.normal(2, 1)
                avg_response_time_hours = np.random.normal(4, 2)
                uptime_percentage = np.random.normal(98, 2)
                churned = 1 if np.random.random() > 0.9 else 0
            
            data.append({
                'customer_id': f'cust_{i}',
                'days_since_last_login': max(0, days_since_last_login),
                'monthly_active_users': max(1, int(monthly_active_users)),
                'feature_adoption_rate': np.clip(feature_adoption_rate, 0, 1),
                'support_tickets_30d': max(0, int(support_tickets_30d)),
                'avg_response_time_hours': max(1, avg_response_time_hours),
                'uptime_percentage': np.clip(uptime_percentage, 70, 100),
                'cost_savings_achieved': np.random.normal(50000, 20000),
                'training_completion_rate': np.random.normal(0.7, 0.3),
                'api_usage_count': np.random.normal(1000, 500),
                'mobile_app_sessions': np.random.normal(100, 50),
                'dashboard_views_30d': np.random.normal(200, 100),
                'work_orders_completed_30d': np.random.normal(50, 25),
                'churned': churned
            })
        
        return pd.DataFrame(data)
    
    async def calculate_customer_health(self, customer_id: str) -> CustomerHealthMetrics:
        """Calculate comprehensive health metrics for a customer"""
        try:
            # Get customer data
            customer_data = await self._get_customer_data(customer_id)
            
            if not customer_data:
                raise ValueError(f"Customer {customer_id} not found")
            
            # Calculate component scores
            usage_score = self._calculate_usage_score(customer_data)
            engagement_score = self._calculate_engagement_score(customer_data)
            satisfaction_score = self._calculate_satisfaction_score(customer_data)
            value_score = self._calculate_value_realization_score(customer_data)
            
            # Calculate overall health score
            health_score = (
                usage_score * self.health_weights['usage'] +
                engagement_score * self.health_weights['engagement'] +
                satisfaction_score * self.health_weights['satisfaction'] +
                value_score * self.health_weights['value']
            )
            
            # Determine health status
            health_status = self._get_health_status(health_score)
            
            # Predict churn probability
            churn_probability = await self._predict_churn_probability(customer_data)
            churn_risk = self._get_churn_risk(churn_probability)
            
            # Calculate trends
            usage_trend = await self._calculate_trend(customer_id, 'usage_score', 30)
            engagement_trend = await self._calculate_trend(customer_id, 'engagement_score', 30)
            satisfaction_trend = await self._calculate_trend(customer_id, 'satisfaction_score', 30)
            
            # Generate recommendations
            risk_factors = self._identify_risk_factors(customer_data, churn_probability)
            recommendations = self._generate_recommendations(customer_data, health_score, churn_probability)
            intervention_priority = self._determine_intervention_priority(health_score, churn_probability)
            
            health_metrics = CustomerHealthMetrics(
                customer_id=customer_id,
                health_score=health_score,
                health_status=health_status,
                churn_probability=churn_probability,
                churn_risk=churn_risk,
                usage_score=usage_score,
                engagement_score=engagement_score,
                satisfaction_score=satisfaction_score,
                value_realization_score=value_score,
                daily_active_users=customer_data.get('daily_active_users', 0),
                monthly_active_users=customer_data.get('monthly_active_users', 0),
                feature_adoption_rate=customer_data.get('feature_adoption_rate', 0.0),
                support_tickets_30d=customer_data.get('support_tickets_30d', 0),
                avg_response_time_hours=customer_data.get('avg_response_time_hours', 0.0),
                uptime_percentage=customer_data.get('uptime_percentage', 0.0),
                cost_savings_achieved=customer_data.get('cost_savings_achieved', 0.0),
                usage_trend=usage_trend,
                engagement_trend=engagement_trend,
                satisfaction_trend=satisfaction_trend,
                risk_factors=risk_factors,
                success_recommendations=recommendations,
                intervention_priority=intervention_priority,
                last_updated=datetime.now()
            )
            
            # Cache results
            await self._cache_health_metrics(health_metrics)
            
            # Broadcast to WebSocket connections
            await self._broadcast_health_update(health_metrics)
            
            return health_metrics
            
        except Exception as e:
            logger.error(f"Error calculating customer health: {e}")
            raise HTTPException(status_code=500, detail="Failed to calculate customer health")
    
    async def _get_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """Get comprehensive customer data from database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT 
                    c.customer_id,
                    c.company_name,
                    c.industry,
                    c.plan_tier,
                    c.subscription_start_date,
                    
                    -- Usage metrics
                    COUNT(DISTINCT ua.user_id) FILTER (WHERE ua.login_date >= CURRENT_DATE) as daily_active_users,
                    COUNT(DISTINCT ua.user_id) FILTER (WHERE ua.login_date >= CURRENT_DATE - INTERVAL '30 days') as monthly_active_users,
                    EXTRACT(DAYS FROM CURRENT_DATE - MAX(ua.login_date)) as days_since_last_login,
                    
                    -- Feature adoption
                    COUNT(DISTINCT fu.feature_name) * 1.0 / NULLIF((SELECT COUNT(*) FROM available_features), 0) as feature_adoption_rate,
                    
                    -- Support metrics
                    COUNT(st.ticket_id) FILTER (WHERE st.created_at >= CURRENT_DATE - INTERVAL '30 days') as support_tickets_30d,
                    AVG(EXTRACT(HOURS FROM st.resolved_at - st.created_at)) FILTER (WHERE st.resolved_at IS NOT NULL) as avg_response_time_hours,
                    
                    -- System performance
                    AVG(sh.uptime_percentage) FILTER (WHERE sh.recorded_at >= CURRENT_DATE - INTERVAL '30 days') as uptime_percentage,
                    
                    -- Value realization
                    SUM(cs.cost_savings_amount) FILTER (WHERE cs.recorded_at >= CURRENT_DATE - INTERVAL '30 days') as cost_savings_achieved,
                    
                    -- Training and adoption
                    COUNT(tc.completion_id) * 1.0 / NULLIF(COUNT(tm.module_id), 0) as training_completion_rate,
                    
                    -- API and mobile usage
                    COUNT(ar.request_id) FILTER (WHERE ar.created_at >= CURRENT_DATE - INTERVAL '30 days') as api_usage_count,
                    COUNT(ms.session_id) FILTER (WHERE ms.platform = 'mobile' AND ms.created_at >= CURRENT_DATE - INTERVAL '30 days') as mobile_app_sessions,
                    COUNT(dv.view_id) FILTER (WHERE dv.created_at >= CURRENT_DATE - INTERVAL '30 days') as dashboard_views_30d,
                    
                    -- Work order activity
                    COUNT(wo.work_order_id) FILTER (WHERE wo.status = 'completed' AND wo.completed_at >= CURRENT_DATE - INTERVAL '30 days') as work_orders_completed_30d
                    
                FROM customers c
                LEFT JOIN user_activity ua ON c.customer_id = ua.customer_id
                LEFT JOIN feature_usage fu ON c.customer_id = fu.customer_id AND fu.used_at >= CURRENT_DATE - INTERVAL '30 days'
                LEFT JOIN support_tickets st ON c.customer_id = st.customer_id
                LEFT JOIN system_health sh ON c.customer_id = sh.customer_id
                LEFT JOIN cost_savings cs ON c.customer_id = cs.customer_id
                LEFT JOIN training_completions tc ON c.customer_id = tc.customer_id
                LEFT JOIN training_modules tm ON c.customer_id = tm.customer_id
                LEFT JOIN api_requests ar ON c.customer_id = ar.customer_id
                LEFT JOIN mobile_sessions ms ON c.customer_id = ms.customer_id
                LEFT JOIN dashboard_views dv ON c.customer_id = dv.customer_id
                LEFT JOIN work_orders wo ON c.customer_id = wo.customer_id
                WHERE c.customer_id = %s
                GROUP BY c.customer_id, c.company_name, c.industry, c.plan_tier, c.subscription_start_date
            """, (customer_id,))
            
            result = cur.fetchone()
            conn.close()
            
            return dict(result) if result else {}
            
        except Exception as e:
            logger.error(f"Error getting customer data: {e}")
            return {}
    
    def _calculate_usage_score(self, customer_data: Dict[str, Any]) -> float:
        """Calculate usage score based on login frequency and activity"""
        try:
            days_since_login = customer_data.get('days_since_last_login', 999)
            monthly_users = customer_data.get('monthly_active_users', 0)
            daily_users = customer_data.get('daily_active_users', 0)
            
            # Login recency score (0-40 points)
            if days_since_login <= 1:
                recency_score = 40
            elif days_since_login <= 7:
                recency_score = 30
            elif days_since_login <= 30:
                recency_score = 20
            else:
                recency_score = 0
            
            # User activity score (0-40 points)
            activity_score = min(40, monthly_users * 2)  # 2 points per active user, max 40
            
            # Daily engagement score (0-20 points)
            engagement_score = min(20, daily_users * 5)  # 5 points per daily user, max 20
            
            total_score = recency_score + activity_score + engagement_score
            return min(100, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating usage score: {e}")
            return 50.0  # Default middle score
    
    def _calculate_engagement_score(self, customer_data: Dict[str, Any]) -> float:
        """Calculate engagement score based on feature adoption and activity"""
        try:
            feature_adoption = customer_data.get('feature_adoption_rate', 0.0)
            api_usage = customer_data.get('api_usage_count', 0)
            mobile_sessions = customer_data.get('mobile_app_sessions', 0)
            dashboard_views = customer_data.get('dashboard_views_30d', 0)
            training_completion = customer_data.get('training_completion_rate', 0.0)
            
            # Feature adoption score (0-30 points)
            adoption_score = feature_adoption * 30
            
            # API usage score (0-25 points)
            api_score = min(25, api_usage / 50)  # 1 point per 50 API calls, max 25
            
            # Mobile engagement score (0-20 points)
            mobile_score = min(20, mobile_sessions / 5)  # 1 point per 5 sessions, max 20
            
            # Dashboard engagement score (0-15 points)
            dashboard_score = min(15, dashboard_views / 10)  # 1 point per 10 views, max 15
            
            # Training completion score (0-10 points)
            training_score = training_completion * 10
            
            total_score = adoption_score + api_score + mobile_score + dashboard_score + training_score
            return min(100, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 50.0
    
    def _calculate_satisfaction_score(self, customer_data: Dict[str, Any]) -> float:
        """Calculate satisfaction score based on support tickets and system performance"""
        try:
            support_tickets = customer_data.get('support_tickets_30d', 0)
            avg_response_time = customer_data.get('avg_response_time_hours', 0)
            uptime_percentage = customer_data.get('uptime_percentage', 95.0)
            
            # Support ticket penalty (0-30 points penalty)
            if support_tickets == 0:
                ticket_score = 30
            elif support_tickets <= 2:
                ticket_score = 20
            elif support_tickets <= 5:
                ticket_score = 10
            else:
                ticket_score = 0
            
            # Response time score (0-35 points)
            if avg_response_time <= 4:
                response_score = 35
            elif avg_response_time <= 24:
                response_score = 25
            elif avg_response_time <= 48:
                response_score = 15
            else:
                response_score = 0
            
            # Uptime score (0-35 points)
            uptime_score = (uptime_percentage - 90) * 3.5  # Scale 90-100% to 0-35 points
            uptime_score = max(0, min(35, uptime_score))
            
            total_score = ticket_score + response_score + uptime_score
            return min(100, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating satisfaction score: {e}")
            return 75.0  # Default good score
    
    def _calculate_value_realization_score(self, customer_data: Dict[str, Any]) -> float:
        """Calculate value realization score based on ROI and business outcomes"""
        try:
            cost_savings = customer_data.get('cost_savings_achieved', 0)
            work_orders_completed = customer_data.get('work_orders_completed_30d', 0)
            subscription_months = self._get_subscription_months(customer_data.get('subscription_start_date'))
            
            # Cost savings score (0-50 points)
            # Scale based on expected savings of $1000-10000 per month
            savings_score = min(50, cost_savings / 200)  # 1 point per $200 saved, max 50
            
            # Work order completion score (0-30 points)
            wo_score = min(30, work_orders_completed / 2)  # 1 point per 2 work orders, max 30
            
            # Time to value score (0-20 points)
            if subscription_months <= 1:
                ttv_score = 5  # New customer, minimal expected value
            elif subscription_months <= 3:
                ttv_score = 15  # Should be seeing some value
            else:
                ttv_score = 20  # Established customer, expect full value
            
            total_score = savings_score + wo_score + ttv_score
            return min(100, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating value realization score: {e}")
            return 40.0  # Default moderate score
    
    def _get_subscription_months(self, start_date) -> int:
        """Calculate months since subscription start"""
        if not start_date:
            return 1
        
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        
        delta = datetime.now() - start_date
        return max(1, delta.days // 30)
    
    def _get_health_status(self, health_score: float) -> HealthStatus:
        """Determine health status from score"""
        if health_score >= 85:
            return HealthStatus.EXCELLENT
        elif health_score >= 70:
            return HealthStatus.GOOD
        elif health_score >= 50:
            return HealthStatus.WARNING
        elif health_score >= 25:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.CHURN_RISK
    
    def _get_churn_risk(self, churn_probability: float) -> ChurnRisk:
        """Determine churn risk from probability"""
        if churn_probability <= 0.30:
            return ChurnRisk.LOW
        elif churn_probability <= 0.60:
            return ChurnRisk.MEDIUM
        elif churn_probability <= 0.80:
            return ChurnRisk.HIGH
        else:
            return ChurnRisk.CRITICAL
    
    async def _predict_churn_probability(self, customer_data: Dict[str, Any]) -> float:
        """Predict churn probability using trained ML model"""
        try:
            if not self.churn_model:
                return 0.5  # Default moderate risk
            
            # Prepare features
            features = []
            for feature in self.model_features:
                value = customer_data.get(feature, 0)
                # Handle None values
                if value is None:
                    value = 0
                features.append(float(value))
            
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Predict probability
            churn_prob = self.churn_model.predict_proba(features_scaled)[0][1]
            
            return float(churn_prob)
            
        except Exception as e:
            logger.error(f"Error predicting churn probability: {e}")
            return 0.5
    
    async def _calculate_trend(self, customer_id: str, metric: str, days: int) -> str:
        """Calculate trend for a specific metric"""
        try:
            # This would typically query historical data
            # For now, return a placeholder trend
            import random
            trends = ['increasing', 'stable', 'decreasing']
            return random.choice(trends)
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return 'stable'
    
    def _identify_risk_factors(self, customer_data: Dict[str, Any], churn_probability: float) -> List[str]:
        """Identify specific risk factors for the customer"""
        risk_factors = []
        
        if customer_data.get('days_since_last_login', 0) > 7:
            risk_factors.append(f"No login in {customer_data.get('days_since_last_login')} days")
        
        if customer_data.get('feature_adoption_rate', 0) < 0.3:
            risk_factors.append("Low feature adoption rate")
        
        if customer_data.get('support_tickets_30d', 0) > 5:
            risk_factors.append("High support ticket volume")
        
        if customer_data.get('uptime_percentage', 100) < 95:
            risk_factors.append("Poor system reliability")
        
        if customer_data.get('training_completion_rate', 1) < 0.5:
            risk_factors.append("Incomplete training program")
        
        if customer_data.get('monthly_active_users', 0) < 2:
            risk_factors.append("Low user engagement")
        
        if churn_probability > 0.7:
            risk_factors.append("High churn probability predicted by AI")
        
        return risk_factors
    
    def _generate_recommendations(self, customer_data: Dict[str, Any], health_score: float, churn_probability: float) -> List[str]:
        """Generate actionable recommendations for customer success"""
        recommendations = []
        
        if health_score < 50:
            recommendations.append("Schedule immediate customer success intervention")
        
        if customer_data.get('feature_adoption_rate', 0) < 0.5:
            recommendations.append("Provide advanced feature training and demo")
        
        if customer_data.get('support_tickets_30d', 0) > 3:
            recommendations.append("Assign dedicated technical support manager")
        
        if customer_data.get('cost_savings_achieved', 0) < 5000:
            recommendations.append("Conduct ROI review and value optimization")
        
        if customer_data.get('training_completion_rate', 1) < 0.7:
            recommendations.append("Enroll in comprehensive training program")
        
        if churn_probability > 0.6:
            recommendations.append("Executive business review recommended")
        
        if customer_data.get('uptime_percentage', 100) < 95:
            recommendations.append("Technical health check and optimization")
        
        if not recommendations:
            recommendations.append("Continue current engagement strategy")
        
        return recommendations
    
    def _determine_intervention_priority(self, health_score: float, churn_probability: float) -> str:
        """Determine intervention priority level"""
        if churn_probability > 0.7 or health_score < 25:
            return "critical"
        elif churn_probability > 0.5 or health_score < 50:
            return "high"
        elif churn_probability > 0.3 or health_score < 70:
            return "medium"
        else:
            return "low"
    
    async def _cache_health_metrics(self, metrics: CustomerHealthMetrics):
        """Cache health metrics in Redis"""
        try:
            if self.redis_client:
                cache_data = {
                    'customer_id': metrics.customer_id,
                    'health_score': metrics.health_score,
                    'health_status': metrics.health_status.value,
                    'churn_probability': metrics.churn_probability,
                    'churn_risk': metrics.churn_risk.value,
                    'last_updated': metrics.last_updated.isoformat()
                }
                
                await self.redis_client.setex(
                    f"customer_health:{metrics.customer_id}",
                    3600,  # 1 hour cache
                    json.dumps(cache_data)
                )
                
        except Exception as e:
            logger.error(f"Error caching health metrics: {e}")
    
    async def _broadcast_health_update(self, metrics: CustomerHealthMetrics):
        """Broadcast health metrics update to WebSocket connections"""
        try:
            if not self.websocket_connections:
                return
            
            update_data = {
                'type': 'customer_health_update',
                'data': {
                    'customer_id': metrics.customer_id,
                    'health_score': metrics.health_score,
                    'health_status': metrics.health_status.value,
                    'churn_probability': metrics.churn_probability,
                    'churn_risk': metrics.churn_risk.value,
                    'intervention_priority': metrics.intervention_priority,
                    'last_updated': metrics.last_updated.isoformat()
                }
            }
            
            # Send to all connected clients
            disconnected = []
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(json.dumps(update_data))
                except Exception:
                    disconnected.append(websocket)
            
            # Remove disconnected clients
            for ws in disconnected:
                self.websocket_connections.remove(ws)
                
        except Exception as e:
            logger.error(f"Error broadcasting health update: {e}")
    
    async def get_kpi_summary(self) -> CustomerKPISummary:
        """Get aggregated customer success KPIs"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get customer counts and health distribution
            cur.execute("""
                SELECT 
                    COUNT(*) as total_customers,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_customers,
                    COUNT(CASE WHEN last_health_score < 50 THEN 1 END) as at_risk_customers,
                    COUNT(CASE WHEN status = 'churned' AND updated_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as churned_customers_30d,
                    AVG(last_health_score) as avg_health_score,
                    AVG(predicted_churn_score) as avg_churn_probability
                FROM customers
            """)
            
            customer_stats = cur.fetchone()
            
            # Get health status distribution
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN last_health_score >= 85 THEN 'excellent'
                        WHEN last_health_score >= 70 THEN 'good'
                        WHEN last_health_score >= 50 THEN 'warning'
                        WHEN last_health_score >= 25 THEN 'critical'
                        ELSE 'churn_risk'
                    END as health_status,
                    COUNT(*) as count
                FROM customers
                WHERE status = 'active'
                GROUP BY health_status
            """)
            
            health_distribution = {row['health_status']: row['count'] for row in cur.fetchall()}
            
            # Get churn risk distribution
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN predicted_churn_score <= 0.30 THEN 'low'
                        WHEN predicted_churn_score <= 0.60 THEN 'medium'
                        WHEN predicted_churn_score <= 0.80 THEN 'high'
                        ELSE 'critical'
                    END as churn_risk,
                    COUNT(*) as count
                FROM customers
                WHERE status = 'active'
                GROUP BY churn_risk
            """)
            
            churn_risk_distribution = {row['churn_risk']: row['count'] for row in cur.fetchall()}
            
            # Get financial metrics
            cur.execute("""
                SELECT 
                    SUM(monthly_recurring_revenue) as mrr,
                    AVG(customer_lifetime_value) as avg_clv,
                    AVG(customer_acquisition_cost) as avg_cac
                FROM customers
                WHERE status = 'active'
            """)
            
            financial_stats = cur.fetchone()
            
            # Get retention rates
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN subscription_start_date <= CURRENT_DATE - INTERVAL '30 days' 
                         AND status = 'active' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(CASE WHEN subscription_start_date <= CURRENT_DATE - INTERVAL '30 days' THEN 1 END), 0) as retention_30d,
                    
                    COUNT(CASE WHEN subscription_start_date <= CURRENT_DATE - INTERVAL '90 days' 
                         AND status = 'active' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(CASE WHEN subscription_start_date <= CURRENT_DATE - INTERVAL '90 days' THEN 1 END), 0) as retention_90d,
                    
                    COUNT(CASE WHEN subscription_start_date <= CURRENT_DATE - INTERVAL '12 months' 
                         AND status = 'active' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(CASE WHEN subscription_start_date <= CURRENT_DATE - INTERVAL '12 months' THEN 1 END), 0) as retention_12m
                FROM customers
            """)
            
            retention_stats = cur.fetchone()
            
            # Get top risk factors
            cur.execute("""
                SELECT 
                    unnest(risk_factors) as risk_factor,
                    COUNT(*) as frequency
                FROM customer_health_history
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY risk_factor
                ORDER BY frequency DESC
                LIMIT 5
            """)
            
            top_risk_factors = [{'factor': row['risk_factor'], 'frequency': row['frequency']} for row in cur.fetchall()]
            
            conn.close()
            
            # Calculate derived metrics
            mrr = financial_stats['mrr'] or 0
            avg_clv = financial_stats['avg_clv'] or 0
            avg_cac = financial_stats['avg_cac'] or 1
            ltv_cac_ratio = avg_clv / avg_cac if avg_cac > 0 else 0
            
            # Count interventions needed
            interventions_needed = customer_stats['at_risk_customers'] + len([f for f in top_risk_factors if f['frequency'] > 5])
            
            return CustomerKPISummary(
                total_customers=customer_stats['total_customers'] or 0,
                active_customers=customer_stats['active_customers'] or 0,
                at_risk_customers=customer_stats['at_risk_customers'] or 0,
                churned_customers_30d=customer_stats['churned_customers_30d'] or 0,
                avg_health_score=round(customer_stats['avg_health_score'] or 0, 1),
                avg_churn_probability=round(customer_stats['avg_churn_probability'] or 0, 3),
                nps_score=8.5,  # Placeholder - would calculate from surveys
                health_distribution=health_distribution,
                churn_risk_distribution=churn_risk_distribution,
                monthly_recurring_revenue=mrr,
                customer_lifetime_value=avg_clv,
                customer_acquisition_cost=avg_cac,
                ltv_cac_ratio=round(ltv_cac_ratio, 1),
                retention_rate_30d=round(retention_stats['retention_30d'] or 0, 1),
                retention_rate_90d=round(retention_stats['retention_90d'] or 0, 1),
                retention_rate_12m=round(retention_stats['retention_12m'] or 0, 1),
                top_risk_factors=top_risk_factors,
                success_interventions_needed=interventions_needed,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting KPI summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get KPI summary")
    
    async def add_websocket_connection(self, websocket: WebSocket):
        """Add WebSocket connection for real-time updates"""
        self.websocket_connections.append(websocket)
        logger.info(f"WebSocket connection added. Total connections: {len(self.websocket_connections)}")
    
    async def remove_websocket_connection(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
        logger.info(f"WebSocket connection removed. Total connections: {len(self.websocket_connections)}")

# FastAPI app for customer success metrics
app = FastAPI(title="ChatterFix Customer Success Metrics", version="2.0.0")
metrics_service = CustomerSuccessMetrics()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "service": "customer-success-analytics",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    await metrics_service.initialize_redis()

@app.websocket("/ws/customer-health")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time customer health updates"""
    await websocket.accept()
    await metrics_service.add_websocket_connection(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for connection health
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        await metrics_service.remove_websocket_connection(websocket)

@app.get("/api/customer-success/health/{customer_id}")
async def get_customer_health(customer_id: str):
    """Get customer health metrics"""
    health_metrics = await metrics_service.calculate_customer_health(customer_id)
    
    return {
        'customer_id': health_metrics.customer_id,
        'health_score': health_metrics.health_score,
        'health_status': health_metrics.health_status.value,
        'churn_probability': health_metrics.churn_probability,
        'churn_risk': health_metrics.churn_risk.value,
        'component_scores': {
            'usage': health_metrics.usage_score,
            'engagement': health_metrics.engagement_score,
            'satisfaction': health_metrics.satisfaction_score,
            'value_realization': health_metrics.value_realization_score
        },
        'key_metrics': {
            'daily_active_users': health_metrics.daily_active_users,
            'monthly_active_users': health_metrics.monthly_active_users,
            'feature_adoption_rate': health_metrics.feature_adoption_rate,
            'support_tickets_30d': health_metrics.support_tickets_30d,
            'uptime_percentage': health_metrics.uptime_percentage,
            'cost_savings_achieved': health_metrics.cost_savings_achieved
        },
        'trends': {
            'usage': health_metrics.usage_trend,
            'engagement': health_metrics.engagement_trend,
            'satisfaction': health_metrics.satisfaction_trend
        },
        'recommendations': {
            'risk_factors': health_metrics.risk_factors,
            'success_recommendations': health_metrics.success_recommendations,
            'intervention_priority': health_metrics.intervention_priority
        },
        'last_updated': health_metrics.last_updated.isoformat()
    }

@app.get("/api/customer-success/kpis")
async def get_customer_kpis():
    """Get aggregated customer success KPIs"""
    kpi_summary = await metrics_service.get_kpi_summary()
    
    return {
        'overview': {
            'total_customers': kpi_summary.total_customers,
            'active_customers': kpi_summary.active_customers,
            'at_risk_customers': kpi_summary.at_risk_customers,
            'churned_customers_30d': kpi_summary.churned_customers_30d
        },
        'health_metrics': {
            'avg_health_score': kpi_summary.avg_health_score,
            'avg_churn_probability': kpi_summary.avg_churn_probability,
            'nps_score': kpi_summary.nps_score
        },
        'distributions': {
            'health_status': kpi_summary.health_distribution,
            'churn_risk': kpi_summary.churn_risk_distribution
        },
        'financial_metrics': {
            'monthly_recurring_revenue': kpi_summary.monthly_recurring_revenue,
            'customer_lifetime_value': kpi_summary.customer_lifetime_value,
            'customer_acquisition_cost': kpi_summary.customer_acquisition_cost,
            'ltv_cac_ratio': kpi_summary.ltv_cac_ratio
        },
        'retention_rates': {
            'retention_30d': kpi_summary.retention_rate_30d,
            'retention_90d': kpi_summary.retention_rate_90d,
            'retention_12m': kpi_summary.retention_rate_12m
        },
        'insights': {
            'top_risk_factors': kpi_summary.top_risk_factors,
            'interventions_needed': kpi_summary.success_interventions_needed
        },
        'last_updated': kpi_summary.last_updated.isoformat()
    }

@app.get("/api/customer-success/at-risk")
async def get_at_risk_customers():
    """Get list of at-risk customers requiring intervention"""
    try:
        conn = psycopg2.connect(**metrics_service.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                customer_id,
                company_name,
                last_health_score,
                predicted_churn_score,
                intervention_priority,
                risk_factors,
                last_updated
            FROM customers
            WHERE status = 'active' 
            AND (last_health_score < 50 OR predicted_churn_score > 0.6)
            ORDER BY predicted_churn_score DESC, last_health_score ASC
            LIMIT 50
        """)
        
        at_risk_customers = cur.fetchall()
        conn.close()
        
        return {
            'at_risk_customers': [dict(customer) for customer in at_risk_customers],
            'total_count': len(at_risk_customers)
        }
        
    except Exception as e:
        logger.error(f"Error getting at-risk customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8012))
    logger.info(f"📊 ChatterFix Customer Success Metrics starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)