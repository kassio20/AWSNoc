import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import boto3
import json
from botocore.exceptions import ClientError
import asyncio
from database_manager import DatabaseManager
from aws_discovery import AWSResourceDiscovery
from ai_analysis import AIAnalysisService

load_dotenv()

# Database configuration
DB_HOST = "awsnoc-ia-dev-database.cjeqe6pc2viw.us-east-2.rds.amazonaws.com"
DB_PORT = 5432
DB_NAME = "awsnoc-ia"
DB_USER = "awsnoc-ia_admin"
DB_PASSWORD = "Dy6uGR1UVasJEp7D"

# Initialize services
db_manager = DatabaseManager(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
ai_service = AIAnalysisService()

# Pydantic models
class AWSAccount(BaseModel):
    id: Optional[int] = None
    name: str
    account_id: str
    region: str
    access_key: str
    secret_key: str
    services: List[str] = ["CloudWatch", "EC2", "RDS", "S3", "Lambda", "ECS"]
    status: str = "active"
    created_at: Optional[datetime] = None

class ResourceInfo(BaseModel):
    resource_type: str
    resource_id: str
    name: str
    status: str
    region: str
    created_at: Optional[str] = None

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    service: str
    resource_id: Optional[str] = None

class AlertCreate(BaseModel):
    resource_id: str
    resource_type: str
    alert_type: str
    severity: str
    title: str
    description: Optional[str] = None

app = FastAPI(
    title="AWSNoc IA IA",
    description="AI-Powered AWS Log Analysis - Development",
    version="1.0.0-dev"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "AWSNoc IA IA - Development Environment",
        "status": "running",
        "version": "1.0.0-dev"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AWSNoc IA IA",
        "environment": "development",
        "version": "1.0.0"
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard"""
    try:
        with open("dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/simple", response_class=HTMLResponse)
async def get_simple_dashboard():
    """Serve the simple dashboard"""
    try:
        with open("simple-dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Simple dashboard not found")

@app.get("/api/v1/test/bedrock")
async def test_bedrock():
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-2')
        
        # Test with a simple prompt
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": "Hello! This is a test."}],
                "max_tokens": 100,
                "temperature": 0.1
            })
        )
        
        result = json.loads(response['body'].read())
        
        return {
            "status": "success",
            "message": "Bedrock is working!",
            "response": result['content'][0]['text']
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Bedrock test failed: {str(e)}"
        }

@app.post("/api/v1/analyze")
async def analyze_log(log_data: dict):
    """Simple log analysis endpoint"""
    try:
        message = log_data.get('message', '')
        service = log_data.get('service', 'unknown')
        
        # Simple analysis logic for development
        severity = "LOW"
        if any(word in message.lower() for word in ['error', 'fail', 'exception']):
            severity = "HIGH"
        elif any(word in message.lower() for word in ['warning', 'warn']):
            severity = "MEDIUM"
            
        return {
            "severity": severity,
            "confidence": 0.8,
            "category": "application",
            "summary": f"Log analysis for {service}: {severity} severity detected",
            "service": service,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize database connection on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database connection and tables"""
    if db_manager.connect():
        db_manager.init_tables()
        print("Database connected and initialized successfully")
    else:
        print("Failed to connect to database")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    db_manager.disconnect()
    print("Database connection closed")

# AWS Account Management Endpoints
@app.post("/api/v1/accounts")
async def create_account(account: AWSAccount, background_tasks: BackgroundTasks):
    """Create a new AWS account for monitoring"""
    try:
        # Validate AWS credentials
        discovery = AWSResourceDiscovery(account.access_key, account.secret_key, account.region)
        if not discovery.validate_credentials():
            raise HTTPException(status_code=400, detail="Invalid AWS credentials")
        
        # Create account in database
        account_data = {
            "name": account.name,
            "account_id": account.account_id,
            "region": account.region,
            "access_key": account.access_key,
            "secret_key": account.secret_key,
            "services": account.services,
            "status": account.status
        }
        
        account_id = db_manager.create_account(account_data)
        if not account_id:
            raise HTTPException(status_code=500, detail="Failed to create account in database")
        
        # Schedule background resource discovery
        background_tasks.add_task(discover_and_save_resources, account_id, account_data)
        
        return {
            "status": "success",
            "message": "Account created successfully",
            "account_id": account_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")

@app.get("/api/v1/accounts")
async def list_accounts():
    """List all AWS accounts"""
    try:
        accounts = db_manager.get_accounts()
        
        # Remove sensitive data from response
        for account in accounts:
            account.pop('access_key', None)
            account.pop('secret_key', None)
        
        return {"accounts": accounts}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")

@app.get("/api/v1/accounts/{account_id}")
async def get_account(account_id: int):
    """Get specific AWS account details"""
    try:
        account = db_manager.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Remove sensitive data
        account.pop('access_key', None)
        account.pop('secret_key', None)
        
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch account: {str(e)}")

@app.delete("/api/v1/accounts/{account_id}")
async def delete_account(account_id: int):
    """Delete AWS account"""
    try:
        if not db_manager.get_account(account_id):
            raise HTTPException(status_code=404, detail="Account not found")
        
        success = db_manager.delete_account(account_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete account")
        
        return {"status": "success", "message": "Account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")

@app.get("/api/v1/accounts/{account_id}/resources")
async def list_account_resources(account_id: int):
    """List AWS resources for an account"""
    try:
        account = db_manager.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        resources = db_manager.get_resources(account_id)
        
        return {
            "account_id": account_id,
            "account_name": account.get('name'),
            "resources": resources
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch resources: {str(e)}")

@app.post("/api/v1/accounts/{account_id}/resources/refresh")
async def refresh_account_resources(account_id: int, background_tasks: BackgroundTasks):
    """Refresh AWS resources for an account"""
    try:
        account = db_manager.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Schedule background resource discovery
        background_tasks.add_task(discover_and_save_resources, account_id, account)
        
        return {
            "status": "success",
            "message": "Resource refresh started",
            "account_id": account_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh resources: {str(e)}")

@app.get("/api/v1/accounts/{account_id}/monitoring")
async def get_monitoring_status(account_id: int):
    """Get monitoring status for an account"""
    try:
        account = db_manager.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        resources = db_manager.get_resources(account_id)
        alerts = db_manager.get_alerts(account_id, active_only=True)
        
        # Count resources by type
        resource_counts = {}
        health_status = {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0}
        
        for resource in resources:
            resource_type = resource['resource_type']
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
            
            # Count health status
            health = resource.get('metadata', {}).get('health_status', 'unknown')
            if health in health_status:
                health_status[health] += 1
            else:
                health_status['unknown'] += 1
        
        # Count alerts by severity
        alert_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for alert in alerts:
            severity = alert.get('severity', 'low')
            if severity in alert_counts:
                alert_counts[severity] += 1
        
        return {
            "account_id": account_id,
            "account_name": account.get('name'),
            "status": account.get('status'),
            "last_check": datetime.now().isoformat(),
            "resource_counts": resource_counts,
            "total_resources": len(resources),
            "health_status": health_status,
            "active_alerts": len(alerts),
            "alert_counts": alert_counts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch monitoring status: {str(e)}")

# Alerts Endpoints
@app.get("/api/v1/alerts")
async def list_all_alerts(active_only: bool = True):
    """List all alerts across accounts"""
    try:
        alerts = db_manager.get_alerts(active_only=active_only)
        return {"alerts": alerts}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

@app.get("/api/v1/accounts/{account_id}/alerts")
async def list_account_alerts(account_id: int, active_only: bool = True):
    """List alerts for a specific account"""
    try:
        account = db_manager.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        alerts = db_manager.get_alerts(account_id=account_id, active_only=active_only)
        return {
            "account_id": account_id,
            "alerts": alerts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

@app.post("/api/v1/accounts/{account_id}/alerts")
async def create_alert(account_id: int, alert: AlertCreate, background_tasks: BackgroundTasks):
    """Create a new alert for a resource"""
    try:
        account = db_manager.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Create alert in database
        alert_data = {
            "account_id": account_id,
            "resource_id": alert.resource_id,
            "resource_type": alert.resource_type,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description
        }
        
        alert_id = db_manager.create_alert(alert_data)
        if not alert_id:
            raise HTTPException(status_code=500, detail="Failed to create alert")
        
        # Schedule AI analysis for the alert
        background_tasks.add_task(analyze_alert_with_ai, alert_id, account_id, alert_data)
        
        return {
            "status": "success",
            "message": "Alert created successfully",
            "alert_id": alert_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")

@app.get("/api/v1/resources/{resource_id}/analyze")
async def analyze_resource(resource_id: str, account_id: int, background_tasks: BackgroundTasks):
    """Analyze a specific resource with AI"""
    try:
        account = db_manager.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        resources = db_manager.get_resources(account_id)
        resource = next((r for r in resources if r['resource_id'] == resource_id), None)
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Schedule AI analysis
        background_tasks.add_task(analyze_resource_with_ai, resource, account_id)
        
        return {
            "status": "success",
            "message": "Resource analysis started",
            "resource_id": resource_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze resource: {str(e)}")

# Background Tasks
async def discover_and_save_resources(account_id: int, account_data: dict):
    """Background task to discover and save AWS resources"""
    try:
        print(f"Starting resource discovery for account {account_id}")
        
        # Create discovery service
        discovery = AWSResourceDiscovery(
            account_data['access_key'],
            account_data['secret_key'],
            account_data['region']
        )
        
        # Discover all resources
        resources = discovery.discover_all_resources()
        
        print(f"Discovered {len(resources)} resources for account {account_id}")
        
        # Save resources to database
        if resources:
            success = db_manager.save_resources(account_id, resources)
            if success:
                print(f"Successfully saved {len(resources)} resources for account {account_id}")
                
                # Analyze resources for potential issues
                await analyze_resources_for_alerts(account_id, resources)
            else:
                print(f"Failed to save resources for account {account_id}")
        
    except Exception as e:
        print(f"Error in resource discovery for account {account_id}: {e}")

async def analyze_resources_for_alerts(account_id: int, resources: List[Dict]):
    """Analyze resources and create alerts for unhealthy ones"""
    try:
        print(f"Analyzing {len(resources)} resources for alerts")
        
        unhealthy_resources = [
            r for r in resources 
            if r.get('metadata', {}).get('health_status') in ['unhealthy', 'critical']
        ]
        
        for resource in unhealthy_resources:
            # Create alert for unhealthy resource
            alert_data = {
                "account_id": account_id,
                "resource_id": resource['resource_id'],
                "resource_type": resource['resource_type'],
                "alert_type": "health_check",
                "severity": "high" if resource.get('metadata', {}).get('health_status') == 'critical' else "medium",
                "title": f"{resource['resource_type']} {resource['name']} is unhealthy",
                "description": f"Resource {resource['name']} ({resource['resource_id']}) failed health check"
            }
            
            alert_id = db_manager.create_alert(alert_data)
            if alert_id:
                print(f"Created alert {alert_id} for unhealthy resource {resource['resource_id']}")
                
                # Schedule AI analysis for the alert
                await analyze_alert_with_ai(alert_id, account_id, alert_data)
        
    except Exception as e:
        print(f"Error analyzing resources for alerts: {e}")

async def analyze_alert_with_ai(alert_id: int, account_id: int, alert_data: dict):
    """Background task to analyze alert with AI"""
    try:
        print(f"Starting AI analysis for alert {alert_id}")
        
        # Get account details
        account = db_manager.get_account(account_id)
        if not account:
            print(f"Account {account_id} not found for alert analysis")
            return
        
        # Find the resource
        resources = db_manager.get_resources(account_id)
        resource = next((r for r in resources if r['resource_id'] == alert_data['resource_id']), None)
        
        if not resource:
            print(f"Resource {alert_data['resource_id']} not found for alert analysis")
            return
        
        # Generate AI recommendations
        recommendations = ai_service.generate_alert_recommendations(
            resource, 
            alert_data['alert_type'], 
            alert_data
        )
        
        print(f"Generated AI recommendations for alert {alert_id}")
        
        # Here you could update the alert with AI analysis results
        # For now, we'll just log the recommendations
        print(f"AI Recommendations for alert {alert_id}: {recommendations.get('summary', 'No summary available')}")
        
    except Exception as e:
        print(f"Error in AI analysis for alert {alert_id}: {e}")

async def analyze_resource_with_ai(resource: dict, account_id: int):
    """Background task to analyze a resource with AI"""
    try:
        print(f"Starting AI analysis for resource {resource['resource_id']}")
        
        # Perform AI health analysis
        analysis = ai_service.analyze_resource_health(resource)
        
        print(f"AI Analysis for resource {resource['resource_id']}: {analysis.get('health_status', 'unknown')}")
        
        # If critical issues found, create alerts
        if analysis.get('health_status') == 'critical':
            for issue in analysis.get('issues', []):
                if issue.get('severity') in ['high', 'critical']:
                    alert_data = {
                        "account_id": account_id,
                        "resource_id": resource['resource_id'],
                        "resource_type": resource['resource_type'],
                        "alert_type": issue.get('type', 'unknown'),
                        "severity": issue.get('severity', 'medium'),
                        "title": issue.get('description', 'AI detected critical issue'),
                        "description": issue.get('impact', 'Critical issue detected by AI analysis'),
                        "ai_analysis": analysis
                    }
                    
                    alert_id = db_manager.create_alert(alert_data)
                    if alert_id:
                        print(f"Created AI-generated alert {alert_id} for resource {resource['resource_id']}")
        
    except Exception as e:
        print(f"Error in AI resource analysis: {e}")

# Helper functions
def validate_aws_credentials(access_key: str, secret_key: str, region: str) -> bool:
    """Validate AWS credentials"""
    try:
        client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        client.get_caller_identity()
        return True
    except ClientError:
        return False

def get_aws_resources(account: AWSAccount) -> List[Dict]:
    """Get AWS resources for monitoring"""
    resources = []
    
    try:
        # Create AWS session with account credentials
        session = boto3.Session(
            aws_access_key_id=account.access_key,
            aws_secret_access_key=account.secret_key,
            region_name=account.region
        )
        
        # EC2 Instances
        if "EC2" in account.services:
            ec2 = session.client('ec2')
            try:
                response = ec2.describe_instances()
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        name = 'N/A'
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                        
                        resources.append({
                            'resource_type': 'EC2',
                            'resource_id': instance['InstanceId'],
                            'name': name,
                            'status': instance['State']['Name'],
                            'region': account.region,
                            'created_at': instance['LaunchTime'].isoformat() if 'LaunchTime' in instance else None
                        })
            except ClientError as e:
                print(f"Error fetching EC2 instances: {e}")
        
        # RDS Instances
        if "RDS" in account.services:
            rds = session.client('rds')
            try:
                response = rds.describe_db_instances()
                for db in response['DBInstances']:
                    resources.append({
                        'resource_type': 'RDS',
                        'resource_id': db['DBInstanceIdentifier'],
                        'name': db['DBInstanceIdentifier'],
                        'status': db['DBInstanceStatus'],
                        'region': account.region,
                        'created_at': db['InstanceCreateTime'].isoformat() if 'InstanceCreateTime' in db else None
                    })
            except ClientError as e:
                print(f"Error fetching RDS instances: {e}")
        
        # S3 Buckets
        if "S3" in account.services:
            s3 = session.client('s3')
            try:
                response = s3.list_buckets()
                for bucket in response['Buckets']:
                    resources.append({
                        'resource_type': 'S3',
                        'resource_id': bucket['Name'],
                        'name': bucket['Name'],
                        'status': 'active',
                        'region': account.region,
                        'created_at': bucket['CreationDate'].isoformat() if 'CreationDate' in bucket else None
                    })
            except ClientError as e:
                print(f"Error fetching S3 buckets: {e}")
        
    except Exception as e:
        print(f"Error getting AWS resources: {e}")
    
    return resources

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

