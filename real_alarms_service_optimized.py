"""
SelectNOC IA - Real CloudWatch Alarms Service - Versão Otimizada
Serviço otimizado para descoberta e análise de alarmes reais com controle de custos
"""
from typing import List, Dict, Any, Optional
import asyncio
import json
import psycopg2
import psycopg2.extras
import time
from datetime import datetime

# Importar versão otimizada
try:
    from cloudwatch_alarms_optimized import OptimizedCloudWatchAlarmsDiscovery
    from config.cloudwatch_config import CloudWatchConfig
    from services.cloudwatch_cache import cache_manager
except ImportError:
    # Fallback para versão original
    from cloudwatch_alarms import CloudWatchAlarmsDiscovery as OptimizedCloudWatchAlarmsDiscovery
    
    class CloudWatchConfig:
        @classmethod
        def get_polling_interval(cls, component): return 30
        @classmethod
        def get_cache_ttl(cls, component): return 25

from ai.bedrock_analyzer import BedrockAnalyzer

class OptimizedRealAlarmsService:
    """
    Serviço otimizado para gerenciar alarmes reais do CloudWatch
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.bedrock_analyzer = BedrockAnalyzer()
        self.last_discovery_time = {}  # Track por conta
        self.polling_intervals = CloudWatchConfig.POLLING_INTERVALS if hasattr(CloudWatchConfig, 'POLLING_INTERVALS') else {'alarms': 30}
    
    def get_db_connection(self):
        """Obter conexão com banco"""
        return psycopg2.connect(**self.db_config)
    
    async def discover_alarms_for_account(self, account_id: int, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Descobrir alarmes para uma conta específica com controle de polling
        """
        try:
            current_time = time.time()
            last_check = self.last_discovery_time.get(account_id, 0)
            polling_interval = self.polling_intervals.get('alarms', 30)
            
            # Verificar se precisa fazer nova descoberta
            if not force_refresh and (current_time - last_check) < polling_interval:
                print(f"Polling interval não atingido para conta {account_id}, usando cache")
                return await self._get_cached_alarms_from_db(account_id)
            
            # Buscar credenciais da conta
            account = self._get_account(account_id)
            if not account:
                print(f"Conta {account_id} não encontrada")
                return []
            
            # Criar descobridor otimizado de alarmes
            alarm_discovery = OptimizedCloudWatchAlarmsDiscovery(
                access_key=account['access_key'],
                secret_key=account['secret_key'],
                region=account['region']
            )
            
            # Descobrir alarmes com otimizações
            print(f"Iniciando descoberta otimizada para conta {account_id} ({account['name']})")
            alarms = await alarm_discovery.discover_all_alarms(force_refresh=force_refresh)
            
            # Salvar alarmes no banco apenas se houver alterações
            if alarms:
                await self._save_alarms_to_db_optimized(account_id, alarms)
                self.last_discovery_time[account_id] = current_time
                print(f"Descobertos e salvos {len(alarms)} alarmes para conta {account['name']}")
            else:
                print(f"Nenhum alarme encontrado para conta {account['name']}")
            
            # Limpar cache periodicamente
            if hasattr(alarm_discovery, 'cleanup_cache'):
                alarm_discovery.cleanup_cache()
            
            return alarms
            
        except Exception as e:
            print(f"Erro descobrindo alarmes para conta {account_id}: {e}")
            return []
    
    async def _get_cached_alarms_from_db(self, account_id: int) -> List[Dict[str, Any]]:
        """Buscar alarmes do cache no banco de dados"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Buscar alarmes recentes (últimos 2 minutos)
            cur.execute("""
                SELECT * FROM real_alarms 
                WHERE account_id = %s 
                AND updated_at > NOW() - INTERVAL '2 minutes'
                ORDER BY updated_at DESC
            """, (account_id,))
            
            alarms = cur.fetchall()
            
            if alarms:
                result = []
                for alarm in alarms:
                    alarm_dict = dict(alarm)
                    # Converter JSON strings
                    for field in ['dimensions', 'affected_resources', 'history', 'metric_data', 'tags']:
                        if alarm_dict.get(field):
                            try:
                                alarm_dict[field] = json.loads(alarm_dict[field])
                            except:
                                pass
                    result.append(alarm_dict)
                
                print(f"Retornando {len(result)} alarmes do cache para conta {account_id}")
                return result
            
            return []
            
        except Exception as e:
            print(f"Erro buscando alarmes do cache: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    async def discover_alarms_all_accounts(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Descobrir alarmes para todas as contas com controle de polling
        """
        try:
            accounts = self._get_all_accounts()
            total_alarms = 0
            processed_accounts = 0
            
            # Processar contas em lotes para evitar sobrecarga
            batch_size = 3
            for i in range(0, len(accounts), batch_size):
                batch = accounts[i:i + batch_size]
                
                # Processar lote de contas em paralelo
                tasks = []
                for account in batch:
                    task = self.discover_alarms_for_account(account['id'], force_refresh)
                    tasks.append(task)
                
                # Aguardar conclusão do lote
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    if isinstance(result, list):
                        total_alarms += len(result)
                        processed_accounts += 1
                        account_name = batch[j]['name']
                        print(f"✅ Conta {account_name}: {len(result)} alarmes")
                    else:
                        account_name = batch[j]['name']
                        print(f"❌ Erro na conta {account_name}: {result}")
                
                # Pausa entre lotes para não sobrecarregar
                if i + batch_size < len(accounts):
                    await asyncio.sleep(2)
            
            return {
                "status": "success",
                "accounts_processed": processed_accounts,
                "total_accounts": len(accounts),
                "total_alarms_discovered": total_alarms,
                "discovery_time": datetime.now().isoformat(),
                "polling_optimized": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "discovery_time": datetime.now().isoformat()
            }
    
    async def get_real_alarms(self, account_id: Optional[int] = None, 
                            include_ok_alarms: bool = False) -> List[Dict[str, Any]]:
        """
        Buscar alarmes reais com filtros de otimização
        """
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Query otimizada - priorizar alarmes ativos
            base_query = """
                SELECT a.*, acc.name as account_name, acc.account_id as aws_account_id
                FROM real_alarms a
                JOIN accounts acc ON a.account_id = acc.id
            """
            
            conditions = []
            params = []
            
            if account_id:
                conditions.append("a.account_id = %s")
                params.append(account_id)
            
            # Filtro para reduzir dados desnecessários
            if not include_ok_alarms:
                conditions.append("a.state_value != 'OK'")
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            # Ordenar por prioridade: ALARM primeiro, depois por timestamp
            base_query += """
                ORDER BY 
                    CASE a.state_value 
                        WHEN 'ALARM' THEN 1 
                        WHEN 'INSUFFICIENT_DATA' THEN 2 
                        WHEN 'OK' THEN 3 
                    END,
                    a.state_updated_timestamp DESC
                LIMIT 500
            """
            
            cur.execute(base_query, params)
            alarms = cur.fetchall()
            
            # Converter para lista de dicionários
            result = []
            for alarm in alarms:
                alarm_dict = dict(alarm)
                # Converter JSON strings de volta para objetos
                for field in ['dimensions', 'affected_resources', 'history', 'metric_data', 'tags', 'ai_analysis']:
                    if alarm_dict.get(field):
                        try:
                            alarm_dict[field] = json.loads(alarm_dict[field])
                        except:
                            pass
                result.append(alarm_dict)
            
            print(f"Retornando {len(result)} alarmes {'para conta ' + str(account_id) if account_id else 'total'}")
            return result
            
        except Exception as e:
            print(f"Erro buscando alarmes reais: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    async def get_real_alarms_with_ai_analysis(self, account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Buscar alarmes reais e executar análise de IA otimizada
        """
        alarms = await self.get_real_alarms(account_id, include_ok_alarms=False)
        
        # Analisar apenas alarmes críticos sem análise de IA
        critical_alarms = [
            alarm for alarm in alarms 
            if (alarm['state_value'] == 'ALARM' and 
                alarm['severity'] in ['CRITICAL', 'HIGH'] and
                (not alarm.get('ai_analysis') or alarm['ai_analysis'] == {}))
        ]
        
        print(f"Analisando {len(critical_alarms)} alarmes críticos com IA")
        
        # Processar análises em lotes menores
        batch_size = 5
        for i in range(0, len(critical_alarms), batch_size):
            batch = critical_alarms[i:i + batch_size]
            
            # Executar análises em paralelo
            analysis_tasks = []
            for alarm in batch:
                task = self._analyze_alarm_with_ai(alarm)
                analysis_tasks.append(task)
            
            batch_analyses = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Atualizar alarmes com análises
            for j, analysis in enumerate(batch_analyses):
                if not isinstance(analysis, Exception):
                    alarm = batch[j]
                    alarm['ai_analysis'] = analysis
                    
                    # Salvar análise no banco de forma assíncrona
                    await self._update_alarm_ai_analysis(alarm['id'], analysis)
            
            # Pequena pausa entre lotes
            if i + batch_size < len(critical_alarms):
                await asyncio.sleep(1)
        
        return alarms
    
    async def _save_alarms_to_db_optimized(self, account_id: int, alarms: List[Dict[str, Any]]):
        """
        Salvar alarmes no banco de forma otimizada
        """
        if not alarms:
            return
        
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Criar tabela se não existir (apenas uma vez)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS real_alarms (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER REFERENCES accounts(id),
                    alarm_name VARCHAR(255) NOT NULL,
                    alarm_arn TEXT,
                    alarm_type VARCHAR(50),
                    state_value VARCHAR(50),
                    state_reason TEXT,
                    state_reason_data TEXT,
                    severity VARCHAR(20),
                    metric_name VARCHAR(255),
                    namespace VARCHAR(255),
                    dimensions TEXT,
                    statistic VARCHAR(50),
                    threshold DECIMAL,
                    comparison_operator VARCHAR(50),
                    evaluation_periods INTEGER,
                    period INTEGER,
                    description TEXT,
                    actions_enabled BOOLEAN,
                    alarm_actions TEXT,
                    ok_actions TEXT,
                    insufficient_data_actions TEXT,
                    state_updated_timestamp TIMESTAMP,
                    configuration_updated_timestamp TIMESTAMP,
                    affected_resources TEXT,
                    history TEXT,
                    metric_data TEXT,
                    region VARCHAR(50),
                    tags TEXT,
                    ai_analysis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(account_id, alarm_arn)
                )
            """)
            
            # Preparar dados para inserção em lote
            insert_data = []
            for alarm in alarms:
                insert_data.append((
                    account_id, alarm['alarm_name'], alarm['alarm_arn'], alarm['alarm_type'],
                    alarm['state_value'], alarm['state_reason'], alarm['state_reason_data'],
                    alarm['severity'], alarm['metric_name'], alarm['namespace'],
                    json.dumps(alarm['dimensions']), alarm['statistic'], alarm['threshold'],
                    alarm['comparison_operator'], alarm['evaluation_periods'], alarm['period'],
                    alarm['description'], alarm['actions_enabled'], 
                    json.dumps(alarm['alarm_actions']), json.dumps(alarm['ok_actions']),
                    json.dumps(alarm['insufficient_data_actions']),
                    alarm['state_updated_timestamp'], alarm['configuration_updated_timestamp'],
                    json.dumps(alarm['affected_resources']), json.dumps(alarm['history']),
                    json.dumps(alarm['metric_data']), alarm['region'], json.dumps(alarm['tags'])
                ))
            
            # Inserção em lote otimizada
            insert_query = """
                INSERT INTO real_alarms (
                    account_id, alarm_name, alarm_arn, alarm_type, state_value,
                    state_reason, state_reason_data, severity, metric_name, namespace,
                    dimensions, statistic, threshold, comparison_operator, evaluation_periods,
                    period, description, actions_enabled, alarm_actions, ok_actions,
                    insufficient_data_actions, state_updated_timestamp, 
                    configuration_updated_timestamp, affected_resources, history,
                    metric_data, region, tags
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (account_id, alarm_arn)
                DO UPDATE SET
                    state_value = EXCLUDED.state_value,
                    state_reason = EXCLUDED.state_reason,
                    state_reason_data = EXCLUDED.state_reason_data,
                    severity = EXCLUDED.severity,
                    state_updated_timestamp = EXCLUDED.state_updated_timestamp,
                    updated_at = CURRENT_TIMESTAMP,
                    last_checked = CURRENT_TIMESTAMP
            """
            
            # Executar inserção em lote
            cur.executemany(insert_query, insert_data)
            conn.commit()
            
            print(f"✅ Salvos {len(alarms)} alarmes para conta {account_id} (lote otimizado)")
            
        except Exception as e:
            print(f"❌ Erro salvando alarmes no banco: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()
    
    async def _analyze_alarm_with_ai(self, alarm: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisar alarme com IA Bedrock (versão otimizada)
        """
        try:
            from collections import namedtuple
            
            LogEvent = namedtuple('LogEvent', [
                'timestamp', 'message', 'service_name', 'log_group', 
                'log_stream', 'account_id', 'region'
            ])
            
            # Construir mensagem contextual mais concisa
            alarm_message = f"""
ALARM: {alarm['alarm_name']} | {alarm['state_value']} | {alarm['severity']}
Métrica: {alarm['namespace']}/{alarm['metric_name']}
Threshold: {alarm['threshold']} | Razão: {alarm['state_reason']}
Recursos: {', '.join(alarm.get('affected_resources', [])[:3])}
"""
            
            log_event = LogEvent(
                timestamp=datetime.now(),
                message=alarm_message,
                service_name=alarm['namespace'],
                log_group=f"/aws/cloudwatch/alarm/{alarm['alarm_name']}",
                log_stream="alarm-stream",
                account_id=alarm.get('aws_account_id', ''),
                region=alarm['region']
            )
            
            # Executar análise com timeout
            analysis = await asyncio.wait_for(
                self.bedrock_analyzer.analyze_log(log_event),
                timeout=30  # 30 segundos de timeout
            )
            
            return analysis
            
        except asyncio.TimeoutError:
            print(f"⏱️ Timeout na análise de IA do alarme {alarm['alarm_name']}")
            return {
                "error": "Timeout na análise",
                "analyzed_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Erro na análise de IA do alarme {alarm['alarm_name']}: {e}")
            return {
                "error": f"Erro na análise: {str(e)}",
                "analyzed_at": datetime.now().isoformat()
            }
    
    async def _update_alarm_ai_analysis(self, alarm_id: int, ai_analysis: Dict[str, Any]):
        """
        Atualizar análise de IA do alarme de forma assíncrona
        """
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE real_alarms 
                SET ai_analysis = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(ai_analysis), alarm_id))
            
            conn.commit()
            
        except Exception as e:
            print(f"Erro atualizando análise de IA: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Buscar dados de uma conta específica"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute("SELECT * FROM accounts WHERE id = %s", (account_id,))
            account = cur.fetchone()
            
            return dict(account) if account else None
            
        except Exception as e:
            print(f"Erro buscando conta {account_id}: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _get_all_accounts(self) -> List[Dict[str, Any]]:
        """Buscar todas as contas ativas"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute("SELECT * FROM accounts WHERE status = 'active'")
            accounts = cur.fetchall()
            
            return [dict(account) for account in accounts]
            
        except Exception as e:
            print(f"Erro buscando contas: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do serviço"""
        return {
            "last_discovery_times": self.last_discovery_time,
            "polling_intervals": self.polling_intervals,
            "cache_stats": getattr(cache_manager, 'get_stats', lambda: {})(),
            "service_version": "optimized_v1.0"
        }

# Alias para compatibilidade
RealAlarmsService = OptimizedRealAlarmsService
