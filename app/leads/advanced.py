"""
Advanced Lead Management

This module provides advanced lead management features:
1. Lead scoring and prioritization
2. Lead activity timeline
3. Automated follow-up sequences
4. Lead lifecycle management
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.leads import bp
from app.models import Lead, LeadActivity, LeadFollowUpSequence, FollowUpStep, LeadSequenceAssignment
from app.utils.decorators import admin_required, manager_required, role_required
from datetime import datetime, timedelta
import json

@bp.route('/leads/advanced')
@login_required
def advanced_dashboard():
    """Advanced lead management dashboard"""
    # Get lead statistics
    total_leads = Lead.query.count()
    new_leads = Lead.query.filter_by(lifecycle_stage='new').count()
    engaged_leads = Lead.query.filter_by(lifecycle_stage='engaged').count()
    qualified_leads = Lead.query.filter_by(lifecycle_stage='qualified').count()
    opportunity_leads = Lead.query.filter_by(lifecycle_stage='opportunity').count()
    customer_leads = Lead.query.filter_by(lifecycle_stage='customer').count()
    closed_leads = Lead.query.filter_by(lifecycle_stage='closed').count()
    
    # Get high priority leads (score > 70)
    high_priority_leads = Lead.query.filter(Lead.score > 70).order_by(Lead.score.desc()).limit(10).all()
    
    # Get leads requiring follow-up today
    today = datetime.utcnow().date()
    follow_up_leads = Lead.query.filter(
        db.func.date(Lead.follow_up_date) == today
    ).order_by(Lead.follow_up_date).all()
    
    # Get active sequences
    active_sequences = LeadFollowUpSequence.query.filter_by(is_active=True).all()
    
    return render_template('leads/advanced_dashboard.html',
                          total_leads=total_leads,
                          new_leads=new_leads,
                          engaged_leads=engaged_leads,
                          qualified_leads=qualified_leads,
                          opportunity_leads=opportunity_leads,
                          customer_leads=customer_leads,
                          closed_leads=closed_leads,
                          high_priority_leads=high_priority_leads,
                          follow_up_leads=follow_up_leads,
                          active_sequences=active_sequences)

@bp.route('/leads/<int:lead_id>/activity')
@login_required
def lead_activity(lead_id):
    """View lead activity timeline"""
    lead = Lead.query.get_or_404(lead_id)
    activities = lead.activities.order_by(LeadActivity.created_at.desc()).all()
    
    # Get related data for activities
    for activity in activities:
        if activity.related_entity_type == 'communication':
            from app.models import Communication
            activity.related_entity = Communication.query.get(activity.related_entity_id)
        elif activity.related_entity_type == 'appointment':
            from app.models import Appointment
            activity.related_entity = Appointment.query.get(activity.related_entity_id)
    
    return render_template('leads/activity.html', lead=lead, activities=activities)

@bp.route('/leads/<int:lead_id>/add-activity', methods=['POST'])
@login_required
def add_lead_activity(lead_id):
    """Add a manual activity to a lead's timeline"""
    lead = Lead.query.get_or_404(lead_id)
    
    activity_type = request.form.get('activity_type')
    description = request.form.get('description')
    
    if not activity_type or not description:
        flash('Activity type and description are required', 'danger')
        return redirect(url_for('leads.lead_activity', lead_id=lead_id))
    
    activity = LeadActivity(
        lead=lead,
        activity_type=activity_type,
        description=description,
        performed_by=current_user
    )
    
    db.session.add(activity)
    
    # Update lead's last activity date
    lead.last_activity_date = datetime.utcnow()
    
    # Recalculate lead score
    lead.calculate_score()
    
    # Update lifecycle stage
    lead.update_lifecycle_stage()
    
    db.session.commit()
    
    flash('Activity added successfully', 'success')
    return redirect(url_for('leads.lead_activity', lead_id=lead_id))

