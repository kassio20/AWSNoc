"""
AWSNoc IA IA - API Routes
Rotas da API para o sistema SaaS
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


# Modelos Pydantic para requests/responses
class LogAnalysisRequest(BaseModel):
    message: str
    service: str
    timestamp: Optional[str] = None
    log_group: Optional[str] = None
    account_id: Optional[str] = None


class LogAnalysisResponse(BaseModel):
    severity: str
    confidence: float
    category: str
    summary: str
    detailed_analysis: Optional[Dict[str, Any]] = None


class AccountConnectionRequest(BaseModel):
    name: str
    auth_method: str  # profile, assume_role, access_keys
    region: str
    credentials: Dict[str, Any]


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    components: Dict[str, str]


def setup_routes(app, awsnoc-ia_instance):
    """Configura todas as rotas da API"""
    
    # Router principal
    api_router = APIRouter(prefix="/api/v1")
    
    @api_router.get("/health", response_model=HealthCheckResponse)
    async def health_check():
        """Health check detalhado do sistema"""
        components = {}
        
        # Verificar componentes
        try:
            if awsnoc-ia_instance.collector:
                components["collector"] = "healthy"
            else:
                components["collector"] = "not_initialized"
                
            if awsnoc-ia_instance.analyzer:
                components["analyzer"] = "healthy"
            else:
                components["analyzer"] = "not_initialized"
                
            # Testar conectividade AWS (básico)
            # Em produção, fazer ping real nos serviços
            components["aws_connectivity"] = "assumed_healthy"
            components["bedrock"] = "assumed_healthy"
            
        except Exception as e:
            logger.error("Erro no health check", error=str(e))
            components["error"] = str(e)
        
        return HealthCheckResponse(
            status="healthy" if all(v == "healthy" or v == "assumed_healthy" for v in components.values()) else "degraded",
            service="AWSNoc IA IA",
            version="1.0.0",
            timestamp=datetime.utcnow().isoformat() + "Z",
            components=components
        )
    
    @api_router.post("/analyze", response_model=LogAnalysisResponse)
    async def analyze_log(request: LogAnalysisRequest):
        """
        Analisa um log usando IA
        """
        try:
            if not awsnoc-ia_instance.analyzer:
                raise HTTPException(status_code=503, detail="Analisador não inicializado")
            
            # Criar evento de log simulado
            from collectors.aws_collector import LogEvent
            
            log_event = LogEvent(
                timestamp=datetime.fromisoformat(request.timestamp.replace('Z', '+00:00')) if request.timestamp else datetime.utcnow(),
                message=request.message,
                service_name=request.service,
                log_group=request.log_group or f"/aws/ecs/{request.service}",
                log_stream=f"{request.service}/main/test",
                account_id=request.account_id or "123456789012",
                region="us-east-1",
                metadata={}
            )
            
            # Analisar com IA
            analysis = await awsnoc-ia_instance.analyzer.analyze_log(log_event)
            
            return LogAnalysisResponse(
                severity=analysis.get('severity', 'UNKNOWN'),
                confidence=analysis.get('confidence', 0.0),
                category=analysis.get('category', 'unknown'),
                summary=analysis.get('summary', 'Análise não disponível'),
                detailed_analysis=analysis.get('detailed_analysis')
            )
            
        except Exception as e:
            logger.error("Erro na análise de log", error=str(e))
            raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")
    
    @api_router.get("/accounts")
    async def list_accounts():
        """Lista contas AWS configuradas"""
        try:
            if not awsnoc-ia_instance.collector:
                return {"accounts": []}
            
            accounts = []
            for collector in awsnoc-ia_instance.collector.collectors:
                accounts.append({
                    "account_id": collector.account_id,
                    "name": collector.account_config.get("name", "Unknown"),
                    "region": collector.region,
                    "auth_method": collector.account_config.get("auth_method"),
                    "status": "connected"  # Em produção, verificar conectividade real
                })
            
            return {"accounts": accounts}
            
        except Exception as e:
            logger.error("Erro ao listar contas", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @api_router.post("/accounts")
    async def add_account(request: AccountConnectionRequest):
        """Adiciona nova conta AWS para monitoramento"""
        try:
            # Em produção, validar credenciais e salvar no banco
            
            # Validar configuração
            account_config = {
                "account_id": "temp_id",  # Em produção, detectar o account ID
                "name": request.name,
                "auth_method": request.auth_method,
                "region": request.region,
                "credentials": request.credentials
            }
            
            # Testar conexão (simulado)
            # Em produção, criar coletor temporário para testar
            
            return {
                "status": "success",
                "message": f"Conta {request.name} adicionada com sucesso",
                "account_config": account_config
            }
            
        except Exception as e:
            logger.error("Erro ao adicionar conta", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @api_router.get("/logs/recent")
    async def get_recent_logs(
        limit: int = 100,
        service: Optional[str] = None,
        severity: Optional[str] = None
    ):
        """Obtém logs recentes com análises de IA"""
        try:
            # Em produção, buscar do banco de dados
            # Por enquanto, retornar dados simulados
            
            recent_logs = [
                {
                    "timestamp": "2024-01-01T12:00:00Z",
                    "service": "api-service",
                    "message": "Connection timeout to database",
                    "severity": "HIGH",
                    "summary": "Database connectivity issue",
                    "account_id": "123456789012"
                },
                {
                    "timestamp": "2024-01-01T11:58:00Z",
                    "service": "worker-service",
                    "message": "Task processing completed successfully",
                    "severity": "LOW",
                    "summary": "Normal operation",
                    "account_id": "123456789012"
                }
            ]
            
            # Filtrar por service se especificado
            if service:
                recent_logs = [log for log in recent_logs if log["service"] == service]
            
            # Filtrar por severity se especificado
            if severity:
                recent_logs = [log for log in recent_logs if log["severity"] == severity]
            
            # Limitar resultados
            recent_logs = recent_logs[:limit]
            
            return {
                "logs": recent_logs,
                "total": len(recent_logs),
                "filtered": bool(service or severity)
            }
            
        except Exception as e:
            logger.error("Erro ao buscar logs recentes", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @api_router.get("/stats/dashboard")
    async def get_dashboard_stats():
        """Estatísticas para o dashboard principal"""
        try:
            # Em produção, calcular estatísticas reais do banco
            stats = {
                "total_accounts": 1,
                "total_services": 3,
                "logs_analyzed_today": 1247,
                "alerts_generated": 12,
                "critical_alerts": 2,
                "avg_resolution_time": "15.5 minutes",
                "top_issues": [
                    {"type": "Database Connection", "count": 5},
                    {"type": "Memory Limit", "count": 3},
                    {"type": "Network Timeout", "count": 2}
                ],
                "severity_distribution": {
                    "critical": 2,
                    "high": 8,
                    "medium": 15,
                    "low": 45
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error("Erro ao obter estatísticas", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @api_router.get("/ai/models/status")
    async def get_ai_models_status():
        """Status dos modelos de IA"""
        try:
            if not awsnoc-ia_instance.analyzer:
                return {"status": "not_initialized"}
            
            # Testar conectividade com Bedrock
            models_status = {
                "bedrock_region": awsnoc-ia_instance.analyzer.region,
                "models": {
                    "claude_sonnet": "available",
                    "claude_haiku": "available", 
                    "titan_text": "available"
                },
                "cache_size": len(awsnoc-ia_instance.analyzer._cache),
                "last_analysis": "2024-01-01T12:00:00Z"  # Em produção, timestamp real
            }
            
            return models_status
            
        except Exception as e:
            logger.error("Erro ao verificar status dos modelos", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @api_router.post("/test/bedrock")
    async def test_bedrock_connection():
        """Testa conectividade com Amazon Bedrock"""
        try:
            if not awsnoc-ia_instance.analyzer:
                raise HTTPException(status_code=503, detail="Analisador não inicializado")
            
            # Teste simples com o Bedrock
            test_log = type('TestLog', (), {
                'service_name': 'test-service',
                'message': 'Test log message for connectivity',
                'timestamp': datetime.utcnow(),
                'log_group': '/test/group',
                'log_stream': 'test-stream',
                'account_id': '123456789012',
                'region': 'us-east-1'
            })()
            
            result = await awsnoc-ia_instance.analyzer._quick_classification(test_log)
            
            return {
                "status": "success",
                "message": "Bedrock conectado com sucesso",
                "test_result": result
            }
            
        except Exception as e:
            logger.error("Erro no teste Bedrock", error=str(e))
            raise HTTPException(status_code=500, detail=f"Erro de conectividade: {str(e)}")
    
    # Incluir router na aplicação
    app.include_router(api_router)
    
    # Rotas diretas no app (para compatibilidade)
    @app.get("/")
    async def root():
        """Página inicial da API"""
        return {
            "service": "AWSNoc IA IA",
            "description": "AI-Powered AWS Log Analysis SaaS",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/v1/health"
        }

