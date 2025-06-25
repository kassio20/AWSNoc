# SelectNOC IA - Guia de Otimização CloudWatch

## 📋 Resumo das Otimizações Implementadas

Este documento detalha as otimizações implementadas para reduzir os custos de consultas ao CloudWatch mantendo a funcionalidade completa do sistema.

## 🚀 Principais Otimizações

### 1. **Polling Inteligente com Intervalos de 30 segundos**
- ✅ Consultas ao CloudWatch limitadas a intervalos de 30 segundos
- ✅ Diferentes intervalos baseados no estado do alarme:
  - Alarmes ATIVOS: 30 segundos
  - Alarmes OK: 2 minutos  
  - Dados insuficientes: 1 minuto

### 2. **Sistema de Cache Inteligente**
- ✅ Cache em memória com TTL configurável
- ✅ Cache específico por tipo de dados:
  - Alarmes: 25 segundos de TTL
  - Métricas: 55 segundos de TTL
  - Histórico: 115 segundos de TTL
- ✅ Limpeza automática de cache expirado

### 3. **Consultas Otimizadas**
- ✅ Busca de histórico apenas para alarmes ativos
- ✅ Busca de métricas apenas para alarmes em estado ALARM
- ✅ Processamento em lotes para reduzir chamadas API
- ✅ Paginação otimizada com limites configuráveis

### 4. **Análise de IA Otimizada**
- ✅ Análise apenas para alarmes críticos e de alta prioridade
- ✅ Processamento em lotes com timeout
- ✅ Cache de análises para evitar reprocessamento

## 📊 Monitoramento de Custos

### Endpoints Adicionados

```bash
# Estatísticas do cache
GET /api/v1/cache/stats

# Limpar cache
POST /api/v1/cache/clear
```

### Monitor de Custos

O sistema inclui um monitor automático que rastreia:
- Número de consultas por hora/dia
- Taxa de hit do cache
- Custos estimados
- Economia gerada pelas otimizações

## 🔧 Configuração

### Arquivo de Configuração: `config/cloudwatch_config.py`

```python
# Intervalos de polling (em segundos)
POLLING_INTERVALS = {
    'alarms': 30,           # Consultar alarmes a cada 30 segundos
    'metrics': 60,          # Consultar métricas a cada 60 segundos  
    'logs': 120,            # Consultar logs a cada 2 minutos
    'discovery': 300        # Descoberta completa a cada 5 minutos
}

# TTL do cache (em segundos)
CACHE_TTL = {
    'alarms': 25,           # Cache de alarmes por 25 segundos
    'metrics': 55,          # Cache de métricas por 55 segundos
    'logs': 115,            # Cache de logs por 115 segundos
}
```

## 📈 Benefícios Esperados

### Redução de Custos
- **60-80% redução** nas consultas diretas ao CloudWatch
- **Economia estimada**: $50-200/mês dependendo do volume
- **Maior eficiência** no uso dos limites de API

### Performance
- **Resposta mais rápida** para consultas repetidas
- **Menor latência** através do cache
- **Melhor experiência** do usuário

### Estabilidade
- **Menor sobrecarga** nos serviços AWS
- **Redução de throttling** da API
- **Maior confiabilidade** do sistema

## 🛠️ Como Usar

### 1. Aplicar as Otimizações

```bash
cd /opt/selectnoc
python3 apply_cloudwatch_optimizations.py
```

### 2. Reiniciar o Serviço

```bash
sudo systemctl restart selectnoc
```

### 3. Verificar Status

```bash
# Verificar logs
sudo journalctl -u selectnoc -f

# Verificar cache
curl http://localhost:8000/api/v1/cache/stats
```

### 4. Monitorar Custos

```bash
# Gerar relatório de custos
python3 cloudwatch_cost_monitor.py
```

## 📋 Checklist de Verificação

- [ ] ✅ Backup do arquivo original criado
- [ ] ✅ Otimizações aplicadas sem erros
- [ ] ✅ Serviço reiniciado com sucesso
- [ ] ✅ Interface mostra "Modo Otimizado Ativo"
- [ ] ✅ Cache stats disponível via API
- [ ] ✅ Logs mostram uso do cache

## ⚙️ Configurações Avançadas

### Ajustar Intervalos de Polling

Edite `/opt/selectnoc/config/cloudwatch_config.py`:

```python
# Para ambientes de desenvolvimento (menor frequência)
POLLING_INTERVALS = {
    'alarms': 60,           # 1 minuto
    'metrics': 120,         # 2 minutos
}

# Para ambientes críticos (maior frequência)
POLLING_INTERVALS = {
    'alarms': 15,           # 15 segundos
    'metrics': 30,          # 30 segundos
}
```

### Ajustar TTL do Cache

```python
# Cache mais agressivo (maior economia)
CACHE_TTL = {
    'alarms': 45,           # 45 segundos
    'metrics': 90,          # 90 segundos
}

# Cache mais conservador (dados mais frescos)
CACHE_TTL = {
    'alarms': 15,           # 15 segundos
    'metrics': 30,          # 30 segundos
}
```

## 🔍 Troubleshooting

### Problema: Cache não funciona
```bash
# Verificar se módulos foram carregados
grep "Módulos de otimização CloudWatch carregados" /var/log/selectnoc/app.log

# Limpar cache
curl -X POST http://localhost:8000/api/v1/cache/clear
```

### Problema: Muitas consultas ainda
```bash
# Verificar configuração
python3 -c "from config.cloudwatch_config import CloudWatchConfig; print(CloudWatchConfig.POLLING_INTERVALS)"

# Aumentar intervalos se necessário
```

### Problema: Dados desatualizados
```bash
# Forçar refresh
curl -X POST http://localhost:8000/api/v1/alarms/discover

# Reduzir TTL do cache
```

## 📊 Monitoramento Contínuo

### Métricas Importantes

1. **Cache Hit Rate**: Deve ser > 50%
2. **Custo Diário**: Deve ser < $1.00
3. **Consultas por Hora**: Monitorar tendências
4. **Tempo de Resposta**: Deve melhorar com cache

### Alertas Recomendados

- Cache hit rate < 30%
- Custo diário > $2.00
- Muitas consultas simultâneas
- Erros de timeout frequentes

## 🔄 Rollback (se necessário)

```bash
cd /opt/selectnoc

# Restaurar backup
cp simple_main_backup_before_optimizations_*.py simple_main.py

# Reiniciar serviço
sudo systemctl restart selectnoc
```

## 📞 Suporte

Para questões sobre as otimizações:
1. Verificar logs: `/var/log/selectnoc/`
2. Testar endpoints: `/api/v1/cache/stats`
3. Revisar configurações: `config/cloudwatch_config.py`

---

**Data de Implementação**: 24/06/2025
**Versão**: 1.0
**Status**: ✅ Ativo e Otimizado
