#!/usr/bin/env python3
"""
AWSNoc IA IA - CloudWatch Cost Monitor
Monitor de custos e otimização para consultas do CloudWatch
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class CloudWatchCostMonitor:
    """
    Monitor de custos e otimização do CloudWatch
    """
    
    def __init__(self):
        self.query_log = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.start_time = time.time()
        
        # Custos estimados por tipo de operação (em USD)
        self.cost_per_operation = {
            'describe_alarms': 0.01,           # $0.01 por 1000 requests
            'get_metric_statistics': 0.01,     # $0.01 por 1000 requests  
            'describe_alarm_history': 0.01,    # $0.01 por 1000 requests
            'list_tags_for_resource': 0.005,   # $0.005 por 1000 requests
            'get_metric_data': 0.01            # $0.01 por 1000 requests
        }
    
    def log_query(self, operation: str, cached: bool = False, 
                  estimated_cost: float = 0.0):
        """Registrar uma consulta ao CloudWatch"""
        query_record = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'cached': cached,
            'estimated_cost': estimated_cost if not cached else 0.0
        }
        
        self.query_log.append(query_record)
        
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        logger.debug(f"CloudWatch query logged: {operation} (cached: {cached})")
    
    def estimate_operation_cost(self, operation: str, 
                               quantity: int = 1) -> float:
        """Estimar custo de uma operação"""
        base_cost = self.cost_per_operation.get(operation, 0.01)
        return (base_cost * quantity) / 1000  # Custo por unidade
    
    def get_hourly_stats(self) -> Dict[str, Any]:
        """Obter estatísticas da última hora"""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        recent_queries = [
            q for q in self.query_log 
            if datetime.fromisoformat(q['timestamp']) > one_hour_ago
        ]
        
        total_cost = sum(q['estimated_cost'] for q in recent_queries)
        cached_queries = len([q for q in recent_queries if q['cached']])
        total_queries = len(recent_queries)
        
        cache_hit_rate = (cached_queries / total_queries * 100) if total_queries > 0 else 0
        
        return {
            'period': 'last_hour',
            'total_queries': total_queries,
            'cached_queries': cached_queries,
            'api_queries': total_queries - cached_queries,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'estimated_cost_usd': round(total_cost, 6),
            'cost_saved_usd': round(
                sum(self.estimate_operation_cost(q['operation']) for q in recent_queries if q['cached']), 6
            )
        }
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do dia"""
        one_day_ago = datetime.now() - timedelta(days=1)
        
        recent_queries = [
            q for q in self.query_log 
            if datetime.fromisoformat(q['timestamp']) > one_day_ago
        ]
        
        total_cost = sum(q['estimated_cost'] for q in recent_queries)
        cached_queries = len([q for q in recent_queries if q['cached']])
        total_queries = len(recent_queries)
        
        cache_hit_rate = (cached_queries / total_queries * 100) if total_queries > 0 else 0
        
        # Calcular economia estimada
        potential_cost = sum(
            self.estimate_operation_cost(q['operation']) for q in recent_queries
        )
        cost_saved = potential_cost - total_cost
        
        return {
            'period': 'last_24_hours',
            'total_queries': total_queries,
            'cached_queries': cached_queries,
            'api_queries': total_queries - cached_queries,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'estimated_cost_usd': round(total_cost, 6),
            'potential_cost_usd': round(potential_cost, 6),
            'cost_saved_usd': round(cost_saved, 6),
            'savings_percentage': round((cost_saved / potential_cost * 100) if potential_cost > 0 else 0, 2)
        }
    
    def get_operation_breakdown(self) -> Dict[str, Any]:
        """Obter breakdown por tipo de operação"""
        operation_stats = {}
        
        for query in self.query_log:
            op = query['operation']
            if op not in operation_stats:
                operation_stats[op] = {
                    'total_calls': 0,
                    'cached_calls': 0,
                    'api_calls': 0,
                    'total_cost': 0.0
                }
            
            operation_stats[op]['total_calls'] += 1
            operation_stats[op]['total_cost'] += query['estimated_cost']
            
            if query['cached']:
                operation_stats[op]['cached_calls'] += 1
            else:
                operation_stats[op]['api_calls'] += 1
        
        # Calcular percentuais
        for op in operation_stats:
            total = operation_stats[op]['total_calls']
            operation_stats[op]['cache_hit_rate'] = round(
                (operation_stats[op]['cached_calls'] / total * 100) if total > 0 else 0, 2
            )
        
        return operation_stats
    
    def get_optimization_recommendations(self) -> List[str]:
        """Obter recomendações de otimização"""
        recommendations = []
        daily_stats = self.get_daily_stats()
        
        # Verificar hit rate do cache
        if daily_stats['cache_hit_rate'] < 50:
            recommendations.append(
                "📈 Cache hit rate baixo (<50%). Considere aumentar o TTL do cache."
            )
        
        # Verificar custo diário
        if daily_stats['estimated_cost_usd'] > 1.0:
            recommendations.append(
                "💰 Custo diário alto (>$1). Revise intervalos de polling."
            )
        
        # Verificar operações mais custosas
        operation_breakdown = self.get_operation_breakdown()
        most_expensive = max(
            operation_breakdown.items(), 
            key=lambda x: x[1]['total_cost'],
            default=(None, {'total_cost': 0})
        )
        
        if most_expensive[1]['total_cost'] > 0.5:
            recommendations.append(
                f"🎯 Operação '{most_expensive[0]}' representa maior custo. "
                f"Considere otimizar sua frequência."
            )
        
        # Recomendações baseadas em tempo de uso
        uptime_hours = (time.time() - self.start_time) / 3600
        if uptime_hours > 24 and daily_stats['total_queries'] > 1000:
            recommendations.append(
                "⚡ Alto volume de consultas. Considere implementar cache distribuído."
            )
        
        if not recommendations:
            recommendations.append("✅ Sistema bem otimizado! Continue monitorando.")
        
        return recommendations
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Obter relatório completo"""
        return {
            'summary': {
                'uptime_hours': round((time.time() - self.start_time) / 3600, 2),
                'total_queries_logged': len(self.query_log),
                'overall_cache_hit_rate': round(
                    (self.cache_hits / (self.cache_hits + self.cache_misses) * 100) 
                    if (self.cache_hits + self.cache_misses) > 0 else 0, 2
                )
            },
            'hourly_stats': self.get_hourly_stats(),
            'daily_stats': self.get_daily_stats(),
            'operation_breakdown': self.get_operation_breakdown(),
            'recommendations': self.get_optimization_recommendations(),
            'generated_at': datetime.now().isoformat()
        }
    
    def cleanup_old_logs(self, days: int = 7):
        """Limpar logs antigos"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        initial_count = len(self.query_log)
        self.query_log = [
            q for q in self.query_log 
            if datetime.fromisoformat(q['timestamp']) > cutoff_date
        ]
        
        removed_count = initial_count - len(self.query_log)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old query logs")
    
    def export_stats(self, filepath: str):
        """Exportar estatísticas para arquivo"""
        try:
            report = self.get_comprehensive_report()
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Stats exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting stats: {e}")

# Instância global do monitor
cost_monitor = CloudWatchCostMonitor()

def log_cloudwatch_query(operation: str, cached: bool = False):
    """Função helper para registrar consultas"""
    estimated_cost = cost_monitor.estimate_operation_cost(operation)
    cost_monitor.log_query(operation, cached, estimated_cost)

if __name__ == "__main__":
    # Exemplo de uso
    print("CloudWatch Cost Monitor - Relatório de Exemplo")
    print("=" * 50)
    
    # Simular algumas consultas
    log_cloudwatch_query('describe_alarms', cached=False)
    log_cloudwatch_query('describe_alarms', cached=True)
    log_cloudwatch_query('get_metric_statistics', cached=False)
    
    report = cost_monitor.get_comprehensive_report()
    print(json.dumps(report, indent=2))
