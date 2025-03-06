from flask import render_template, redirect, url_for, flash, request, current_app, send_file, make_response
from flask_login import login_required, current_user
from app import db
from app.inventory import bp
from app.models_main import Inventory, Lead, LeadVehicleMatch
from app.leads.forms import InventoryForm, SearchInventoryForm, MatchForm
from sqlalchemy import func
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import BooleanField, SubmitField
import csv
import io

@bp.route('/')
@login_required
def dashboard():
    # Get inventory statistics
    stats = {}
    stats['total'] = Inventory.query.count()
    stats['available'] = Inventory.query.filter_by(status='Available').count()
    stats['on_hold'] = Inventory.query.filter_by(status='On Hold').count()
    stats['sold'] = Inventory.query.filter_by(status='Sold').count()
    stats['new'] = Inventory.query.filter_by(new_or_used='New').count()
    stats['used'] = Inventory.query.filter_by(new_or_used='Used').count()
    
    # Calculate total inventory value
    msrp_result = db.session.query(func.sum(Inventory.msrp)).first()
    sale_price_result = db.session.query(func.sum(Inventory.sale_price)).first()
    stats['total_msrp'] = int(msrp_result[0] or 0)
    stats['total_sale_price'] = int(sale_price_result[0] or 0)
    
    # Get recent activity (using inventory items for now)
    # In a real implementation, you would have a separate activity log table
    recent_activity = []
    recent_inventory = Inventory.query.order_by(Inventory.created_at.desc()).limit(10).all()
    for item in recent_inventory:
        recent_activity.append({
            'timestamp': item.created_at,
            'inventory_id': item.id,
            'vehicle_year': item.year,
            'vehicle_make': item.make,
            'vehicle_model': item.model,
            'stock_number': item.stock_number,
            'action': 'Added to Inventory',
            'status': item.status
        })
    
    # Get popular matches
    # This would be more sophisticated in a real implementation
    popular_matches = []
    match_counts = db.session.query(
        LeadVehicleMatch.inventory_id, 
        func.count(LeadVehicleMatch.id).label('lead_count')
    ).group_by(LeadVehicleMatch.inventory_id).order_by(func.count(LeadVehicleMatch.id).desc()).limit(3).all()
    
    for match_count in match_counts:
        inventory = Inventory.query.get(match_count.inventory_id)
        if inventory:
            popular_matches.append({
                'inventory_id': inventory.id,
                'vehicle_year': inventory.year,
                'vehicle_make': inventory.make,
                'vehicle_model': inventory.model,
                'stock_number': inventory.stock_number,
                'lead_count': match_count.lead_count
            })
    
    return render_template('inventory/dashboard.html', title='Inventory Dashboard', 
                          stats=stats, recent_activity=recent_activity, 
                          popular_matches=popular_matches)

@bp.route('/list')
@login_required
def list_inventory():
    # Get search parameters
    search_form = SearchInventoryForm()
    query = Inventory.query
    
    # Apply filters if provided
    if request.args.get('search_term'):
        search_term = request.args.get('search_term')
        query = query.filter(
            Inventory.make.ilike(f'%{search_term}%') |
            Inventory.model.ilike(f'%{search_term}%') |
            Inventory.stock_number.ilike(f'%{search_term}%')
        )
    
    if request.args.get('make'):
        query = query.filter(Inventory.make == request.args.get('make'))
    
    if request.args.get('model'):
        query = query.filter(Inventory.model == request.args.get('model'))
    
    if request.args.get('year_min'):
        query = query.filter(Inventory.year >= request.args.get('year_min'))
    
    if request.args.get('year_max'):
        query = query.filter(Inventory.year <= request.args.get('year_max'))
    
    if request.args.get('body_style'):
        query = query.filter(Inventory.body_style == request.args.get('body_style'))
    
    if request.args.get('new_or_used'):
        query = query.filter(Inventory.new_or_used == request.args.get('new_or_used'))
    
    if request.args.get('status'):
        query = query.filter(Inventory.status == request.args.get('status'))
    
    # Get inventory items
    inventory = query.order_by(Inventory.created_at.desc()).all()
    
    return render_template('inventory/list.html', title='Inventory', inventory=inventory, form=search_form)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_inventory():
    form = InventoryForm()
    if form.validate_on_submit():
        inventory = Inventory(
            stock_number=form.stock_number.data,
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            trim=form.trim.data,
            body_style=form.body_style.data,
            color_exterior=form.color_exterior.data,
            color_interior=form.color_interior.data,
            engine=form.engine.data,
            transmission=form.transmission.data,
            drivetrain=form.drivetrain.data,
            fuel_type=form.fuel_type.data,
            new_or_used=form.new_or_used.data,
            mileage=form.mileage.data,
            features=form.features.data,
            invoice_price=form.invoice_price.data,
            msrp=form.msrp.data,
            sale_price=form.sale_price.data,
            status=form.status.data,
            location=form.location.data,
            description=form.description.data,
            image_urls=form.image_urls.data
        )
        db.session.add(inventory)
        db.session.commit()
        flash('Vehicle added to inventory successfully!', 'success')
        return redirect(url_for('inventory.list_inventory'))
    return render_template('inventory/create_edit.html', title='Add Inventory', form=form)

