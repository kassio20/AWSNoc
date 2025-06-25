# 🎨 Frontend SelectNOC

## 📁 Estrutura do Frontend

```
frontend/
├── index.html              # Página principal de login/entrada
├── pages/                  # Páginas da aplicação
│   ├── accounts.html       # Dashboard principal com contas AWS
│   ├── account-details.html # Detalhes de recursos por conta
│   ├── alert-analysis.html # Análise de alertas com IA
│   ├── ecs-details.html    # Monitoramento ECS Services
│   ├── ec2-details.html    # Monitoramento EC2 Instances
│   ├── rds-details.html    # Monitoramento RDS Databases
│   ├── loadbalancer-details.html # Monitoramento Load Balancers
│   ├── elasticache-details.html  # Monitoramento ElastiCache
│   └── ecs-service-logs.html     # Logs de serviços ECS
├── assets/                 # Recursos estáticos
│   └── logo/              # Logos e imagens
└── src/                   # Código fonte frontend
```

## 🚀 Funcionalidades

### 🏠 **Dashboard Principal** (`accounts.html`)
- Visualização de todas as contas AWS configuradas
- Estatísticas em tempo real de recursos
- Navegação rápida entre serviços
- Interface responsiva e moderna

### 📊 **Detalhes da Conta** (`account-details.html`)
- Visão consolidada de todos os recursos AWS
- Métricas em tempo real (CPU, memória, rede)
- Navegação por categorias de serviços
- Cards interativos com informações detalhadas

### 🔍 **Análise de Alertas** (`alert-analysis.html`)
- Interface para análise automatizada com IA
- Integração com Amazon Bedrock (Claude-3)
- Exibição de causa raiz e recomendações
- Histórico de análises

### 🐳 **Monitoramento ECS** (`ecs-details.html`)
- Monitoramento de serviços e containers ECS
- Métricas de CPU e memória em tempo real
- Status de tasks (Running/Stopped/Pending)
- Visualização de clusters e task definitions

### 💻 **Monitoramento EC2** (`ec2-details.html`)
- Status de instâncias EC2
- Métricas de performance
- Health checks e status de rede
- Informações de configuração

### 🗄️ **Monitoramento RDS** (`rds-details.html`)
- Performance de bancos de dados
- Métricas de conexões e queries
- Status de backup e maintenance
- Monitoramento de storage

## 🎨 Design System

### Cores Principais
```css
--primary-blue: #58a6ff
--dark-bg: #0d1117
--card-bg: rgba(45, 51, 59, 0.5)
--border-color: #30363d
--text-primary: #f0f6fc
--text-secondary: #7d8590
```

### Componentes
- **Cards responsivos** com hover effects
- **Badges de status** com cores semânticas
- **Grids adaptáveis** para diferentes tamanhos de tela
- **Modais informativos** para detalhes
- **Charts interativos** para métricas

## 📱 Responsividade

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px

### Grid System
- **Auto-fit columns** com tamanho mínimo de 280px
- **Flex layouts** para componentes
- **CSS Grid** para layouts principais

## 🔧 Configuração

### Deploy
1. Copie os arquivos para `/var/www/html/`
2. Configure nginx como proxy reverso
3. Certifique-se que o backend está rodando na porta 8000

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ @backend;
    }
    
    location @backend {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🛠️ Tecnologias Utilizadas

- **HTML5** - Estrutura semântica
- **CSS3** - Estilos modernos com grid/flexbox
- **JavaScript ES6+** - Interatividade e APIs
- **Chart.js** - Gráficos e visualizações
- **Fetch API** - Comunicação com backend
- **CSS Grid/Flexbox** - Layout responsivo

## 🔄 Integração com Backend

### Endpoints Utilizados
```javascript
// Principais endpoints do backend
GET /api/v1/accounts                    # Lista contas
GET /api/v1/accounts/{id}              # Detalhes da conta
GET /api/v1/accounts/{id}/resources    # Recursos AWS
GET /api/v1/accounts/{id}/alerts       # Alertas ativos
POST /api/v1/alerts/{id}/analyze       # Análise com IA
```

### Polling e Cache
- **Auto-refresh**: 30 segundos (otimizado)
- **Cache local**: Para reduzir chamadas
- **Loading states**: Para melhor UX

## 🎯 Próximas Melhorias

- [ ] **Dark/Light theme toggle**
- [ ] **Filtros avançados** para recursos
- [ ] **Dashboards customizáveis**
- [ ] **Notificações em tempo real** (WebSocket)
- [ ] **Export de dados** (PDF/Excel)
- [ ] **PWA support** para mobile

---

**Interface desenvolvida para máxima usabilidade e performance** ⚡
