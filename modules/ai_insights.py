"""
AI Insights Module - Intelligent Analysis and Report Generation
Integrates with OpenAI/Gemini to provide smart operational insights
"""

import asyncio
import httpx
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class InsightCache:
    """Cache for AI-generated insights"""
    content: str
    generated_at: datetime
    expires_at: datetime
    cache_key: str

class AIInsightsEngine:
    """AI-powered insights generation engine"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.cache = {}
        self.cache_ttl_hours = 24
        
    def _get_cache_key(self, data_hash: str, insight_type: str) -> str:
        """Generate cache key for insights"""
        return f"ai_insight_{insight_type}_{data_hash}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached insight is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_insight = self.cache[cache_key]
        return datetime.now() < cached_insight.expires_at
    
    def _get_cached_insight(self, cache_key: str) -> Optional[str]:
        """Retrieve cached insight if valid"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key].content
        return None
    
    def _cache_insight(self, cache_key: str, content: str):
        """Cache AI-generated insight"""
        expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)
        self.cache[cache_key] = InsightCache(
            content=content,
            generated_at=datetime.now(),
            expires_at=expires_at,
            cache_key=cache_key
        )
    
    async def _call_openai_api(self, prompt: str, max_tokens: int = 300) -> Optional[str]:
        """Call OpenAI API for insight generation"""
        if not self.openai_api_key:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert CMMS analyst. Provide concise, actionable insights about maintenance operations. Focus on identifying trends, risks, and specific recommendations."
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"OpenAI API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None
    
    def _generate_fallback_insight(self, data_type: str, data: Dict[str, Any]) -> str:
        """Generate fallback insights when AI APIs are unavailable"""
        fallback_insights = {
            "operational_summary": self._generate_operational_fallback(data),
            "asset_analysis": self._generate_asset_fallback(data),
            "maintenance_trends": self._generate_maintenance_fallback(data),
            "risk_assessment": self._generate_risk_fallback(data)
        }
        
        return fallback_insights.get(data_type, "No insights available at this time.")
    
    def _generate_operational_fallback(self, data: Dict[str, Any]) -> str:
        """Generate operational summary fallback"""
        work_orders = data.get('work_orders', [])
        if not work_orders:
            return "Limited operational data available. Consider increasing data collection."
        
        total_orders = len(work_orders)
        completed = len([wo for wo in work_orders if wo.get('status') == 'Completed'])
        completion_rate = (completed / total_orders * 100) if total_orders > 0 else 0
        
        if completion_rate >= 90:
            return f"Excellent operational performance: {completion_rate:.1f}% completion rate across {total_orders} work orders. Team efficiency is high."
        elif completion_rate >= 75:
            return f"Good operational performance: {completion_rate:.1f}% completion rate. Consider optimizing resource allocation for better efficiency."
        else:
            return f"Performance needs attention: {completion_rate:.1f}% completion rate indicates potential bottlenecks. Review workflow and resource availability."
    
    def _generate_asset_fallback(self, data: Dict[str, Any]) -> str:
        """Generate asset analysis fallback"""
        assets = data.get('assets', [])
        if not assets:
            return "No asset data available for analysis."
        
        total_assets = len(assets)
        critical_condition = len([a for a in assets if a.get('condition') in ['Critical', 'Poor']])
        
        if critical_condition == 0:
            return f"All {total_assets} assets are in good condition. Maintain current preventive maintenance schedule."
        else:
            return f"Asset attention required: {critical_condition} out of {total_assets} assets need immediate maintenance. Priority should be given to critical condition assets."
    
    def _generate_maintenance_fallback(self, data: Dict[str, Any]) -> str:
        """Generate maintenance trends fallback"""
        parts = data.get('parts', [])
        low_stock = len([p for p in parts if p.get('current_stock', 0) <= p.get('min_stock', 0)])
        
        if low_stock > 0:
            return f"Inventory alert: {low_stock} parts are below minimum stock levels. Immediate restocking recommended to prevent maintenance delays."
        else:
            return "Inventory levels are adequate. Continue monitoring consumption patterns for optimization opportunities."
    
    def _generate_risk_fallback(self, data: Dict[str, Any]) -> str:
        """Generate risk assessment fallback"""
        predictions = data.get('predictions', [])
        high_risk = len([p for p in predictions if p.get('risk_level') == 'high'])
        
        if high_risk > 0:
            return f"Risk alert: {high_risk} assets identified as high-risk for failure. Schedule immediate inspections and preventive maintenance."
        else:
            return "Risk levels are manageable. Continue monitoring asset conditions and maintaining preventive schedules."
    
    async def generate_operational_summary(self, work_orders: List[Dict], assets: List[Dict], parts: List[Dict]) -> str:
        """Generate comprehensive operational summary"""
        data_hash = hashlib.md5(str(len(work_orders) + len(assets) + len(parts)).encode()).hexdigest()
        cache_key = self._get_cache_key(data_hash, "operational_summary")
        
        # Check cache first
        cached_result = self._get_cached_insight(cache_key)
        if cached_result:
            return cached_result
        
        # Prepare data summary for AI
        total_work_orders = len(work_orders)
        completed_orders = len([wo for wo in work_orders if wo.get('status') == 'Completed'])
        completion_rate = (completed_orders / total_work_orders * 100) if total_work_orders > 0 else 0
        
        total_assets = len(assets)
        critical_assets = len([a for a in assets if a.get('condition') in ['Critical', 'Poor']])
        
        total_parts = len(parts)
        low_stock_parts = len([p for p in parts if p.get('current_stock', 0) <= p.get('min_stock', 0)])
        
        prompt = f"""
        Analyze this CMMS operational data and provide a concise summary with specific insights:
        
        Work Orders: {total_work_orders} total, {completed_orders} completed ({completion_rate:.1f}% rate)
        Assets: {total_assets} total, {critical_assets} in critical/poor condition
        Inventory: {total_parts} parts, {low_stock_parts} below minimum stock
        
        Provide a 2-3 sentence analysis focusing on:
        1. Key operational trends or concerns
        2. Specific actionable recommendations
        3. Any anomalies or opportunities for improvement
        
        Be specific and mention actual numbers in your analysis.
        """
        
        # Try AI API first
        ai_result = await self._call_openai_api(prompt)
        if ai_result:
            self._cache_insight(cache_key, ai_result)
            return ai_result
        
        # Fallback to rule-based insights
        fallback_result = self._generate_fallback_insight("operational_summary", {
            'work_orders': work_orders,
            'assets': assets,
            'parts': parts
        })
        self._cache_insight(cache_key, fallback_result)
        return fallback_result
    
    async def generate_asset_insights(self, assets: List[Dict], predictions: List[Dict]) -> List[Dict[str, Any]]:
        """Generate AI insights for specific assets"""
        insights = []
        
        # Focus on highest risk assets
        high_risk_assets = [p for p in predictions if p.get('failure_risk', 0) > 0.6][:5]
        
        for prediction in high_risk_assets:
            asset_id = prediction.get('asset_id')
            asset_data = next((a for a in assets if str(a.get('id')) == str(asset_id)), {})
            
            data_hash = hashlib.md5(f"{asset_id}_{prediction.get('failure_risk')}".encode()).hexdigest()
            cache_key = self._get_cache_key(data_hash, f"asset_{asset_id}")
            
            cached_result = self._get_cached_insight(cache_key)
            if cached_result:
                insights.append({
                    'asset_id': asset_id,
                    'insight': cached_result,
                    'generated_by': 'ai_cached',
                    'risk_level': prediction.get('risk_level'),
                    'failure_risk': prediction.get('failure_risk')
                })
                continue
            
            # Generate AI insight for this specific asset
            prompt = f"""
            Analyze this specific asset for maintenance insights:
            
            Asset ID: {asset_id}
            Type: {asset_data.get('asset_type', 'Unknown')}
            Failure Risk: {prediction.get('failure_risk', 0):.2f}
            Recommended Action: {prediction.get('recommendation', 'None')}
            Next Maintenance: {prediction.get('next_due_date', 'Unknown')}
            
            Provide a 1-2 sentence specific insight about this asset's condition and the most likely cause of its high risk status. Be specific and actionable.
            """
            
            ai_result = await self._call_openai_api(prompt, max_tokens=150)
            if ai_result:
                self._cache_insight(cache_key, ai_result)
                insights.append({
                    'asset_id': asset_id,
                    'insight': ai_result,
                    'generated_by': 'ai',
                    'risk_level': prediction.get('risk_level'),
                    'failure_risk': prediction.get('failure_risk')
                })
            else:
                # Fallback insight
                fallback = f"Asset #{asset_id} shows {prediction.get('failure_risk', 0):.0%} failure risk. {prediction.get('recommendation', 'Immediate inspection recommended.')}"
                insights.append({
                    'asset_id': asset_id,
                    'insight': fallback,
                    'generated_by': 'fallback',
                    'risk_level': prediction.get('risk_level'),
                    'failure_risk': prediction.get('failure_risk')
                })
        
        return insights
    
    async def generate_maintenance_recommendations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered maintenance recommendations"""
        cache_key = self._get_cache_key("maintenance_recs", "recommendations")
        
        cached_result = self._get_cached_insight(cache_key)
        if cached_result:
            try:
                return json.loads(cached_result)
            except:
                pass
        
        prompt = """
        Based on CMMS operational data, provide maintenance recommendations in JSON format:
        
        {
            "immediate_actions": ["action1", "action2"],
            "weekly_priorities": ["priority1", "priority2"], 
            "optimization_opportunities": ["opportunity1", "opportunity2"],
            "cost_reduction_tips": ["tip1", "tip2"]
        }
        
        Focus on practical, actionable recommendations for a maintenance team.
        """
        
        ai_result = await self._call_openai_api(prompt)
        if ai_result:
            try:
                result_json = json.loads(ai_result)
                self._cache_insight(cache_key, ai_result)
                return result_json
            except:
                pass
        
        # Fallback recommendations
        fallback_recs = {
            "immediate_actions": [
                "Review high-risk assets requiring urgent maintenance",
                "Restock parts that are below minimum inventory levels"
            ],
            "weekly_priorities": [
                "Schedule preventive maintenance for medium-risk assets",
                "Update maintenance schedules based on usage patterns"
            ],
            "optimization_opportunities": [
                "Implement predictive maintenance for critical assets",
                "Optimize spare parts inventory based on consumption trends"
            ],
            "cost_reduction_tips": [
                "Group maintenance tasks by location to reduce travel time",
                "Negotiate bulk purchasing agreements for frequently used parts"
            ]
        }
        
        self._cache_insight(cache_key, json.dumps(fallback_recs))
        return fallback_recs

# Global AI insights engine instance
ai_insights_engine = AIInsightsEngine()

async def get_ai_summary(work_orders: List[Dict], assets: List[Dict], parts: List[Dict]) -> Dict[str, Any]:
    """Get comprehensive AI-generated summary"""
    try:
        summary = await ai_insights_engine.generate_operational_summary(work_orders, assets, parts)
        recommendations = await ai_insights_engine.generate_maintenance_recommendations({
            'work_orders': work_orders,
            'assets': assets,
            'parts': parts
        })
        
        return {
            'summary': summary,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat(),
            'generated_by': 'ai',
            'cache_expires': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return {
            'summary': 'AI insights temporarily unavailable. System is operating normally.',
            'recommendations': {
                'immediate_actions': ['Continue regular maintenance schedules'],
                'weekly_priorities': ['Monitor system performance'],
                'optimization_opportunities': ['Review operational procedures'],
                'cost_reduction_tips': ['Optimize resource allocation']
            },
            'generated_at': datetime.now().isoformat(),
            'generated_by': 'fallback',
            'error': str(e)
        }

async def get_asset_specific_insights(assets: List[Dict], predictions: List[Dict]) -> List[Dict[str, Any]]:
    """Get AI insights for specific high-risk assets"""
    try:
        return await ai_insights_engine.generate_asset_insights(assets, predictions)
    except Exception as e:
        logger.error(f"Error generating asset insights: {e}")
        return []