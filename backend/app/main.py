import os
#!/usr/bin/env python3
"""
AWSNoc IA IA - Versão Simples e Funcional
Sistema SaaS básico para monitoramento AWS
"""

import json
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

# Configuração do banco
DB_CONFIG = {
    "host": "awsnoc-ia-dev-database.cjeqe6pc2viw.us-east-2.rds.amazonaws.com",
    "port": 5432,
    "database": "awsnoc-ia",
    "user": "awsnoc-ia_admin", 
    "password": "Dy6uGR1UVasJEp7D"
}

app = FastAPI(
    title="AWSNoc IA IA",
    description="AI-Powered AWS Monitoring SaaS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class AWSAccount(BaseModel):
    id: Optional[int] = None
    name: str
    account_id: str
    region: str
    access_key: str
    secret_key: str
    services: List[str] = []
    status: str = "active"

def get_db_connection():
    """Conecta ao banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None

def safe_json_loads(value):
    """Safely parse JSON, handling both strings and lists"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value) if value.strip() else []
        except:
            return []
    return []

@app.get("/")
async def root():
    return {
        "message": "AWSNoc IA IA - Sistema de Monitoramento AWS",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "AWSNoc IA IA"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard principal"""
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AWSNoc IA IA - Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; min-height: 100vh; padding: 2rem;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 2rem; padding: 2rem;
                background: rgba(255,255,255,0.1); border-radius: 15px; backdrop-filter: blur(10px);
            }
            .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
            .card { background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 15px;
                backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);
            }
            .card h3 { margin-bottom: 1rem; font-size: 1.3rem; }
            .status { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 20px;
                font-size: 0.8rem; font-weight: bold; margin-left: 0.5rem;
            }
            .status.active { background: #10b981; }
            .status.inactive { background: #ef4444; }
            .btn { display: inline-block; padding: 0.5rem 1rem; background: #3b82f6;
                color: white; text-decoration: none; border-radius: 8px; margin: 0.25rem;
                border: none; cursor: pointer;
            }
            .btn:hover { background: #2563eb; }
            #accounts-list, #resources-list, #alerts-list { min-height: 100px; }
            .loading { text-align: center; opacity: 0.7; }
            .error { color: #ef4444; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 AWSNoc IA IA</h1>
                <p>Sistema de Monitoramento Inteligente AWS</p>
                <p class="loading" id="status">Carregando...</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📊 Contas AWS</h3>
                    <div id="accounts-list" class="loading">Carregando contas...</div>
                    <button class="btn" onclick="loadAccounts()">🔄 Recarregar</button>
                </div>
                
                <div class="card">
                    <h3>🔧 Recursos</h3>
                    <div id="resources-list" class="loading">Selecione uma conta primeiro</div>
                    <button class="btn" onclick="loadResources()">🔄 Recarregar</button>
                </div>
                
                <div class="card">
                    <h3>🚨 Alertas</h3>
                    <div id="alerts-list" class="loading">Carregando alertas...</div>
                    <button class="btn" onclick="loadAlerts()">🔄 Recarregar</button>
                </div>
            </div>
        </div>

        <script>
            let selectedAccountId = null;

            async function fetchAPI(endpoint) {
                try {
                    const response = await fetch(endpoint);
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    return await response.json();
                } catch (error) {
                    console.error('API Error:', error);
                    throw error;
                }
            }

            async function loadAccounts() {
                try {
                    document.getElementById('accounts-list').innerHTML = '<div class="loading">Carregando...</div>';
                    const data = await fetchAPI('/api/v1/accounts');
                    
                    if (data.accounts && data.accounts.length > 0) {
                        let html = '';
                        data.accounts.forEach(account => {
                            html += `
                                <div style="margin-bottom: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                                    <strong>${account.name}</strong>
                                    <span class="status ${account.status}">${account.status}</span>
                                    <br><small>ID: ${account.account_id} | Região: ${account.region}</small>
                                    <br><button class="btn" onclick="selectAccount(${account.id}, '${account.name}')">📋 Selecionar</button>
                                </div>
                            `;
                        });
                        document.getElementById('accounts-list').innerHTML = html;
                        
                        // Auto-selecionar primeira conta
                        if (!selectedAccountId) {
                            selectAccount(data.accounts[0].id, data.accounts[0].name);
                        }
                    } else {
                        document.getElementById('accounts-list').innerHTML = '<div class="error">Nenhuma conta encontrada</div>';
                    }
                } catch (error) {
                    document.getElementById('accounts-list').innerHTML = `<div class="error">Erro: ${error.message}</div>`;
                }
            }

            function selectAccount(accountId, accountName) {
                selectedAccountId = accountId;
                document.getElementById('status').innerHTML = `Conta selecionada: <strong>${accountName}</strong>`;
                loadResources();
                loadAlerts();
            }

            async function loadResources() {
                if (!selectedAccountId) {
                    document.getElementById('resources-list').innerHTML = '<div class="error">Selecione uma conta primeiro</div>';
                    return;
                }
                
                try {
                    document.getElementById('resources-list').innerHTML = '<div class="loading">Carregando recursos...</div>';
                    const data = await fetchAPI(`/api/v1/accounts/${selectedAccountId}/resources`);
                    
                    if (data.resources && data.resources.length > 0) {
                        let html = '<div style="margin-bottom: 1rem;"><strong>Total: ' + data.resources.length + ' recursos</strong></div>';
                        data.resources.slice(0, 5).forEach(resource => {
                            html += `
                                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 4px;">
                                    <strong>${resource.resource_type}</strong>: ${resource.name || resource.resource_id}
                                    <span class="status ${resource.status === 'running' || resource.status === 'available' ? 'active' : 'inactive'}">${resource.status}</span>
                                </div>
                            `;
                        });
                        if (data.resources.length > 5) {
                            html += `<div style="opacity: 0.7;">... e mais ${data.resources.length - 5} recursos</div>`;
                        }
                        document.getElementById('resources-list').innerHTML = html;
                    } else {
                        document.getElementById('resources-list').innerHTML = '<div class="error">Nenhum recurso encontrado</div>';
                    }
                } catch (error) {
                    document.getElementById('resources-list').innerHTML = `<div class="error">Erro: ${error.message}</div>`;
                }
            }

            async function loadAlerts() {
                try {
                    document.getElementById('alerts-list').innerHTML = '<div class="loading">Carregando alertas...</div>';
                    const data = await fetchAPI('/api/v1/alerts');
                    
                    if (data.alerts && data.alerts.length > 0) {
                        let html = '<div style="margin-bottom: 1rem;"><strong>Total: ' + data.alerts.length + ' alertas</strong></div>';
                        data.alerts.slice(0, 3).forEach(alert => {
                            html += `
                                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 4px;">
                                    <strong>${alert.title}</strong>
                                    <span class="status ${alert.severity === 'critical' ? 'inactive' : 'active'}">${alert.severity}</span>
                                    <br><small>${alert.resource_type}: ${alert.resource_id}</small>
                                </div>
                            `;
                        });
                        if (data.alerts.length > 3) {
                            html += `<div style="opacity: 0.7;">... e mais ${data.alerts.length - 3} alertas</div>`;
                        }
                        document.getElementById('alerts-list').innerHTML = html;
                    } else {
                        document.getElementById('alerts-list').innerHTML = '<div style="color: #10b981;">✅ Nenhum alerta ativo</div>';
                    }
                } catch (error) {
                    document.getElementById('alerts-list').innerHTML = `<div class="error">Erro: ${error.message}</div>`;
                }
            }

            // Carregar dados iniciais
            document.addEventListener('DOMContentLoaded', () => {
                loadAccounts();
                loadAlerts();
                
                // Auto-refresh a cada 30 segundos
                setInterval(() => {
                    loadAccounts();
                    if (selectedAccountId) {
                        loadResources();
                    }
                    loadAlerts();
                }, 30000);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/v1/accounts")
async def get_accounts():
    """Lista todas as contas AWS"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com banco")
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, name, account_id, region, services, status, created_at
            FROM aws_accounts ORDER BY created_at DESC
        """)
        
        accounts = []
        for row in cursor.fetchall():
            account = dict(row)
            account['services'] = safe_json_loads(account.get('services'))
            accounts.append(account)
        
        cursor.close()
        conn.close()
        return {"accounts": accounts}
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/api/v1/accounts/{account_id}")
async def get_account(account_id: int):
    """Busca uma conta específica"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com banco")
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM aws_accounts WHERE id = %s", (account_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        
        account = dict(row)
        account['services'] = safe_json_loads(account.get('services'))
        
        cursor.close()
        conn.close()
        return account
        
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/api/v1/accounts/{account_id}/resources")
async def get_account_resources(account_id: int):
    """Lista recursos de uma conta"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com banco")
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM aws_resources WHERE account_id = %s ORDER BY resource_type, name", (account_id,))
        
        resources = []
        for row in cursor.fetchall():
            resource = dict(row)
            resource['metadata'] = safe_json_loads(resource.get('metadata'))
            resources.append(resource)
        
        cursor.close()
        conn.close()
        return {"account_id": account_id, "resources": resources}
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/api/v1/alerts")
async def get_alerts():
    """Lista todos os alertas REAIS (executa health check primeiro)"""
    try:
        # Executar verificação de saúde primeiro para obter alertas reais
        if health_checker_available:
            await run_health_check(DB_CONFIG)
        
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT al.*, a.name as account_name, a.account_id as aws_account_id
            FROM alerts al 
            JOIN aws_accounts a ON al.account_id = a.id 
            WHERE al.status = 'active'
            ORDER BY 
                CASE al.severity 
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                al.created_at DESC
        """)
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            # Parse ai_analysis se for string
            if isinstance(alert.get('ai_analysis'), str):
                alert['ai_analysis'] = safe_json_loads(alert['ai_analysis'])
            alerts.append(alert)
        
        cursor.close()
        conn.close()
        return {"alerts": alerts}
        
    except Exception as e:
        print(f"Erro ao buscar alertas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.post("/api/v1/accounts")
async def create_account(account: AWSAccount):
    """Cria uma nova conta AWS"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com banco")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO aws_accounts (name, account_id, region, access_key, secret_key, services, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            account.name, account.account_id, account.region,
            account.access_key, account.secret_key,
            json.dumps(account.services), account.status
        ))
        
        account_id = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Conta criada", "account_id": account_id}
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8000, reload=False)


# Serve new HTML pages
@app.get("/accounts.html", response_class=HTMLResponse)
async def get_accounts_page():
    try:
        with open("accounts.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Accounts page not found")

@app.get("/account-details.html", response_class=HTMLResponse)
async def get_account_details_page():
    try:
        with open("account-details.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Account details page not found")

@app.get("/alert-analysis.html", response_class=HTMLResponse)
async def get_alert_analysis_page():
    try:
        with open("alert-analysis.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Alert analysis page not found")

# Redirect root to new accounts page
@app.get("/", response_class=HTMLResponse)
async def redirect_root():
    return HTMLResponse(content="""
    <html>
    <head>
        <meta charset="UTF-8">
        <script>window.location.href = '/accounts.html';</script>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #0d1117; color: #e6edf3; 
                display: flex; align-items: center; justify-content: center;
                min-height: 100vh; margin: 0;
            }
        </style>
    </head>
    <body>
        <div style="text-align: center;">
            <h1>🚀 AWSNoc IA IA</h1>
            <p>Redirecionando...</p>
        </div>
    </body>
    </html>
    """)

# === NOVOS ENDPOINTS PARA DESCOBERTA REAL DE RECURSOS AWS ===

@app.post("/api/v1/discovery/trigger")
async def trigger_discovery():
    """Trigger manual para descoberta de recursos AWS"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM aws_accounts WHERE status = 'active'")
        accounts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not accounts:
            return {"message": "Nenhuma conta ativa encontrada", "resources_found": 0, "alerts_generated": 0}
        
        total_resources = 0
        total_alerts = 0
        
        for account in accounts:
            try:
                # Importar sistema de descoberta
                from aws_discovery import AWSResourceDiscovery
                from ai_analysis import AIAnalysisService
                
                ai_service = AIAnalysisService()
                
                # Descobrir recursos reais da AWS
                discovery = AWSResourceDiscovery(
                    account['access_key'],
                    account['secret_key'],
                    account['region']
                )
                
                resources = discovery.discover_all_resources()
                total_resources += len(resources)
                
                # Salvar recursos no banco
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Limpar recursos antigos desta conta
                cursor.execute("DELETE FROM aws_resources WHERE account_id = %s", (account['id'],))
                
                # Inserir novos recursos
                for resource in resources:
                    cursor.execute("""
                        INSERT INTO aws_resources 
                        (account_id, resource_type, resource_id, name, status, region, metadata, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        account['id'],
                        resource['resource_type'],
                        resource['resource_id'],
                        resource.get('name'),
                        resource.get('status'),
                        resource.get('region'),
                        json.dumps(resource.get('metadata', {})),
                        resource.get('created_at', datetime.now())
                    ))
                
                # Analisar recursos para gerar alertas
                for resource in resources:
                    try:
                        analysis = ai_service.analyze_resource_health(resource)
                        
                        if analysis.get('health_status') in ['warning', 'critical']:
                            issues = analysis.get('issues', [])
                            
                            for issue in issues:
                                if issue.get('severity') in ['high', 'critical']:
                                    # Criar alerta
                                    cursor.execute("""
                                        INSERT INTO alerts 
                                        (account_id, resource_id, resource_type, alert_type, severity, title, description, ai_analysis)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (
                                        account['id'],
                                        resource['resource_id'],
                                        resource['resource_type'],
                                        issue.get('type', 'unknown'),
                                        issue.get('severity'),
                                        f"{issue.get('type', 'Issue').title()} - {resource.get('name', 'Unknown Resource')}",
                                        issue.get('description', 'No description available'),
                                        json.dumps(analysis)
                                    ))
                                    total_alerts += 1
                    except Exception as e:
                        print(f"Erro ao analisar recurso {resource.get('resource_id')}: {e}")
                        continue
                
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Erro ao descobrir recursos da conta {account['name']}: {e}")
                continue
        
        return {
            "message": f"Descoberta executada para {len(accounts)} contas",
            "resources_found": total_resources,
            "alerts_generated": total_alerts,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Erro na descoberta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/resources/discovered")
async def get_discovered_resources():
    """Lista recursos descobertos pelo sistema real"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT r.*, a.name as account_name, a.account_id as aws_account_id
            FROM aws_resources r 
            JOIN aws_accounts a ON r.account_id = a.id 
            ORDER BY r.created_at DESC 
            LIMIT 100
        """)
        
        resources = []
        for row in cursor.fetchall():
            resource = dict(row)
            # Parse metadata se for string
            if isinstance(resource['metadata'], str):
                resource['metadata'] = safe_json_loads(resource['metadata'])
            resources.append(resource)
        
        cursor.close()
        conn.close()
        
        return {
            "resources": resources,
            "total": len(resources),
            "status": "success"
        }
        
    except Exception as e:
        print(f"Erro ao buscar recursos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alerts/real")
