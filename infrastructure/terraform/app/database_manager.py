import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Dict, Optional
import json

class DatabaseManager:
    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            )
            self.connection.autocommit = True
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def init_tables(self):
        """Initialize database tables"""
        if not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # AWS Accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aws_accounts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    account_id VARCHAR(50) NOT NULL UNIQUE,
                    region VARCHAR(50) NOT NULL,
                    access_key VARCHAR(255) NOT NULL,
                    secret_key VARCHAR(255) NOT NULL,
                    services JSONB DEFAULT '[]',
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # AWS Resources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aws_resources (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER REFERENCES aws_accounts(id),
                    resource_type VARCHAR(100) NOT NULL,
                    resource_id VARCHAR(255) NOT NULL,
                    name VARCHAR(255),
                    status VARCHAR(100),
                    region VARCHAR(50),
                    metadata JSONB DEFAULT '{}',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP
                )
            """)
            
            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER REFERENCES aws_accounts(id),
                    resource_id VARCHAR(255),
                    resource_type VARCHAR(100),
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    description TEXT,
                    status VARCHAR(50) DEFAULT 'active',
                    ai_analysis JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)
            
            # Logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_logs (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER REFERENCES aws_accounts(id),
                    resource_id VARCHAR(255),
                    resource_type VARCHAR(100),
                    log_group VARCHAR(255),
                    log_stream VARCHAR(255),
                    timestamp TIMESTAMP,
                    level VARCHAR(20),
                    message TEXT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error initializing tables: {e}")
            return False
    
    def create_account(self, account_data: dict) -> Optional[int]:
        """Create a new AWS account"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO aws_accounts (name, account_id, region, access_key, secret_key, services, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                account_data['name'],
                account_data['account_id'],
                account_data['region'],
                account_data['access_key'],
                account_data['secret_key'],
                json.dumps(account_data.get('services', [])),
                account_data.get('status', 'active')
            ))
            
            account_id = cursor.fetchone()[0]
            cursor.close()
            return account_id
            
        except Exception as e:
            print(f"Error creating account: {e}")
            return None
    
    def get_accounts(self) -> List[Dict]:
        """Get all AWS accounts"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT id, name, account_id, region, services, status, created_at
                FROM aws_accounts
                ORDER BY created_at DESC
            """)
            
            accounts = []
            for row in cursor.fetchall():
                account = dict(row)
                # Se services já é uma lista, mantém como está; se é string, faz parse
                if isinstance(account['services'], str):
                    account['services'] = json.loads(account['services']) if account['services'] else []
                elif account['services'] is None:
                    account['services'] = []
                accounts.append(account)
            
            cursor.close()
            return accounts
            
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []
    
    def get_account(self, account_id: int) -> Optional[Dict]:
        """Get specific AWS account"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT * FROM aws_accounts WHERE id = %s
            """, (account_id,))
            
            row = cursor.fetchone()
            if row:
                account = dict(row)
                # Se services já é uma lista, mantém como está; se é string, faz parse
                if isinstance(account['services'], str):
                    account['services'] = json.loads(account['services']) if account['services'] else []
                elif account['services'] is None:
                    account['services'] = []
                cursor.close()
                return account
            
            cursor.close()
            return None
            
        except Exception as e:
            print(f"Error getting account: {e}")
            return None
    
    def delete_account(self, account_id: int) -> bool:
        """Delete AWS account and related data"""
        try:
            cursor = self.connection.cursor()
            
            # Delete related data first
            cursor.execute("DELETE FROM alerts WHERE account_id = %s", (account_id,))
            cursor.execute("DELETE FROM resource_logs WHERE account_id = %s", (account_id,))
            cursor.execute("DELETE FROM aws_resources WHERE account_id = %s", (account_id,))
            cursor.execute("DELETE FROM aws_accounts WHERE id = %s", (account_id,))
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error deleting account: {e}")
            return False
    
    def save_resources(self, account_id: int, resources: List[Dict]) -> bool:
        """Save or update AWS resources"""
        try:
            cursor = self.connection.cursor()
            
            # Clear existing resources for this account
            cursor.execute("DELETE FROM aws_resources WHERE account_id = %s", (account_id,))
            
            # Insert new resources
            for resource in resources:
                cursor.execute("""
                    INSERT INTO aws_resources 
                    (account_id, resource_type, resource_id, name, status, region, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    account_id,
                    resource['resource_type'],
                    resource['resource_id'],
                    resource.get('name'),
                    resource.get('status'),
                    resource.get('region'),
                    json.dumps(resource.get('metadata', {})),
                    resource.get('created_at', datetime.now())
                ))
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error saving resources: {e}")
            return False
    
    def get_resources(self, account_id: int) -> List[Dict]:
        """Get AWS resources for an account"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT * FROM aws_resources 
                WHERE account_id = %s 
                ORDER BY resource_type, name
            """, (account_id,))
            
            resources = []
            for row in cursor.fetchall():
                resource = dict(row)
                resource['metadata'] = json.loads(resource['metadata']) if resource['metadata'] else {}
                resources.append(resource)
            
            cursor.close()
            return resources
            
        except Exception as e:
            print(f"Error getting resources: {e}")
            return []
    
    def create_alert(self, alert_data: dict) -> Optional[int]:
        """Create a new alert"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO alerts 
                (account_id, resource_id, resource_type, alert_type, severity, title, description, ai_analysis)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                alert_data['account_id'],
                alert_data.get('resource_id'),
                alert_data.get('resource_type'),
                alert_data['alert_type'],
                alert_data['severity'],
                alert_data['title'],
                alert_data.get('description'),
                json.dumps(alert_data.get('ai_analysis', {}))
            ))
            
            alert_id = cursor.fetchone()[0]
            cursor.close()
            return alert_id
            
        except Exception as e:
            print(f"Error creating alert: {e}")
            return None
    
    def get_alerts(self, account_id: Optional[int] = None, active_only: bool = True) -> List[Dict]:
        """Get alerts"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            query = "SELECT * FROM alerts"
            params = []
            
            conditions = []
            if account_id:
                conditions.append("account_id = %s")
                params.append(account_id)
            
            if active_only:
                conditions.append("status = 'active'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            alerts = []
            for row in cursor.fetchall():
                alert = dict(row)
                alert['ai_analysis'] = json.loads(alert['ai_analysis']) if alert['ai_analysis'] else {}
                alerts.append(alert)
            
            cursor.close()
            return alerts
            
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []

