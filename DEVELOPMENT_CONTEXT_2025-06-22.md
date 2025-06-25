# 📋 SelectNOC IA - Contexto de Desenvolvimento
**Data:** 22/06/2025  
**Sessão:** Correções críticas e melhorias na análise de IA

## 🏗️ Arquitetura Atual

### **Infraestrutura:**
- **Servidor:** Ubuntu Linux na AWS (3.13.129.191)
- **NGINX:** Porta 80 (proxy reverso + arquivos estáticos)
- **Backend Python:** Porta 8000 (FastAPI + uvicorn)
- **Banco:** PostgreSQL RDS (selectnoc-dev-database.cjeqe6pc2viw.us-east-2.rds.amazonaws.com)

### **Estrutura de Arquivos:**
```
/opt/selectnoc/                    # Código fonte (GitHub)
├── simple_main.py                # Backend principal (FastAPI)
├── frontend/
│   ├── pages/
│   │   ├── account-details.html
│   │   └── accounts.html
│   └── index.html
└── account-details-with-ai.html   # Versão com botão IA

/var/www/html/                     # Arquivos servidos pelo NGINX
├── index.html                     # Home page (redireciona)
├── accounts.html                  # Lista de contas
├── account-details.html           # Detalhes + análise IA
└── alert-analysis.html            # Análise específica
```

### **NGINX Configuração:**
```nginx
# /etc/nginx/sites-enabled/selectnoc-clean
server {
    listen 80;
    root /var/www/html;
    
    # Frontend estático
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy para backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

## 🚨 Problemas Resolvidos Nesta Sessão

### **1. Botão de Análise de IA Não Funcionava**
**Problema:** Botão "🧠 Executar Análise Inteligente de IA" não aparecia nos modais

**Causa Raiz:**
- Função displayAlertModal duplicada no HTML
- Primeira versão (sem botão) sobrescrevia a segunda (com botão)
- API_BASE configurado incorretamente (window.location.origin + ':8000')

**Solução:**
- Removida função duplicada
- Configurado API_BASE = window.location.origin (para proxy NGINX)
- Adicionado botão manualmente na função existente
- Criada função analyzeAlert() simplificada

### **2. JavaScript Quebrado**
**Problema:** Erros de sintaxe impedindo execução do JavaScript

**Causa Raiz:**
- F-strings com aspas não escapadas
- Funções indefinidas (startFullDiscovery, refreshResources)
- Conflitos entre versões de arquivos

**Solução:**
- Corrigida sintaxe das f-strings
- Restaurado arquivo base funcional
- Aplicadas correções pontuais sem quebrar funcionalidade

### **3. Análise SSM Conectando no Servidor Errado**
**Problema:** IA analisava servidor SelectNOC em vez da instância Node.js quebrada

**Causa Raiz:**
- Critério de seleção muito amplo: any(keyword in tags for keyword in ['app', 'service', 'web'])
- Qualquer EC2 com essas palavras nas tags era selecionada

**Solução:**
```python
# Critério melhorado
target_registered = instance_id in str(targets_health)
name_match = (tg_name.lower() in str(tags).lower() or 
             "ec2" in tg_name.lower() and any(keyword in str(tags).lower() 
             for keyword in ['ec2', 'unhealthy', 'test']))

if target_registered or name_match:
    # Analisar apenas instâncias relevantes
```

### **4. Home Page Não Redirecionava**
**Problema:** http://3.13.129.191/ não funcionava

**Causa Raiz:**
- index.html redirecionando para /frontend/pages/accounts.html
- NGINX não tinha esse caminho configurado

**Solução:**
- Corrigido redirecionamento para /accounts.html

## 🧠 Funcionalidades de IA Implementadas

### **Análise de Target Groups:**
- Descoberta inteligente de serviços associados (ECS, EC2, Lambda)
- Análise específica por tipo de recurso
- Conectividade SSM para diagnóstico remoto

### **Diagnóstico via SSM:**
```python
diagnostic_commands = [
    {
        'name': 'system_status',
        'command': 'uptime && free -h && df -h'
    },
    {
        'name': 'network_connectivity', 
        'command': f'curl -I http://localhost:{port}/health'
    },
    {
        'name': 'application_processes',
        'command': 'ps aux | grep -E "(node|npm|python|java)" | grep -v grep'
    },
    {
        'name': 'application_ports',
        'command': f'netstat -tlnp | grep :{port}'
    }
]
```

### **Análise com AWS Bedrock:**
- Prompt engineering para diagnóstico contextual
- Integração com dados de CloudWatch Logs
- Recomendações baseadas em padrões identificados

## 🔐 Credenciais e Sessões

**CRÍTICO:** Todas as chamadas AWS usam credenciais da conta cadastrada no banco, NÃO a role da EC2:

```python
# Sempre passar session com credenciais da conta
session = boto3.Session(
    aws_access_key_id=account['access_key'],
    aws_secret_access_key=account['secret_key'],
    region_name=account['region']
)

