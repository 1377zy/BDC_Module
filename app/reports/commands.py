"""
Command-line utilities for the reports module
"""
import click
from flask.cli import with_appcontext
from app.reports.report_scheduler import ReportScheduler
from app import db
from app.models import ReportTemplate, User, ScheduledReport

@click.command('check-scheduled-reports')
@with_appcontext
def check_scheduled_reports_command():
    """Check for scheduled reports that need to be sent and process them."""
    click.echo('Checking for scheduled reports...')
    ReportScheduler.check_and_send_reports()
    click.echo('Finished processing scheduled reports.')

@click.command('send-report')
@click.argument('report_id', type=int)
@with_appcontext
def send_report_command(report_id):
    """Send a specific report immediately."""
    report = ScheduledReport.query.get(report_id)
    if not report:
        click.echo(f'Error: Report with ID {report_id} not found.')
        return
    
    click.echo(f'Sending report: {report.name}...')
    try:
        ReportScheduler.generate_and_send_report(report, force_send=True)
        click.echo('Report sent successfully.')
    except Exception as e:
        click.echo(f'Error sending report: {str(e)}')

@click.command('create-default-templates')
@with_appcontext
def create_default_templates_command():
    """Create default report templates for each report type if they don't exist."""
    click.echo('Creating default report templates...')
    
    # Get the first admin user to set as creator
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User.query.first()  # Fallback to any user if no admin exists
    
    if not admin:
        click.echo('Error: No users found in the system.')
        return
    
    # Define default templates for each report type
    default_templates = [
        {
            'name': 'Default Inventory Report',
            'description': 'Standard template for inventory reports with company branding',
            'report_type': 'inventory',
            'header_html': '''
                <div class="header">
                    <div class="logo">
                        <img src="{{ url_for('static', filename='img/logo.png', _external=True) }}" alt="Company Logo">
                    </div>
                    <div class="report-title">
                        <h1>{{ report_title }}</h1>
                        <p class="date-range">{{ date_range }}</p>
                    </div>
                </div>
            ''',
            'footer_html': '''
                <div class="footer">
                    <div class="company-info">
                        <p>{{ company_name }} - Confidential Report</p>
                    </div>
                    <div class="page-info">
                        <p>Page {{ page_number }} of {{ total_pages }}</p>
                        <p class="generated-at">Generated on {{ generated_at }} by {{ generated_by }}</p>
                    </div>
                </div>
            ''',
            'css_styles': '''
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                .logo img {
                    max-height: 60px;
                }
                .report-title h1 {
                    color: #2c3e50;
                    margin: 0;
                }
                .date-range {
                    color: #7f8c8d;
                    font-style: italic;
                }
                .footer {
                    display: flex;
                    justify-content: space-between;
                    font-size: 9pt;
                    color: #7f8c8d;
                    border-top: 1px solid #ddd;
                    padding-top: 5px;
                    margin-top: 20px;
                }
                .summary-box {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                .kpi {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                }
                .kpi-item {
                    flex: 0 0 30%;
                    text-align: center;
                    background-color: #fff;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 10px;
                }
                .kpi-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #3498db;
                }
                .kpi-label {
                    font-size: 12px;
                    color: #7f8c8d;
                }
            ''',
            'is_default': True
        },
        {
            'name': 'Default Leads Report',
            'description': 'Standard template for leads reports with company branding',
            'report_type': 'leads',
            'header_html': '''
                <div class="header">
                    <div class="logo">
                        <img src="{{ url_for('static', filename='img/logo.png', _external=True) }}" alt="Company Logo">
                    </div>
                    <div class="report-title">
                        <h1>{{ report_title }}</h1>
                        <p class="date-range">{{ date_range }}</p>
                    </div>
                </div>
            ''',
            'footer_html': '''
                <div class="footer">
                    <div class="company-info">
                        <p>{{ company_name }} - Confidential Report</p>
                    </div>
                    <div class="page-info">
                        <p>Page {{ page_number }} of {{ total_pages }}</p>
                        <p class="generated-at">Generated on {{ generated_at }} by {{ generated_by }}</p>
                    </div>
                </div>
            ''',
            'css_styles': '''
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #e74c3c;
                    padding-bottom: 10px;
                }
                .logo img {
                    max-height: 60px;
                }
                .report-title h1 {
                    color: #2c3e50;
                    margin: 0;
                }
                .date-range {
                    color: #7f8c8d;
                    font-style: italic;
                }
                .footer {
                    display: flex;
                    justify-content: space-between;
                    font-size: 9pt;
                    color: #7f8c8d;
                    border-top: 1px solid #ddd;
                    padding-top: 5px;
                    margin-top: 20px;
                }
                .summary-box {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                .kpi {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                }
                .kpi-item {
                    flex: 0 0 30%;
                    text-align: center;
                    background-color: #fff;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 10px;
                }
                .kpi-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #e74c3c;
                }
                .kpi-label {
                    font-size: 12px;
                    color: #7f8c8d;
                }
            ''',
            'is_default': True
        },
        {
            'name': 'Default Sales Report',
            'description': 'Standard template for sales reports with company branding',
            'report_type': 'sales',
            'header_html': '''
                <div class="header">
                    <div class="logo">
                        <img src="{{ url_for('static', filename='img/logo.png', _external=True) }}" alt="Company Logo">
                    </div>
                    <div class="report-title">
                        <h1>{{ report_title }}</h1>
                        <p class="date-range">{{ date_range }}</p>
                    </div>
                </div>
            ''',
            'footer_html': '''
                <div class="footer">
                    <div class="company-info">
                        <p>{{ company_name }} - Confidential Report</p>
                    </div>
                    <div class="page-info">
                        <p>Page {{ page_number }} of {{ total_pages }}</p>
                        <p class="generated-at">Generated on {{ generated_at }} by {{ generated_by }}</p>
                    </div>
                </div>
            ''',
            'css_styles': '''
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #27ae60;
                    padding-bottom: 10px;
                }
                .logo img {
                    max-height: 60px;
                }
                .report-title h1 {
                    color: #2c3e50;
                    margin: 0;
                }
                .date-range {
                    color: #7f8c8d;
                    font-style: italic;
                }
                .footer {
                    display: flex;
                    justify-content: space-between;
                    font-size: 9pt;
                    color: #7f8c8d;
                    border-top: 1px solid #ddd;
                    padding-top: 5px;
                    margin-top: 20px;
                }
                .summary-box {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                .kpi {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                }
                .kpi-item {
                    flex: 0 0 30%;
                    text-align: center;
                    background-color: #fff;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 10px;
                }
                .kpi-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #27ae60;
                }
                .kpi-label {
                    font-size: 12px;
                    color: #7f8c8d;
                }
            ''',
            'is_default': True
        },
        {
            'name': 'Default Performance Report',
            'description': 'Standard template for staff performance reports with company branding',
            'report_type': 'performance',
            'header_html': '''
                <div class="header">
                    <div class="logo">
                        <img src="{{ url_for('static', filename='img/logo.png', _external=True) }}" alt="Company Logo">
                    </div>
                    <div class="report-title">
                        <h1>{{ report_title }}</h1>
                        <p class="date-range">{{ date_range }}</p>
                    </div>
                </div>
            ''',
            'footer_html': '''
                <div class="footer">
                    <div class="company-info">
                        <p>{{ company_name }} - Confidential Report</p>
                    </div>
                    <div class="page-info">
                        <p>Page {{ page_number }} of {{ total_pages }}</p>
                        <p class="generated-at">Generated on {{ generated_at }} by {{ generated_by }}</p>
                    </div>
                </div>
            ''',
            'css_styles': '''
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #9b59b6;
                    padding-bottom: 10px;
                }
                .logo img {
                    max-height: 60px;
                }
                .report-title h1 {
                    color: #2c3e50;
                    margin: 0;
                }
                .date-range {
                    color: #7f8c8d;
                    font-style: italic;
                }
                .footer {
                    display: flex;
                    justify-content: space-between;
                    font-size: 9pt;
                    color: #7f8c8d;
                    border-top: 1px solid #ddd;
                    padding-top: 5px;
                    margin-top: 20px;
                }
                .summary-box {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                .kpi {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                }
                .kpi-item {
                    flex: 0 0 30%;
                    text-align: center;
                    background-color: #fff;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 10px;
                }
                .kpi-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #9b59b6;
                }
                .kpi-label {
                    font-size: 12px;
                    color: #7f8c8d;
                }
            ''',
            'is_default': True
        },
        {
            'name': 'Default Task Management Report',
            'description': 'Standard template for task management reports with company branding',
            'report_type': 'tasks',
            'header_html': '''
                <div class="header">
                    <div class="logo">
                        <img src="{{ url_for('static', filename='img/logo.png', _external=True) }}" alt="Company Logo">
                    </div>
                    <div class="report-title">
                        <h1>{{ report_title }}</h1>
                        <p class="date-range">{{ date_range }}</p>
                    </div>
                </div>
            ''',
            'footer_html': '''
                <div class="footer">
                    <div class="company-info">
                        <p>{{ company_name }} - Confidential Report</p>
                    </div>
                    <div class="page-info">
                        <p>Page {{ page_number }} of {{ total_pages }}</p>
                        <p class="generated-at">Generated on {{ generated_at }} by {{ generated_by }}</p>
                    </div>
                </div>
            ''',
            'css_styles': '''
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                .logo img {
                    max-height: 60px;
                }
                .report-title h1 {
                    color: #2c3e50;
                    margin: 0;
                }
                .date-range {
                    color: #7f8c8d;
                    font-style: italic;
                }
                .footer {
                    display: flex;
                    justify-content: space-between;
                    font-size: 9pt;
                    color: #7f8c8d;
                    margin-top: 20px;
                    border-top: 1px solid #e9ecef;
                    padding-top: 10px;
                }
                .task-summary {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                    margin-bottom: 20px;
                }
                .task-metric {
                    flex: 0 0 30%;
                    text-align: center;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }
                .task-metric.high-priority {
                    border-left: 4px solid #e74c3c;
                }
                .task-metric.medium-priority {
                    border-left: 4px solid #f39c12;
                }
                .task-metric.low-priority {
                    border-left: 4px solid #3498db;
                }
                .task-metric.completed {
                    border-left: 4px solid #2ecc71;
                }
                .task-metric.open {
                    border-left: 4px solid #95a5a6;
                }
                .task-metric.overdue {
                    border-left: 4px solid #e74c3c;
                }
                .metric-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }
                .metric-label {
                    font-size: 14px;
                    color: #7f8c8d;
                    margin-top: 5px;
                }
                .task-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                .task-table th {
                    background-color: #f8f9fa;
                    color: #2c3e50;
                    font-weight: bold;
                    text-align: left;
                    padding: 12px;
                    border-bottom: 2px solid #e9ecef;
                }
                .task-table td {
                    padding: 10px 12px;
                    border-bottom: 1px solid #e9ecef;
                }
                .task-table tr:hover {
                    background-color: #f8f9fa;
                }
                .priority-high {
                    color: #e74c3c;
                    font-weight: bold;
                }
                .priority-medium {
                    color: #f39c12;
                }
                .priority-low {
                    color: #3498db;
                }
                .status-open {
                    color: #95a5a6;
                }
                .status-completed {
                    color: #2ecc71;
                }
                .chart-container {
                    margin: 20px 0;
                    background-color: #fff;
                    border-radius: 5px;
                    padding: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }
                .chart-title {
                    font-size: 16px;
                    color: #2c3e50;
                    margin-bottom: 10px;
                    text-align: center;
                }
            ''',
            'is_default': True
        }
    ]
    
    # Create templates if they don't exist
    templates_created = 0
    for template_data in default_templates:
        # Check if a default template already exists for this report type
        existing = ReportTemplate.query.filter_by(
            report_type=template_data['report_type'], 
            is_default=True
        ).first()
        
        if not existing:
            template = ReportTemplate(
                name=template_data['name'],
                description=template_data['description'],
                report_type=template_data['report_type'],
                header_html=template_data['header_html'],
                footer_html=template_data['footer_html'],
                css_styles=template_data['css_styles'],
                is_default=template_data['is_default'],
                created_by_id=admin.id
            )
            db.session.add(template)
            templates_created += 1
    
    db.session.commit()
    click.echo(f'Created {templates_created} default templates.')

def init_app(app):
    """Register commands with the Flask application."""
    app.cli.add_command(check_scheduled_reports_command)
    app.cli.add_command(send_report_command)
    app.cli.add_command(create_default_templates_command)
