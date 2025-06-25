# 🚀 AWSNoc IA - AWS Network Operations Center

## 📋 Descrição

O **AWSNoc IA** é uma solução completa de monitoramento e análise inteligente para infraestrutura AWS, desenvolvida para oferecer visibilidade em tempo real, alertas proativos e análises automatizadas com inteligência artificial.

## ✨ Principais Funcionalidades

### 🔍 **Monitoramento em Tempo Real**
- **Dashboard centralizado** com visão geral de todos os recursos AWS
- **Monitoramento multi-conta** com suporte a múltiplas contas AWS
- **Atualização automática** a cada 30 segundos (otimizado para reduzir custos do CloudWatch)

### 🎯 **Descoberta Automática de Recursos**
- **EC2 Instances** - Status, métricas de CPU/memória, logs
- **ECS Services** - Containers, tasks, métricas de performance
- **RDS Databases** - Performance, conexões, queries
- **Load Balancers (ALB/ELB)** - Health checks, targets
- **Target Groups** - Status de saúde dos alvos
- **S3 Buckets** - Estatísticas de uso
- **Lambda Functions** - Execuções e erros

### 🤖 **Análise Inteligente com IA**
- **Amazon Bedrock (Claude-3)** para análise automatizada de problemas
- **Análise de logs em tempo real** com identificação de padrões
- **Recomendações automatizadas** para resolução de problemas
- **Correlação inteligente** entre eventos e recursos

### 📊 **Sistema de Alertas Avançado**
- **Alertas proativos** baseados em métricas do CloudWatch
- **Classificação automática** por severidade (Critical, High, Medium, Low)
- **Análise de causa raiz** automatizada com IA
- **Histórico completo** de alertas e resoluções

### 💰 **Otimização de Custos**
- **Cache inteligente** para reduzir chamadas ao CloudWatch
- **Polling otimizado** com intervalos configuráveis
- **Métricas sob demanda** para reduzir custos desnecessários

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │   AWS Services  │
│   (HTML/JS)     │◄──►│   (FastAPI)      │◄──►│   (boto3)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   SQLite DB      │
                       │  (Alertas/Cache) │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Amazon Bedrock  │
                       │   (Claude-3)     │
                       └──────────────────┘
```

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.11+**
- **FastAPI** - Framework web assíncrono
- **SQLite** - Banco de dados local
- **boto3** - SDK oficial da AWS
- **uvicorn** - Servidor ASGI

### Frontend
- **HTML5/CSS3/JavaScript** - Interface responsiva
- **Chart.js** - Gráficos e visualizações
- **Bootstrap** - Framework CSS

### Inteligência Artificial
- **Amazon Bedrock** - Serviço de IA da AWS
- **Claude-3 (Anthropic)** - Modelo de linguagem para análises

### Infraestrutura
- **AWS EC2** - Hospedagem da aplicação
- **AWS CloudWatch** - Métricas e logs
- **nginx** - Servidor web proxy

## 📦 Instalação e Configuração

### Pré-requisitos
- Python 3.11 ou superior
- Conta AWS com permissões adequadas
- Acesso ao Amazon Bedrock (Claude-3)

### 1. Clone o repositório
```bash
git clone https://github.com/kassio20/AWSNoc.git
cd AWSNoc
```

### 2. Instale as dependências
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Configure as credenciais AWS
```bash
# Configure suas credenciais AWS
aws configure

# Ou use variáveis de ambiente
export AWS_ACCESS_KEY_ID="sua_access_key"
export AWS_SECRET_ACCESS_KEY="sua_secret_key"
export AWS_DEFAULT_REGION="us-east-2"
```

### 4. Configure o banco de dados
```bash
python database_manager.py
```

### 5. Execute a aplicação
```bash
python simple_main.py
```

A aplicação estará disponível em: `http://localhost:8000`

## 📱 Como Usar

### 1. **Adicionar Conta AWS**
- Acesse o dashboard principal
- Clique em "Adicionar Conta"
- Insira as credenciais AWS e região

### 2. **Visualizar Recursos**
- Selecione uma conta no dashboard
- Navegue pelas diferentes categorias de recursos
- Visualize métricas em tempo real

### 3. **Monitorar Alertas**
- Acesse a seção "Alertas Ativos"
- Visualize alertas organizados por severidade
- Clique em um alerta para análise detalhada com IA

### 4. **Análise com IA**
- Clique em "Analisar com IA" em qualquer alerta
- Aguarde a análise automatizada do Claude-3
- Visualize causa raiz e recomendações

## 📊 Principais Métricas Monitoradas

