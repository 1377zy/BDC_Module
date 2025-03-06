"""Add archived fields to ScheduledReport

Revision ID: add_archived_fields
Revises: 
Create Date: 2025-03-02 17:19:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_archived_fields'
down_revision = None  # Update this to the actual previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Add archived and archive_path columns to scheduled_report table
    op.add_column('scheduled_report', sa.Column('archived', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('scheduled_report', sa.Column('archive_path', sa.String(length=255), nullable=True))
    
    # Update existing records to set archived=False
    op.execute("UPDATE scheduled_report SET archived = 0 WHERE archived IS NULL")
    
    # Set the column to not nullable after updating existing records
    op.alter_column('scheduled_report', 'archived', nullable=False, existing_type=sa.Boolean(), server_default='0')


def downgrade():
    # Remove the columns
    op.drop_column('scheduled_report', 'archive_path')
    op.drop_column('scheduled_report', 'archived')
