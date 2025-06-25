import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Optional
from datetime import datetime
import json

class AWSResourceDiscovery:
    def __init__(self, access_key: str, secret_key: str, region: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.session = None
        
    def create_session(self):
        """Create AWS session with credentials"""
        try:
            self.session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            return True
        except Exception as e:
            print(f"Error creating AWS session: {e}")
            return False
    
    def discover_all_resources(self) -> List[Dict]:
        """Discover all AWS resources across services"""
        if not self.session:
            if not self.create_session():
                return []
        
        all_resources = []
        
        # Discover resources from different services
        all_resources.extend(self.discover_ec2_resources())
        all_resources.extend(self.discover_rds_resources())
        all_resources.extend(self.discover_s3_resources())
        all_resources.extend(self.discover_alb_resources())
        all_resources.extend(self.discover_target_groups())
        all_resources.extend(self.discover_ecs_resources())
        all_resources.extend(self.discover_lambda_resources())
        all_resources.extend(self.discover_cloudwatch_alarms())
        all_resources.extend(self.discover_vpc_resources())
        all_resources.extend(self.discover_iam_resources())
        all_resources.extend(self.discover_route53_resources())
        all_resources.extend(self.discover_elasticache_resources())
        all_resources.extend(self.discover_elasticsearch_resources())
        all_resources.extend(self.discover_sqs_resources())
        all_resources.extend(self.discover_sns_resources())
        all_resources.extend(self.discover_api_gateway_resources())
        
        return all_resources
    
    def discover_ec2_resources(self) -> List[Dict]:
        """Discover EC2 instances and related resources"""
        resources = []
        
        try:
            ec2 = self.session.client('ec2')
            
            # EC2 Instances
            response = ec2.describe_instances()
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    name = self._get_tag_value(instance.get('Tags', []), 'Name', 'N/A')
                    
                    # Get instance health check
                    health_status = "healthy"
                    if instance['State']['Name'] not in ['running', 'stopped']:
                        health_status = "unhealthy"
                    
                    resources.append({
                        'resource_type': 'EC2_Instance',
                        'resource_id': instance['InstanceId'],
                        'name': name,
                        'status': instance['State']['Name'],
                        'region': self.region,
                        'created_at': instance.get('LaunchTime', datetime.now()).isoformat() if isinstance(instance.get('LaunchTime'), datetime) else str(instance.get('LaunchTime')),
                        'metadata': {
                            'instance_type': instance.get('InstanceType'),
                            'vpc_id': instance.get('VpcId'),
                            'subnet_id': instance.get('SubnetId'),
                            'private_ip': instance.get('PrivateIpAddress'),
                            'public_ip': instance.get('PublicIpAddress'),
                            'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                            'health_status': health_status,
                            'tags': instance.get('Tags', [])
                        }
                    })
            
            # Security Groups
            response = ec2.describe_security_groups()
            for sg in response['SecurityGroups']:
                resources.append({
                    'resource_type': 'SecurityGroup',
                    'resource_id': sg['GroupId'],
                    'name': sg.get('GroupName', 'N/A'),
                    'status': 'active',
                    'region': self.region,
                    'created_at': None,
                    'metadata': {
                        'description': sg.get('Description'),
                        'vpc_id': sg.get('VpcId'),
                        'rules_inbound': len(sg.get('IpPermissions', [])),
                        'rules_outbound': len(sg.get('IpPermissionsEgress', [])),
                        'tags': sg.get('Tags', [])
                    }
                })
            
            # Key Pairs
            response = ec2.describe_key_pairs()
            for kp in response['KeyPairs']:
                resources.append({
                    'resource_type': 'KeyPair',
                    'resource_id': kp['KeyPairId'],
                    'name': kp['KeyName'],
                    'status': 'active',
                    'region': self.region,
                    'created_at': kp.get('CreateTime', datetime.now()).isoformat() if isinstance(kp.get('CreateTime'), datetime) else str(kp.get('CreateTime')),
                    'metadata': {
                        'key_type': kp.get('KeyType'),
                        'fingerprint': kp.get('KeyFingerprint'),
                        'tags': kp.get('Tags', [])
                    }
                })
                
        except ClientError as e:
            print(f"Error discovering EC2 resources: {e}")
        
        return resources
    
    def discover_rds_resources(self) -> List[Dict]:
        """Discover RDS instances and clusters"""
        resources = []
        
        try:
            rds = self.session.client('rds')
            
            # RDS DB Instances
            response = rds.describe_db_instances()
            for db in response['DBInstances']:
                # Check health status
                health_status = "healthy" if db['DBInstanceStatus'] == 'available' else "unhealthy"
                
                resources.append({
                    'resource_type': 'RDS_Instance',
                    'resource_id': db['DBInstanceIdentifier'],
                    'name': db['DBInstanceIdentifier'],
                    'status': db['DBInstanceStatus'],
                    'region': self.region,
                    'created_at': db.get('InstanceCreateTime', datetime.now()).isoformat() if isinstance(db.get('InstanceCreateTime'), datetime) else str(db.get('InstanceCreateTime')),
                    'metadata': {
                        'engine': db.get('Engine'),
                        'engine_version': db.get('EngineVersion'),
                        'db_instance_class': db.get('DBInstanceClass'),
                        'allocated_storage': db.get('AllocatedStorage'),
                        'storage_type': db.get('StorageType'),
                        'multi_az': db.get('MultiAZ'),
                        'vpc_security_groups': [sg['VpcSecurityGroupId'] for sg in db.get('VpcSecurityGroups', [])],
                        'health_status': health_status,
                        'endpoint': db.get('Endpoint', {}).get('Address') if db.get('Endpoint') else None,
                        'port': db.get('Endpoint', {}).get('Port') if db.get('Endpoint') else None
                    }
                })
            
            # RDS Clusters
            try:
                response = rds.describe_db_clusters()
                for cluster in response['DBClusters']:
                    health_status = "healthy" if cluster['Status'] == 'available' else "unhealthy"
                    
                    resources.append({
                        'resource_type': 'RDS_Cluster',
                        'resource_id': cluster['DBClusterIdentifier'],
                        'name': cluster['DBClusterIdentifier'],
                        'status': cluster['Status'],
                        'region': self.region,
                        'created_at': cluster.get('ClusterCreateTime', datetime.now()).isoformat() if isinstance(cluster.get('ClusterCreateTime'), datetime) else str(cluster.get('ClusterCreateTime')),
                        'metadata': {
                            'engine': cluster.get('Engine'),
                            'engine_version': cluster.get('EngineVersion'),
                            'master_username': cluster.get('MasterUsername'),
                            'database_name': cluster.get('DatabaseName'),
                            'cluster_members': len(cluster.get('DBClusterMembers', [])),
                            'health_status': health_status,
                            'endpoint': cluster.get('Endpoint'),
                            'reader_endpoint': cluster.get('ReaderEndpoint')
                        }
                    })
            except ClientError:
                pass  # Clusters not supported in all regions
                
        except ClientError as e:
            print(f"Error discovering RDS resources: {e}")
        
        return resources
    
    def discover_s3_resources(self) -> List[Dict]:
        """Discover S3 buckets"""
        resources = []
        
        try:
            s3 = self.session.client('s3')
            
            response = s3.list_buckets()
            for bucket in response['Buckets']:
                # Try to get bucket location
                try:
                    location = s3.get_bucket_location(Bucket=bucket['Name'])
                    bucket_region = location['LocationConstraint'] or 'us-east-1'
                except ClientError:
                    bucket_region = 'unknown'
                
                # Get bucket size (approximate)
                try:
                    cloudwatch = self.session.client('cloudwatch')
                    metrics = cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='BucketSizeBytes',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket['Name']},
                            {'Name': 'StorageType', 'Value': 'StandardStorage'}
                        ],
                        StartTime=datetime.now() - timedelta(days=2),
                        EndTime=datetime.now(),
                        Period=86400,
                        Statistics=['Average']
                    )
                    bucket_size = metrics['Datapoints'][-1]['Average'] if metrics['Datapoints'] else 0
                except:
                    bucket_size = 0
                
                resources.append({
                    'resource_type': 'S3_Bucket',
                    'resource_id': bucket['Name'],
                    'name': bucket['Name'],
                    'status': 'active',
                    'region': bucket_region,
                    'created_at': bucket['CreationDate'].isoformat() if isinstance(bucket['CreationDate'], datetime) else str(bucket['CreationDate']),
                    'metadata': {
                        'region': bucket_region,
                        'size_bytes': bucket_size,
                        'health_status': 'healthy'
                    }
                })
                
        except ClientError as e:
            print(f"Error discovering S3 resources: {e}")
        
        return resources
    
    def discover_alb_resources(self) -> List[Dict]:
        """Discover Application Load Balancers"""
        resources = []
        
        try:
            elbv2 = self.session.client('elbv2')
            
            response = elbv2.describe_load_balancers()
            for lb in response['LoadBalancers']:
                # Check health status
                health_status = "healthy" if lb['State']['Code'] == 'active' else "unhealthy"
                
                resources.append({
                    'resource_type': 'ALB',
                    'resource_id': lb['LoadBalancerArn'],
                    'name': lb['LoadBalancerName'],
                    'status': lb['State']['Code'],
                    'region': self.region,
                    'created_at': lb.get('CreatedTime', datetime.now()).isoformat() if isinstance(lb.get('CreatedTime'), datetime) else str(lb.get('CreatedTime')),
                    'metadata': {
                        'dns_name': lb.get('DNSName'),
                        'scheme': lb.get('Scheme'),
                        'load_balancer_type': lb.get('Type'),
                        'vpc_id': lb.get('VpcId'),
                        'availability_zones': [az['ZoneName'] for az in lb.get('AvailabilityZones', [])],
                        'security_groups': lb.get('SecurityGroups', []),
                        'health_status': health_status
                    }
                })
                
        except ClientError as e:
            print(f"Error discovering ALB resources: {e}")
        
        return resources
    
    def discover_target_groups(self) -> List[Dict]:
        """Discover Target Groups"""
        resources = []
        
        try:
            elbv2 = self.session.client('elbv2')
            
            response = elbv2.describe_target_groups()
            for tg in response['TargetGroups']:
                # Get target health
                try:
                    health_response = elbv2.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
                    healthy_targets = sum(1 for target in health_response['TargetHealthDescriptions'] 
                                        if target['TargetHealth']['State'] == 'healthy')
                    total_targets = len(health_response['TargetHealthDescriptions'])
                    health_status = "healthy" if healthy_targets == total_targets and total_targets > 0 else "unhealthy"
                except ClientError:
                    healthy_targets = 0
                    total_targets = 0
                    health_status = "unknown"
                
                resources.append({
                    'resource_type': 'TargetGroup',
                    'resource_id': tg['TargetGroupArn'],
                    'name': tg['TargetGroupName'],
                    'status': 'active',
                    'region': self.region,
                    'created_at': None,
                    'metadata': {
                        'protocol': tg.get('Protocol'),
                        'port': tg.get('Port'),
                        'vpc_id': tg.get('VpcId'),
                        'target_type': tg.get('TargetType'),
                        'health_check_path': tg.get('HealthCheckPath'),
                        'health_check_protocol': tg.get('HealthCheckProtocol'),
                        'healthy_targets': healthy_targets,
                        'total_targets': total_targets,
                        'health_status': health_status
                    }
                })
                
        except ClientError as e:
            print(f"Error discovering Target Groups: {e}")
        
        return resources
    
    def discover_ecs_resources(self) -> List[Dict]:
        """Discover ECS clusters and services"""
        resources = []
        
        try:
            ecs = self.session.client('ecs')
            
            # ECS Clusters
            response = ecs.list_clusters()
            for cluster_arn in response['clusterArns']:
                cluster_details = ecs.describe_clusters(clusters=[cluster_arn])
                for cluster in cluster_details['clusters']:
                    health_status = "healthy" if cluster['status'] == 'ACTIVE' else "unhealthy"
                    
                    resources.append({
                        'resource_type': 'ECS_Cluster',
                        'resource_id': cluster['clusterArn'],
                        'name': cluster['clusterName'],
                        'status': cluster['status'],
                        'region': self.region,
                        'created_at': None,
                        'metadata': {
                            'running_tasks': cluster.get('runningTasksCount', 0),
                            'pending_tasks': cluster.get('pendingTasksCount', 0),
                            'active_services': cluster.get('activeServicesCount', 0),
                            'registered_container_instances': cluster.get('registeredContainerInstancesCount', 0),
                            'health_status': health_status
                        }
                    })
                    
                    # ECS Services in this cluster
                    try:
                        services_response = ecs.list_services(cluster=cluster_arn)
                        if services_response['serviceArns']:
                            service_details = ecs.describe_services(
                                cluster=cluster_arn,
                                services=services_response['serviceArns']
                            )
                            
                            for service in service_details['services']:
                                service_health = "healthy" if service['status'] == 'ACTIVE' and service.get('runningCount', 0) > 0 else "unhealthy"
                                
                                resources.append({
                                    'resource_type': 'ECS_Service',
                                    'resource_id': service['serviceArn'],
                                    'name': service['serviceName'],
                                    'status': service['status'],
                                    'region': self.region,
                                    'created_at': service.get('createdAt', datetime.now()).isoformat() if isinstance(service.get('createdAt'), datetime) else str(service.get('createdAt')),
                                    'metadata': {
                                        'cluster_name': cluster['clusterName'],
                                        'task_definition': service.get('taskDefinition'),
                                        'desired_count': service.get('desiredCount', 0),
                                        'running_count': service.get('runningCount', 0),
                                        'pending_count': service.get('pendingCount', 0),
                                        'launch_type': service.get('launchType'),
                                        'health_status': service_health
                                    }
                                })
                    except ClientError:
                        pass
                        
        except ClientError as e:
            print(f"Error discovering ECS resources: {e}")
        
        return resources
    
    def discover_lambda_resources(self) -> List[Dict]:
        """Discover Lambda functions"""
        resources = []
        
        try:
            lambda_client = self.session.client('lambda')
            
            paginator = lambda_client.get_paginator('list_functions')
            for page in paginator.paginate():
                for func in page['Functions']:
                    # Check if function has recent errors
                    health_status = "healthy"
                    try:
                        # Get function metrics from CloudWatch
                        cloudwatch = self.session.client('cloudwatch')
                        end_time = datetime.now()
                        start_time = end_time - timedelta(hours=1)
                        
                        error_metrics = cloudwatch.get_metric_statistics(
                            Namespace='AWS/Lambda',
                            MetricName='Errors',
                            Dimensions=[{'Name': 'FunctionName', 'Value': func['FunctionName']}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=300,
                            Statistics=['Sum']
                        )
                        
                        if error_metrics['Datapoints'] and any(dp['Sum'] > 0 for dp in error_metrics['Datapoints']):
                            health_status = "unhealthy"
                    except:
                        pass
                    
                    resources.append({
                        'resource_type': 'Lambda_Function',
                        'resource_id': func['FunctionArn'],
                        'name': func['FunctionName'],
                        'status': func.get('State', 'Active'),
                        'region': self.region,
                        'created_at': func.get('LastModified'),
                        'metadata': {
                            'runtime': func.get('Runtime'),
                            'handler': func.get('Handler'),
                            'code_size': func.get('CodeSize'),
                            'timeout': func.get('Timeout'),
                            'memory_size': func.get('MemorySize'),
                            'version': func.get('Version'),
                            'health_status': health_status
                        }
                    })
                    
        except ClientError as e:
            print(f"Error discovering Lambda resources: {e}")
        
        return resources
    
    def discover_cloudwatch_alarms(self) -> List[Dict]:
        """Discover CloudWatch Alarms"""
        resources = []
        
        try:
            cloudwatch = self.session.client('cloudwatch')
            
            paginator = cloudwatch.get_paginator('describe_alarms')
            for page in paginator.paginate():
                for alarm in page['MetricAlarms']:
                    health_status = "healthy" if alarm['StateValue'] == 'OK' else "unhealthy"
                    
                    resources.append({
                        'resource_type': 'CloudWatch_Alarm',
                        'resource_id': alarm['AlarmArn'],
                        'name': alarm['AlarmName'],
                        'status': alarm['StateValue'],
                        'region': self.region,
                        'created_at': alarm.get('AlarmConfigurationUpdatedTimestamp', datetime.now()).isoformat() if isinstance(alarm.get('AlarmConfigurationUpdatedTimestamp'), datetime) else str(alarm.get('AlarmConfigurationUpdatedTimestamp')),
                        'metadata': {
                            'metric_name': alarm.get('MetricName'),
                            'namespace': alarm.get('Namespace'),
                            'statistic': alarm.get('Statistic'),
                            'threshold': alarm.get('Threshold'),
                            'comparison_operator': alarm.get('ComparisonOperator'),
                            'state_reason': alarm.get('StateReason'),
                            'health_status': health_status
                        }
                    })
                    
        except ClientError as e:
            print(f"Error discovering CloudWatch Alarms: {e}")
        
        return resources
    
    def discover_vpc_resources(self) -> List[Dict]:
        """Discover VPC resources"""
        resources = []
        
        try:
            ec2 = self.session.client('ec2')
            
            # VPCs
            response = ec2.describe_vpcs()
            for vpc in response['Vpcs']:
                name = self._get_tag_value(vpc.get('Tags', []), 'Name', 'N/A')
                
                resources.append({
                    'resource_type': 'VPC',
                    'resource_id': vpc['VpcId'],
                    'name': name,
                    'status': vpc['State'],
                    'region': self.region,
                    'created_at': None,
                    'metadata': {
                        'cidr_block': vpc.get('CidrBlock'),
                        'is_default': vpc.get('IsDefault'),
                        'instance_tenancy': vpc.get('InstanceTenancy'),
                        'health_status': 'healthy' if vpc['State'] == 'available' else 'unhealthy'
                    }
                })
            
            # Subnets
            response = ec2.describe_subnets()
            for subnet in response['Subnets']:
                name = self._get_tag_value(subnet.get('Tags', []), 'Name', 'N/A')
                
                resources.append({
                    'resource_type': 'Subnet',
                    'resource_id': subnet['SubnetId'],
                    'name': name,
                    'status': subnet['State'],
                    'region': self.region,
                    'created_at': None,
                    'metadata': {
                        'vpc_id': subnet.get('VpcId'),
                        'cidr_block': subnet.get('CidrBlock'),
                        'availability_zone': subnet.get('AvailabilityZone'),
                        'available_ip_address_count': subnet.get('AvailableIpAddressCount'),
                        'health_status': 'healthy' if subnet['State'] == 'available' else 'unhealthy'
                    }
                })
                
        except ClientError as e:
            print(f"Error discovering VPC resources: {e}")
        
        return resources
    
    def discover_iam_resources(self) -> List[Dict]:
        """Discover IAM resources"""
        resources = []
        
        try:
            iam = self.session.client('iam')
            
            # IAM Roles
            paginator = iam.get_paginator('list_roles')
            for page in paginator.paginate():
                for role in page['Roles']:
                    resources.append({
                        'resource_type': 'IAM_Role',
                        'resource_id': role['Arn'],
                        'name': role['RoleName'],
                        'status': 'active',
                        'region': 'global',
                        'created_at': role.get('CreateDate', datetime.now()).isoformat() if isinstance(role.get('CreateDate'), datetime) else str(role.get('CreateDate')),
                        'metadata': {
                            'path': role.get('Path'),
                            'max_session_duration': role.get('MaxSessionDuration'),
                            'health_status': 'healthy'
                        }
                    })
                    
        except ClientError as e:
            print(f"Error discovering IAM resources: {e}")
        
        return resources
    
    def discover_route53_resources(self) -> List[Dict]:
        """Discover Route53 hosted zones"""
        resources = []
        
        try:
            route53 = self.session.client('route53')
            
            paginator = route53.get_paginator('list_hosted_zones')
            for page in paginator.paginate():
                for zone in page['HostedZones']:
                    resources.append({
                        'resource_type': 'Route53_HostedZone',
                        'resource_id': zone['Id'],
                        'name': zone['Name'],
                        'status': 'active',
                        'region': 'global',
                        'created_at': None,
                        'metadata': {
                            'resource_record_set_count': zone.get('ResourceRecordSetCount'),
                            'private_zone': zone.get('Config', {}).get('PrivateZone', False),
                            'health_status': 'healthy'
                        }
                    })
                    
        except ClientError as e:
            print(f"Error discovering Route53 resources: {e}")
        
        return resources
    
    def discover_elasticache_resources(self) -> List[Dict]:
        """Discover ElastiCache clusters"""
        resources = []
        
        try:
            elasticache = self.session.client('elasticache')
            
            # Redis clusters
            try:
                response = elasticache.describe_cache_clusters()
                for cluster in response['CacheClusters']:
                    health_status = "healthy" if cluster['CacheClusterStatus'] == 'available' else "unhealthy"
                    
                    resources.append({
                        'resource_type': 'ElastiCache_Cluster',
                        'resource_id': cluster['CacheClusterId'],
                        'name': cluster['CacheClusterId'],
                        'status': cluster['CacheClusterStatus'],
                        'region': self.region,
                        'created_at': cluster.get('CacheClusterCreateTime', datetime.now()).isoformat() if isinstance(cluster.get('CacheClusterCreateTime'), datetime) else str(cluster.get('CacheClusterCreateTime')),
                        'metadata': {
                            'engine': cluster.get('Engine'),
                            'engine_version': cluster.get('EngineVersion'),
                            'cache_node_type': cluster.get('CacheNodeType'),
                            'num_cache_nodes': cluster.get('NumCacheNodes'),
                            'health_status': health_status
                        }
                    })
            except ClientError:
                pass
                
        except ClientError as e:
            print(f"Error discovering ElastiCache resources: {e}")
        
        return resources
    
    def discover_elasticsearch_resources(self) -> List[Dict]:
        """Discover Elasticsearch domains"""
        resources = []
        
        try:
            es = self.session.client('es')
            
            response = es.list_domain_names()
            if response['DomainNames']:
                domain_names = [domain['DomainName'] for domain in response['DomainNames']]
                domain_details = es.describe_elasticsearch_domains(DomainNames=domain_names)
                
                for domain in domain_details['DomainStatusList']:
                    health_status = "healthy" if domain.get('Processing') == False else "unhealthy"
                    
                    resources.append({
                        'resource_type': 'Elasticsearch_Domain',
                        'resource_id': domain['ARN'],
                        'name': domain['DomainName'],
                        'status': 'active' if domain.get('Created') else 'creating',
                        'region': self.region,
                        'created_at': domain.get('Created', datetime.now()).isoformat() if isinstance(domain.get('Created'), datetime) else str(domain.get('Created')),
                        'metadata': {
                            'elasticsearch_version': domain.get('ElasticsearchVersion'),
                            'instance_type': domain.get('ElasticsearchClusterConfig', {}).get('InstanceType'),
                            'instance_count': domain.get('ElasticsearchClusterConfig', {}).get('InstanceCount'),
                            'health_status': health_status
                        }
                    })
                    
        except ClientError as e:
            print(f"Error discovering Elasticsearch resources: {e}")
        
        return resources
    
    def discover_sqs_resources(self) -> List[Dict]:
        """Discover SQS queues"""
        resources = []
        
        try:
            sqs = self.session.client('sqs')
            
            response = sqs.list_queues()
            for queue_url in response.get('QueueUrls', []):
                queue_name = queue_url.split('/')[-1]
                
                # Get queue attributes
                try:
                    attrs = sqs.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=['All']
                    )
                    attributes = attrs.get('Attributes', {})
                    
                    # Check if queue has DLQ or high message count
                    message_count = int(attributes.get('ApproximateNumberOfMessages', 0))
                    health_status = "healthy" if message_count < 1000 else "warning"
                    
                    created_timestamp = attributes.get('CreatedTimestamp')
                    created_at = datetime.fromtimestamp(int(created_timestamp)).isoformat() if created_timestamp else None
                    
                    resources.append({
                        'resource_type': 'SQS_Queue',
                        'resource_id': queue_url,
                        'name': queue_name,
                        'status': 'active',
                        'region': self.region,
                        'created_at': created_at,
                        'metadata': {
                            'message_count': message_count,
                            'visibility_timeout': attributes.get('VisibilityTimeout'),
                            'message_retention_period': attributes.get('MessageRetentionPeriod'),
                            'health_status': health_status
                        }
                    })
                except ClientError:
                    pass
                    
        except ClientError as e:
            print(f"Error discovering SQS resources: {e}")
        
        return resources
    
    def discover_sns_resources(self) -> List[Dict]:
        """Discover SNS topics"""
        resources = []
        
        try:
            sns = self.session.client('sns')
            
            paginator = sns.get_paginator('list_topics')
            for page in paginator.paginate():
                for topic in page['Topics']:
                    topic_name = topic['TopicArn'].split(':')[-1]
                    
                    # Get topic attributes
                    try:
                        attrs = sns.get_topic_attributes(TopicArn=topic['TopicArn'])
                        attributes = attrs.get('Attributes', {})
                        
                        resources.append({
                            'resource_type': 'SNS_Topic',
                            'resource_id': topic['TopicArn'],
                            'name': topic_name,
                            'status': 'active',
                            'region': self.region,
                            'created_at': None,
                            'metadata': {
                                'subscriptions_confirmed': attributes.get('SubscriptionsConfirmed', 0),
                                'subscriptions_pending': attributes.get('SubscriptionsPending', 0),
                                'health_status': 'healthy'
                            }
                        })
                    except ClientError:
                        pass
                        
        except ClientError as e:
            print(f"Error discovering SNS resources: {e}")
        
        return resources
    
    def discover_api_gateway_resources(self) -> List[Dict]:
        """Discover API Gateway APIs"""
        resources = []
        
        try:
            apigateway = self.session.client('apigateway')
            
            response = apigateway.get_rest_apis()
            for api in response['items']:
                resources.append({
                    'resource_type': 'API_Gateway',
                    'resource_id': api['id'],
                    'name': api['name'],
                    'status': 'active',
                    'region': self.region,
                    'created_at': api.get('createdDate', datetime.now()).isoformat() if isinstance(api.get('createdDate'), datetime) else str(api.get('createdDate')),
                    'metadata': {
                        'description': api.get('description'),
                        'version': api.get('version'),
                        'health_status': 'healthy'
                    }
                })
                
        except ClientError as e:
            print(f"Error discovering API Gateway resources: {e}")
        
        return resources
    
    def _get_tag_value(self, tags: List[Dict], key: str, default: str = '') -> str:
        """Get tag value by key"""
        for tag in tags:
            if tag.get('Key') == key:
                return tag.get('Value', default)
        return default
    
    def validate_credentials(self) -> bool:
        """Validate AWS credentials"""
        try:
            if not self.session:
                if not self.create_session():
                    return False
            
            sts = self.session.client('sts')
            sts.get_caller_identity()
            return True
        except (ClientError, NoCredentialsError):
            return False


# Import datetime.timedelta for S3 metrics
from datetime import timedelta

