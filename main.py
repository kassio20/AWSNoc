#!/usr/bin/env python3
"""
SelectNOC IA - Sistema Principal
Sistema SaaS de análise inteligente de logs AWS usando Bedrock e Claude-3
"""

import asyncio
import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog
import yaml

from collectors.aws_collector import MultiAccountCollector
from ai.bedrock_analyzer import BedrockAnalyzer
from api.routes import setup_routes

# Configurar logging estruturado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class SelectNOCIA:
    """
    Classe principal do sistema SelectNOC IA
    """
    
    def __init__(self, config_path: str = "config/aws_ai_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.app = FastAPI(
            title="SelectNOC IA",
            description="AI-Powered AWS Log Analysis SaaS",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configurar adequadamente em produção
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Inicializar componentes
        self.collector = None
        self.analyzer = None
        
        # Configurar rotas
        setup_routes(self.app, self)
        
    def _load_config(self) -> dict:
        """Carrega configuração do arquivo YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("Configuração carregada", config_file=self.config_path)
            return config
        except FileNotFoundError:
            logger.error("Arquivo de configuração não encontrado", path=self.config_path)
            return {}
        except yaml.YAMLError as e:
            logger.error("Erro ao carregar configuração YAML", error=str(e))
            return {}
    
    async def initialize(self):
        """Inicializa todos os componentes do sistema"""
        try:
            logger.info("Inicializando SelectNOC IA...")
            
            # Configurar exemplo de contas AWS (em produção virá do banco)
            accounts_config = [
                {
                    "account_id": "123456789012",
                    "name": "microsistec-dev",
                    "auth_method": "profile",
                    "region": "us-west-2",
                    "credentials": {"profile_name": "microsistec-dev"},
                    "bedrock_region": "us-east-1"
                }
            ]
            
            # Inicializar coletor multi-conta
            self.collector = MultiAccountCollector(accounts_config)
            
            # Inicializar analisador Bedrock
            self.analyzer = BedrockAnalyzer(
                region=self.config.get("aws_ai_stack", {}).get("bedrock", {}).get("region_primary", "us-east-1")
            )
            
            logger.info("SelectNOC IA inicializado com sucesso")
            
        except Exception as e:
            logger.error("Erro na inicialização", error=str(e))
            raise
    
    async def start_monitoring(self):
        """Inicia o loop principal de monitoramento"""
        logger.info("Iniciando monitoramento em tempo real...")
        
        while True:
            try:
                # Coletar logs de todas as contas
                events = await self.collector.collect_all_accounts()
                
                # Processar eventos com IA se necessário
                for event in events:
                    if 'ai_analysis' in event.metadata:
                        analysis = event.metadata['ai_analysis']
                        
                        # Log do resultado da análise
                        logger.info(
                            "Log analisado pela IA",
                            service=event.service_name,
                            severity=analysis.get('severity', 'UNKNOWN'),
                            summary=analysis.get('summary', ''),
                            account=event.account_id
                        )
                        
                        # Se for crítico, pode disparar alertas imediatos
                        if analysis.get('severity') == 'CRITICAL':
                            await self._handle_critical_alert(event, analysis)
                
                # Aguardar antes da próxima coleta
                await asyncio.sleep(30)  # 30 segundos
                
            except Exception as e:
                logger.error("Erro no loop de monitoramento", error=str(e))
                await asyncio.sleep(60)  # Esperar mais tempo em caso de erro
    
    async def _handle_critical_alert(self, event, analysis):
        """Trata alertas críticos"""
        logger.critical(
            "ALERTA CRÍTICO DETECTADO",
            service=event.service_name,
            account=event.account_id,
            root_cause=analysis.get('detailed_analysis', {}).get('root_cause', 'Unknown'),
            next_steps=analysis.get('detailed_analysis', {}).get('next_steps', [])
        )
        
        # Aqui integraria com sistemas de alertas (Slack, PagerDuty, etc.)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Executa o servidor principal"""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )


# Instância global
selectnoc = SelectNOCIA()
app = selectnoc.app


# Eventos do FastAPI
@app.on_event("startup")
async def startup_event():
    """Executado na inicialização do servidor"""
    await selectnoc.initialize()
    
    # Iniciar monitoramento em background
    asyncio.create_task(selectnoc.start_monitoring())


@app.on_event("shutdown")
async def shutdown_event():
    """Executado no shutdown do servidor"""
    logger.info("Encerrando SelectNOC IA...")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "service": "SelectNOC IA",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }


# Endpoint para testar análise de IA
@app.post("/analyze")
async def analyze_log(log_data: dict):
    """
    Endpoint para testar análise de log
    
    Exemplo de payload:
    {
        "message": "ERROR: Database connection failed",
        "service": "my-api",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        if not selectnoc.analyzer:
            raise HTTPException(status_code=503, detail="Analisador não inicializado")
        
        # Simular um evento de log
        from collectors.aws_collector import LogEvent
        from datetime import datetime
        
        log_event = LogEvent(
            timestamp=datetime.fromisoformat(log_data.get("timestamp", "2024-01-01T12:00:00")),
            message=log_data["message"],
            service_name=log_data.get("service", "unknown"),
            log_group="/test/log-group",
            log_stream="test-stream",
            account_id="123456789012",
            region="us-east-1",
            metadata={}
        )
        
        # Analisar com IA
        analysis = await selectnoc.analyzer.analyze_log(log_event)
        
        return {
            "input": log_data,
            "analysis": analysis,
            "status": "success"
        }
        
    except Exception as e:
        logger.error("Erro na análise", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SelectNOC IA - Sistema de Análise Inteligente de Logs AWS")
    parser.add_argument("--host", default="0.0.0.0", help="Host para o servidor")
    parser.add_argument("--port", type=int, default=8000, help="Porta para o servidor")
    parser.add_argument("--config", default="config/aws_ai_config.yaml", help="Arquivo de configuração")
    
    args = parser.parse_args()
    
    # Atualizar caminho da configuração
    global selectnoc
    selectnoc = SelectNOCIA(config_path=args.config)
    
    # Executar servidor
    logger.info(
        "Iniciando SelectNOC IA",
        host=args.host,
        port=args.port,
        config=args.config
    )
    
    selectnoc.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

