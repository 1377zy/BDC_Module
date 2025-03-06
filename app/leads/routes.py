from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required
from app import db
from app.leads import bp
from app.leads.forms import LeadForm, VehicleInterestForm, SearchLeadForm
from app.models_main import Lead, VehicleInterest, Appointment, Communication

@bp.route('/list')
@login_required
def list_leads():
    form = SearchLeadForm()
    page = request.args.get('page', 1, type=int)
    
    # Create base query
    query = Lead.query
    
    # Apply filters if provided in URL
    status = request.args.get('status')
    source = request.args.get('source')
    search = request.args.get('search_term')
    
    if status:
        query = query.filter(Lead.status == status)
        form.status.data = status
    
    if source:
        query = query.filter(Lead.source == source)
        form.source.data = source
        
    if search:
        form.search_term.data = search
        query = query.filter(
            (Lead.first_name.ilike(f'%{search}%')) |
            (Lead.last_name.ilike(f'%{search}%')) |
            (Lead.email.ilike(f'%{search}%')) |
            (Lead.phone.ilike(f'%{search}%'))
        )
    
    # Order by most recent first
    leads = query.order_by(Lead.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('leads/list.html', title='All Leads', 
                           leads=leads, form=form)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_lead():
    form = LeadForm()
    if form.validate_on_submit():
        lead = Lead(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            source=form.source.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(lead)
        db.session.commit()
        flash('Lead created successfully!')
        return redirect(url_for('leads.view_lead', lead_id=lead.id))
    return render_template('leads/create.html', title='Create Lead', form=form)

@bp.route('/<int:lead_id>')
@login_required
def view_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    vehicle_interests = VehicleInterest.query.filter_by(lead_id=lead_id).all()
    appointments = lead.appointments.order_by(Appointment.date.desc()).all()
    communications = lead.communications.order_by(Communication.sent_at.desc()).all()
    
    return render_template('leads/view.html', title=f'Lead: {lead.first_name} {lead.last_name}',
                           lead=lead, vehicle_interests=vehicle_interests,
                           appointments=appointments, communications=communications)

@bp.route('/edit/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def edit_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    form = LeadForm()
    
    if form.validate_on_submit():
        lead.first_name = form.first_name.data
        lead.last_name = form.last_name.data
        lead.email = form.email.data
        lead.phone = form.phone.data
        lead.source = form.source.data
        lead.status = form.status.data
        lead.notes = form.notes.data
        
        db.session.commit()
        flash('Lead updated successfully!')
        return redirect(url_for('leads.view_lead', lead_id=lead.id))
    
    elif request.method == 'GET':
        form.first_name.data = lead.first_name
        form.last_name.data = lead.last_name
        form.email.data = lead.email
        form.phone.data = lead.phone
        form.source.data = lead.source
        form.status.data = lead.status
        form.notes.data = lead.notes
        
    return render_template('leads/edit.html', title='Edit Lead', form=form, lead=lead)

@bp.route('/<int:lead_id>/add_vehicle_interest', methods=['GET', 'POST'])
@login_required
def add_vehicle_interest(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    form = VehicleInterestForm()
    
    if form.validate_on_submit():
        vehicle_interest = VehicleInterest(
            lead_id=lead.id,
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            new_or_used=form.new_or_used.data,
            notes=form.notes.data
        )
        db.session.add(vehicle_interest)
        db.session.commit()
        flash('Vehicle interest added successfully!')
        return redirect(url_for('leads.view_lead', lead_id=lead.id))
        
    return render_template('leads/add_vehicle_interest.html', 
                           title='Add Vehicle Interest', form=form, lead=lead)

@bp.route('/download-template')
@login_required
def download_template():
    """Download a CSV template for lead imports"""
    import csv
    from io import StringIO
    import datetime
    
    # Create CSV data in memory
    csv_data = StringIO()
    writer = csv.writer(csv_data)
    
    # Write header row with all required and optional fields
    writer.writerow([
        'first_name', 'last_name', 'email', 'phone', 'source', 'status', 
        'notes', 'make', 'model', 'year', 'new_or_used'
    ])
    
    # Write a sample row to show the expected format
    writer.writerow([
        'John', 'Doe', 'john.doe@example.com', '555-123-4567', 'Website', 'New',
        'Interested in financing options', 'Toyota', 'Camry', '2023', 'New'
    ])
    
    # Write another sample row
    writer.writerow([
        'Jane', 'Smith', 'jane.smith@example.com', '555-987-6543', 'Walk-in', 'Contacted',
        'Prefers to be contacted in the evening', 'Honda', 'Civic', '2020', 'Used'
    ])
    
    # Prepare response
    from flask import Response
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"lead_import_template_{timestamp}.csv"
    
    return Response(
        csv_data.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_leads():
    """Import leads from a CSV file"""
    import csv
    from io import TextIOWrapper
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and file.filename.endswith('.csv'):
            # Process the CSV file
            csv_file = TextIOWrapper(file, encoding='utf-8')
            csv_reader = csv.DictReader(csv_file)
            
            # Validate the CSV structure
            required_fields = ['first_name', 'last_name', 'email', 'phone']
            first_row = next(csv_reader, None)
            csv_file.seek(0)  # Reset to beginning of file
            next(csv_reader)  # Skip header row again
            
            missing_fields = [field for field in required_fields if field not in first_row]
            if missing_fields:
                flash(f'CSV file is missing required fields: {", ".join(missing_fields)}', 'danger')
                return redirect(request.url)
            
            # Process each row
            success_count = 0
            error_count = 0
            
            for row in csv_reader:
                try:
                    # Create new lead
                    lead = Lead(
                        first_name=row.get('first_name', '').strip(),
                        last_name=row.get('last_name', '').strip(),
                        email=row.get('email', '').strip(),
                        phone=row.get('phone', '').strip(),
                        source=row.get('source', 'Import').strip(),
                        status=row.get('status', 'New').strip(),
                        notes=row.get('notes', '').strip()
                    )
                    db.session.add(lead)
                    db.session.flush()  # Get the lead ID without committing
                    
                    # Add vehicle interest if provided
                    if all(key in row and row[key].strip() for key in ['make', 'model']):
                        vehicle_interest = VehicleInterest(
                            lead_id=lead.id,
                            make=row.get('make', '').strip(),
                            model=row.get('model', '').strip(),
                            year=row.get('year', '').strip(),
                            new_or_used=row.get('new_or_used', '').strip(),
                            notes=''
                        )
                        db.session.add(vehicle_interest)
                    
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error importing lead: {e}")
            
            # Commit all successful imports
            db.session.commit()
            
            if success_count > 0:
                flash(f'Successfully imported {success_count} leads', 'success')
            if error_count > 0:
                flash(f'Failed to import {error_count} leads', 'warning')
                
            return redirect(url_for('leads.list_leads'))
        else:
            flash('File must be a CSV', 'danger')
            return redirect(request.url)
    
    return render_template('leads/import.html', title='Import Leads')