@bp.route('/leads/sequences')
@login_required
@role_required(['manager', 'admin'])
def follow_up_sequences():
    """Manage follow-up sequences"""
    sequences = LeadFollowUpSequence.query.all()
    return render_template('leads/sequences.html', sequences=sequences)

@bp.route('/leads/sequences/new', methods=['GET', 'POST'])
@login_required
@role_required(['manager', 'admin'])
def new_sequence():
    """Create a new follow-up sequence"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        trigger_type = request.form.get('trigger_type')
        lead_source = request.form.get('lead_source') or None
        
        if not name or not trigger_type:
            flash('Name and trigger type are required', 'danger')
            return redirect(url_for('leads.new_sequence'))
        
        sequence = LeadFollowUpSequence(
            name=name,
            description=description,
            trigger_type=trigger_type,
            lead_source=lead_source,
            created_by=current_user,
            is_active=True
        )
        
        db.session.add(sequence)
        db.session.commit()
        
        flash('Sequence created successfully. Now add steps to your sequence.', 'success')
        return redirect(url_for('leads.edit_sequence', sequence_id=sequence.id))
    
    # GET request
    lead_sources = db.session.query(Lead.source).distinct().all()
    lead_sources = [source[0] for source in lead_sources if source[0]]
    
    return render_template('leads/new_sequence.html', lead_sources=lead_sources)

@bp.route('/leads/sequences/<int:sequence_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['manager', 'admin'])
def edit_sequence(sequence_id):
    """Edit a follow-up sequence and its steps"""
    sequence = LeadFollowUpSequence.query.get_or_404(sequence_id)
    
    if request.method == 'POST':
        sequence.name = request.form.get('name')
        sequence.description = request.form.get('description')
        sequence.trigger_type = request.form.get('trigger_type')
        sequence.lead_source = request.form.get('lead_source') or None
        sequence.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('Sequence updated successfully', 'success')
        return redirect(url_for('leads.follow_up_sequences'))
    
    # GET request
    steps = sequence.steps.order_by(FollowUpStep.step_number).all()
    lead_sources = db.session.query(Lead.source).distinct().all()
    lead_sources = [source[0] for source in lead_sources if source[0]]
    
    # Get email and SMS templates for step creation
    from app.models import EmailTemplate, SMSTemplate
    email_templates = EmailTemplate.query.all()
    sms_templates = SMSTemplate.query.all()
    
    return render_template('leads/edit_sequence.html', 
                          sequence=sequence, 
                          steps=steps,
                          lead_sources=lead_sources,
                          email_templates=email_templates,
                          sms_templates=sms_templates)

@bp.route('/leads/sequences/<int:sequence_id>/steps/add', methods=['POST'])
@login_required
@role_required(['manager', 'admin'])
def add_sequence_step(sequence_id):
    """Add a step to a follow-up sequence"""
    sequence = LeadFollowUpSequence.query.get_or_404(sequence_id)
    
    # Get the next step number
    next_step = 1
    last_step = sequence.steps.order_by(FollowUpStep.step_number.desc()).first()
    if last_step:
        next_step = last_step.step_number + 1
    
    action_type = request.form.get('action_type')
    delay_days = int(request.form.get('delay_days', 0))
    delay_hours = int(request.form.get('delay_hours', 0))
    
    step = FollowUpStep(
        sequence=sequence,
        step_number=next_step,
        delay_days=delay_days,
        delay_hours=delay_hours,
        action_type=action_type,
        is_active=True
    )
    
    # Set template or task details based on action type
    if action_type == 'email':
        step.template_id = request.form.get('email_template_id')
    elif action_type == 'sms':
        step.template_id = request.form.get('sms_template_id')
    elif action_type == 'task':
        step.task_description = request.form.get('task_description')
        step.task_assignee_role = request.form.get('task_assignee_role')
    
    db.session.add(step)
    db.session.commit()
    
    flash('Step added successfully', 'success')
    return redirect(url_for('leads.edit_sequence', sequence_id=sequence_id))

@bp.route('/leads/sequences/<int:sequence_id>/steps/<int:step_id>/delete', methods=['POST'])
@login_required
@role_required(['manager', 'admin'])
def delete_sequence_step(sequence_id, step_id):
    """Delete a step from a follow-up sequence"""
    step = FollowUpStep.query.get_or_404(step_id)
    
    # Verify the step belongs to the specified sequence
    if step.sequence_id != sequence_id:
        flash('Invalid step', 'danger')
        return redirect(url_for('leads.edit_sequence', sequence_id=sequence_id))
    
    # Get the step number for reordering
    deleted_step_number = step.step_number
    
    # Delete the step
    db.session.delete(step)
    
    # Reorder the remaining steps
    for s in FollowUpStep.query.filter(
        FollowUpStep.sequence_id == sequence_id,
        FollowUpStep.step_number > deleted_step_number
    ).all():
        s.step_number -= 1
    
    db.session.commit()
    
    flash('Step deleted successfully', 'success')
    return redirect(url_for('leads.edit_sequence', sequence_id=sequence_id))

@bp.route('/leads/sequences/<int:sequence_id>/delete', methods=['POST'])
@login_required
@role_required(['manager', 'admin'])
def delete_sequence(sequence_id):
    """Delete a follow-up sequence and all its steps"""
    sequence = LeadFollowUpSequence.query.get_or_404(sequence_id)
    
    # Delete all steps first (should cascade, but being explicit)
    for step in sequence.steps:
        db.session.delete(step)
    
    # Delete sequence assignments
    assignments = LeadSequenceAssignment.query.filter_by(sequence_id=sequence_id).all()
    for assignment in assignments:
        db.session.delete(assignment)
    
    # Delete the sequence
    db.session.delete(sequence)
    db.session.commit()
    
    flash('Sequence deleted successfully', 'success')
    return redirect(url_for('leads.follow_up_sequences'))

@bp.route('/leads/<int:lead_id>/assign-sequence', methods=['POST'])
@login_required
def assign_sequence(lead_id):
    """Assign a lead to a follow-up sequence"""
    lead = Lead.query.get_or_404(lead_id)
    sequence_id = request.form.get('sequence_id')
    
    if not sequence_id:
        flash('Sequence is required', 'danger')
        return redirect(url_for('leads.view', lead_id=lead_id))
    
    sequence = LeadFollowUpSequence.query.get_or_404(sequence_id)
    
    # Check if the lead is already assigned to this sequence
    existing = LeadSequenceAssignment.query.filter_by(
        lead_id=lead_id,
        sequence_id=sequence_id,
        is_active=True
    ).first()
    
    if existing:
        flash('Lead is already assigned to this sequence', 'warning')
        return redirect(url_for('leads.view', lead_id=lead_id))
    
    # Calculate the next step due date
    first_step = sequence.steps.order_by(FollowUpStep.step_number).first()
    next_due = None
    
    if first_step:
        next_due = datetime.utcnow() + timedelta(
            days=first_step.delay_days,
            hours=first_step.delay_hours
        )
    
    # Create the assignment
    assignment = LeadSequenceAssignment(
        lead=lead,
        sequence=sequence,
        current_step=0,
        is_active=True,
        next_step_due_at=next_due
    )
    
    db.session.add(assignment)
    
    # Add an activity record
    activity = LeadActivity(
        lead=lead,
        activity_type='sequence_assigned',
        description=f'Assigned to sequence: {sequence.name}',
        performed_by=current_user
    )
    
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Lead assigned to sequence: {sequence.name}', 'success')
    return redirect(url_for('leads.view', lead_id=lead_id))

@bp.route('/leads/process-sequences')
@login_required
@role_required(['manager', 'admin'])
def process_sequences():
    """Manually trigger processing of follow-up sequences"""
    from app.leads.tasks import process_follow_up_sequences
    count = process_follow_up_sequences()
    
    flash(f'Processed {count} follow-up steps', 'success')
    return redirect(url_for('leads.advanced_dashboard'))

@bp.route('/leads/<int:lead_id>/score')
@login_required
def lead_score_details(lead_id):
    """View detailed breakdown of a lead's score"""
    lead = Lead.query.get_or_404(lead_id)
    
    # Recalculate score to get fresh data
    lead.calculate_score()
    
    # Get score components
    source_scores = {
        'Website': 10,
        'Referral': 30,
        'Walk-in': 40,
        'Phone': 20,
        'Email': 15,
        'Social Media': 10,
        'Third Party': 5
    }
    
    source_score = source_scores.get(lead.source, 0)
    contact_score = 0
    if lead.email:
        contact_score += 10
    if lead.phone:
        contact_score += 10
    
    interests_count = lead.vehicle_interests.count()
    interests_score = min(interests_count * 5, 15)
    
    comms_count = lead.communications.count()
    comms_score = min(comms_count * 2, 20)
    
    appointments_count = lead.appointments.count()
    appointments_score = min(appointments_count * 10, 30)
    
    recency_score = 0
    if lead.last_activity_date:
        days_since_activity = (datetime.utcnow() - lead.last_activity_date).days
        if days_since_activity < 1:
            recency_score = 15
        elif days_since_activity < 3:
            recency_score = 10
        elif days_since_activity < 7:
            recency_score = 5
    
    score_components = {
        'Source': source_score,
        'Contact Info': contact_score,
        'Vehicle Interests': interests_score,
        'Communications': comms_score,
        'Appointments': appointments_score,
        'Recency': recency_score
    }
    
    return render_template('leads/score_details.html', 
                          lead=lead, 
                          score_components=score_components,
                          total_score=lead.score)

