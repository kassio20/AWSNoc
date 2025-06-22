"""
SelectNOC IA - AWS Collector with Native AI Integration
Coleta dados do CloudWatch e integra diretamente com Bedrock para análise
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LogEvent:
    """Estrutura padronizada para eventos de log"""
    timestamp: datetime
    message: str
    service_name: str
    log_group: str
    log_stream: str
    account_id: str
    region: str
    metadata: Dict[str, Any]


class AWSCollector:
    """
    Coletor AWS integrado com Bedrock para análise em tempo real
    """
    
    def __init__(self, account_config: Dict[str, Any]):
        self.account_config = account_config
        self.account_id = account_config["account_id"]
        self.region = account_config["region"]
        
        # Inicializar clientes AWS
        self._init_aws_clients()
        
        # Cliente Bedrock para análise imediata
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=account_config.get("bedrock_region", "us-east-1")
        )
        
        # Cache para evitar análises duplicadas
        self._analysis_cache = {}
        
    def _init_aws_clients(self):
        """Inicializa clientes AWS baseado no método de autenticação"""
        auth_method = self.account_config["auth_method"]
        
        if auth_method == "assume_role":
            # Cross-account role
            sts_client = boto3.client('sts')
            assumed_role = sts_client.assume_role(
                RoleArn=self.account_config["credentials"]["role_arn"],
                RoleSessionName=self.account_config["credentials"]["session_name"],
                ExternalId=self.account_config["credentials"].get("external_id")
            )
            
            credentials = assumed_role['Credentials']
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
        elif auth_method == "profile":
            # Profile local
            session = boto3.Session(
                profile_name=self.account_config["credentials"]["profile_name"]
            )
            
        elif auth_method == "access_keys":
            # Access keys diretas
            session = boto3.Session(
                aws_access_key_id=self.account_config["credentials"]["access_key_id"],
                aws_secret_access_key=self.account_config["credentials"]["secret_access_key"]
            )
            
        else:  # instance_profile
            # EC2 instance profile
            session = boto3.Session()
        
        # Inicializar clientes específicos
        self.cloudwatch_logs = session.client('logs', region_name=self.region)
        self.cloudwatch_metrics = session.client('cloudwatch', region_name=self.region)
        self.ecs_client = session.client('ecs', region_name=self.region)
        self.elb_client = session.client('elbv2', region_name=self.region)
        self.rds_client = session.client('rds', region_name=self.region)
        
    async def collect_real_time_logs(self, log_groups: List[str]) -> List[LogEvent]:
        """
        Coleta logs em tempo real e aplica análise de IA imediata
        """
        all_events = []
        
        for log_group in log_groups:
            try:
                # Buscar logs dos últimos 5 minutos
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(minutes=5)
                
                response = self.cloudwatch_logs.filter_log_events(
                    logGroupName=log_group,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000)
                )
                
                for event in response.get('events', []):
                    log_event = LogEvent(
                        timestamp=datetime.fromtimestamp(event['timestamp'] / 1000),
                        message=event['message'],
                        service_name=self._extract_service_name(log_group),
                        log_group=log_group,
                        log_stream=event.get('logStreamName', ''),
                        account_id=self.account_id,
                        region=self.region,
                        metadata={}
                    )
                    
                    # Análise imediata com Bedrock se for um log de erro
                    if self._is_error_log(event['message']):
                        analysis = await self._analyze_log_with_bedrock(log_event)
                        log_event.metadata['ai_analysis'] = analysis
                    
                    all_events.append(log_event)
                    
            except ClientError as e:
                logger.error(
                    "Erro ao coletar logs",
                    log_group=log_group,
                    account_id=self.account_id,
                    error=str(e)
                )
        
        return all_events
    
    async def _analyze_log_with_bedrock(self, log_event: LogEvent) -> Dict[str, Any]:
        """
        Análise imediata do log usando Claude-3 Haiku para classificação rápida
        """
        # Cache key para evitar análises duplicadas
        cache_key = f"{log_event.service_name}:{hash(log_event.message)}"
        
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]
        
        prompt = f"""
        Analise rapidamente este log AWS e classifique:
        
        Serviço: {log_event.service_name}
        Log: {log_event.message}
        Timestamp: {log_event.timestamp}
        
        Responda em JSON:
        {{
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "confidence": 0.0-1.0,
            "category": "network|database|compute|storage|application",
            "needs_detailed_analysis": true/false,
            "summary": "resumo em uma linha"
        }}
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.05
                })
            )
            
            result = json.loads(response['body'].read())
            analysis = json.loads(result['content'][0]['text'])
            
            # Cache por 1 hora
            self._analysis_cache[cache_key] = analysis
            
            # Se precisar de análise detalhada, fazer com Claude-3 Sonnet
            if analysis.get('needs_detailed_analysis'):
                detailed_analysis = await self._detailed_analysis_with_sonnet(log_event)
                analysis['detailed_analysis'] = detailed_analysis
            
            return analysis
            
        except Exception as e:
            logger.error(
                "Erro na análise Bedrock",
                log_event=log_event.message[:100],
                error=str(e)
            )
            return {"error": str(e), "severity": "UNKNOWN"}
    
    async def _detailed_analysis_with_sonnet(self, log_event: LogEvent) -> Dict[str, Any]:
        """
        Análise detalhada usando Claude-3 Sonnet para casos complexos
        """
        # Coletar contexto adicional
        context = await self._gather_context(log_event)
        
        prompt = f"""
        Você é um especialista em infraestrutura AWS. Faça uma análise detalhada:
        
        CONTEXTO:
        - Serviço: {log_event.service_name}
        - Log Group: {log_event.log_group}
        - Timestamp: {log_event.timestamp}
        - Account: {log_event.account_id}
        - Region: {log_event.region}
        
        LOG PARA ANÁLISE:
        {log_event.message}
        
        CONTEXTO ADICIONAL:
        {json.dumps(context, indent=2)}
        
        Forneça análise detalhada em JSON:
        {{
            "root_cause": "causa raiz identificada",
            "affected_services": ["lista", "de", "serviços"],
            "next_steps": ["passos", "específicos", "a", "seguir"],
            "runbook_suggestion": "nome do runbook relevante",
            "estimated_resolution_time": "tempo estimado",
            "business_impact": "LOW|MEDIUM|HIGH|CRITICAL",
            "similar_incidents": ["IDs de incidentes similares se houver"]
        }}
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.1
                })
            )
            
            result = json.loads(response['body'].read())
            return json.loads(result['content'][0]['text'])
            
        except Exception as e:
            logger.error(
                "Erro na análise detalhada Sonnet",
                error=str(e)
            )
            return {"error": str(e)}
    
    async def _gather_context(self, log_event: LogEvent) -> Dict[str, Any]:
        """
        Coleta contexto adicional para análise mais precisa
        """
        context = {}
        
        try:
            # Status dos serviços relacionados
            if log_event.service_name:
                context['service_health'] = await self._get_service_health(log_event.service_name)
            
            # Métricas recentes
            context['recent_metrics'] = await self._get_recent_metrics(log_event.service_name)
            
            # Eventos recentes
            context['recent_events'] = await self._get_recent_events()
            
        except Exception as e:
            logger.warning("Erro ao coletar contexto", error=str(e))
        
        return context
    
    async def _get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Verifica saúde do serviço"""
        # Implementar verificação de health específica por tipo de serviço
        return {"status": "unknown"}
    
    async def _get_recent_metrics(self, service_name: str) -> Dict[str, Any]:
        """Coleta métricas recentes do CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=30)
            
            # Métricas básicas de CPU e Memory se for ECS
            if 'ecs' in service_name.lower():
                response = self.cloudwatch_metrics.get_metric_statistics(
                    Namespace='AWS/ECS',
                    MetricName='CPUUtilization',
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum']
                )
                return {"cpu_metrics": response.get('Datapoints', [])}
                
        except Exception as e:
            logger.warning("Erro ao coletar métricas", error=str(e))
        
        return {}
    
    async def _get_recent_events(self) -> List[Dict[str, Any]]:
        """Coleta eventos recentes que podem estar relacionados"""
        # Implementar coleta de eventos do EventBridge/CloudTrail
        return []
    
    def _extract_service_name(self, log_group: str) -> str:
        """Extrai nome do serviço do log group"""
        # Exemplos: /aws/ecs/my-service -> my-service
        parts = log_group.split('/')
        if len(parts) >= 3:
            return parts[-1]
        return log_group
    
    def _is_error_log(self, message: str) -> bool:
        """Identifica se é um log de erro que precisa de análise"""
        error_indicators = [
            'error', 'exception', 'failed', 'timeout', 'connection refused',
            'out of memory', '500', '502', '503', '504', 'fatal', 'critical'
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in error_indicators)


class MultiAccountCollector:
    """
    Gerenciador de múltiplos coletores AWS
    """
    
    def __init__(self, accounts_config: List[Dict[str, Any]]):
        self.collectors = []
        
        for account_config in accounts_config:
            try:
                collector = AWSCollector(account_config)
                self.collectors.append(collector)
                logger.info(
                    "Coletor AWS inicializado",
                    account_id=account_config["account_id"],
                    name=account_config["name"]
                )
            except Exception as e:
                logger.error(
                    "Erro ao inicializar coletor",
                    account_id=account_config["account_id"],
                    error=str(e)
                )
    
    async def collect_all_accounts(self) -> List[LogEvent]:
        """Coleta logs de todas as contas em paralelo"""
        tasks = []
        
        for collector in self.collectors:
            # Pegar log groups da configuração da conta
            log_groups = self._get_log_groups_for_account(collector.account_id)
            task = collector.collect_real_time_logs(log_groups)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_events = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Erro na coleta", error=str(result))
            else:
                all_events.extend(result)
        
        return all_events
    
    def _get_log_groups_for_account(self, account_id: str) -> List[str]:
        """Retorna log groups configurados para a conta"""
        # Implementar lógica para obter log groups da configuração
        # Por enquanto, retornar alguns padrões comuns
        return [
            "/aws/ecs/my-service",
            "/aws/lambda/my-function",
            "/aws/rds/instance/my-db/error"
        ]


# Exemplo de uso
async def main():
    """Exemplo de execução do coletor"""
    accounts_config = [
        {
            "account_id": "123456789012",
            "name": "microsistec-prod",
            "auth_method": "profile",
            "region": "us-west-2",
            "credentials": {"profile_name": "microsistec-dev"}
        }
    ]
    
    collector = MultiAccountCollector(accounts_config)
    events = await collector.collect_all_accounts()
    
    for event in events:
        if 'ai_analysis' in event.metadata:
            print(f"[{event.timestamp}] {event.service_name}: {event.metadata['ai_analysis']['summary']}")


if __name__ == "__main__":
    asyncio.run(main())

