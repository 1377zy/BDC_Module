from flask import render_template, request, jsonify, current_app, send_file, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from app.reports import bp
from app.models import Lead, Appointment, Communication, Car, VehicleInterest, User, ScheduledReport, Task
from datetime import datetime, timedelta
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import func
from app import db
import os
import tempfile

@bp.route('/')
@login_required
def index():
    """Reporting dashboard with links to various reports."""
    return render_template('reports/index.html', title='Reports')

@bp.route('/inventory')
@login_required
def inventory_report():
    """Generate inventory reports."""
    # Get inventory statistics
    total_vehicles = Car.query.count()
    available_vehicles = Car.query.filter_by(status='Available').count()
    on_hold_vehicles = Car.query.filter_by(status='On Hold').count()
    sold_vehicles = Car.query.filter_by(status='Sold').count()
    
    # Get new vs used breakdown
    new_vehicles = Car.query.filter_by(new_or_used='New').count()
    used_vehicles = Car.query.filter_by(new_or_used='Used').count()
    
    # Get make/model distribution
    make_distribution = db.session.query(
        Car.make, func.count(Car.id).label('count')
    ).group_by(Car.make).order_by(func.count(Car.id).desc()).all()
    
    # Get price range distribution
    price_ranges = [
        {'min': 0, 'max': 10000, 'label': 'Under $10k', 'count': 0},
        {'min': 10000, 'max': 20000, 'label': '$10k-$20k', 'count': 0},
        {'min': 20000, 'max': 30000, 'label': '$20k-$30k', 'count': 0},
        {'min': 30000, 'max': 50000, 'label': '$30k-$50k', 'count': 0},
        {'min': 50000, 'max': 1000000, 'label': 'Over $50k', 'count': 0}
    ]
    
    for price_range in price_ranges:
        price_range['count'] = Car.query.filter(
            Car.price >= price_range['min'],
            Car.price < price_range['max']
        ).count()
    
    # Get inventory age
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sixty_days_ago = datetime.now() - timedelta(days=60)
    ninety_days_ago = datetime.now() - timedelta(days=90)
    
    inventory_age = {
        'under_30_days': Car.query.filter(
            Car.created_at >= thirty_days_ago,
            Car.status == 'Available'
        ).count(),
        '30_to_60_days': Car.query.filter(
            Car.created_at >= sixty_days_ago,
            Car.created_at < thirty_days_ago,
            Car.status == 'Available'
        ).count(),
        '60_to_90_days': Car.query.filter(
            Car.created_at >= ninety_days_ago,
            Car.created_at < sixty_days_ago,
            Car.status == 'Available'
        ).count(),
        'over_90_days': Car.query.filter(
            Car.created_at < ninety_days_ago,
            Car.status == 'Available'
        ).count()
    }
    
    return render_template('reports/inventory.html', 
                          title='Inventory Report',
                          total_vehicles=total_vehicles,
                          available_vehicles=available_vehicles,
                          on_hold_vehicles=on_hold_vehicles,
                          sold_vehicles=sold_vehicles,
                          new_vehicles=new_vehicles,
                          used_vehicles=used_vehicles,
                          make_distribution=make_distribution,
                          price_ranges=price_ranges,
                          inventory_age=inventory_age)

@bp.route('/leads')
@login_required
def leads_report():
    """Generate lead reports."""
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date_str:
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    if not end_date_str:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Get lead statistics
    total_leads = Lead.query.filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).count()
    
    # Lead status breakdown
    statuses = ['New', 'Contacted', 'Qualified', 'Appointment Set', 'Sold', 'Lost']
    lead_status_counts = {}
    for status in statuses:
        count = Lead.query.filter(
            Lead.status == status,
            Lead.created_at >= start_date,
            Lead.created_at <= end_date
        ).count()
        lead_status_counts[status] = count
    
    # Lead source breakdown
    lead_sources = db.session.query(
        Lead.source, func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).group_by(Lead.source).all()
    
    # Daily lead trend
    daily_leads = db.session.query(
        func.date(Lead.created_at).label('date'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).group_by(func.date(Lead.created_at)).all()
    
    # Convert to list of dicts for easier template use
    daily_leads_data = [{'date': str(day.date), 'count': day.count} for day in daily_leads]
    
    return render_template('reports/leads.html',
                          title='Leads Report',
                          total_leads=total_leads,
                          lead_status_counts=lead_status_counts,
                          lead_sources=lead_sources,
                          daily_leads=daily_leads_data,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'))

@bp.route('/sales')
@login_required
def sales_report():
    """Generate sales reports."""
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date_str:
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    if not end_date_str:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Get sales statistics (cars with 'Sold' status)
    sold_vehicles = Car.query.filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).all()
    
    total_sales = len(sold_vehicles)
    
    # Calculate total revenue
    total_revenue = sum(car.price for car in sold_vehicles) if sold_vehicles else 0
    
    # Sales by make
    sales_by_make = db.session.query(
        Car.make, func.count(Car.id).label('count'), func.sum(Car.price).label('revenue')
    ).filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).group_by(Car.make).order_by(func.count(Car.id).desc()).all()
    
    # Sales by new/used
    new_sales = Car.query.filter(
        Car.status == 'Sold',
        Car.new_or_used == 'New',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).count()
    
    used_sales = Car.query.filter(
        Car.status == 'Sold',
        Car.new_or_used == 'Used',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).count()
    
    # Daily sales trend
    daily_sales = db.session.query(
        func.date(Car.sold_date).label('date'),
        func.count(Car.id).label('count'),
        func.sum(Car.price).label('revenue')
    ).filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).group_by(func.date(Car.sold_date)).all()
    
    # Convert to list of dicts for easier template use
    daily_sales_data = [
        {'date': str(day.date), 'count': day.count, 'revenue': day.revenue} 
        for day in daily_sales
    ]
    
    return render_template('reports/sales.html',
                          title='Sales Report',
                          total_sales=total_sales,
                          total_revenue=total_revenue,
                          sales_by_make=sales_by_make,
                          new_sales=new_sales,
                          used_sales=used_sales,
                          daily_sales=daily_sales_data,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'))

@bp.route('/performance')
@login_required
def performance_report():
    """Generate staff performance reports."""
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date_str:
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    if not end_date_str:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Get all staff members
    staff = User.query.all()
    
    # Performance metrics for each staff member
    performance_data = []
    
    for user in staff:
        # Leads assigned
        leads_assigned = Lead.query.filter(
            Lead.assigned_to_id == user.id,
            Lead.created_at >= start_date,
            Lead.created_at <= end_date
        ).count()
        
        # Appointments scheduled
        appointments_scheduled = Appointment.query.join(Lead).filter(
            Lead.assigned_to_id == user.id,
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        ).count()
        
        # Communications sent
        communications_sent = Communication.query.join(Lead).filter(
            Lead.assigned_to_id == user.id,
            Communication.direction == 'Outbound',
            Communication.sent_at >= start_date,
            Communication.sent_at <= end_date
        ).count()
        
        # Sales closed (leads that reached 'Sold' status)
        sales_closed = Lead.query.filter(
            Lead.assigned_to_id == user.id,
            Lead.status == 'Sold',
            Lead.updated_at >= start_date,
            Lead.updated_at <= end_date
        ).count()
        
        # Calculate conversion rate
        conversion_rate = (sales_closed / leads_assigned * 100) if leads_assigned > 0 else 0
        
        performance_data.append({
            'user': user,
            'leads_assigned': leads_assigned,
            'appointments_scheduled': appointments_scheduled,
            'communications_sent': communications_sent,
            'sales_closed': sales_closed,
            'conversion_rate': round(conversion_rate, 1)
        })
    
    # Sort by sales closed (descending)
    performance_data.sort(key=lambda x: x['sales_closed'], reverse=True)
    
    return render_template('reports/performance.html',
                          title='Staff Performance Report',
                          performance_data=performance_data,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'))

@bp.route('/export/inventory')
@login_required
def export_inventory():
    """Export inventory data to CSV."""
    # Get all cars
    cars = Car.query.all()
    
    # Create DataFrame
    data = []
    for car in cars:
        data.append({
            'ID': car.id,
            'VIN': car.vin,
            'Year': car.year,
            'Make': car.make,
            'Model': car.model,
            'Trim': car.trim,
            'Price': car.price,
            'Mileage': car.mileage,
            'Exterior Color': car.exterior_color,
            'Interior Color': car.interior_color,
            'Status': car.status,
            'New/Used': car.new_or_used,
            'Date Added': car.created_at.strftime('%Y-%m-%d'),
            'Last Updated': car.updated_at.strftime('%Y-%m-%d') if car.updated_at else '',
            'Sold Date': car.sold_date.strftime('%Y-%m-%d') if car.sold_date else ''
        })
    
    df = pd.DataFrame(data)
    
    # Create a string buffer
    output = io.StringIO()
    df.to_csv(output, index=False)
    
    # Create a bytes buffer from the string buffer
    bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))
    
    # Return the CSV file
    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'inventory_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@bp.route('/export/leads')
