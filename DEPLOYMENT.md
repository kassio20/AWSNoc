# 🚀 Guia de Deployment - SelectNOC IA

## 📋 Visão Geral

Este guia cobre o deployment completo do SelectNOC IA na sua conta AWS, criando uma ferramenta interna para seu NOC monitorar múltiplas contas de clientes.

## 🎯 Arquitetura Final

```
┌─────────────────────────────────────────────────────────────────┐
│                     SUA CONTA AWS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐     │
│  │ CloudFront  │    │     ALB     │    │   ECS Fargate   │     │
│  │  Frontend   │    │   Backend   │    │   (API + AI)    │     │
│  └─────────────┘    └─────────────┘    └─────────────────┘     │
│         │                   │                    │              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐     │
│  │ S3 Frontend │    │     RDS     │    │  ElastiCache    │     │
│  │   Assets    │    │ PostgreSQL  │    │     Redis       │     │
│  └─────────────┘    └─────────────┘    └─────────────────┘     │
│                                                                 │
│                    ┌─────────────────┐                         │
│                    │ Amazon Bedrock  │                         │
│                    │   Claude-3      │                         │
│                    └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
         ┌─────────────────┐    ┌─────────────────┐
         │ Cliente A AWS   │    │ Cliente B AWS   │
         │ (Cross-Account  │    │ (IAM Keys ou    │
         │    Roles)       │    │ Temp Creds)     │
         └─────────────────┘    └─────────────────┘
```

## 🛠️ Pré-requisitos

### 1. Ferramentas Necessárias
```bash
# Terraform
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Docker
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# Node.js (para frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Configurar AWS CLI
```bash
# Configure com suas credenciais
aws configure --profile selectnoc-deploy
# Região: us-east-1 (ou sua preferida)
# Format: json

# Verificar acesso
aws sts get-caller-identity --profile selectnoc-deploy
```

### 3. Verificar Acesso ao Bedrock
```bash
# Verificar modelos disponíveis
aws bedrock list-foundation-models \
  --region us-east-1 \
  --profile selectnoc-deploy

# Se não tiver acesso, solicitar no console AWS:
# https://console.aws.amazon.com/bedrock/home#/modelaccess
```

## 🏗️ Deployment Step-by-Step

### Etapa 1: Clonar e Preparar Projeto
```bash
# 1. Clone o projeto
git clone <repo-url> SelectNocIA
cd SelectNocIA

# 2. Configurar ambiente
cp .env.example .env
# Editar .env com suas configurações

# 3. Instalar dependências Python
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Instalar dependências Frontend
cd frontend
npm install
cd ..
```

### Etapa 2: Build das Imagens Docker
```bash
# 1. Build da API
docker build -t selectnoc-ia/api:latest -f docker/Dockerfile.api .

# 2. Build do Collector
docker build -t selectnoc-ia/collector:latest -f docker/Dockerfile.collector .

# 3. Build do Frontend
cd frontend
npm run build
cd ..
```

### Etapa 3: Deploy da Infraestrutura
```bash
# 1. Ir para diretório Terraform
cd infrastructure/terraform

# 2. Inicializar Terraform
terraform init

# 3. Planejar deployment
terraform plan \
  -var="aws_region=us-east-1" \
  -var="environment=production" \
  -var="domain_name=selectnoc.ai"

# 4. Aplicar infraestrutura
terraform apply \
  -var="aws_region=us-east-1" \
  -var="environment=production" \
  -var="domain_name=selectnoc.ai"

# 5. Salvar outputs importantes
terraform output > ../outputs.txt
```

### Etapa 4: Push das Imagens para ECR
```bash
# 1. Obter ECR repository URLs
ECR_API=$(terraform output -raw ecr_api_repository_url)
ECR_COLLECTOR=$(terraform output -raw ecr_collector_repository_url)

# 2. Login no ECR
aws ecr get-login-password --region us-east-1 --profile selectnoc-deploy | \
  docker login --username AWS --password-stdin $ECR_API

# 3. Tag e push API
docker tag selectnoc-ia/api:latest $ECR_API:latest
docker push $ECR_API:latest

# 4. Tag e push Collector
docker tag selectnoc-ia/collector:latest $ECR_COLLECTOR:latest
docker push $ECR_COLLECTOR:latest
```

### Etapa 5: Deploy do Frontend
```bash
# 1. Obter bucket S3
S3_BUCKET=$(terraform output -raw s3_frontend_bucket)

# 2. Sync frontend build
aws s3 sync frontend/dist/ s3://$S3_BUCKET/ \
  --profile selectnoc-deploy \
  --delete

# 3. Invalidar CloudFront
CLOUDFRONT_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='SelectNOC IA Frontend'].Id" \
  --output text --profile selectnoc-deploy)

aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_ID \
  --paths "/*" \
  --profile selectnoc-deploy
```

### Etapa 6: Configurar Database
```bash
# 1. Obter endpoint do RDS
DB_ENDPOINT=$(terraform output -raw database_endpoint)

# 2. Executar migrations
python manage.py migrate

# 3. Criar usuário admin
python manage.py create_admin_user
```

## 🔧 Configuração Pós-Deploy

### 1. Verificar Health Checks
```bash
# Obter URL do ALB
ALB_URL=$(terraform output -raw alb_dns_name)

# Testar API
curl http://$ALB_URL/health

