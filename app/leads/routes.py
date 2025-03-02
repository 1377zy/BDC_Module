from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required
from app import db
from app.leads import bp
from app.leads.forms import LeadForm, VehicleInterestForm, SearchLeadForm
from app.models import Lead, VehicleInterest, Appointment, Communication

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
