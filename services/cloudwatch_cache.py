"""
SelectNOC IA - Cache Service para CloudWatch
Serviço de cache para otimizar consultas e reduzir custos do CloudWatch
"""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class CloudWatchCache:
    """
    Sistema de cache em memória para dados do CloudWatch
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl: Dict[str, float] = {}
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Gerar chave única para o cache"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def set(self, key: str, data: Any, ttl_seconds: int = 300) -> None:
        """Armazenar dados no cache com TTL"""
        try:
            self._cache[key] = {
                'data': data,
                'stored_at': time.time(),
                'ttl': ttl_seconds
            }
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
        except Exception as e:
            logger.error(f"Erro ao salvar no cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Recuperar dados do cache se ainda válidos"""
        try:
            if key not in self._cache:
                return None
            
            cache_entry = self._cache[key]
            stored_at = cache_entry['stored_at']
            ttl = cache_entry['ttl']
            
            # Verificar se ainda é válido
            if time.time() - stored_at > ttl:
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
                return None
            
            logger.debug(f"Cache hit: {key}")
            return cache_entry['data']
            
        except Exception as e:
            logger.error(f"Erro ao recuperar do cache: {e}")
            return None
    
    def invalidate(self, pattern: str = None) -> None:
        """Invalidar entradas do cache"""
        try:
            if pattern:
                keys_to_remove = [k for k in self._cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self._cache[key]
                logger.debug(f"Cache invalidated: {len(keys_to_remove)} entries with pattern '{pattern}'")
            else:
                self._cache.clear()
                logger.debug("Cache cleared completely")
        except Exception as e:
            logger.error(f"Erro ao invalidar cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for key, entry in self._cache.items():
            if current_time - entry['stored_at'] <= entry['ttl']:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'memory_usage_mb': len(str(self._cache)) / (1024 * 1024)
        }
    
    def cleanup_expired(self) -> int:
        """Limpar entradas expiradas"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time - entry['stored_at'] > entry['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)

class CloudWatchCacheManager:
    """
    Gerenciador de cache específico para CloudWatch
    """
    
    def __init__(self):
        self.cache = CloudWatchCache()
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutos
    
    def get_alarms_key(self, account_id: Optional[int] = None) -> str:
        """Gerar chave para cache de alarmes"""
        return f"alarms_{account_id or 'all'}"
    
    def get_metrics_key(self, namespace: str, metric_name: str, 
                       dimensions: List[Dict], period: int) -> str:
        """Gerar chave para cache de métricas"""
        dims_str = json.dumps(dimensions, sort_keys=True)
        return f"metrics_{namespace}_{metric_name}_{dims_str}_{period}"
    
    def get_alarm_history_key(self, alarm_name: str, hours: int = 24) -> str:
        """Gerar chave para cache de histórico de alarmes"""
        return f"alarm_history_{alarm_name}_{hours}h"
    
    def cache_alarms(self, alarms: List[Dict], account_id: Optional[int] = None, 
                    ttl: int = 25) -> None:
        """Cache de alarmes"""
        key = self.get_alarms_key(account_id)
        self.cache.set(key, alarms, ttl)
    
    def get_cached_alarms(self, account_id: Optional[int] = None) -> Optional[List[Dict]]:
        """Recuperar alarmes do cache"""
        key = self.get_alarms_key(account_id)
        return self.cache.get(key)
    
    def cache_metrics(self, metrics_data: Dict, namespace: str, metric_name: str,
                     dimensions: List[Dict], period: int, ttl: int = 55) -> None:
        """Cache de métricas"""
        key = self.get_metrics_key(namespace, metric_name, dimensions, period)
        self.cache.set(key, metrics_data, ttl)
    
    def get_cached_metrics(self, namespace: str, metric_name: str,
                          dimensions: List[Dict], period: int) -> Optional[Dict]:
        """Recuperar métricas do cache"""
        key = self.get_metrics_key(namespace, metric_name, dimensions, period)
        return self.cache.get(key)
    
    def cache_alarm_history(self, history: List[Dict], alarm_name: str, 
                          hours: int = 24, ttl: int = 115) -> None:
        """Cache de histórico de alarmes"""
        key = self.get_alarm_history_key(alarm_name, hours)
        self.cache.set(key, history, ttl)
    
    def get_cached_alarm_history(self, alarm_name: str, 
                               hours: int = 24) -> Optional[List[Dict]]:
        """Recuperar histórico de alarmes do cache"""
        key = self.get_alarm_history_key(alarm_name, hours)
        return self.cache.get(key)
    
    def invalidate_account_cache(self, account_id: int) -> None:
        """Invalidar cache específico de uma conta"""
        self.cache.invalidate(f"_{account_id}")
    
    def invalidate_alarms_cache(self) -> None:
        """Invalidar cache de alarmes"""
        self.cache.invalidate("alarms_")
    
    def periodic_cleanup(self) -> None:
        """Limpeza periódica do cache"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cleaned = self.cache.cleanup_expired()
            self.last_cleanup = current_time
            logger.info(f"Cache cleanup: removed {cleaned} expired entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        return self.cache.get_cache_stats()

# Instância global do cache
cache_manager = CloudWatchCacheManager()