# Usar session em todos os clientes
ssm = session.client('ssm', region_name=instance_region)
```

## 📁 Endpoints API Principais

### **Alertas:**
- GET /api/v1/accounts/{id}/alerts - Lista alertas da conta
- GET /api/v1/alerts/force-refresh - Force refresh dos alertas
- POST /api/v1/alerts/{id}/analyze - **Análise de IA do alerta**

### **Recursos:**
- GET /api/v1/accounts/{id}/resources - Lista recursos descobertos
- POST /api/v1/discovery/enhanced - Discovery avançado de recursos

### **Páginas:**
- GET /accounts.html - Lista de contas AWS
- GET /account-details.html?id={id} - Detalhes da conta + alertas
- GET /alert-analysis.html - Análise específica de alertas

## 🛠️ Comandos de Manutenção

### **Reiniciar Backend:**
```bash
cd /opt/selectnoc
pkill -f "python3 simple_main.py"
nohup python3 simple_main.py > app.log 2>&1 &
```

### **Verificar Logs:**
```bash
tail -f /opt/selectnoc/app.log
```

### **Atualizar Frontend:**
```bash
# Copiar arquivos corrigidos
sudo cp /opt/selectnoc/account-details.html /var/www/html/
sudo cp /opt/selectnoc/frontend/index.html /var/www/html/
```

### **Deploy de Mudanças:**
```bash
cd /opt/selectnoc
git pull origin main
# Reiniciar backend (comando acima)
# Copiar arquivos frontend (comando acima)
```

## 🔧 Configurações Importantes

### **API_BASE (Frontend):**
```javascript
// ✅ Correto (com NGINX proxy)
const API_BASE = window.location.origin;

// ❌ Incorreto 
const API_BASE = window.location.origin + ':8000';
```

### **Database:**
```python
DB_CONFIG = {
    "host": "selectnoc-dev-database.cjeqe6pc2viw.us-east-2.rds.amazonaws.com",
    "port": 5432,
    "database": "selectnoc", 
    "user": "selectnoc_admin",
    "password": "Dy6uGR1UVasJEp7D"
}
```

## 🎯 Próximos Passos Sugeridos

1. **Monitoramento:** Implementar logs estruturados para análises SSM
2. **Cache:** Adicionar cache Redis para análises de IA pesadas
3. **Alertas:** Sistema de notificações via SNS/SQS
4. **Métricas:** Dashboard de performance das análises
5. **Segurança:** Rotação automática de credenciais AWS

## 📝 Notas de Debugging

### **Sintomas Comuns:**
- **Botões não funcionam:** Verificar console do navegador (F12)
- **"function not defined":** Problema de ordem de carregamento JS
- **Análise na instância errada:** Verificar critério de seleção EC2
- **API 404:** Verificar se backend está rodando na porta 8000

### **Cache do Navegador:**
- Sempre usar Ctrl+F5 para forçar refresh
- Adicionar timestamps no <title> para forçar cache bust
- Meta tags anti-cache já configuradas

## 🔗 Links Importantes

- **GitHub:** https://github.com/kassio20/AWSNoc
- **Aplicação:** http://3.13.129.191/
- **Último Commit:** 4cbf466 (Major improvements: AI analysis button fix + Enhanced SSM diagnostics)

---
**💡 Este arquivo serve como memória contextual para futuras sessões de desenvolvimento. Sempre atualize quando fizer mudanças significativas!**