@bp.route('/<int:inventory_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_inventory(inventory_id):
    inventory = Inventory.query.get_or_404(inventory_id)
    form = InventoryForm(obj=inventory)
    if form.validate_on_submit():
        inventory.stock_number = form.stock_number.data
        inventory.make = form.make.data
        inventory.model = form.model.data
        inventory.year = form.year.data
        inventory.trim = form.trim.data
        inventory.body_style = form.body_style.data
        inventory.color_exterior = form.color_exterior.data
        inventory.color_interior = form.color_interior.data
        inventory.engine = form.engine.data
        inventory.transmission = form.transmission.data
        inventory.drivetrain = form.drivetrain.data
        inventory.fuel_type = form.fuel_type.data
        inventory.new_or_used = form.new_or_used.data
        inventory.mileage = form.mileage.data
        inventory.features = form.features.data
        inventory.invoice_price = form.invoice_price.data
        inventory.msrp = form.msrp.data
        inventory.sale_price = form.sale_price.data
        inventory.status = form.status.data
        inventory.location = form.location.data
        inventory.description = form.description.data
        inventory.image_urls = form.image_urls.data
        db.session.commit()
        flash('Inventory updated successfully!', 'success')
        return redirect(url_for('inventory.view_inventory', inventory_id=inventory.id))
    return render_template('inventory/create_edit.html', title='Edit Inventory', form=form, inventory=inventory)

@bp.route('/<int:inventory_id>')
@login_required
def view_inventory(inventory_id):
    inventory = Inventory.query.get_or_404(inventory_id)
    return render_template('inventory/view.html', title=f'{inventory.year} {inventory.make} {inventory.model}', inventory=inventory)

@bp.route('/<int:inventory_id>/delete', methods=['POST'])
@login_required
def delete_inventory(inventory_id):
    inventory = Inventory.query.get_or_404(inventory_id)
    db.session.delete(inventory)
    db.session.commit()
    flash('Vehicle removed from inventory', 'success')
    return redirect(url_for('inventory.list_inventory'))

@bp.route('/matches')
@login_required
def list_matches():
    matches = LeadVehicleMatch.query.order_by(LeadVehicleMatch.created_at.desc()).all()
    return render_template('inventory/matches.html', title='Lead-Vehicle Matches', matches=matches)

@bp.route('/create_match', methods=['GET', 'POST'])
@login_required
def create_match():
    form = MatchForm()
    # Populate select fields with dynamic choices
    form.lead_id.choices = [(l.id, f'{l.first_name} {l.last_name}') for l in Lead.query.all()]
    form.inventory_id.choices = [(i.id, f'{i.year} {i.make} {i.model} ({i.stock_number})') for i in Inventory.query.all()]
    
    if form.validate_on_submit():
        match = LeadVehicleMatch(
            lead_id=form.lead_id.data,
            inventory_id=form.inventory_id.data,
            user_id=current_user.id,
            match_score=form.match_score.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(match)
        db.session.commit()
        flash('Match created successfully!', 'success')
        return redirect(url_for('inventory.list_matches'))
    return render_template('inventory/create_match.html', title='Create Match', form=form)

@bp.route('/match/<int:match_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_match(match_id):
    match = LeadVehicleMatch.query.get_or_404(match_id)
    form = MatchForm(obj=match)
    # Populate select fields with dynamic choices
    form.lead_id.choices = [(l.id, f'{l.first_name} {l.last_name}') for l in Lead.query.all()]
    form.inventory_id.choices = [(i.id, f'{i.year} {i.make} {i.model} ({i.stock_number})') for i in Inventory.query.all()]
    
    if form.validate_on_submit():
        match.lead_id = form.lead_id.data
        match.inventory_id = form.inventory_id.data
        match.match_score = form.match_score.data
        match.status = form.status.data
        match.notes = form.notes.data
        db.session.commit()
        flash('Match updated successfully!', 'success')
        return redirect(url_for('inventory.list_matches'))
    return render_template('inventory/create_match.html', title='Edit Match', form=form, match=match)

@bp.route('/match/<int:match_id>/delete', methods=['POST'])
@login_required
def delete_match(match_id):
    match = LeadVehicleMatch.query.get_or_404(match_id)
    db.session.delete(match)
    db.session.commit()
    flash('Match deleted successfully', 'success')
    return redirect(url_for('inventory.list_matches'))

@bp.route('/lead/<int:lead_id>/matches')
@login_required
def lead_matches(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    matches = LeadVehicleMatch.query.filter_by(lead_id=lead_id).all()
    return render_template('inventory/lead_matches.html', title=f'Matches for {lead.first_name} {lead.last_name}', lead=lead, matches=matches)

class ImportInventoryForm(FlaskForm):
    file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    has_header = BooleanField('File has header row', default=True)
    submit = SubmitField('Import')

@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_inventory():
    form = ImportInventoryForm()
    if form.validate_on_submit():
        # Process the uploaded file
        csv_file = form.file.data
        stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream) if form.has_header.data else csv.reader(stream)
        
        # Track import results
        imported = 0
        errors = []
        
        # Process each row
        for row_num, row in enumerate(csv_reader, start=1):
            try:
                # If no header, convert to dict with column names
                if not form.has_header.data:
                    # Define expected columns in order
                    columns = ['stock_number', 'year', 'make', 'model', 'trim', 'new_or_used', 
                              'status', 'color_exterior', 'color_interior', 'body_style', 'mileage', 'engine',
                              'transmission', 'drivetrain', 'fuel_type', 'features', 'invoice_price',
                              'msrp', 'sale_price', 'location', 'description']
                    row = {columns[i]: val for i, val in enumerate(row) if i < len(columns)}
                
                # Check for required fields
                required_fields = ['stock_number', 'year', 'make', 'model', 'new_or_used', 'status']
                missing_fields = [field for field in required_fields if not row.get(field)]
                
                if missing_fields:
                    errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                    continue
                
                # Check if stock number already exists
                existing = Inventory.query.filter_by(stock_number=row['stock_number']).first()
                if existing:
                    errors.append(f"Row {row_num}: Stock number {row['stock_number']} already exists")
                    continue
                
                # Create new inventory item
                inventory = Inventory(
                    stock_number=row['stock_number'],
                    year=int(row['year']),
                    make=row['make'],
                    model=row['model'],
                    trim=row.get('trim', ''),
                    new_or_used=row['new_or_used'],
                    status=row['status'],
                    color_exterior=row.get('color_exterior', ''),
                    color_interior=row.get('color_interior', ''),
                    mileage=int(row.get('mileage', 0)) if row.get('mileage') else 0,
                    sale_price=float(row.get('sale_price', 0)) if row.get('sale_price') else 0,
                    body_style=row.get('body_style', ''),
                    engine=row.get('engine', ''),
                    transmission=row.get('transmission', ''),
                    drivetrain=row.get('drivetrain', ''),
                    fuel_type=row.get('fuel_type', ''),
                    features=row.get('features', ''),
                    msrp=float(row.get('msrp', 0)) if row.get('msrp') else 0,
                    invoice_price=float(row.get('invoice_price', 0)) if row.get('invoice_price') else 0,
                    location=row.get('location', ''),
                    description=row.get('description', '')
                )
                
                db.session.add(inventory)
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: Error - {str(e)}")
        
        # Commit all valid entries
        if imported > 0:
            db.session.commit()
            flash(f'Successfully imported {imported} vehicles to inventory', 'success')
        
        # Show errors if any
        if errors:
            for error in errors[:10]:  # Show first 10 errors
                flash(error, 'danger')
            if len(errors) > 10:
                flash(f'... and {len(errors) - 10} more errors', 'danger')
        
        return redirect(url_for('inventory.list_inventory'))
    
    return render_template('inventory/import.html', title='Import Inventory', form=form)

@bp.route('/download-template')
@login_required
def download_template():
    # Create a CSV in memory
    si = io.StringIO()
    writer = csv.writer(si)
    
    # Write headers
    headers = ['stock_number', 'year', 'make', 'model', 'trim', 'new_or_used', 'status',
              'color_exterior', 'color_interior', 'body_style', 'mileage', 'engine',
              'transmission', 'drivetrain', 'fuel_type', 'features', 'invoice_price',
              'msrp', 'sale_price', 'location', 'description']
    writer.writerow(headers)
    
    # Write sample data
    sample_data = [
        ['A12345', '2023', 'Honda', 'Accord', 'EX-L', 'New', 'Available', 
         'Crystal Black Pearl', 'Black Leather', 'Sedan', '0', '1.5L Turbo',
         'CVT', 'FWD', 'Gasoline', 'Sunroof, Heated Seats', '29995', '32995', '31995',
         'Main Lot', 'Beautiful new Accord with all the features.'],
        ['U98765', '2020', 'Toyota', 'RAV4', 'XLE', 'Used', 'Available',
         'Silver', 'Gray Cloth', 'SUV', '25000', '2.5L 4-Cylinder',
         'Automatic', 'AWD', 'Gasoline', 'Backup Camera, Bluetooth', '24000', '28000', '26995',
         'Used Car Lot', 'Well-maintained RAV4 with low miles.']
    ]
    
    for row in sample_data:
        writer.writerow(row)
    
    # Create response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=inventory_template_{datetime.now().strftime('%Y%m%d')}.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

@bp.route('/export')
@login_required
def export_inventory():
    # Get all inventory or filter based on query parameters
    query = Inventory.query
    
    # Apply filters if provided (similar to list_inventory)
    if request.args.get('status'):
        query = query.filter(Inventory.status == request.args.get('status'))
    
    if request.args.get('new_or_used'):
        query = query.filter(Inventory.new_or_used == request.args.get('new_or_used'))
    
    if request.args.get('make'):
        query = query.filter(Inventory.make == request.args.get('make'))
    
    # Get the inventory items
    inventory = query.all()
    
    # Create a CSV in memory
    si = io.StringIO()
    writer = csv.writer(si)
    
    # Write headers
    headers = ['stock_number', 'year', 'make', 'model', 'trim', 'new_or_used', 'status',
              'color_exterior', 'color_interior', 'body_style', 'mileage', 'engine',
              'transmission', 'drivetrain', 'fuel_type', 'features', 'invoice_price',
              'msrp', 'sale_price', 'location', 'description', 'created_at']
    writer.writerow(headers)
    
    # Write inventory data
    for item in inventory:
        row = [
            item.stock_number, item.year, item.make, item.model, item.trim,
            item.new_or_used, item.status, item.color_exterior, item.color_interior,
            item.body_style, item.mileage, item.engine, item.transmission,
            item.drivetrain, item.fuel_type, item.features, item.invoice_price,
            item.msrp, item.sale_price, item.location, item.description,
            item.created_at.strftime('%Y-%m-%d')
        ]
        writer.writerow(row)
    
    # Create response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=inventory_export_{datetime.now().strftime('%Y%m%d')}.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

# Vehicle Recommendation System
@bp.route('/lead/<int:lead_id>/recommendations')
@login_required
def recommend_vehicles(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    
    # Get the lead's vehicle interests
    vehicle_interests = []
    for interest in lead.vehicle_interests:
        vehicle_interests.append({
            'make': interest.make,
            'model': interest.model,
            'year': interest.year,
            'trim': interest.trim,
            'color_exterior': interest.color_exterior,
            'new_or_used': interest.new_or_used,
            'body_style': interest.body_style
        })
    
    # If no interests, get all available inventory
    if not vehicle_interests:
        recommendations = Inventory.query.filter_by(status='Available').limit(6).all()
        for item in recommendations:
            item.match_score = 'N/A'  # No score since no preferences
        return render_template('inventory/recommendations.html', title=f'Recommendations for {lead.first_name} {lead.last_name}',
                              lead=lead, vehicle_interests=vehicle_interests, recommendations=recommendations)
    
    # Get all available inventory
    available_inventory = Inventory.query.filter_by(status='Available').all()
    
    # Calculate match scores for each inventory item
    scored_inventory = []
    for item in available_inventory:
        best_score = 0
        
        # Compare against each interest
        for interest in vehicle_interests:
            score = 0
            total_points = 0
            
            # Make (25 points)
            if interest.get('make'):
                total_points += 25
                if interest['make'].lower() == item.make.lower():
                    score += 25
            
            # Model (25 points)
            if interest.get('model'):
                total_points += 25
                if interest['model'].lower() == item.model.lower():
                    score += 25
            
            # Year (15 points)
            if interest.get('year'):
                total_points += 15
                interest_year = int(interest['year']) if interest['year'] else 0
                if interest_year == item.year:
                    score += 15
                elif abs(interest_year - item.year) <= 1:
                    score += 10
                elif abs(interest_year - item.year) <= 3:
                    score += 5
            
            # New/Used (10 points)
            if interest.get('new_or_used'):
                total_points += 10
                if interest['new_or_used'] == item.new_or_used:
                    score += 10
            
            # Trim (10 points)
            if interest.get('trim') and item.trim:
                total_points += 10
                if interest['trim'].lower() in item.trim.lower() or item.trim.lower() in interest['trim'].lower():
                    score += 10
            
            # Color (10 points)
            if interest.get('color_exterior') and item.color_exterior:
                total_points += 10
                if interest['color_exterior'].lower() in item.color_exterior.lower() or item.color_exterior.lower() in interest['color_exterior'].lower():
                    score += 10
            
            # Body Style (5 points)
            if interest.get('body_style') and item.body_style:
                total_points += 5
                if interest['body_style'].lower() in item.body_style.lower() or item.body_style.lower() in interest['body_style'].lower():
                    score += 5
            
            # Calculate percentage match (if we have points to calculate)
            match_percentage = int((score / total_points) * 100) if total_points > 0 else 0
            
            # Keep the best score across all interests
            if match_percentage > best_score:
                best_score = match_percentage
        
        # Add match score to the inventory item
        item.match_score = best_score
        scored_inventory.append(item)
    
    # Sort by match score (highest first) and take top 6
    recommendations = sorted(scored_inventory, key=lambda x: x.match_score, reverse=True)[:6]
    
    return render_template('inventory/recommendations.html', title=f'Recommendations for {lead.first_name} {lead.last_name}',
                          lead=lead, vehicle_interests=vehicle_interests, recommendations=recommendations)

# Create a match directly from recommendations
@bp.route('/lead/<int:lead_id>/match/<int:inventory_id>', methods=['GET', 'POST'])
@login_required
def create_match_for_lead(lead_id, inventory_id):
    lead = Lead.query.get_or_404(lead_id)
    inventory = Inventory.query.get_or_404(inventory_id)
    
    # Check if match already exists
    existing_match = LeadVehicleMatch.query.filter_by(lead_id=lead_id, inventory_id=inventory_id).first()
    if existing_match:
        flash(f'This lead is already matched with {inventory.year} {inventory.make} {inventory.model}', 'warning')
        return redirect(url_for('inventory.lead_matches', lead_id=lead_id))
    
    # Create the match
    match = LeadVehicleMatch(
        lead_id=lead_id,
        inventory_id=inventory_id,
        notes=f'Auto-matched from recommendations on {datetime.now().strftime("%Y-%m-%d")}',
        created_by=current_user.id
    )
    
    db.session.add(match)
    db.session.commit()
    
    flash(f'Successfully matched {lead.first_name} {lead.last_name} with {inventory.year} {inventory.make} {inventory.model}', 'success')
    return redirect(url_for('inventory.lead_matches', lead_id=lead_id))
