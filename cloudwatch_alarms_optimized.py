"""
AWSNoc IA IA - CloudWatch Alarms Discovery - Versão Otimizada
Módulo otimizado para descoberta e análise de alarmes com cache e controle de custos
"""

import boto3
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
import logging
import time

# Importar configurações e cache
try:
    from config.cloudwatch_config import CloudWatchConfig
    from services.cloudwatch_cache import cache_manager
except ImportError:
    # Fallback para configurações padrão se os módulos não existirem
    class CloudWatchConfig:
        POLLING_INTERVALS = {'alarms': 30}
        CACHE_TTL = {'alarms': 25}
        QUERY_LIMITS = {'max_alarm_history_records': 10, 'history_hours': 24}
        OPTIMIZATION = {'cache_enabled': True}
        ALARM_POLLING_BY_STATE = {'ALARM': 30, 'OK': 120, 'INSUFFICIENT_DATA': 60}
        
        @classmethod
        def get_cache_ttl(cls, component): return 25
        @classmethod
        def should_use_cache(cls): return True
        @classmethod
        def get_alarm_polling_interval(cls, state): return 30
    
    # Mock cache manager se não disponível
    class MockCacheManager:
        def get_cached_alarms(self, *args): return None
        def cache_alarms(self, *args, **kwargs): pass
        def get_cached_alarm_history(self, *args): return None
        def cache_alarm_history(self, *args, **kwargs): pass
        def periodic_cleanup(self): pass
    
    cache_manager = MockCacheManager()

logger = logging.getLogger(__name__)