@login_required
def export_leads():
    """Export leads data to CSV."""
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date_str:
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    if not end_date_str:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Get leads within date range
    leads = Lead.query.filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).all()
    
    # Create DataFrame
    data = []
    for lead in leads:
        assigned_to = User.query.get(lead.assigned_to_id).username if lead.assigned_to_id else 'Unassigned'
        
        data.append({
            'ID': lead.id,
            'First Name': lead.first_name,
            'Last Name': lead.last_name,
            'Email': lead.email,
            'Phone': lead.phone,
            'Source': lead.source,
            'Status': lead.status,
            'Assigned To': assigned_to,
            'Created Date': lead.created_at.strftime('%Y-%m-%d'),
            'Last Updated': lead.updated_at.strftime('%Y-%m-%d') if lead.updated_at else ''
        })
    
    df = pd.DataFrame(data)
    
    # Create a string buffer
    output = io.StringIO()
    df.to_csv(output, index=False)
    
    # Create a bytes buffer from the string buffer
    bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))
    
    # Return the CSV file
    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'leads_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@bp.route('/export/sales')
@login_required
def export_sales():
    """Export sales data to CSV."""
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date_str:
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    if not end_date_str:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Query sold vehicles
    sold_vehicles = Car.query.filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).all()
    
    # Create a DataFrame
    sales_data = []
    for vehicle in sold_vehicles:
        # Get the lead associated with this sale if available
        lead = Lead.query.filter_by(id=vehicle.sold_to_lead_id).first() if vehicle.sold_to_lead_id else None
        
        # Get the user who sold the vehicle if available
        user = User.query.filter_by(id=vehicle.sold_by_user_id).first() if vehicle.sold_by_user_id else None
        
        sales_data.append({
            'VIN': vehicle.vin,
            'Make': vehicle.make,
            'Model': vehicle.model,
            'Year': vehicle.year,
            'New/Used': vehicle.new_or_used,
            'Price': vehicle.price,
            'Sale Date': vehicle.sold_date,
            'Days in Inventory': (vehicle.sold_date - vehicle.created_at).days if vehicle.sold_date else None,
            'Customer Name': f"{lead.first_name} {lead.last_name}" if lead else "N/A",
            'Customer Email': lead.email if lead else "N/A",
            'Customer Phone': lead.phone if lead else "N/A",
            'Salesperson': f"{user.first_name} {user.last_name}" if user else "N/A"
        })
    
    # Create DataFrame
    df = pd.DataFrame(sales_data)
    
    # Create a string buffer
    buffer = io.BytesIO()
    
    # Write to the buffer
    df.to_csv(buffer, index=False, encoding='utf-8')
    
    # Seek to the beginning of the buffer
    buffer.seek(0)
    
    # Generate filename with date range
    filename = f"sales_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
    
    # Send the file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )

@bp.route('/chart/inventory-status')
@login_required
def chart_inventory_status():
    """Generate a pie chart of inventory status."""
    # Get inventory statistics
    available_vehicles = Car.query.filter_by(status='Available').count()
    on_hold_vehicles = Car.query.filter_by(status='On Hold').count()
    sold_vehicles = Car.query.filter_by(status='Sold').count()
    
    # Create a pie chart
    plt.figure(figsize=(8, 6))
    plt.pie(
        [available_vehicles, on_hold_vehicles, sold_vehicles],
        labels=['Available', 'On Hold', 'Sold'],
        autopct='%1.1f%%',
        colors=['#28a745', '#ffc107', '#dc3545']
    )
    plt.title('Inventory Status Distribution')
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(temp_file.name)
    plt.close()
    
    # Return the image file
    return send_file(
        temp_file.name,
        mimetype='image/png',
        as_attachment=False,
        download_name='inventory_status_chart.png'
    )

@bp.route('/chart/lead-sources')
@login_required
def chart_lead_sources():
    """Generate a bar chart of lead sources."""
    # Get lead source data
    lead_sources = db.session.query(
        Lead.source, func.count(Lead.id).label('count')
    ).group_by(Lead.source).all()
    
    # Extract data
    sources = [source[0] for source in lead_sources]
    counts = [source[1] for source in lead_sources]
    
    # Create a bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(sources, counts, color='#007bff')
    plt.title('Lead Sources')
    plt.xlabel('Source')
    plt.ylabel('Number of Leads')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(temp_file.name)
    plt.close()
    
    # Return the image file
    return send_file(
        temp_file.name,
        mimetype='image/png',
        as_attachment=False,
        download_name='lead_sources_chart.png'
    )

