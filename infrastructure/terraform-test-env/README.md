# SelectNocIA Test Environment

Este ambiente de testes foi criado para simular falhas nos serviços e testar a capacidade da IA do SelectNocIA de identificar problemas e sugerir soluções.

## Arquitetura

- **VPC**: Rede isolada com subnets públicas e privadas
- **ALB**: Application Load Balancer público para distribuir tráfego
- **ECS**: Cluster Fargate com dois serviços:
  - **Hello World Service**: Aplicação Node.js saudável (2 instâncias)
  - **Unhealthy App Service**: Aplicação para simular falhas (1 instância)
- **Target Groups**: Grupos de alvos com health checks configurados
- **CloudWatch**: Logs e métricas para monitoramento

## Recursos Criados

### Networking
- 1 VPC (10.0.0.0/16)
- 2 Subnets públicas (para ALB)
- 2 Subnets privadas (para ECS tasks)
- 2 NAT Gateways (para acesso à internet das tasks)
- Internet Gateway
- Route Tables

### Load Balancer
- Application Load Balancer público
- 2 Target Groups:
  - `hello-world-tg`: Para aplicação saudável
  - `unhealthy-app-tg`: Para aplicação de testes
- Listener rules para roteamento

### ECS
- Cluster ECS com Container Insights habilitado
- 2 Task Definitions (Node.js apps)
- 2 Services (Fargate)
- IAM Roles para execução
- CloudWatch Log Group

## Deploy

1. Inicializar Terraform:
```bash
terraform init
```

2. Planejar o deploy:
```bash
terraform plan
```

3. Aplicar as mudanças:
```bash
terraform apply
```

## URLs de Teste

Após o deploy, você terá acesso a:

- **Hello World App**: `http://<ALB_DNS>/`
- **Unhealthy App**: `http://<ALB_DNS>/unhealthy`
- **Quebrar App**: `http://<ALB_DNS>/unhealthy/break` (simula falha)
- **Consertar App**: `http://<ALB_DNS>/unhealthy/fix` (restaura saúde)

## Simulação de Falhas

### 1. Falha no Health Check
```bash
curl http://<ALB_DNS>/unhealthy/break
```
Isso fará com que o health check falhe e o target group marque a instância como unhealthy.

### 2. Restaurar Saúde
```bash
curl http://<ALB_DNS>/unhealthy/fix
```
Restaura o health check para sucesso.

### 3. Parar Serviço
```bash
aws ecs update-service --cluster selectnocia-test-cluster --service selectnocia-unhealthy-app-service --desired-count 0
```

### 4. Escalar Serviço
```bash
aws ecs update-service --cluster selectnocia-test-cluster --service selectnocia-hello-world-service --desired-count 4
```

## Monitoramento

### CloudWatch Logs
```bash
aws logs describe-log-groups --log-group-name-prefix "/ecs/selectnocia-test"
```

### ECS Service Status
```bash
aws ecs describe-services --cluster selectnocia-test-cluster --services selectnocia-hello-world-service selectnocia-unhealthy-app-service
```

### Target Group Health
```bash
aws elbv2 describe-target-health --target-group-arn <TARGET_GROUP_ARN>
```

## Cenários de Teste para IA

1. **Health Check Failures**: Simular falhas nos health checks
2. **Service Scaling Issues**: Parar ou escalar serviços incorretamente
3. **Load Balancer Issues**: Targets unhealthy
4. **Network Issues**: Security groups ou conectividade
5. **Resource Limits**: CPU/Memory high utilization

## Limpeza

Para destruir o ambiente:
```bash
terraform destroy
```

## Custos Estimados

- **ALB**: ~$16/mês
- **NAT Gateways**: ~$32/mês (2x $16)
- **ECS Fargate**: ~$20/mês (3 tasks)
- **CloudWatch Logs**: ~$1/mês
- **Total**: ~$69/mês

**Importante**: Este é um ambiente de testes. Destrua após o uso para evitar custos desnecessários.