@bp.route('/leads/lifecycle')
@login_required
def lifecycle_management():
    """Lead lifecycle management view"""
    # Get leads by lifecycle stage
    new_leads = Lead.query.filter_by(lifecycle_stage='new').all()
    engaged_leads = Lead.query.filter_by(lifecycle_stage='engaged').all()
    qualified_leads = Lead.query.filter_by(lifecycle_stage='qualified').all()
    opportunity_leads = Lead.query.filter_by(lifecycle_stage='opportunity').all()
    customer_leads = Lead.query.filter_by(lifecycle_stage='customer').all()
    closed_leads = Lead.query.filter_by(lifecycle_stage='closed').all()
    
    return render_template('leads/lifecycle.html',
                          new_leads=new_leads,
                          engaged_leads=engaged_leads,
                          qualified_leads=qualified_leads,
                          opportunity_leads=opportunity_leads,
                          customer_leads=customer_leads,
                          closed_leads=closed_leads)

@bp.route('/leads/update-lifecycle-stage', methods=['POST'])
@login_required
def update_lifecycle_stage():
    """Update a lead's lifecycle stage"""
    lead_id = request.form.get('lead_id')
    stage = request.form.get('stage')
    
    if not lead_id or not stage:
        return jsonify({'success': False, 'message': 'Lead ID and stage are required'})
    
    lead = Lead.query.get_or_404(lead_id)
    
    # Validate stage
    valid_stages = ['new', 'engaged', 'qualified', 'opportunity', 'customer', 'closed']
    if stage not in valid_stages:
        return jsonify({'success': False, 'message': 'Invalid stage'})
    
    # Update the lead's lifecycle stage
    lead.lifecycle_stage = stage
    
    # Record the activity
    activity = LeadActivity(
        lead=lead,
        activity_type='lifecycle_update',
        description=f'Lifecycle stage updated to: {stage}',
        performed_by=current_user
    )
    db.session.add(activity)
    
    # Update lead's last activity date
    lead.last_activity_date = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})
