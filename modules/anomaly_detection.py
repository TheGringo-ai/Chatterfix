"""
Anomaly Detection Module
Monitors CMMS metrics and detects statistical anomalies
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging
from dataclasses import dataclass
from collections import deque
import json

logger = logging.getLogger(__name__)

@dataclass
class MetricHistory:
    """Historical data for a specific metric"""
    values: deque
    timestamps: deque
    mean: float = 0.0
    std: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    metric_name: str
    current_value: float
    expected_range: Tuple[float, float]
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    detected_at: datetime
    confidence: float

class AnomalyDetector:
    """Statistical anomaly detection for CMMS metrics"""
    
    def __init__(self, window_size=100, sensitivity=2.0):
        self.window_size = window_size
        self.sensitivity = sensitivity  # Standard deviations for anomaly threshold
        self.metric_history = {}
        self.anomalies = deque(maxlen=1000)  # Keep last 1000 anomalies
        
    def _initialize_metric(self, metric_name: str):
        """Initialize tracking for a new metric"""
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = MetricHistory(
                values=deque(maxlen=self.window_size),
                timestamps=deque(maxlen=self.window_size)
            )
    
    def update_metric(self, metric_name: str, value: float, timestamp: datetime = None):
        """Update metric value and recalculate statistics"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self._initialize_metric(metric_name)
        
        history = self.metric_history[metric_name]
        history.values.append(value)
        history.timestamps.append(timestamp)
        history.last_updated = timestamp
        
        # Recalculate statistics if we have enough data
        if len(history.values) >= 5:
            history.mean = np.mean(history.values)
            history.std = np.std(history.values)
    
    def detect_anomaly(self, metric_name: str, current_value: float) -> Tuple[bool, Anomaly]:
        """Detect if current value is anomalous"""
        if metric_name not in self.metric_history:
            self._initialize_metric(metric_name)
            self.update_metric(metric_name, current_value)
            return False, None
        
        history = self.metric_history[metric_name]
        
        # Need at least 10 data points for reliable anomaly detection
        if len(history.values) < 10:
            self.update_metric(metric_name, current_value)
            return False, None
        
        # Calculate z-score
        z_score = abs(current_value - history.mean) / max(history.std, 0.01)
        
        # Determine if anomalous
        is_anomalous = z_score > self.sensitivity
        
        if is_anomalous:
            # Calculate expected range
            lower_bound = history.mean - self.sensitivity * history.std
            upper_bound = history.mean + self.sensitivity * history.std
            
            # Determine severity based on z-score
            if z_score > 4:
                severity = 'critical'
            elif z_score > 3:
                severity = 'high'
            elif z_score > 2.5:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Generate description
            direction = "above" if current_value > history.mean else "below"
            description = f"{metric_name} is {direction} normal range ({current_value:.2f} vs expected {history.mean:.2f}±{history.std:.2f})"
            
            anomaly = Anomaly(
                metric_name=metric_name,
                current_value=current_value,
                expected_range=(lower_bound, upper_bound),
                severity=severity,
                description=description,
                detected_at=datetime.now(),
                confidence=min(0.99, z_score / 5.0)  # Confidence based on z-score
            )
            
            self.anomalies.append(anomaly)
            logger.warning(f"Anomaly detected: {description}")
            
            # Update metric history
            self.update_metric(metric_name, current_value)
            
            return True, anomaly
        
        # Update metric history for normal values
        self.update_metric(metric_name, current_value)
        return False, None
    
    def get_recent_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get anomalies detected in the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_anomalies = [
            anomaly for anomaly in self.anomalies 
            if anomaly.detected_at > cutoff_time
        ]
        
        return [
            {
                'metric_name': anomaly.metric_name,
                'current_value': anomaly.current_value,
                'expected_range': anomaly.expected_range,
                'severity': anomaly.severity,
                'description': anomaly.description,
                'detected_at': anomaly.detected_at.isoformat(),
                'confidence': anomaly.confidence
            }
            for anomaly in recent_anomalies
        ]
    
    def get_metric_status(self, metric_name: str) -> Dict[str, Any]:
        """Get current status of a specific metric"""
        if metric_name not in self.metric_history:
            return {
                'metric_name': metric_name,
                'status': 'unknown',
                'message': 'No historical data available'
            }
        
        history = self.metric_history[metric_name]
        
        if len(history.values) < 5:
            return {
                'metric_name': metric_name,
                'status': 'learning',
                'message': f'Collecting baseline data ({len(history.values)}/10 points)',
                'last_updated': history.last_updated.isoformat()
            }
        
        current_value = history.values[-1]
        z_score = abs(current_value - history.mean) / max(history.std, 0.01)
        
        if z_score > self.sensitivity:
            status = 'anomalous'
        elif z_score > self.sensitivity * 0.8:
            status = 'warning'
        else:
            status = 'normal'
        
        return {
            'metric_name': metric_name,
            'status': status,
            'current_value': current_value,
            'mean': history.mean,
            'std': history.std,
            'z_score': z_score,
            'data_points': len(history.values),
            'last_updated': history.last_updated.isoformat()
        }

