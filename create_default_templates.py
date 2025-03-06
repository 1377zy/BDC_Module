"""
Script to create default report templates
Run this script directly to create default templates for each report type
"""
import os
import sys
from datetime import datetime

# Add the app directory to the path so we can import from the app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import Flask app and create app context
from app import create_app, db
from app.models import ReportTemplate, User

app = create_app()
with app.app_context():
    print('Creating default report templates...')
    
    # Get the first admin user to set as creator
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User.query.first()  # Fallback to any user if no admin exists
    
    if not admin:
        print('Error: No users found in the system.')
        sys.exit(1)
    
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
    print(f'Created {templates_created} default templates.')
