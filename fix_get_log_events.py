#!/usr/bin/env python3
"""
Script para corrigir as chamadas get_log_events problemáticas
"""

def fix_get_log_events():
    """Corrigir as chamadas get_log_events sem logStreamName"""
    
    file_path = '/opt/selectnoc/simple_main.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar e substituir a chamada problemática
    old_pattern = '''                            log_events = logs.get_log_events(
                                logGroupName=log_group_name,
                                startTime=start_time,
                                endTime=end_time,
                                limit=100
                            )'''
    
    new_pattern = '''                            # Primeiro listar streams disponíveis
                            try:
                                streams_response = logs.describe_log_streams(
                                    logGroupName=log_group_name,
                                    orderBy="LastEventTime",
                                    descending=True,
                                    limit=5
                                )
                                
                                # Buscar logs dos streams mais recentes
                                log_events = {"events": []}
                                for stream in streams_response.get("logStreams", [])[:3]:  # Máximo 3 streams
                                    try:
                                        stream_events = logs.get_log_events(
                                            logGroupName=log_group_name,
                                            logStreamName=stream["logStreamName"],
                                            startTime=start_time,
                                            endTime=end_time,
                                            limit=50
                                        )
                                        log_events["events"].extend(stream_events["events"])
                                    except Exception as e:
                                        print(f"Erro ao buscar logs do stream {stream.get('logStreamName', 'unknown')}: {e}")
                                        continue
                            except Exception as e:
                                print(f"Erro ao listar log streams para {log_group_name}: {e}")
                                log_events = {"events": []}'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print('✅ Correção aplicada com sucesso!')
        return True
    else:
        print('❌ Padrão não encontrado!')
        return False

if __name__ == '__main__':
    fix_get_log_events()
