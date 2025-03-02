from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required
from app import db
from app.communications import bp
from app.communications.forms import (EmailForm, SMSForm, EmailTemplateForm, 
                                     SMSTemplateForm, CommunicationSearchForm)
from app.models import Lead, Communication, EmailTemplate, SMSTemplate
from app.email.email_handler import send_email
from app.sms.sms_handler import send_sms
from datetime import datetime

@bp.route('/email/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def send_email_to_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    form = EmailForm()
    
    # Get email templates for dropdown
    templates = EmailTemplate.query.order_by(EmailTemplate.name).all()
    form.template_id.choices = [(0, 'Select a template...')] + [(t.id, t.name) for t in templates]
    
    if form.validate_on_submit():
        if not lead.email:
            flash('This lead does not have an email address!', 'danger')
            return redirect(url_for('communications.send_email_to_lead', lead_id=lead_id))
        
        try:
            # Send the email
            send_email(
                subject=form.subject.data,
                recipient=lead.email,
                body=form.body.data,
                html_body=form.body.data
            )
            
            # Record the communication
            comm = Communication(
                lead_id=lead.id,
                type='Email',
                direction='Outbound',
                content=form.body.data,
                status='Sent'
            )
            db.session.add(comm)
            
            # Update lead status if new
            if lead.status == 'New':
                lead.status = 'Contacted'
                
            db.session.commit()
            flash('Email sent successfully!', 'success')
            return redirect(url_for('leads.view_lead', lead_id=lead.id))
        
        except Exception as e:
            flash(f'Error sending email: {str(e)}', 'danger')
    
    return render_template('communications/email.html', title='Send Email', 
                           form=form, lead=lead)

@bp.route('/sms/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def send_sms_to_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    form = SMSForm()
    
    # Get SMS templates for dropdown
    templates = SMSTemplate.query.order_by(SMSTemplate.name).all()
    form.template_id.choices = [(0, 'Select a template...')] + [(t.id, t.name) for t in templates]
    
    if form.validate_on_submit():
        if not lead.phone:
            flash('This lead does not have a phone number!', 'danger')
            return redirect(url_for('communications.send_sms_to_lead', lead_id=lead_id))
        
        try:
            # Send the SMS
            send_sms(
                to_number=lead.phone,
                body=form.body.data
            )
            
            # Record the communication
            comm = Communication(
                lead_id=lead.id,
                type='SMS',
                direction='Outbound',
                content=form.body.data,
                status='Sent'
            )
            db.session.add(comm)
            
            # Update lead status if new
            if lead.status == 'New':
                lead.status = 'Contacted'
                
            db.session.commit()
            flash('SMS sent successfully!', 'success')
            return redirect(url_for('leads.view_lead', lead_id=lead.id))
        
        except Exception as e:
            flash(f'Error sending SMS: {str(e)}', 'danger')
    
    return render_template('communications/sms.html', title='Send SMS', 
                           form=form, lead=lead)

@bp.route('/template/email/list')
@login_required
def list_email_templates():
    templates = EmailTemplate.query.order_by(EmailTemplate.name).all()
    return render_template('communications/email_templates.html', 
                           title='Email Templates', templates=templates)

@bp.route('/template/email/create', methods=['GET', 'POST'])
@login_required
def create_email_template():
    form = EmailTemplateForm()
    
    if form.validate_on_submit():
        template = EmailTemplate(
            name=form.name.data,
            subject=form.subject.data,
            body=form.body.data,
            purpose=form.purpose.data
        )
        db.session.add(template)
        db.session.commit()
        flash('Email template created successfully!', 'success')
        return redirect(url_for('communications.list_email_templates'))
    
    return render_template('communications/create_email_template.html',
                           title='Create Email Template', form=form)

@bp.route('/template/email/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_email_template(template_id):
    template = EmailTemplate.query.get_or_404(template_id)
    form = EmailTemplateForm()
    
    if form.validate_on_submit():
        template.name = form.name.data
        template.subject = form.subject.data
        template.body = form.body.data
        template.purpose = form.purpose.data
        db.session.commit()
        flash('Email template updated successfully!', 'success')
        return redirect(url_for('communications.list_email_templates'))
        
    elif request.method == 'GET':
        form.name.data = template.name
        form.subject.data = template.subject
        form.body.data = template.body
        form.purpose.data = template.purpose
    
    return render_template('communications/edit_email_template.html',
                           title='Edit Email Template', form=form, template=template)

@bp.route('/template/sms/list')
@login_required
def list_sms_templates():
    templates = SMSTemplate.query.order_by(SMSTemplate.name).all()
    return render_template('communications/sms_templates.html', 
                           title='SMS Templates', templates=templates)

@bp.route('/template/sms/create', methods=['GET', 'POST'])
@login_required
def create_sms_template():
    form = SMSTemplateForm()
    
    if form.validate_on_submit():
        template = SMSTemplate(
            name=form.name.data,
            body=form.body.data,
            purpose=form.purpose.data
        )
        db.session.add(template)
        db.session.commit()
        flash('SMS template created successfully!', 'success')
        return redirect(url_for('communications.list_sms_templates'))
    
    return render_template('communications/create_sms_template.html',
                           title='Create SMS Template', form=form)

@bp.route('/template/sms/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_sms_template(template_id):
    template = SMSTemplate.query.get_or_404(template_id)
    form = SMSTemplateForm()
    
    if form.validate_on_submit():
        template.name = form.name.data
        template.body = form.body.data
        template.purpose = form.purpose.data
        db.session.commit()
        flash('SMS template updated successfully!', 'success')
        return redirect(url_for('communications.list_sms_templates'))
        
    elif request.method == 'GET':
        form.name.data = template.name
        form.body.data = template.body
        form.purpose.data = template.purpose
    
    return render_template('communications/edit_sms_template.html',
                           title='Edit SMS Template', form=form, template=template)

@bp.route('/list')
@login_required
def list_communications():
    form = CommunicationSearchForm()
    page = request.args.get('page', 1, type=int)
    
    # Create base query
    query = Communication.query
    
    # Apply filters if provided in URL
    comm_type = request.args.get('comm_type')
    direction = request.args.get('direction')
    lead_name = request.args.get('lead_name')
    
    if comm_type:
        query = query.filter(Communication.type == comm_type)
        form.comm_type.data = comm_type
    
    if direction:
        query = query.filter(Communication.direction == direction)
        form.direction.data = direction
        
    if lead_name:
        form.lead_name.data = lead_name
        query = query.join(Lead).filter(
            (Lead.first_name.ilike(f'%{lead_name}%')) |
            (Lead.last_name.ilike(f'%{lead_name}%'))
        )
    
    # Order by most recent first
    communications = query.order_by(Communication.sent_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('communications/list.html', title='All Communications', 
                           communications=communications, form=form)

@bp.route('/get_template/<template_type>/<int:template_id>')
@login_required
def get_template(template_type, template_id):
    if template_type == 'email':
        template = EmailTemplate.query.get_or_404(template_id)
        return jsonify({
            'subject': template.subject,
            'body': template.body
        })
    elif template_type == 'sms':
        template = SMSTemplate.query.get_or_404(template_id)
        return jsonify({
            'body': template.body
        })
    
    return jsonify({'error': 'Invalid template type'}), 400
