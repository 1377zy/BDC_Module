import os
import shutil
import sqlite3
import json
import datetime
import logging
import threading
import time
from flask import current_app

def backup_database():
    """Create a backup of the SQLite database"""
    app = current_app._get_current_object()
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        app.logger.error(f"Database file not found at {db_path}")
        return False
    
    backup_dir = app.config.get('BACKUP_DIRECTORY', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'app_backup_{timestamp}.db')
    
    try:
        # Create connection to source database
        source = sqlite3.connect(db_path)
        # Create connection to backup database
        backup = sqlite3.connect(backup_path)
        
        # Backup database
        source.backup(backup)
        
        # Close connections
        source.close()
        backup.close()
        
        app.logger.info(f"Database backup created at {backup_path}")
        
        # Clean up old backups (keep last 10)
        backup_files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
                              if f.endswith('.db')])
        
        if len(backup_files) > 10:
            for old_backup in backup_files[:-10]:
                os.remove(old_backup)
                app.logger.info(f"Removed old backup: {old_backup}")
                
        return True
    except Exception as e:
        app.logger.error(f"Database backup failed: {str(e)}")
        return False

def backup_json_data():
    """Create a backup of JSON data files"""
    app = current_app._get_current_object()
    data_dir = os.path.join(app.root_path, '..', 'data')
    
    if not os.path.exists(data_dir):
        app.logger.warning(f"Data directory not found at {data_dir}")
        return False
    
    backup_dir = app.config.get('BACKUP_DIRECTORY', 'backups')
    json_backup_dir = os.path.join(backup_dir, 'json_data')
    os.makedirs(json_backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(json_backup_dir, f'json_backup_{timestamp}')
    os.makedirs(backup_path, exist_ok=True)
    
    try:
        # Copy all JSON files
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        for file in json_files:
            src = os.path.join(data_dir, file)
            dst = os.path.join(backup_path, file)
            shutil.copy2(src, dst)
            
        app.logger.info(f"JSON data backup created at {backup_path}")
        
        # Clean up old backups (keep last 10)
        backup_dirs = sorted([os.path.join(json_backup_dir, d) for d in os.listdir(json_backup_dir) 
                             if os.path.isdir(os.path.join(json_backup_dir, d))])
        
        if len(backup_dirs) > 10:
            for old_backup in backup_dirs[:-10]:
                shutil.rmtree(old_backup)
                app.logger.info(f"Removed old JSON backup: {old_backup}")
                
        return True
    except Exception as e:
        app.logger.error(f"JSON data backup failed: {str(e)}")
        return False

def backup_scheduler():
    """Background thread to schedule regular backups"""
    app = current_app._get_current_object()
    interval_hours = app.config.get('BACKUP_INTERVAL_HOURS', 24)
    
    while True:
        with app.app_context():
            app.logger.info("Running scheduled database backup")
            backup_database()
            backup_json_data()
            
        # Sleep for the configured interval
        time.sleep(interval_hours * 3600)

def init_backup_scheduler(app):
    """Initialize the backup scheduler"""
    if not app.config.get('BACKUP_ENABLED', False):
        return
    
    # Create initial backup
    with app.app_context():
        app.logger.info("Creating initial database backup")
        backup_database()
        backup_json_data()
    
    # Start scheduler in a background thread
    scheduler_thread = threading.Thread(target=backup_scheduler, daemon=True)
    scheduler_thread.start()
    app.logger.info(f"Backup scheduler started with interval of {app.config.get('BACKUP_INTERVAL_HOURS', 24)} hours")