async def get_real_alerts():
    """Lista alertas reais gerados pelo sistema de descoberta"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT al.*, a.name as account_name, a.account_id as aws_account_id
            FROM alerts al 
            JOIN aws_accounts a ON al.account_id = a.id 
            WHERE al.status = 'active'
            ORDER BY 
                CASE al.severity 
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                al.created_at DESC
        """)
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            # Parse ai_analysis se for string
            if isinstance(alert.get('ai_analysis'), str):
                alert['ai_analysis'] = safe_json_loads(alert['ai_analysis'])
            alerts.append(alert)
        
        cursor.close()
        conn.close()
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "status": "success"
        }
        
    except Exception as e:
        print(f"Erro ao buscar alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Importar o novo serviço de alarmes reais
try:
    from real_alarms_service import RealAlarmsService
    real_alarms_service = RealAlarmsService(DB_CONFIG)
except ImportError as e:
    print(f"Aviso: Não foi possível importar RealAlarmsService: {e}")
    real_alarms_service = None

@app.post("/api/v1/alarms/discover")
async def discover_cloudwatch_alarms():
    """Descobrir alarmes reais do CloudWatch para todas as contas"""
    if not real_alarms_service:
        raise HTTPException(status_code=503, detail="Serviço de alarmes reais não disponível")
    
    try:
        result = await real_alarms_service.discover_alarms_all_accounts()
        return result
    except Exception as e:
        print(f"Erro na descoberta de alarmes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/alarms/discover/{account_id}")
async def discover_cloudwatch_alarms_for_account(account_id: int):
    """Descobrir alarmes reais do CloudWatch para uma conta específica"""
    if not real_alarms_service:
        raise HTTPException(status_code=503, detail="Serviço de alarmes reais não disponível")
    
    try:
        alarms = await real_alarms_service.discover_alarms_for_account(account_id)
        return {
            "account_id": account_id,
            "alarms_discovered": len(alarms),
            "alarms": alarms,
            "status": "success"
        }
    except Exception as e:
        print(f"Erro na descoberta de alarmes para conta {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alarms/cloudwatch")
async def get_real_cloudwatch_alarms():
    """Buscar alarmes reais do CloudWatch com análise de IA"""
    if not real_alarms_service:
        raise HTTPException(status_code=503, detail="Serviço de alarmes reais não disponível")
    
    try:
        alarms = await real_alarms_service.get_real_alarms_with_ai_analysis()
        
        # Separar por severidade e estado
        active_alarms = [a for a in alarms if a['state_value'] == 'ALARM']
        critical_alarms = [a for a in active_alarms if a['severity'] == 'CRITICAL']
        
        return {
            "alarms": alarms,
            "summary": {
                "total_alarms": len(alarms),
                "active_alarms": len(active_alarms),
                "critical_alarms": len(critical_alarms),
                "ok_alarms": len([a for a in alarms if a['state_value'] == 'OK']),
                "insufficient_data": len([a for a in alarms if a['state_value'] == 'INSUFFICIENT_DATA'])
            },
            "status": "success"
        }
    except Exception as e:
        print(f"Erro buscando alarmes CloudWatch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alarms/cloudwatch/{account_id}")
async def get_real_cloudwatch_alarms_by_account(account_id: int):
    """Buscar alarmes reais do CloudWatch para uma conta específica"""
    if not real_alarms_service:
        raise HTTPException(status_code=503, detail="Serviço de alarmes reais não disponível")
    
    try:
        alarms = await real_alarms_service.get_real_alarms_with_ai_analysis(account_id)
        
        return {
            "account_id": account_id,
            "alarms": alarms,
            "total": len(alarms),
            "status": "success"
        }
    except Exception as e:
        print(f"Erro buscando alarmes para conta {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Página HTML para visualizar alarmes reais
@app.get("/alarms-dashboard.html")
async def get_alarms_dashboard():
    """Dashboard de alarmes reais do CloudWatch"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AWSNoc IA IA - Alarmes CloudWatch</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    </head>
    <body class="bg-gray-50">
        <div x-data="alarmsApp()" x-init="init()" class="container mx-auto px-4 py-8">
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h1 class="text-3xl font-bold text-gray-800 mb-2">
                    🚨 Alarmes CloudWatch - Monitoramento em Tempo Real
                </h1>
                <p class="text-gray-600">Sistema inteligente de monitoramento AWS com análise de IA</p>
            </div>

            <!-- Controles -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <div class="flex flex-wrap gap-4 items-center">
                    <button @click="discoverAlarms()" :disabled="loading" 
                            class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50">
                        <span x-show="!loading">🔍 Descobrir Alarmes</span>
                        <span x-show="loading">🔄 Descobrindo...</span>
                    </button>
                    
                    <button @click="loadAlarms()" :disabled="loading"
                            class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded disabled:opacity-50">
                        ♻️ Atualizar
                    </button>
                    
                    <div class="text-sm text-gray-600">
                        Última atualização: <span x-text="lastUpdate"></span>
                    </div>
                </div>
            </div>

            <!-- Resumo -->
            <div x-show="summary" class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="bg-red-100 border-l-4 border-red-500 p-4 rounded">
                    <div class="text-red-800 font-semibold">Críticos</div>
                    <div class="text-2xl font-bold text-red-600" x-text="summary?.critical_alarms || 0"></div>
                </div>
                <div class="bg-orange-100 border-l-4 border-orange-500 p-4 rounded">
                    <div class="text-orange-800 font-semibold">Ativos</div>
                    <div class="text-2xl font-bold text-orange-600" x-text="summary?.active_alarms || 0"></div>
                </div>
                <div class="bg-green-100 border-l-4 border-green-500 p-4 rounded">
                    <div class="text-green-800 font-semibold">OK</div>
                    <div class="text-2xl font-bold text-green-600" x-text="summary?.ok_alarms || 0"></div>
                </div>
                <div class="bg-blue-100 border-l-4 border-blue-500 p-4 rounded">
                    <div class="text-blue-800 font-semibold">Total</div>
                    <div class="text-2xl font-bold text-blue-600" x-text="summary?.total_alarms || 0"></div>
                </div>
            </div>

            <!-- Lista de Alarmes -->
            <div x-show="alarms.length > 0" class="bg-white rounded-lg shadow-lg">
                <div class="p-6 border-b">
                    <h2 class="text-xl font-semibold text-gray-800">Alarmes CloudWatch</h2>
                </div>
                <div class="divide-y">
                    <template x-for="alarm in alarms" :key="alarm.id">
                        <div class="p-6 hover:bg-gray-50" 
                             :class="{'border-l-4 border-red-500': alarm.severity === 'CRITICAL', 
                                     'border-l-4 border-orange-500': alarm.severity === 'HIGH',
                                     'border-l-4 border-yellow-500': alarm.severity === 'MEDIUM',
                                     'border-l-4 border-green-500': alarm.severity === 'LOW'}">
                            
                            <div class="flex justify-between items-start mb-4">
                                <div>
                                    <h3 class="text-lg font-semibold text-gray-800" x-text="alarm.alarm_name"></h3>
                                    <div class="flex items-center gap-4 text-sm text-gray-600 mt-1">
                                        <span class="px-2 py-1 rounded text-xs font-medium"
                                              :class="{'bg-red-100 text-red-800': alarm.state_value === 'ALARM',
                                                      'bg-green-100 text-green-800': alarm.state_value === 'OK',
                                                      'bg-yellow-100 text-yellow-800': alarm.state_value === 'INSUFFICIENT_DATA'}"
                                              x-text="alarm.state_value">
                                        </span>
                                        <span x-text="alarm.account_name"></span>
                                        <span x-text="alarm.region"></span>
                                        <span x-text="alarm.namespace + '/' + alarm.metric_name"></span>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="px-2 py-1 rounded text-xs font-medium"
                                         :class="{'bg-red-100 text-red-800': alarm.severity === 'CRITICAL',
                                                 'bg-orange-100 text-orange-800': alarm.severity === 'HIGH',
                                                 'bg-yellow-100 text-yellow-800': alarm.severity === 'MEDIUM',
                                                 'bg-green-100 text-green-800': alarm.severity === 'LOW'}"
                                         x-text="alarm.severity">
                                    </div>
                                </div>
                            </div>

                            <div class="text-sm text-gray-600 mb-4">
                                <strong>Razão:</strong> <span x-text="alarm.state_reason"></span>
                            </div>

                            <!-- Recursos Afetados -->
                            <div x-show="alarm.affected_resources && alarm.affected_resources.length > 0" class="mb-4">
                                <div class="text-sm font-medium text-gray-700 mb-2">Recursos Afetados:</div>
                                <div class="flex flex-wrap gap-2">
                                    <template x-for="resource in alarm.affected_resources">
                                        <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs" x-text="resource"></span>
                                    </template>
                                </div>
                            </div>

                            <!-- Análise de IA -->
                            <div x-show="alarm.ai_analysis && Object.keys(alarm.ai_analysis).length > 0 && !alarm.ai_analysis.error" 
                                 class="bg-blue-50 border border-blue-200 rounded p-4 mt-4">
                                <div class="text-sm font-medium text-blue-800 mb-2">🤖 Análise de IA:</div>
                                
                                <div x-show="alarm.ai_analysis.root_cause" class="mb-2">
                                    <strong class="text-blue-700">Causa Raiz:</strong>
                                    <span class="text-blue-600" x-text="alarm.ai_analysis.root_cause"></span>
                                </div>
                                
                                <div x-show="alarm.ai_analysis.immediate_actions" class="mb-2">
                                    <strong class="text-blue-700">Ações Imediatas:</strong>
                                    <ul class="list-disc list-inside text-blue-600 text-sm mt-1">
                                        <template x-for="action in alarm.ai_analysis.immediate_actions">
                                            <li x-text="action"></li>
                                        </template>
                                    </ul>
                                </div>
                                
                                <div x-show="alarm.ai_analysis.business_impact" class="text-sm">
                                    <strong class="text-blue-700">Impacto:</strong>
                                    <span class="text-blue-600" x-text="alarm.ai_analysis.business_impact"></span>
                                </div>
                            </div>

                            <!-- Dados da Métrica -->
                            <div x-show="alarm.metric_data" class="text-xs text-gray-500 mt-4 bg-gray-50 p-3 rounded">
                                <strong>Dados da Métrica:</strong>
                                Valor atual: <span x-text="alarm.metric_data?.latest_value"></span> |
                                Threshold: <span x-text="alarm.threshold"></span> |
                                Operador: <span x-text="alarm.comparison_operator"></span>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- Estado de Carregamento -->
            <div x-show="loading" class="text-center py-8">
                <div class="text-gray-600">🔄 Carregando alarmes...</div>
            </div>

            <!-- Estado Vazio -->
            <div x-show="!loading && alarms.length === 0" class="text-center py-8">
                <div class="text-gray-600">📊 Nenhum alarme encontrado</div>
                <button @click="discoverAlarms()" class="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                    🔍 Descobrir Alarmes CloudWatch
                </button>
            </div>
        </div>

        <script>
            function alarmsApp() {
                return {
                    alarms: [],
                    summary: null,
                    loading: false,
                    lastUpdate: '',
                    
                    async init() {
                        await this.loadAlarms();
                    },
                    
                    async loadAlarms() {
                        this.loading = true;
                        try {
                            const response = await fetch('/api/v1/alarms/cloudwatch');
                            const data = await response.json();
                            
                            if (data.status === 'success') {
                                this.alarms = data.alarms;
                                this.summary = data.summary;
                                this.lastUpdate = new Date().toLocaleString('pt-BR');
                            } else {
                                console.error('Erro:', data);
                            }
                        } catch (error) {
                            console.error('Erro carregando alarmes:', error);
                        } finally {
                            this.loading = false;
                        }
                    },
                    
                    async discoverAlarms() {
                        this.loading = true;
                        try {
                            const response = await fetch('/api/v1/alarms/discover', {
                                method: 'POST'
                            });
                            const data = await response.json();
                            
                            if (data.status === 'success') {
                                alert(`✅ Descoberta concluída! Processadas ${data.accounts_processed} contas, ${data.total_alarms_discovered} alarmes encontrados.`);
                                await this.loadAlarms();
                            } else {
                                alert('❌ Erro na descoberta: ' + (data.error || 'Erro desconhecido'));
                            }
                        } catch (error) {
                            console.error('Erro na descoberta:', error);
                            alert('❌ Erro na descoberta: ' + error.message);
                        } finally {
                            this.loading = false;
                        }
                    }
                }
            }
        </script>
    </body>
    </html>
    """)


# Importar health checker
try:
    from health_checker import run_health_check
    health_checker_available = True
except ImportError as e:
    print(f"Aviso: Health checker não disponível: {e}")
    health_checker_available = False

@app.post("/api/v1/health/check")
async def run_health_check_endpoint():
    """Executar verificação de saúde em tempo real"""
    if not health_checker_available:
        raise HTTPException(status_code=503, detail="Health checker não disponível")
    
    try:
        alerts = await run_health_check(DB_CONFIG)
        return {
            "alerts_found": len(alerts),
            "alerts": alerts,
            "status": "success",
            "check_time": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Erro na verificação de saúde: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alerts/live")
async def get_live_alerts():
    """Buscar alertas em tempo real (executa health check primeiro)"""
    try:
        # Executar verificação de saúde primeiro
        if health_checker_available:
            await run_health_check(DB_CONFIG)
        
        # Buscar alertas atualizados
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT al.*, a.name as account_name, a.account_id as aws_account_id
            FROM alerts al 
            JOIN aws_accounts a ON al.account_id = a.id 
            WHERE al.status = 'active'
            ORDER BY 
                CASE al.severity 
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                al.created_at DESC
        """)
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            # Parse ai_analysis se for string
            if isinstance(alert.get('ai_analysis'), str):
                alert['ai_analysis'] = safe_json_loads(alert['ai_analysis'])
            alerts.append(alert)
        
        cursor.close()
        conn.close()
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "status": "success",
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Erro ao buscar alertas live: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Atualizar endpoint de alertas para usar dados reais
@app.get("/api/v1/alerts/dashboard")
async def get_alerts_for_dashboard():
    """Buscar alertas para dashboard (dados reais)"""
    try:
        # Executar verificação de saúde se disponível
        if health_checker_available:
            await run_health_check(DB_CONFIG)
        
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Buscar alertas críticos e altos
        cursor.execute("""
            SELECT al.*, a.name as account_name, a.account_id as aws_account_id
            FROM alerts al 
            JOIN aws_accounts a ON al.account_id = a.id 
            WHERE al.status = 'active' AND al.severity IN ('critical', 'high')
            ORDER BY 
                CASE al.severity 
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    ELSE 3
                END,
                al.created_at DESC
            LIMIT 10
        """)
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            alerts.append({
                'id': alert['id'],
                'title': alert['title'],
                'description': alert['description'],
                'severity': alert['severity'],
                'resource_type': alert['resource_type'],
                'resource_id': alert['resource_id'],
                'account_name': alert['account_name'],
                'created_at': alert['created_at'].isoformat() if alert['created_at'] else None
            })
        
        cursor.close()
        conn.close()
        
        return {
            "alerts": alerts,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Erro ao buscar alertas para dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/accounts/{account_id}/alerts")
async def get_account_alerts(account_id: int):
    """Buscar alertas REAIS para uma conta específica"""
    try:
        # Executar verificação de saúde primeiro
        if health_checker_available:
            await run_health_check(DB_CONFIG)
        
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT al.*, a.name as account_name, a.account_id as aws_account_id
            FROM alerts al 
            JOIN aws_accounts a ON al.account_id = a.id 
            WHERE al.status = 'active' AND al.account_id = %s
            ORDER BY 
                CASE al.severity 
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                al.created_at DESC
        """, (account_id,))
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            # Parse ai_analysis se for string
            if isinstance(alert.get('ai_analysis'), str):
                alert['ai_analysis'] = safe_json_loads(alert['ai_analysis'])
            alerts.append(alert)
        
        cursor.close()
        conn.close()
        return {"alerts": alerts}
        
    except Exception as e:
        print(f"Erro ao buscar alertas da conta {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.get("/api/v1/alerts/force-refresh")
async def force_refresh_alerts():
    """FORÇA refresh dos alertas (sem cache)"""
    try:
        # LIMPAR todos os alertas antigos primeiro
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM alerts")
            conn.commit()
            conn.close()
            print("🗑️ Alertas antigos removidos")
        
        # Executar verificação de saúde FORÇADA
        if health_checker_available:
            alerts = await run_health_check(DB_CONFIG)
            print(f"✅ {len(alerts)} novos alertas reais detectados")
        
        # Buscar alertas atualizados
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT al.*, a.name as account_name, a.account_id as aws_account_id
            FROM alerts al 
            JOIN aws_accounts a ON al.account_id = a.id 
            WHERE al.status = 'active'
            ORDER BY 
                CASE al.severity 
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                al.created_at DESC
        """)
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            if isinstance(alert.get('ai_analysis'), str):
                alert['ai_analysis'] = safe_json_loads(alert['ai_analysis'])
            alerts.append(alert)
        
        cursor.close()
        conn.close()
        
        from datetime import datetime
        return {
            "alerts": alerts,
            "refresh_time": datetime.now().isoformat(),
            "cache_bust": int(datetime.now().timestamp()),
            "status": "force_refreshed"
        }
        
    except Exception as e:
        print(f"Erro no force refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.get("/api/v1/debug/alerts-raw")
async def debug_alerts_raw():
    """DEBUG: Ver alertas direto do banco sem health check"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        
        all_alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            all_alerts.append(alert)
        
        cursor.close()
        conn.close()
        
        return {
            "total_alerts": len(all_alerts),
            "alerts": all_alerts,
            "debug": "raw_from_database"
        }
        
    except Exception as e:
        return {"error": str(e)}



@app.get("/api/v1/alerts/{alert_id}")
async def get_alert_details(alert_id: int):
    """Busca detalhes de um alerta específico"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Buscar alerta específico com informações da conta
        query = """
        SELECT a.*, acc.name as account_name, acc.account_id as aws_account_id
        FROM alerts a
        LEFT JOIN accounts acc ON a.account_id = acc.id
        WHERE a.id = %s
        """
        
        cursor.execute(query, (alert_id,))
        alert_row = cursor.fetchone()
        
        if not alert_row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Alerta não encontrado")
        
        alert = dict(alert_row)
        
        # Parse do JSON se necessário
        if alert.get('ai_analysis') and isinstance(alert['ai_analysis'], str):
            try:
                alert['ai_analysis'] = json.loads(alert['ai_analysis'])
            except:
                pass
        
        cursor.close()
        conn.close()
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar alerta: {str(e)}")

@app.post("/api/v1/alerts/{alert_id}/analyze")
async def analyze_alert_with_ai(alert_id: int):
    """Análise inteligente de alerta usando AWS Bedrock + CloudWatch Logs"""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Erro de conexão com banco")
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Buscar alerta específico
        cursor.execute("SELECT * FROM alerts WHERE id = %s", (alert_id,))
        alert = cursor.fetchone()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alerta não encontrado")
        
        # Buscar conta AWS
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (alert['account_id'],))
        account = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not account:
            raise HTTPException(status_code=404, detail="Conta AWS não encontrada")
        
        # Inicializar cliente AWS
        import boto3
        
        session = boto3.Session(
            aws_access_key_id=account['access_key'],
            aws_secret_access_key=account['secret_key'],
            region_name=account['region']
        )
        
        # Análise específica por tipo de recurso
        analysis_result = {}
        
        if alert['resource_type'] == 'ECS_Service':
            analysis_result = await analyze_ecs_service_with_ai(session, alert, account)
        elif alert['resource_type'] == 'TargetGroup':
            analysis_result = await analyze_target_group_with_ai(session, alert, account)
        elif alert['resource_type'] == 'EC2':
            analysis_result = await analyze_ec2_with_ai(session, alert, account)
        elif alert['resource_type'] == 'RDS':
            analysis_result = await analyze_rds_with_ai(session, alert, account)
        else:
            analysis_result = await analyze_generic_with_ai(session, alert, account)
        
        # Salvar análise no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE alerts SET ai_analysis = %s WHERE id = %s",
            (json.dumps(analysis_result), alert_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "alert_id": alert_id,
            "analysis": analysis_result,
            "status": "completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

async def analyze_ecs_service_with_ai(session, alert, account):
    """Análise específica para ECS Service"""
    try:
        ecs = session.client('ecs')
        logs = session.client('logs')
        bedrock = session.client('bedrock-runtime', region_name='us-east-2')
        
        # Extrair informações do ARN
        service_arn = alert['resource_id']
        service_name = service_arn.split('/')[-1]
        cluster_name = service_arn.split('/')[-2]
        
        # 1. Buscar detalhes do serviço
        service_details = ecs.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        service = service_details['services'][0]
        task_definition_arn = service['taskDefinition']
        
        # 2. Buscar task definition
        task_def = ecs.describe_task_definition(
            taskDefinition=task_definition_arn
        )
        
        # 3. Buscar tasks que falharam
        failed_tasks = ecs.list_tasks(
            cluster=cluster_name,
            serviceName=service_name,
            desiredStatus='STOPPED'
        )
        
        task_failures = []
        if failed_tasks['taskArns']:
            task_details = ecs.describe_tasks(
                cluster=cluster_name,
                tasks=failed_tasks['taskArns'][:5]  # Últimas 5 tasks
            )
            
            for task in task_details['tasks']:
                if 'stoppedReason' in task:
                    task_failures.append({
                        'task_arn': task['taskArn'],
                        'stopped_reason': task['stoppedReason'],
                        'stopped_at': task.get('stoppedAt', '').isoformat() if task.get('stoppedAt') else None,
                        'containers': [
                            {
                                'name': container['name'],
                                'exit_code': container.get('exitCode'),
                                'reason': container.get('reason', '')
                            }
                            for container in task.get('containers', [])
                            if container.get('lastStatus') == 'STOPPED'
                        ]
                    })
        
        # 4. Buscar logs do CloudWatch
        log_group_name = None
        container_logs = []
        
        for container_def in task_def['taskDefinition']['containerDefinitions']:
            if 'logConfiguration' in container_def:
                log_config = container_def['logConfiguration']
                if log_config.get('logDriver') == 'awslogs':
                    log_group_name = log_config['options'].get('awslogs-group')
                    
                    if log_group_name:
                        try:
                            # Buscar logs das últimas 2 horas
                            import time
                            end_time = int(time.time() * 1000)
                            start_time = end_time - (2 * 60 * 60 * 1000)  # 2 horas atrás
                            
                            log_events = logs.get_log_events(
                                logGroupName=log_group_name,
                                startTime=start_time,
                                endTime=end_time,
                                limit=100
                            )
                            
                            container_logs.append({
                                'container': container_def['name'],
                                'log_group': log_group_name,
                                'recent_logs': [
                                    {
                                        'timestamp': event['timestamp'],
                                        'message': event['message']
                                    }
                                    for event in log_events['events'][-20:]  # Últimas 20 linhas
                                ]
                            })
                        except Exception as log_error:
                            container_logs.append({
                                'container': container_def['name'],
                                'log_group': log_group_name,
                                'error': str(log_error)
                            })
        
        # 5. Preparar contexto para IA
        ai_context = f"""
        ALERTA ECS SERVICE: {alert['title']}
        DESCRIÇÃO: {alert['description']}
        
        DETALHES DO SERVIÇO:
        - Cluster: {cluster_name}
        - Service: {service_name}
        - Task Definition: {task_definition_arn}
        - Desired Count: {service.get('desiredCount', 0)}
        - Running Count: {service.get('runningCount', 0)}
        - Pending Count: {service.get('pendingCount', 0)}
        
        FALHAS DE TASKS:
        {json.dumps(task_failures, indent=2)}
        
        LOGS RECENTES DOS CONTAINERS:
        {json.dumps(container_logs, indent=2)}
        
        CONFIGURAÇÃO DO CONTAINER:
        {json.dumps([{
            'name': c['name'],
            'image': c['image'],
            'memory': c.get('memory'),
            'memoryReservation': c.get('memoryReservation'),
            'cpu': c.get('cpu'),
            'environment': c.get('environment', [])
        } for c in task_def['taskDefinition']['containerDefinitions']], indent=2)}
        """
        
        # 6. Chamar Bedrock para análise
        prompt = f"""
        Você é um especialista em AWS ECS e DevOps. Analise o seguinte problema de ECS Service:

        {ai_context}

        Por favor, forneça:
        1. CAUSA RAIZ: Qual é a causa mais provável do problema?
        2. EVIDÊNCIAS: Quais evidências nos logs/configurações suportam essa conclusão?
        3. IMPACTO: Qual o impacto no serviço?
        4. SOLUÇÃO IMEDIATA: Passos específicos para resolver agora
        5. PREVENÇÃO: Como evitar no futuro
        6. COMANDOS AWS CLI: Comandos específicos para diagnosticar/corrigir

        Responda em português, seja específico e prático.
        """
        
        try:
            response = bedrock.invoke_model(
                modelId='us.anthropic.claude-3-5-haiku-20241022-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_analysis = response_body['content'][0]['text']
            
        except Exception as bedrock_error:
            ai_analysis = f"Erro ao conectar com Bedrock: {str(bedrock_error)}"
        
        return {
            "type": "ecs_service_analysis",
            "alert_info": {
                "title": alert['title'],
                "description": alert['description'],
                "resource_id": alert['resource_id']
            },
            "service_details": {
                "cluster": cluster_name,
                "service": service_name,
                "task_definition": task_definition_arn,
                "desired_count": service.get('desiredCount', 0),
                "running_count": service.get('runningCount', 0),
                "pending_count": service.get('pendingCount', 0)
            },
            "task_failures": task_failures,
            "container_logs": container_logs,
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        
    except Exception as e:
        return {
            "type": "ecs_service_analysis",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "status": "failed"
        }

async def analyze_target_group_with_ai(session, alert, account):
    """Análise INTELIGENTE para descobrir qual serviço deveria estar no Target Group"""
    try:
        elbv2 = session.client('elbv2')
        ec2 = session.client('ec2')
        ecs = session.client('ecs')
        eks = session.client('eks')
        lambda_client = session.client('lambda')
        logs = session.client('logs')
        bedrock = session.client('bedrock-runtime', region_name='us-east-2')
        
        # Extrair ARN do target group
        tg_arn = alert['resource_id']
        tg_name = tg_arn.split('/')[-2]
        
        print(f"🔍 Analisando Target Group: {tg_name}")
        
        # 1. Buscar detalhes do Target Group
        tg_details = elbv2.describe_target_groups(TargetGroupArns=[tg_arn])
        target_group = tg_details['TargetGroups'][0]
        
        # 2. Buscar targets atuais (mesmo que vazio)
        targets_health = elbv2.describe_target_health(TargetGroupArn=tg_arn)
        
        # 3. DESCOBERTA INTELIGENTE: Encontrar serviços que DEVERIAM usar este TG
        discovered_services = []
        
        print("🔍 Buscando ECS Services...")
        # 3.1 BUSCAR ECS SERVICES configurados para este Target Group
        try:
            clusters = ecs.list_clusters()
            
            for cluster_arn in clusters['clusterArns']:
                cluster_name = cluster_arn.split('/')[-1]
                services = ecs.list_services(cluster=cluster_name)
                
                for service_arn in services['serviceArns']:
                    service_name = service_arn.split('/')[-1]
                    
                    service_details = ecs.describe_services(
                        cluster=cluster_name,
                        services=[service_name]
                    )
                    
                    for service in service_details['services']:
                        load_balancers = service.get('loadBalancers', [])
                        
                        # Verificar se este serviço está configurado para usar nosso TG
                        for lb in load_balancers:
                            if lb.get('targetGroupArn') == tg_arn:
                                print(f"✅ ENCONTRADO! ECS Service {service_name} configurado para TG {tg_name}")
                                
                                # Analisar o serviço em detalhes
                                ecs_analysis = await analyze_ecs_for_target_group(
                                    ecs, logs, cluster_name, service_name, service, lb
                                )
                                
                                discovered_services.append({
                                    'type': 'ECS_Service',
                                    'name': service_name,
                                    'cluster': cluster_name,
                                    'configured_for_tg': True,
                                    'analysis': ecs_analysis
                                })
                                
        except Exception as ecs_error:
            discovered_services.append({
                'type': 'ECS_SEARCH_ERROR',
                'error': str(ecs_error)
            })
        
        print("🔍 Buscando EC2 Instances...")
        # 3.2 BUSCAR EC2 INSTANCES que podem estar configuradas para este TG
        try:
            # Buscar por tags ou nome que relacionam com o TG
            instances = ec2.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']},
                ]
            )
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    
                    # Verificar se as tags indicam relação com o TG
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    # Buscar por padrões de nome/tag que relacionam com o TG
                    if (tg_name.lower() in str(tags).lower() or 
                        any(keyword in str(tags).lower() for keyword in ['app', 'service', 'web']) or
                        instance_id in str(targets_health)):
                        
                        print(f"✅ ENCONTRADO! EC2 Instance {instance_id} pode estar relacionada ao TG")
                        
                        ec2_analysis = await analyze_ec2_for_target_group(
                            ec2, logs, instance_id, instance, target_group
                        )
                        
                        discovered_services.append({
                            'type': 'EC2_Instance',
                            'name': instance_id,
                            'configured_for_tg': 'possibly',
                            'analysis': ec2_analysis
                        })
                        
        except Exception as ec2_error:
            discovered_services.append({
                'type': 'EC2_SEARCH_ERROR',
                'error': str(ec2_error)
            })
        
        print("🔍 Buscando Lambda Functions...")
        # 3.3 BUSCAR LAMBDA FUNCTIONS
        try:
            functions = lambda_client.list_functions()
            
            for func in functions['Functions']:
                func_name = func['FunctionName']
                
                # Verificar se o nome da função está relacionado ao TG
                if (tg_name.lower() in func_name.lower() or
                    any(keyword in func_name.lower() for keyword in ['app', 'api', 'web'])):
                    
                    print(f"✅ ENCONTRADO! Lambda Function {func_name} pode estar relacionada ao TG")
                    
                    lambda_analysis = await analyze_lambda_for_target_group(
                        lambda_client, logs, func_name, func, target_group
                    )
                    
                    discovered_services.append({
                        'type': 'Lambda_Function',
                        'name': func_name,
                        'configured_for_tg': 'possibly',
                        'analysis': lambda_analysis
                    })
                    
        except Exception as lambda_error:
            discovered_services.append({
                'type': 'LAMBDA_SEARCH_ERROR',
                'error': str(lambda_error)
            })
        
        # 4. Buscar Load Balancers associados
        associated_lbs = []
        try:
            lbs = elbv2.describe_load_balancers()
            
            for lb in lbs['LoadBalancers']:
                listeners = elbv2.describe_listeners(LoadBalancerArn=lb['LoadBalancerArn'])
                for listener in listeners['Listeners']:
                    rules = elbv2.describe_rules(ListenerArn=listener['ListenerArn'])
                    for rule in rules['Rules']:
                        for action in rule['Actions']:
                            if action.get('TargetGroupArn') == tg_arn:
                                associated_lbs.append({
                                    'lb_name': lb['LoadBalancerName'],
                                    'lb_dns': lb['DNSName'],
                                    'lb_scheme': lb['Scheme'],
                                    'listener_port': listener['Port'],
                                    'listener_protocol': listener['Protocol']
                                })
        except:
            pass
        
        # 5. Preparar contexto SUPERINTELIGENTE para IA
        ai_context = f"""
        🔍 ANÁLISE INTELIGENTE DE TARGET GROUP - DESCOBERTA DE SERVIÇOS:
        
        TARGET GROUP: {target_group['TargetGroupName']}
        STATUS: {alert['description']}
        
        CONFIGURAÇÃO DO TARGET GROUP:
        - Protocol: {target_group['Protocol']} 
        - Port: {target_group['Port']}
        - Health Check: {target_group['HealthCheckProtocol']}:{target_group.get('HealthCheckPort', 'traffic-port')}{target_group.get('HealthCheckPath', '')}
        - Thresholds: {target_group['HealthyThresholdCount']}/{target_group['UnhealthyThresholdCount']}
        - Timeout: {target_group['HealthCheckTimeoutSeconds']}s / Interval: {target_group['HealthCheckIntervalSeconds']}s
        
        LOAD BALANCERS CONECTADOS:
        {json.dumps(associated_lbs, indent=2)}
        
        🎯 SERVIÇOS DESCOBERTOS QUE DEVERIAM USAR ESTE TARGET GROUP:
        {json.dumps(discovered_services, indent=2)}
        
        TARGETS ATUAIS NO TG:
        {json.dumps([{'id': t['Target']['Id'], 'port': t['Target']['Port'], 'health': t['TargetHealth']['State']} for t in targets_health['TargetHealthDescriptions']], indent=2)}
        """
        
        # 6. Chamar Bedrock para análise SUPERINTELIGENTE
        prompt = f"""
        Você é um arquiteto DevOps expert em AWS. Analise este Target Group que deveria ter targets mas não tem.

        {ai_context}

        SUA MISSÃO ESPECÍFICA:

        1. IDENTIFICAR O SERVIÇO REAL: Dos serviços descobertos, qual é o principal que deveria estar registrado no Target Group?

        2. CAUSA RAIZ ESPECÍFICA: Por que este serviço NÃO está se registrando no Target Group? Analise:
           - Logs de erro do serviço identificado
           - Status do serviço (running/stopped/failing)
           - Configurações de rede (security groups, subnets)
           - Health checks failing

        3. DIAGNÓSTICO TÉCNICO: Qual problema específico está impedindo o registro:
           - Serviço não está rodando?
           - Health check failing?
           - Problema de network/security group?
           - Configuração incorreta?

        4. SOLUÇÃO ESPECÍFICA: Passos exatos para corrigir o problema do serviço identificado

        5. COMANDOS DIAGNÓSTICO: AWS CLI específicos para verificar e corrigir

        IMPORTANTE: Seja específico sobre QUAL serviço está com problema e EXATAMENTE como corrigir.
        
        Responda em português, seja técnico e detalhado.
        """
        
        try:
            response = bedrock.invoke_model(
                modelId='us.anthropic.claude-3-5-haiku-20241022-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 3000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_analysis = response_body['content'][0]['text']
            
        except Exception as bedrock_error:
            ai_analysis = f"Erro ao conectar com Bedrock: {str(bedrock_error)}"
        
        return {
            "type": "intelligent_target_group_discovery",
            "alert_info": {
                "title": alert['title'],
                "description": alert['description'],
                "resource_id": alert['resource_id']
            },
            "target_group_details": target_group,
            "associated_load_balancers": associated_lbs,
            "discovered_services": discovered_services,
            "current_targets": targets_health['TargetHealthDescriptions'],
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        
    except Exception as e:
        return {
            "type": "intelligent_target_group_discovery",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "status": "failed"
        }

async def analyze_ecs_for_target_group(ecs, logs, cluster_name, service_name, service, load_balancer_config):
    """Análise específica do ECS Service configurado para o Target Group"""
    try:
        analysis = {
            'service_status': {
                'desired_count': service.get('desiredCount', 0),
                'running_count': service.get('runningCount', 0),
                'pending_count': service.get('pendingCount', 0),
                'task_definition': service['taskDefinition']
            },
            'load_balancer_config': load_balancer_config,
            'task_failures': [],
            'logs': [],
            'health_issues': []
        }
        
        # Buscar tasks que falharam
        try:
            failed_tasks = ecs.list_tasks(
                cluster=cluster_name,
                serviceName=service_name,
                desiredStatus='STOPPED'
            )
            
            if failed_tasks['taskArns']:
                task_details = ecs.describe_tasks(
                    cluster=cluster_name,
                    tasks=failed_tasks['taskArns'][:5]
                )
                
                for task in task_details['tasks']:
                    if 'stoppedReason' in task:
                        analysis['task_failures'].append({
                            'task_arn': task['taskArn'],
                            'stopped_reason': task['stoppedReason'],
                            'stopped_at': task.get('stoppedAt', '').isoformat() if task.get('stoppedAt') else None,
                            'containers': [
                                {
                                    'name': container['name'],
                                    'exit_code': container.get('exitCode'),
                                    'reason': container.get('reason', '')
                                }
                                for container in task.get('containers', [])
                            ]
                        })
        except:
            pass
        
        # Buscar logs do serviço
        try:
            task_def = ecs.describe_task_definition(taskDefinition=service['taskDefinition'])
            
            for container_def in task_def['taskDefinition']['containerDefinitions']:
                if 'logConfiguration' in container_def:
                    log_config = container_def['logConfiguration']
                    if log_config.get('logDriver') == 'awslogs':
                        log_group_name = log_config['options'].get('awslogs-group')
                        
                        if log_group_name:
                            try:
                                import time
                                end_time = int(time.time() * 1000)
                                start_time = end_time - (2 * 60 * 60 * 1000)
                                
                                log_events = logs.get_log_events(
                                    logGroupName=log_group_name,
                                    startTime=start_time,
                                    endTime=end_time,
                                    limit=50
                                )
                                
                                analysis['logs'].extend([
                                    {
                                        'timestamp': event['timestamp'],
                                        'message': event['message'],
                                        'log_group': log_group_name,
                                        'container': container_def['name']
                                    }
                                    for event in log_events['events'][-20:]
                                ])
                            except Exception as log_error:
                                analysis['logs'].append({
                                    'error': f'Erro ao buscar logs: {str(log_error)}',
                                    'log_group': log_group_name
                                })
        except:
            pass
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}

async def analyze_ec2_for_target_group(ec2, logs, instance_id, instance, target_group):
    """Análise específica da EC2 Instance"""
    try:
        return {
            'instance_details': {
                'instance_id': instance_id,
                'instance_state': instance['State']['Name'],
                'instance_type': instance['InstanceType'],
                'private_ip': instance.get('PrivateIpAddress'),
                'public_ip': instance.get('PublicIpAddress'),
                'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])]
            },
            'logs': [{'note': 'EC2 log analysis would require CloudWatch agent or specific log groups'}]
        }
    except Exception as e:
        return {'error': str(e)}

async def analyze_lambda_for_target_group(lambda_client, logs, func_name, func, target_group):
    """Análise específica da Lambda Function"""
    try:
        return {
            'function_details': {
                'function_name': func_name,
                'runtime': func['Runtime'],
                'state': func['State'],
                'last_modified': func['LastModified']
            },
            'logs': [{'note': 'Lambda analysis would require CloudWatch Logs integration'}]
        }
    except Exception as e:
        return {'error': str(e)}
async def analyze_generic_with_ai(session, alert, account):
    """Análise genérica para outros tipos de recursos"""
    return {
        "type": "generic_analysis",
        "alert_info": {
            "title": alert['title'],
            "description": alert['description'],
            "resource_id": alert['resource_id'],
            "resource_type": alert['resource_type']
        },
        "ai_analysis": f"Análise detalhada para {alert['resource_type']} ainda não implementada. Resource ID: {alert['resource_id']}",
        "timestamp": datetime.now().isoformat(),
        "status": "completed"
    }
