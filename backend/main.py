from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import boto3
import asyncio
from database import DatabaseManager

app = FastAPI(title="SelectNOC IA", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
db_manager = DatabaseManager()

# Pydantic Models
class AWSAccount(BaseModel):
    name: str
    account_id: str
    region: str
    access_key: str
    secret_key: str

@app.get("/")
async def root():
    return {"message": "SelectNOC IA - Monitoring AWS Resources", "status": "running"}

@app.get("/api/v1/accounts")
async def get_accounts():
    accounts = db_manager.get_accounts()
    return {"accounts": accounts}

@app.post("/api/v1/accounts")
async def create_account(account: AWSAccount):
    # Validate AWS credentials
    try:
        session = boto3.Session(
            aws_access_key_id=account.access_key,
            aws_secret_access_key=account.secret_key,
            region_name=account.region
        )
        sts = session.client('sts')
        sts.get_caller_identity()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid AWS credentials")
    
    # Save to RDS
    account_data = {
        "name": account.name,
        "account_id": account.account_id,
        "region": account.region,
        "access_key": account.access_key,
        "secret_key": account.secret_key,
        "status": "active"
    }
    
    try:
        account_id = db_manager.add_account(account_data)
        
        # Start resource discovery
        asyncio.create_task(discover_resources(account_id, account))
        
        return {"status": "success", "message": "Account created successfully", "account_id": account_id}
    except Exception as e:
        if "duplicate key" in str(e):
            raise HTTPException(status_code=400, detail="Account already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/v1/accounts/{account_id}/resources")
async def get_account_resources(account_id: int):
    try:
        account = db_manager.get_account_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        resources = db_manager.get_resources(account_id)
        
        return {
            "account_id": account_id,
            "account_name": account["name"],
            "resources": resources
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

async def discover_resources(account_id: int, account: AWSAccount):
    """Discover AWS resources for an account"""
    try:
        session = boto3.Session(
            aws_access_key_id=account.access_key,
            aws_secret_access_key=account.secret_key,
            region_name=account.region
        )
        
        resources = []
        
        # EC2 instances
        try:
            ec2 = session.client('ec2')
            instances = ec2.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    resources.append({
                        "resource_type": "EC2",
                        "resource_id": instance['InstanceId'],
                        "name": next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), instance['InstanceId']),
                        "status": instance['State']['Name'],
                        "region": account.region,
                        "availability_zone": instance.get('Placement', {}).get('AvailabilityZone'),
                        "instance_type": instance.get('InstanceType'),
                        "created_at": datetime.now()
                    })
        except Exception as e:
            print(f"Error discovering EC2: {e}")
        
        # ELB Target Groups
        try:
            elbv2 = session.client('elbv2')
            target_groups = elbv2.describe_target_groups()
            for tg in target_groups['TargetGroups']:
                health = elbv2.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
                healthy_count = len([t for t in health['TargetHealthDescriptions'] if t['TargetHealth']['State'] == 'healthy'])
                total_count = len(health['TargetHealthDescriptions'])
                
                resources.append({
                    "resource_type": "TargetGroup",
                    "resource_id": tg['TargetGroupArn'].split('/')[-1],
                    "name": tg['TargetGroupName'],
                    "status": f"{healthy_count}/{total_count} healthy",
                    "region": account.region,
                    "created_at": datetime.now(),
                    "metrics": {"healthy_targets": healthy_count, "total_targets": total_count}
                })
        except Exception as e:
            print(f"Error discovering Target Groups: {e}")
        
        # Save resources to database
        if resources:
            db_manager.save_resources(account_id, resources)
            print(f"✅ Discovered {len(resources)} resources for account {account.name}")
        else:
            print(f"⚠️ No resources found for account {account.name}")
        
    except Exception as e:
        print(f"❌ Error discovering resources: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