@bp.route('/chart/staff-performance')
@login_required
def chart_staff_performance():
    """Generate a chart of staff performance metrics."""
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date_str:
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    if not end_date_str:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Get all staff members (users with role 'staff' or 'admin')
    staff = User.query.filter(User.role.in_(['staff', 'admin'])).all()
    
    # Collect performance data
    performance_data = []
    for user in staff:
        # Get leads assigned to this staff member
        leads_assigned = Lead.query.filter(
            Lead.assigned_to_id == user.id,
            Lead.created_at >= start_date,
            Lead.created_at <= end_date
        ).count()
        
        # Get appointments scheduled by this staff member
        appointments_scheduled = Appointment.query.filter(
            Appointment.scheduled_by_id == user.id,
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        ).count()
        
        # Get sales closed by this staff member
        sales_closed = Car.query.filter(
            Car.sold_by_user_id == user.id,
            Car.sold_date >= start_date,
            Car.sold_date <= end_date
        ).count()
        
        # Calculate conversion rate (sales / leads)
        conversion_rate = (sales_closed / leads_assigned * 100) if leads_assigned > 0 else 0
        
        performance_data.append({
            'name': f"{user.first_name} {user.last_name}",
            'leads': leads_assigned,
            'appointments': appointments_scheduled,
            'sales': sales_closed,
            'conversion': conversion_rate
        })
    
    # Sort by sales (highest first)
    performance_data.sort(key=lambda x: x['sales'], reverse=True)
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    # Extract data for plotting
    names = [p['name'] for p in performance_data]
    leads = [p['leads'] for p in performance_data]
    appointments = [p['appointments'] for p in performance_data]
    sales = [p['sales'] for p in performance_data]
    conversion_rates = [p['conversion'] for p in performance_data]
    
    # Set a colorful palette
    colors = sns.color_palette('husl', len(names))
    
    # Plot 1: Stacked bar chart of leads, appointments, and sales
    width = 0.8
    ax1.bar(names, leads, width, label='Leads Assigned', color='#3498db')
    ax1.bar(names, appointments, width, bottom=leads, label='Appointments', color='#f39c12')
    ax1.bar(names, sales, width, bottom=[i+j for i,j in zip(leads, appointments)], label='Sales', color='#2ecc71')
    
    ax1.set_ylabel('Count')
    ax1.set_title('Staff Activity Metrics')
    ax1.legend(loc='upper right')
    
    # Rotate x-axis labels for better readability
    ax1.set_xticklabels(names, rotation=45, ha='right')
    
    # Plot 2: Conversion rates
    ax2.bar(names, conversion_rates, color=colors)
    ax2.set_ylabel('Conversion Rate (%)')
    ax2.set_title('Lead to Sale Conversion Rate')
    
    # Rotate x-axis labels for better readability
    ax2.set_xticklabels(names, rotation=45, ha='right')
    
    # Add value labels on top of bars
    for i, v in enumerate(conversion_rates):
        ax2.text(i, v + 1, f"{v:.1f}%", ha='center')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(temp_file.name)
    plt.close()
    
    # Return the image
    return send_file(temp_file.name, mimetype='image/png')

@bp.route('/export/performance')
@login_required
def export_performance():
    """Export staff performance data to CSV."""
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date_str:
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    if not end_date_str:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Get all staff members (users with role 'staff' or 'admin')
    staff = User.query.filter(User.role.in_(['staff', 'admin'])).all()
    
    # Collect performance data
    performance_data = []
    for user in staff:
        # Get leads assigned to this staff member
        leads_assigned = Lead.query.filter(
            Lead.assigned_to_id == user.id,
            Lead.created_at >= start_date,
            Lead.created_at <= end_date
        ).count()
        
        # Get appointments scheduled by this staff member
        appointments_scheduled = Appointment.query.filter(
            Appointment.scheduled_by_id == user.id,
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        ).count()
        
        # Get communications sent by this staff member
        communications_sent = Communication.query.filter(
            Communication.sent_by_id == user.id,
            Communication.sent_at >= start_date,
            Communication.sent_at <= end_date
        ).count()
        
        # Get sales closed by this staff member
        sales_closed = Car.query.filter(
            Car.sold_by_user_id == user.id,
            Car.sold_date >= start_date,
            Car.sold_date <= end_date
        ).count()
        
        # Calculate conversion rate (sales / leads)
        conversion_rate = (sales_closed / leads_assigned * 100) if leads_assigned > 0 else 0
        
        # Calculate average time to appointment
        lead_to_appointment_days = []
        leads = Lead.query.filter(
            Lead.assigned_to_id == user.id,
            Lead.created_at >= start_date,
            Lead.created_at <= end_date
        ).all()
        
        for lead in leads:
            # Find the first appointment for this lead
            appointment = Appointment.query.filter(
                Appointment.lead_id == lead.id,
                Appointment.scheduled_by_id == user.id,
                Appointment.created_at >= start_date,
                Appointment.created_at <= end_date
            ).order_by(Appointment.created_at).first()
            
            if appointment:
                days_diff = (appointment.created_at - lead.created_at).days
                lead_to_appointment_days.append(days_diff)
        
        avg_days_to_appointment = sum(lead_to_appointment_days) / len(lead_to_appointment_days) if lead_to_appointment_days else 0
        
        performance_data.append({
            'Staff Name': f"{user.first_name} {user.last_name}",
            'Email': user.email,
            'Role': user.role,
            'Leads Assigned': leads_assigned,
            'Appointments Scheduled': appointments_scheduled,
            'Communications Sent': communications_sent,
            'Sales Closed': sales_closed,
            'Conversion Rate (%)': round(conversion_rate, 2),
            'Avg Days to Appointment': round(avg_days_to_appointment, 1),
            'Revenue Generated ($)': sum([car.price for car in Car.query.filter(
                Car.sold_by_user_id == user.id,
                Car.sold_date >= start_date,
                Car.sold_date <= end_date
            ).all()]),
            'Period Start': start_date.strftime('%Y-%m-%d'),
            'Period End': end_date.strftime('%Y-%m-%d')
        })
    
    # Create DataFrame
    df = pd.DataFrame(performance_data)
    
    # Create a string buffer
    buffer = io.BytesIO()
    
    # Write to the buffer
    df.to_csv(buffer, index=False, encoding='utf-8')
    
    # Seek to the beginning of the buffer
    buffer.seek(0)
    
    # Generate filename with date range
    filename = f"staff_performance_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
    
    # Send the file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )

