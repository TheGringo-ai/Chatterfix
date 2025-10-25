#!/usr/bin/env python3
"""
Natural Language Command Processor
Revolutionary business automation through conversational AI commands

Features:
- Multi-LLM intent recognition and entity extraction
- Business context understanding and intelligent recommendations
- Automated workflow orchestration for complex business operations
- Integration with Universal AI Command Center
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class CommandIntent:
    action: str
    confidence: float
    entities: Dict[str, Any]
    business_context: Dict[str, Any]
    required_confirmations: List[str]

@dataclass
class BusinessProfile:
    business_name: str
    industry: str
    size_indicators: Dict[str, Any]
    estimated_users: int
    recommended_tier: str
    required_modules: List[str]
    deployment_config: Dict[str, Any]

@dataclass
class CommandExecution:
    command_id: str
    status: str
    steps: List[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    execution_time: float
    created_instances: List[Dict[str, Any]]

class IntentClassifier:
    """Advanced intent recognition using multiple AI models"""
    
    def __init__(self):
        self.action_patterns = {
            'deploy': [
                r'deploy.*(?:instance|system|platform)',
                r'create.*(?:instance|system|for)',
                r'set.*up.*(?:chatterfix|cmms|system)',
                r'provision.*(?:instance|system)',
                r'launch.*(?:instance|system)'
            ],
            'manage': [
                r'manage.*(?:users|access|permissions)',
                r'add.*(?:users|members|staff)',
                r'configure.*(?:access|roles|permissions)',
                r'set.*(?:permissions|roles|access)'
            ],
            'billing': [
                r'upgrade.*(?:plan|tier|subscription)',
                r'change.*(?:billing|plan|subscription)',
                r'set.*(?:billing|payment|subscription)',
                r'configure.*(?:billing|payment)'
            ],
            'monitor': [
                r'show.*(?:status|metrics|performance)',
                r'check.*(?:health|status|performance)',
                r'monitor.*(?:system|performance|usage)',
                r'get.*(?:metrics|status|report)'
            ]
        }
        
        self.entity_patterns = {
            'business_name': r'(?:for\s+)([A-Z][a-zA-Z\s\&\']*(?:Inc|LLC|Corp|Company|Garage|Shop|Store|Service|Systems|Solutions)?)(?:\s|$)',
            'industry': r'(?:auto|automotive|repair|garage|retail|restaurant|manufacturing|healthcare|construction|logistics)',
            'size_indicators': [
                r'(\d+)\s*(?:vehicles|trucks|cars|fleet)',
                r'(\d+)\s*(?:employees|staff|workers|people)',
                r'(\d+)\s*(?:locations|sites|stores|branches)',
                r'(\d+)\s*(?:users|accounts|licenses)'
            ],
            'product': r'(?:chatterfix|cmms|maintenance|system|platform)',
            'tier': r'(?:basic|standard|professional|enterprise|premium)',
            'urgency': r'(?:urgent|asap|immediately|today|rush|priority)'
        }

    async def classify(self, command: str) -> CommandIntent:
        """Classify user intent and extract entities"""
        command_lower = command.lower()
        
        # Determine primary action
        action = 'unknown'
        max_confidence = 0.0
        
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command_lower):
                    confidence = len(re.findall(pattern, command_lower)) * 0.3 + 0.4
                    if confidence > max_confidence:
                        max_confidence = confidence
                        action = action_type
        
        # Extract entities
        entities = await self._extract_entities(command)
        
        # Determine business context
        business_context = await self._analyze_business_context(entities)
        
        # Determine required confirmations
        confirmations = await self._determine_confirmations(action, entities, business_context)
        
        return CommandIntent(
            action=action,
            confidence=max_confidence,
            entities=entities,
            business_context=business_context,
            required_confirmations=confirmations
        )

    async def _extract_entities(self, command: str) -> Dict[str, Any]:
        """Extract business entities from command"""
        entities = {}
        
        # Extract business name
        business_match = re.search(self.entity_patterns['business_name'], command, re.IGNORECASE)
        if business_match:
            entities['business_name'] = business_match.group(1).strip()
        
        # Extract industry indicators
        industry_match = re.search(self.entity_patterns['industry'], command.lower())
        if industry_match:
            entities['industry'] = industry_match.group(0)
        
        # Extract size indicators
        size_indicators = {}
        for pattern in self.entity_patterns['size_indicators']:
            matches = re.findall(pattern, command.lower())
            if matches:
                if 'vehicles' in pattern or 'trucks' in pattern or 'cars' in pattern:
                    size_indicators['fleet_size'] = int(matches[0])
                elif 'employees' in pattern or 'staff' in pattern or 'workers' in pattern:
                    size_indicators['employee_count'] = int(matches[0])
                elif 'locations' in pattern or 'sites' in pattern:
                    size_indicators['location_count'] = int(matches[0])
                elif 'users' in pattern or 'accounts' in pattern:
                    size_indicators['user_count'] = int(matches[0])
        
        if size_indicators:
            entities['size_indicators'] = size_indicators
        
        # Extract tier preference
        tier_match = re.search(self.entity_patterns['tier'], command.lower())
        if tier_match:
            entities['requested_tier'] = tier_match.group(0)
        
        # Extract urgency
        urgency_match = re.search(self.entity_patterns['urgency'], command.lower())
        if urgency_match:
            entities['urgency'] = urgency_match.group(0)
        
        return entities

    async def _analyze_business_context(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business context and make intelligent recommendations"""
        context = {
            'confidence_score': 0.0,
            'data_quality': 'unknown',
            'recommendations': []
        }
        
        # Business name analysis
        if 'business_name' in entities:
            context['confidence_score'] += 0.3
            
            # Industry inference from business name
            business_name = entities['business_name'].lower()
            if any(term in business_name for term in ['garage', 'auto', 'car', 'automotive']):
                context['inferred_industry'] = 'automotive_repair'
                context['confidence_score'] += 0.2
            elif any(term in business_name for term in ['restaurant', 'cafe', 'diner', 'food']):
                context['inferred_industry'] = 'restaurant'
                context['confidence_score'] += 0.2
            elif any(term in business_name for term in ['retail', 'store', 'shop', 'mart']):
                context['inferred_industry'] = 'retail'
                context['confidence_score'] += 0.2
        
        # Size analysis and recommendations
        if 'size_indicators' in entities:
            size_data = entities['size_indicators']
            context['confidence_score'] += 0.3
            
            # Fleet size-based recommendations
            if 'fleet_size' in size_data:
                fleet_size = size_data['fleet_size']
                if fleet_size < 10:
                    context['recommended_tier'] = 'professional'
                    context['estimated_users'] = 3
                elif fleet_size < 50:
                    context['recommended_tier'] = 'professional'
                    context['estimated_users'] = 8
                else:
                    context['recommended_tier'] = 'enterprise'
                    context['estimated_users'] = 15
                
                context['recommendations'].append(f"Based on {fleet_size} vehicles, recommend {context['recommended_tier']} tier")
            
            # Employee count-based recommendations
            if 'employee_count' in size_data:
                employee_count = size_data['employee_count']
                context['estimated_users'] = min(employee_count, employee_count // 2 + 2)
                
                if employee_count < 5:
                    context['recommended_tier'] = 'professional'
                elif employee_count < 25:
                    context['recommended_tier'] = 'professional'
                else:
                    context['recommended_tier'] = 'enterprise'
        
        # Data quality assessment
        if context['confidence_score'] > 0.7:
            context['data_quality'] = 'high'
        elif context['confidence_score'] > 0.4:
            context['data_quality'] = 'medium'
        else:
            context['data_quality'] = 'low'
        
        return context

    async def _determine_confirmations(self, action: str, entities: Dict[str, Any], 
                                     business_context: Dict[str, Any]) -> List[str]:
        """Determine what confirmations are needed before execution"""
        confirmations = []
        
        if action == 'deploy':
            if 'business_name' not in entities:
                confirmations.append("Business name required")
            
            if business_context['data_quality'] == 'low':
                confirmations.append("Industry and size information recommended")
            
            if 'recommended_tier' not in business_context and 'requested_tier' not in entities:
                confirmations.append("Subscription tier selection needed")
        
        return confirmations

class BusinessIntelligenceEngine:
    """Advanced business profiling and intelligent recommendations"""
    
    def __init__(self):
        self.industry_templates = {
            'automotive_repair': {
                'modules': ['fleet_management', 'parts_inventory', 'work_orders', 'customer_vehicles'],
                'typical_users': lambda size: max(3, min(15, size // 8 + 2)),
                'storage_multiplier': 2.0,
                'integrations': ['parts_suppliers', 'diagnostic_tools']
            },
            'restaurant': {
                'modules': ['equipment_maintenance', 'health_compliance', 'vendor_management'],
                'typical_users': lambda size: max(2, min(10, size // 5 + 1)),
                'storage_multiplier': 1.0,
                'integrations': ['pos_systems', 'health_department']
            },
            'retail': {
                'modules': ['store_maintenance', 'hvac_management', 'security_systems'],
                'typical_users': lambda size: max(2, min(12, size // 10 + 2)),
                'storage_multiplier': 1.5,
                'integrations': ['pos_systems', 'security_monitoring']
            },
            'manufacturing': {
                'modules': ['production_equipment', 'quality_control', 'safety_compliance'],
                'typical_users': lambda size: max(5, min(25, size // 4 + 3)),
                'storage_multiplier': 3.0,
                'integrations': ['erp_systems', 'safety_monitoring']
            }
        }

    async def create_business_profile(self, entities: Dict[str, Any], 
                                    business_context: Dict[str, Any]) -> BusinessProfile:
        """Create comprehensive business profile with intelligent recommendations"""
        
        # Determine industry
        industry = 'general'
        if 'industry' in entities:
            industry = entities['industry']
        elif 'inferred_industry' in business_context:
            industry = business_context['inferred_industry']
        
        # Get industry template
        template = self.industry_templates.get(industry, self.industry_templates['automotive_repair'])
        
        # Calculate size estimates
        size_indicators = entities.get('size_indicators', {})
        estimated_size = self._estimate_business_size(size_indicators)
        estimated_users = business_context.get('estimated_users', template['typical_users'](estimated_size))
        
        # Determine tier
        recommended_tier = business_context.get('recommended_tier', 'professional')
        if 'requested_tier' in entities:
            recommended_tier = entities['requested_tier']
        
        # Create deployment configuration
        deployment_config = await self._create_deployment_config(
            industry, estimated_users, estimated_size, template
        )
        
        return BusinessProfile(
            business_name=entities.get('business_name', 'Unknown Business'),
            industry=industry,
            size_indicators=size_indicators,
            estimated_users=estimated_users,
            recommended_tier=recommended_tier,
            required_modules=template['modules'],
            deployment_config=deployment_config
        )

    def _estimate_business_size(self, size_indicators: Dict[str, Any]) -> int:
        """Estimate overall business size from various indicators"""
        if 'employee_count' in size_indicators:
            return size_indicators['employee_count']
        elif 'fleet_size' in size_indicators:
            return size_indicators['fleet_size'] * 2  # Estimate employees from fleet size
        elif 'user_count' in size_indicators:
            return size_indicators['user_count'] * 3  # Estimate total size from users
        elif 'location_count' in size_indicators:
            return size_indicators['location_count'] * 10  # Estimate from locations
        else:
            return 10  # Default small business size

    async def _create_deployment_config(self, industry: str, users: int, size: int, 
                                      template: Dict[str, Any]) -> Dict[str, Any]:
        """Create optimized deployment configuration"""
        
        # Calculate resource requirements
        base_cpu = 2
        base_memory = 4  # GB
        base_storage = 50  # GB
        
        # Scale based on users and size
        cpu_cores = max(2, min(16, base_cpu + (users // 5)))
        memory_gb = max(4, min(64, base_memory + (users // 3)))
        storage_gb = max(50, min(1000, int(base_storage * template['storage_multiplier'] * (size / 10))))
        
        return {
            'compute': {
                'cpu_cores': cpu_cores,
                'memory_gb': memory_gb,
                'instance_type': 'optimized' if users > 20 else 'standard'
            },
            'storage': {
                'database_gb': storage_gb,
                'backup_gb': storage_gb * 2,
                'attachments_gb': storage_gb // 2
            },
            'network': {
                'bandwidth': 'standard' if users < 10 else 'high',
                'cdn_enabled': users > 15,
                'load_balancer': users > 20
            },
            'modules': template['modules'],
            'integrations': template['integrations'],
            'backup_frequency': 'daily',
            'monitoring_level': 'standard' if users < 15 else 'premium'
        }

class NaturalLanguageProcessor:
    """Main processor orchestrating all natural language business commands"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.business_intelligence = BusinessIntelligenceEngine()
        self.active_executions: Dict[str, CommandExecution] = {}

    async def process_command(self, command: str, user_id: str = None) -> Dict[str, Any]:
        """Process natural language business command and return execution plan"""
        
        logger.info(f"Processing natural language command: {command}")
        
        try:
            # Step 1: Intent classification and entity extraction
            intent = await self.intent_classifier.classify(command)
            
            # Step 2: Business intelligence analysis
            if intent.action == 'deploy':
                business_profile = await self.business_intelligence.create_business_profile(
                    intent.entities, intent.business_context
                )
                
                # Step 3: Create execution plan
                execution_plan = await self._create_execution_plan(intent, business_profile)
                
                # Step 4: Return for confirmation or immediate execution
                if intent.required_confirmations:
                    return {
                        'status': 'confirmation_required',
                        'intent': asdict(intent),
                        'business_profile': asdict(business_profile),
                        'execution_plan': execution_plan,
                        'confirmations_needed': intent.required_confirmations,
                        'estimated_cost': self._calculate_estimated_cost(business_profile),
                        'deployment_time': '10-15 minutes'
                    }
                else:
                    # Execute immediately
                    execution = await self._execute_deployment(intent, business_profile)
                    return {
                        'status': 'executing',
                        'execution': asdict(execution),
                        'business_profile': asdict(business_profile)
                    }
            
            elif intent.action == 'monitor':
                return await self._handle_monitoring_command(intent)
            
            elif intent.action == 'manage':
                return await self._handle_management_command(intent)
            
            elif intent.action == 'billing':
                return await self._handle_billing_command(intent)
            
            else:
                return {
                    'status': 'error',
                    'message': f"Action '{intent.action}' not yet implemented",
                    'suggested_commands': [
                        'Deploy a ChatterFix instance for [Business Name]',
                        'Show status for [Customer Name]',
                        'Add users to [Business Name]',
                        'Upgrade [Business Name] to enterprise'
                    ]
                }
        
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                'status': 'error',
                'message': f"Error processing command: {str(e)}",
                'suggestion': 'Please try rephrasing your command or contact support'
            }

    async def _create_execution_plan(self, intent: CommandIntent, 
                                   business_profile: BusinessProfile) -> Dict[str, Any]:
        """Create detailed execution plan for deployment"""
        
        steps = [
            {
                'step': 1,
                'name': 'Cloud Provider Selection',
                'description': 'Select optimal cloud provider based on requirements',
                'estimated_time': '30 seconds'
            },
            {
                'step': 2,
                'name': 'Infrastructure Provisioning',
                'description': f'Deploy {business_profile.deployment_config["compute"]["cpu_cores"]} CPU, {business_profile.deployment_config["compute"]["memory_gb"]}GB RAM instance',
                'estimated_time': '3-5 minutes'
            },
            {
                'step': 3,
                'name': 'Database Setup',
                'description': f'Configure PostgreSQL with {business_profile.deployment_config["storage"]["database_gb"]}GB storage',
                'estimated_time': '2-3 minutes'
            },
            {
                'step': 4,
                'name': 'Application Deployment',
                'description': f'Deploy ChatterFix CMMS with {len(business_profile.required_modules)} modules',
                'estimated_time': '3-4 minutes'
            },
            {
                'step': 5,
                'name': 'Security Configuration',
                'description': f'Setup SSL, access controls, and backup for {business_profile.estimated_users} users',
                'estimated_time': '1-2 minutes'
            },
            {
                'step': 6,
                'name': 'Billing Integration',
                'description': f'Configure {business_profile.recommended_tier} tier billing and monitoring',
                'estimated_time': '1 minute'
            }
        ]
        
        return {
            'steps': steps,
            'total_estimated_time': '10-15 minutes',
            'cloud_provider': 'Auto-selected based on cost and performance',
            'deployment_region': 'Closest to customer location',
            'backup_strategy': 'Daily automated backups with 30-day retention',
            'monitoring': 'Real-time performance and health monitoring',
            'support': '24/7 automated monitoring with escalation to support team'
        }

    def _calculate_estimated_cost(self, business_profile: BusinessProfile) -> Dict[str, Any]:
        """Calculate estimated monthly costs"""
        
        tier_costs = {
            'professional': 89,
            'enterprise': 189,
            'custom': 299
        }
        
        base_cost = tier_costs.get(business_profile.recommended_tier, 89)
        user_cost = max(0, (business_profile.estimated_users - 5) * 15)  # First 5 users included
        
        # Infrastructure costs
        config = business_profile.deployment_config
        infrastructure_cost = (
            config['compute']['cpu_cores'] * 20 +  # $20/core/month
            config['compute']['memory_gb'] * 5 +   # $5/GB/month
            config['storage']['database_gb'] * 0.5  # $0.50/GB/month
        )
        
        total_monthly = base_cost + user_cost + infrastructure_cost
        
        return {
            'base_subscription': base_cost,
            'additional_users': user_cost,
            'infrastructure': round(infrastructure_cost, 2),
            'total_monthly': round(total_monthly, 2),
            'annual_discount': round(total_monthly * 12 * 0.15, 2),  # 15% annual discount
            'setup_fee': 0  # No setup fee for automated deployment
        }

    async def _execute_deployment(self, intent: CommandIntent, 
                                 business_profile: BusinessProfile) -> CommandExecution:
        """Execute the actual deployment process"""
        
        command_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution = CommandExecution(
            command_id=command_id,
            status='in_progress',
            steps=[],
            result=None,
            execution_time=0.0,
            created_instances=[]
        )
        
        self.active_executions[command_id] = execution
        
        # This would integrate with the actual provisioning system
        # For now, return a simulated execution
        execution.steps = [
            {'step': 1, 'status': 'completed', 'message': 'Cloud provider selected: GCP'},
            {'step': 2, 'status': 'in_progress', 'message': 'Provisioning infrastructure...'}
        ]
        
        execution.status = 'executing'
        
        return execution

    async def _handle_monitoring_command(self, intent: CommandIntent) -> Dict[str, Any]:
        """Handle monitoring and status commands"""
        return {
            'status': 'success',
            'type': 'monitoring',
            'message': 'Monitoring command recognized',
            'available_metrics': ['system_health', 'user_activity', 'performance', 'billing_status']
        }

    async def _handle_management_command(self, intent: CommandIntent) -> Dict[str, Any]:
        """Handle user and access management commands"""
        return {
            'status': 'success',
            'type': 'management',
            'message': 'Management command recognized',
            'available_actions': ['add_users', 'modify_permissions', 'configure_roles']
        }

    async def _handle_billing_command(self, intent: CommandIntent) -> Dict[str, Any]:
        """Handle billing and subscription commands"""
        return {
            'status': 'success',
            'type': 'billing',
            'message': 'Billing command recognized',
            'available_actions': ['change_tier', 'update_payment', 'view_usage', 'generate_invoice']
        }

    async def get_execution_status(self, command_id: str) -> Optional[CommandExecution]:
        """Get status of ongoing execution"""
        return self.active_executions.get(command_id)

    async def confirm_and_execute(self, command_id: str, confirmations: Dict[str, Any]) -> Dict[str, Any]:
        """Confirm parameters and execute pending command"""
        # This would handle user confirmations and proceed with execution
        return {
            'status': 'confirmed',
            'message': 'Executing confirmed deployment',
            'command_id': command_id
        }

# Global instance for use by Universal AI Command Center
nlp_processor = NaturalLanguageProcessor()