"""
Lead Management Upgrade Migration Script

This script adds the following features to the lead management system:
1. Lead scoring and lifecycle stages
2. Lead activity tracking
3. Automated follow-up sequences

Run this script with: python -m migrations.lead_management_upgrade
"""

import sys
import os
import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db, create_app
from app.models import Lead, User

def upgrade_database():
    """Perform the database upgrade"""
    app = create_app()
    with app.app_context():
        # Check if the columns already exist to avoid errors
        inspector = db.inspect(db.engine)
        lead_columns = [column['name'] for column in inspector.get_columns('lead')]
        
        # Add new columns to Lead table if they don't exist
        new_columns = {
            'score': db.Column(db.Integer, default=0),
            'last_activity_date': db.Column(db.DateTime, nullable=True),
            'follow_up_date': db.Column(db.DateTime, nullable=True),
            'follow_up_type': db.Column(db.String(20), nullable=True),
            'lifecycle_stage': db.Column(db.String(30), default='new')
        }
        
        for column_name, column_def in new_columns.items():
            if column_name not in lead_columns:
                print(f"Adding column {column_name} to Lead table")
                db.engine.execute(f'ALTER TABLE lead ADD COLUMN {column_name} {get_column_type(column_def)}')
        
        # Create new tables if they don't exist
        if not db.engine.dialect.has_table(db.engine, 'lead_activity'):
            print("Creating LeadActivity table")
            db.engine.execute('''
                CREATE TABLE lead_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    activity_type VARCHAR(30),
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    performed_by_id INTEGER,
                    related_entity_type VARCHAR(30),
                    related_entity_id INTEGER,
                    FOREIGN KEY (lead_id) REFERENCES lead (id),
                    FOREIGN KEY (performed_by_id) REFERENCES user (id)
                )
            ''')
        
        if not db.engine.dialect.has_table(db.engine, 'lead_follow_up_sequence'):
            print("Creating LeadFollowUpSequence table")
            db.engine.execute('''
                CREATE TABLE lead_follow_up_sequence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(64),
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_by_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    trigger_type VARCHAR(30),
                    lead_source VARCHAR(64),
                    FOREIGN KEY (created_by_id) REFERENCES user (id)
                )
            ''')
        
        if not db.engine.dialect.has_table(db.engine, 'follow_up_step'):
            print("Creating FollowUpStep table")
            db.engine.execute('''
                CREATE TABLE follow_up_step (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence_id INTEGER,
                    step_number INTEGER,
                    delay_days INTEGER DEFAULT 0,
                    delay_hours INTEGER DEFAULT 0,
                    action_type VARCHAR(20),
                    template_id INTEGER,
                    task_description TEXT,
                    task_assignee_role VARCHAR(20),
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (sequence_id) REFERENCES lead_follow_up_sequence (id)
                )
            ''')
        
        if not db.engine.dialect.has_table(db.engine, 'lead_sequence_assignment'):
            print("Creating LeadSequenceAssignment table")
            db.engine.execute('''
                CREATE TABLE lead_sequence_assignment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    sequence_id INTEGER,
                    current_step INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_step_completed_at DATETIME,
                    next_step_due_at DATETIME,
                    completed_at DATETIME,
                    FOREIGN KEY (lead_id) REFERENCES lead (id),
                    FOREIGN KEY (sequence_id) REFERENCES lead_follow_up_sequence (id)
                )
            ''')
        
        # Initialize lead scores and lifecycle stages for existing leads
        leads = Lead.query.all()
        print(f"Updating {len(leads)} existing leads with scores and lifecycle stages")
        for lead in leads:
            lead.calculate_score()
            lead.update_lifecycle_stage()
        
        db.session.commit()
        print("Migration completed successfully!")

def get_column_type(column):
    """Convert SQLAlchemy column type to SQL string for ALTER TABLE"""
    if isinstance(column.type, Integer):
        return "INTEGER" + (" DEFAULT 0" if column.default and column.default.arg == 0 else "")
    elif isinstance(column.type, String):
        return f"VARCHAR({column.type.length})" + (f" DEFAULT '{column.default.arg}'" if column.default else "")
    elif isinstance(column.type, Text):
        return "TEXT"
    elif isinstance(column.type, Boolean):
        return "BOOLEAN" + (" DEFAULT 1" if column.default and column.default.arg else " DEFAULT 0")
    elif isinstance(column.type, DateTime):
        return "DATETIME" + (" DEFAULT CURRENT_TIMESTAMP" if column.default else "")
    else:
        return "TEXT"  # Default fallback

if __name__ == '__main__':
    upgrade_database()