@bp.route('/scheduled-reports')
@login_required
def scheduled_reports():
    """Display and manage scheduled reports."""
    # Only managers and admins can access scheduled reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to access scheduled reports.', 'danger')
        return redirect(url_for('reports.index'))
        
    scheduled_reports = ScheduledReport.query.filter_by(created_by_id=current_user.id).all()
    
    return render_template('reports/scheduled_reports.html', scheduled_reports=scheduled_reports)

@bp.route('/scheduled-reports/create', methods=['POST'])
@login_required
def create_scheduled_report():
    """Create a new scheduled report."""
    # Only managers and admins can create scheduled reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to create scheduled reports.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Get form data
    name = request.form.get('name')
    report_type = request.form.get('report_type')
    frequency = request.form.get('frequency')
    time_of_day = datetime.strptime(request.form.get('time_of_day'), '%H:%M').time()
    recipients = request.form.get('recipients')
    format = request.form.get('format')
    include_charts = 'include_charts' in request.form
    date_range = request.form.get('date_range')
    template_id = request.form.get('template_id')
    
    # Get frequency-specific options
    day_of_week = None
    day_of_month = None
    
    if frequency == 'weekly':
        day_of_week = int(request.form.get('day_of_week', 0))
    elif frequency == 'monthly':
        day_of_month = int(request.form.get('day_of_month', 1))
    
    # Get custom date range if selected
    custom_start_date = None
    custom_end_date = None
    
    if date_range == 'custom':
        custom_start_date = datetime.strptime(request.form.get('custom_start_date'), '%Y-%m-%d').date()
        custom_end_date = datetime.strptime(request.form.get('custom_end_date'), '%Y-%m-%d').date()
    
    # Create the scheduled report
    report = ScheduledReport(
        name=name,
        report_type=report_type,
        frequency=frequency,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        time_of_day=time_of_day,
        recipients=recipients,
        format=format,
        include_charts=include_charts,
        date_range=date_range,
        custom_start_date=custom_start_date,
        custom_end_date=custom_end_date,
        created_by_id=current_user.id,
        template_id=template_id if template_id else None
    )
    
    db.session.add(report)
    db.session.commit()
    
    flash(f'Scheduled report "{name}" has been created successfully.', 'success')
    return redirect(url_for('reports.scheduled_reports'))

@bp.route('/scheduled-reports/edit/<int:report_id>', methods=['GET', 'POST'])
@login_required
def edit_scheduled_report(report_id):
    """Edit an existing scheduled report."""
    # Only managers and admins can edit scheduled reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to edit scheduled reports.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Get the report
    report = ScheduledReport.query.get_or_404(report_id)
    
    # Ensure the user owns this report
    if report.created_by_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to edit this scheduled report.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    if request.method == 'POST':
        # Update the report with form data
        report.name = request.form.get('name')
        report.report_type = request.form.get('report_type')
        report.frequency = request.form.get('frequency')
        report.time_of_day = datetime.strptime(request.form.get('time_of_day'), '%H:%M').time()
        report.recipients = request.form.get('recipients')
        report.format = request.form.get('format')
        report.include_charts = 'include_charts' in request.form
        report.date_range = request.form.get('date_range')
        report.template_id = request.form.get('template_id') if request.form.get('template_id') else None
        
        # Update frequency-specific options
        if report.frequency == 'weekly':
            report.day_of_week = int(request.form.get('day_of_week', 0))
            report.day_of_month = None
        elif report.frequency == 'monthly':
            report.day_of_month = int(request.form.get('day_of_month', 1))
            report.day_of_week = None
        else:
            report.day_of_week = None
            report.day_of_month = None
        
        # Update custom date range if selected
        if report.date_range == 'custom':
            report.custom_start_date = datetime.strptime(request.form.get('custom_start_date'), '%Y-%m-%d').date()
            report.custom_end_date = datetime.strptime(request.form.get('custom_end_date'), '%Y-%m-%d').date()
        else:
            report.custom_start_date = None
            report.custom_end_date = None
        
        db.session.commit()
        
        flash(f'Scheduled report "{report.name}" has been updated successfully.', 'success')
        return redirect(url_for('reports.scheduled_reports'))
    
    # Render the edit form
    return render_template('reports/edit_scheduled_report.html', report=report)

@bp.route('/scheduled-reports/toggle/<int:report_id>')
@login_required
def toggle_scheduled_report(report_id):
    """Toggle the active status of a scheduled report."""
    # Only managers and admins can toggle scheduled reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to manage scheduled reports.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Get the report
    report = ScheduledReport.query.get_or_404(report_id)
    
    # Ensure the user owns this report
    if report.created_by_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to manage this scheduled report.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    # Toggle the active status
    report.is_active = not report.is_active
    db.session.commit()
    
    status = 'activated' if report.is_active else 'deactivated'
    flash(f'Scheduled report "{report.name}" has been {status}.', 'success')
    return redirect(url_for('reports.scheduled_reports'))

@bp.route('/scheduled-reports/delete/<int:report_id>')
@login_required
def delete_scheduled_report(report_id):
    """Delete a scheduled report."""
    # Only managers and admins can delete scheduled reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to delete scheduled reports.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Get the report
    report = ScheduledReport.query.get_or_404(report_id)
    
    # Ensure the user owns this report
    if report.created_by_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to delete this scheduled report.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    # Delete the report
    db.session.delete(report)
    db.session.commit()
    
    flash(f'Scheduled report "{report.name}" has been deleted.', 'success')
    return redirect(url_for('reports.scheduled_reports'))

@bp.route('/scheduled-reports/send-now/<int:report_id>')
@login_required
def send_scheduled_report_now(report_id):
    """Manually send a scheduled report immediately."""
    # Only managers and admins can send scheduled reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to send scheduled reports.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Get the report
    report = ScheduledReport.query.get_or_404(report_id)
    
    # Ensure the user owns this report
    if report.created_by_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to send this scheduled report.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    # Send the report
    try:
        from app.reports.report_scheduler import ReportScheduler
        
        # Use the ReportScheduler to generate and send the report
        ReportScheduler.send_report(report)
        
        # Update the last_sent_at timestamp
        report.last_sent_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Scheduled report "{report.name}" has been sent successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error sending scheduled report: {str(e)}")
        flash(f'Error sending report: {str(e)}', 'danger')
    
    return redirect(url_for('reports.scheduled_reports'))

