"""
AWSNoc IA IA - Real CloudWatch Alarms Service
Serviço para descoberta e análise de alarmes reais
"""
from typing import List, Dict, Any, Optional

import asyncio
import json
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any
from datetime import datetime
from cloudwatch_alarms import CloudWatchAlarmsDiscovery
from ai.bedrock_analyzer import BedrockAnalyzer

class RealAlarmsService:
    """
    Serviço para gerenciar alarmes reais do CloudWatch
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.bedrock_analyzer = BedrockAnalyzer()
    
    def get_db_connection(self):
        """Obter conexão com banco"""
        return psycopg2.connect(**self.db_config)
    
    async def discover_alarms_for_account(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Descobrir alarmes para uma conta específica
        """
        try:
            # Buscar credenciais da conta
            account = self._get_account(account_id)
            if not account:
                return []
            
            # Criar descobridor de alarmes
            alarm_discovery = CloudWatchAlarmsDiscovery(
                access_key=account['access_key'],
                secret_key=account['secret_key'],
                region=account['region']
            )
            
            # Descobrir alarmes
            alarms = await alarm_discovery.discover_all_alarms()
            
            # Salvar alarmes no banco
            await self._save_alarms_to_db(account_id, alarms)
            
            return alarms
            
        except Exception as e:
            print(f"Erro descobrindo alarmes para conta {account_id}: {e}")
            return []
    
    async def discover_alarms_all_accounts(self) -> Dict[str, Any]:
        """
        Descobrir alarmes para todas as contas
        """
        try:
            accounts = self._get_all_accounts()
            total_alarms = 0
            
            for account in accounts:
                alarms = await self.discover_alarms_for_account(account['id'])
                total_alarms += len(alarms)
                print(f"Descobertos {len(alarms)} alarmes para conta {account['name']}")
            
            return {
                "status": "success",
                "accounts_processed": len(accounts),
                "total_alarms_discovered": total_alarms,
                "discovery_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "discovery_time": datetime.now().isoformat()
            }
    
    async def get_real_alarms(self, account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Buscar alarmes reais salvos no banco
        """
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if account_id:
                cur.execute("""
                    SELECT a.*, acc.name as account_name, acc.account_id as aws_account_id
                    FROM real_alarms a
                    JOIN accounts acc ON a.account_id = acc.id
                    WHERE a.account_id = %s
                    ORDER BY a.created_at DESC
                """, (account_id,))
            else:
                cur.execute("""
                    SELECT a.*, acc.name as account_name, acc.account_id as aws_account_id
                    FROM real_alarms a
                    JOIN accounts acc ON a.account_id = acc.id
                    ORDER BY a.created_at DESC
                """)
            
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
            
            return result
            
        except Exception as e:
            print(f"Erro buscando alarmes reais: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    async def get_real_alarms_with_ai_analysis(self, account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Buscar alarmes reais e executar análise de IA para os que estão em ALARM
        """
        alarms = await self.get_real_alarms(account_id)
        
        # Analisar alarmes em estado ALARM que não têm análise de IA
        for alarm in alarms:
            if (alarm['state_value'] == 'ALARM' and 
                (not alarm.get('ai_analysis') or alarm['ai_analysis'] == {})):
                
                # Executar análise de IA
                ai_analysis = await self._analyze_alarm_with_ai(alarm)
                alarm['ai_analysis'] = ai_analysis
                
                # Salvar análise no banco
                await self._update_alarm_ai_analysis(alarm['id'], ai_analysis)
        
        return alarms
    
    async def _analyze_alarm_with_ai(self, alarm: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisar alarme com IA Bedrock
        """
        try:
            # Criar um evento de log simulado para o analisador
            from collections import namedtuple
            
            LogEvent = namedtuple('LogEvent', [
                'timestamp', 'message', 'service_name', 'log_group', 
                'log_stream', 'account_id', 'region'
            ])
            
            # Construir mensagem contextual do alarme
            alarm_message = f"""
            CLOUDWATCH ALARM: {alarm['alarm_name']}
            Estado: {alarm['state_value']}
            Razão: {alarm['state_reason']}
            Namespace: {alarm['namespace']}
            Métrica: {alarm['metric_name']}
            Threshold: {alarm['threshold']}
            Recursos Afetados: {', '.join(alarm.get('affected_resources', []))}
            """
            
            log_event = LogEvent(
                timestamp=datetime.now(),
                message=alarm_message,
                service_name=alarm['namespace'],
                log_group=f"/aws/cloudwatch/alarm/{alarm['alarm_name']}",
                log_stream="alarm-stream",
                account_id=alarm['aws_account_id'],
                region=alarm['region']
            )
            
            # Executar análise
            analysis = await self.bedrock_analyzer.analyze_log(log_event)
            
            return analysis
            
        except Exception as e:
            print(f"Erro na análise de IA do alarme {alarm['alarm_name']}: {e}")
            return {
                "error": f"Erro na análise: {str(e)}",
                "analyzed_at": datetime.now().isoformat()
            }
    
    async def _save_alarms_to_db(self, account_id: int, alarms: List[Dict[str, Any]]):
        """
        Salvar alarmes descobertos no banco
        """
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Criar tabela se não existir
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
                    UNIQUE(account_id, alarm_arn)
                )
            """)
            
            # Inserir ou atualizar alarmes
            for alarm in alarms:
                cur.execute("""
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
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    account_id,
                    alarm['alarm_name'],
                    alarm['alarm_arn'],
                    alarm['alarm_type'],
                    alarm['state_value'],
                    alarm['state_reason'],
                    alarm['state_reason_data'],
                    alarm['severity'],
                    alarm['metric_name'],
                    alarm['namespace'],
                    json.dumps(alarm['dimensions']),
                    alarm['statistic'],
                    alarm['threshold'],
                    alarm['comparison_operator'],
                    alarm['evaluation_periods'],
                    alarm['period'],
                    alarm['description'],
                    alarm['actions_enabled'],
                    json.dumps(alarm['alarm_actions']),
                    json.dumps(alarm['ok_actions']),
                    json.dumps(alarm['insufficient_data_actions']),
                    alarm['state_updated_timestamp'],
                    alarm['configuration_updated_timestamp'],
                    json.dumps(alarm['affected_resources']),
                    json.dumps(alarm['history']),
                    json.dumps(alarm['metric_data']),
                    alarm['region'],
                    json.dumps(alarm['tags'])
                ))
            
            conn.commit()
            print(f"Salvos {len(alarms)} alarmes para conta {account_id}")
            
        except Exception as e:
            print(f"Erro salvando alarmes no banco: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()
    
    async def _update_alarm_ai_analysis(self, alarm_id: int, ai_analysis: Dict[str, Any]):
        """
        Atualizar análise de IA do alarme
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
        """
        Buscar dados de uma conta específica
        """
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
        """
        Buscar todas as contas ativas
        """
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
