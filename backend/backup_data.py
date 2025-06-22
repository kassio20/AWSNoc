import json
import pickle
import os
from datetime import datetime

def backup_memory_data():
    """Backup current in-memory data to files"""
    backup_dir = '/opt/selectnoc/data_backup'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Import the main module to access the data
    import sys
    sys.path.append('/opt/selectnoc/backend')
    
    try:
        import main
        
        # Backup accounts
        accounts_file = f'{backup_dir}/accounts_{timestamp}.json'
        with open(accounts_file, 'w') as f:
            # Convert account objects to dictionaries for JSON serialization
            accounts_data = {}
            for account_id, account in main.accounts_db.items():
                accounts_data[account_id] = {
                    'id': account.id,
                    'name': account.name,
                    'account_id': account.account_id,
                    'region': account.region,
                    'access_key': account.access_key,
                    'secret_key': account.secret_key,
                    'services': account.services,
                    'status': account.status,
                    'created_at': account.created_at.isoformat() if account.created_at else None
                }
            json.dump(accounts_data, f, indent=2)
        
        # Backup resources
        resources_file = f'{backup_dir}/resources_{timestamp}.json'
        with open(resources_file, 'w') as f:
            json.dump(main.resources_db, f, indent=2)
        
        # Backup metrics
        metrics_file = f'{backup_dir}/metrics_{timestamp}.json'
        with open(metrics_file, 'w') as f:
            json.dump(main.metrics_db, f, indent=2)
        
        # Create symlinks to latest
        latest_accounts = f'{backup_dir}/accounts_latest.json'
        latest_resources = f'{backup_dir}/resources_latest.json'
        latest_metrics = f'{backup_dir}/metrics_latest.json'
        
        if os.path.exists(latest_accounts):
            os.remove(latest_accounts)
        if os.path.exists(latest_resources):
            os.remove(latest_resources)
        if os.path.exists(latest_metrics):
            os.remove(latest_metrics)
            
        os.symlink(accounts_file, latest_accounts)
        os.symlink(resources_file, latest_resources)
        os.symlink(metrics_file, latest_metrics)
        
        print(f'Backup realizado com sucesso: {timestamp}')
        return True
        
    except Exception as e:
        print(f'Erro no backup: {e}')
        return False

if __name__ == '__main__':
    backup_memory_data()