### EC2 Instances
- ✅ CPU Utilization
- ✅ Memory Usage
- ✅ Disk I/O
- ✅ Network Traffic
- ✅ Status Checks

### ECS Services
- ✅ Task Status (Running/Stopped/Pending)
- ✅ CPU/Memory Utilization
- ✅ Service Health
- ✅ Container Logs

### RDS Databases
- ✅ CPU Utilization
- ✅ Database Connections
- ✅ Query Performance
- ✅ Storage Usage

### Load Balancers
- ✅ Target Health
- ✅ Request Count
- ✅ Response Time
- ✅ Error Rates

## 🔧 Configurações Avançadas

### Otimização de Custos CloudWatch
```python
# config/cloudwatch_config.py
POLLING_INTERVALS = {
    'dashboard': 30,      # segundos
    'metrics': 60,        # segundos  
    'logs': 300,          # segundos
}

CACHE_TTL = {
    'resources': 60,      # segundos
    'metrics': 30,        # segundos
}
```

### Configuração de Alertas
```python
# Severidades configuráveis
ALERT_THRESHOLDS = {
    'cpu_critical': 90,    # %
    'cpu_high': 75,        # %
    'memory_critical': 90, # %
    'disk_critical': 85,   # %
}
```

## 🚀 Deploy em Produção

### 1. **Deploy em EC2**
- Consulte o arquivo `DEPLOYMENT.md` para instruções detalhadas
- Configure nginx como proxy reverso
- Configure SSL/TLS com certificados

### 2. **Configuração do Serviço**
```bash
# Criar serviço systemd
sudo nano /etc/systemd/system/awsnoc-ia.service

[Unit]
Description=AWSNoc IA IA Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/awsnoc-ia
ExecStart=/opt/awsnoc-ia/venv/bin/python simple_main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📈 Otimizações Implementadas

### ✅ **Redução de Custos CloudWatch**
- Cache inteligente com TTL configurável
- Polling otimizado para 30 segundos
- Métricas sob demanda

### ✅ **Performance**
- Conexões assíncronas com AWS
- Cache de recursos em memória
- Lazy loading de métricas

### ✅ **Segurança**
- Validação de credenciais AWS
- Sanitização de inputs
- Logs de auditoria

## 🔍 Monitoramento e Logs

### Logs da Aplicação
```bash
# Visualizar logs do serviço
sudo journalctl -u awsnoc-ia -f

# Logs do nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Métricas de Performance
- Tempo de resposta das APIs
- Uso de memória da aplicação
- Latência das consultas ao CloudWatch

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Documentação Adicional

- 📘 [Guia de Otimização CloudWatch](CLOUDWATCH_OPTIMIZATION_GUIDE.md)
- 🚀 [Guia de Deploy](DEPLOYMENT.md)
- ⚡ [Resumo de Otimizações](OPTIMIZATION_SUMMARY.md)

## 📞 Suporte

Para suporte técnico ou dúvidas:
- 📧 Email: [seu-email@exemplo.com]
- 🐛 Issues: [GitHub Issues](https://github.com/kassio20/AWSNoc/issues)

## 📝 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

**Desenvolvido com ❤️ para monitoramento inteligente de infraestrutura AWS**

### 🎯 Status do Projeto

- ✅ **Produção** - Estável e otimizado
- ✅ **Dados Reais** - 100% integrado com AWS real
- ✅ **IA Funcional** - Amazon Bedrock Claude-3 ativo
- ✅ **Custos Otimizados** - CloudWatch com cache inteligente
- ✅ **Interface Completa** - Dashboard responsivo e intuitivo

**Última atualização:** Dezembro 2024

## 🎨 Estrutura do Frontend

O frontend está localizado no diretório `frontend/` e inclui:

### 📁 **Estrutura de Arquivos**
```
frontend/
├── index.html              # Página de entrada
├── pages/                  # Páginas da aplicação
│   ├── accounts.html       # Dashboard principal
│   ├── account-details.html # Detalhes de recursos
│   ├── alert-analysis.html # Análise com IA
│   ├── ecs-details.html    # Monitoramento ECS
│   ├── ec2-details.html    # Monitoramento EC2
│   ├── rds-details.html    # Monitoramento RDS
│   └── ...                 # Outras páginas
├── assets/                 # Recursos estáticos
│   └── logo/              # Logos e imagens
└── README.md              # Documentação frontend
```

### 🌐 **Deploy do Frontend**
```bash
# Copiar arquivos para servidor web
sudo cp -r frontend/* /var/www/html/

# Reiniciar nginx
sudo nginx -s reload
```

Para documentação completa do frontend, consulte: [Frontend README](frontend/README.md)