class CMOSMetricsCalculator:
    """Calculate CMMS-specific metrics for anomaly detection"""
    
    @staticmethod
    def calculate_completion_rate(work_orders: List[Dict]) -> float:
        """Calculate work order completion rate"""
        if not work_orders:
            return 0.0
        
        completed = len([wo for wo in work_orders if wo.get('status') == 'Completed'])
        return (completed / len(work_orders)) * 100
    
    @staticmethod
    def calculate_overdue_percentage(work_orders: List[Dict]) -> float:
        """Calculate percentage of overdue work orders"""
        if not work_orders:
            return 0.0
        
        now = datetime.now()
        overdue = 0
        
        for wo in work_orders:
            if wo.get('status') in ['Open', 'In Progress']:
                # Simulate due dates for demo (in production, use actual due dates)
                created_date = datetime.now() - timedelta(days=np.random.randint(1, 30))
                due_date = created_date + timedelta(days=7)  # Assume 7-day SLA
                if now > due_date:
                    overdue += 1
        
        return (overdue / len(work_orders)) * 100
    
    @staticmethod
    def calculate_mean_time_to_repair(work_orders: List[Dict]) -> float:
        """Calculate mean time to repair in hours"""
        completed_orders = [wo for wo in work_orders if wo.get('status') == 'Completed']
        
        if not completed_orders:
            return 0.0
        
        # Simulate repair times for demo (in production, use actual timestamps)
        repair_times = [np.random.uniform(1, 48) for _ in completed_orders]
        return np.mean(repair_times)
    
    @staticmethod
    def calculate_asset_downtime_rate(assets: List[Dict]) -> float:
        """Calculate percentage of assets currently down"""
        if not assets:
            return 0.0
        
        down_assets = len([a for a in assets if a.get('status') in ['Down', 'Out of Service', 'Critical']])
        return (down_assets / len(assets)) * 100
    
    @staticmethod
    def calculate_parts_stockout_rate(parts: List[Dict]) -> float:
        """Calculate percentage of parts that are out of stock"""
        if not parts:
            return 0.0
        
        out_of_stock = len([p for p in parts if p.get('current_stock', 0) <= 0])
        return (out_of_stock / len(parts)) * 100
    
    @staticmethod
    def calculate_maintenance_cost_per_asset(work_orders: List[Dict], assets: List[Dict]) -> float:
        """Calculate average maintenance cost per asset"""
        if not assets:
            return 0.0
        
        # Simulate costs for demo (in production, use actual cost data)
        total_cost = len(work_orders) * np.random.uniform(100, 1000)
        return total_cost / len(assets)

# Global anomaly detector instance
anomaly_detector = AnomalyDetector(sensitivity=2.0)
metrics_calculator = CMOSMetricsCalculator()

def monitor_cmms_metrics(work_orders: List[Dict], assets: List[Dict], parts: List[Dict]) -> Dict[str, Any]:
    """Monitor all CMMS metrics for anomalies"""
    detected_anomalies = []
    metric_statuses = {}
    
    # Calculate current metrics
    metrics = {
        'completion_rate': metrics_calculator.calculate_completion_rate(work_orders),
        'overdue_percentage': metrics_calculator.calculate_overdue_percentage(work_orders),
        'mean_time_to_repair': metrics_calculator.calculate_mean_time_to_repair(work_orders),
        'asset_downtime_rate': metrics_calculator.calculate_asset_downtime_rate(assets),
        'parts_stockout_rate': metrics_calculator.calculate_parts_stockout_rate(parts),
        'maintenance_cost_per_asset': metrics_calculator.calculate_maintenance_cost_per_asset(work_orders, assets)
    }
    
    # Check each metric for anomalies
    for metric_name, value in metrics.items():
        is_anomalous, anomaly = anomaly_detector.detect_anomaly(metric_name, value)
        
        if is_anomalous and anomaly:
            detected_anomalies.append({
                'metric_name': anomaly.metric_name,
                'current_value': anomaly.current_value,
                'expected_range': anomaly.expected_range,
                'severity': anomaly.severity,
                'description': anomaly.description,
                'detected_at': anomaly.detected_at.isoformat(),
                'confidence': anomaly.confidence
            })
        
        metric_statuses[metric_name] = anomaly_detector.get_metric_status(metric_name)
    
    return {
        'current_anomalies': detected_anomalies,
        'metric_statuses': metric_statuses,
        'current_metrics': metrics,
        'monitoring_since': datetime.now().isoformat(),
        'total_anomalies_24h': len(anomaly_detector.get_recent_anomalies(24))
    }

def get_alerts() -> Dict[str, Any]:
    """Get current alerts and anomalies"""
    recent_anomalies = anomaly_detector.get_recent_anomalies(24)
    
    # Categorize anomalies by severity
    critical_alerts = [a for a in recent_anomalies if a['severity'] == 'critical']
    high_alerts = [a for a in recent_anomalies if a['severity'] == 'high']
    medium_alerts = [a for a in recent_anomalies if a['severity'] == 'medium']
    
    return {
        'alert_summary': {
            'critical': len(critical_alerts),
            'high': len(high_alerts),
            'medium': len(medium_alerts),
            'total': len(recent_anomalies)
        },
        'critical_alerts': critical_alerts,
        'high_priority_alerts': high_alerts,
        'recent_anomalies': recent_anomalies,
        'system_status': 'critical' if critical_alerts else 'warning' if high_alerts else 'normal',
        'last_updated': datetime.now().isoformat()
    }