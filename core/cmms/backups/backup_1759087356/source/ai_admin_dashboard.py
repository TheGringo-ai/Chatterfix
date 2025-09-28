#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - AI Admin Dashboard
Advanced AI model management, fine-tuning, and monitoring
"""

import sqlite3
import json
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
import statistics
import time

@dataclass
class ModelMetrics:
    model_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    average_confidence: float
    last_used: datetime
    cost_per_request: float
    total_cost: float

@dataclass
class ModelConfig:
    id: int
    model_name: str
    model_type: str
    endpoint_url: str
    api_key: str
    parameters: Dict[str, Any]
    is_active: bool
    performance_metrics: Dict[str, Any]
    created_date: datetime

class AIAdminDashboard:
    """Advanced AI model management and monitoring system"""
    
    def __init__(self, db_path: str = "./data/cmms_enhanced.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Model performance tracking
        self.performance_cache = {}
        self.active_models = {}
        
        # Cost tracking (approximate costs per 1K tokens)
        self.model_costs = {
            'gpt-4': 0.03,
            'gpt-3.5-turbo': 0.002,
            'claude-3': 0.025,
            'llama3': 0.0,  # Local model, no API cost
            'grok': 0.01,
            'whisper': 0.006
        }
        
        self._init_admin_tables()
        self._load_active_models()
    
    def _init_admin_tables(self):
        """Initialize AI admin tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # AI request logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                request_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                response_timestamp DATETIME,
                request_tokens INTEGER,
                response_tokens INTEGER,
                total_tokens INTEGER,
                response_time_ms INTEGER,
                success BOOLEAN,
                error_message TEXT,
                confidence_score DECIMAL(3,2),
                user_id INTEGER,
                session_id TEXT,
                request_type TEXT, -- 'chat', 'completion', 'transcription', 'ocr'
                cost_usd DECIMAL(8,4),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Model fine-tuning jobs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_fine_tuning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                base_model TEXT NOT NULL,
                training_data_path TEXT,
                fine_tune_job_id TEXT,
                status TEXT DEFAULT 'pending', -- pending, running, completed, failed
                parameters TEXT DEFAULT '{}',
                metrics TEXT DEFAULT '{}',
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_date DATETIME,
                created_by INTEGER,
                cost_usd DECIMAL(8,2),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Model A/B testing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_ab_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                model_a TEXT NOT NULL,
                model_b TEXT NOT NULL,
                traffic_split DECIMAL(3,2) DEFAULT 0.5,
                status TEXT DEFAULT 'active', -- active, paused, completed
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_date DATETIME,
                success_metric TEXT DEFAULT 'response_quality',
                results TEXT DEFAULT '{}',
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Custom prompts and templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_prompt_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL,
                category TEXT NOT NULL, -- 'work_order', 'asset_analysis', 'predictive', 'general'
                prompt_template TEXT NOT NULL,
                variables TEXT DEFAULT '[]', -- JSON array of variable names
                model_type TEXT, -- specific model type or 'any'
                usage_count INTEGER DEFAULT 0,
                rating DECIMAL(2,1) DEFAULT 0.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Model performance alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL, -- 'performance', 'cost', 'error_rate', 'availability'
                model_name TEXT,
                severity TEXT DEFAULT 'medium', -- low, medium, high, critical
                message TEXT NOT NULL,
                threshold_value DECIMAL(10,4),
                current_value DECIMAL(10,4),
                alert_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by INTEGER,
                acknowledged_date DATETIME,
                resolved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (acknowledged_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_active_models(self):
        """Load active model configurations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ai_model_configs WHERE is_active = TRUE')
        
        for row in cursor.fetchall():
            model_config = ModelConfig(
                id=row[0],
                model_name=row[1],
                model_type=row[2],
                endpoint_url=row[3] or "",
                api_key=row[4] or "",
                parameters=json.loads(row[5] or "{}"),
                is_active=bool(row[6]),
                performance_metrics=json.loads(row[7] or "{}"),
                created_date=datetime.fromisoformat(row[9])
            )
            self.active_models[model_config.model_name] = model_config
        
        conn.close()
    
    # ==================== MODEL MONITORING ====================
    
    async def log_ai_request(self, model_name: str, model_type: str, request_tokens: int,
                            response_tokens: int, response_time_ms: int, success: bool,
                            error_message: str = None, confidence_score: float = None,
                            user_id: int = None, request_type: str = 'chat') -> int:
        """Log AI request for monitoring and analytics"""
        try:
            total_tokens = request_tokens + response_tokens
            cost = self._calculate_cost(model_name, total_tokens)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_request_logs (
                    model_name, model_type, response_timestamp, request_tokens,
                    response_tokens, total_tokens, response_time_ms, success,
                    error_message, confidence_score, user_id, request_type, cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_name, model_type, datetime.now(), request_tokens,
                response_tokens, total_tokens, response_time_ms, success,
                error_message, confidence_score, user_id, request_type, cost
            ))
            
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Update performance cache
            await self._update_performance_metrics(model_name)
            
            # Check for alerts
            await self._check_performance_alerts(model_name)
            
            return log_id
            
        except Exception as e:
            self.logger.error(f"Failed to log AI request: {e}")
            return 0
    
    def _calculate_cost(self, model_name: str, total_tokens: int) -> float:
        """Calculate cost for AI request"""
        base_model = model_name.split(':')[0]  # Handle model variants
        cost_per_1k = self.model_costs.get(base_model, 0.01)  # Default cost
        return (total_tokens / 1000) * cost_per_1k
    
    async def _update_performance_metrics(self, model_name: str):
        """Update cached performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent performance data (last 24 hours)
            cursor.execute('''
                SELECT response_time_ms, success, confidence_score, cost_usd
                FROM ai_request_logs 
                WHERE model_name = ? AND request_timestamp >= datetime('now', '-1 day')
            ''', (model_name,))
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return
            
            # Calculate metrics
            response_times = [r[0] for r in records if r[0]]
            successes = [r[1] for r in records]
            confidences = [r[2] for r in records if r[2]]
            costs = [r[3] for r in records if r[3]]
            
            metrics = ModelMetrics(
                model_name=model_name,
                total_requests=len(records),
                successful_requests=sum(successes),
                failed_requests=len(records) - sum(successes),
                average_response_time=statistics.mean(response_times) if response_times else 0,
                average_confidence=statistics.mean(confidences) if confidences else 0,
                last_used=datetime.now(),
                cost_per_request=statistics.mean(costs) if costs else 0,
                total_cost=sum(costs) if costs else 0
            )
            
            self.performance_cache[model_name] = metrics
            
        except Exception as e:
            self.logger.error(f"Performance metrics update failed: {e}")
    
    async def _check_performance_alerts(self, model_name: str):
        """Check if performance alerts should be triggered"""
        try:
            metrics = self.performance_cache.get(model_name)
            if not metrics:
                return
            
            alerts = []
            
            # High error rate alert
            error_rate = metrics.failed_requests / metrics.total_requests if metrics.total_requests > 0 else 0
            if error_rate > 0.1:  # 10% error rate threshold
                alerts.append({
                    'type': 'error_rate',
                    'severity': 'high' if error_rate > 0.2 else 'medium',
                    'message': f'High error rate for {model_name}: {error_rate:.1%}',
                    'threshold': 0.1,
                    'current': error_rate
                })
            
            # Slow response time alert
            if metrics.average_response_time > 5000:  # 5 seconds threshold
                alerts.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'message': f'Slow response time for {model_name}: {metrics.average_response_time:.0f}ms',
                    'threshold': 5000,
                    'current': metrics.average_response_time
                })
            
            # High cost alert
            if metrics.total_cost > 10.0:  # $10 per day threshold
                alerts.append({
                    'type': 'cost',
                    'severity': 'high',
                    'message': f'High daily cost for {model_name}: ${metrics.total_cost:.2f}',
                    'threshold': 10.0,
                    'current': metrics.total_cost
                })
            
            # Save alerts
            if alerts:
                await self._save_alerts(alerts, model_name)
                
        except Exception as e:
            self.logger.error(f"Alert checking failed: {e}")
    
    async def _save_alerts(self, alerts: List[Dict], model_name: str):
        """Save performance alerts to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''
                INSERT INTO ai_alerts (alert_type, model_name, severity, message, threshold_value, current_value)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                alert['type'], model_name, alert['severity'],
                alert['message'], alert['threshold'], alert['current']
            ))
        
        conn.commit()
        conn.close()
    
    # ==================== MODEL MANAGEMENT ====================
    
    async def add_model_config(self, model_name: str, model_type: str, endpoint_url: str = "",
                              api_key: str = "", parameters: Dict = None, user_id: int = None) -> int:
        """Add new AI model configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_model_configs (
                    model_name, model_type, endpoint_url, api_key, 
                    model_parameters, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                model_name, model_type, endpoint_url, api_key,
                json.dumps(parameters or {}), user_id
            ))
            
            config_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Reload active models
            self._load_active_models()
            
            return config_id
            
        except Exception as e:
            self.logger.error(f"Failed to add model config: {e}")
            return 0
    
    async def update_model_config(self, config_id: int, updates: Dict) -> bool:
        """Update model configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query dynamically
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key in ['model_name', 'model_type', 'endpoint_url', 'api_key', 'is_active']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                elif key == 'parameters':
                    set_clauses.append("model_parameters = ?")
                    values.append(json.dumps(value))
            
            if not set_clauses:
                return False
            
            values.append(config_id)
            query = f"UPDATE ai_model_configs SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            # Reload active models
            self._load_active_models()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update model config: {e}")
            return False
    
    async def test_model_connection(self, model_name: str) -> Dict[str, Any]:
        """Test connection to AI model"""
        try:
            model_config = self.active_models.get(model_name)
            if not model_config:
                return {"success": False, "error": "Model not found"}
            
            start_time = time.time()
            
            if model_config.model_type == 'ollama':
                result = await self._test_ollama_connection(model_config)
            elif model_config.model_type == 'openai':
                result = await self._test_openai_connection(model_config)
            elif model_config.model_type == 'grok':
                result = await self._test_grok_connection(model_config)
            else:
                return {"success": False, "error": "Unsupported model type"}
            
            response_time = (time.time() - start_time) * 1000
            
            result["response_time_ms"] = response_time
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_ollama_connection(self, config: ModelConfig) -> Dict[str, Any]:
        """Test Ollama connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.endpoint_url}/api/chat",
                    json={
                        "model": config.model_name,
                        "messages": [{"role": "user", "content": "Test connection"}],
                        "stream": False
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "Ollama connection successful"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_openai_connection(self, config: ModelConfig) -> Dict[str, Any]:
        """Test OpenAI connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.endpoint_url}/chat/completions",
                    headers={"Authorization": f"Bearer {config.api_key}"},
                    json={
                        "model": config.model_name,
                        "messages": [{"role": "user", "content": "Test"}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "OpenAI connection successful"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_grok_connection(self, config: ModelConfig) -> Dict[str, Any]:
        """Test Grok connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.endpoint_url}/chat/completions",
                    headers={"Authorization": f"Bearer {config.api_key}"},
                    json={
                        "model": config.model_name,
                        "messages": [{"role": "user", "content": "Test"}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "Grok connection successful"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== ANALYTICS AND REPORTING ====================
    
    def get_model_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive model performance summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall statistics
            cursor.execute('''
                SELECT 
                    model_name,
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                    AVG(response_time_ms) as avg_response_time,
                    AVG(confidence_score) as avg_confidence,
                    SUM(cost_usd) as total_cost
                FROM ai_request_logs 
                WHERE request_timestamp >= datetime('now', '-{} days')
                GROUP BY model_name
            '''.format(days))
            
            model_stats = {}
            for row in cursor.fetchall():
                model_name = row[0]
                model_stats[model_name] = {
                    'total_requests': row[1],
                    'successful_requests': row[2],
                    'success_rate': (row[2] / row[1]) if row[1] > 0 else 0,
                    'avg_response_time': row[3] or 0,
                    'avg_confidence': row[4] or 0,
                    'total_cost': row[5] or 0
                }
            
            # Request trends
            cursor.execute('''
                SELECT 
                    DATE(request_timestamp) as date,
                    model_name,
                    COUNT(*) as requests
                FROM ai_request_logs 
                WHERE request_timestamp >= datetime('now', '-{} days')
                GROUP BY DATE(request_timestamp), model_name
                ORDER BY date
            '''.format(days))
            
            trends = {}
            for row in cursor.fetchall():
                date, model_name, requests = row
                if date not in trends:
                    trends[date] = {}
                trends[date][model_name] = requests
            
            conn.close()
            
            return {
                'model_statistics': model_stats,
                'request_trends': trends,
                'cached_metrics': {name: asdict(metrics) for name, metrics in self.performance_cache.items()}
            }
            
        except Exception as e:
            self.logger.error(f"Performance summary failed: {e}")
            return {}
    
    def get_active_alerts(self) -> List[Dict]:
        """Get active performance alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM ai_alerts 
                WHERE resolved = FALSE 
                ORDER BY alert_date DESC, severity DESC
            ''')
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'id': row[0],
                    'alert_type': row[1],
                    'model_name': row[2],
                    'severity': row[3],
                    'message': row[4],
                    'threshold_value': row[5],
                    'current_value': row[6],
                    'alert_date': row[7],
                    'acknowledged': bool(row[8])
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get alerts: {e}")
            return []
    
    def get_cost_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed cost analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Daily costs
            cursor.execute('''
                SELECT 
                    DATE(request_timestamp) as date,
                    model_name,
                    SUM(cost_usd) as daily_cost,
                    COUNT(*) as requests
                FROM ai_request_logs 
                WHERE request_timestamp >= datetime('now', '-{} days')
                GROUP BY DATE(request_timestamp), model_name
                ORDER BY date
            '''.format(days))
            
            daily_costs = {}
            for row in cursor.fetchall():
                date, model_name, cost, requests = row
                if date not in daily_costs:
                    daily_costs[date] = {}
                daily_costs[date][model_name] = {
                    'cost': cost,
                    'requests': requests,
                    'cost_per_request': cost / requests if requests > 0 else 0
                }
            
            # Total costs by model
            cursor.execute('''
                SELECT 
                    model_name,
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as total_requests
                FROM ai_request_logs 
                WHERE request_timestamp >= datetime('now', '-{} days')
                GROUP BY model_name
                ORDER BY total_cost DESC
            '''.format(days))
            
            model_costs = {}
            total_cost = 0
            for row in cursor.fetchall():
                model_name, cost, requests = row
                model_costs[model_name] = {
                    'total_cost': cost,
                    'total_requests': requests,
                    'cost_per_request': cost / requests if requests > 0 else 0
                }
                total_cost += cost
            
            conn.close()
            
            return {
                'daily_costs': daily_costs,
                'model_costs': model_costs,
                'total_cost': total_cost,
                'average_daily_cost': total_cost / days if days > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Cost analysis failed: {e}")
            return {}

# Initialize the AI admin dashboard
ai_admin = AIAdminDashboard()