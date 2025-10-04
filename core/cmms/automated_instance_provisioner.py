#!/usr/bin/env python3
"""
Automated Instance Provisioning Engine
Advanced Business Automation for ChatterFix CMMS Platform

This engine handles natural language business commands and automatically:
- Provisions new ChatterFix instances
- Sets up billing and subscriptions
- Configures access controls and user roles
- Manages multi-tenant security
- Orchestrates deployment across cloud providers
"""

import asyncio
import json
import os
import uuid
import logging
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

import httpx
import yaml
from pydantic import BaseModel, Field

# Import our Natural Language Processor
from natural_language_processor import NaturalLanguageProcessor, CommandIntent, BusinessProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProvisioningStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONFIGURING = "configuring"
    DEPLOYING = "deploying"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"

class CloudProvider(Enum):
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"
    MULTI_CLOUD = "multi_cloud"

@dataclass
class InstanceConfiguration:
    """Configuration for a new ChatterFix instance"""
    business_name: str
    contact_email: str
    industry: str
    team_size: int
    deployment_size: str  # small, medium, large, enterprise
    cloud_provider: CloudProvider
    region: str
    instance_id: str
    subdomain: str
    billing_plan: str
    features: List[str]
    security_level: str
    backup_frequency: str
    monitoring_level: str
    ai_capabilities: List[str]
    integrations: List[str]
    compliance_requirements: List[str]

@dataclass
class ProvisioningTask:
    """Individual provisioning task"""
    task_id: str
    instance_id: str
    task_type: str
    description: str
    status: ProvisioningStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    dependencies: List[str]
    estimated_duration: int  # minutes
    actual_duration: Optional[int] = None
    error_message: Optional[str] = None

