#!/usr/bin/env python3
"""
Adicionar análise de instâncias EC2 via SSM na análise de Target Group
"""

def enhance_target_group_ec2_analysis():
    """Adicionar descoberta e análise de instâncias EC2 via SSM"""
    
    file_path = '/opt/awsnoc-ia/simple_main.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar onde adicionar a análise EC2 (após a descoberta ECS)
    insertion_point = '''        except Exception as e:
            print(f"Erro ao descobrir serviços ECS: {e}")'''
    
    ec2_analysis_code = '''        except Exception as e:
            print(f"Erro ao descobrir serviços ECS: {e}")
        
        # 3.5. DESCOBRIR E ANALISAR INSTÂNCIAS EC2 NO TARGET GROUP
        ec2 = session.client('ec2')
        ssm = session.client('ssm')
        ec2_instances = []
        
        try:
            # Verificar se há targets EC2 no Target Group
            for target_health in targets_health['TargetHealthDescriptions']:
                target = target_health['Target']
                
                # Se o target é uma instância EC2 (não um IP)
                if target['Id'].startswith('i-'):
                    instance_id = target['Id']
                    
                    # Buscar detalhes da instância
                    ec2_response = ec2.describe_instances(InstanceIds=[instance_id])
                    instance = ec2_response['Reservations'][0]['Instances'][0]
                    
                    # Preparar dados da instância
                    instance_data = {
                        'instance_id': instance_id,
                        'state': instance['State']['Name'],
                        'private_ip': instance.get('PrivateIpAddress'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'instance_type': instance['InstanceType'],
                        'target_health': target_health['TargetHealth']['State'],
                        'health_description': target_health['TargetHealth'].get('Description', ''),
                        'application_logs': [],
                        'system_status': {}
                    }
                    
                    # CONECTAR VIA SSM E CAPTURAR DADOS
                    try:
                        # Verificar se a instância está disponível para SSM
                        ssm_instances = ssm.describe_instance_information(
                            Filters=[{'Key': 'InstanceIds', 'Values': [instance_id]}]
                        )
                        
                        if ssm_instances['InstanceInformationList']:
                            print(f"🔗 Conectando na instância {instance_id} via SSM...")
                            
                            # 1. Verificar serviço na porta do Target Group
                            port_check_command = ssm.send_command(
                                InstanceIds=[instance_id],
                                DocumentName="AWS-RunShellScript",
                                Parameters={
                                    'commands': [
                                        f'sudo netstat -tulpn | grep :{target["Port"]}',
                                        f'curl -s -m 5 http://localhost:{target["Port"]}/health || echo "Health endpoint failed"',
                                        'ps aux | grep -E "(node|python|java|nginx)" | grep -v grep',
                                        'systemctl status nginx || systemctl status apache2 || echo "No web server"',
                                        'df -h /',
                                        'free -m',
                                        'uptime'
                                    ]
                                }
                            )
                            
                            # Aguardar comando e buscar resultado
                            command_id = port_check_command['Command']['CommandId']
                            import time
                            time.sleep(3)
                            
                            command_result = ssm.get_command_invocation(
                                CommandId=command_id,
                                InstanceId=instance_id
                            )
                            
                            if command_result['Status'] == 'Success':
                                system_output = command_result['StandardOutput']
                                instance_data['system_status'] = {
                                    'port_check': system_output,
                                    'command_success': True
                                }
                            else:
                                instance_data['system_status'] = {
                                    'error': command_result.get('StandardErrorContent', 'Unknown error'),
                                    'command_success': False
                                }
                            
                            # 2. Capturar logs da aplicação (tentar várias localizações comuns)
                            logs_command = ssm.send_command(
                                InstanceIds=[instance_id],
                                DocumentName="AWS-RunShellScript",
                                Parameters={
                                    'commands': [
                                        'sudo tail -n 50 /var/log/application.log 2>/dev/null || echo "No application.log"',
                                        'sudo tail -n 50 /var/log/nginx/error.log 2>/dev/null || echo "No nginx error.log"',
                                        'sudo tail -n 50 /var/log/apache2/error.log 2>/dev/null || echo "No apache error.log"',
                                        'sudo journalctl -u nginx -n 20 --no-pager 2>/dev/null || echo "No nginx service logs"',
                                        'sudo find /var/log -name "*.log" -mtime -1 -exec tail -n 10 {} \\; 2>/dev/null | head -n 100',
                                        'sudo dmesg | tail -n 20'
                                    ]
                                }
                            )
                            
                            # Aguardar e buscar logs
                            logs_command_id = logs_command['Command']['CommandId']
                            time.sleep(3)
                            
                            logs_result = ssm.get_command_invocation(
                                CommandId=logs_command_id,
                                InstanceId=instance_id
                            )
                            
                            if logs_result['Status'] == 'Success':
                                logs_output = logs_result['StandardOutput']
                                # Dividir em linhas e filtrar logs relevantes
                                log_lines = logs_output.split('\\n')
                                relevant_logs = [line for line in log_lines if line.strip() and 
                                               any(keyword in line.lower() for keyword in ['error', 'fail', 'exception', 'warn', 'critical'])]
                                
                                instance_data['application_logs'] = relevant_logs[:20]  # Top 20 logs de erro
                            else:
                                instance_data['application_logs'] = [f"Erro ao capturar logs: {logs_result.get('StandardErrorContent', 'Unknown')}"]
                        
                        else:
                            instance_data['system_status'] = {'error': 'Instância não disponível via SSM'}
                            
                    except Exception as ssm_error:
                        print(f"Erro SSM na instância {instance_id}: {ssm_error}")
                        instance_data['system_status'] = {'error': f'Erro SSM: {str(ssm_error)}'}
                    
                    ec2_instances.append(instance_data)
                    
        except Exception as e:
            print(f"Erro ao descobrir instâncias EC2: {e}")'''
    
    # Substituir o código
    content = content.replace(insertion_point, ec2_analysis_code)
    
    # Atualizar o contexto da IA para incluir dados EC2
    old_ai_context = '''        SERVIÇOS ECS DESCOBERTOS:
        {json.dumps(ecs_services, indent=2)}
        
        ANÁLISE DOS TARGETS:
        {json.dumps(target_analysis, indent=2)}'''
    
    new_ai_context = '''        SERVIÇOS ECS DESCOBERTOS:
        {json.dumps(ecs_services, indent=2)}
        
        INSTÂNCIAS EC2 DESCOBERTAS:
        {json.dumps(ec2_instances, indent=2)}
        
        ANÁLISE DOS TARGETS:
        {json.dumps(target_analysis, indent=2)}'''
    
    content = content.replace(old_ai_context, new_ai_context)
    
    # Atualizar o prompt da IA
    old_prompt = '''        INSTRUÇÕES ESPECÍFICAS:
        - Se houver serviços ECS associados, analise as falhas das tasks e logs dos containers
        - Conecte os problemas do Target Group com as falhas dos containers ECS
        - Cite os logs específicos que mostram a causa raiz
        - Priorize a correção dos problemas ECS antes do Target Group'''
    
    new_prompt = '''        INSTRUÇÕES ESPECÍFICAS:
        - Se houver SERVIÇOS ECS: analise as falhas das tasks e logs dos containers
        - Se houver INSTÂNCIAS EC2: analise os logs via SSM, status da aplicação e conectividade
        - PRIORIZE a análise do tipo de recurso descoberto (ECS ou EC2)
        - Conecte os problemas do Target Group com as falhas do recurso subjacente
        - Cite os logs específicos que mostram a causa raiz
        - Para EC2: foque na aplicação rodando na porta, logs do sistema e conectividade'''
    
    content = content.replace(old_prompt, new_prompt)
    
    # Atualizar estrutura de retorno
    old_return_struct = '''            "associated_ecs_services": ecs_services,
            "targets_analysis": target_analysis,'''
    
    new_return_struct = '''            "associated_ecs_services": ecs_services,
            "associated_ec2_instances": ec2_instances,
            "targets_analysis": target_analysis,'''
    
    content = content.replace(old_return_struct, new_return_struct)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ Análise EC2 via SSM adicionada ao Target Group!')
    return True

if __name__ == '__main__':
    enhance_target_group_ec2_analysis()
