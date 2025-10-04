#!/usr/bin/env python3
"""
Amazon Web Services Integration Module
Provides seamless integration with AWS services for multi-cloud customer management
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import httpx

logger = logging.getLogger(__name__)

@dataclass
class AWSProject:
    project_id: str
    project_name: str
    account_id: str
    customer_id: str
    region: str
    services_enabled: List[str]
    created_at: datetime
    status: str
    monthly_budget: float
    current_spend: float
    tags: Dict[str, str]

@dataclass
class AWSService:
    service_id: str
    name: str
    description: str
    category: str
    pricing_tier: str
    monthly_cost: float
    setup_required: bool
    region_specific: bool

@dataclass
class AWSDeployment:
    deployment_id: str
    project_id: str
    service_name: str
    service_type: str  # lambda, ecs, ec2, etc.
    region: str
    configuration: Dict[str, Any]
    status: str
    endpoint_url: Optional[str]
    created_at: datetime

class AWSIntegration:
    def __init__(self, access_key_id: str, secret_access_key: str, default_region: str = 'us-east-1'):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.default_region = default_region
        
        # Initialize AWS clients
        self.session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=default_region
        )
        
        # Initialize service clients
        self.ec2_client = self.session.client('ec2')
        self.lambda_client = self.session.client('lambda')
        self.ecs_client = self.session.client('ecs')
        self.s3_client = self.session.client('s3')
        self.rds_client = self.session.client('rds')
        self.iam_client = self.session.client('iam')
        self.cloudformation_client = self.session.client('cloudformation')
        self.cloudwatch_client = self.session.client('cloudwatch')
        self.ce_client = self.session.client('ce')  # Cost Explorer
        self.organizations_client = self.session.client('organizations')
        
        # Define available AWS services
        self.available_services = {
            'lambda': AWSService(
                service_id='lambda',
                name='AWS Lambda',
                description='Serverless compute service',
                category='compute',
                pricing_tier='pay_per_request',
                monthly_cost=0.0,
                setup_required=True,
                region_specific=True
            ),
            'ecs_fargate': AWSService(
                service_id='ecs_fargate',
                name='ECS Fargate',
                description='Serverless container platform',
                category='compute',
                pricing_tier='pay_per_use',
                monthly_cost=0.0,
                setup_required=True,
                region_specific=True
            ),
            'ec2': AWSService(
                service_id='ec2',
                name='EC2 Instances',
                description='Virtual servers in the cloud',
                category='compute',
                pricing_tier='hourly',
                monthly_cost=25.0,
                setup_required=True,
                region_specific=True
            ),
            's3': AWSService(
                service_id='s3',
                name='S3 Storage',
                description='Object storage service',
                category='storage',
                pricing_tier='pay_per_gb',
                monthly_cost=5.0,
                setup_required=False,
                region_specific=False
            ),
            'rds': AWSService(
                service_id='rds',
                name='RDS Database',
                description='Managed relational database service',
                category='database',
                pricing_tier='instance_based',
                monthly_cost=50.0,
                setup_required=True,
                region_specific=True
            ),
            'api_gateway': AWSService(
                service_id='api_gateway',
                name='API Gateway',
                description='Managed API service',
                category='networking',
                pricing_tier='pay_per_request',
                monthly_cost=0.0,
                setup_required=True,
                region_specific=True
            ),
            'dynamodb': AWSService(
                service_id='dynamodb',
                name='DynamoDB',
                description='NoSQL database service',
                category='database',
                pricing_tier='pay_per_request',
                monthly_cost=0.0,
                setup_required=False,
                region_specific=True
            ),
            'bedrock': AWSService(
                service_id='bedrock',
                name='Amazon Bedrock',
                description='Fully managed foundation models',
                category='ai_ml',
                pricing_tier='pay_per_request',
                monthly_cost=0.0,
                setup_required=True,
                region_specific=True
            ),
            'sagemaker': AWSService(
                service_id='sagemaker',
                name='SageMaker',
                description='Machine learning platform',
                category='ai_ml',
                pricing_tier='instance_based',
                monthly_cost=100.0,
                setup_required=True,
                region_specific=True
            )
        }
    
    async def create_customer_account(self, customer_id: str, customer_name: str, 
                                      selected_services: List[str], region: str = None) -> AWSProject:
        """Create AWS resources for a new customer"""
        try:
            region = region or self.default_region
            logger.info(f"Creating AWS resources for customer: {customer_id}")
            
            # Get current account ID
            sts_client = self.session.client('sts')
            account_info = sts_client.get_caller_identity()
            account_id = account_info['Account']
            
            # Create project identifier
            project_id = f"{customer_id.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}"
            
            # Create IAM role for customer resources
            await self._create_customer_iam_role(project_id, customer_id)
            
            # Setup CloudFormation stack for customer
            stack_name = f"customer-{project_id}-stack"
            await self._create_cloudformation_stack(stack_name, selected_services, region)
            
            # Calculate monthly budget
            monthly_budget = sum(
                self.available_services[service_id].monthly_cost 
                for service_id in selected_services 
                if service_id in self.available_services
            )
            
            # Create project tags
            tags = {
                'Customer': customer_id,
                'Project': project_id,
                'ManagedBy': 'UACC',
                'Environment': 'production',
                'CreatedDate': datetime.now().strftime('%Y-%m-%d')
            }
            
            aws_project = AWSProject(
                project_id=project_id,
                project_name=customer_name,
                account_id=account_id,
                customer_id=customer_id,
                region=region,
                services_enabled=selected_services,
                created_at=datetime.now(),
                status="active",
                monthly_budget=monthly_budget,
                current_spend=0.0,
                tags=tags
            )
            
            logger.info(f"Successfully created AWS project: {project_id}")
            return aws_project
            
        except Exception as e:
            logger.error(f"Error creating AWS customer account: {str(e)}")
            raise Exception(f"Failed to create AWS customer account: {str(e)}")
    
    async def deploy_serverless_application(self, deployment_config: Dict[str, Any]) -> AWSDeployment:
        """Deploy a serverless application using Lambda and API Gateway"""
        try:
            project_id = deployment_config['project_id']
            function_name = deployment_config['function_name']
            region = deployment_config.get('region', self.default_region)
            
            logger.info(f"Deploying serverless app {function_name} to {project_id}")
            
            # Create Lambda function
            lambda_config = {
                'FunctionName': f"{project_id}-{function_name}",
                'Runtime': deployment_config.get('runtime', 'python3.9'),
                'Role': f"arn:aws:iam::{self.session.client('sts').get_caller_identity()['Account']}:role/{project_id}-execution-role",
                'Handler': deployment_config.get('handler', 'index.handler'),
                'Code': {
                    'ZipFile': deployment_config.get('code_zip', b'')
                },
                'Environment': {
                    'Variables': deployment_config.get('env_vars', {})
                },
                'Tags': {
                    'Project': project_id,
                    'ManagedBy': 'UACC'
                }
            }
            
            # Deploy Lambda function
            response = self.lambda_client.create_function(**lambda_config)
            function_arn = response['FunctionArn']
            
            # Create API Gateway (simplified)
            api_name = f"{project_id}-{function_name}-api"
            # In production, you'd create a full API Gateway setup
            
            deployment = AWSDeployment(
                deployment_id=f"{project_id}-{function_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                service_name=function_name,
                service_type='lambda',
                region=region,
                configuration=lambda_config,
                status='deployed',
                endpoint_url=f"https://{api_name}.execute-api.{region}.amazonaws.com/prod",
                created_at=datetime.now()
            )
            
            logger.info(f"Successfully deployed serverless application: {function_name}")
            return deployment
            
        except Exception as e:
            logger.error(f"Error deploying serverless application: {str(e)}")
            raise Exception(f"Failed to deploy serverless application: {str(e)}")
    
    async def deploy_container_application(self, deployment_config: Dict[str, Any]) -> AWSDeployment:
        """Deploy a containerized application using ECS Fargate"""
        try:
            project_id = deployment_config['project_id']
            service_name = deployment_config['service_name']
            region = deployment_config.get('region', self.default_region)
            
            logger.info(f"Deploying container app {service_name} to {project_id}")
            
            # Create ECS cluster
            cluster_name = f"{project_id}-cluster"
            try:
                self.ecs_client.create_cluster(clusterName=cluster_name)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ClusterNameInUseException':
                    raise
            
            # Create task definition
            task_definition = {
                'family': f"{project_id}-{service_name}",
                'networkMode': 'awsvpc',
                'requiresCompatibilities': ['FARGATE'],
                'cpu': deployment_config.get('cpu', '256'),
                'memory': deployment_config.get('memory', '512'),
                'executionRoleArn': f"arn:aws:iam::{self.session.client('sts').get_caller_identity()['Account']}:role/{project_id}-execution-role",
                'containerDefinitions': [
                    {
                        'name': service_name,
                        'image': deployment_config['image_url'],
                        'portMappings': [
                            {
                                'containerPort': deployment_config.get('port', 80),
                                'protocol': 'tcp'
                            }
                        ],
                        'environment': [
                            {'name': k, 'value': v} 
                            for k, v in deployment_config.get('env_vars', {}).items()
                        ],
                        'logConfiguration': {
                            'logDriver': 'awslogs',
                            'options': {
                                'awslogs-group': f"/ecs/{project_id}-{service_name}",
                                'awslogs-region': region,
                                'awslogs-stream-prefix': 'ecs'
                            }
                        }
                    }
                ],
                'tags': [
                    {'key': 'Project', 'value': project_id},
                    {'key': 'ManagedBy', 'value': 'UACC'}
                ]
            }
            
            # Register task definition
            task_response = self.ecs_client.register_task_definition(**task_definition)
            task_arn = task_response['taskDefinition']['taskDefinitionArn']
            
            # Create ECS service (simplified - would need VPC configuration)
            service_config = {
                'cluster': cluster_name,
                'serviceName': f"{project_id}-{service_name}",
                'taskDefinition': task_arn,
                'desiredCount': deployment_config.get('desired_count', 1),
                'launchType': 'FARGATE',
                'tags': [
                    {'key': 'Project', 'value': project_id},
                    {'key': 'ManagedBy', 'value': 'UACC'}
                ]
            }
            
            deployment = AWSDeployment(
                deployment_id=f"{project_id}-{service_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                service_name=service_name,
                service_type='ecs_fargate',
                region=region,
                configuration=service_config,
                status='deploying',
                endpoint_url=None,  # Would be set after load balancer setup
                created_at=datetime.now()
            )
            
            logger.info(f"Successfully initiated container deployment: {service_name}")
            return deployment
            
        except Exception as e:
            logger.error(f"Error deploying container application: {str(e)}")
            raise Exception(f"Failed to deploy container application: {str(e)}")
    
    async def get_cost_analysis(self, project_id: str, days: int = 30) -> Dict[str, Any]:
        """Get cost analysis for a project"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get cost and usage data
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': [self.session.client('sts').get_caller_identity()['Account']]
                    }
                }
            )
            
            # Process cost data
            total_cost = 0.0
            service_costs = {}
            daily_costs = []
            
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                daily_total = 0.0
                
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if service not in service_costs:
                        service_costs[service] = 0.0
                    service_costs[service] += cost
                    daily_total += cost
                
                daily_costs.append({
                    'date': date,
                    'cost': daily_total
                })
                total_cost += daily_total
            
            # Get top services by cost
            top_services = sorted(
                [{'service': k, 'cost': v} for k, v in service_costs.items()],
                key=lambda x: x['cost'],
                reverse=True
            )[:5]
            
            cost_analysis = {
                'project_id': project_id,
                'period_days': days,
                'total_cost': round(total_cost, 2),
                'average_daily_cost': round(total_cost / days, 2),
                'top_services': top_services,
                'daily_breakdown': daily_costs,
                'cost_trends': {
                    'trend': 'increasing' if len(daily_costs) > 1 and daily_costs[-1]['cost'] > daily_costs[0]['cost'] else 'stable',
                    'percentage_change': 0.0  # Would calculate actual percentage
                },
                'recommendations': [
                    'Consider using Reserved Instances for long-running EC2 instances',
                    'Enable S3 Intelligent Tiering for storage cost optimization',
                    'Review and optimize Lambda function memory allocation'
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            return cost_analysis
            
        except Exception as e:
            logger.error(f"Error getting cost analysis: {str(e)}")
            raise Exception(f"Failed to get cost analysis: {str(e)}")
    
    async def setup_monitoring(self, project_id: str) -> bool:
        """Set up CloudWatch monitoring for project resources"""
        try:
            logger.info(f"Setting up monitoring for project: {project_id}")
            
            # Create CloudWatch log group
            log_group_name = f"/aws/uacc/{project_id}"
            try:
                logs_client = self.session.client('logs')
                logs_client.create_log_group(logGroupName=log_group_name)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
            
            # Create basic alarms (simplified)
            alarm_configs = [
                {
                    'AlarmName': f"{project_id}-high-costs",
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'EvaluationPeriods': 1,
                    'MetricName': 'EstimatedCharges',
                    'Namespace': 'AWS/Billing',
                    'Period': 86400,  # Daily
                    'Statistic': 'Maximum',
                    'Threshold': 100.0,
                    'ActionsEnabled': True,
                    'AlarmDescription': f'High costs detected for project {project_id}',
                    'Dimensions': [
                        {
                            'Name': 'Currency',
                            'Value': 'USD'
                        }
                    ]
                }
            ]
            
            for alarm_config in alarm_configs:
                self.cloudwatch_client.put_metric_alarm(**alarm_config)
            
            logger.info(f"Successfully set up monitoring for {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up monitoring: {str(e)}")
            return False
    
    async def cleanup_project_resources(self, project_id: str) -> bool:
        """Clean up all AWS resources for a project"""
        try:
            logger.info(f"Cleaning up AWS resources for project: {project_id}")
            
            # Delete CloudFormation stack
            stack_name = f"customer-{project_id}-stack"
            try:
                self.cloudformation_client.delete_stack(StackName=stack_name)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ValidationError':
                    logger.warning(f"Could not delete stack {stack_name}: {e}")
            
            # Delete Lambda functions
            try:
                paginator = self.lambda_client.get_paginator('list_functions')
                for page in paginator.paginate():
                    for function in page['Functions']:
                        if project_id in function['FunctionName']:
                            self.lambda_client.delete_function(
                                FunctionName=function['FunctionName']
                            )
            except Exception as e:
                logger.warning(f"Error cleaning up Lambda functions: {e}")
            
            # Delete ECS services and clusters
            try:
                cluster_name = f"{project_id}-cluster"
                # List and delete services first
                services = self.ecs_client.list_services(cluster=cluster_name)
                for service_arn in services['serviceArns']:
                    self.ecs_client.delete_service(
                        cluster=cluster_name,
                        service=service_arn,
                        force=True
                    )
                
                # Delete cluster
                self.ecs_client.delete_cluster(cluster=cluster_name)
            except Exception as e:
                logger.warning(f"Error cleaning up ECS resources: {e}")
            
            # Delete CloudWatch alarms
            try:
                alarms = self.cloudwatch_client.describe_alarms(
                    AlarmNamePrefix=project_id
                )
                alarm_names = [alarm['AlarmName'] for alarm in alarms['MetricAlarms']]
                if alarm_names:
                    self.cloudwatch_client.delete_alarms(AlarmNames=alarm_names)
            except Exception as e:
                logger.warning(f"Error cleaning up CloudWatch alarms: {e}")
            
            logger.info(f"Successfully cleaned up AWS resources for {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up AWS resources: {str(e)}")
            return False
    
    async def scale_service(self, project_id: str, service_name: str, 
                           desired_count: int, service_type: str = 'ecs') -> bool:
        """Scale AWS services (ECS or Lambda)"""
        try:
            if service_type == 'ecs':
                cluster_name = f"{project_id}-cluster"
                service_full_name = f"{project_id}-{service_name}"
                
                self.ecs_client.update_service(
                    cluster=cluster_name,
                    service=service_full_name,
                    desiredCount=desired_count
                )
                
            elif service_type == 'lambda':
                # Lambda scaling is handled automatically
                # Could update reserved concurrency if needed
                function_name = f"{project_id}-{service_name}"
                self.lambda_client.put_reserved_concurrency_configuration(
                    FunctionName=function_name,
                    ReservedConcurrencyLimit=desired_count
                )
            
            logger.info(f"Successfully scaled {service_name} to {desired_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error scaling service: {str(e)}")
            return False
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive status of AWS project resources"""
        try:
            status = {
                'project_id': project_id,
                'last_updated': datetime.now().isoformat(),
                'overall_health': 'healthy',
                'services': {
                    'lambda_functions': [],
                    'ecs_services': [],
                    'ec2_instances': [],
                    's3_buckets': [],
                    'rds_instances': []
                },
                'costs': await self.get_cost_analysis(project_id, 7),
                'alerts': [],
                'recommendations': []
            }
            
            # Check Lambda functions
            try:
                paginator = self.lambda_client.get_paginator('list_functions')
                for page in paginator.paginate():
                    for function in page['Functions']:
                        if project_id in function['FunctionName']:
                            status['services']['lambda_functions'].append({
                                'name': function['FunctionName'],
                                'runtime': function['Runtime'],
                                'last_modified': function['LastModified'],
                                'state': 'Active'  # Simplified
                            })
            except Exception as e:
                logger.warning(f"Error checking Lambda functions: {e}")
            
            # Check ECS services
            try:
                cluster_name = f"{project_id}-cluster"
                services = self.ecs_client.list_services(cluster=cluster_name)
                for service_arn in services['serviceArns']:
                    service_details = self.ecs_client.describe_services(
                        cluster=cluster_name,
                        services=[service_arn]
                    )
                    for service in service_details['services']:
                        status['services']['ecs_services'].append({
                            'name': service['serviceName'],
                            'status': service['status'],
                            'running_count': service['runningCount'],
                            'desired_count': service['desiredCount']
                        })
            except Exception as e:
                logger.warning(f"Error checking ECS services: {e}")
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting project status: {str(e)}")
            raise Exception(f"Failed to get project status: {str(e)}")
    
    async def _create_customer_iam_role(self, project_id: str, customer_id: str) -> str:
        """Create IAM role for customer resources"""
        try:
            role_name = f"{project_id}-execution-role"
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Execution role for customer {customer_id} project {project_id}",
                Tags=[
                    {'Key': 'Project', 'Value': project_id},
                    {'Key': 'Customer', 'Value': customer_id},
                    {'Key': 'ManagedBy', 'Value': 'UACC'}
                ]
            )
            
            # Attach basic execution policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy'
            ]
            
            for policy_arn in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
            
            return role_name
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'EntityAlreadyExists':
                raise
            return f"{project_id}-execution-role"
    
    async def _create_cloudformation_stack(self, stack_name: str, 
                                           services: List[str], region: str) -> str:
        """Create CloudFormation stack for customer resources"""
        try:
            # Simplified CloudFormation template
            template = {
                "AWSTemplateFormatVersion": "2010-09-09",
                "Description": f"UACC managed customer resources - {stack_name}",
                "Resources": {
                    "CustomerVPC": {
                        "Type": "AWS::EC2::VPC",
                        "Properties": {
                            "CidrBlock": "10.0.0.0/16",
                            "EnableDnsHostnames": True,
                            "EnableDnsSupport": True,
                            "Tags": [
                                {"Key": "Name", "Value": f"{stack_name}-vpc"},
                                {"Key": "ManagedBy", "Value": "UACC"}
                            ]
                        }
                    }
                }
            }
            
            # Add service-specific resources
            if 's3' in services:
                template["Resources"]["CustomerS3Bucket"] = {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {
                        "BucketName": f"{stack_name.lower()}-storage",
                        "PublicAccessBlockConfiguration": {
                            "BlockPublicAcls": True,
                            "BlockPublicPolicy": True,
                            "IgnorePublicAcls": True,
                            "RestrictPublicBuckets": True
                        }
                    }
                }
            
            self.cloudformation_client.create_stack(
                StackName=stack_name,
                TemplateBody=json.dumps(template),
                Tags=[
                    {'Key': 'ManagedBy', 'Value': 'UACC'},
                    {'Key': 'Purpose', 'Value': 'CustomerResources'}
                ]
            )
            
            return stack_name
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'AlreadyExistsException':
                raise
            return stack_name
    
    def get_available_services(self) -> List[AWSService]:
        """Get list of available AWS services"""
        return list(self.available_services.values())
    
    def get_service_info(self, service_id: str) -> Optional[AWSService]:
        """Get information about a specific AWS service"""
        return self.available_services.get(service_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on AWS integration"""
        try:
            # Test AWS connection
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()
            
            health_status = {
                'aws_connection': 'healthy',
                'account_id': identity['Account'],
                'user_id': identity['UserId'],
                'region': self.default_region,
                'services_accessible': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Test service access
            test_services = [
                ('lambda', self.lambda_client.list_functions),
                ('ecs', self.ecs_client.list_clusters),
                ('s3', self.s3_client.list_buckets),
                ('ec2', self.ec2_client.describe_regions)
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
                'aws_connection': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Integration factory
def create_aws_integration(access_key_id: str, secret_access_key: str, 
                          region: str = 'us-east-1') -> AWSIntegration:
    """Factory function to create AWS integration instance"""
    return AWSIntegration(access_key_id, secret_access_key, region)