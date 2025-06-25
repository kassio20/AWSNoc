# 🚀 ANÁLISE GENÉRICA DE LOGS ECS - Target Groups

## 🎯 SOLUÇÃO UNIVERSAL PARA QUALQUER TARGET GROUP ECS

### 📋 **DESCOBERTA DINÂMICA DE LOG GROUPS**
A análise agora funciona para **QUALQUER** Target Group ECS, não importa o nome do cluster ou service:

#### ✅ **Extração Automática da Task Definition**
- Lê automaticamente a task definition do service
- Extrai log groups configurados em cada container
- Detecta nomes de containers e gera padrões de logs

#### ✅ **Padrões Dinâmicos Gerados**
Para qualquer `cluster_name` e `service_name`:
```
/ecs/{service_name}
/aws/ecs/{service_name}
/{service_name}
{service_name}
/aws/ecs/{cluster_name}
/ecs/{cluster_name}
/aws/ecs/{cluster_name}/{service_name}
/aws/ecs/containerinsights/{cluster_name}/performance
/aws/fargate/{service_name}
/app/{service_name}
/logs/{service_name}
```

### 🔍 **DETECÇÃO INTELIGENTE DE PROBLEMAS**
Sistema de classificação automática que funciona para qualquer tipo de aplicação:

#### 🚨 **DEPENDENCY_ERROR**
- `npm ERR!`, `yarn error`, `pip error`
- Problemas de build e dependências

#### 🔌 **CONNECTION_ERROR** 
- `connection refused`, `connection timeout`, `connection reset`
- Problemas de conectividade de rede

#### 💾 **MEMORY_ERROR**
- `out of memory`, `memory`, `oom`
- Problemas de recursos de memória

#### 🔐 **PERMISSION_ERROR**
- `permission denied`, `access denied`, `403`, `401`
- Problemas de permissões e autenticação

#### 🌐 **PORT_ERROR**
- `port`, `bind`, `address already in use`
- Problemas com portas e binding

#### ❤️ **HEALTH_CHECK_ISSUE**
- `health`, `healthcheck`, `/health`
- Problemas com health checks

#### ⚖️ **LOAD_BALANCER_ISSUE**
- `target group`, `load balancer`, `elb`
- Problemas com Target Groups e ELB

#### 🐳 **CONTAINER_RUNTIME_ERROR**
- `container`, `docker`, `runtime`
- Problemas de runtime do container

#### ⚙️ **CONFIGURATION_ERROR**
- `config`, `configuration`, `env`, `environment`
- Problemas de configuração e variáveis

### 🔄 **PROCESSO DE ANÁLISE ADAPTATIVO**

#### 1. **Descoberta Automática**
```python
# Para QUALQUER service ECS
→ Extrai task definition automaticamente
→ Identifica log groups configurados
→ Gera padrões baseados em cluster/service/container names
→ Remove duplicatas e valores None
```

#### 2. **Busca Inteligente de Logs**
```python
# Para cada task que falhou
→ Busca logs específicos usando task ID
→ Se não encontrar, busca logs gerais com filtros de erro
→ Classifica automaticamente os tipos de problema
→ Correlaciona problemas entre múltiplas tasks
```

#### 3. **Análise da IA Melhorada**
```python
# Contexto enriquecido para IA
→ Task IDs específicas com timestamps
→ Logs categorizados por tipo de problema
→ Exit codes e stopped reasons detalhados
→ Padrões de falha identificados
→ Recomendações específicas por tipo de problema
```

### 🎯 **CASOS DE USO SUPORTADOS**

#### ✅ **Qualquer Aplicação**
- Node.js (npm, yarn)
- Python (pip, requirements.txt)
- Java (Maven, Gradle)
- .NET, Go, PHP, Ruby, etc.

#### ✅ **Qualquer Arquitetura**
- Fargate
- EC2 Launch Type
- Container Insights habilitado/desabilitado
- Qualquer naming convention

#### ✅ **Qualquer Problema**
- Application crashes
- Dependency failures
- Health check failures
- Memory/CPU issues
- Network connectivity
- Permission problems
- Configuration errors

### 📊 **RESULTADO ESPERADO**

#### **ANTES**: Análise genérica limitada
- Logs básicos sem contexto específico
- Análise superficial de tasks
- Padrões hardcoded para ambientes específicos

#### **DEPOIS**: Análise cirúrgica universal
- **Task IDs específicas** com logs individuais
- **Classificação automática** de tipos de problema  
- **Log groups descobertos dinamicamente** 
- **Análise adaptável** para qualquer Target Group ECS
- **IA com contexto rico** sobre problemas específicos

### 🔧 **COMO FUNCIONA**

1. **Target Group detectado como unhealthy**
2. **Sistema descobre automaticamente** qual ECS service está associado
3. **Extrai task definition** e log groups configurados
4. **Gera padrões dinâmicos** baseados em nomes reais
5. **Busca logs específicos** das tasks que falharam
6. **Classifica problemas** automaticamente
7. **Fornece análise precisa** para IA com comandos específicos

---

## ✅ **RESULTADO: SOLUÇÃO UNIVERSAL**

Esta análise agora funciona para **QUALQUER Target Group associado a ECS**, independente de:
- Nome do cluster
- Nome do service  
- Tipo de aplicação
- Arquitetura (Fargate/EC2)
- Naming conventions
- Log group configurations

**A IA receberá logs específicos das tasks que falharam, com classificação automática dos problemas e contexto rico para diagnóstico preciso!** 🎯
