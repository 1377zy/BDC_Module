"""
Report Templates Module

This module handles the management of report templates for the BDC application.
Templates allow customization of the look and feel of reports.
"""

from flask import render_template, redirect, url_for, flash, request, current_app, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models import ReportTemplate
from app.reports import bp
from app.utils.decorators import admin_required, manager_required, role_required
from datetime import datetime, timedelta
import json
import uuid
from werkzeug.utils import secure_filename
import os


@bp.route('/templates')
@login_required
@manager_required
def report_templates():
    """Display all report templates."""
    templates = ReportTemplate.query.order_by(ReportTemplate.report_type, ReportTemplate.name).all()
    return render_template('reports/template_management.html', templates=templates)


@bp.route('/templates/new', methods=['GET', 'POST'])
@login_required
@manager_required
def new_template():
    """Create a new report template."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        report_type = request.form.get('report_type')
        header_html = request.form.get('header_html')
        footer_html = request.form.get('footer_html')
        css_styles = request.form.get('css_styles')
        include_logo = 'include_logo' in request.form
        include_timestamp = 'include_timestamp' in request.form
        include_page_numbers = 'include_page_numbers' in request.form
        is_default = 'is_default' in request.form
        
        # Validate required fields
        if not name or not report_type:
            flash('Name and report type are required.', 'danger')
            return redirect(url_for('reports.new_template'))
        
        # Create new template
        template = ReportTemplate(
            name=name,
            description=description,
            report_type=report_type,
            header_html=header_html,
            footer_html=footer_html,
            css_styles=css_styles,
            include_logo=include_logo,
            include_timestamp=include_timestamp,
            include_page_numbers=include_page_numbers,
            created_by_id=current_user.id,
            is_default=is_default
        )
        
        # If this is set as default, unset any other defaults for this report type
        if is_default:
            existing_defaults = ReportTemplate.query.filter_by(
                report_type=report_type, 
                is_default=True
            ).all()
            for existing in existing_defaults:
                existing.is_default = False
        
        db.session.add(template)
        db.session.commit()
        
        flash(f'Template "{name}" created successfully.', 'success')
        return redirect(url_for('reports.report_templates'))
    
    return render_template('reports/new_template.html')


@bp.route('/templates/create', methods=['POST'])
@login_required
@manager_required
def create_template():
    """Create a new report template."""
    name = request.form.get('name')
    description = request.form.get('description')
    report_type = request.form.get('report_type')
    header_html = request.form.get('header_html')
    footer_html = request.form.get('footer_html')
    css_styles = request.form.get('css_styles')
    
    # Validate required fields
    if not name or not report_type:
        flash('Name and report type are required.', 'danger')
        return redirect(url_for('reports.report_templates'))
    
    # Create new template
    template = ReportTemplate(
        name=name,
        description=description,
        report_type=report_type,
        header_html=header_html,
        footer_html=footer_html,
        css_styles=css_styles,
        created_by_id=current_user.id
    )
    
    db.session.add(template)
    db.session.commit()
    
    flash(f'Template "{name}" has been created.', 'success')
    return redirect(url_for('reports.report_templates'))


@bp.route('/templates/edit/<int:template_id>', methods=['POST'])
@login_required
@manager_required
def edit_template(template_id):
    """Edit an existing report template."""
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Only the creator or an admin can edit the template
    if template.created_by_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to edit this template.', 'danger')
        return redirect(url_for('reports.report_templates'))
    
    if request.method == 'POST':
        template.name = request.form.get('name')
        template.description = request.form.get('description')
        template.report_type = request.form.get('report_type')
        template.header_html = request.form.get('header_html')
        template.footer_html = request.form.get('footer_html')
        template.css_styles = request.form.get('css_styles')
        
        db.session.commit()
        
        flash(f'Template "{template.name}" has been updated.', 'success')
        return redirect(url_for('reports.report_templates'))


@bp.route('/templates/delete/<int:template_id>')
@login_required
@manager_required
def delete_template(template_id):
    """Delete a report template."""
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Check if user has permission to delete this template
    if template.created_by_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to delete this template.', 'danger')
        return redirect(url_for('reports.report_templates'))
    
    # Check if template is in use
    if template.scheduled_reports:
        flash('This template is in use by one or more scheduled reports and cannot be deleted.', 'danger')
        return redirect(url_for('reports.report_templates'))
    
    template_name = template.name
    db.session.delete(template)
    db.session.commit()
    
    flash(f'Template "{template_name}" deleted successfully.', 'success')
    return redirect(url_for('reports.report_templates'))


@bp.route('/templates/set-default/<int:template_id>', methods=['POST'])
@login_required
def set_default_template(template_id):
    """Set a template as the default for its report type."""
    # Only managers and admins can manage templates
    if current_user.role not in ['manager', 'admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Get the template
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Get all templates of this type
    templates = ReportTemplate.query.filter_by(report_type=template.report_type).all()
    
    # Set all templates of this type to non-default
    for t in templates:
        t.is_default = False
    
    # Set this template as default
    template.is_default = True
    
    # Save changes
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Template "{template.name}" has been set as the default for {template.report_type} reports'
    })


@bp.route('/templates/duplicate/<int:template_id>', methods=['POST'])
@login_required
def duplicate_template(template_id):
    """Duplicate an existing template."""
    # Only managers and admins can manage templates
    if current_user.role not in ['manager', 'admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Get the template to duplicate
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Create a new template with the same properties
    new_template = ReportTemplate(
        name=f"{template.name} (Copy)",
        description=template.description,
        report_type=template.report_type,
        header_html=template.header_html,
        footer_html=template.footer_html,
        css_styles=template.css_styles,
        include_logo=template.include_logo,
        include_timestamp=template.include_timestamp,
        is_default=False,  # Never set a duplicate as default
        created_by_id=current_user.id
    )
    
    db.session.add(new_template)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Template "{template.name}" has been duplicated',
        'new_template_id': new_template.id
    })


@bp.route('/preview-template/<int:template_id>')
@login_required
@manager_required
def preview_template(template_id):
    """Preview a report template with sample data"""
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Generate sample data based on the template type
    sample_data = generate_sample_data(template.report_type)
    
    # Add template to the sample data
    sample_data['template'] = template
    
    # Render the preview
    return render_template('reports/template_preview.html', 
                          template=template, 
                          sample_data=sample_data)


@bp.route('/templates/for_type/<report_type>', methods=['GET'])
@login_required
def get_templates_for_type(report_type):
    """Get all templates for a specific report type."""
    # Only managers and admins can access templates
    if current_user.role not in ['manager', 'admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Validate report type
    if report_type not in ['inventory', 'leads', 'sales', 'performance', 'tasks']:
        return jsonify({'success': False, 'message': 'Invalid report type'}), 400
    
    # Get all templates for this report type
    templates = ReportTemplate.query.filter_by(report_type=report_type).all()
    
    # Format the templates for JSON response
    template_list = []
    for template in templates:
        template_list.append({
            'id': template.id,
            'name': template.name,
            'is_default': template.is_default
        })
    
    return jsonify({
        'success': True,
        'templates': template_list
    })


@bp.route('/templates/default/<report_type>', methods=['GET'])
@login_required
def get_default_template(report_type):
    """Get the default template for a specific report type."""
    # Only managers and admins can access templates
    if current_user.role not in ['manager', 'admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Validate report type
    if report_type not in ['inventory', 'leads', 'sales', 'performance', 'tasks']:
        return jsonify({'success': False, 'message': 'Invalid report type'}), 400
    
    # Get the default template for this report type
    template = ReportTemplate.query.filter_by(report_type=report_type, is_default=True).first()
    
    if not template:
        return jsonify({
            'success': True,
            'has_default': False,
            'message': 'No default template found for this report type'
        })
    
    return jsonify({
        'success': True,
        'has_default': True,
        'template': {
            'id': template.id,
            'name': template.name
        }
    })


@bp.route('/templates/analytics')
@login_required
@role_required(['manager', 'admin'])
def template_analytics():
    """
    Display analytics about template usage
    """
    # Get templates grouped by report type
    inventory_templates = ReportTemplate.query.filter_by(report_type='inventory').order_by(ReportTemplate.usage_count.desc()).all()
    leads_templates = ReportTemplate.query.filter_by(report_type='leads').order_by(ReportTemplate.usage_count.desc()).all()
    sales_templates = ReportTemplate.query.filter_by(report_type='sales').order_by(ReportTemplate.usage_count.desc()).all()
    performance_templates = ReportTemplate.query.filter_by(report_type='performance').order_by(ReportTemplate.usage_count.desc()).all()
    tasks_templates = ReportTemplate.query.filter_by(report_type='tasks').order_by(ReportTemplate.usage_count.desc()).all()
    
    # Calculate total usage by report type
    inventory_usage = sum(template.usage_count for template in inventory_templates)
    leads_usage = sum(template.usage_count for template in leads_templates)
    sales_usage = sum(template.usage_count for template in sales_templates)
    performance_usage = sum(template.usage_count for template in performance_templates)
    tasks_usage = sum(template.usage_count for template in tasks_templates)
    
    # Get top 5 most used templates overall
    most_used_templates = ReportTemplate.query.order_by(ReportTemplate.usage_count.desc()).limit(5).all()
    
    # Get recently created templates (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_templates = ReportTemplate.query.filter(ReportTemplate.created_at >= thirty_days_ago).order_by(ReportTemplate.created_at.desc()).all()
    
    # Get unused templates
    unused_templates = ReportTemplate.query.filter_by(usage_count=0).all()
    
    return render_template('reports/template_analytics.html',
                          inventory_templates=inventory_templates,
                          leads_templates=leads_templates,
                          sales_templates=sales_templates,
                          performance_templates=performance_templates,
                          tasks_templates=tasks_templates,
                          inventory_usage=inventory_usage,
                          leads_usage=leads_usage,
                          sales_usage=sales_usage,
                          performance_usage=performance_usage,
                          tasks_usage=tasks_usage,
                          most_used_templates=most_used_templates,
                          recent_templates=recent_templates,
                          unused_templates=unused_templates)


@bp.route('/templates/export/<int:template_id>')
@login_required
@role_required(['manager', 'admin'])
def export_template(template_id):
    """
    Export a template as a JSON file
    """
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Create a dictionary with template data
    template_data = {
        'name': template.name,
        'description': template.description,
        'report_type': template.report_type,
        'header_html': template.header_html,
        'footer_html': template.footer_html,
        'css_styles': template.css_styles,
        'include_logo': template.include_logo,
        'include_timestamp': template.include_timestamp,
        'include_page_numbers': template.include_page_numbers,
        'export_date': datetime.utcnow().isoformat(),
        'export_version': '1.0'
    }
    
    # Create a temporary file to store the JSON data
    temp_dir = os.path.join(current_app.instance_path, 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    filename = f"template_{secure_filename(template.name)}_{uuid.uuid4().hex[:8]}.json"
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, 'w') as f:
        json.dump(template_data, f, indent=4)
    
    return send_file(file_path, 
                    mimetype='application/json',
                    as_attachment=True,
                    download_name=filename)


@bp.route('/templates/import', methods=['POST'])
@login_required
@role_required(['manager', 'admin'])
def import_template():
    """
    Import a template from a JSON file
    """
    if 'template_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('reports.templates'))
    
    file = request.files['template_file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('reports.templates'))
    
    if not file.filename.endswith('.json'):
        flash('Invalid file format. Please upload a JSON file', 'danger')
        return redirect(url_for('reports.templates'))
    
    try:
        template_data = json.load(file)
        
        # Validate required fields
        required_fields = ['name', 'report_type', 'header_html', 'footer_html', 'css_styles']
        for field in required_fields:
            if field not in template_data:
                flash(f'Invalid template file: missing {field}', 'danger')
                return redirect(url_for('reports.templates'))
        
        # Check if a template with the same name already exists
        existing_template = ReportTemplate.query.filter_by(name=template_data['name']).first()
        if existing_template:
            # Append a suffix to make the name unique
            template_data['name'] = f"{template_data['name']} (Imported)"
        
        # Create a new template
        new_template = ReportTemplate(
            name=template_data['name'],
            description=template_data.get('description', ''),
            report_type=template_data['report_type'],
            header_html=template_data['header_html'],
            footer_html=template_data['footer_html'],
            css_styles=template_data['css_styles'],
            include_logo=template_data.get('include_logo', True),
            include_timestamp=template_data.get('include_timestamp', True),
            include_page_numbers=template_data.get('include_page_numbers', True),
            created_by_id=current_user.id,
            is_default=False,  # Never set imported templates as default automatically
            usage_count=0
        )
        
        db.session.add(new_template)
        db.session.commit()
        
        flash(f'Template "{new_template.name}" imported successfully', 'success')
        return redirect(url_for('reports.templates'))
        
    except json.JSONDecodeError:
        flash('Invalid JSON file', 'danger')
        return redirect(url_for('reports.templates'))
    except Exception as e:
        flash(f'Error importing template: {str(e)}', 'danger')
        return redirect(url_for('reports.templates'))


@bp.route('/templates/bulk-export', methods=['POST'])
@login_required
@role_required(['manager', 'admin'])
def bulk_export_templates():
    """
    Export multiple templates as a single JSON file
    """
    template_ids = request.form.getlist('template_ids')
    
    if not template_ids:
        flash('No templates selected for export', 'warning')
        return redirect(url_for('reports.templates'))
    
    templates = ReportTemplate.query.filter(ReportTemplate.id.in_(template_ids)).all()
    
    if not templates:
        flash('No valid templates found for export', 'warning')
        return redirect(url_for('reports.templates'))
    
    # Create a dictionary with all templates data
    export_data = {
        'export_date': datetime.utcnow().isoformat(),
        'export_version': '1.0',
        'templates_count': len(templates),
        'templates': []
    }
    
    for template in templates:
        template_data = {
            'name': template.name,
            'description': template.description,
            'report_type': template.report_type,
            'header_html': template.header_html,
            'footer_html': template.footer_html,
            'css_styles': template.css_styles,
            'include_logo': template.include_logo,
            'include_timestamp': template.include_timestamp,
            'include_page_numbers': template.include_page_numbers
        }
        export_data['templates'].append(template_data)
    
    # Create a temporary file to store the JSON data
    temp_dir = os.path.join(current_app.instance_path, 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    filename = f"bdc_templates_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, 'w') as f:
        json.dump(export_data, f, indent=4)
    
    return send_file(file_path, 
                    mimetype='application/json',
                    as_attachment=True,
                    download_name=filename)


@bp.route('/templates/bulk-import', methods=['POST'])
@login_required
@role_required(['manager', 'admin'])
def bulk_import_templates():
    """
    Import multiple templates from a single JSON file
    """
    if 'bulk_template_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('reports.templates'))
    
    file = request.files['bulk_template_file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('reports.templates'))
    
    if not file.filename.endswith('.json'):
        flash('Invalid file format. Please upload a JSON file', 'danger')
        return redirect(url_for('reports.templates'))
    
    try:
        import_data = json.load(file)
        
        # Validate the import data
        if 'templates' not in import_data or not isinstance(import_data['templates'], list):
            flash('Invalid import file format', 'danger')
            return redirect(url_for('reports.templates'))
        
        templates_data = import_data['templates']
        imported_count = 0
        skipped_count = 0
        
        for template_data in templates_data:
            # Validate required fields
            required_fields = ['name', 'report_type', 'header_html', 'footer_html', 'css_styles']
            if not all(field in template_data for field in required_fields):
                skipped_count += 1
                continue
            
            # Check if a template with the same name already exists
            existing_template = ReportTemplate.query.filter_by(name=template_data['name']).first()
            if existing_template:
                # Append a suffix to make the name unique
                template_data['name'] = f"{template_data['name']} (Imported)"
            
            # Create a new template
            new_template = ReportTemplate(
                name=template_data['name'],
                description=template_data.get('description', ''),
                report_type=template_data['report_type'],
                header_html=template_data['header_html'],
                footer_html=template_data['footer_html'],
                css_styles=template_data['css_styles'],
                include_logo=template_data.get('include_logo', True),
                include_timestamp=template_data.get('include_timestamp', True),
                include_page_numbers=template_data.get('include_page_numbers', True),
                created_by_id=current_user.id,
                is_default=False,  # Never set imported templates as default automatically
                usage_count=0
            )
            
            db.session.add(new_template)
            imported_count += 1
        
        db.session.commit()
        
        if imported_count > 0:
            flash(f'Successfully imported {imported_count} templates', 'success')
        if skipped_count > 0:
            flash(f'Skipped {skipped_count} invalid templates', 'warning')
        
        return redirect(url_for('reports.templates'))
        
    except json.JSONDecodeError:
        flash('Invalid JSON file', 'danger')
        return redirect(url_for('reports.templates'))
    except Exception as e:
        flash(f'Error importing templates: {str(e)}', 'danger')
        return redirect(url_for('reports.templates'))


def generate_sample_data(report_type):
    """Generate sample data for template preview"""
    sample_data = {
        'title': f'Sample {report_type.capitalize()} Report',
        'date_range': 'January 1, 2025 - March 1, 2025',
        'report_generated_at': datetime.utcnow(),
        'generated_by': 'Template Preview',
        'report_type': report_type,
        'company_name': 'ABC Motors',
        'page_number': 1,
        'total_pages': 5
    }
    
    # Add report-specific sample data
    if report_type == 'inventory':
        sample_data.update({
            'total_vehicles': 157,
            'avg_days_in_stock': 45,
            'avg_price': 32500,
            'top_models': [
                {'make': 'Toyota', 'model': 'Camry', 'count': 12, 'avg_days': 32, 'avg_price': 28500},
                {'make': 'Honda', 'model': 'Accord', 'count': 10, 'avg_days': 38, 'avg_price': 29700},
                {'make': 'Ford', 'model': 'F-150', 'count': 8, 'avg_days': 41, 'avg_price': 42300},
            ]
        })
    elif report_type == 'leads':
        sample_data.update({
            'total_leads': 243,
            'conversion_rate': 18.5,
            'avg_response_time': '2.3 hours',
            'source_metrics': [
                {'name': 'Website', 'total': 98, 'appointments': 45, 'test_drives': 32, 'sales': 21, 'conversion_rate': 21.4},
                {'name': 'Phone', 'total': 76, 'appointments': 38, 'test_drives': 25, 'sales': 18, 'conversion_rate': 23.7},
                {'name': 'Walk-in', 'total': 69, 'appointments': 69, 'test_drives': 42, 'sales': 15, 'conversion_rate': 21.7},
            ]
        })
    elif report_type == 'sales':
        sample_data.update({
            'total_sales': 87,
            'total_revenue': 2850000,
            'avg_sale_price': 32758,
            'top_vehicles': [
                {'make': 'Toyota', 'model': 'RAV4', 'units': 12, 'revenue': 384000, 'avg_price': 32000, 'avg_profit': 2800},
                {'make': 'Honda', 'model': 'CR-V', 'units': 10, 'revenue': 335000, 'avg_price': 33500, 'avg_profit': 2650},
                {'make': 'Ford', 'model': 'Explorer', 'units': 8, 'revenue': 304000, 'avg_price': 38000, 'avg_profit': 3100},
            ]
        })
    elif report_type == 'performance':
        sample_data.update({
            'total_staff': 12,
            'avg_conversion_rate': 22.7,
            'avg_sales_per_staff': 7.25,
            'staff_metrics': [
                {'name': 'John Smith', 'leads': 45, 'appointments': 32, 'test_drives': 28, 'sales': 12, 'conversion_rate': 26.7, 'avg_sale_value': 34500},
                {'name': 'Jane Doe', 'leads': 38, 'appointments': 25, 'test_drives': 22, 'sales': 10, 'conversion_rate': 26.3, 'avg_sale_value': 36200},
                {'name': 'Mike Johnson', 'leads': 42, 'appointments': 30, 'test_drives': 24, 'sales': 9, 'conversion_rate': 21.4, 'avg_sale_value': 32800},
            ]
        })
    elif report_type == 'tasks':
        sample_data.update({
            'tasks': [
                {'title': 'Follow up with John Smith', 'description': 'Call regarding test drive appointment', 'priority': 'high', 'status': 'open', 'due_date': datetime.utcnow() + timedelta(days=1), 'assigned_to': 'Jane Doe'},
                {'title': 'Update inventory listing', 'description': 'Add new Honda Accord models', 'priority': 'medium', 'status': 'open', 'due_date': datetime.utcnow() + timedelta(days=2), 'assigned_to': 'Mike Johnson'},
                {'title': 'Send financing options', 'description': 'Email financing options to Sarah Williams', 'priority': 'high', 'status': 'completed', 'due_date': datetime.utcnow() - timedelta(days=1), 'assigned_to': 'John Smith'},
                {'title': 'Schedule test drive', 'description': 'For Toyota RAV4 with David Brown', 'priority': 'medium', 'status': 'open', 'due_date': datetime.utcnow() + timedelta(days=3), 'assigned_to': 'Jane Doe'},
                {'title': 'Follow up on trade-in', 'description': 'Call Robert Johnson about trade-in value', 'priority': 'low', 'status': 'open', 'due_date': datetime.utcnow() + timedelta(days=5), 'assigned_to': 'Mike Johnson'},
            ],
            'open_tasks_count': 4,
            'completed_tasks_count': 1,
            'high_priority_tasks_count': 2,
            'medium_priority_tasks_count': 2,
            'low_priority_tasks_count': 1,
            'overdue_tasks_count': 0,
            'user_labels': ['Jane Doe', 'Mike Johnson', 'John Smith'],
            'user_open_tasks': [2, 2, 0],
            'user_completed_tasks': [0, 0, 1]
        })
    
    return sample_data
