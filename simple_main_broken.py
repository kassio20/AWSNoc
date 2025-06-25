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
    """Lista todos os alertas"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexão com banco")
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM alerts WHERE status = 'active' ORDER BY created_at DESC")
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            alert['ai_analysis'] = safe_json_loads(alert.get('ai_analysis'))
            alerts.append(alert)
        
        cursor.close()
        conn.close()
        return {"alerts": alerts}
        
    except Exception as e:
        conn.close()
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

# === SISTEMA DE DESCOBERTA REAL DE RECURSOS AWS ===

from aws_discovery import AWSResourceDiscovery
from ai_analysis import AIAnalysisService

# Serviços globais
ai_service = AIAnalysisService()

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
                resource['metadata'] = json.loads(resource['metadata']) if resource['metadata'] else {}
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

@app.get("/api/v1/alerts/active")
async def get_active_alerts():
    """Lista alertas ativos gerados pelo sistema real"""
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
            if isinstance(alert['ai_analysis'], str):
                alert['ai_analysis'] = json.loads(alert['ai_analysis']) if alert['ai_analysis'] else {}
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

