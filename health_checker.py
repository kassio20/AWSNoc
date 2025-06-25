"""
AWSNoc IA IA - Health Checker
Sistema inteligente para detectar problemas reais em recursos AWS
"""

import boto3
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import psycopg2
import psycopg2.extras

class HealthChecker:
    """
    Verificador de saúde dos recursos AWS
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def get_db_connection(self):
        """Obter conexão com banco"""
        return psycopg2.connect(**self.db_config)
    
    async def check_all_resources_health(self) -> List[Dict[str, Any]]:
        """
        Verificar saúde de todos os recursos
        """
        alerts = []
        
        # Buscar todas as contas
        accounts = self._get_all_accounts()
        
        for account in accounts:
            try:
                session = boto3.Session(
                    aws_access_key_id=account['access_key'],
                    aws_secret_access_key=account['secret_key'],
                    region_name=account['region']
                )
                
                # Verificar Target Groups
                tg_alerts = await self._check_target_groups_health(session, account)
                alerts.extend(tg_alerts)
                
                # Verificar ECS Services
                ecs_alerts = await self._check_ecs_services_health(session, account)
                alerts.extend(ecs_alerts)
                
                # Verificar EC2 Instances
                ec2_alerts = await self._check_ec2_instances_health(session, account)
                alerts.extend(ec2_alerts)
                
                # Verificar RDS Instances
                rds_alerts = await self._check_rds_instances_health(session, account)
                alerts.extend(rds_alerts)
                
            except Exception as e:
                print(f"Erro verificando saúde da conta {account['name']}: {e}")
                continue
        
        # Salvar alertas no banco
        await self._save_health_alerts(alerts)
        
        return alerts
    
    async def _check_target_groups_health(self, session, account) -> List[Dict[str, Any]]:
        """Verificar saúde dos Target Groups"""
        alerts = []
        
        try:
            elbv2 = session.client('elbv2')
            
            # Buscar todos os Target Groups
            response = elbv2.describe_target_groups()
            
            for tg in response['TargetGroups']:
                try:
                    # Verificar saúde dos targets
                    health_response = elbv2.describe_target_health(
                        TargetGroupArn=tg['TargetGroupArn']
                    )
                    
                    targets = health_response['TargetHealthDescriptions']
                    healthy_targets = [t for t in targets if t['TargetHealth']['State'] == 'healthy']
                    unhealthy_targets = [t for t in targets if t['TargetHealth']['State'] != 'healthy']
                    
                    if len(targets) == 0:
                        # Nenhum target registrado
                        alerts.append({
                            'account_id': account['id'],
                            'account_name': account['name'],
                            'aws_account_id': account['account_id'],
                            'resource_type': 'TargetGroup',
                            'resource_id': tg['TargetGroupArn'],
                            'resource_name': tg['TargetGroupName'],
                            'alert_type': 'health_check',
                            'severity': 'critical',
                            'title': f"Target Group {tg['TargetGroupName']} - No Targets Registered",
                            'description': f"Target Group {tg['TargetGroupName']} has no targets registered",
                            'status': 'active',
                            'region': account['region'],
                            'metadata': {
                                'target_group_arn': tg['TargetGroupArn'],
                                'target_count': 0,
                                'healthy_count': 0,
                                'unhealthy_count': 0,
                                'protocol': tg.get('Protocol'),
                                'port': tg.get('Port')
                            }
                        })
                    elif len(unhealthy_targets) > 0:
                        # Alguns targets não saudáveis
                        severity = 'critical' if len(healthy_targets) == 0 else 'high'
                        
                        alerts.append({
                            'account_id': account['id'],
                            'account_name': account['name'],
                            'aws_account_id': account['account_id'],
                            'resource_type': 'TargetGroup',
                            'resource_id': tg['TargetGroupArn'],
                            'resource_name': tg['TargetGroupName'],
                            'alert_type': 'health_check',
                            'severity': severity,
                            'title': f"Target Group {tg['TargetGroupName']} - Unhealthy Targets",
                            'description': f"Target Group {tg['TargetGroupName']} has {len(unhealthy_targets)} unhealthy targets out of {len(targets)} total",
                            'status': 'active',
                            'region': account['region'],
                            'metadata': {
                                'target_group_arn': tg['TargetGroupArn'],
                                'target_count': len(targets),
                                'healthy_count': len(healthy_targets),
                                'unhealthy_count': len(unhealthy_targets),
                                'protocol': tg.get('Protocol'),
                                'port': tg.get('Port'),
                                'unhealthy_reasons': [t['TargetHealth'].get('Reason', 'Unknown') for t in unhealthy_targets]
                            }
                        })
                
                except Exception as e:
                    print(f"Erro verificando Target Group {tg['TargetGroupName']}: {e}")
                    continue
        
        except Exception as e:
            print(f"Erro listando Target Groups: {e}")
        
        return alerts
    
    async def _check_ecs_services_health(self, session, account) -> List[Dict[str, Any]]:
        """Verificar saúde dos ECS Services"""
        alerts = []
        
        try:
            ecs = session.client('ecs')
            
            # Buscar todos os clusters
            clusters_response = ecs.list_clusters()
            
            for cluster_arn in clusters_response['clusterArns']:
                try:
                    # Buscar serviços do cluster
                    services_response = ecs.list_services(cluster=cluster_arn)
                    
                    if not services_response['serviceArns']:
                        continue
                    
                    # Descrever serviços
                    services_detail = ecs.describe_services(
                        cluster=cluster_arn,
                        services=services_response['serviceArns']
                    )
                    
                    for service in services_detail['services']:
                        running_count = service.get('runningCount', 0)
                        desired_count = service.get('desiredCount', 0)
                        pending_count = service.get('pendingCount', 0)
                        
                        if running_count < desired_count:
                            severity = 'critical' if running_count == 0 else 'high'
                            
                            alerts.append({
                                'account_id': account['id'],
                                'account_name': account['name'],
                                'aws_account_id': account['account_id'],
                                'resource_type': 'ECS_Service',
                                'resource_id': service['serviceArn'],
                                'resource_name': service['serviceName'],
                                'alert_type': 'health_check',
                                'severity': severity,
                                'title': f"ECS Service {service['serviceName']} - Unhealthy",
                                'description': f"ECS Service {service['serviceName']} has {running_count} running tasks out of {desired_count} desired ({pending_count} pending)",
                                'status': 'active',
                                'region': account['region'],
                                'metadata': {
                                    'service_arn': service['serviceArn'],
                                    'cluster_arn': cluster_arn,
                                    'running_count': running_count,
                                    'desired_count': desired_count,
                                    'pending_count': pending_count,
                                    'task_definition': service.get('taskDefinition'),
                                    'launch_type': service.get('launchType')
                                }
                            })
                
                except Exception as e:
                    print(f"Erro verificando serviços do cluster {cluster_arn}: {e}")
                    continue
        
        except Exception as e:
            print(f"Erro listando clusters ECS: {e}")
        
        return alerts
    
    async def _check_ec2_instances_health(self, session, account) -> List[Dict[str, Any]]:
        """Verificar saúde das instâncias EC2"""
        alerts = []
        
        try:
            ec2 = session.client('ec2')
            
            # Buscar todas as instâncias
            response = ec2.describe_instances()
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    state = instance['State']['Name']
                    
                    if state in ['stopped', 'stopping', 'terminated', 'terminating']:
                        severity = 'critical' if state in ['terminated', 'terminating'] else 'high'
                        
                        name = ''
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                        
                        alerts.append({
                            'account_id': account['id'],
                            'account_name': account['name'],
                            'aws_account_id': account['account_id'],
                            'resource_type': 'EC2_Instance',
                            'resource_id': instance['InstanceId'],
                            'resource_name': name or instance['InstanceId'],
                            'alert_type': 'health_check',
                            'severity': severity,
                            'title': f"EC2 Instance {name or instance['InstanceId']} - {state.title()}",
                            'description': f"EC2 Instance {instance['InstanceId']} is in {state} state",
                            'status': 'active',
                            'region': account['region'],
                            'metadata': {
                                'instance_id': instance['InstanceId'],
                                'instance_type': instance.get('InstanceType'),
                                'instance_state': state,
                                'vpc_id': instance.get('VpcId'),
                                'subnet_id': instance.get('SubnetId'),
                                'private_ip': instance.get('PrivateIpAddress'),
                                'public_ip': instance.get('PublicIpAddress')
                            }
                        })
        
        except Exception as e:
            print(f"Erro verificando instâncias EC2: {e}")
        
        return alerts
    
    async def _check_rds_instances_health(self, session, account) -> List[Dict[str, Any]]:
        """Verificar saúde das instâncias RDS"""
        alerts = []
        
        try:
            rds = session.client('rds')
            
            # Buscar todas as instâncias RDS
            response = rds.describe_db_instances()
            
            for db in response['DBInstances']:
                status = db['DBInstanceStatus']
                
                if status != 'available':
                    severity = 'critical' if status in ['failed', 'stopped'] else 'high'
                    
                    alerts.append({
                        'account_id': account['id'],
                        'account_name': account['name'],
                        'aws_account_id': account['account_id'],
                        'resource_type': 'RDS_Instance',
                        'resource_id': db['DBInstanceIdentifier'],
                        'resource_name': db['DBInstanceIdentifier'],
                        'alert_type': 'health_check',
                        'severity': severity,
                        'title': f"RDS Instance {db['DBInstanceIdentifier']} - {status.title()}",
                        'description': f"RDS Instance {db['DBInstanceIdentifier']} is in {status} state",
                        'status': 'active',
                        'region': account['region'],
                        'metadata': {
                            'db_instance_identifier': db['DBInstanceIdentifier'],
                            'db_instance_class': db.get('DBInstanceClass'),
                            'db_instance_status': status,
                            'engine': db.get('Engine'),
                            'engine_version': db.get('EngineVersion'),
                            'allocated_storage': db.get('AllocatedStorage'),
                            'multi_az': db.get('MultiAZ')
                        }
                    })
        
        except Exception as e:
            print(f"Erro verificando instâncias RDS: {e}")
        
        return alerts
    
    async def _save_health_alerts(self, alerts: List[Dict[str, Any]]):
        """Salvar alertas de saúde no banco"""
        if not alerts:
            return
        
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Limpar alertas antigos de health_check
            cur.execute("DELETE FROM alerts WHERE alert_type = 'health_check'")
            
            # Inserir novos alertas
            for alert in alerts:
                cur.execute("""
                    INSERT INTO alerts (
                        account_id, resource_id, resource_type, alert_type, 
                        severity, title, description, status, ai_analysis, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    alert['account_id'],
                    alert['resource_id'],
                    alert['resource_type'],
                    alert['alert_type'],
                    alert['severity'],
                    alert['title'],
                    alert['description'],
                    alert['status'],
                    json.dumps(alert.get('metadata', {})),
                    datetime.now()
                ))
            
            conn.commit()
            print(f"Salvos {len(alerts)} alertas de saúde no banco")
            
        except Exception as e:
            print(f"Erro salvando alertas de saúde: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _get_all_accounts(self) -> List[Dict[str, Any]]:
        """Buscar todas as contas ativas"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute("SELECT * FROM aws_accounts WHERE status = 'active'")
            accounts = cur.fetchall()
            
            return [dict(account) for account in accounts]
            
        except Exception as e:
            print(f"Erro buscando contas: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()

# Função utilitária para executar verificação
async def run_health_check(db_config):
    """Executar verificação de saúde"""
    checker = HealthChecker(db_config)
    alerts = await checker.check_all_resources_health()
    return alerts

if __name__ == "__main__":
    # Configuração do banco (deve ser a mesma do simple_main.py)
    DB_CONFIG = {
        "host": "awsnoc-ia-dev-database.cjeqe6pc2viw.us-east-2.rds.amazonaws.com",
        "port": 5432,
        "database": "awsnoc-ia",
        "user": "awsnoc-ia_admin", 
        "password": "Dy6uGR1UVasJEp7D"
    }
    
    async def main():
        alerts = await run_health_check(DB_CONFIG)
        print(f"Encontrados {len(alerts)} alertas de saúde")
        for alert in alerts:
            print(f"- {alert['severity'].upper()}: {alert['title']}")
    
    asyncio.run(main())
