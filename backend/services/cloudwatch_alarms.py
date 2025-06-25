"""
SelectNOC IA - CloudWatch Alarms Discovery
Módulo para descoberta e análise de alarmes reais do CloudWatch
"""

import boto3
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)

class CloudWatchAlarmsDiscovery:
    """
    Descoberta e análise de alarmes do CloudWatch
    """
    
    def __init__(self, access_key: str, secret_key: str, region: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.session = None
        
    def create_session(self):
        """Criar sessão AWS com credenciais"""
        try:
            self.session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            return True
        except Exception as e:
            logger.error("Erro criando sessão AWS", error=str(e))
            return False
    
    async def discover_all_alarms(self) -> List[Dict[str, Any]]:
        """
        Descobrir todos os alarmes CloudWatch da conta
        """
        if not self.session:
            if not self.create_session():
                return []
        
        try:
            cloudwatch = self.session.client('cloudwatch')
            all_alarms = []
            
            # Buscar alarmes métricos
            metric_alarms = await self._get_metric_alarms(cloudwatch)
            all_alarms.extend(metric_alarms)
            
            # Buscar alarmes compostos
            composite_alarms = await self._get_composite_alarms(cloudwatch)
            all_alarms.extend(composite_alarms)
            
            logger.info(f"Descobertos {len(all_alarms)} alarmes", region=self.region)
            return all_alarms
            
        except Exception as e:
            logger.error("Erro na descoberta de alarmes", error=str(e))
            return []
    
    async def _get_metric_alarms(self, cloudwatch) -> List[Dict[str, Any]]:
        """Buscar alarmes métricos"""
        alarms = []
        
        try:
            paginator = cloudwatch.get_paginator('describe_alarms')
            
            for page in paginator.paginate():
                for alarm in page['MetricAlarms']:
                    alarm_data = await self._process_metric_alarm(alarm, cloudwatch)
                    if alarm_data:
                        alarms.append(alarm_data)
                        
        except ClientError as e:
            logger.error("Erro buscando alarmes métricos", error=str(e))
        
        return alarms
    
    async def _get_composite_alarms(self, cloudwatch) -> List[Dict[str, Any]]:
        """Buscar alarmes compostos"""
        alarms = []
        
        try:
            paginator = cloudwatch.get_paginator('describe_alarms')
            
            for page in paginator.paginate(AlarmTypes=['CompositeAlarm']):
                for alarm in page['CompositeAlarms']:
                    alarm_data = await self._process_composite_alarm(alarm, cloudwatch)
                    if alarm_data:
                        alarms.append(alarm_data)
                        
        except ClientError as e:
            logger.error("Erro buscando alarmes compostos", error=str(e))
        
        return alarms
    
    async def _process_metric_alarm(self, alarm: Dict, cloudwatch) -> Optional[Dict[str, Any]]:
        """Processar alarme métrico"""
        try:
            # Determinar severidade baseada no estado e configuração
            severity = self._determine_alarm_severity(alarm)
            
            # Buscar histórico do alarme
            history = await self._get_alarm_history(alarm['AlarmName'], cloudwatch)
            
            # Buscar dados da métrica
            metric_data = await self._get_metric_statistics(alarm, cloudwatch)
            
            # Determinar recursos afetados
            affected_resources = self._extract_affected_resources(alarm)
            
            return {
                'alarm_name': alarm['AlarmName'],
                'alarm_arn': alarm['AlarmArn'],
                'alarm_type': 'metric',
                'state_value': alarm['StateValue'],
                'state_reason': alarm.get('StateReason', ''),
                'state_reason_data': alarm.get('StateReasonData', ''),
                'severity': severity,
                'metric_name': alarm.get('MetricName', ''),
                'namespace': alarm.get('Namespace', ''),
                'dimensions': alarm.get('Dimensions', []),
                'statistic': alarm.get('Statistic', ''),
                'threshold': alarm.get('Threshold', 0),
                'comparison_operator': alarm.get('ComparisonOperator', ''),
                'evaluation_periods': alarm.get('EvaluationPeriods', 0),
                'period': alarm.get('Period', 0),
                'description': alarm.get('AlarmDescription', ''),
                'actions_enabled': alarm.get('ActionsEnabled', False),
                'alarm_actions': alarm.get('AlarmActions', []),
                'ok_actions': alarm.get('OKActions', []),
                'insufficient_data_actions': alarm.get('InsufficientDataActions', []),
                'state_updated_timestamp': alarm.get('StateUpdatedTimestamp'),
                'configuration_updated_timestamp': alarm.get('AlarmConfigurationUpdatedTimestamp'),
                'affected_resources': affected_resources,
                'history': history,
                'metric_data': metric_data,
                'region': self.region,
                'created_at': datetime.now().isoformat(),
                'tags': await self._get_alarm_tags(alarm['AlarmArn'], cloudwatch)
            }
            
        except Exception as e:
            logger.error("Erro processando alarme métrico", alarm_name=alarm.get('AlarmName'), error=str(e))
            return None
    
    def _determine_alarm_severity(self, alarm: Dict) -> str:
        """Determinar severidade do alarme baseado no estado e configuração"""
        state = alarm['StateValue']
        
        if state == 'ALARM':
            # Analisar namespace e métrica para determinar criticidade
            namespace = alarm.get('Namespace', '')
            metric_name = alarm.get('MetricName', '')
            
            # Métricas críticas
            critical_patterns = [
                ('AWS/EC2', ['StatusCheckFailed', 'CPUUtilization']),
                ('AWS/RDS', ['DatabaseConnections', 'CPUUtilization']),
                ('AWS/ELB', ['UnHealthyHostCount', 'HTTPCode_ELB_5XX']),
                ('AWS/ApplicationELB', ['UnHealthyHostCount', 'HTTPCode_ELB_5XX']),
                ('AWS/ECS', ['CPUUtilization', 'MemoryUtilization']),
                ('AWS/Lambda', ['Errors', 'Duration'])
            ]
            
            for ns, metrics in critical_patterns:
                if namespace == ns and any(metric in metric_name for metric in metrics):
                    return 'CRITICAL'
            
            return 'HIGH'
        
        elif state == 'INSUFFICIENT_DATA':
            return 'MEDIUM'
        
        else:  # OK
            return 'LOW'
    
    async def _get_alarm_history(self, alarm_name: str, cloudwatch, max_records: int = 10) -> List[Dict]:
        """Buscar histórico do alarme"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)  # Últimas 24 horas
            
            response = cloudwatch.describe_alarm_history(
                AlarmName=alarm_name,
                StartDate=start_time,
                EndDate=end_time,
                MaxRecords=max_records,
                ScanBy='TimestampDescending'
            )
            
            return [
                {
                    'timestamp': item.get('Timestamp'),
                    'history_item_type': item.get('HistoryItemType'),
                    'history_summary': item.get('HistorySummary'),
                    'history_data': item.get('HistoryData')
                }
                for item in response.get('AlarmHistoryItems', [])
            ]
            
        except ClientError as e:
            logger.error("Erro buscando histórico do alarme", alarm_name=alarm_name, error=str(e))
            return []
    
    def _extract_affected_resources(self, alarm: Dict) -> List[str]:
        """Extrair recursos afetados do alarme baseado nas dimensões"""
        resources = []
        
        for dimension in alarm.get('Dimensions', []):
            name = dimension.get('Name')
            value = dimension.get('Value')
            
            if name == 'InstanceId':
                resources.append(f"EC2:{value}")
            elif name == 'DBInstanceIdentifier':
                resources.append(f"RDS:{value}")
            elif name == 'LoadBalancer':
                resources.append(f"ELB:{value}")
            elif name == 'TargetGroup':
                resources.append(f"TargetGroup:{value}")
            elif name == 'FunctionName':
                resources.append(f"Lambda:{value}")
            elif name == 'ServiceName':
                resources.append(f"ECS:{value}")
            elif name == 'ClusterName':
                resources.append(f"ECS_Cluster:{value}")
            elif name == 'BucketName':
                resources.append(f"S3:{value}")
        
        return resources
    
    async def _get_alarm_tags(self, alarm_arn: str, cloudwatch) -> List[Dict]:
        """Buscar tags do alarme"""
        try:
            response = cloudwatch.list_tags_for_resource(ResourceARN=alarm_arn)
            return response.get('Tags', [])
        except ClientError:
            return []
    
    def validate_credentials(self) -> bool:
        """Validar credenciais AWS"""
        try:
            if not self.session:
                if not self.create_session():
                    return False
            
            sts = self.session.client('sts')
            sts.get_caller_identity()
            return True
        except (ClientError, NoCredentialsError):
            return False

    async def _get_metric_statistics(self, alarm: Dict, cloudwatch) -> Optional[Dict]:
        """Buscar estatísticas da métrica do alarme"""
        try:
            if alarm['StateValue'] != 'ALARM':
                return None
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)  # Última hora
            
            metric_params = {
                'Namespace': alarm.get('Namespace'),
                'MetricName': alarm.get('MetricName'),
                'Dimensions': alarm.get('Dimensions', []),
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': alarm.get('Period', 300),
                'Statistics': [alarm.get('Statistic', 'Average')]
            }
            
            response = cloudwatch.get_metric_statistics(**metric_params)
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                # Ordenar por timestamp
                datapoints.sort(key=lambda x: x['Timestamp'])
                
                return {
                    'latest_value': datapoints[-1].get(alarm.get('Statistic', 'Average')),
                    'latest_timestamp': datapoints[-1].get('Timestamp'),
                    'threshold': alarm.get('Threshold'),
                    'comparison_operator': alarm.get('ComparisonOperator'),
                    'datapoint_count': len(datapoints),
                    'recent_datapoints': datapoints[-5:]  # Últimos 5 pontos
                }
            
            return None
            
        except ClientError as e:
            logger.error("Erro buscando estatísticas da métrica", error=str(e))
            return None

    async def _process_composite_alarm(self, alarm: Dict, cloudwatch) -> Optional[Dict[str, Any]]:
        """Processar alarme composto"""
        try:
            severity = self._determine_alarm_severity(alarm)
            history = await self._get_alarm_history(alarm['AlarmName'], cloudwatch)
            
            return {
                'alarm_name': alarm['AlarmName'],
                'alarm_arn': alarm['AlarmArn'],
                'alarm_type': 'composite',
                'state_value': alarm['StateValue'],
                'state_reason': alarm.get('StateReason', ''),
                'state_reason_data': alarm.get('StateReasonData', ''),
                'severity': severity,
                'alarm_rule': alarm.get('AlarmRule', ''),
                'description': alarm.get('AlarmDescription', ''),
                'actions_enabled': alarm.get('ActionsEnabled', False),
                'alarm_actions': alarm.get('AlarmActions', []),
                'ok_actions': alarm.get('OKActions', []),
                'insufficient_data_actions': alarm.get('InsufficientDataActions', []),
                'state_updated_timestamp': alarm.get('StateUpdatedTimestamp'),
                'configuration_updated_timestamp': alarm.get('AlarmConfigurationUpdatedTimestamp'),
                'affected_resources': [],
                'history': history,
                'region': self.region,
                'created_at': datetime.now().isoformat(),
                'tags': await self._get_alarm_tags(alarm['AlarmArn'], cloudwatch),
                # Campos específicos para composite
                'metric_name': '',
                'namespace': '',
                'dimensions': [],
                'statistic': '',
                'threshold': 0,
                'comparison_operator': '',
                'evaluation_periods': 0,
                'period': 0,
                'metric_data': None
            }
            
        except Exception as e:
            logger.error("Erro processando alarme composto", alarm_name=alarm.get('AlarmName'), error=str(e))
            return None