@bp.route('/scheduled-reports/preview', methods=['POST'])
@login_required
def preview_scheduled_report():
    """Preview a report before scheduling it."""
    # Only managers and admins can preview scheduled reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to preview scheduled reports.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Get form data
    report_type = request.form.get('report_type')
    date_range = request.form.get('date_range')
    include_charts = 'include_charts' in request.form
    template_id = request.form.get('template_id')
    
    # Calculate date range based on selection
    end_date = datetime.now().date()
    
    if date_range == 'last_7_days':
        start_date = end_date - timedelta(days=7)
    elif date_range == 'last_30_days':
        start_date = end_date - timedelta(days=30)
    elif date_range == 'last_90_days':
        start_date = end_date - timedelta(days=90)
    elif date_range == 'custom':
        start_date = datetime.strptime(request.form.get('custom_start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('custom_end_date'), '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=30)  # Default to last 30 days
    
    # Generate report data based on type
    if report_type == 'inventory':
        data = generate_inventory_report_data(start_date, end_date)
    elif report_type == 'leads':
        data = generate_leads_report_data(start_date, end_date)
    elif report_type == 'sales':
        data = generate_sales_report_data(start_date, end_date)
    elif report_type == 'performance':
        data = generate_performance_report_data(start_date, end_date)
    elif report_type == 'tasks':
        data = generate_task_report_data(start_date, end_date)
    else:
        flash('Invalid report type.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    # Add metadata
    data['title'] = f"{report_type.capitalize()} Report"
    data['date_range'] = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    data['generated_by'] = f"{current_user.first_name} {current_user.last_name}"
    data['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Generate PDF with template if specified
    template_id_int = int(template_id) if template_id and template_id.isdigit() else None
    pdf_content = generate_pdf_report(report_type, data, include_charts, template_id_int)
    
    # Create a response with the PDF content
    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={report_type}_report_preview.pdf'
    
    return response

@bp.route('/preview-template/<int:template_id>')
@login_required
def preview_template(template_id):
    """Preview a report template with sample data."""
    # Only managers and admins can preview report templates
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to preview report templates.', 'danger')
        return redirect(url_for('reports.index'))
    
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Create sample data based on report type
    data = {
        'title': f"Sample {template.report_type.capitalize()} Report",
        'date_range': f"{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
        'generated_by': f"{current_user.first_name} {current_user.last_name}",
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Add sample data specific to report type
    if template.report_type == 'inventory':
        data.update({
            'total_vehicles': 250,
            'avg_days_in_stock': 45,
            'avg_price': 32500,
            'top_models': [
                {'make': 'Toyota', 'model': 'Camry', 'count': 12, 'avg_days': 38, 'avg_price': 28500},
                {'make': 'Honda', 'model': 'Accord', 'count': 10, 'avg_days': 42, 'avg_price': 27800},
                {'make': 'Ford', 'model': 'F-150', 'count': 8, 'avg_days': 30, 'avg_price': 42300}
            ]
        })
    elif template.report_type == 'leads':
        data.update({
            'total_leads': 320,
            'conversion_rate': 28.5,
            'avg_response_time': '2.3 hours',
            'source_metrics': [
                {'name': 'Website', 'total': 120, 'appointments': 85, 'test_drives': 62, 'sales': 28, 'conversion_rate': 23.3},
                {'name': 'Phone', 'total': 95, 'appointments': 72, 'test_drives': 58, 'sales': 32, 'conversion_rate': 33.7},
                {'name': 'Walk-in', 'total': 65, 'appointments': 65, 'test_drives': 52, 'sales': 30, 'conversion_rate': 46.2}
            ]
        })
    elif template.report_type == 'sales':
        data.update({
            'total_sales': 85,
            'total_revenue': 2850000,
            'avg_sale_price': 33500,
            'top_vehicles': [
                {'make': 'Toyota', 'model': 'RAV4', 'units': 18, 'revenue': 540000, 'avg_price': 30000, 'avg_profit': 3200},
                {'make': 'Honda', 'model': 'CR-V', 'units': 15, 'revenue': 435000, 'avg_price': 29000, 'avg_profit': 2800},
                {'make': 'Ford', 'model': 'Escape', 'units': 12, 'revenue': 336000, 'avg_price': 28000, 'avg_profit': 2500}
            ]
        })
    elif template.report_type == 'performance':
        data.update({
            'total_staff': 12,
            'avg_conversion_rate': 32.5,
            'avg_sales_per_staff': 7.1,
            'staff_metrics': [
                {'name': 'John Smith', 'leads': 45, 'appointments': 32, 'test_drives': 28, 'sales': 15, 'conversion_rate': 33.3, 'avg_sale_value': 32500},
                {'name': 'Sarah Johnson', 'leads': 42, 'appointments': 35, 'test_drives': 30, 'sales': 18, 'conversion_rate': 42.9, 'avg_sale_value': 35200},
                {'name': 'Michael Brown', 'leads': 38, 'appointments': 30, 'test_drives': 25, 'sales': 12, 'conversion_rate': 31.6, 'avg_sale_value': 29800}
            ]
        })
    elif template.report_type == 'tasks':
        data.update({
            'open_tasks_count': 45,
            'completed_tasks_count': 78,
            'overdue_tasks_count': 12,
            'high_priority_tasks_count': 15,
            'medium_priority_tasks_count': 32,
            'low_priority_tasks_count': 76,
            'user_labels': ['John Smith', 'Sarah Johnson', 'Michael Brown'],
            'user_open_tasks': [15, 18, 12],
            'user_completed_tasks': [22, 35, 21],
            'tasks': [
                {'title': 'Follow up with lead', 'assigned_to': {'get_full_name': lambda: 'John Smith'}, 'priority': 'high', 'due_date': datetime.now().date() + timedelta(days=2), 'status': 'open', 'related_entity_type': 'lead', 'related_entity_id': 1},
                {'title': 'Schedule test drive', 'assigned_to': {'get_full_name': lambda: 'Sarah Johnson'}, 'priority': 'medium', 'due_date': datetime.now().date() + timedelta(days=1), 'status': 'open', 'related_entity_type': 'lead', 'related_entity_id': 2},
                {'title': 'Send price quote', 'assigned_to': {'get_full_name': lambda: 'Michael Brown'}, 'priority': 'low', 'due_date': datetime.now().date() - timedelta(days=1), 'status': 'completed', 'related_entity_type': 'lead', 'related_entity_id': 3}
            ],
            'get_lead': lambda id: {'get_full_name': lambda: f'Lead {id}'},
            'now': datetime.now()
        })
    
    return render_template('reports/preview_template.html', template=template, data=data)

@bp.route('/preview-template-with-data/<int:template_id>', methods=['POST'])
@login_required
def preview_template_with_data(template_id):
    """Preview a report template with actual data."""
    # Only managers and admins can preview report templates
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to preview report templates.', 'danger')
        return redirect(url_for('reports.index'))
    
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Get form data
    report_type = request.form.get('report_type')
    date_range = request.form.get('date_range')
    include_charts = 'include_charts' in request.form
    
    # Calculate date range based on selection
    end_date = datetime.now().date()
    
    if date_range == 'last_7_days':
        start_date = end_date - timedelta(days=7)
    elif date_range == 'last_30_days':
        start_date = end_date - timedelta(days=30)
    elif date_range == 'last_90_days':
        start_date = end_date - timedelta(days=90)
    elif date_range == 'custom':
        start_date = datetime.strptime(request.form.get('custom_start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('custom_end_date'), '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=30)  # Default to last 30 days
    
    # Generate report data based on type
    if report_type == 'inventory':
        data = generate_inventory_report_data(start_date, end_date)
    elif report_type == 'leads':
        data = generate_leads_report_data(start_date, end_date)
    elif report_type == 'sales':
        data = generate_sales_report_data(start_date, end_date)
    elif report_type == 'performance':
        data = generate_performance_report_data(start_date, end_date)
    elif report_type == 'tasks':
        data = generate_task_report_data(start_date, end_date)
    else:
        flash('Invalid report type.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    # Add metadata
    data['title'] = f"{report_type.capitalize()} Report"
    data['date_range'] = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    data['generated_by'] = f"{current_user.first_name} {current_user.last_name}"
    data['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('reports/preview_template.html', template=template, data=data)

@bp.route('/scheduled-reports/download-archive/<int:report_id>')
@login_required
def download_archived_report(report_id):
    """Download an archived report."""
    # Only managers and admins can download archived reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to download archived reports.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Get the report
    report = ScheduledReport.query.get_or_404(report_id)
    
    # Ensure the user owns this report
    if report.created_by_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to download this archived report.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    # Check if the report is archived
    if not report.archived or not report.archive_path:
        flash('This report is not archived or the archive is not available.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    try:
        # Check if the archive file exists
        if not os.path.exists(report.archive_path):
            flash('The archive file does not exist.', 'danger')
            return redirect(url_for('reports.scheduled_reports'))
        
        # Return the archive file
        return send_file(
            report.archive_path,
            as_attachment=True,
            download_name=f"archive_{report.report_type}_report.zip",
            mimetype='application/zip'
        )
    except Exception as e:
        current_app.logger.error(f"Error downloading archived report: {str(e)}")
        flash(f'Error downloading archived report: {str(e)}', 'danger')
        return redirect(url_for('reports.scheduled_reports'))

@bp.route('/scheduled-reports/download-archive/<int:report_id>')
@login_required
def download_archived_report(report_id):
    """Download an archived scheduled report."""
    # Only managers and admins can download archived reports
    if current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to download archived reports.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Get the report
    report = ScheduledReport.query.get_or_404(report_id)
    
    # Ensure the user owns this report
    if report.created_by_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to download this archived report.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    # Get the archive path
    archive_path = os.path.join(current_app.config['REPORT_ARCHIVE_DIR'], f"{report_id}_{report.last_sent_at.strftime('%Y%m%d_%H%M%S')}.pdf")
    
    if not os.path.exists(archive_path):
        flash('Archived report not found.', 'danger')
        return redirect(url_for('reports.scheduled_reports'))
    
    return send_file(
        archive_path,
        as_attachment=True,
        download_name=f"{report.name}_{report.last_sent_at.strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )

@bp.route('/tasks')
@login_required
def task_report():
    """Generate task management reports."""
    # Get date range
    date_range = request.args.get('date_range', 'last_30_days')
    start_date, end_date = get_date_range(date_range)
    
    # Get filters
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    # Generate report data
    report_data = generate_task_report_data(start_date, end_date, user_id, status, priority)
    
    # Get all users for filter dropdown
    users = User.query.all()
    
    return render_template('reports/task_report.html',
                          title='Task Report',
                          date_range=date_range,
                          start_date=start_date.strftime('%Y-%m-%d') if start_date else '',
                          end_date=end_date.strftime('%Y-%m-%d') if end_date else '',
                          user_id=user_id,
                          status=status,
                          priority=priority,
                          users=users,
                          now=datetime.utcnow(),
                          **report_data)

@bp.route('/tasks/export/csv')
@login_required
def task_report_csv():
    """Export task report data to CSV."""
    # Get date range
    date_range = request.args.get('date_range', 'last_30_days')
    start_date, end_date = get_date_range(date_range)
    
    # Get filters
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    # Generate report data
    report_data = generate_task_report_data(start_date, end_date, user_id, status, priority)
    
    # Create DataFrame from tasks
    tasks = report_data['tasks']
    data = []
    
    for task in tasks:
        # Get related entity info
        related_entity = ''
        if task.related_entity_type == 'lead' and task.related_entity_id:
            lead = Lead.query.get(task.related_entity_id)
            if lead:
                related_entity = lead.get_full_name()
        
        # Add task data
        data.append({
            'Title': task.title,
            'Description': task.description,
            'Priority': task.priority,
            'Status': task.status,
            'Due Date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            'Assigned To': task.assigned_to.get_full_name(),
            'Related To': related_entity,
            'Created At': task.created_at.strftime('%Y-%m-%d %H:%M'),
            'Completed At': task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else ''
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create CSV file
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    # Generate filename
    filename = f"task_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )

@bp.route('/tasks/export/pdf')
@login_required
def task_report_pdf():
    """Export task report data to PDF."""
    # Get date range
    date_range = request.args.get('date_range', 'last_30_days')
    start_date, end_date = get_date_range(date_range)
    
    # Get filters
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    # Generate report data
    report_data = generate_task_report_data(start_date, end_date, user_id, status, priority)
    
    # Get template
    from app.reports.pdf_generator import generate_pdf
    
    # Generate PDF
    pdf_file = generate_pdf(
        'task_report',
        {
            'title': 'Task Management Report',
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M'),
            'data': report_data
        }
    )
    
    # Generate filename
    filename = f"task_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

def generate_task_report_data(start_date, end_date, user_id=None, status=None, priority=None):
    """
    Generate data for task report
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        user_id (str): Filter by user ID
        status (str): Filter by task status
        priority (str): Filter by task priority
        
    Returns:
        dict: Data for the report
    """
    from app.models import Task
    
    # Base query for tasks
    query = Task.query.filter(
        Task.created_at >= start_date,
        Task.created_at <= end_date
    )
    
    # Apply filters
    if user_id:
        query = query.filter(Task.assigned_to_id == user_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    # Get tasks
    tasks = query.all()
    
    # Count tasks by status
    open_tasks_count = sum(1 for task in tasks if task.status == 'open')
    completed_tasks_count = sum(1 for task in tasks if task.status == 'completed')
    
    # Count tasks by priority
    high_priority_tasks_count = sum(1 for task in tasks if task.priority == 'high')
    medium_priority_tasks_count = sum(1 for task in tasks if task.priority == 'medium')
    low_priority_tasks_count = sum(1 for task in tasks if task.priority == 'low')
    
    # Count overdue tasks
    now = datetime.utcnow().date()
    overdue_tasks_count = sum(1 for task in tasks if task.due_date and task.due_date < now and task.status != 'completed')
    
    # Get tasks by user
    users = User.query.all()
    user_labels = [user.get_full_name() for user in users]
    user_open_tasks = []
    user_completed_tasks = []
    
    for user in users:
        user_open_tasks.append(sum(1 for task in tasks if task.assigned_to_id == user.id and task.status == 'open'))
        user_completed_tasks.append(sum(1 for task in tasks if task.assigned_to_id == user.id and task.status == 'completed'))
    
    # Helper function to get lead for a task
    def get_lead(lead_id):
        return Lead.query.get(lead_id)
    
    return {
        'tasks': tasks,
        'open_tasks_count': open_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'high_priority_tasks_count': high_priority_tasks_count,
        'medium_priority_tasks_count': medium_priority_tasks_count,
        'low_priority_tasks_count': low_priority_tasks_count,
        'overdue_tasks_count': overdue_tasks_count,
        'user_labels': user_labels,
        'user_open_tasks': user_open_tasks,
        'user_completed_tasks': user_completed_tasks,
        'get_lead': get_lead
    }

def get_date_range(date_range):
    """
    Get start and end dates based on date range selection
    
    Args:
        date_range (str): Date range selection (today, this_week, this_month, last_30_days, last_90_days, custom)
        
    Returns:
        tuple: (start_date, end_date)
    """
    today = datetime.utcnow().date()
    
    if date_range == 'today':
        return today, today
    
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start_date, end_date
    
    elif date_range == 'last_30_days':
        start_date = today - timedelta(days=30)
        return start_date, today
    
    elif date_range == 'last_90_days':
        start_date = today - timedelta(days=90)
        return start_date, today
    
    elif date_range == 'custom':
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                return start_date, end_date
            except ValueError:
                pass
    
    # Default to last 30 days
    start_date = today - timedelta(days=30)
    return start_date, today

# Report data generation functions
def generate_inventory_report_data(start_date, end_date):
    """
    Generate data for inventory report
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        
    Returns:
        dict: Data for the report
    """
    from app.models import Car
    from sqlalchemy import func
    
    # Get inventory statistics
    total_vehicles = Car.query.filter(
        Car.created_at >= start_date,
        Car.created_at <= end_date
    ).count()
    
    # Calculate average days in stock
    avg_days_query = db.session.query(
        func.avg(func.julianday('now') - func.julianday(Car.created_at)).label('avg_days')
    ).filter(
        Car.status != 'Sold',
        Car.created_at >= start_date,
        Car.created_at <= end_date
    ).first()
    
    avg_days_in_stock = round(avg_days_query.avg_days) if avg_days_query.avg_days else 0
    
    # Calculate average price
    avg_price_query = db.session.query(
        func.avg(Car.price).label('avg_price')
    ).filter(
        Car.created_at >= start_date,
        Car.created_at <= end_date
    ).first()
    
    avg_price = int(avg_price_query.avg_price) if avg_price_query.avg_price else 0
    
    # Get top models
    top_models_query = db.session.query(
        Car.make,
        Car.model,
        func.count(Car.id).label('count'),
        func.avg(func.julianday('now') - func.julianday(Car.created_at)).label('avg_days'),
        func.avg(Car.price).label('avg_price')
    ).filter(
        Car.created_at >= start_date,
        Car.created_at <= end_date
    ).group_by(Car.make, Car.model).order_by(func.count(Car.id).desc()).limit(10).all()
    
    top_models = []
    for model in top_models_query:
        top_models.append({
            'make': model.make,
            'model': model.model,
            'count': model.count,
            'avg_days': round(model.avg_days) if model.avg_days else 0,
            'avg_price': int(model.avg_price) if model.avg_price else 0
        })
    
    # Get status distribution
    status_query = db.session.query(
        Car.status,
        func.count(Car.id).label('count')
    ).filter(
        Car.created_at >= start_date,
        Car.created_at <= end_date
    ).group_by(Car.status).all()
    
    status_distribution = {status.status: status.count for status in status_query}
    
    # Get age distribution
    age_distribution = {
        '0-30 days': 0,
        '31-60 days': 0,
        '61-90 days': 0,
        '91+ days': 0
    }
    
    for car in Car.query.filter(Car.status != 'Sold').all():
        days_in_stock = (datetime.now().date() - car.created_at.date()).days
        if days_in_stock <= 30:
            age_distribution['0-30 days'] += 1
        elif days_in_stock <= 60:
            age_distribution['31-60 days'] += 1
        elif days_in_stock <= 90:
            age_distribution['61-90 days'] += 1
        else:
            age_distribution['91+ days'] += 1
    
    return {
        'total_vehicles': total_vehicles,
        'avg_days_in_stock': avg_days_in_stock,
        'avg_price': avg_price,
        'top_models': top_models,
        'status_distribution': status_distribution,
        'age_distribution': age_distribution
    }

def generate_leads_report_data(start_date, end_date):
    """
    Generate data for leads report
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        
    Returns:
        dict: Data for the report
    """
    from app.models import Lead, Appointment, Car
    from sqlalchemy import func
    
    # Get lead statistics
    total_leads = Lead.query.filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).count()
    
    # Calculate conversion rate (sales / leads)
    sales_count = Car.query.filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).count()
    
    conversion_rate = round((sales_count / total_leads * 100), 1) if total_leads > 0 else 0
    
    # Calculate average response time
    response_times = []
    for lead in Lead.query.filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).all():
        first_comm = lead.communications.order_by(Communication.created_at).first()
        if first_comm:
            response_time = (first_comm.created_at - lead.created_at).total_seconds() / 3600  # hours
            response_times.append(response_time)
    
    avg_response_time = f"{round(sum(response_times) / len(response_times), 1)} hours" if response_times else "N/A"
    
    # Get lead source distribution
    source_query = db.session.query(
        Lead.source,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).group_by(Lead.source).all()
    
    source_distribution = {source.source: source.count for source in source_query}
    
    # Get lead status distribution
    status_query = db.session.query(
        Lead.status,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).group_by(Lead.status).all()
    
    status_distribution = {status.status: status.count for status in status_query}
    
    # Get source metrics
    source_metrics = []
    for source in source_query:
        source_name = source.source
        source_total = source.count
        
        # Get appointments for this source
        appointments = Appointment.query.join(Lead).filter(
            Lead.source == source_name,
            Appointment.scheduled_at >= start_date,
            Appointment.scheduled_at <= end_date
        ).count()
        
        # Get test drives for this source
        test_drives = Appointment.query.join(Lead).filter(
            Lead.source == source_name,
            Appointment.appointment_type == 'Test Drive',
            Appointment.scheduled_at >= start_date,
            Appointment.scheduled_at <= end_date
        ).count()
        
        # Get sales for this source
        sales = Car.query.join(Lead, Car.lead_id == Lead.id).filter(
            Lead.source == source_name,
            Car.status == 'Sold',
            Car.sold_date >= start_date,
            Car.sold_date <= end_date
        ).count()
        
        # Calculate conversion rate
        source_conversion_rate = round((sales / source_total * 100), 1) if source_total > 0 else 0
        
        source_metrics.append({
            'name': source_name,
            'total': source_total,
            'appointments': appointments,
            'test_drives': test_drives,
            'sales': sales,
            'conversion_rate': source_conversion_rate
        })
    
    return {
        'total_leads': total_leads,
        'conversion_rate': conversion_rate,
        'avg_response_time': avg_response_time,
        'source_distribution': source_distribution,
        'status_distribution': status_distribution,
        'source_metrics': source_metrics
    }

def generate_sales_report_data(start_date, end_date):
    """
    Generate data for sales report
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        
    Returns:
        dict: Data for the report
    """
    from app.models import Car
    from sqlalchemy import func
    
    # Get sales statistics
    sales_query = Car.query.filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    )
    
    total_sales = sales_query.count()
    
    # Calculate total revenue
    total_revenue = sum([car.price for car in sales_query.all()])
    
    # Calculate average sale price
    avg_sale_price = int(total_revenue / total_sales) if total_sales > 0 else 0
    
    # Get monthly trend
    monthly_trend_query = db.session.query(
        func.strftime('%Y-%m', Car.sold_date).label('month'),
        func.count(Car.id).label('count'),
        func.sum(Car.price).label('revenue')
    ).filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).group_by(func.strftime('%Y-%m', Car.sold_date)).all()
    
    monthly_trend = []
    for month in monthly_trend_query:
        monthly_trend.append({
            'month': month.month,
            'count': month.count,
            'revenue': int(month.revenue) if month.revenue else 0
        })
    
    # Get vehicle type distribution
    vehicle_type_query = db.session.query(
        Car.vehicle_type,
        func.count(Car.id).label('count'),
        func.sum(Car.price).label('revenue')
    ).filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).group_by(Car.vehicle_type).all()
    
    vehicle_type_distribution = {}
    for vt in vehicle_type_query:
        vehicle_type_distribution[vt.vehicle_type] = {
            'count': vt.count,
            'revenue': int(vt.revenue) if vt.revenue else 0
        }
    
    # Get top selling vehicles
    top_vehicles_query = db.session.query(
        Car.make,
        Car.model,
        func.count(Car.id).label('count'),
        func.sum(Car.price).label('revenue'),
        func.avg(Car.price).label('avg_price'),
        func.avg(Car.profit).label('avg_profit')
    ).filter(
        Car.status == 'Sold',
        Car.sold_date >= start_date,
        Car.sold_date <= end_date
    ).group_by(Car.make, Car.model).order_by(func.count(Car.id).desc()).limit(10).all()
    
    top_vehicles = []
    for vehicle in top_vehicles_query:
        top_vehicles.append({
            'make': vehicle.make,
            'model': vehicle.model,
            'units': vehicle.count,
            'revenue': int(vehicle.revenue) if vehicle.revenue else 0,
            'avg_price': int(vehicle.avg_price) if vehicle.avg_price else 0,
            'avg_profit': int(vehicle.avg_profit) if vehicle.avg_profit else 0
        })
    
    return {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'avg_sale_price': avg_sale_price,
        'monthly_trend': monthly_trend,
        'vehicle_type_distribution': vehicle_type_distribution,
        'top_vehicles': top_vehicles
    }

def generate_performance_report_data(start_date, end_date):
    """
    Generate data for staff performance report
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
        
    Returns:
        dict: Data for the report
    """
    from app.models import User, Lead, Appointment, Car, Communication
    
    # Get all sales staff
    sales_staff = User.query.filter(User.role.in_(['sales', 'manager'])).all()
    
    total_staff = len(sales_staff)
    
    # Calculate staff metrics
    staff_metrics = []
    total_conversion_rate = 0
    total_sales = 0
    
    for user in sales_staff:
        # Get leads assigned to this staff member
        leads_assigned = Lead.query.filter(
            Lead.assigned_to_id == user.id,
            Lead.created_at >= start_date,
            Lead.created_at <= end_date
        ).count()
        
        # Get appointments scheduled by this staff member
        appointments_scheduled = Appointment.query.filter(
            Appointment.created_by_id == user.id,
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        ).count()
        
        # Get test drives conducted by this staff member
        test_drives = Appointment.query.filter(
            Appointment.created_by_id == user.id,
            Appointment.appointment_type == 'Test Drive',
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        ).count()
        
        # Get sales closed by this staff member
        sales_closed = Car.query.filter(
            Car.sold_by_user_id == user.id,
            Car.sold_date >= start_date,
            Car.sold_date <= end_date
        ).count()
        
        # Calculate conversion rate (sales / leads)
        conversion_rate = round((sales_closed / leads_assigned * 100), 1) if leads_assigned > 0 else 0
        
        # Calculate average sale value
        sales = Car.query.filter(
            Car.sold_by_user_id == user.id,
            Car.sold_date >= start_date,
            Car.sold_date <= end_date
        ).all()
        
        total_revenue = sum([car.price for car in sales])
        avg_sale_value = int(total_revenue / sales_closed) if sales_closed > 0 else 0
        
        staff_metrics.append({
            'name': f"{user.first_name} {user.last_name}",
            'leads': leads_assigned,
            'appointments': appointments_scheduled,
            'test_drives': test_drives,
            'sales': sales_closed,
            'conversion_rate': conversion_rate,
            'avg_sale_value': avg_sale_value
        })
        
        total_conversion_rate += conversion_rate
        total_sales += sales_closed
    
    # Calculate averages
    avg_conversion_rate = round(total_conversion_rate / total_staff, 1) if total_staff > 0 else 0
    avg_sales_per_staff = round(total_sales / total_staff, 1) if total_staff > 0 else 0
    
    # Sort by sales (highest first)
    staff_metrics.sort(key=lambda x: x['sales'], reverse=True)
    
    return {
        'total_staff': total_staff,
        'avg_conversion_rate': avg_conversion_rate,
        'avg_sales_per_staff': avg_sales_per_staff,
        'staff_metrics': staff_metrics
    }
