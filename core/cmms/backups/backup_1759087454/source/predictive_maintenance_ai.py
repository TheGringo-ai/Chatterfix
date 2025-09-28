#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - AI-Powered Predictive Maintenance Engine
Uses multi-AI system to predict failures and optimize maintenance schedules
"""

import sqlite3
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import httpx
import asyncio
import logging
from dataclasses import dataclass
import math

@dataclass
class PredictionResult:
    asset_id: int
    prediction_type: str
    confidence_score: float
    predicted_failure_date: Optional[datetime]
    recommended_action: str
    urgency_level: str
    estimated_cost: float
    ai_provider: str

class PredictiveMaintenanceAI:
    """Advanced AI-powered predictive maintenance system"""
    
    def __init__(self, db_path: str = "./data/cmms_enhanced.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # AI Provider configurations (from main app)
        self.ai_providers = {
            'ollama': 'http://localhost:11434/api/chat',
            'grok': 'https://api.x.ai/v1/chat/completions',
            'openai': 'https://api.openai.com/v1/chat/completions'
        }
        
        # Predictive models configuration
        self.prediction_models = {
            'time_based': self._time_based_prediction,
            'condition_based': self._condition_based_prediction,
            'usage_based': self._usage_based_prediction,
            'ai_enhanced': self._ai_enhanced_prediction
        }
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def run_predictive_analysis(self) -> List[PredictionResult]:
        """Run comprehensive predictive maintenance analysis"""
        try:
            predictions = []
            
            # Get all active assets
            assets = self._get_active_assets()
            
            for asset in assets:
                asset_predictions = await self._analyze_asset(asset)
                predictions.extend(asset_predictions)
            
            # Store predictions in database
            self._store_predictions(predictions)
            
            # Generate automated work orders for critical predictions
            await self._generate_predictive_work_orders(predictions)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Predictive analysis failed: {str(e)}")
            return []
    
    async def _analyze_asset(self, asset: Dict[str, Any]) -> List[PredictionResult]:
        """Comprehensive asset analysis using multiple prediction methods"""
        predictions = []
        
        try:
            # 1. Time-based prediction
            time_pred = self._time_based_prediction(asset)
            if time_pred:
                predictions.append(time_pred)
            
            # 2. Condition-based prediction
            condition_pred = self._condition_based_prediction(asset)
            if condition_pred:
                predictions.append(condition_pred)
            
            # 3. Usage-based prediction
            usage_pred = self._usage_based_prediction(asset)
            if usage_pred:
                predictions.append(usage_pred)
            
            # 4. AI-enhanced prediction (using our multi-AI system)
            ai_pred = await self._ai_enhanced_prediction(asset)
            if ai_pred:
                predictions.append(ai_pred)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Asset analysis failed for {asset['id']}: {str(e)}")
            return []
    
    def _time_based_prediction(self, asset: Dict[str, Any]) -> Optional[PredictionResult]:
        """Predict maintenance needs based on time intervals"""
        try:
            last_maintenance = asset.get('last_maintenance_date')
            frequency_days = asset.get('maintenance_frequency_days', 90)
            
            if not last_maintenance:
                return None
            
            last_date = datetime.fromisoformat(last_maintenance)
            next_due = last_date + timedelta(days=frequency_days)
            days_until_due = (next_due - datetime.now()).days
            
            if days_until_due <= 7:  # Due within a week
                confidence = max(0.8, 1.0 - (days_until_due / 7))
                urgency = "High" if days_until_due <= 3 else "Medium"
                
                return PredictionResult(
                    asset_id=asset['id'],
                    prediction_type='time_based',
                    confidence_score=confidence,
                    predicted_failure_date=next_due,
                    recommended_action=f"Schedule preventive maintenance for {asset['name']}",
                    urgency_level=urgency,
                    estimated_cost=self._estimate_maintenance_cost(asset, 'preventive'),
                    ai_provider='internal_algorithm'
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Time-based prediction failed: {str(e)}")
            return None
    
    def _condition_based_prediction(self, asset: Dict[str, Any]) -> Optional[PredictionResult]:
        """Predict maintenance based on asset condition and sensor data"""
        try:
            condition_rating = asset.get('condition_rating', 5)
            ai_health_score = asset.get('ai_health_score', 1.0)
            
            # Get recent sensor readings
            sensor_data = self._get_recent_sensor_data(asset['id'])
            
            # Calculate degradation score
            degradation_score = self._calculate_degradation(asset, sensor_data)
            
            # Combine factors for overall health assessment
            overall_health = (condition_rating / 5.0) * ai_health_score * (1 - degradation_score)
            
            if overall_health < 0.3:  # Critical condition
                confidence = 1 - overall_health
                days_to_failure = max(1, int(overall_health * 30))  # 1-30 days based on health
                
                return PredictionResult(
                    asset_id=asset['id'],
                    prediction_type='condition_based',
                    confidence_score=confidence,
                    predicted_failure_date=datetime.now() + timedelta(days=days_to_failure),
                    recommended_action=f"Immediate inspection required for {asset['name']} - condition deteriorating",
                    urgency_level="Critical" if overall_health < 0.15 else "High",
                    estimated_cost=self._estimate_maintenance_cost(asset, 'corrective'),
                    ai_provider='condition_algorithm'
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Condition-based prediction failed: {str(e)}")
            return None
    
    def _usage_based_prediction(self, asset: Dict[str, Any]) -> Optional[PredictionResult]:
        """Predict maintenance based on operating hours and usage patterns"""
        try:
            operating_hours = asset.get('operating_hours', 0)
            max_hours = asset.get('max_operating_hours')
            
            if not max_hours or max_hours <= 0:
                return None
            
            usage_ratio = operating_hours / max_hours
            
            if usage_ratio > 0.85:  # Approaching maximum hours
                confidence = min(0.95, usage_ratio)
                hours_remaining = max_hours - operating_hours
                
                # Estimate days based on typical usage (8 hours/day average)
                days_remaining = max(1, int(hours_remaining / 8))
                
                return PredictionResult(
                    asset_id=asset['id'],
                    prediction_type='usage_based',
                    confidence_score=confidence,
                    predicted_failure_date=datetime.now() + timedelta(days=days_remaining),
                    recommended_action=f"Plan major overhaul for {asset['name']} - approaching maximum operating hours",
                    urgency_level="High" if usage_ratio > 0.95 else "Medium",
                    estimated_cost=self._estimate_maintenance_cost(asset, 'overhaul'),
                    ai_provider='usage_algorithm'
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Usage-based prediction failed: {str(e)}")
            return None
    
    async def _ai_enhanced_prediction(self, asset: Dict[str, Any]) -> Optional[PredictionResult]:
        """Use multi-AI system for advanced predictive analysis"""
        try:
            # Prepare asset data for AI analysis
            asset_context = self._prepare_asset_context(asset)
            
            # Query our multi-AI system for prediction
            ai_analysis = await self._query_ai_for_prediction(asset_context)
            
            if ai_analysis and ai_analysis.get('prediction_confidence', 0) > 0.5:
                return PredictionResult(
                    asset_id=asset['id'],
                    prediction_type='ai_enhanced',
                    confidence_score=ai_analysis.get('prediction_confidence', 0.5),
                    predicted_failure_date=ai_analysis.get('predicted_failure_date'),
                    recommended_action=ai_analysis.get('recommended_action', 'AI analysis suggests maintenance'),
                    urgency_level=ai_analysis.get('urgency_level', 'Medium'),
                    estimated_cost=ai_analysis.get('estimated_cost', 1000.0),
                    ai_provider=ai_analysis.get('ai_provider', 'multi_ai')
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"AI-enhanced prediction failed: {str(e)}")
            return None
    
    async def _query_ai_for_prediction(self, asset_context: str) -> Optional[Dict[str, Any]]:
        """Query our AI system for predictive maintenance insights"""
        try:
            prompt = f"""
            Analyze this asset data for predictive maintenance:
            
            {asset_context}
            
            Provide a JSON response with:
            - prediction_confidence (0.0-1.0)
            - predicted_failure_date (ISO format or null)
            - recommended_action (string)
            - urgency_level (Critical/High/Medium/Low)
            - estimated_cost (number)
            - reasoning (explanation)
            
            Consider factors like:
            - Asset age and condition
            - Maintenance history patterns
            - Industry best practices
            - Failure mode analysis
            """
            
            # Try Ollama first (local, fast)
            result = await self._query_ai_provider('ollama', prompt)
            if result:
                return self._parse_ai_prediction(result, 'ollama')
            
            # Fallback to Grok
            result = await self._query_ai_provider('grok', prompt)
            if result:
                return self._parse_ai_prediction(result, 'grok')
            
            # Fallback to OpenAI
            result = await self._query_ai_provider('openai', prompt)
            if result:
                return self._parse_ai_prediction(result, 'openai')
            
            return None
            
        except Exception as e:
            self.logger.error(f"AI query failed: {str(e)}")
            return None
    
    async def _query_ai_provider(self, provider: str, prompt: str) -> Optional[str]:
        """Query specific AI provider"""
        try:
            if provider == 'ollama':
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        'http://localhost:11434/api/chat',
                        json={
                            'model': 'llama3',
                            'messages': [{'role': 'user', 'content': prompt}],
                            'stream': False
                        },
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        return response.json()['message']['content']
            
            # Add Grok and OpenAI implementations here
            # (Would need API keys from main app)
            
            return None
            
        except Exception as e:
            self.logger.error(f"AI provider {provider} query failed: {str(e)}")
            return None
    
    def _parse_ai_prediction(self, ai_response: str, provider: str) -> Optional[Dict[str, Any]]:
        """Parse AI response into structured prediction data"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\\{.*\\}', ai_response, re.DOTALL)
            if json_match:
                prediction_data = json.loads(json_match.group())
                prediction_data['ai_provider'] = provider
                return prediction_data
            
            # Fallback: parse text response manually
            return self._parse_text_prediction(ai_response, provider)
            
        except Exception as e:
            self.logger.error(f"AI response parsing failed: {str(e)}")
            return None
    
    def _parse_text_prediction(self, text: str, provider: str) -> Dict[str, Any]:
        """Parse text-based AI response"""
        # Simple text parsing for confidence indicators
        confidence = 0.5  # Default
        urgency = "Medium"
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'urgent', 'immediate']):
            confidence = 0.8
            urgency = "High"
        elif any(word in text_lower for word in ['concerning', 'attention', 'soon']):
            confidence = 0.6
            urgency = "Medium"
        
        return {
            'prediction_confidence': confidence,
            'predicted_failure_date': None,
            'recommended_action': text[:200] + "..." if len(text) > 200 else text,
            'urgency_level': urgency,
            'estimated_cost': 1000.0,
            'ai_provider': provider,
            'reasoning': text
        }
    
    def _get_active_assets(self) -> List[Dict[str, Any]]:
        """Get all active assets for analysis"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM assets 
            WHERE status = 'Active' 
            ORDER BY criticality DESC, last_maintenance_date ASC
        """)
        
        assets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return assets
    
    def _get_recent_sensor_data(self, asset_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent sensor readings for an asset"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sensor_readings 
            WHERE asset_id = ? AND reading_timestamp >= datetime('now', '-{} days')
            ORDER BY reading_timestamp DESC
        """.format(days), (asset_id,))
        
        readings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return readings
    
    def _calculate_degradation(self, asset: Dict[str, Any], sensor_data: List[Dict[str, Any]]) -> float:
        """Calculate asset degradation score based on sensor trends"""
        if not sensor_data:
            return 0.0
        
        try:
            # Group by sensor type and calculate trends
            sensor_groups = {}
            for reading in sensor_data:
                sensor_type = reading['sensor_type']
                if sensor_type not in sensor_groups:
                    sensor_groups[sensor_type] = []
                sensor_groups[sensor_type].append(reading)
            
            degradation_scores = []
            
            for sensor_type, readings in sensor_groups.items():
                if len(readings) >= 3:  # Need at least 3 points for trend
                    values = [r['sensor_value'] for r in readings]
                    trend_score = self._calculate_trend_degradation(values, sensor_type)
                    degradation_scores.append(trend_score)
            
            return np.mean(degradation_scores) if degradation_scores else 0.0
            
        except Exception as e:
            self.logger.error(f"Degradation calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_trend_degradation(self, values: List[float], sensor_type: str) -> float:
        """Calculate degradation based on sensor value trends"""
        if len(values) < 3:
            return 0.0
        
        # Calculate trend (slope)
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        # Different sensors have different "bad" directions
        if sensor_type.lower() in ['temperature', 'pressure', 'vibration', 'noise']:
            # Higher values indicate degradation
            degradation = max(0, slope) / (max(values) - min(values) + 1)
        elif sensor_type.lower() in ['efficiency', 'performance', 'flow_rate']:
            # Lower values indicate degradation  
            degradation = max(0, -slope) / (max(values) - min(values) + 1)
        else:
            # Default: any significant change indicates degradation
            degradation = abs(slope) / (max(values) - min(values) + 1)
        
        return min(1.0, degradation)
    
    def _prepare_asset_context(self, asset: Dict[str, Any]) -> str:
        """Prepare comprehensive asset context for AI analysis"""
        # Get maintenance history
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total_work_orders,
                   AVG(actual_hours) as avg_repair_time,
                   SUM(actual_cost) as total_maintenance_cost
            FROM work_orders 
            WHERE asset_id = ? AND status = 'Completed'
        """, (asset['id'],))
        
        maintenance_stats = dict(cursor.fetchone() or {})
        conn.close()
        
        # Calculate asset age
        if asset.get('installation_date'):
            install_date = datetime.fromisoformat(asset['installation_date'])
            asset_age_days = (datetime.now() - install_date).days
        else:
            asset_age_days = 0
        
        context = f"""
        Asset Information:
        - ID: {asset['id']}
        - Name: {asset['name']}
        - Category: {asset.get('category', 'Unknown')}
        - Manufacturer: {asset.get('manufacturer', 'Unknown')}
        - Model: {asset.get('model', 'Unknown')}
        - Age: {asset_age_days} days
        - Condition Rating: {asset.get('condition_rating', 'Unknown')}/5
        - Criticality: {asset.get('criticality', 'Unknown')}
        - Operating Hours: {asset.get('operating_hours', 0)}
        - Max Operating Hours: {asset.get('max_operating_hours', 'Unknown')}
        - AI Health Score: {asset.get('ai_health_score', 1.0)}
        
        Maintenance History:
        - Total Work Orders: {maintenance_stats.get('total_work_orders', 0)}
        - Average Repair Time: {maintenance_stats.get('avg_repair_time', 0)} hours
        - Total Maintenance Cost: ${maintenance_stats.get('total_maintenance_cost', 0)}
        - Last Maintenance: {asset.get('last_maintenance_date', 'Never')}
        """
        
        return context
    
    def _estimate_maintenance_cost(self, asset: Dict[str, Any], maintenance_type: str) -> float:
        """Estimate maintenance cost based on asset and type"""
        base_costs = {
            'preventive': 500,
            'corrective': 1500,
            'overhaul': 5000
        }
        
        base_cost = base_costs.get(maintenance_type, 1000)
        
        # Adjust based on asset criticality
        criticality_multiplier = {
            'Critical': 1.5,
            'High': 1.2,
            'Medium': 1.0,
            'Low': 0.8
        }
        
        multiplier = criticality_multiplier.get(asset.get('criticality', 'Medium'), 1.0)
        
        return base_cost * multiplier
    
    def _store_predictions(self, predictions: List[PredictionResult]):
        """Store predictions in database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        for pred in predictions:
            cursor.execute("""
                INSERT INTO ai_predictions (
                    prediction_type, target_id, target_type, prediction_data,
                    confidence_score, expiry_date, provider
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pred.prediction_type,
                pred.asset_id,
                'asset',
                json.dumps({
                    'predicted_failure_date': pred.predicted_failure_date.isoformat() if pred.predicted_failure_date else None,
                    'recommended_action': pred.recommended_action,
                    'urgency_level': pred.urgency_level,
                    'estimated_cost': pred.estimated_cost
                }),
                pred.confidence_score,
                datetime.now() + timedelta(days=30),  # Predictions expire in 30 days
                pred.ai_provider
            ))
        
        conn.commit()
        conn.close()
    
    async def _generate_predictive_work_orders(self, predictions: List[PredictionResult]):
        """Generate automated work orders for high-confidence predictions"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        for pred in predictions:
            if pred.confidence_score >= 0.7 and pred.urgency_level in ['Critical', 'High']:
                # Generate work order number
                wo_number = f"PWO-{datetime.now().strftime('%Y%m%d')}-{pred.asset_id:04d}"
                
                # Get asset name
                cursor.execute("SELECT name FROM assets WHERE id = ?", (pred.asset_id,))
                asset_result = cursor.fetchone()
                asset_name = asset_result['name'] if asset_result else f"Asset #{pred.asset_id}"
                
                cursor.execute("""
                    INSERT INTO work_orders (
                        wo_number, title, description, work_type, priority, 
                        status, asset_id, ai_generated, ai_urgency_score,
                        estimated_cost, due_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    wo_number,
                    f"Predictive Maintenance: {asset_name}",
                    f"AI Prediction: {pred.recommended_action}\\n\\nConfidence: {pred.confidence_score:.1%}\\nProvider: {pred.ai_provider}",
                    'Predictive',
                    pred.urgency_level,
                    'Open',
                    pred.asset_id,
                    True,
                    pred.confidence_score,
                    pred.estimated_cost,
                    pred.predicted_failure_date
                ))
        
        conn.commit()
        conn.close()

# Initialize the predictive maintenance system
predictive_ai = PredictiveMaintenanceAI()

async def run_daily_predictions():
    """Daily scheduled predictive analysis"""
    print("🤖 Running AI-powered predictive maintenance analysis...")
    predictions = await predictive_ai.run_predictive_analysis()
    print(f"✅ Generated {len(predictions)} predictions")
    
    high_priority = [p for p in predictions if p.urgency_level in ['Critical', 'High']]
    if high_priority:
        print(f"⚠️  {len(high_priority)} high-priority predictions require attention!")
    
    return predictions

if __name__ == "__main__":
    asyncio.run(run_daily_predictions())