class AutomatedInstanceProvisioner:
    """
    Advanced automated provisioning engine that can:
    1. Parse natural language business commands
    2. Create intelligent deployment configurations
    3. Provision infrastructure across multiple cloud providers
    4. Set up billing, security, and monitoring
    5. Configure user access and roles
    6. Handle multi-tenant deployment patterns
    """
    
    def __init__(self):
        self.nlp_processor = NaturalLanguageProcessor()
        self.active_provisioning_tasks: Dict[str, List[ProvisioningTask]] = {}
        self.completed_instances: Dict[str, InstanceConfiguration] = {}
        self.provisioning_templates: Dict[str, Dict[str, Any]] = {}
        self._load_provisioning_templates()
        
    def _load_provisioning_templates(self):
        """Load deployment templates for different business sizes and industries"""
        self.provisioning_templates = {
            "small_business": {
                "cpu": 2,
                "memory": "4Gi",
                "storage": "50Gi",
                "replicas": 1,
                "auto_scaling": {"min": 1, "max": 3},
                "features": ["basic_cmms", "work_orders", "asset_management", "basic_reporting"],
                "ai_models": ["llama3.2:latest"],
                "billing_plan": "starter",
                "estimated_cost": 150
            },
            "medium_business": {
                "cpu": 4,
                "memory": "8Gi", 
                "storage": "200Gi",
                "replicas": 2,
                "auto_scaling": {"min": 2, "max": 6},
                "features": ["full_cmms", "work_orders", "asset_management", "advanced_reporting", "predictive_maintenance"],
                "ai_models": ["llama3.2:latest", "codegemma:latest"],
                "billing_plan": "professional",
                "estimated_cost": 400
            },
            "large_business": {
                "cpu": 8,
                "memory": "16Gi",
                "storage": "500Gi", 
                "replicas": 3,
                "auto_scaling": {"min": 3, "max": 10},
                "features": ["enterprise_cmms", "work_orders", "asset_management", "advanced_reporting", "predictive_maintenance", "custom_workflows", "api_access"],
                "ai_models": ["llama3.2:latest", "codegemma:latest", "mistral:latest"],
                "billing_plan": "enterprise",
                "estimated_cost": 900
            },
            "enterprise": {
                "cpu": 16,
                "memory": "32Gi",
                "storage": "1Ti",
                "replicas": 5,
                "auto_scaling": {"min": 5, "max": 20},
                "features": ["enterprise_cmms", "work_orders", "asset_management", "advanced_reporting", "predictive_maintenance", "custom_workflows", "api_access", "white_label", "sso_integration"],
                "ai_models": ["llama3.2:latest", "codegemma:latest", "mistral:latest", "phi3:latest"],
                "billing_plan": "enterprise_plus",
                "estimated_cost": 2500
            }
        }

    async def process_business_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process natural language business commands like:
        - "Deploy a ChatterFix instance for Joe's Garage"
        - "Create a new CMMS system for ABC Manufacturing with predictive maintenance"
        - "Set up ChatterFix for Small Town Auto Repair with 5 technicians"
        """
        logger.info(f"Processing business command: {command}")
        
        try:
            # Use Natural Language Processor to understand the command
            result = await self.nlp_processor.process_command(command, context or {})
            
            intent_action = result.get("intent", {}).get("action", "")
            
            if intent_action == "deploy":
                return await self._handle_deployment_request(result, command)
            elif intent_action == "billing":
                return await self._handle_billing_request(result, command)
            elif intent_action == "access":
                return await self._handle_access_request(result, command)
            elif intent_action == "scale":
                return await self._handle_scaling_request(result, command)
            else:
                return {
                    "status": "error",
                    "message": f"Command intent '{result['intent']}' not supported by provisioning engine",
                    "suggestions": [
                        "Try: 'Deploy ChatterFix for [Business Name]'",
                        "Try: 'Create CMMS instance for [Company] with [features]'",
                        "Try: 'Set up billing for [Business Name]'"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error processing business command: {e}")
            return {
                "status": "error",
                "message": f"Failed to process command: {str(e)}",
                "command": command
            }

    async def _handle_deployment_request(self, nlp_result: Dict[str, Any], original_command: str) -> Dict[str, Any]:
        """Handle deployment requests with intelligent configuration"""
        entities = nlp_result.get("entities", {})
        business_profile = nlp_result.get("business_profile", {})
        
        # Extract key information
        business_name = entities.get("business_name", "Unknown Business")
        industry = entities.get("industry", business_profile.get("industry", "general"))
        team_size = entities.get("team_size", business_profile.get("team_size", 5))
        
        # Determine deployment size based on business intelligence
        deployment_size = self._determine_deployment_size(business_profile)
        
        # Generate unique instance configuration
        instance_config = await self._create_instance_configuration(
            business_name=business_name,
            industry=industry, 
            team_size=team_size,
            deployment_size=deployment_size,
            business_profile=business_profile,
            entities=entities
        )
        
        # Create provisioning plan
        provisioning_plan = await self._create_provisioning_plan(instance_config)
        
        # Start automated provisioning
        provisioning_id = await self._start_provisioning(instance_config, provisioning_plan)
        
        return {
            "status": "success",
            "message": f"Starting automated deployment for {business_name}",
            "provisioning_id": provisioning_id,
            "instance_config": asdict(instance_config),
            "provisioning_plan": provisioning_plan,
            "estimated_completion": (datetime.now() + timedelta(minutes=provisioning_plan.get("total_duration", 45))).isoformat(),
            "estimated_cost": provisioning_plan.get("estimated_monthly_cost", 150),
            "next_steps": [
                "Infrastructure provisioning has begun",
                "Database and storage setup in progress", 
                "ChatterFix application deployment starting",
                "Security and access controls being configured",
                "Billing and subscription setup initiated",
                "You'll receive email updates at each milestone"
            ]
        }

    def _determine_deployment_size(self, business_profile: Dict[str, Any]) -> str:
        """Intelligently determine deployment size based on business profile"""
        team_size = business_profile.get("team_size", 5)
        revenue = business_profile.get("estimated_revenue", 0)
        complexity = business_profile.get("complexity_score", 5)
        
        if team_size >= 100 or revenue >= 10000000 or complexity >= 9:
            return "enterprise"
        elif team_size >= 25 or revenue >= 1000000 or complexity >= 7:
            return "large_business"
        elif team_size >= 10 or revenue >= 250000 or complexity >= 5:
            return "medium_business"
        else:
            return "small_business"

    async def _create_instance_configuration(self, business_name: str, industry: str, team_size: int, deployment_size: str, business_profile: Dict[str, Any], entities: Dict[str, Any]) -> InstanceConfiguration:
        """Create intelligent instance configuration"""
        instance_id = f"cf-{uuid.uuid4().hex[:8]}"
        subdomain = business_name.lower().replace(" ", "-").replace("'", "")[:20]
        
        template = self.provisioning_templates[deployment_size]
        
        # Determine cloud provider based on preferences or industry best practices
        cloud_provider = self._select_optimal_cloud_provider(industry, business_profile)
        
        # Select region based on business location or preferences
        region = self._select_optimal_region(entities.get("location"), cloud_provider)
        
        # Customize features based on industry and requirements
        features = self._customize_features_for_industry(template["features"], industry, entities)
        
        # Select AI capabilities based on team size and complexity
        ai_capabilities = self._select_ai_capabilities(deployment_size, industry, entities)
        
        return InstanceConfiguration(
            business_name=business_name,
            contact_email=entities.get("email", "admin@" + subdomain + ".com"),
            industry=industry,
            team_size=team_size,
            deployment_size=deployment_size,
            cloud_provider=cloud_provider,
            region=region,
            instance_id=instance_id,
            subdomain=subdomain,
            billing_plan=template["billing_plan"],
            features=features,
            security_level=self._determine_security_level(industry, deployment_size),
            backup_frequency=self._determine_backup_frequency(deployment_size),
            monitoring_level=self._determine_monitoring_level(deployment_size),
            ai_capabilities=ai_capabilities,
            integrations=self._suggest_integrations(industry, entities),
            compliance_requirements=self._determine_compliance_requirements(industry)
        )

    def _select_optimal_cloud_provider(self, industry: str, business_profile: Dict[str, Any]) -> CloudProvider:
        """Select optimal cloud provider based on industry and requirements"""
        # Industry-specific cloud preferences
        industry_preferences = {
            "healthcare": CloudProvider.AWS,  # HIPAA compliance
            "finance": CloudProvider.AZURE,   # Financial services focus
            "government": CloudProvider.GCP,  # Government cloud offerings
            "manufacturing": CloudProvider.AWS,  # Industrial IoT capabilities
            "retail": CloudProvider.GCP,      # Analytics and ML
            "automotive": CloudProvider.AZURE, # Manufacturing partnerships
        }
        
        return industry_preferences.get(industry, CloudProvider.GCP)

    def _select_optimal_region(self, location: Optional[str], cloud_provider: CloudProvider) -> str:
        """Select optimal deployment region"""
        if not location:
            return "us-central1"  # Default
            
        # Location-based region mapping
        location_lower = location.lower()
        
        if cloud_provider == CloudProvider.GCP:
            if any(term in location_lower for term in ["west", "california", "oregon", "washington"]):
                return "us-west1"
            elif any(term in location_lower for term in ["east", "new york", "virginia", "georgia"]):
                return "us-east1"
            elif any(term in location_lower for term in ["europe", "uk", "germany", "france"]):
                return "europe-west1"
            elif any(term in location_lower for term in ["asia", "japan", "singapore", "taiwan"]):
                return "asia-northeast1"
        
        return "us-central1"

    def _customize_features_for_industry(self, base_features: List[str], industry: str, entities: Dict[str, Any]) -> List[str]:
        """Customize features based on industry requirements"""
        features = base_features.copy()
        
        industry_features = {
            "manufacturing": ["equipment_monitoring", "production_scheduling", "quality_control"],
            "automotive": ["fleet_management", "service_scheduling", "parts_tracking"],
            "healthcare": ["medical_equipment_tracking", "compliance_reporting", "sanitation_scheduling"],
            "construction": ["project_management", "equipment_rental", "safety_compliance"],
            "retail": ["store_maintenance", "pos_integration", "inventory_tracking"],
            "hospitality": ["room_maintenance", "guest_services", "food_safety"]
        }
        
        if industry in industry_features:
            features.extend(industry_features[industry])
        
        # Add requested features from entities
        requested_features = entities.get("requested_features", [])
        features.extend(requested_features)
        
        return list(set(features))  # Remove duplicates

    def _select_ai_capabilities(self, deployment_size: str, industry: str, entities: Dict[str, Any]) -> List[str]:
        """Select AI capabilities based on deployment size and industry"""
        base_capabilities = ["natural_language_processing", "work_order_assistance"]
        
        if deployment_size in ["medium_business", "large_business", "enterprise"]:
            base_capabilities.extend(["predictive_maintenance", "intelligent_scheduling"])
        
        if deployment_size in ["large_business", "enterprise"]:
            base_capabilities.extend(["advanced_analytics", "custom_ai_workflows"])
            
        if deployment_size == "enterprise":
            base_capabilities.extend(["multi_provider_ai", "custom_model_training"])
        
        # Industry-specific AI capabilities
        industry_ai = {
            "manufacturing": ["production_optimization", "quality_prediction"],
            "automotive": ["diagnostic_assistance", "maintenance_prediction"],
            "healthcare": ["equipment_lifecycle_analysis", "compliance_monitoring"],
            "construction": ["project_risk_analysis", "resource_optimization"]
        }
        
        if industry in industry_ai:
            base_capabilities.extend(industry_ai[industry])
        
        return list(set(base_capabilities))

    def _determine_security_level(self, industry: str, deployment_size: str) -> str:
        """Determine security level based on industry and deployment size"""
        high_security_industries = ["healthcare", "finance", "government", "legal"]
        
        if industry in high_security_industries:
            return "enterprise"
        elif deployment_size == "enterprise":
            return "high"
        elif deployment_size in ["large_business", "medium_business"]:
            return "standard"
        else:
            return "basic"

    def _determine_backup_frequency(self, deployment_size: str) -> str:
        """Determine backup frequency based on deployment size"""
        backup_schedule = {
            "small_business": "daily",
            "medium_business": "twice_daily", 
            "large_business": "hourly",
            "enterprise": "continuous"
        }
        return backup_schedule.get(deployment_size, "daily")

    def _determine_monitoring_level(self, deployment_size: str) -> str:
        """Determine monitoring level based on deployment size"""
        monitoring_levels = {
            "small_business": "basic",
            "medium_business": "standard",
            "large_business": "advanced", 
            "enterprise": "comprehensive"
        }
        return monitoring_levels.get(deployment_size, "basic")

    def _suggest_integrations(self, industry: str, entities: Dict[str, Any]) -> List[str]:
        """Suggest relevant integrations based on industry"""
        base_integrations = ["email", "calendar"]
        
        industry_integrations = {
            "manufacturing": ["erp_systems", "scada", "mes"],
            "automotive": ["dealer_management", "parts_suppliers", "warranty_systems"],
            "healthcare": ["emr_systems", "medical_devices", "compliance_platforms"],
            "construction": ["project_management", "accounting", "safety_systems"],
            "retail": ["pos_systems", "inventory_management", "customer_service"],
            "hospitality": ["pms", "booking_systems", "guest_services"]
        }
        
        if industry in industry_integrations:
            base_integrations.extend(industry_integrations[industry])
        
        return base_integrations

    def _determine_compliance_requirements(self, industry: str) -> List[str]:
        """Determine compliance requirements based on industry"""
        compliance_map = {
            "healthcare": ["HIPAA", "FDA", "HITECH"],
            "finance": ["SOX", "PCI_DSS", "GLBA"],
            "government": ["FedRAMP", "FISMA", "NIST"],
            "manufacturing": ["ISO_9001", "OSHA", "EPA"],
            "automotive": ["ISO_TS_16949", "NHTSA", "EPA"],
            "construction": ["OSHA", "EPA", "DOT"]
        }
        
        return compliance_map.get(industry, ["GDPR", "SOC_2"])

    async def _create_provisioning_plan(self, config: InstanceConfiguration) -> Dict[str, Any]:
        """Create detailed provisioning execution plan"""
        template = self.provisioning_templates[config.deployment_size]
        
        tasks = [
            {"name": "Infrastructure Setup", "duration": 8, "type": "infrastructure"},
            {"name": "Database Configuration", "duration": 5, "type": "database"},
            {"name": "Application Deployment", "duration": 10, "type": "application"},
            {"name": "Security Configuration", "duration": 7, "type": "security"},
            {"name": "AI Models Setup", "duration": 12, "type": "ai_setup"},
            {"name": "Integration Configuration", "duration": 8, "type": "integrations"},
            {"name": "Billing Setup", "duration": 3, "type": "billing"},
            {"name": "User Access Configuration", "duration": 5, "type": "access"},
            {"name": "Monitoring Setup", "duration": 4, "type": "monitoring"},
            {"name": "Testing & Validation", "duration": 8, "type": "testing"}
        ]
        
        return {
            "tasks": tasks,
            "total_duration": sum(task["duration"] for task in tasks),
            "estimated_monthly_cost": template["estimated_cost"],
            "resource_requirements": {
                "cpu": template["cpu"],
                "memory": template["memory"],
                "storage": template["storage"],
                "replicas": template["replicas"]
            },
            "deployment_strategy": "blue_green" if config.deployment_size in ["large_business", "enterprise"] else "rolling",
            "rollback_plan": "automated_rollback_on_failure",
            "success_criteria": [
                "All health checks passing",
                "Database connectivity verified",
                "AI models responding",
                "User authentication working",
                "Billing integration active"
            ]
        }

    async def _start_provisioning(self, config: InstanceConfiguration, plan: Dict[str, Any]) -> str:
        """Start the automated provisioning process"""
        provisioning_id = f"prov-{uuid.uuid4().hex[:8]}"
        
        # Create provisioning tasks
        tasks = []
        for i, task_info in enumerate(plan["tasks"]):
            task = ProvisioningTask(
                task_id=f"{provisioning_id}-task-{i+1:02d}",
                instance_id=config.instance_id,
                task_type=task_info["type"],
                description=task_info["name"],
                status=ProvisioningStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={"config": asdict(config)},
                dependencies=[],
                estimated_duration=task_info["duration"]
            )
            tasks.append(task)
        
        self.active_provisioning_tasks[provisioning_id] = tasks
        
        # Start background provisioning
        asyncio.create_task(self._execute_provisioning(provisioning_id, config, plan))
        
        logger.info(f"Started provisioning {provisioning_id} for {config.business_name}")
        return provisioning_id

    async def _execute_provisioning(self, provisioning_id: str, config: InstanceConfiguration, plan: Dict[str, Any]):
        """Execute the actual provisioning steps"""
        tasks = self.active_provisioning_tasks[provisioning_id]
        
        try:
            for task in tasks:
                task.status = ProvisioningStatus.IN_PROGRESS
                task.updated_at = datetime.now()
                
                logger.info(f"Executing task: {task.description}")
                
                # Execute specific provisioning step
                success = await self._execute_provisioning_task(task, config)
                
                if success:
                    task.status = ProvisioningStatus.COMPLETED
                    task.actual_duration = task.estimated_duration  # Simplified for now
                else:
                    task.status = ProvisioningStatus.FAILED
                    task.error_message = f"Failed to execute {task.description}"
                    break
                
                task.updated_at = datetime.now()
                
                # Brief delay between tasks
                await asyncio.sleep(2)
            
            # Check if all tasks completed successfully
            if all(task.status == ProvisioningStatus.COMPLETED for task in tasks):
                logger.info(f"Provisioning {provisioning_id} completed successfully")
                self.completed_instances[config.instance_id] = config
                
                # Notify completion (would integrate with notification system)
                await self._notify_provisioning_completion(config, provisioning_id)
            else:
                logger.error(f"Provisioning {provisioning_id} failed")
                
        except Exception as e:
            logger.error(f"Provisioning {provisioning_id} failed with error: {e}")
            for task in tasks:
                if task.status == ProvisioningStatus.IN_PROGRESS:
                    task.status = ProvisioningStatus.FAILED
                    task.error_message = str(e)

    async def _execute_provisioning_task(self, task: ProvisioningTask, config: InstanceConfiguration) -> bool:
        """Execute individual provisioning task"""
        # This would contain actual provisioning logic
        # For now, simulating with delays and logging
        
        logger.info(f"Executing {task.task_type}: {task.description}")
        
        if task.task_type == "infrastructure":
            return await self._setup_infrastructure(config)
        elif task.task_type == "database":
            return await self._setup_database(config)
        elif task.task_type == "application":
            return await self._deploy_application(config)
        elif task.task_type == "security":
            return await self._configure_security(config)
        elif task.task_type == "ai_setup":
            return await self._setup_ai_models(config)
        elif task.task_type == "integrations":
            return await self._configure_integrations(config)
        elif task.task_type == "billing":
            return await self._setup_billing(config)
        elif task.task_type == "access":
            return await self._configure_access(config)
        elif task.task_type == "monitoring":
            return await self._setup_monitoring(config)
        elif task.task_type == "testing":
            return await self._run_tests(config)
        
        return True

    async def _setup_infrastructure(self, config: InstanceConfiguration) -> bool:
        """Set up cloud infrastructure"""
        logger.info(f"Setting up {config.cloud_provider.value} infrastructure in {config.region}")
        # Simulate infrastructure setup
        await asyncio.sleep(3)
        return True

    async def _setup_database(self, config: InstanceConfiguration) -> bool:
        """Set up database"""
        logger.info(f"Setting up database for {config.instance_id}")
        # Simulate database setup
        await asyncio.sleep(2)
        return True

    async def _deploy_application(self, config: InstanceConfiguration) -> bool:
        """Deploy ChatterFix application"""
        logger.info(f"Deploying ChatterFix application for {config.business_name}")
        # Simulate application deployment
        await asyncio.sleep(4)
        return True

    async def _configure_security(self, config: InstanceConfiguration) -> bool:
        """Configure security settings"""
        logger.info(f"Configuring {config.security_level} security level")
        # Simulate security configuration
        await asyncio.sleep(3)
        return True

    async def _setup_ai_models(self, config: InstanceConfiguration) -> bool:
        """Set up AI models"""
        logger.info(f"Setting up AI capabilities: {config.ai_capabilities}")
        # Simulate AI model setup
        await asyncio.sleep(5)
        return True

    async def _configure_integrations(self, config: InstanceConfiguration) -> bool:
        """Configure integrations"""
        logger.info(f"Configuring integrations: {config.integrations}")
        # Simulate integration setup
        await asyncio.sleep(3)
        return True

    async def _setup_billing(self, config: InstanceConfiguration) -> bool:
        """Set up billing and subscription"""
        logger.info(f"Setting up {config.billing_plan} billing plan")
        # Simulate billing setup
        await asyncio.sleep(2)
        return True

    async def _configure_access(self, config: InstanceConfiguration) -> bool:
        """Configure user access and roles"""
        logger.info(f"Configuring access for team of {config.team_size}")
        # Simulate access configuration
        await asyncio.sleep(2)
        return True

    async def _setup_monitoring(self, config: InstanceConfiguration) -> bool:
        """Set up monitoring and alerting"""
        logger.info(f"Setting up {config.monitoring_level} monitoring")
        # Simulate monitoring setup
        await asyncio.sleep(2)
        return True

    async def _run_tests(self, config: InstanceConfiguration) -> bool:
        """Run deployment tests"""
        logger.info(f"Running tests for {config.instance_id}")
        # Simulate testing
        await asyncio.sleep(3)
        return True

    async def _notify_provisioning_completion(self, config: InstanceConfiguration, provisioning_id: str):
        """Notify stakeholders of completed provisioning"""
        logger.info(f"✅ ChatterFix instance ready for {config.business_name}")
        logger.info(f"🌐 Access URL: https://{config.subdomain}.chatterfix.com")
        logger.info(f"📧 Admin email: {config.contact_email}")
        logger.info(f"💰 Monthly cost: ${self.provisioning_templates[config.deployment_size]['estimated_cost']}")

    async def get_provisioning_status(self, provisioning_id: str) -> Dict[str, Any]:
        """Get status of active provisioning"""
        if provisioning_id not in self.active_provisioning_tasks:
            return {"error": "Provisioning ID not found"}
        
        tasks = self.active_provisioning_tasks[provisioning_id]
        completed_tasks = [t for t in tasks if t.status == ProvisioningStatus.COMPLETED]
        failed_tasks = [t for t in tasks if t.status == ProvisioningStatus.FAILED]
        in_progress_tasks = [t for t in tasks if t.status == ProvisioningStatus.IN_PROGRESS]
        
        progress_percentage = (len(completed_tasks) / len(tasks)) * 100
        
        return {
            "provisioning_id": provisioning_id,
            "status": "failed" if failed_tasks else ("completed" if len(completed_tasks) == len(tasks) else "in_progress"),
            "progress_percentage": progress_percentage,
            "completed_tasks": len(completed_tasks),
            "total_tasks": len(tasks),
            "current_task": in_progress_tasks[0].description if in_progress_tasks else None,
            "estimated_completion": self._estimate_completion_time(tasks),
            "tasks": [
                {
                    "description": task.description,
                    "status": task.status.value,
                    "duration": task.actual_duration or task.estimated_duration,
                    "error": task.error_message
                }
                for task in tasks
            ]
        }

    def _estimate_completion_time(self, tasks: List[ProvisioningTask]) -> Optional[str]:
        """Estimate completion time for remaining tasks"""
        remaining_tasks = [t for t in tasks if t.status in [ProvisioningStatus.PENDING, ProvisioningStatus.IN_PROGRESS]]
        if not remaining_tasks:
            return None
        
        remaining_duration = sum(t.estimated_duration for t in remaining_tasks)
        estimated_completion = datetime.now() + timedelta(minutes=remaining_duration)
        return estimated_completion.isoformat()

    async def _handle_billing_request(self, nlp_result: Dict[str, Any], original_command: str) -> Dict[str, Any]:
        """Handle billing and subscription management requests"""
        return {
            "status": "success",
            "message": "Billing management functionality will be implemented next",
            "capabilities": ["subscription_setup", "billing_automation", "cost_optimization"]
        }

    async def _handle_access_request(self, nlp_result: Dict[str, Any], original_command: str) -> Dict[str, Any]:
        """Handle access control and user management requests"""
        return {
            "status": "success", 
            "message": "Access control functionality will be implemented next",
            "capabilities": ["user_management", "role_assignment", "security_policies"]
        }

    async def _handle_scaling_request(self, nlp_result: Dict[str, Any], original_command: str) -> Dict[str, Any]:
        """Handle resource scaling requests"""
        return {
            "status": "success",
            "message": "Resource scaling functionality will be implemented next", 
            "capabilities": ["auto_scaling", "resource_optimization", "performance_tuning"]
        }


# Test the provisioner
async def test_provisioner():
    """Test the automated provisioning engine"""
    provisioner = AutomatedInstanceProvisioner()
    
    test_commands = [
        "Deploy a ChatterFix instance for Joe's Garage with 8 mechanics",
        "Create a new CMMS system for ABC Manufacturing with predictive maintenance",
        "Set up ChatterFix for Small Town Auto Repair with basic features",
        "Deploy enterprise ChatterFix for MegaCorp Industries with 200 users"
    ]
    
    for command in test_commands:
        print(f"\n🔄 Testing: {command}")
        result = await provisioner.process_business_command(command)
        print(f"✅ Result: {result['message']}")
        if result.get("provisioning_id"):
            print(f"📋 Provisioning ID: {result['provisioning_id']}")
            
            # Check status after a moment
            await asyncio.sleep(5)
            status = await provisioner.get_provisioning_status(result["provisioning_id"])
            print(f"📊 Progress: {status['progress_percentage']:.1f}%")


if __name__ == "__main__":
    asyncio.run(test_provisioner())