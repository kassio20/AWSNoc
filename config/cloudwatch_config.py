"""
SelectNOC IA - Configuração de CloudWatch
Configurações para otimizar custos de consultas do CloudWatch
"""

from datetime import timedelta

class CloudWatchConfig:
    """
    Configurações para consultas do CloudWatch
    """
    
    # Intervalos de polling (em segundos)
    POLLING_INTERVALS = {
        'alarms': 30,           # Consultar alarmes a cada 30 segundos
        'metrics': 60,          # Consultar métricas a cada 60 segundos  
        'logs': 120,            # Consultar logs a cada 2 minutos
        'discovery': 300        # Descoberta completa a cada 5 minutos
    }
    
    # Configurações de cache
    CACHE_TTL = {
        'alarms': 25,           # Cache de alarmes por 25 segundos
        'metrics': 55,          # Cache de métricas por 55 segundos
        'logs': 115,            # Cache de logs por 115 segundos
        'discovery': 295        # Cache de descoberta por 295 segundos
    }
    
    # Limites para consultas do CloudWatch
    QUERY_LIMITS = {
        'max_datapoints_per_query': 100,    # Máximo de pontos de dados por consulta
        'max_metrics_per_batch': 20,        # Máximo de métricas por lote
        'history_hours': 24,                # Horas de histórico para buscar
        'max_alarm_history_records': 10     # Máximo de registros de histórico por alarme
    }
    
    # Configurações de otimização
    OPTIMIZATION = {
        'use_composite_queries': True,       # Usar consultas compostas quando possível
        'batch_metric_requests': True,       # Agrupar requisições de métricas
        'cache_enabled': True,               # Habilitar cache
        'compress_historical_data': True,    # Comprimir dados históricos
        'lazy_load_details': True           # Carregar detalhes sob demanda
    }
    
    # Configurações específicas por estado de alarme
    ALARM_POLLING_BY_STATE = {
        'ALARM': 30,            # Alarmes ativos: verificar a cada 30s
        'OK': 120,              # Alarmes OK: verificar a cada 2 minutos
        'INSUFFICIENT_DATA': 60  # Dados insuficientes: verificar a cada 1 minuto
    }
    
    # Configurações de timeout
    TIMEOUTS = {
        'connection_timeout': 30,
        'read_timeout': 60,
        'retry_attempts': 3,
        'retry_delay': 5
    }

    @classmethod
    def get_polling_interval(cls, component: str) -> int:
        """Obter intervalo de polling para um componente"""
        return cls.POLLING_INTERVALS.get(component, 60)
    
    @classmethod
    def get_cache_ttl(cls, component: str) -> int:
        """Obter TTL do cache para um componente"""
        return cls.CACHE_TTL.get(component, 30)
    
    @classmethod
    def should_use_cache(cls) -> bool:
        """Verificar se deve usar cache"""
        return cls.OPTIMIZATION['cache_enabled']
    
    @classmethod
    def get_alarm_polling_interval(cls, state: str) -> int:
        """Obter intervalo de polling específico para o estado do alarme"""
        return cls.ALARM_POLLING_BY_STATE.get(state, 60)
