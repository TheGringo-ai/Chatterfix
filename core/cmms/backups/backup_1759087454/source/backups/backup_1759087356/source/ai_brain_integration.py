#!/usr/bin/env python3
"""
ChatterFix CMMS AI Brain Integration for Data Mode System
Smart data mode detection, recommendations, and optimization
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from admin import admin_manager, get_system_mode
from data_toggle_system import data_toggle_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIBrainDataModeIntegration:
    """AI Brain integration for smart data mode management"""
    
    def __init__(self):
        self.admin = admin_manager
        self.data_system = data_toggle_system
        
    def analyze_system_usage(self) -> Dict[str, Any]:
        """Analyze system usage patterns to provide intelligent recommendations"""
        try:
            current_mode = get_system_mode()
            overview = self.data_system.get_system_overview()
            
            analysis = {
                "current_mode": current_mode,
                "analysis_timestamp": datetime.now().isoformat(),
                "usage_patterns": self._analyze_usage_patterns(overview),
                "data_health": self._analyze_data_health(overview),
                "performance_metrics": self._analyze_performance(overview),
                "recommendations": self._generate_recommendations(overview)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing system usage: {e}")
            return {"error": str(e)}
    
    def _analyze_usage_patterns(self, overview: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze usage patterns from system overview"""
        demo_records = overview.get("demo_mode", {}).get("record_counts", {})
        production_records = overview.get("production_mode", {}).get("record_counts", {})
        
        demo_total = sum(demo_records.values()) if demo_records else 0
        production_total = sum(production_records.values()) if production_records else 0
        
        mode_switches = len(overview.get("mode_switch_history", []))
        
        return {
            "demo_data_activity": demo_total,
            "production_data_activity": production_total,
            "mode_switches_count": mode_switches,
            "primary_usage_mode": "demo" if demo_total > production_total else "production",
            "usage_balance": {
                "demo_percentage": (demo_total / (demo_total + production_total) * 100) if (demo_total + production_total) > 0 else 0,
                "production_percentage": (production_total / (demo_total + production_total) * 100) if (demo_total + production_total) > 0 else 0
            }
        }
    
    def _analyze_data_health(self, overview: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data health and integrity"""
        demo_mode = overview.get("demo_mode", {})
        production_mode = overview.get("production_mode", {})
        
        demo_size = demo_mode.get("database_size_mb", 0)
        production_size = production_mode.get("database_size_mb", 0)
        
        demo_exists = demo_mode.get("database_exists", False)
        production_exists = production_mode.get("database_exists", False)
        
        health_score = 0
        issues = []
        
        # Check database existence
        if demo_exists:
            health_score += 25
        else:
            issues.append("Demo database not found")
            
        if production_exists:
            health_score += 25
        else:
            issues.append("Production database not found")
        
        # Check database sizes
        if demo_size > 0:
            health_score += 25
        else:
            issues.append("Demo database appears empty")
            
        if production_size >= 0:  # Production can be empty initially
            health_score += 25
        
        return {
            "health_score": health_score,
            "status": "excellent" if health_score >= 90 else "good" if health_score >= 70 else "fair" if health_score >= 50 else "poor",
            "issues": issues,
            "database_integrity": {
                "demo_healthy": demo_exists and demo_size > 0,
                "production_healthy": production_exists,
                "demo_size_mb": demo_size,
                "production_size_mb": production_size
            }
        }
    
    def _analyze_performance(self, overview: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system performance metrics"""
        current_mode = overview.get("current_mode", "production")
        mode_switches = overview.get("mode_switch_history", [])
        
        recent_switches = [
            switch for switch in mode_switches 
            if datetime.fromisoformat(switch["timestamp"]) > datetime.now() - timedelta(days=7)
        ]
        
        return {
            "current_mode_stability": len(recent_switches) < 3,  # Less than 3 switches in 7 days
            "mode_switches_last_week": len(recent_switches),
            "mode_switch_frequency": "low" if len(recent_switches) < 2 else "medium" if len(recent_switches) < 5 else "high",
            "system_stability_score": max(0, 100 - (len(recent_switches) * 10)),  # Penalize frequent switches
            "optimal_mode_detected": self._detect_optimal_mode(overview)
        }
    
    def _detect_optimal_mode(self, overview: Dict[str, Any]) -> str:
        """Use AI to detect optimal mode based on usage patterns"""
        company_setup = overview.get("settings", {}).get("company_setup", {})
        current_mode = overview.get("current_mode", "production")
        
        # If company setup is not completed, recommend demo mode
        if not company_setup.get("completed", False):
            return "demo"
        
        # If company setup is completed and we're in demo mode, suggest production
        if company_setup.get("completed", False) and current_mode == "demo":
            return "production"
        
        # Analyze data activity
        usage_patterns = self._analyze_usage_patterns(overview)
        
        # If there's significant production data activity, stay in production
        if usage_patterns["production_data_activity"] > usage_patterns["demo_data_activity"] * 2:
            return "production"
        
        # If still mostly using demo data, suggest staying in demo for training
        if usage_patterns["demo_percentage"] > 80:
            return "demo"
        
        return current_mode  # No change recommended
    
    def _generate_recommendations(self, overview: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations"""
        recommendations = []
        
        current_mode = overview.get("current_mode", "production")
        company_setup = overview.get("settings", {}).get("company_setup", {})
        usage_patterns = self._analyze_usage_patterns(overview)
        data_health = self._analyze_data_health(overview)
        performance = self._analyze_performance(overview)
        
        # Company setup recommendations
        if not company_setup.get("completed", False):
            recommendations.append({
                "type": "company_setup",
                "priority": "high",
                "title": "Complete Company Setup",
                "description": "Complete your company setup to unlock full production features and optimize system configuration.",
                "action": "complete_company_setup",
                "icon": "🏢",
                "ai_confidence": 0.95
            })
        
        # Mode optimization recommendations
        optimal_mode = performance.get("optimal_mode_detected", current_mode)
        if optimal_mode != current_mode:
            if optimal_mode == "production":
                recommendations.append({
                    "type": "mode_switch",
                    "priority": "medium",
                    "title": "Ready for Production Mode",
                    "description": "Your setup is complete and you're ready to switch to production mode for live operations.",
                    "action": "switch_to_production",
                    "icon": "🚀",
                    "ai_confidence": 0.85
                })
            else:
                recommendations.append({
                    "type": "mode_switch",
                    "priority": "low",
                    "title": "Consider Demo Mode for Training",
                    "description": "You might benefit from demo mode for training and testing before full production use.",
                    "action": "switch_to_demo",
                    "icon": "🧪",
                    "ai_confidence": 0.70
                })
        
        # Data backup recommendations
        if data_health["health_score"] >= 75 and not self._recent_backup_exists():
            recommendations.append({
                "type": "backup",
                "priority": "medium",
                "title": "Create Data Backup",
                "description": "Your system has valuable data. Create a backup to protect against data loss.",
                "action": "create_backup",
                "icon": "💾",
                "ai_confidence": 0.80
            })
        
        # Performance optimization recommendations
        if performance["mode_switch_frequency"] == "high":
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "title": "Reduce Mode Switching",
                "description": "Frequent mode switching can impact performance. Consider settling on one mode for daily operations.",
                "action": "mode_stabilization",
                "icon": "⚡",
                "ai_confidence": 0.75
            })
        
        # Demo data utilization recommendations
        if current_mode == "demo" and usage_patterns["demo_data_activity"] < 10:
            recommendations.append({
                "type": "training",
                "priority": "low",
                "title": "Explore Demo Features",
                "description": "You're in demo mode but haven't explored much. Try creating work orders and managing assets with sample data.",
                "action": "explore_demo_features",
                "icon": "🎯",
                "ai_confidence": 0.65
            })
        
        # Data migration recommendations
        if (current_mode == "production" and 
            usage_patterns["production_data_activity"] == 0 and 
            usage_patterns["demo_data_activity"] > 0):
            recommendations.append({
                "type": "data_migration",
                "priority": "low",
                "title": "Consider Demo Data Migration",
                "description": "You have demo data but empty production. Consider copying demo data as a starting template.",
                "action": "migrate_demo_data",
                "icon": "📊",
                "ai_confidence": 0.60
            })
        
        return recommendations
    
    def _recent_backup_exists(self) -> bool:
        """Check if a recent backup exists"""
        try:
            mode_history = self.admin.get_mode_switch_history(10)
            recent_backups = [
                entry for entry in mode_history 
                if datetime.fromisoformat(entry["timestamp"]) > datetime.now() - timedelta(days=7)
            ]
            return len(recent_backups) > 0
        except:
            return False
    
    def get_smart_mode_suggestion(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get AI-powered mode suggestion based on context"""
        try:
            overview = self.data_system.get_system_overview()
            analysis = self.analyze_system_usage()
            
            current_mode = get_system_mode()
            optimal_mode = analysis.get("performance_metrics", {}).get("optimal_mode_detected", current_mode)
            
            confidence = 0.5  # Base confidence
            
            # Increase confidence based on factors
            company_setup = overview.get("settings", {}).get("company_setup", {})
            if company_setup.get("completed", False):
                confidence += 0.2
            
            usage_patterns = analysis.get("usage_patterns", {})
            if usage_patterns.get("primary_usage_mode") == optimal_mode:
                confidence += 0.2
            
            data_health = analysis.get("data_health", {})
            if data_health.get("health_score", 0) > 75:
                confidence += 0.1
            
            suggestion = {
                "suggested_mode": optimal_mode,
                "current_mode": current_mode,
                "confidence": min(confidence, 1.0),
                "reasoning": self._get_suggestion_reasoning(current_mode, optimal_mode, analysis),
                "benefits": self._get_mode_benefits(optimal_mode),
                "estimated_impact": self._estimate_mode_impact(current_mode, optimal_mode),
                "ai_analysis": analysis
            }
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error getting smart mode suggestion: {e}")
            return {
                "suggested_mode": current_mode,
                "current_mode": current_mode,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _get_suggestion_reasoning(self, current_mode: str, optimal_mode: str, analysis: Dict[str, Any]) -> List[str]:
        """Generate reasoning for mode suggestion"""
        reasoning = []
        
        if current_mode == optimal_mode:
            reasoning.append(f"Current {current_mode} mode is optimal for your usage patterns")
        else:
            if optimal_mode == "production":
                reasoning.append("Company setup is complete and ready for live operations")
                reasoning.append("Production mode provides full functionality and data persistence")
            else:
                reasoning.append("Demo mode recommended for training and testing")
                reasoning.append("Demo mode provides safe environment with sample data")
        
        usage_patterns = analysis.get("usage_patterns", {})
        if usage_patterns.get("mode_switches_count", 0) > 5:
            reasoning.append("High mode switch frequency detected - consider stabilizing on one mode")
        
        data_health = analysis.get("data_health", {})
        if data_health.get("health_score", 0) < 50:
            reasoning.append("Data health issues detected - review database integrity")
        
        return reasoning
    
    def _get_mode_benefits(self, mode: str) -> List[str]:
        """Get benefits of specified mode"""
        if mode == "demo":
            return [
                "Safe testing environment with TechFlow Manufacturing Corp sample data",
                "Full CRUD operations without affecting real data",
                "Training and workflow testing capabilities",
                "Easy data reset for clean testing",
                "Risk-free experimentation"
            ]
        else:
            return [
                "Real company data and live operations",
                "Full system functionality and integrations",
                "Data persistence and backup systems",
                "Production-grade security and audit trails",
                "Custom workflows and configurations"
            ]
    
    def _estimate_mode_impact(self, current_mode: str, target_mode: str) -> Dict[str, Any]:
        """Estimate impact of switching modes"""
        if current_mode == target_mode:
            return {"impact_level": "none", "description": "No change required"}
        
        if target_mode == "production":
            return {
                "impact_level": "medium",
                "description": "Switch to live operations with real data",
                "data_impact": "Production database will be used",
                "functionality_impact": "Full features enabled",
                "risk_level": "medium"
            }
        else:
            return {
                "impact_level": "low",
                "description": "Switch to safe demo environment",
                "data_impact": "Demo database with sample data",
                "functionality_impact": "Training mode with mock data",
                "risk_level": "low"
            }

# Global AI brain integration instance
ai_brain_integration = AIBrainDataModeIntegration()

# Convenience functions
def get_ai_mode_analysis() -> Dict[str, Any]:
    """Get AI analysis of current data mode usage"""
    return ai_brain_integration.analyze_system_usage()

def get_smart_mode_suggestion(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get AI-powered mode suggestion"""
    return ai_brain_integration.get_smart_mode_suggestion(context)

def get_ai_recommendations() -> List[Dict[str, Any]]:
    """Get AI-powered recommendations"""
    analysis = ai_brain_integration.analyze_system_usage()
    return analysis.get("recommendations", [])

if __name__ == "__main__":
    # Test the AI brain integration
    print("🧠 ChatterFix CMMS AI Brain Data Mode Integration")
    print("=" * 60)
    
    integration = AIBrainDataModeIntegration()
    
    # Get analysis
    analysis = integration.analyze_system_usage()
    print(f"Current mode: {analysis.get('current_mode', 'unknown')}")
    
    # Get recommendations
    recommendations = analysis.get("recommendations", [])
    print(f"AI recommendations: {len(recommendations)}")
    
    for rec in recommendations:
        print(f"  {rec.get('icon', '💡')} {rec.get('title', 'Recommendation')} ({rec.get('priority', 'medium')})")
        print(f"    Confidence: {rec.get('ai_confidence', 0.5):.0%}")
    
    # Get smart suggestion
    suggestion = integration.get_smart_mode_suggestion()
    print(f"\nSmart suggestion: {suggestion.get('suggested_mode', 'unknown')}")
    print(f"Confidence: {suggestion.get('confidence', 0):.0%}")