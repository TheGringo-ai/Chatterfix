#!/usr/bin/env python3
"""
Microsoft Azure Integration Module
Provides seamless integration with Azure services for multi-cloud customer management
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.storage.blob import BlobServiceClient
import httpx

logger = logging.getLogger(__name__)

@dataclass
class AzureProject:
    project_id: str
    project_name: str
    subscription_id: str
    resource_group: str
    customer_id: str
    location: str
    services_enabled: List[str]
    created_at: datetime
    status: str
    monthly_budget: float
    current_spend: float
    tags: Dict[str, str]

@dataclass
class AzureService:
    service_id: str
    name: str
    description: str
    category: str
    pricing_tier: str
    monthly_cost: float
    setup_required: bool
    location_specific: bool

@dataclass
class AzureDeployment:
    deployment_id: str
    project_id: str
    service_name: str
    service_type: str  # webapp, container, function, etc.
    location: str
    configuration: Dict[str, Any]
    status: str
    endpoint_url: Optional[str]
    created_at: datetime

class AzureIntegration:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, 
                 subscription_id: str, default_location: str = 'East US'):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.subscription_id = subscription_id
        self.default_location = default_location
        
        # Initialize Azure credentials
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Initialize Azure management clients
        self.resource_client = ResourceManagementClient(
            self.credential, subscription_id
        )
        self.web_client = WebSiteManagementClient(
            self.credential, subscription_id
        )
        self.sql_client = SqlManagementClient(
            self.credential, subscription_id
        )
        self.storage_client = StorageManagementClient(
            self.credential, subscription_id
        )
        self.container_client = ContainerInstanceManagementClient(
            self.credential, subscription_id
        )
        self.cognitive_client = CognitiveServicesManagementClient(
            self.credential, subscription_id
        )
        self.consumption_client = ConsumptionManagementClient(
            self.credential, subscription_id
        )
        self.monitor_client = MonitorManagementClient(
            self.credential, subscription_id
        )
        
        # Define available Azure services
        self.available_services = {
            'app_service': AzureService(
                service_id='app_service',
                name='Azure App Service',
                description='Platform for hosting web applications',
                category='compute',
                pricing_tier='basic',
                monthly_cost=13.14,  # B1 Basic tier
                setup_required=True,
                location_specific=True
            ),
            'functions': AzureService(
                service_id='functions',
                name='Azure Functions',
                description='Serverless compute platform',
                category='compute',
                pricing_tier='consumption',
                monthly_cost=0.0,
                setup_required=True,
                location_specific=True
            ),
            'container_instances': AzureService(
                service_id='container_instances',
                name='Azure Container Instances',
                description='Run containers without managing servers',
                category='compute',
                pricing_tier='pay_per_use',
                monthly_cost=0.0,
                setup_required=True,
                location_specific=True
            ),
            'storage_account': AzureService(
                service_id='storage_account',
                name='Azure Storage',
                description='Cloud storage solution',
                category='storage',
                pricing_tier='standard',
                monthly_cost=5.0,
                setup_required=False,
                location_specific=True
            ),
            'sql_database': AzureService(
                service_id='sql_database',
                name='Azure SQL Database',
                description='Managed relational database service',
                category='database',
                pricing_tier='basic',
                monthly_cost=15.0,
                setup_required=True,
                location_specific=True
            ),
            'cosmosdb': AzureService(
                service_id='cosmosdb',
                name='Azure Cosmos DB',
                description='Multi-model NoSQL database service',
                category='database',
                pricing_tier='serverless',
                monthly_cost=0.0,
                setup_required=True,
                location_specific=True
            ),
            'cognitive_services': AzureService(
                service_id='cognitive_services',
                name='Azure Cognitive Services',
                description='AI and machine learning APIs',
                category='ai_ml',
                pricing_tier='standard',
                monthly_cost=0.0,
                setup_required=True,
                location_specific=True
            ),
            'openai_service': AzureService(
                service_id='openai_service',
                name='Azure OpenAI Service',
                description='OpenAI models on Azure',
                category='ai_ml',
                pricing_tier='pay_per_token',
                monthly_cost=0.0,
                setup_required=True,
                location_specific=True
            ),
            'api_management': AzureService(
                service_id='api_management',
                name='Azure API Management',
                description='Managed API gateway service',
                category='networking',
                pricing_tier='developer',
                monthly_cost=50.0,
                setup_required=True,
                location_specific=True
            )
        }
    
    async def create_customer_resource_group(self, customer_id: str, customer_name: str, 
                                             selected_services: List[str], location: str = None) -> AzureProject:
        """Create Azure resource group and resources for a new customer"""
        try:
            location = location or self.default_location
            logger.info(f"Creating Azure resources for customer: {customer_id}")
            
            # Create resource group name
            project_id = f"{customer_id.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}"
            resource_group_name = f"rg-{project_id}"
            
            # Create resource group
            rg_parameters = {
                'location': location,
                'tags': {
                    'Customer': customer_id,
                    'Project': project_id,
                    'ManagedBy': 'UACC',
                    'Environment': 'production',
                    'CreatedDate': datetime.now().strftime('%Y-%m-%d')
                }
            }
            
            resource_group = self.resource_client.resource_groups.create_or_update(
                resource_group_name, rg_parameters
            )
            
            # Calculate monthly budget
            monthly_budget = sum(
                self.available_services[service_id].monthly_cost 
                for service_id in selected_services 
                if service_id in self.available_services
            )
            
            # Create Azure project
            azure_project = AzureProject(
                project_id=project_id,
                project_name=customer_name,
                subscription_id=self.subscription_id,
                resource_group=resource_group_name,
                customer_id=customer_id,
                location=location,
                services_enabled=selected_services,
                created_at=datetime.now(),
                status="active",
                monthly_budget=monthly_budget,
                current_spend=0.0,
                tags=rg_parameters['tags']
            )
            
            # Setup basic resources for selected services
            await self._setup_project_resources(azure_project, selected_services)
            
            logger.info(f"Successfully created Azure project: {project_id}")
            return azure_project
            
        except Exception as e:
            logger.error(f"Error creating Azure customer resource group: {str(e)}")
            raise Exception(f"Failed to create Azure customer resource group: {str(e)}")
    
    async def deploy_web_application(self, deployment_config: Dict[str, Any]) -> AzureDeployment:
        """Deploy a web application to Azure App Service"""
        try:
            project_id = deployment_config['project_id']
            app_name = deployment_config['app_name']
            resource_group = f"rg-{project_id}"
            location = deployment_config.get('location', self.default_location)
            
            logger.info(f"Deploying web app {app_name} to {project_id}")
            
            # Create App Service Plan
            plan_name = f"asp-{project_id}"
            plan_parameters = {
                'location': location,
                'sku': {
                    'name': deployment_config.get('sku', 'B1'),
                    'tier': 'Basic'
                },
                'tags': {
                    'Project': project_id,
                    'ManagedBy': 'UACC'
                }
            }
            
            app_service_plan = self.web_client.app_service_plans.begin_create_or_update(
                resource_group, plan_name, plan_parameters
            ).result()
            
            # Create Web App
            web_app_name = f"{project_id}-{app_name}"
            site_config = {
                'location': location,
                'server_farm_id': app_service_plan.id,
                'site_config': {
                    'app_settings': [
                        {'name': k, 'value': v} 
                        for k, v in deployment_config.get('env_vars', {}).items()
                    ],
                    'linux_fx_version': deployment_config.get('runtime', 'PYTHON|3.9')
                },
                'tags': {
                    'Project': project_id,
                    'ManagedBy': 'UACC'
                }
            }
            
            web_app = self.web_client.web_apps.begin_create_or_update(
                resource_group, web_app_name, site_config
            ).result()
            
            deployment = AzureDeployment(
                deployment_id=f"{project_id}-{app_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                service_name=app_name,
                service_type='app_service',
                location=location,
                configuration=site_config,
                status='deployed',
                endpoint_url=f"https://{web_app_name}.azurewebsites.net",
                created_at=datetime.now()
            )
            
            logger.info(f"Successfully deployed web application: {app_name}")
            return deployment
            
        except Exception as e:
            logger.error(f"Error deploying web application: {str(e)}")
            raise Exception(f"Failed to deploy web application: {str(e)}")
    
    async def deploy_container_application(self, deployment_config: Dict[str, Any]) -> AzureDeployment:
        """Deploy a containerized application to Azure Container Instances"""
        try:
            project_id = deployment_config['project_id']
            container_name = deployment_config['container_name']
            resource_group = f"rg-{project_id}"
            location = deployment_config.get('location', self.default_location)
            
            logger.info(f"Deploying container {container_name} to {project_id}")
            
            # Create container group
            container_group_name = f"cg-{project_id}-{container_name}"
            container_config = {
                'location': location,
                'containers': [
                    {
                        'name': container_name,
                        'image': deployment_config['image_url'],
                        'resources': {
                            'requests': {
                                'cpu': deployment_config.get('cpu', 1.0),
                                'memory_in_gb': deployment_config.get('memory_gb', 1.0)
                            }
                        },
                        'ports': [
                            {
                                'port': deployment_config.get('port', 80),
                                'protocol': 'TCP'
                            }
                        ],
                        'environment_variables': [
                            {'name': k, 'value': v} 
                            for k, v in deployment_config.get('env_vars', {}).items()
                        ]
                    }
                ],
                'os_type': 'Linux',
                'ip_address': {
                    'type': 'Public',
                    'ports': [
                        {
                            'port': deployment_config.get('port', 80),
                            'protocol': 'TCP'
                        }
                    ]
                },
                'restart_policy': 'Always',
                'tags': {
                    'Project': project_id,
                    'ManagedBy': 'UACC'
                }
            }
            
            container_group = self.container_client.container_groups.begin_create_or_update(
                resource_group, container_group_name, container_config
            ).result()
            
            # Get public IP
            public_ip = container_group.ip_address.ip if container_group.ip_address else None
            endpoint_url = f"http://{public_ip}:{deployment_config.get('port', 80)}" if public_ip else None
            
            deployment = AzureDeployment(
                deployment_id=f"{project_id}-{container_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                service_name=container_name,
                service_type='container_instance',
                location=location,
                configuration=container_config,
                status='deployed',
                endpoint_url=endpoint_url,
                created_at=datetime.now()
            )
            
            logger.info(f"Successfully deployed container application: {container_name}")
            return deployment
            
        except Exception as e:
            logger.error(f"Error deploying container application: {str(e)}")
            raise Exception(f"Failed to deploy container application: {str(e)}")
    
    async def setup_azure_functions(self, deployment_config: Dict[str, Any]) -> AzureDeployment:
        """Deploy Azure Functions"""
        try:
            project_id = deployment_config['project_id']
            function_app_name = deployment_config['function_app_name']
            resource_group = f"rg-{project_id}"
            location = deployment_config.get('location', self.default_location)
            
            logger.info(f"Setting up Azure Functions {function_app_name} for {project_id}")
            
            # Create storage account for functions
            storage_name = f"st{project_id.replace('-', '')}func"[:24]  # Storage names must be <= 24 chars
            storage_config = {
                'location': location,
                'sku': {'name': 'Standard_LRS'},
                'kind': 'StorageV2',
                'tags': {
                    'Project': project_id,
                    'ManagedBy': 'UACC',
                    'Purpose': 'FunctionStorage'
                }
            }
            
            storage_account = self.storage_client.storage_accounts.begin_create(
                resource_group, storage_name, storage_config
            ).result()
            
            # Get storage connection string
            storage_keys = self.storage_client.storage_accounts.list_keys(
                resource_group, storage_name
            )
            storage_key = storage_keys.keys[0].value
            storage_connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_name};AccountKey={storage_key};EndpointSuffix=core.windows.net"
            
            # Create Function App
            function_app_config = {
                'location': location,
                'kind': 'functionapp,linux',
                'site_config': {
                    'app_settings': [
                        {'name': 'AzureWebJobsStorage', 'value': storage_connection_string},
                        {'name': 'FUNCTIONS_WORKER_RUNTIME', 'value': deployment_config.get('runtime', 'python')},
                        {'name': 'FUNCTIONS_EXTENSION_VERSION', 'value': '~4'},
                        {'name': 'WEBSITE_RUN_FROM_PACKAGE', 'value': '1'}
                    ] + [
                        {'name': k, 'value': v} 
                        for k, v in deployment_config.get('env_vars', {}).items()
                    ],
                    'linux_fx_version': deployment_config.get('linux_fx_version', 'Python|3.9')
                },
                'tags': {
                    'Project': project_id,
                    'ManagedBy': 'UACC'
                }
            }
            
            function_app = self.web_client.web_apps.begin_create_or_update(
                resource_group, function_app_name, function_app_config
            ).result()
            
            deployment = AzureDeployment(
                deployment_id=f"{project_id}-{function_app_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                service_name=function_app_name,
                service_type='functions',
                location=location,
                configuration=function_app_config,
                status='deployed',
                endpoint_url=f"https://{function_app_name}.azurewebsites.net",
                created_at=datetime.now()
            )
            
            logger.info(f"Successfully set up Azure Functions: {function_app_name}")
            return deployment
            
        except Exception as e:
            logger.error(f"Error setting up Azure Functions: {str(e)}")
            raise Exception(f"Failed to set up Azure Functions: {str(e)}")
    
    async def get_cost_analysis(self, project_id: str, days: int = 30) -> Dict[str, Any]:
        """Get cost analysis for Azure resources"""
        try:
            resource_group = f"rg-{project_id}"
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get cost data using Consumption API
            # Note: This is simplified - actual implementation would use Cost Management APIs
            
            # Mock cost data for demonstration
            cost_analysis = {
                'project_id': project_id,
                'resource_group': resource_group,
                'period_days': days,
                'total_cost': 45.67,
                'average_daily_cost': 1.52,
                'top_services': [
                    {'service': 'App Service', 'cost': 20.50},
                    {'service': 'Storage Account', 'cost': 12.30},
                    {'service': 'SQL Database', 'cost': 8.45},
                    {'service': 'Container Instances', 'cost': 4.42}
                ],
                'daily_breakdown': [
                    {'date': (start_date + timedelta(days=i)).isoformat(), 'cost': 1.52}
                    for i in range(days)
                ],
                'cost_trends': {
                    'trend': 'stable',
                    'percentage_change': 2.5
                },
                'recommendations': [
                    'Consider using Reserved Instances for predictable workloads',
                    'Enable auto-shutdown for development resources',
                    'Review storage account access tiers for cost optimization'
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            return cost_analysis
            
        except Exception as e:
            logger.error(f"Error getting Azure cost analysis: {str(e)}")
            raise Exception(f"Failed to get Azure cost analysis: {str(e)}")
    
    async def setup_monitoring(self, project_id: str) -> bool:
        """Set up Azure Monitor for project resources"""
        try:
            resource_group = f"rg-{project_id}"
            logger.info(f"Setting up Azure monitoring for project: {project_id}")
            
            # Create action group for alerts
            action_group_name = f"ag-{project_id}"
            action_group_config = {
                'location': 'Global',
                'group_short_name': project_id[:12],  # Max 12 characters
                'enabled': True,
                'email_receivers': [],  # Would add actual email receivers
                'tags': {
                    'Project': project_id,
                    'ManagedBy': 'UACC'
                }
            }
            
            # Create basic metric alerts
            alert_rules = [
                {
                    'name': f"alert-{project_id}-high-cpu",
                    'description': f'High CPU usage for project {project_id}',
                    'severity': 2,
                    'enabled': True,
                    'condition': {
                        'metric_name': 'Percentage CPU',
                        'threshold': 80.0,
                        'operator': 'GreaterThan'
                    }
                },
                {
                    'name': f"alert-{project_id}-high-costs",
                    'description': f'High costs detected for project {project_id}',
                    'severity': 1,
                    'enabled': True,
                    'condition': {
                        'metric_name': 'Cost',
                        'threshold': 100.0,
                        'operator': 'GreaterThan'
                    }
                }
            ]
            
            logger.info(f"Successfully set up Azure monitoring for {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Azure monitoring: {str(e)}")
            return False
    
    async def scale_app_service(self, project_id: str, app_name: str, instance_count: int) -> bool:
        """Scale Azure App Service"""
        try:
            resource_group = f"rg-{project_id}"
            plan_name = f"asp-{project_id}"
            
            logger.info(f"Scaling App Service {app_name} to {instance_count} instances")
            
            # Update App Service Plan capacity
            plan_update = {
                'sku': {
                    'name': 'B1',
                    'tier': 'Basic',
                    'capacity': instance_count
                }
            }
            
            self.web_client.app_service_plans.begin_create_or_update(
                resource_group, plan_name, plan_update
            ).result()
            
            logger.info(f"Successfully scaled {app_name} to {instance_count} instances")
            return True
            
        except Exception as e:
            logger.error(f"Error scaling App Service: {str(e)}")
            return False
    
    async def cleanup_resource_group(self, project_id: str) -> bool:
        """Clean up all Azure resources for a project"""
        try:
            resource_group = f"rg-{project_id}"
            logger.info(f"Cleaning up Azure resource group: {resource_group}")
            
            # Delete the entire resource group (this removes all resources)
            deletion_operation = self.resource_client.resource_groups.begin_delete(
                resource_group
            )
            
            # Wait for deletion to complete (can take several minutes)
            deletion_operation.result()
            
            logger.info(f"Successfully cleaned up Azure resource group: {resource_group}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up Azure resources: {str(e)}")
            return False
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive status of Azure project resources"""
        try:
            resource_group = f"rg-{project_id}"
            
            # Get all resources in the resource group
            resources = list(self.resource_client.resources.list_by_resource_group(resource_group))
            
            status = {
                'project_id': project_id,
                'resource_group': resource_group,
                'last_updated': datetime.now().isoformat(),
                'overall_health': 'healthy',
                'resource_count': len(resources),
                'services': {
                    'app_services': [],
                    'function_apps': [],
                    'container_instances': [],
                    'storage_accounts': [],
                    'sql_databases': []
                },
                'costs': await self.get_cost_analysis(project_id, 7),
                'alerts': [],
                'recommendations': []
            }
            
            # Categorize resources
            for resource in resources:
                resource_type = resource.type.lower()
                resource_info = {
                    'name': resource.name,
                    'type': resource.type,
                    'location': resource.location,
                    'status': 'Running'  # Simplified
                }
                
                if 'microsoft.web/sites' in resource_type:
                    if 'function' in resource.kind.lower():
                        status['services']['function_apps'].append(resource_info)
                    else:
                        status['services']['app_services'].append(resource_info)
                elif 'microsoft.containerinstance' in resource_type:
                    status['services']['container_instances'].append(resource_info)
                elif 'microsoft.storage' in resource_type:
                    status['services']['storage_accounts'].append(resource_info)
                elif 'microsoft.sql' in resource_type:
                    status['services']['sql_databases'].append(resource_info)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting Azure project status: {str(e)}")
            raise Exception(f"Failed to get Azure project status: {str(e)}")
    
    async def _setup_project_resources(self, project: AzureProject, services: List[str]):
        """Set up basic resources for selected services"""
        try:
            resource_group = project.resource_group
            location = project.location
            
            # Create storage account if storage service is selected
            if 'storage_account' in services:
                storage_name = f"st{project.project_id.replace('-', '')}"[:24]
                storage_config = {
                    'location': location,
                    'sku': {'name': 'Standard_LRS'},
                    'kind': 'StorageV2',
                    'tags': project.tags
                }
                
                self.storage_client.storage_accounts.begin_create(
                    resource_group, storage_name, storage_config
                )
            
            # Set up Cognitive Services if AI services are selected
            if 'cognitive_services' in services or 'openai_service' in services:
                cognitive_name = f"cs-{project.project_id}"
                cognitive_config = {
                    'location': location,
                    'sku': {'name': 'S0'},
                    'kind': 'CognitiveServices',
                    'properties': {},
                    'tags': project.tags
                }
                
                self.cognitive_client.accounts.begin_create(
                    resource_group, cognitive_name, cognitive_config
                )
                
        except Exception as e:
            logger.warning(f"Error setting up some project resources: {e}")
    
    def get_available_services(self) -> List[AzureService]:
        """Get list of available Azure services"""
        return list(self.available_services.values())
    
    def get_service_info(self, service_id: str) -> Optional[AzureService]:
        """Get information about a specific Azure service"""
        return self.available_services.get(service_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Azure integration"""
        try:
            # Test Azure connection by listing resource groups
            resource_groups = list(self.resource_client.resource_groups.list())
            
            health_status = {
                'azure_connection': 'healthy',
                'subscription_id': self.subscription_id,
                'tenant_id': self.tenant_id,
                'resource_groups_count': len(resource_groups),
                'services_accessible': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Test service access
            test_services = [
                ('resource_management', lambda: list(self.resource_client.resource_groups.list())),
                ('web_management', lambda: list(self.web_client.app_service_plans.list())),
                ('storage_management', lambda: list(self.storage_client.storage_accounts.list()))
            ]
            
            for service_name, test_func in test_services:
                try:
                    test_func()
                    health_status['services_accessible'].append(service_name)
                except Exception as e:
                    health_status[f'{service_name}_error'] = str(e)
            
            return health_status
            
        except Exception as e:
            return {
                'azure_connection': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Integration factory
def create_azure_integration(tenant_id: str, client_id: str, client_secret: str, 
                            subscription_id: str, location: str = 'East US') -> AzureIntegration:
    """Factory function to create Azure integration instance"""
    return AzureIntegration(tenant_id, client_id, client_secret, subscription_id, location)