# SelectNOC IA - Sistema SaaS de Análise Inteligente de Logs AWS

## 🎯 Visão Geral

SelectNOC IA é um **SaaS completo** para análise inteligente de logs AWS usando **Amazon Bedrock** e **Claude-3**. O sistema monitora múltiplas contas AWS, analisa logs em tempo real e fornece insights acionáveis através de IA nativa da AWS.

### 🚀 Principais Diferenciais

- **100% AWS Native**: Usa apenas CloudWatch como fonte, sem agentes adicionais
- **60-80% mais barato** que Datadog, New Relic, Splunk
- **IA Avançada**: Amazon Bedrock com Claude-3 Sonnet/Haiku
- **Multi-Tenant**: Suporte a múltiplas contas AWS
- **Análise em Tempo Real**: Classificação automática e sugestões de correção

## Stack de IA Especializada em AWS

### Modelos Principais
- **Amazon Bedrock**: Claude-3 Sonnet/Haiku para análise de logs AWS
- **Amazon CodeWhisperer**: Análise de código e sugestões de fix
- **Amazon Comprehend**: NLP para classificação de logs e eventos
- **SageMaker Endpoints**: Modelos customizados para detecção de anomalias
- **AWS X-Ray**: Tracing inteligente para correlação de serviços

### Modelos Especializados Terceiros
- **LangChain AWS Tools**: Integração nativa com serviços AWS
- **Anthropic Claude-3**: Especializado em análise técnica e troubleshooting
- **OpenAI GPT-4 Turbo**: Fine-tuned com dados de AWS CloudTrail
- **Hugging Face Transformers**: Modelos pré-treinados em logs de infraestrutura

## Funcionalidades Core

### 1. Análise Inteligente de Logs
- Classificação automática por severidade usando Amazon Comprehend
- Detecção de padrões anômalos com SageMaker
- Correlação temporal de eventos usando Bedrock

### 2. Monitoramento AWS Nativo
- **ECS Services**: Health checks, deployment failures, resource constraints
- **Target Groups**: Health status, latency patterns, error rates
- **RDS Metrics**: Performance insights, connection issues, query analysis
- **CloudWatch Logs**: Real-time streaming e análise contextual

### 3. IA Preditiva e Sugestões
- Predição de falhas baseada em padrões históricos
- Sugestões automáticas de runbooks usando CodeWhisperer
- Correlação entre deploys e incidentes via X-Ray

## Arquitetura Técnica

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AWS Bedrock   │    │   SageMaker      │    │  Amazon         │
│   (Claude-3)    │◄──►│   Endpoints      │◄──►│  Comprehend     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                       ▲
         │                        │                       │
┌─────────────────────────────────────────────────────────────────┐
│                    SelectNOC IA Core Engine                     │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│  AWS Collectors │   AI Processors │   Correlators   │ Alerting  │
│                 │                 │                 │           │
│ • ECS Services  │ • Log Analysis  │ • Event Fusion  │ • Smart   │
│ • Target Groups │ • Anomaly Det.  │ • Code Changes  │   Alerts  │
│ • RDS Metrics   │ • Severity Cls. │ • Time Windows  │ • Runbooks│
│ • CloudWatch    │ • Root Cause    │ • Service Maps  │ • Tickets │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

## Stack Tecnológica AWS-First

### Backend
- **Python 3.11+** com AWS SDK (Boto3)
- **LangChain AWS Integration** para orquestração de IA
- **FastAPI** para APIs REST
- **Celery + Redis** para processamento assíncrono

### IA/ML
- **Amazon Bedrock** - Modelos foundation (Claude-3, Jurassic-2)
- **SageMaker** - Modelos customizados de anomalia
- **Amazon Comprehend** - NLP para logs
- **AWS CodeWhisperer** - Análise de código
- **LangChain** - Orquestração de múltiplos modelos

### AWS Services
- **CloudWatch** - Logs, Metrics, Alarms
- **X-Ray** - Distributed tracing
- **ECS** - Container monitoring
- **RDS Performance Insights** - Database metrics
- **EventBridge** - Event correlation
- **Lambda** - Serverless processors

### Storage & Cache
- **Amazon RDS PostgreSQL** - Dados estruturados
- **Amazon ElastiCache (Redis)** - Cache e filas
- **Amazon S3** - Log archives e model artifacts
- **Amazon DynamoDB** - Métricas em tempo real

## Modelos de IA Configurados

### 1. Classificação de Severidade
```python
# Amazon Comprehend + Custom SageMaker
severity_model = {
    "critical": "Service down, data loss risk",
    "high": "Performance degradation, user impact",
    "medium": "Resource warnings, potential issues",
    "low": "Informational, monitoring alerts"
}
```

### 2. Root Cause Analysis
```python
# Bedrock Claude-3 com contexto AWS
root_cause_prompt = """
Analise os logs do serviço AWS ECS:
- Target Group: {tg_name}
- Health Status: {health_status}
- Logs: {log_entries}
- Métricas RDS: {rds_metrics}

Identifique a causa raiz e sugira próximos passos.
"""
```

### 3. Correlação de Eventos
```python
# LangChain + X-Ray + CloudWatch
correlation_pipeline = [
    "code_changes_detector",    # Git commits vs incidents
    "deployment_correlator",    # ECS deployments vs errors
    "database_impact_analyzer", # RDS metrics vs app errors
    "network_dependency_mapper" # Target Group health propagation
]
```

## Instalação e Setup

```bash
# Clone e setup
git clone <repo-url> SelectNocIA
cd SelectNocIA

# Ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Dependências
pip install -r requirements.txt

# Configuração AWS
aws configure
# Configure Bedrock model access
# Setup SageMaker endpoints
```

## Configuração de IA

1. **Bedrock Models**: Configure acesso aos modelos Claude-3
2. **SageMaker**: Deploy modelos de anomalia customizados
3. **Comprehend**: Setup classificadores de texto
4. **API Keys**: Configure OpenAI/Anthropic como backup

## Próximos Passos

1. 🔧 Setup da estrutura base do projeto
2. 🤖 Integração com Amazon Bedrock
3. 📊 Coletores AWS (ECS, RDS, CloudWatch)
4. 🧠 Engine de correlação inteligente
5. 📱 Dashboard para visualização
6. 🚨 Sistema de alertas proativos

Pronto para começar a implementação!

