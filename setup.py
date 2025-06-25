#!/usr/bin/env python3
"""
SelectNOC IA - Setup Script
Script de configuração inicial do projeto
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path

def create_directory_structure():
    """Cria estrutura de diretórios necessária"""
    directories = [
        "logs",
        "data",
        "temp",
        "templates",
        "static",
        "docs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Diretório {directory} criado")

def create_environment_file():
    """Cria arquivo .env de exemplo"""
    env_content = """# SelectNOC IA Environment Variables

# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE=default

# Bedrock Configuration
BEDROCK_REGION=us-east-1

# API Keys (opcionais - fallback)
# ANTHROPIC_API_KEY=your_anthropic_key_here
# OPENAI_API_KEY=your_openai_key_here

# Database
DATABASE_URL=postgresql://selectnoc:password@localhost:5432/selectnoc_ia
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
ENCRYPTION_KEY=your-encryption-key-for-sensitive-data

# Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
PAGERDUTY_ROUTING_KEY=your_pagerduty_routing_key

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Application
DEBUG=false
LOG_LEVEL=INFO
"""
    
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write(env_content)
        print("✓ Arquivo .env criado")
    else:
        print("⚠ Arquivo .env já existe")

def install_dependencies():
    """Instala dependências Python"""
    print("Instalando dependências...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✓ Dependências instaladas com sucesso")
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao instalar dependências: {e}")
        print(f"Saída do erro: {e.stderr}")
        return False
    return True

def create_sample_config():
    """Cria configuração de exemplo para desenvolvimento"""
    sample_config = {
        "aws_ai_stack": {
            "strategy": "aws_native_first",
            "bedrock": {
                "region_primary": "us-east-1",
                "models": {
                    "log_analysis_primary": {
                        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                        "temperature": 0.1,
                        "max_tokens": 4000
                    },
                    "log_classification": {
                        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
                        "temperature": 0.05,
                        "max_tokens": 1000
                    }
                }
            }
        },
        "ai_pipeline": {
            "architecture": "event_driven",
            "real_time_analysis": {
                "trigger": "cloudwatch_log_stream"
            }
        }
    }
    
    config_file = "config/dev_config.yaml"
    os.makedirs("config", exist_ok=True)
    
    with open(config_file, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    print(f"✓ Configuração de desenvolvimento criada: {config_file}")

def check_aws_credentials():
    """Verifica se as credenciais AWS estão configuradas"""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS configurado - Account: {identity['Account']}")
        return True
    except Exception as e:
        print(f"⚠ AWS não configurado: {e}")
        print("Execute: aws configure")
        return False

def create_systemd_service():
    """Cria arquivo de serviço systemd"""
    current_dir = Path.cwd()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=SelectNOC IA - Intelligent AWS Log Analysis
After=network.target

[Service]
Type=simple
User=selectnoc
WorkingDirectory={current_dir}
Environment=PATH={current_dir}/venv/bin
ExecStart={python_path} main.py --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "selectnoc-ia.service"
    with open(service_file, "w") as f:
        f.write(service_content)
    
    print(f"✓ Arquivo de serviço criado: {service_file}")
    print("Para instalar: sudo cp selectnoc-ia.service /etc/systemd/system/")

def create_nginx_config():
    """Cria configuração nginx de exemplo"""
    nginx_config = """server {
    listen 80;
    server_name selectnoc.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name selectnoc.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files (if any)
    location /static/ {
        alias /path/to/selectnoc/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
    
    with open("nginx-selectnoc.conf", "w") as f:
        f.write(nginx_config)
    
    print("✓ Configuração nginx criada: nginx-selectnoc.conf")

def run_tests():
    """Executa testes básicos"""
    print("Executando testes básicos...")
    
    try:
        # Teste de importação
        import collectors.aws_collector
        import ai.bedrock_analyzer
        import api.routes
        print("✓ Importações funcionando")
        
        # Teste de configuração
        with open("config/aws_ai_config.yaml", "r") as f:
            config = yaml.safe_load(f)
        print("✓ Configuração YAML válida")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro nos testes: {e}")
        return False

def main():
    """Função principal do setup"""
    print("🚀 SelectNOC IA - Setup Inicial")
    print("=" * 50)
    
    # Verificar Python
    if sys.version_info < (3, 11):
        print("✗ Python 3.11+ é necessário")
        sys.exit(1)
    print(f"✓ Python {sys.version}")
    
    # Criar estrutura
    create_directory_structure()
    
    # Instalar dependências
    if not install_dependencies():
        print("✗ Falha na instalação das dependências")
        sys.exit(1)
    
    # Configurações
    create_environment_file()
    create_sample_config()
    
    # Arquivos de deployment
    create_systemd_service()
    create_nginx_config()
    
    # Verificações
    aws_ok = check_aws_credentials()
    tests_ok = run_tests()
    
    print("\n" + "=" * 50)
    print("📋 RESUMO DO SETUP")
    print("=" * 50)
    
    if aws_ok and tests_ok:
        print("✅ Setup concluído com sucesso!")
        print("\n📝 PRÓXIMOS PASSOS:")
        print("1. Configure o arquivo .env com suas credenciais")
        print("2. Ajuste config/aws_ai_config.yaml para sua conta AWS")
        print("3. Execute: python main.py")
        print("4. Acesse: http://localhost:8000/docs")
        print("\n🔧 Para produção:")
        print("- Configure SSL/HTTPS")
        print("- Configure banco PostgreSQL")
        print("- Configure Redis")
        print("- Configure monitoramento")
    else:
        print("⚠️ Setup concluído com avisos")
        print("Verifique as configurações antes de executar")
    
    print(f"\n📁 Projeto instalado em: {Path.cwd()}")

if __name__ == "__main__":
    main()

