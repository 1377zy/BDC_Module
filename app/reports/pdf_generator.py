"""
PDF Report Generator for Auto Dealership BDC
Generates PDF reports from report data using WeasyPrint
"""
import os
import tempfile
from datetime import datetime
from flask import render_template, current_app
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import matplotlib.pyplot as plt
import io
import base64
from app.models import ReportTemplate
from app import db

def generate_pdf_report(report_type, data, include_charts=True, template_id=None):
    """
    Generate a PDF report based on the report type and data
    
    Args:
        report_type (str): Type of report (inventory, leads, sales, performance)
        data (dict): Data for the report
        include_charts (bool): Whether to include charts in the report
        template_id (int, optional): ID of the template to use
        
    Returns:
        bytes: PDF file content
    """
    # Create a temporary directory for the PDF generation
    with tempfile.TemporaryDirectory() as tmpdir:
        # Get template if specified
        template = None
        if template_id:
            template = ReportTemplate.query.get(template_id)
        
        # If no template specified or template not found, try to get default template
        if not template:
            template = ReportTemplate.query.filter_by(report_type=report_type, is_default=True).first()
        
        # Generate charts if needed
        if include_charts:
            chart_images = generate_chart_images(report_type, data)
            data['chart_images'] = chart_images
        
        # Add metadata
        data['report_generated_at'] = datetime.utcnow()
        data['report_type'] = report_type
        
        # Determine which template to use
        if template:
            # Use custom template
            html_content = render_template('reports/pdf/template_report.html', 
                                          template=template, 
                                          data=data)
            
            # Create custom CSS from template
            custom_css = template.css_styles if template.css_styles else ''
            
            # Increment usage count for the template
            template.usage_count += 1
            db.session.commit()
        else:
            # Use default template
            html_content = render_template(f'reports/pdf/{report_type}_report.html', **data)
            custom_css = ''
        
        # Write HTML to a temporary file
        html_file = os.path.join(tmpdir, 'report.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Get CSS
        css_file = os.path.join(current_app.root_path, 'static', 'css', 'pdf_report.css')
        css = CSS(filename=css_file, font_config=font_config)
        
        # Add custom CSS if available
        css_list = [css]
        if custom_css:
            css_custom_file = os.path.join(tmpdir, 'custom.css')
            with open(css_custom_file, 'w', encoding='utf-8') as f:
                f.write(custom_css)
            css_list.append(CSS(filename=css_custom_file, font_config=font_config))
        
        # Generate PDF
        html = HTML(filename=html_file)
        pdf_content = html.write_pdf(stylesheets=css_list, font_config=font_config)
        
        return pdf_content

def generate_chart_images(report_type, data):
    """
    Generate chart images for the report
    
    Args:
        report_type (str): Type of report
        data (dict): Data for the report
        
    Returns:
        dict: Dictionary of chart images as base64 encoded strings
    """
    chart_images = {}
    
    if report_type == 'inventory':
        # Status distribution chart
        if 'status_counts' in data:
            chart_images['status_chart'] = generate_pie_chart(
                data['status_counts'], 
                'Vehicle Status Distribution',
                colors=['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b']
            )
        
        # Make distribution chart
        if 'make_counts' in data:
            chart_images['make_chart'] = generate_bar_chart(
                data['make_counts'],
                'Inventory by Make',
                'Make',
                'Count'
            )
            
        # Age distribution chart
        if 'age_distribution' in data:
            chart_images['age_chart'] = generate_bar_chart(
                data['age_distribution'],
                'Inventory Age Distribution',
                'Days in Inventory',
                'Count'
            )
    
    elif report_type == 'leads':
        # Source distribution chart
        if 'source_counts' in data:
            chart_images['source_chart'] = generate_pie_chart(
                data['source_counts'],
                'Lead Sources Distribution',
                colors=['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#5a5c69']
            )
            
        # Status distribution chart
        if 'status_counts' in data:
            chart_images['status_chart'] = generate_pie_chart(
                data['status_counts'],
                'Lead Status Distribution',
                colors=['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b']
            )
            
        # Daily leads chart
        if 'daily_leads' in data:
            chart_images['daily_chart'] = generate_line_chart(
                data['daily_leads'],
                'Daily Lead Generation',
                'Date',
                'Number of Leads'
            )
    
    elif report_type == 'sales':
        # Sales by make chart
        if 'sales_by_make' in data:
            chart_images['make_chart'] = generate_bar_chart(
                data['sales_by_make'],
                'Sales by Make',
                'Make',
                'Number of Sales'
            )
            
        # Daily sales chart
        if 'daily_sales' in data:
            chart_images['daily_chart'] = generate_line_chart(
                data['daily_sales'],
                'Daily Sales',
                'Date',
                'Number of Sales'
            )
            
        # New vs Used chart
        if 'new_vs_used' in data:
            chart_images['new_used_chart'] = generate_pie_chart(
                data['new_vs_used'],
                'New vs Used Vehicle Sales',
                colors=['#4e73df', '#1cc88a']
            )
    
    elif report_type == 'performance':
        # Staff performance comparison
        if 'staff_performance' in data:
            # Extract data for charts
            staff_names = [staff['name'] for staff in data['staff_performance']]
            leads_assigned = [staff['leads_assigned'] for staff in data['staff_performance']]
            appointments_scheduled = [staff['appointments_scheduled'] for staff in data['staff_performance']]
            sales_closed = [staff['sales_closed'] for staff in data['staff_performance']]
            
            # Leads assigned chart
            chart_images['leads_chart'] = generate_horizontal_bar_chart(
                dict(zip(staff_names, leads_assigned)),
                'Leads Assigned by Staff',
                'Staff Member',
                'Number of Leads'
            )
            
            # Appointments scheduled chart
            chart_images['appointments_chart'] = generate_horizontal_bar_chart(
                dict(zip(staff_names, appointments_scheduled)),
                'Appointments Scheduled by Staff',
                'Staff Member',
                'Number of Appointments'
            )
            
            # Sales closed chart
            chart_images['sales_chart'] = generate_horizontal_bar_chart(
                dict(zip(staff_names, sales_closed)),
                'Sales Closed by Staff',
                'Staff Member',
                'Number of Sales'
            )
    
    elif report_type == 'tasks':
        # Task status chart
        if 'open_tasks_count' in data and 'completed_tasks_count' in data:
            status_data = {
                'Open': data['open_tasks_count'],
                'Completed': data['completed_tasks_count']
            }
            chart_images['status_chart'] = generate_pie_chart(
                status_data,
                'Tasks by Status',
                colors=['#4e73df', '#1cc88a']
            )
        
        # Task priority chart
        if 'high_priority_tasks_count' in data and 'medium_priority_tasks_count' in data and 'low_priority_tasks_count' in data:
            priority_data = {
                'High': data['high_priority_tasks_count'],
                'Medium': data['medium_priority_tasks_count'],
                'Low': data['low_priority_tasks_count']
            }
            chart_images['priority_chart'] = generate_pie_chart(
                priority_data,
                'Tasks by Priority',
                colors=['#e74a3b', '#f6c23e', '#1cc88a']
            )
        
        # Tasks by user chart
        if 'user_labels' in data and 'user_open_tasks' in data and 'user_completed_tasks' in data:
            # Create a dictionary with user names as keys and lists of [open_tasks, completed_tasks] as values
            user_data = {}
            for i, user in enumerate(data['user_labels']):
                user_data[user] = [data['user_open_tasks'][i], data['user_completed_tasks'][i]]
            
            # Generate stacked bar chart
            chart_images['user_chart'] = generate_stacked_bar_chart(
                user_data,
                'Tasks by User',
                'User',
                'Number of Tasks',
                ['Open', 'Completed'],
                colors=['#4e73df', '#1cc88a']
            )
    
    return chart_images

def generate_pie_chart(data, title, colors=None):
    """Generate a pie chart and return as base64 encoded string"""
    plt.figure(figsize=(8, 6))
    plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', startangle=90, colors=colors)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title(title)
    plt.tight_layout()
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    # Encode as base64 string
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def generate_bar_chart(data, title, xlabel, ylabel):
    """Generate a bar chart and return as base64 encoded string"""
    plt.figure(figsize=(10, 6))
    plt.bar(data.keys(), data.values(), color='#4e73df')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    # Encode as base64 string
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def generate_horizontal_bar_chart(data, title, xlabel, ylabel):
    """Generate a horizontal bar chart and return as base64 encoded string"""
    plt.figure(figsize=(10, 6))
    plt.barh(list(data.keys()), list(data.values()), color='#4e73df')
    plt.title(title)
    plt.xlabel(ylabel)
    plt.ylabel(xlabel)
    plt.tight_layout()
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    # Encode as base64 string
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def generate_line_chart(data, title, xlabel, ylabel):
    """Generate a line chart and return as base64 encoded string"""
    plt.figure(figsize=(10, 6))
    plt.plot(data.keys(), data.values(), marker='o', linestyle='-', color='#4e73df')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    # Encode as base64 string
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'

def generate_stacked_bar_chart(data, title, xlabel, ylabel, categories, colors=None):
    """
    Generate a stacked bar chart and return as base64 encoded string
    
    Args:
        data (dict): Dictionary with labels as keys and lists of values for each category
        title (str): Chart title
        xlabel (str): X-axis label
        ylabel (str): Y-axis label
        categories (list): List of category names
        colors (list, optional): List of colors for each category
        
    Returns:
        str: Base64 encoded image
    """
    plt.figure(figsize=(10, 6))
    
    # Extract labels and data for each category
    labels = list(data.keys())
    data_by_category = []
    
    for i in range(len(categories)):
        data_by_category.append([data[label][i] for label in labels])
    
    # Create the stacked bar chart
    bottom = [0] * len(labels)
    bars = []
    
    for i, category_data in enumerate(data_by_category):
        color = colors[i] if colors and i < len(colors) else None
        bar = plt.bar(labels, category_data, bottom=bottom, label=categories[i], color=color)
        bars.append(bar)
        
        # Update the bottom for the next category
        bottom = [bottom[j] + category_data[j] for j in range(len(category_data))]
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Convert plot to base64 image
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')

def generate_inventory_pdf(start_date, end_date, report_name=None):
    """
    Generate an inventory PDF report for the given date range
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        report_name (str, optional): Name for the report
        
    Returns:
        str: Path to the generated PDF file
    """
    from app.models import Vehicle
    from app.reports.routes import get_inventory_data
    
    # Get inventory data
    data = get_inventory_data(start_date, end_date)
    
    # Add additional data for PDF
    data['dealership_name'] = current_app.config.get('DEALERSHIP_NAME', 'Auto Dealership')
    data['start_date'] = start_date
    data['end_date'] = end_date
    
    if report_name:
        data['report_name'] = report_name
    else:
        data['report_name'] = f"Inventory Report {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    # Generate recommendations based on data
    recommendations = []
    
    # Check for aging inventory
    if data.get('avg_days_in_inventory', 0) > 60:
        recommendations.append("Consider offering promotions for vehicles that have been in inventory for more than 60 days.")
    
    # Check make distribution
    if data.get('make_counts'):
        make_counts = data['make_counts']
        top_make = max(make_counts.items(), key=lambda x: x[1])[0]
        recommendations.append(f"Your inventory is heavily weighted toward {top_make}. Consider diversifying your inventory.")
    
    # Add general recommendations
    recommendations.append("Regularly review pricing strategy based on market trends and competitor pricing.")
    recommendations.append("Ensure vehicle photos and descriptions are up-to-date and appealing to potential customers.")
    
    data['recommendations'] = recommendations
    
    # Generate PDF
    pdf_content = generate_pdf_report('inventory', data)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.write(pdf_content)
    temp_file.close()
    
    return temp_file.name

def generate_leads_pdf(start_date, end_date, report_name=None):
    """
    Generate a leads PDF report for the given date range
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        report_name (str, optional): Name for the report
        
    Returns:
        str: Path to the generated PDF file
    """
    from app.models import Lead
    from app.reports.routes import get_leads_data
    
    # Get leads data
    data = get_leads_data(start_date, end_date)
    
    # Add additional data for PDF
    data['dealership_name'] = current_app.config.get('DEALERSHIP_NAME', 'Auto Dealership')
    data['start_date'] = start_date
    data['end_date'] = end_date
    
    if report_name:
        data['report_name'] = report_name
    else:
        data['report_name'] = f"Leads Report {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    # Generate recommendations based on data
    recommendations = []
    
    # Check conversion rate
    if data.get('conversion_rate', 0) < 10:
        recommendations.append("Lead-to-sale conversion rate is below target. Consider reviewing the sales process and providing additional training.")
    
    # Check lead sources
    if data.get('source_analysis'):
        source_analysis = data['source_analysis']
        best_source = max(source_analysis, key=lambda x: x.get('conversion_rate', 0))
        worst_source = min(source_analysis, key=lambda x: x.get('conversion_rate', 0))
        
        recommendations.append(f"{best_source['name']} has the highest conversion rate at {best_source['conversion_rate']}%. Consider increasing marketing efforts on this channel.")
        recommendations.append(f"{worst_source['name']} has the lowest conversion rate at {worst_source['conversion_rate']}%. Review the quality of leads from this source.")
    
    # Add general recommendations
    recommendations.append("Implement a lead scoring system to prioritize high-potential leads.")
    recommendations.append("Ensure prompt follow-up with all new leads within the first hour.")
    
    data['recommendations'] = recommendations
    
    # Generate PDF
    pdf_content = generate_pdf_report('leads', data)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.write(pdf_content)
    temp_file.close()
    
    return temp_file.name

def generate_sales_pdf(start_date, end_date, report_name=None):
    """
    Generate a sales PDF report for the given date range
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        report_name (str, optional): Name for the report
        
    Returns:
        str: Path to the generated PDF file
    """
    from app.models import Sale
    from app.reports.routes import get_sales_data
    
    # Get sales data
    data = get_sales_data(start_date, end_date)
    
    # Add additional data for PDF
    data['dealership_name'] = current_app.config.get('DEALERSHIP_NAME', 'Auto Dealership')
    data['start_date'] = start_date
    data['end_date'] = end_date
    
    if report_name:
        data['report_name'] = report_name
    else:
        data['report_name'] = f"Sales Report {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    # Generate recommendations based on data
    recommendations = []
    
    # Check sales trend
    if data.get('daily_sales'):
        daily_sales = data['daily_sales']
        if len(daily_sales) > 1:
            first_half = sum(list(daily_sales.values())[:len(daily_sales)//2])
            second_half = sum(list(daily_sales.values())[len(daily_sales)//2:])
            
            if second_half < first_half:
                recommendations.append("Sales are trending downward in the latter part of the period. Consider implementing a sales incentive program.")
            else:
                recommendations.append("Sales are trending upward. Capitalize on this momentum with targeted marketing campaigns.")
    
    # Check sales by make
    if data.get('sales_by_make_details'):
        sales_by_make = data['sales_by_make_details']
        top_make = max(sales_by_make, key=lambda x: x.get('revenue', 0))
        
        recommendations.append(f"{top_make['name']} is your top revenue generator. Ensure adequate inventory and consider special promotions.")
    
    # Add general recommendations
    recommendations.append("Review pricing strategy for slow-moving inventory to increase turnover.")
    recommendations.append("Implement a customer referral program to leverage existing customer relationships.")
    
    data['recommendations'] = recommendations
    
    # Generate PDF
    pdf_content = generate_pdf_report('sales', data)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.write(pdf_content)
    temp_file.close()
    
    return temp_file.name

def generate_performance_pdf(start_date, end_date, report_name=None):
    """
    Generate a staff performance PDF report for the given date range
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        report_name (str, optional): Name for the report
        
    Returns:
        str: Path to the generated PDF file
    """
    from app.models import User, Lead, Appointment, Sale
    from app.reports.routes import get_performance_data
    
    # Get performance data
    data = get_performance_data(start_date, end_date)
    
    # Add additional data for PDF
    data['dealership_name'] = current_app.config.get('DEALERSHIP_NAME', 'Auto Dealership')
    data['start_date'] = start_date
    data['end_date'] = end_date
    
    if report_name:
        data['report_name'] = report_name
    else:
        data['report_name'] = f"Staff Performance Report {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    # Generate recommendations based on data
    recommendations = []
    training_opportunities = []
    
    # Check team performance
    if data.get('team_lead_to_appointment', 0) < 30:
        recommendations.append("Team lead-to-appointment rate is below target. Consider implementing a standardized lead qualification process.")
        training_opportunities.append("Conduct training on effective lead qualification and appointment setting techniques.")
    
    if data.get('team_appointment_to_sale', 0) < 50:
        recommendations.append("Team appointment-to-sale conversion is below target. Review the sales process and customer experience.")
        training_opportunities.append("Provide training on closing techniques and handling customer objections.")
    
    # Check individual performance
    if data.get('staff_performance'):
        staff_performance = data['staff_performance']
        
        # Identify underperforming staff
        for staff in staff_performance:
            if staff.get('lead_to_appointment', 0) < 20:
                training_opportunities.append(f"{staff['name']} needs improvement in lead qualification and appointment setting.")
            
            if staff.get('appointment_to_sale', 0) < 40:
                training_opportunities.append(f"{staff['name']} needs improvement in closing techniques.")
    
    # Add general recommendations
    recommendations.append("Implement a regular coaching program for all sales staff.")
    recommendations.append("Consider a performance-based incentive program to motivate staff.")
    recommendations.append("Share best practices from top performers with the rest of the team.")
    
    data['recommendations'] = recommendations
    data['training_opportunities'] = training_opportunities
    
    # Generate PDF
    pdf_content = generate_pdf_report('performance', data)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.write(pdf_content)
    temp_file.close()
    
    return temp_file.name