# Resposta esperada:
# {"status": "healthy", "service": "SelectNOC IA"}
```

### 2. Configurar DNS (Opcional)
```bash
# Se você tem um domínio, criar registros:
# app.selectnoc.ai -> CNAME para CloudFront
# api.selectnoc.ai -> CNAME para ALB
```

### 3. Testar Bedrock
```bash
# Testar via API
curl -X POST http://$ALB_URL/api/v1/test/bedrock
```

### 4. Setup Inicial do Frontend
1. Acesse: http://cloudfront-domain/
2. Faça login inicial
3. Configure primeiro usuário NOC
4. Adicione primeira conta de cliente

## 📱 Configuração do Frontend NOC

### 1. Estrutura de Usuários NOC
```yaml
Roles:
  - admin: "Gerenciar contas, usuários, configurações"
  - operator: "Monitorar alertas, gerenciar incidentes"
  - viewer: "Apenas visualização"
```

### 2. Adicionar Primeira Conta de Cliente

#### Via Cross-Account Role (Recomendado):
1. **No Frontend**: Ir em "Contas" → "Adicionar Conta"
2. **Escolher**: "Cross-Account Role"
3. **Download**: Template CloudFormation
4. **Cliente executa**: Template na conta dele
5. **Inserir**: Role ARN e External ID
6. **Testar**: Conexão

#### Via IAM Keys:
1. **Cliente cria**: Usuário IAM read-only
2. **Inserir**: Access Key + Secret Key
3. **Testar**: Permissões

## 🔐 Segurança e Boas Práticas

### 1. Permissões Mínimas para Clientes
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:StartQuery",
        "logs:GetQueryResults",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "ecs:DescribeClusters",
        "ecs:DescribeServices",
        "elasticloadbalancing:DescribeTargetHealth",
        "rds:DescribeDBInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. Monitoramento da Plataforma
```bash
# CloudWatch Dashboards criados automaticamente:
# - SelectNOC-IA-Application-Performance
# - SelectNOC-IA-Customer-Usage
# - SelectNOC-IA-AI-Performance
```

### 3. Backup e Disaster Recovery
```bash
# RDS: Backups automáticos (7 dias)
# S3: Versionamento habilitado
# ECS: Multi-AZ deployment
```

## 📊 Monitoramento e Alertas

### 1. Métricas Principais
```yaml
Application:
  - "API Response Time"
  - "Error Rate"
  - "AI Analysis Latency"
  - "Database Connections"

Business:
  - "Accounts Monitored"
  - "Logs Processed/Hour"
  - "Alerts Generated"
  - "Customer Satisfaction"
```

### 2. Alertas Críticos
```yaml
Infrastructure:
  - "ECS Service Down"
  - "Database Unavailable"
  - "High Memory Usage"

Customer Impact:
  - "Failed Customer Auth"
  - "High Analysis Latency"
  - "Bedrock API Errors"
```

## 💰 Estimativa de Custos

### Infraestrutura Base (Mensal):
```yaml
Compute:
  - "ECS Fargate (2 tasks)": "$150-250"
  - "ALB": "$20-30"

Database:
  - "RDS r6g.large Multi-AZ": "$200-300"
  - "ElastiCache r6g.large": "$150-200"

Storage:
  - "S3": "$10-50"
  - "EBS": "$20-40"

AI Services:
  - "Bedrock (Claude-3)": "$100-500"
  - "CloudWatch Logs": "$50-200"

Total Base: "$700-1370/mês"
```

### Scaling por Cliente:
```yaml
Por 10 contas monitoradas: "+$100-200/mês"
Por 1M logs processados: "+$50-100/mês"
```

## 🔄 CI/CD e Updates

### 1. GitHub Actions (Opcional)
```yaml
# .github/workflows/deploy.yml
# Automated deployment on git push
```

### 2. Manual Updates
```bash
# Update API
docker build -t selectnoc-ia/api:v1.1 .
docker tag selectnoc-ia/api:v1.1 $ECR_API:v1.1
docker push $ECR_API:v1.1

# Update ECS service
aws ecs update-service \
  --cluster selectnoc-ia-cluster \
  --service selectnoc-ia-api-service \
  --task-definition selectnoc-ia-api:v1.1
```

## 🆘 Troubleshooting

### 1. Problemas Comuns
```bash
# ECS Tasks não iniciam
aws ecs describe-services --cluster selectnoc-ia-cluster
aws logs tail /ecs/selectnoc-ia --follow

# Bedrock não funciona
aws bedrock list-foundation-models --region us-east-1

# Frontend não carrega
aws cloudfront list-invalidations --distribution-id $CLOUDFRONT_ID
```

### 2. Logs Importantes
```bash
# Application logs
aws logs tail /ecs/selectnoc-ia --follow

# Database logs
aws rds describe-db-log-files --db-instance-identifier selectnoc-ia-db

# Load balancer logs
# (Configurados para S3 automaticamente)
```

## 📞 Suporte e Manutenção

### 1. Backups
- **Database**: Automatico (7 dias)
- **Código**: Git repository
- **Configurações**: Terraform state

### 2. Updates de Segurança
- **OS**: ECS Fargate managed
- **Database**: Auto minor version updates
- **Dependencies**: Monitoramento via GitHub Security

### 3. Scaling
```bash
# Aumentar capacidade ECS
aws ecs update-service \
  --cluster selectnoc-ia-cluster \
  --service selectnoc-ia-api-service \
  --desired-count 4

# Upgrade database
# (Requer planejamento de downtime)
```

## ✅ Checklist de Go-Live

- [ ] Infraestrutura deployed
- [ ] Frontend acessível
- [ ] API respondendo
- [ ] Bedrock funcionando
- [ ] Database conectado
- [ ] Redis funcionando
- [ ] SSL/HTTPS configurado
- [ ] Monitoramento ativo
- [ ] Backups configurados
- [ ] Primeira conta de cliente adicionada
- [ ] Equipe NOC treinada
- [ ] Documentação distribuída

---

🎉 **Parabéns!** Seu SelectNOC IA está pronto para monitorar múltiplas contas AWS com inteligência artificial!

