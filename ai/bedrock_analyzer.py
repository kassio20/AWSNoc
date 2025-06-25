"""
AWSNoc IA IA - Bedrock Analyzer
Analisador de logs usando Amazon Bedrock com Claude-3
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
import structlog

logger = structlog.get_logger(__name__)


class BedrockAnalyzer:
    """
    Analisador de logs usando Amazon Bedrock
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        
        # Cache para análises
        self._cache = {}
        
        # Modelos disponíveis
        self.models = {
            "claude_sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude_haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "titan_text": "amazon.titan-text-premier-v1:0"
        }
        
    async def analyze_log(self, log_event) -> Dict[str, Any]:
        """
        Análise principal de um evento de log
        """
        # Cache key
        cache_key = f"{log_event.service_name}:{hash(log_event.message)}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Análise rápida primeiro
            quick_analysis = await self._quick_classification(log_event)
            
            # Se for crítico ou alto, fazer análise detalhada
            if quick_analysis.get('severity') in ['CRITICAL', 'HIGH']:
                detailed_analysis = await self._detailed_analysis(log_event)
                quick_analysis['detailed_analysis'] = detailed_analysis
            
            # Cache resultado
            self._cache[cache_key] = quick_analysis
            
            return quick_analysis
            
        except Exception as e:
            logger.error("Erro na análise", error=str(e))
            return {"error": str(e), "severity": "UNKNOWN"}
    
    async def _quick_classification(self, log_event) -> Dict[str, Any]:
        """
        Classificação rápida usando Claude-3 Haiku
        """
        prompt = f"""
        Analise rapidamente este log AWS e classifique:
        
        Serviço: {log_event.service_name}
        Log: {log_event.message}
        Timestamp: {log_event.timestamp}
        
        Responda apenas em JSON válido:
        {{
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "confidence": 0.95,
            "category": "network|database|compute|storage|application",
            "needs_detailed_analysis": true,
            "summary": "resumo em uma linha"
        }}
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.models["claude_haiku"],
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.05
                })
            )
            
            result = json.loads(response['body'].read())
            analysis_text = result['content'][0]['text']
            
            # Extrair JSON da resposta
            if '```json' in analysis_text:
                json_start = analysis_text.find('```json') + 7
                json_end = analysis_text.find('```', json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            
            return json.loads(analysis_text)
            
        except Exception as e:
            logger.error("Erro na classificação rápida", error=str(e))
            return {
                "severity": "MEDIUM",
                "confidence": 0.5,
                "category": "unknown",
                "needs_detailed_analysis": False,
                "summary": "Erro na análise automática",
                "error": str(e)
            }
    
    async def _detailed_analysis(self, log_event) -> Dict[str, Any]:
        """
        Análise detalhada usando Claude-3 Sonnet
        """
        prompt = f"""
        Você é um especialista em infraestrutura AWS com 15+ anos de experiência.
        Analise detalhadamente este log crítico:
        
        CONTEXTO:
        - Serviço: {log_event.service_name}
        - Log Group: {log_event.log_group}
        - Stream: {log_event.log_stream}
        - Timestamp: {log_event.timestamp}
        - Account: {log_event.account_id}
        - Region: {log_event.region}
        
        LOG PARA ANÁLISE:
        {log_event.message}
        
        Forneça análise detalhada em JSON válido:
        {{
            "root_cause": "Identificação precisa da causa raiz",
            "affected_services": ["ECS", "RDS", "ALB"],
            "next_steps": [
                "Verificar conexões RDS",
                "Analisar logs do ALB",
                "Verificar target group health"
            ],
            "runbook_suggestion": "database-connection-issues",
            "estimated_resolution_time": "15-30 minutes",
            "business_impact": "HIGH",
            "prevention_measures": [
                "Implementar connection pooling",
                "Configurar auto-scaling RDS"
            ],
            "monitoring_recommendations": [
                "Alertas para connection count",
                "Dashboard de performance RDS"
            ]
        }}
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.models["claude_sonnet"],
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.1
                })
            )
            
            result = json.loads(response['body'].read())
            analysis_text = result['content'][0]['text']
            
            # Extrair JSON da resposta
            if '```json' in analysis_text:
                json_start = analysis_text.find('```json') + 7
                json_end = analysis_text.find('```', json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            
            return json.loads(analysis_text)
            
        except Exception as e:
            logger.error("Erro na análise detalhada", error=str(e))
            return {
                "root_cause": "Erro na análise detalhada",
                "error": str(e)
            }


# Exemplo de uso
if __name__ == "__main__":
    import asyncio
    from collections import namedtuple
    
    # Simular um evento de log
    LogEvent = namedtuple('LogEvent', [
        'timestamp', 'message', 'service_name', 'log_group', 
        'log_stream', 'account_id', 'region'
    ])
    
    log_event = LogEvent(
        timestamp=datetime.now(),
        message="ERROR: Database connection pool exhausted - Connection timeout after 30000ms",
        service_name="api-service",
        log_group="/aws/ecs/api-service",
        log_stream="api-service/main/abcd1234",
        account_id="123456789012",
        region="us-west-2"
    )
    
    async def test_analysis():
        analyzer = BedrockAnalyzer()
        result = await analyzer.analyze_log(log_event)
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(test_analysis())