class OptimizedCloudWatchAlarmsDiscovery:
    """
    Descoberta otimizada de alarmes do CloudWatch com cache e controle de custos
    """
    
    def __init__(self, access_key: str, secret_key: str, region: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.session = None
        self.last_full_discovery = 0
        self.last_incremental_check = 0
        
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
            logger.error("Erro criando sessão AWS", extra={'error': str(e)})
            return False
    
    async def discover_all_alarms(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Descobrir alarmes com otimizações de cache e polling inteligente
        """
        current_time = time.time()
        
        # Verificar cache primeiro se não for refresh forçado
        if not force_refresh and CloudWatchConfig.should_use_cache():
            cached_alarms = cache_manager.get_cached_alarms()
            if cached_alarms:
                logger.info(f"Usando alarmes do cache: {len(cached_alarms)} alarmes")
                return cached_alarms
        
        # Verificar se precisa fazer descoberta completa ou incremental
        polling_interval = CloudWatchConfig.get_polling_interval('alarms')
        
        if current_time - self.last_incremental_check < polling_interval and not force_refresh:
            logger.debug("Polling interval não atingido, retornando cache")
            return cache_manager.get_cached_alarms() or []
        
        if not self.session:
            if not self.create_session():
                return []
        
        try:
            cloudwatch = self.session.client('cloudwatch')
            all_alarms = []
            
            # Buscar alarmes métricos de forma otimizada
            metric_alarms = await self._get_metric_alarms_optimized(cloudwatch)
            all_alarms.extend(metric_alarms)
            
            # Buscar alarmes compostos
            composite_alarms = await self._get_composite_alarms_optimized(cloudwatch)
            all_alarms.extend(composite_alarms)
            
            # Atualizar timestamps
            self.last_incremental_check = current_time
            if force_refresh or current_time - self.last_full_discovery > 300:  # 5 minutos
                self.last_full_discovery = current_time
            
            # Armazenar no cache
            if CloudWatchConfig.should_use_cache():
                ttl = CloudWatchConfig.get_cache_ttl('alarms')
                cache_manager.cache_alarms(all_alarms, ttl=ttl)
            
            logger.info(f"Descobertos {len(all_alarms)} alarmes na região {self.region}")
            return all_alarms
            
        except Exception as e:
            logger.error("Erro na descoberta de alarmes", extra={'error': str(e)})
            return []
    
    async def _get_metric_alarms_optimized(self, cloudwatch) -> List[Dict[str, Any]]:
        """Buscar alarmes métricos de forma otimizada"""
        alarms = []
        
        try:
            # Usar paginação mais eficiente
            paginator = cloudwatch.get_paginator('describe_alarms')
            page_iterator = paginator.paginate(
                PaginationConfig={
                    'MaxItems': 100,  # Limitar itens por página
                    'PageSize': 50    # Tamanho da página
                }
            )
            
            for page in page_iterator:
                # Processar alarmes em lote
                batch_tasks = []
                for alarm in page.get('MetricAlarms', []):
                    task = self._process_metric_alarm_optimized(alarm, cloudwatch)
                    batch_tasks.append(task)
                
                # Executar em lote com limite de concorrência
                if batch_tasks:
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    for result in batch_results:
                        if isinstance(result, dict):
                            alarms.append(result)
                        elif not isinstance(result, Exception):
                            logger.error(f"Resultado inesperado: {result}")
                
                # Pequena pausa para não sobrecarregar a API
                await asyncio.sleep(0.1)
                        
        except ClientError as e:
            logger.error("Erro buscando alarmes métricos", extra={'error': str(e)})
        
        return alarms
    
    async def _get_composite_alarms_optimized(self, cloudwatch) -> List[Dict[str, Any]]:
        """Buscar alarmes compostos de forma otimizada"""
        alarms = []
        
        try:
            paginator = cloudwatch.get_paginator('describe_alarms')
            page_iterator = paginator.paginate(
                AlarmTypes=['CompositeAlarm'],
                PaginationConfig={'PageSize': 50}
            )
            
            for page in page_iterator:
                for alarm in page.get('CompositeAlarms', []):
                    alarm_data = await self._process_composite_alarm_optimized(alarm, cloudwatch)
                    if alarm_data:
                        alarms.append(alarm_data)
                
                await asyncio.sleep(0.1)
                        
        except ClientError as e:
            logger.error("Erro buscando alarmes compostos", extra={'error': str(e)})
        
        return alarms
    
    async def _process_metric_alarm_optimized(self, alarm: Dict, cloudwatch) -> Optional[Dict[str, Any]]:
        """Processar alarme métrico de forma otimizada"""
        try:
            alarm_name = alarm['AlarmName']
            state = alarm['StateValue']
            
            # Determinar severidade
            severity = self._determine_alarm_severity(alarm)
            
            # Buscar histórico apenas se necessário e com cache
            history = []
            if state == 'ALARM':  # Só buscar histórico para alarmes ativos
                history = await self._get_alarm_history_cached(alarm_name, cloudwatch)
            
            # Buscar dados da métrica apenas para alarmes em ALARM
            metric_data = None
            if state == 'ALARM':
                metric_data = await self._get_metric_statistics_optimized(alarm, cloudwatch)
            
            # Extrair recursos afetados
            affected_resources = self._extract_affected_resources(alarm)
            
            # Buscar tags apenas se necessário
            tags = []
            if alarm.get('AlarmArn'):
                tags = await self._get_alarm_tags_cached(alarm['AlarmArn'], cloudwatch)
            
            return {
                'alarm_name': alarm_name,
                'alarm_arn': alarm['AlarmArn'],
                'alarm_type': 'metric',
                'state_value': state,
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
                'tags': tags,
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Erro processando alarme métrico", 
                        extra={'alarm_name': alarm.get('AlarmName'), 'error': str(e)})
            return None
    
    async def _get_alarm_history_cached(self, alarm_name: str, cloudwatch, 
                                      hours: int = 24) -> List[Dict]:
        """Buscar histórico do alarme com cache"""
        try:
            # Verificar cache primeiro
            if CloudWatchConfig.should_use_cache():
                cached_history = cache_manager.get_cached_alarm_history(alarm_name, hours)
                if cached_history:
                    return cached_history
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            max_records = CloudWatchConfig.QUERY_LIMITS.get('max_alarm_history_records', 10)
            
            response = cloudwatch.describe_alarm_history(
                AlarmName=alarm_name,
                StartDate=start_time,
                EndDate=end_time,
                MaxRecords=max_records,
                ScanBy='TimestampDescending'
            )
            
            history = [
                {
                    'timestamp': item.get('Timestamp'),
                    'history_item_type': item.get('HistoryItemType'),
                    'history_summary': item.get('HistorySummary'),
                    'history_data': item.get('HistoryData')
                }
                for item in response.get('AlarmHistoryItems', [])
            ]
            
            # Armazenar no cache
            if CloudWatchConfig.should_use_cache():
                cache_manager.cache_alarm_history(history, alarm_name, hours)
            
            return history
            
        except ClientError as e:
            logger.error("Erro buscando histórico do alarme", 
                        extra={'alarm_name': alarm_name, 'error': str(e)})
            return []
    
    async def _get_metric_statistics_optimized(self, alarm: Dict, cloudwatch) -> Optional[Dict]:
        """Buscar estatísticas da métrica de forma otimizada"""
        try:
            if alarm['StateValue'] != 'ALARM':
                return None
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)  # Reduzido para 1 hora
            
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
                    'recent_datapoints': datapoints[-3:]  # Reduzido para 3 pontos
                }
            
            return None
            
        except ClientError as e:
            logger.error("Erro buscando estatísticas da métrica", extra={'error': str(e)})
            return None
    
    async def _get_alarm_tags_cached(self, alarm_arn: str, cloudwatch) -> List[Dict]:
        """Buscar tags do alarme com cache simples"""
        try:
            response = cloudwatch.list_tags_for_resource(ResourceARN=alarm_arn)
            return response.get('Tags', [])
        except ClientError:
            return []
    
    def _determine_alarm_severity(self, alarm: Dict) -> str:
        """Determinar severidade do alarme baseado no estado e configuração"""
        state = alarm['StateValue']
        
        if state == 'ALARM':
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
    
    def _extract_affected_resources(self, alarm: Dict) -> List[str]:
        """Extrair recursos afetados do alarme baseado nas dimensões"""
        resources = []
        
        for dimension in alarm.get('Dimensions', []):
            name = dimension.get('Name')
            value = dimension.get('Value')
            
            resource_mapping = {
                'InstanceId': f"EC2:{value}",
                'DBInstanceIdentifier': f"RDS:{value}",
                'LoadBalancer': f"ELB:{value}",
                'TargetGroup': f"TargetGroup:{value}",
                'FunctionName': f"Lambda:{value}",
                'ServiceName': f"ECS:{value}",
                'ClusterName': f"ECS_Cluster:{value}",
                'BucketName': f"S3:{value}"
            }
            
            if name in resource_mapping:
                resources.append(resource_mapping[name])
        
        return resources
    
    async def _process_composite_alarm_optimized(self, alarm: Dict, cloudwatch) -> Optional[Dict[str, Any]]:
        """Processar alarme composto de forma otimizada"""
        try:
            severity = self._determine_alarm_severity(alarm)
            
            # Histórico apenas para alarmes ativos
            history = []
            if alarm['StateValue'] == 'ALARM':
                history = await self._get_alarm_history_cached(alarm['AlarmName'], cloudwatch)
            
            # Tags apenas se necessário
            tags = []
            if alarm.get('AlarmArn'):
                tags = await self._get_alarm_tags_cached(alarm['AlarmArn'], cloudwatch)
            
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
                'tags': tags,
                'last_checked': datetime.now().isoformat(),
                # Campos específicos para composite (compatibilidade)
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
            logger.error("Erro processando alarme composto", 
                        extra={'alarm_name': alarm.get('AlarmName'), 'error': str(e)})
            return None
    
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
    
    def cleanup_cache(self):
        """Limpeza periódica do cache"""
        if hasattr(cache_manager, 'periodic_cleanup'):
            cache_manager.periodic_cleanup()

# Alias para compatibilidade com código existente
CloudWatchAlarmsDiscovery = OptimizedCloudWatchAlarmsDiscovery
