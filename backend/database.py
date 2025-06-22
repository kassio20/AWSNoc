import psycopg2
import psycopg2.extras
import json
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self):
        self.host = 'selectnoc-dev-database.cjeqe6pc2viw.us-east-2.rds.amazonaws.com'
        self.port = 5432
        self.database = 'selectnoc'
        self.user = 'selectnoc_admin'
        self.password = 'Dy6uGR1UVasJEp7D'
        self.init_database()
    
    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                account_id VARCHAR(255) UNIQUE NOT NULL,
                region VARCHAR(50) NOT NULL,
                access_key VARCHAR(255) NOT NULL,
                secret_key VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create resources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id SERIAL PRIMARY KEY,
                account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
                resource_type VARCHAR(100) NOT NULL,
                resource_id VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                status VARCHAR(100),
                region VARCHAR(50),
                availability_zone VARCHAR(50),
                instance_type VARCHAR(50),
                vpc_id VARCHAR(50),
                subnet_id VARCHAR(50),
                security_groups TEXT,
                tags TEXT,
                metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_id, resource_type, resource_id)
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print('PostgreSQL tables created successfully!')
    
    def add_account(self, account_data: Dict) -> int:
        """Add a new account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO accounts (name, account_id, region, access_key, secret_key, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            account_data['name'],
            account_data['account_id'],
            account_data['region'],
            account_data['access_key'],
            account_data['secret_key'],
            account_data.get('status', 'active')
        ))
        
        account_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return account_id
    
    def get_accounts(self) -> List[Dict]:
        """Get all accounts"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute('SELECT * FROM accounts ORDER BY created_at DESC')
        accounts = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        return accounts
    
    def get_account_by_id(self, account_id: int) -> Optional[Dict]:
        """Get account by ID"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (account_id,))
        account = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return dict(account) if account else None
    
    def save_resources(self, account_id: int, resources: List[Dict]):
        """Save resources for an account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Clear existing resources for this account
        cursor.execute('DELETE FROM resources WHERE account_id = %s', (account_id,))
        
        # Insert new resources
        for resource in resources:
            cursor.execute('''
                INSERT INTO resources (
                    account_id, resource_type, resource_id, name, status, region,
                    availability_zone, instance_type, vpc_id, subnet_id,
                    security_groups, tags, metrics, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (account_id, resource_type, resource_id) 
                DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                account_id,
                resource.get('resource_type'),
                resource.get('resource_id'),
                resource.get('name'),
                resource.get('status'),
                resource.get('region'),
                resource.get('availability_zone'),
                resource.get('instance_type'),
                resource.get('vpc_id'),
                resource.get('subnet_id'),
                json.dumps(resource.get('security_groups', [])),
                json.dumps(resource.get('tags', {})),
                json.dumps(resource.get('metrics', {})),
                resource.get('created_at', datetime.now())
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_resources(self, account_id: int) -> List[Dict]:
        """Get resources for an account"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute('SELECT * FROM resources WHERE account_id = %s ORDER BY created_at DESC', (account_id,))
        resources = []
        
        for row in cursor.fetchall():
            resource = dict(row)
            # Parse JSON fields
            resource['security_groups'] = json.loads(resource.get('security_groups', '[]'))
            resource['tags'] = json.loads(resource.get('tags', '{}'))
            resource['metrics'] = json.loads(resource.get('metrics', '{}'))
            resources.append(resource)
        
        cursor.close()
        conn.close()
        return resources

