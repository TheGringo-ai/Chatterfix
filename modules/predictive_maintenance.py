"""
AI-Driven Predictive Maintenance Module
Uses machine learning to predict asset failures and maintenance needs
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os
import json

logger = logging.getLogger(__name__)

class PredictiveMaintenanceEngine:
    """ML-powered predictive maintenance engine"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.last_training = None
        
    def generate_synthetic_training_data(self, n_samples=1000):
        """Generate synthetic training data for demonstration"""
        np.random.seed(42)  # For reproducible results
        
        data = []
        for i in range(n_samples):
            # Asset characteristics
            asset_age_months = np.random.randint(1, 120)  # 1-10 years
            usage_hours_weekly = np.random.normal(40, 15)  # Normal usage with variation
            last_maintenance_days = np.random.randint(1, 365)
            
            # Operating conditions
            temperature_avg = np.random.normal(75, 10)  # Average operating temp
            vibration_level = np.random.normal(0.5, 0.2)  # Vibration intensity
            load_factor = np.random.uniform(0.3, 1.0)  # How hard the asset works
            
            # Maintenance history
            maintenance_frequency = np.random.poisson(4)  # Maintenance events per year
            part_replacements = np.random.poisson(2)  # Parts replaced per year
            
            # Calculate failure risk (target variable)
            # Higher risk for: older assets, heavy usage, poor maintenance, extreme conditions
            risk_score = (
                (asset_age_months / 120) * 0.3 +  # Age factor
                (max(0, usage_hours_weekly - 40) / 40) * 0.2 +  # Overuse factor
                (last_maintenance_days / 365) * 0.25 +  # Maintenance delay factor
                (abs(temperature_avg - 75) / 50) * 0.15 +  # Temperature stress
                (max(0, vibration_level - 0.5) / 0.5) * 0.1  # Vibration factor
            )
            
            # Add some randomness
            risk_score += np.random.normal(0, 0.1)
            risk_score = np.clip(risk_score, 0, 1)
            
            data.append({
                'asset_age_months': asset_age_months,
                'usage_hours_weekly': usage_hours_weekly,
                'last_maintenance_days': last_maintenance_days,
                'temperature_avg': temperature_avg,
                'vibration_level': vibration_level,
                'load_factor': load_factor,
                'maintenance_frequency': maintenance_frequency,
                'part_replacements': part_replacements,
                'failure_risk': risk_score
            })
        
        return pd.DataFrame(data)
    
    def train_model(self):
        """Train the predictive maintenance model"""
        try:
            logger.info("Training predictive maintenance model...")
            
            # Generate training data
            df = self.generate_synthetic_training_data()
            
            # Prepare features and target
            feature_columns = [
                'asset_age_months', 'usage_hours_weekly', 'last_maintenance_days',
                'temperature_avg', 'vibration_level', 'load_factor',
                'maintenance_frequency', 'part_replacements'
            ]
            
            X = df[feature_columns]
            y = df['failure_risk']
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_scaled, y)
            
            self.is_trained = True
            self.last_training = datetime.now()
            
            # Get feature importance
            feature_importance = dict(zip(feature_columns, self.model.feature_importances_))
            logger.info(f"Model trained successfully. Feature importance: {feature_importance}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training predictive maintenance model: {e}")
            return False
    
    def predict_asset_risk(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict failure risk for a single asset"""
        if not self.is_trained:
            self.train_model()
        
        try:
            # Extract features from asset data
            features = [
                asset_data.get('age_months', 24),
                asset_data.get('usage_hours_weekly', 40),
                asset_data.get('last_maintenance_days', 30),
                asset_data.get('temperature_avg', 75),
                asset_data.get('vibration_level', 0.5),
                asset_data.get('load_factor', 0.7),
                asset_data.get('maintenance_frequency', 4),
                asset_data.get('part_replacements', 2)
            ]
            
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Predict risk
            risk_score = self.model.predict(features_scaled)[0]
            risk_score = np.clip(risk_score, 0, 1)
            
            # Calculate next maintenance date based on risk
            days_until_maintenance = max(7, int(30 * (1 - risk_score)))
            next_due_date = (datetime.now() + timedelta(days=days_until_maintenance)).strftime('%Y-%m-%d')
            
            # Generate recommendation based on risk level and asset type
            recommendation = self._generate_recommendation(risk_score, asset_data)
            
            return {
                'asset_id': asset_data.get('id', 'unknown'),
                'failure_risk': round(risk_score, 3),
                'risk_level': self._get_risk_level(risk_score),
                'next_due_date': next_due_date,
                'recommendation': recommendation,
                'confidence': round(0.85 + np.random.uniform(-0.1, 0.1), 3),
                'predicted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting asset risk: {e}")
            return {
                'asset_id': asset_data.get('id', 'unknown'),
                'failure_risk': 0.5,
                'risk_level': 'medium',
                'next_due_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'recommendation': 'Schedule routine inspection',
                'confidence': 0.5,
                'predicted_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to categorical level"""
        if risk_score >= 0.7:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendation(self, risk_score: float, asset_data: Dict[str, Any]) -> str:
        """Generate maintenance recommendation based on risk and asset type"""
        asset_type = asset_data.get('asset_type', 'Equipment').lower()
        
        if risk_score >= 0.8:
            recommendations = {
                'hvac': 'URGENT: Check refrigerant levels and replace filters immediately',
                'elevator': 'URGENT: Inspect cables, brakes, and safety systems',
                'production': 'URGENT: Stop operation and inspect critical components',
                'safety': 'URGENT: Test all safety systems and replace faulty components',
                'default': 'URGENT: Schedule immediate inspection and component replacement'
            }
        elif risk_score >= 0.6:
            recommendations = {
                'hvac': 'Schedule comprehensive HVAC maintenance within 7 days',
                'elevator': 'Perform emergency brake and motor inspection',
                'production': 'Plan production shutdown for maintenance',
                'safety': 'Test and calibrate all safety equipment',
                'default': 'Schedule detailed inspection within one week'
            }
        elif risk_score >= 0.4:
            recommendations = {
                'hvac': 'Replace filters and check thermostat calibration',
                'elevator': 'Lubricate moving parts and check emergency systems',
                'production': 'Inspect bearings and replace worn components',
                'safety': 'Test emergency systems and update signage',
                'default': 'Perform routine maintenance and component check'
            }
        else:
            recommendations = {
                'hvac': 'Continue regular filter changes and monitoring',
                'elevator': 'Maintain current inspection schedule',
                'production': 'Monitor performance trends',
                'safety': 'Continue routine safety checks',
                'default': 'Asset operating normally, continue monitoring'
            }
        
        return recommendations.get(asset_type, recommendations['default'])

# Global predictive maintenance engine instance
pm_engine = PredictiveMaintenanceEngine()

def get_predictive_maintenance_data(assets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get predictive maintenance data for all assets"""
    predictions = []
    
    for asset in assets_data:
        # Simulate asset telemetry data (in production, this would come from sensors)
        asset_telemetry = {
            'id': asset.get('id'),
            'asset_type': asset.get('asset_type', 'Equipment'),
            'age_months': np.random.randint(6, 60),  # Simulate asset age
            'usage_hours_weekly': np.random.normal(40, 10),
            'last_maintenance_days': np.random.randint(5, 120),
            'temperature_avg': np.random.normal(75, 15),
            'vibration_level': np.random.uniform(0.2, 1.2),
            'load_factor': np.random.uniform(0.4, 0.95),
            'maintenance_frequency': np.random.poisson(3),
            'part_replacements': np.random.poisson(1)
        }
        
        prediction = pm_engine.predict_asset_risk(asset_telemetry)
        predictions.append(prediction)
    
    # Sort by failure risk (highest first)
    predictions.sort(key=lambda x: x['failure_risk'], reverse=True)
    
    return predictions

def get_asset_risk_summary() -> Dict[str, Any]:
    """Get summary of asset risk levels"""
    # This would typically analyze all assets, for demo we'll generate sample data
    total_assets = 50
    high_risk = np.random.randint(3, 8)
    medium_risk = np.random.randint(8, 15)
    low_risk = total_assets - high_risk - medium_risk
    
    return {
        'total_assets': total_assets,
        'risk_distribution': {
            'high': high_risk,
            'medium': medium_risk, 
            'low': low_risk
        },
        'immediate_attention_required': high_risk,
        'estimated_downtime_prevented_hours': high_risk * 8 + medium_risk * 2,
        'cost_savings_estimated': high_risk * 2500 + medium_risk * 800,
        'last_updated': datetime.now().isoformat()
    }