"""Add report templates

Revision ID: add_report_templates
Revises: add_archived_fields
Create Date: 2025-03-02 17:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_report_templates'
down_revision = 'add_archived_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create report_template table
    op.create_table('report_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(length=64), nullable=False),
        sa.Column('header_html', sa.Text(), nullable=True),
        sa.Column('footer_html', sa.Text(), nullable=True),
        sa.Column('css_styles', sa.Text(), nullable=True),
        sa.Column('include_logo', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('include_timestamp', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('include_page_numbers', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add template_id column to scheduled_report table
    op.add_column('scheduled_report', sa.Column('template_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_scheduled_report_template', 'scheduled_report', 'report_template', ['template_id'], ['id'])
    
    # Create default templates for each report type
    op.execute("""
    INSERT INTO report_template (name, description, report_type, include_logo, include_timestamp, include_page_numbers, is_default)
    VALUES 
    ('Default Inventory Template', 'Default template for inventory reports', 'inventory', 1, 1, 1, 1),
    ('Default Leads Template', 'Default template for lead reports', 'leads', 1, 1, 1, 1),
    ('Default Sales Template', 'Default template for sales reports', 'sales', 1, 1, 1, 1),
    ('Default Performance Template', 'Default template for performance reports', 'performance', 1, 1, 1, 1)
    """)


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_scheduled_report_template', 'scheduled_report', type_='foreignkey')
    
    # Remove template_id column from scheduled_report
    op.drop_column('scheduled_report', 'template_id')
    
    # Drop report_template table
    op.drop_table('report_template')
