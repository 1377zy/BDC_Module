"""add usage_count to report templates

Revision ID: add_usage_count_to_templates
Revises: 
Create Date: 2025-03-02 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_usage_count_to_templates'
down_revision = None  # Update this with the previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Add usage_count column to report_template table
    op.add_column('report_template', sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    # Remove usage_count column from report_template table
    op.drop_column('report_template', 'usage_count')
