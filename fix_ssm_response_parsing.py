#!/usr/bin/env python3
"""
Corrigir parsing da resposta SSM
"""

def fix_ssm_response_parsing():
    """Corrigir o erro de parsing da resposta SSM"""
    
    file_path = '/opt/awsnoc-ia/simple_main.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir o parsing da resposta SSM
    old_parsing = '''                            if command_result['Status'] == 'Success':
                                system_output = command_result['StandardOutput']
                                instance_data['system_status'] = {
                                    'port_check': system_output,
                                    'command_success': True
                                }
                            else:
                                instance_data['system_status'] = {
                                    'error': command_result.get('StandardErrorContent', 'Unknown error'),
                                    'command_success': False
                                }'''
    
    new_parsing = '''                            if command_result.get('Status') == 'Success':
                                system_output = command_result.get('StandardOutput', 'No output')
                                error_output = command_result.get('StandardErrorContent', '')
                                instance_data['system_status'] = {
                                    'port_check': system_output,
                                    'error_output': error_output,
                                    'command_success': True,
                                    'ssm_status': 'success'
                                }
                            else:
                                instance_data['system_status'] = {
                                    'error': command_result.get('StandardErrorContent', 'Command failed'),
                                    'status': command_result.get('Status', 'Unknown'),
                                    'command_success': False,
                                    'ssm_status': 'failed'
                                }'''
    
    content = content.replace(old_parsing, new_parsing)
    
    # Corrigir também o parsing dos logs
    old_logs_parsing = '''                            if logs_result['Status'] == 'Success':
                                logs_output = logs_result['StandardOutput']
                                # Dividir em linhas e filtrar logs relevantes
                                log_lines = logs_output.split('\\n')
                                relevant_logs = [line for line in log_lines if line.strip() and 
                                               any(keyword in line.lower() for keyword in ['error', 'fail', 'exception', 'warn', 'critical'])]
                                
                                instance_data['application_logs'] = relevant_logs[:20]  # Top 20 logs de erro
                            else:
                                instance_data['application_logs'] = [f"Erro ao capturar logs: {logs_result.get('StandardErrorContent', 'Unknown')}"]'''
    
    new_logs_parsing = '''                            if logs_result.get('Status') == 'Success':
                                logs_output = logs_result.get('StandardOutput', '')
                                # Dividir em linhas e filtrar logs relevantes
                                log_lines = logs_output.split('\\n')
                                
                                # Filtrar logs de erro e informativos
                                error_logs = [line for line in log_lines if line.strip() and 
                                            any(keyword in line.lower() for keyword in ['error', 'fail', 'exception', 'critical'])]
                                
                                # Se não há logs de erro, pegar logs gerais
                                if not error_logs:
                                    general_logs = [line for line in log_lines if line.strip() and len(line) > 10][:10]
                                    instance_data['application_logs'] = general_logs
                                else:
                                    instance_data['application_logs'] = error_logs[:15]
                                
                                # Adicionar resumo dos logs
                                instance_data['logs_summary'] = {
                                    'total_lines': len(log_lines),
                                    'error_lines': len(error_logs),
                                    'logs_captured': len(instance_data['application_logs'])
                                }
                            else:
                                instance_data['application_logs'] = [f"Erro ao capturar logs: {logs_result.get('StandardErrorContent', 'Command failed')}"]
                                instance_data['logs_summary'] = {'error': True}'''
    
    content = content.replace(old_logs_parsing, new_logs_parsing)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ Parsing da resposta SSM corrigido!')
    return True

if __name__ == '__main__':
    fix_ssm_response_parsing()
