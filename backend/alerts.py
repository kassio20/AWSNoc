from fastapi import HTTPException
from datetime import datetime
import boto3

def analyze_resource_health(resource):
    """Analyze a resource and return alert information"""
    resource_type = resource.get("resource_type", "")
    resource_id = resource.get("resource_id", "")
    status = resource.get("status", "")
    
    # Analisar diferentes tipos de recursos
    if resource_type == "target_group":
        if "0/" in status and "healthy" in status:
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "severity": "critical",
                "title": f"Target Group {resource_id} - No Healthy Targets",
                "description": f"Target group has no healthy targets: {status}",
                "affected_service": "Load Balancer",
                "impact": "Service unavailable - traffic cannot be routed",
                "detected_at": datetime.now().isoformat()
            }
        elif "/" in status and "healthy" in status:
            try:
                healthy_count = int(status.split("/")[0])
                total_count = int(status.split("/")[1].split(" ")[0])
                if healthy_count < total_count:
                    return {
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "severity": "warning",
                        "title": f"Target Group {resource_id} - Partial Healthy Targets",
                        "description": f"Target group has degraded health: {status}",
                        "affected_service": "Load Balancer",
                        "impact": "Reduced capacity - some targets are unhealthy",
                        "detected_at": datetime.now().isoformat()
                    }
            except (ValueError, IndexError):
                pass
    
    elif resource_type == "instance":
        if status != "running":
            severity = "critical" if status in ["stopped", "terminated"] else "warning"
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "severity": severity,
                "title": f"EC2 Instance {resource_id} - {status.title()}",
                "description": f"Instance is in {status} state",
                "affected_service": "Compute",
                "impact": "Service disruption - instance not available",
                "detected_at": datetime.now().isoformat()
            }
    
    elif resource_type == "database":
        if status != "available":
            severity = "critical" if status in ["stopped", "failed"] else "warning"
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "severity": severity,
                "title": f"RDS Database {resource_id} - {status.title()}",
                "description": f"Database is in {status} state",
                "affected_service": "Database",
                "impact": "Data access disruption - database not available",
                "detected_at": datetime.now().isoformat()
            }
    
    # Recurso saudável
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "severity": "healthy",
        "title": f"{resource_type.title()} {resource_id} - Healthy",
        "description": f"Resource is operating normally: {status}",
        "affected_service": "N/A",
        "impact": "No impact",
        "detected_at": datetime.now().isoformat()
    }

async def generate_ai_analysis(resource, alert_info, bedrock_client):
    """Generate AI analysis for a resource issue"""
    try:
        prompt = f"""Analyze this AWS resource issue and provide detailed technical analysis:

Resource Type: {resource.get('resource_type')}
Resource ID: {resource.get('resource_id')}
Current Status: {resource.get('status')}
Alert Severity: {alert_info['severity']}
Issue Description: {alert_info['description']}

Please provide:
1. Root cause analysis
2. Potential impacts on the system
3. Steps to investigate further
4. Preventive measures

Be specific and technical in your analysis."""

        response = bedrock_client.converse(
            modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
            }]
        )
        
        return response["output"]["message"]["content"][0]["text"]
    except Exception as e:
        return f"AI analysis temporarily unavailable: {str(e)}"

def generate_recommendations(resource, alert_info):
    """Generate actionable recommendations for fixing the issue"""
    recommendations = []
    resource_id = resource.get('resource_id', '')
    
    if alert_info["resource_type"] == "target_group":
        if "0/" in resource.get("status", ""):
            recommendations = [
                {
                    "action": "Check target health",
                    "command": f"aws elbv2 describe-target-health --target-group-arn {resource_id}",
                    "description": "Verify which targets are unhealthy and why"
                },
                {
                    "action": "Check application logs",
                    "command": "Check application logs on the target instances",
                    "description": "Look for application errors or startup issues"
                },
                {
                    "action": "Verify health check configuration",
                    "command": f"aws elbv2 describe-target-groups --target-group-arns {resource_id}",
                    "description": "Check if health check path and settings are correct"
                },
                {
                    "action": "Test health check manually",
                    "command": "curl -I http://target-ip:port/health-check-path",
                    "description": "Manually test the health check endpoint"
                }
            ]
    
    elif alert_info["resource_type"] == "instance":
        if resource.get("status") == "stopped":
            recommendations = [
                {
                    "action": "Start the instance",
                    "command": f"aws ec2 start-instances --instance-ids {resource_id}",
                    "description": "Start the stopped EC2 instance"
                },
                {
                    "action": "Check instance logs",
                    "command": f"aws ec2 get-console-output --instance-id {resource_id}",
                    "description": "Review console output for startup issues"
                }
            ]
    
    elif alert_info["resource_type"] == "database":
        if resource.get("status") != "available":
            recommendations = [
                {
                    "action": "Check database status",
                    "command": f"aws rds describe-db-instances --db-instance-identifier {resource_id}",
                    "description": "Get detailed database status information"
                },
                {
                    "action": "Review database logs",
                    "command": f"aws rds describe-db-log-files --db-instance-identifier {resource_id}",
                    "description": "Check database error logs"
                }
            ]
    
    return recommendations
