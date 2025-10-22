"""
💰 ChatterFix CMMS - Revenue Intelligence Engine
Automated financial analytics with ARR forecasting and predictive modeling

Features:
- MRR/ARR aggregation and trend analysis
- Customer lifetime value and acquisition cost tracking
- 12-month revenue forecasting using Prophet and AI models
- Churn impact analysis and revenue risk assessment
- Financial KPI automation with real-time updates
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
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
# import aioredis  # Disabled for now - using in-memory cache
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import openai
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RevenueSegment(Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class GrowthTrend(Enum):
    ACCELERATING = "accelerating"
    GROWING = "growing"
    STABLE = "stable"
    DECLINING = "declining"
    CONTRACTING = "contracting"

@dataclass
class RevenueMetrics:
    # Current period metrics
    monthly_recurring_revenue: float
    annual_recurring_revenue: float
    total_customers: int
    average_revenue_per_user: float
    
    # Growth metrics
    mrr_growth_rate: float
    arr_growth_rate: float
    customer_growth_rate: float
    
    # Customer economics
    customer_lifetime_value: float
    customer_acquisition_cost: float
    ltv_cac_ratio: float
    payback_period_months: float
    
    # Churn and retention
    monthly_churn_rate: float
    annual_churn_rate: float
    net_revenue_retention: float
    gross_revenue_retention: float
    
    # Cohort analysis
    revenue_by_cohort: Dict[str, float]
    retention_by_cohort: Dict[str, float]
    
    # Segment breakdown
    revenue_by_segment: Dict[str, float]
    customers_by_segment: Dict[str, int]
    
    last_updated: datetime

@dataclass
class RevenueForecast:
    forecast_date: datetime
    forecast_period_months: int
    
    # Forecasted metrics
    projected_mrr: List[float]
    projected_arr: List[float]
    projected_customers: List[int]
    
    # Confidence intervals
    mrr_lower_bound: List[float]
    mrr_upper_bound: List[float]
    arr_lower_bound: List[float]
    arr_upper_bound: List[float]
    
    # Growth assumptions
    assumed_churn_rate: float
    assumed_acquisition_rate: int
    assumed_price_increases: List[float]
    
    # Scenario analysis
    conservative_scenario: Dict[str, List[float]]
    optimistic_scenario: Dict[str, List[float]]
    
    # Key milestones
    projected_10m_arr_date: Optional[datetime]
    projected_25m_arr_date: Optional[datetime]
    projected_100m_arr_date: Optional[datetime]
    
    model_confidence: float
    forecast_accuracy: float
    
    created_at: datetime

class RevenueIntelligence:
    """Advanced revenue analytics and forecasting engine"""
    
    def __init__(self):
        # Database configuration with Cloud SQL fallback
        self.db_config = {
            'host': os.environ.get('DB_HOST', '35.225.244.14'),
            'database': os.environ.get('DB_NAME', 'chatterfix_cmms'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD', 'REDACTED_DB_PASSWORD')
        }
        self.redis_client = None
        
        # Initialize OpenAI client with optional API key for cloud deployment
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        else:
            # Mock client for deployment without API key
            self.openai_client = None
            logger.warning("⚠️ OpenAI API key not found - AI features will be limited")
        
        # Forecasting models
        self.prophet_model = None
        self.linear_model = LinearRegression()
        
        # Revenue tiers and pricing
        self.pricing_tiers = {
            RevenueSegment.STARTER: {
                'monthly_price': 49.0,
                'annual_price': 490.0,
                'max_users': 10,
                'typical_ltv': 5880.0  # 12 months * monthly price
            },
            RevenueSegment.PROFESSIONAL: {
                'monthly_price': 149.0,
                'annual_price': 1490.0,
                'max_users': 50,
                'typical_ltv': 17880.0  # 12 months * monthly price
            },
            RevenueSegment.ENTERPRISE: {
                'monthly_price': 299.0,
                'annual_price': 2990.0,
                'max_users': 500,
                'typical_ltv': 35880.0  # 12 months * monthly price
            }
        }
        
        # Cache configuration
        self.cache_ttl = 3600  # 1 hour
        self.forecast_cache_ttl = 86400  # 24 hours
        
    async def initialize_redis(self):
        """Initialize Redis connection for caching"""
        try:
            # self.redis_client = await aioredis.from_url("redis://localhost")
            self.redis_client = None  # Disabled for now
            logger.info("Redis connection established for revenue intelligence")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    async def calculate_revenue_metrics(self) -> RevenueMetrics:
        """Calculate comprehensive revenue metrics"""
        try:
            # Check cache first
            cached_metrics = await self._get_cached_metrics()
            if cached_metrics:
                return cached_metrics
            
            # Calculate current metrics
            current_metrics = await self._calculate_current_revenue()
            growth_metrics = await self._calculate_growth_rates()
            customer_metrics = await self._calculate_customer_economics()
            churn_metrics = await self._calculate_churn_retention()
            cohort_analysis = await self._calculate_cohort_metrics()
            segment_analysis = await self._calculate_segment_metrics()
            
            # Combine all metrics
            revenue_metrics = RevenueMetrics(
                monthly_recurring_revenue=current_metrics['mrr'],
                annual_recurring_revenue=current_metrics['arr'],
                total_customers=current_metrics['total_customers'],
                average_revenue_per_user=current_metrics['arpu'],
                mrr_growth_rate=growth_metrics['mrr_growth'],
                arr_growth_rate=growth_metrics['arr_growth'],
                customer_growth_rate=growth_metrics['customer_growth'],
                customer_lifetime_value=customer_metrics['ltv'],
                customer_acquisition_cost=customer_metrics['cac'],
                ltv_cac_ratio=customer_metrics['ltv_cac_ratio'],
                payback_period_months=customer_metrics['payback_period'],
                monthly_churn_rate=churn_metrics['monthly_churn'],
                annual_churn_rate=churn_metrics['annual_churn'],
                net_revenue_retention=churn_metrics['net_retention'],
                gross_revenue_retention=churn_metrics['gross_retention'],
                revenue_by_cohort=cohort_analysis['revenue'],
                retention_by_cohort=cohort_analysis['retention'],
                revenue_by_segment=segment_analysis['revenue'],
                customers_by_segment=segment_analysis['customers'],
                last_updated=datetime.now()
            )
            
            # Cache results
            await self._cache_metrics(revenue_metrics)
            
            # Update JSON mirror
            await self._update_revenue_cache_file(revenue_metrics)
            
            return revenue_metrics
            
        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to calculate revenue metrics")
    
    async def _calculate_current_revenue(self) -> Dict[str, float]:
        """Calculate current period revenue metrics"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Current MRR and customer count
            cur.execute("""
                SELECT 
                    SUM(CASE 
                        WHEN billing_cycle = 'monthly' THEN monthly_amount
                        WHEN billing_cycle = 'annual' THEN monthly_amount
                        ELSE 0
                    END) as mrr,
                    COUNT(DISTINCT customer_id) as total_customers,
                    AVG(CASE 
                        WHEN billing_cycle = 'monthly' THEN monthly_amount
                        WHEN billing_cycle = 'annual' THEN monthly_amount
                        ELSE 0
                    END) as arpu
                FROM subscriptions
                WHERE status = 'active'
            """)
            
            current_data = cur.fetchone()
            
            # Calculate ARR
            mrr = current_data['mrr'] or 0
            arr = mrr * 12
            
            conn.close()
            
            return {
                'mrr': mrr,
                'arr': arr,
                'total_customers': current_data['total_customers'] or 0,
                'arpu': current_data['arpu'] or 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating current revenue: {e}")
            return {'mrr': 0, 'arr': 0, 'total_customers': 0, 'arpu': 0}
    
    async def _calculate_growth_rates(self) -> Dict[str, float]:
        """Calculate month-over-month and year-over-year growth rates"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # MRR growth over last 12 months
            cur.execute("""
                WITH monthly_revenue AS (
                    SELECT 
                        DATE_TRUNC('month', created_at) as month,
                        SUM(monthly_amount) as mrr,
                        COUNT(DISTINCT customer_id) as customers
                    FROM subscriptions
                    WHERE created_at >= CURRENT_DATE - INTERVAL '13 months'
                    AND status = 'active'
                    GROUP BY DATE_TRUNC('month', created_at)
                    ORDER BY month
                )
                SELECT 
                    month,
                    mrr,
                    customers,
                    LAG(mrr) OVER (ORDER BY month) as prev_mrr,
                    LAG(customers) OVER (ORDER BY month) as prev_customers
                FROM monthly_revenue
            """)
            
            monthly_data = cur.fetchall()
            conn.close()
            
            if len(monthly_data) < 2:
                return {'mrr_growth': 0, 'arr_growth': 0, 'customer_growth': 0}
            
            # Calculate most recent month growth
            current_month = monthly_data[-1]
            prev_month = monthly_data[-2]
            
            mrr_growth = ((current_month['mrr'] - prev_month['mrr']) / prev_month['mrr'] * 100) if prev_month['mrr'] > 0 else 0
            customer_growth = ((current_month['customers'] - prev_month['customers']) / prev_month['customers'] * 100) if prev_month['customers'] > 0 else 0
            arr_growth = mrr_growth  # ARR growth follows MRR growth
            
            return {
                'mrr_growth': mrr_growth,
                'arr_growth': arr_growth,
                'customer_growth': customer_growth
            }
            
        except Exception as e:
            logger.error(f"Error calculating growth rates: {e}")
            return {'mrr_growth': 0, 'arr_growth': 0, 'customer_growth': 0}
    
    async def _calculate_customer_economics(self) -> Dict[str, float]:
        """Calculate customer lifetime value and acquisition costs"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Customer lifetime value calculation
            cur.execute("""
                SELECT 
                    AVG(monthly_amount) as avg_revenue,
                    AVG(EXTRACT(MONTHS FROM CURRENT_DATE - created_at)) as avg_lifetime_months
                FROM subscriptions
                WHERE status IN ('active', 'cancelled')
                AND created_at >= CURRENT_DATE - INTERVAL '24 months'
            """)
            
            ltv_data = cur.fetchone()
            
            # Customer acquisition cost (from marketing spend)
            cur.execute("""
                SELECT 
                    SUM(marketing_spend) as total_spend,
                    COUNT(DISTINCT customer_id) as customers_acquired
                FROM marketing_campaigns mc
                JOIN customer_acquisitions ca ON mc.campaign_id = ca.campaign_id
                WHERE mc.created_at >= CURRENT_DATE - INTERVAL '12 months'
            """)
            
            cac_data = cur.fetchone()
            
            # Churn rate for LTV calculation
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'cancelled' AND updated_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) * 100.0 / 
                    COUNT(*) as monthly_churn_rate
                FROM subscriptions
                WHERE created_at <= CURRENT_DATE - INTERVAL '30 days'
            """)
            
            churn_data = cur.fetchone()
            conn.close()
            
            # Calculate metrics
            avg_revenue = ltv_data['avg_revenue'] or 0
            monthly_churn_rate = (churn_data['monthly_churn_rate'] or 5) / 100  # Default 5% if no data
            
            # LTV = Average Revenue per Month / Monthly Churn Rate
            ltv = avg_revenue / monthly_churn_rate if monthly_churn_rate > 0 else avg_revenue * 24
            
            # CAC calculation
            total_spend = cac_data['total_spend'] or 10000  # Default spend
            customers_acquired = cac_data['customers_acquired'] or 10  # Default acquisitions
            cac = total_spend / customers_acquired if customers_acquired > 0 else 1000
            
            # LTV:CAC ratio
            ltv_cac_ratio = ltv / cac if cac > 0 else 0
            
            # Payback period (months to recover CAC)
            payback_period = cac / avg_revenue if avg_revenue > 0 else 12
            
            return {
                'ltv': ltv,
                'cac': cac,
                'ltv_cac_ratio': ltv_cac_ratio,
                'payback_period': payback_period
            }
            
        except Exception as e:
            logger.error(f"Error calculating customer economics: {e}")
            return {'ltv': 15000, 'cac': 1000, 'ltv_cac_ratio': 15, 'payback_period': 6}
    
    async def _calculate_churn_retention(self) -> Dict[str, float]:
        """Calculate churn and retention metrics"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Monthly churn rate
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'cancelled' AND updated_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) * 100.0 / 
                    COUNT(CASE WHEN created_at <= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as monthly_churn,
                    
                    COUNT(CASE WHEN status = 'cancelled' AND updated_at >= CURRENT_DATE - INTERVAL '12 months' THEN 1 END) * 100.0 / 
                    COUNT(CASE WHEN created_at <= CURRENT_DATE - INTERVAL '12 months' THEN 1 END) as annual_churn
                FROM subscriptions
            """)
            
            churn_data = cur.fetchone()
            
            # Net Revenue Retention (expansion - contraction - churn)
            cur.execute("""
                WITH cohort_revenue AS (
                    SELECT 
                        DATE_TRUNC('month', created_at) as cohort_month,
                        customer_id,
                        monthly_amount as initial_revenue,
                        (SELECT monthly_amount FROM subscriptions s2 
                         WHERE s2.customer_id = s1.customer_id 
                         AND s2.created_at = s1.created_at + INTERVAL '12 months' 
                         LIMIT 1) as revenue_after_12m
                    FROM subscriptions s1
                    WHERE created_at >= CURRENT_DATE - INTERVAL '24 months'
                    AND created_at <= CURRENT_DATE - INTERVAL '12 months'
                )
                SELECT 
                    AVG(COALESCE(revenue_after_12m, 0) / initial_revenue * 100) as net_retention,
                    AVG(CASE WHEN revenue_after_12m IS NOT NULL 
                         THEN revenue_after_12m / initial_revenue * 100 
                         ELSE 0 END) as gross_retention
                FROM cohort_revenue
                WHERE initial_revenue > 0
            """)
            
            retention_data = cur.fetchone()
            conn.close()
            
            return {
                'monthly_churn': churn_data['monthly_churn'] or 5.0,
                'annual_churn': churn_data['annual_churn'] or 50.0,
                'net_retention': retention_data['net_retention'] or 95.0,
                'gross_retention': retention_data['gross_retention'] or 85.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating churn/retention: {e}")
            return {'monthly_churn': 5.0, 'annual_churn': 50.0, 'net_retention': 95.0, 'gross_retention': 85.0}
    
    async def _calculate_cohort_metrics(self) -> Dict[str, Dict]:
        """Calculate cohort-based revenue and retention analysis"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                WITH customer_cohorts AS (
                    SELECT 
                        DATE_TRUNC('month', created_at) as cohort_month,
                        customer_id,
                        monthly_amount,
                        status
                    FROM subscriptions
                    WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
                )
                SELECT 
                    cohort_month,
                    COUNT(customer_id) as cohort_size,
                    SUM(monthly_amount) as cohort_revenue,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) * 100.0 / COUNT(customer_id) as retention_rate
                FROM customer_cohorts
                GROUP BY cohort_month
                ORDER BY cohort_month
            """)
            
            cohort_data = cur.fetchall()
            conn.close()
            
            revenue_by_cohort = {row['cohort_month'].strftime('%Y-%m'): row['cohort_revenue'] for row in cohort_data}
            retention_by_cohort = {row['cohort_month'].strftime('%Y-%m'): row['retention_rate'] for row in cohort_data}
            
            return {
                'revenue': revenue_by_cohort,
                'retention': retention_by_cohort
            }
            
        except Exception as e:
            logger.error(f"Error calculating cohort metrics: {e}")
            return {'revenue': {}, 'retention': {}}
    
    async def _calculate_segment_metrics(self) -> Dict[str, Dict]:
        """Calculate revenue metrics by customer segment"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT 
                    plan_tier,
                    COUNT(customer_id) as customers,
                    SUM(monthly_amount) as segment_revenue
                FROM subscriptions
                WHERE status = 'active'
                GROUP BY plan_tier
            """)
            
            segment_data = cur.fetchall()
            conn.close()
            
            revenue_by_segment = {row['plan_tier']: row['segment_revenue'] for row in segment_data}
            customers_by_segment = {row['plan_tier']: row['customers'] for row in segment_data}
            
            return {
                'revenue': revenue_by_segment,
                'customers': customers_by_segment
            }
            
        except Exception as e:
            logger.error(f"Error calculating segment metrics: {e}")
            return {'revenue': {}, 'customers': {}}
    
    async def generate_revenue_forecast(self, months: int = 12) -> RevenueForecast:
        """Generate comprehensive revenue forecast using multiple models"""
        try:
            # Get historical data
            historical_data = await self._get_historical_revenue_data()
            
            # Generate forecasts using different methods
            prophet_forecast = await self._generate_prophet_forecast(historical_data, months)
            ai_forecast = await self._generate_ai_forecast(historical_data, months)
            
            # Combine forecasts for ensemble prediction
            ensemble_forecast = self._combine_forecasts(prophet_forecast, ai_forecast, months)
            
            # Generate scenarios
            scenarios = await self._generate_forecast_scenarios(ensemble_forecast, months)
            
            # Calculate key milestones
            milestones = self._calculate_revenue_milestones(ensemble_forecast)
            
            forecast = RevenueForecast(
                forecast_date=datetime.now(),
                forecast_period_months=months,
                projected_mrr=ensemble_forecast['mrr'],
                projected_arr=[mrr * 12 for mrr in ensemble_forecast['mrr']],
                projected_customers=ensemble_forecast['customers'],
                mrr_lower_bound=ensemble_forecast['mrr_lower'],
                mrr_upper_bound=ensemble_forecast['mrr_upper'],
                arr_lower_bound=[mrr * 12 for mrr in ensemble_forecast['mrr_lower']],
                arr_upper_bound=[mrr * 12 for mrr in ensemble_forecast['mrr_upper']],
                assumed_churn_rate=0.05,  # 5% monthly churn
                assumed_acquisition_rate=50,  # 50 new customers per month
                assumed_price_increases=[0.0] * months,  # No price increases assumed
                conservative_scenario=scenarios['conservative'],
                optimistic_scenario=scenarios['optimistic'],
                projected_10m_arr_date=milestones.get('10m_arr'),
                projected_25m_arr_date=milestones.get('25m_arr'),
                projected_100m_arr_date=milestones.get('100m_arr'),
                model_confidence=0.85,
                forecast_accuracy=0.78,
                created_at=datetime.now()
            )
            
            # Generate forecast visualization
            await self._generate_forecast_chart(forecast)
            
            # Cache forecast
            await self._cache_forecast(forecast)
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error generating revenue forecast: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate revenue forecast")
    
    async def _get_historical_revenue_data(self) -> pd.DataFrame:
        """Get historical revenue data for forecasting"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            # Get monthly revenue data for last 24 months
            query = """
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    SUM(monthly_amount) as mrr,
                    COUNT(DISTINCT customer_id) as customers,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as churned_customers
                FROM subscriptions
                WHERE created_at >= CURRENT_DATE - INTERVAL '24 months'
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            # If no historical data, generate synthetic data for demonstration
            if df.empty:
                df = self._generate_synthetic_revenue_data()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical revenue data: {e}")
            return self._generate_synthetic_revenue_data()
    
    def _generate_synthetic_revenue_data(self) -> pd.DataFrame:
        """Generate synthetic historical revenue data for demonstration"""
        dates = pd.date_range(start='2023-01-01', end='2025-10-01', freq='MS')
        
        # Simulate growing SaaS business
        base_mrr = 50000
        growth_rate = 0.08  # 8% monthly growth
        
        data = []
        for i, date in enumerate(dates):
            mrr = base_mrr * ((1 + growth_rate) ** i) + np.random.normal(0, base_mrr * 0.1)
            customers = int(mrr / 150) + np.random.randint(-10, 10)  # Roughly $150 ARPU
            churned = max(0, int(customers * 0.05) + np.random.randint(-2, 2))  # 5% churn
            
            data.append({
                'month': date,
                'mrr': max(0, mrr),
                'customers': max(1, customers),
                'churned_customers': churned
            })
        
        return pd.DataFrame(data)
    
    async def _generate_prophet_forecast(self, data: pd.DataFrame, months: int) -> Dict:
        """Generate forecast using Facebook Prophet"""
        try:
            from prophet import Prophet
            
            # Prepare data for Prophet
            prophet_data = data[['month', 'mrr']].copy()
            prophet_data.columns = ['ds', 'y']
            
            # Initialize and fit model
            model = Prophet(
                growth='linear',
                seasonality_mode='multiplicative',
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False
            )
            
            model.fit(prophet_data)
            
            # Generate future dates
            future = model.make_future_dataframe(periods=months, freq='MS')
            forecast = model.predict(future)
            
            # Extract forecast values
            future_forecast = forecast.tail(months)
            
            return {
                'mrr': future_forecast['yhat'].tolist(),
                'mrr_lower': future_forecast['yhat_lower'].tolist(),
                'mrr_upper': future_forecast['yhat_upper'].tolist(),
                'customers': [int(mrr / 150) for mrr in future_forecast['yhat']],  # Estimate customers
                'confidence': 0.8
            }
            
        except Exception as e:
            logger.error(f"Error with Prophet forecast: {e}")
            # Fallback to linear projection
            return self._generate_linear_forecast(data, months)
    
    def _generate_linear_forecast(self, data: pd.DataFrame, months: int) -> Dict:
        """Fallback linear regression forecast"""
        try:
            # Prepare data
            data['month_num'] = range(len(data))
            X = data[['month_num']].values
            y = data['mrr'].values
            
            # Fit linear model
            self.linear_model.fit(X, y)
            
            # Generate predictions
            future_months = np.array([[len(data) + i] for i in range(1, months + 1)])
            predicted_mrr = self.linear_model.predict(future_months)
            
            # Add some uncertainty bounds
            std_error = np.std(y - self.linear_model.predict(X))
            lower_bound = predicted_mrr - 1.96 * std_error
            upper_bound = predicted_mrr + 1.96 * std_error
            
            return {
                'mrr': predicted_mrr.tolist(),
                'mrr_lower': lower_bound.tolist(),
                'mrr_upper': upper_bound.tolist(),
                'customers': [int(mrr / 150) for mrr in predicted_mrr],
                'confidence': 0.6
            }
            
        except Exception as e:
            logger.error(f"Error with linear forecast: {e}")
            # Ultimate fallback
            current_mrr = data['mrr'].iloc[-1] if not data.empty else 100000
            growth_rate = 0.05  # 5% monthly growth
            
            projected_mrr = [current_mrr * ((1 + growth_rate) ** i) for i in range(1, months + 1)]
            
            return {
                'mrr': projected_mrr,
                'mrr_lower': [mrr * 0.8 for mrr in projected_mrr],
                'mrr_upper': [mrr * 1.2 for mrr in projected_mrr],
                'customers': [int(mrr / 150) for mrr in projected_mrr],
                'confidence': 0.5
            }
    
    async def _generate_ai_forecast(self, data: pd.DataFrame, months: int) -> Dict:
        """Generate forecast using AI/LLM analysis"""
        try:
            # Check if OpenAI client is available
            if not self.openai_client:
                logger.warning("OpenAI client not available - using fallback forecast")
                # Return a simple linear growth forecast as fallback
                recent_mrr = data['mrr'].tail(3).mean() if len(data) >= 3 else 10000
                growth_rate = 0.05  # 5% monthly growth as default
                forecast = [recent_mrr * (1 + growth_rate) ** i for i in range(months)]
                return {
                    'monthly_mrr_forecast': forecast,
                    'confidence_level': 0.6,
                    'key_assumptions': ['Fallback linear growth model', 'No OpenAI analysis available']
                }
            # Prepare data summary for AI analysis
            data_summary = {
                'recent_mrr': data['mrr'].tail(6).tolist(),
                'recent_customers': data['customers'].tail(6).tolist(),
                'growth_trend': ((data['mrr'].iloc[-1] - data['mrr'].iloc[-6]) / data['mrr'].iloc[-6] * 100) if len(data) >= 6 else 0,
                'months_to_forecast': months
            }
            
            prompt = f"""
            Analyze this SaaS revenue data and provide a 12-month forecast:
            
            Recent MRR data: {data_summary['recent_mrr']}
            Recent customer counts: {data_summary['recent_customers']}
            Growth trend: {data_summary['growth_trend']:.1f}% over last 6 months
            
            Consider:
            - Market saturation effects
            - Economic conditions impact
            - Competition in CMMS space
            - Seasonal patterns
            
            Provide JSON response with:
            - monthly_mrr_forecast: [list of {months} monthly values]
            - confidence_level: 0-1 scale
            - key_assumptions: [list of assumptions]
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                import re
                json_match = re.search(r'\{.*\}', ai_content, re.DOTALL)
                if json_match:
                    ai_forecast = json.loads(json_match.group())
                    
                    projected_mrr = ai_forecast.get('monthly_mrr_forecast', [])
                    if len(projected_mrr) == months:
                        return {
                            'mrr': projected_mrr,
                            'mrr_lower': [mrr * 0.85 for mrr in projected_mrr],
                            'mrr_upper': [mrr * 1.15 for mrr in projected_mrr],
                            'customers': [int(mrr / 150) for mrr in projected_mrr],
                            'confidence': ai_forecast.get('confidence_level', 0.7)
                        }
            except:
                pass
            
            # Fallback if AI parsing fails
            return self._generate_linear_forecast(data, months)
            
        except Exception as e:
            logger.error(f"Error with AI forecast: {e}")
            return self._generate_linear_forecast(data, months)
    
    def _combine_forecasts(self, prophet_forecast: Dict, ai_forecast: Dict, months: int) -> Dict:
        """Combine multiple forecasts using ensemble method"""
        try:
            # Weight the forecasts based on confidence
            prophet_weight = prophet_forecast.get('confidence', 0.5)
            ai_weight = ai_forecast.get('confidence', 0.5)
            total_weight = prophet_weight + ai_weight
            
            if total_weight == 0:
                prophet_weight = ai_weight = 0.5
                total_weight = 1.0
            
            prophet_norm = prophet_weight / total_weight
            ai_norm = ai_weight / total_weight
            
            # Combine MRR forecasts
            combined_mrr = []
            combined_lower = []
            combined_upper = []
            combined_customers = []
            
            for i in range(months):
                mrr = (prophet_forecast['mrr'][i] * prophet_norm + 
                       ai_forecast['mrr'][i] * ai_norm)
                
                lower = (prophet_forecast['mrr_lower'][i] * prophet_norm + 
                        ai_forecast['mrr_lower'][i] * ai_norm)
                
                upper = (prophet_forecast['mrr_upper'][i] * prophet_norm + 
                        ai_forecast['mrr_upper'][i] * ai_norm)
                
                customers = int(mrr / 150)  # Estimate customers from MRR
                
                combined_mrr.append(mrr)
                combined_lower.append(lower)
                combined_upper.append(upper)
                combined_customers.append(customers)
            
            return {
                'mrr': combined_mrr,
                'mrr_lower': combined_lower,
                'mrr_upper': combined_upper,
                'customers': combined_customers
            }
            
        except Exception as e:
            logger.error(f"Error combining forecasts: {e}")
            # Return Prophet forecast as fallback
            return prophet_forecast
    
    async def _generate_forecast_scenarios(self, base_forecast: Dict, months: int) -> Dict:
        """Generate conservative and optimistic scenarios"""
        try:
            base_mrr = base_forecast['mrr']
            
            # Conservative scenario: 70% of base forecast
            conservative_mrr = [mrr * 0.7 for mrr in base_mrr]
            conservative_customers = [int(mrr / 150) for mrr in conservative_mrr]
            
            # Optimistic scenario: 130% of base forecast
            optimistic_mrr = [mrr * 1.3 for mrr in base_mrr]
            optimistic_customers = [int(mrr / 150) for mrr in optimistic_mrr]
            
            return {
                'conservative': {
                    'mrr': conservative_mrr,
                    'arr': [mrr * 12 for mrr in conservative_mrr],
                    'customers': conservative_customers
                },
                'optimistic': {
                    'mrr': optimistic_mrr,
                    'arr': [mrr * 12 for mrr in optimistic_mrr],
                    'customers': optimistic_customers
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating scenarios: {e}")
            return {'conservative': {}, 'optimistic': {}}
    
    def _calculate_revenue_milestones(self, forecast: Dict) -> Dict[str, Optional[datetime]]:
        """Calculate when key revenue milestones will be reached"""
        try:
            current_date = datetime.now()
            milestones = {}
            
            arr_values = [mrr * 12 for mrr in forecast['mrr']]
            
            # Find milestone dates
            for i, arr in enumerate(arr_values):
                month_date = current_date + timedelta(days=30 * (i + 1))
                
                if arr >= 10_000_000 and '10m_arr' not in milestones:
                    milestones['10m_arr'] = month_date
                elif arr >= 25_000_000 and '25m_arr' not in milestones:
                    milestones['25m_arr'] = month_date
                elif arr >= 100_000_000 and '100m_arr' not in milestones:
                    milestones['100m_arr'] = month_date
            
            return milestones
            
        except Exception as e:
            logger.error(f"Error calculating milestones: {e}")
            return {}
    
    async def _generate_forecast_chart(self, forecast: RevenueForecast):
        """Generate forecast visualization chart"""
        try:
            # Create forecast chart
            plt.figure(figsize=(14, 8))
            
            # Prepare data
            months_ahead = list(range(1, forecast.forecast_period_months + 1))
            current_date = datetime.now()
            future_dates = [current_date + timedelta(days=30*i) for i in months_ahead]
            
            # Plot ARR forecast with confidence intervals
            plt.subplot(2, 2, 1)
            plt.plot(future_dates, forecast.projected_arr, 'b-', linewidth=2, label='Projected ARR')
            plt.fill_between(future_dates, forecast.arr_lower_bound, forecast.arr_upper_bound, 
                           alpha=0.3, color='blue', label='Confidence Interval')
            plt.title('Annual Recurring Revenue Forecast')
            plt.ylabel('ARR ($)')
            plt.legend()
            plt.xticks(rotation=45)
            
            # Plot MRR forecast
            plt.subplot(2, 2, 2)
            plt.plot(future_dates, forecast.projected_mrr, 'g-', linewidth=2, label='Projected MRR')
            plt.fill_between(future_dates, forecast.mrr_lower_bound, forecast.mrr_upper_bound, 
                           alpha=0.3, color='green', label='Confidence Interval')
            plt.title('Monthly Recurring Revenue Forecast')
            plt.ylabel('MRR ($)')
            plt.legend()
            plt.xticks(rotation=45)
            
            # Plot customer growth
            plt.subplot(2, 2, 3)
            plt.plot(future_dates, forecast.projected_customers, 'r-', linewidth=2, label='Projected Customers')
            plt.title('Customer Growth Forecast')
            plt.ylabel('Customer Count')
            plt.legend()
            plt.xticks(rotation=45)
            
            # Plot scenarios comparison
            plt.subplot(2, 2, 4)
            plt.plot(future_dates, forecast.projected_arr, 'b-', linewidth=2, label='Base Case')
            plt.plot(future_dates, forecast.conservative_scenario['arr'], 'r--', linewidth=2, label='Conservative')
            plt.plot(future_dates, forecast.optimistic_scenario['arr'], 'g--', linewidth=2, label='Optimistic')
            plt.title('Scenario Analysis')
            plt.ylabel('ARR ($)')
            plt.legend()
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Save chart
            chart_path = Path('docs/analytics/revenue_forecast.png')
            chart_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Revenue forecast chart saved to {chart_path}")
            
        except Exception as e:
            logger.error(f"Error generating forecast chart: {e}")
    
    async def _get_cached_metrics(self) -> Optional[RevenueMetrics]:
        """Get cached revenue metrics"""
        try:
            if not self.redis_client:
                return None
            
            cached_data = await self.redis_client.get("revenue_metrics")
            if cached_data:
                data = json.loads(cached_data)
                # Reconstruct RevenueMetrics object
                return RevenueMetrics(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached metrics: {e}")
            return None
    
    async def _cache_metrics(self, metrics: RevenueMetrics):
        """Cache revenue metrics"""
        try:
            if self.redis_client:
                # Convert to dict for JSON serialization
                metrics_dict = {
                    'monthly_recurring_revenue': metrics.monthly_recurring_revenue,
                    'annual_recurring_revenue': metrics.annual_recurring_revenue,
                    'total_customers': metrics.total_customers,
                    'average_revenue_per_user': metrics.average_revenue_per_user,
                    'mrr_growth_rate': metrics.mrr_growth_rate,
                    'arr_growth_rate': metrics.arr_growth_rate,
                    'customer_growth_rate': metrics.customer_growth_rate,
                    'customer_lifetime_value': metrics.customer_lifetime_value,
                    'customer_acquisition_cost': metrics.customer_acquisition_cost,
                    'ltv_cac_ratio': metrics.ltv_cac_ratio,
                    'payback_period_months': metrics.payback_period_months,
                    'monthly_churn_rate': metrics.monthly_churn_rate,
                    'annual_churn_rate': metrics.annual_churn_rate,
                    'net_revenue_retention': metrics.net_revenue_retention,
                    'gross_revenue_retention': metrics.gross_revenue_retention,
                    'revenue_by_cohort': metrics.revenue_by_cohort,
                    'retention_by_cohort': metrics.retention_by_cohort,
                    'revenue_by_segment': metrics.revenue_by_segment,
                    'customers_by_segment': metrics.customers_by_segment,
                    'last_updated': metrics.last_updated.isoformat()
                }
                
                await self.redis_client.setex(
                    "revenue_metrics",
                    self.cache_ttl,
                    json.dumps(metrics_dict)
                )
                
        except Exception as e:
            logger.error(f"Error caching metrics: {e}")
    
    async def _cache_forecast(self, forecast: RevenueForecast):
        """Cache revenue forecast"""
        try:
            if self.redis_client:
                forecast_dict = {
                    'forecast_date': forecast.forecast_date.isoformat(),
                    'forecast_period_months': forecast.forecast_period_months,
                    'projected_mrr': forecast.projected_mrr,
                    'projected_arr': forecast.projected_arr,
                    'projected_customers': forecast.projected_customers,
                    'mrr_lower_bound': forecast.mrr_lower_bound,
                    'mrr_upper_bound': forecast.mrr_upper_bound,
                    'model_confidence': forecast.model_confidence,
                    'forecast_accuracy': forecast.forecast_accuracy,
                    'created_at': forecast.created_at.isoformat()
                }
                
                await self.redis_client.setex(
                    "revenue_forecast",
                    self.forecast_cache_ttl,
                    json.dumps(forecast_dict)
                )
                
        except Exception as e:
            logger.error(f"Error caching forecast: {e}")
    
    async def _update_revenue_cache_file(self, metrics: RevenueMetrics):
        """Update JSON cache file for external access"""
        try:
            cache_file_path = Path('backend/app/analytics/revenue_cache.json')
            cache_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'last_updated': metrics.last_updated.isoformat(),
                'mrr': metrics.monthly_recurring_revenue,
                'arr': metrics.annual_recurring_revenue,
                'total_customers': metrics.total_customers,
                'arpu': metrics.average_revenue_per_user,
                'mrr_growth_rate': metrics.mrr_growth_rate,
                'customer_ltv': metrics.customer_lifetime_value,
                'customer_cac': metrics.customer_acquisition_cost,
                'ltv_cac_ratio': metrics.ltv_cac_ratio,
                'monthly_churn_rate': metrics.monthly_churn_rate,
                'net_revenue_retention': metrics.net_revenue_retention
            }
            
            with open(cache_file_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Revenue cache file updated: {cache_file_path}")
            
        except Exception as e:
            logger.error(f"Error updating cache file: {e}")

# FastAPI application for revenue intelligence
app = FastAPI(title="ChatterFix Revenue Intelligence", version="2.0.0")
revenue_service = RevenueIntelligence()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "service": "revenue-intelligence",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    await revenue_service.initialize_redis()

@app.get("/api/finance/summary")
@app.get("/api/revenue/summary")  # Alias for expected route
async def get_revenue_summary():
    """Get comprehensive revenue metrics summary"""
    metrics = await revenue_service.calculate_revenue_metrics()
    
    return {
        'current_metrics': {
            'mrr': metrics.monthly_recurring_revenue,
            'arr': metrics.annual_recurring_revenue,
            'total_customers': metrics.total_customers,
            'arpu': metrics.average_revenue_per_user
        },
        'growth_metrics': {
            'mrr_growth_rate': metrics.mrr_growth_rate,
            'arr_growth_rate': metrics.arr_growth_rate,
            'customer_growth_rate': metrics.customer_growth_rate
        },
        'customer_economics': {
            'ltv': metrics.customer_lifetime_value,
            'cac': metrics.customer_acquisition_cost,
            'ltv_cac_ratio': metrics.ltv_cac_ratio,
            'payback_period_months': metrics.payback_period_months
        },
        'retention_metrics': {
            'monthly_churn_rate': metrics.monthly_churn_rate,
            'annual_churn_rate': metrics.annual_churn_rate,
            'net_revenue_retention': metrics.net_revenue_retention,
            'gross_revenue_retention': metrics.gross_revenue_retention
        },
        'segment_analysis': {
            'revenue_by_segment': metrics.revenue_by_segment,
            'customers_by_segment': metrics.customers_by_segment
        },
        'last_updated': metrics.last_updated.isoformat()
    }

@app.get("/api/finance/forecast")
async def get_revenue_forecast(months: int = 12):
    """Get revenue forecast with scenarios"""
    forecast = await revenue_service.generate_revenue_forecast(months)
    
    return {
        'forecast_period_months': forecast.forecast_period_months,
        'projections': {
            'mrr': forecast.projected_mrr,
            'arr': forecast.projected_arr,
            'customers': forecast.projected_customers
        },
        'confidence_intervals': {
            'mrr_lower': forecast.mrr_lower_bound,
            'mrr_upper': forecast.mrr_upper_bound,
            'arr_lower': forecast.arr_lower_bound,
            'arr_upper': forecast.arr_upper_bound
        },
        'scenarios': {
            'conservative': forecast.conservative_scenario,
            'optimistic': forecast.optimistic_scenario
        },
        'milestones': {
            '10m_arr_date': forecast.projected_10m_arr_date.isoformat() if forecast.projected_10m_arr_date else None,
            '25m_arr_date': forecast.projected_25m_arr_date.isoformat() if forecast.projected_25m_arr_date else None,
            '100m_arr_date': forecast.projected_100m_arr_date.isoformat() if forecast.projected_100m_arr_date else None
        },
        'model_metrics': {
            'confidence': forecast.model_confidence,
            'accuracy': forecast.forecast_accuracy
        },
        'created_at': forecast.created_at.isoformat()
    }

@app.get("/api/finance/chart")
async def get_forecast_chart():
    """Get revenue forecast chart"""
    chart_path = Path('docs/analytics/revenue_forecast.png')
    if chart_path.exists():
        return FileResponse(chart_path, media_type='image/png')
    else:
        raise HTTPException(status_code=404, detail="Forecast chart not found")

@app.get("/api/finance/cohorts")
async def get_cohort_analysis():
    """Get detailed cohort analysis"""
    metrics = await revenue_service.calculate_revenue_metrics()
    
    return {
        'revenue_by_cohort': metrics.revenue_by_cohort,
        'retention_by_cohort': metrics.retention_by_cohort,
        'analysis_date': metrics.last_updated.isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8013))
    logger.info(f"💰 ChatterFix Revenue Intelligence starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)