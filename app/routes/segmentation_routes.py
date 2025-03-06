from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
# Import directly from the main models.py file
from app import db
from datetime import datetime
from sqlalchemy import or_, and_
import json

# Import the models we need
from app.models_main import Lead, Segment, SegmentCriteria, LeadInterest, LeadBudget, LeadTimeline, CustomSegmentField, CustomSegmentValue

segmentation_bp = Blueprint('segmentation', __name__)

def register_segmentation_routes(app):
    """Register the segmentation blueprint with the Flask app."""
    app.register_blueprint(segmentation_bp, url_prefix='/segmentation')

@segmentation_bp.route('/leads/segmentation')
def lead_segmentation():
    """Display the lead segmentation page with all segments."""
    segments = Segment.query.all()
    custom_fields = CustomSegmentField.query.all()
    
    return render_template('leads/segmentation.html', 
                          segments=segments,
                          custom_fields=custom_fields)

@segmentation_bp.route('/leads/segment/new')
def new_segment():
    """Display the segment creation form."""
    segment_type = request.args.get('type', 'custom')
    custom_fields = CustomSegmentField.query.all()
    
    return render_template('leads/segment_editor.html',
                          segment=None,
                          segment_type=segment_type,
                          criteria=None,
                          criteria_logic='and',
                          custom_fields=custom_fields)

@segmentation_bp.route('/leads/segment/<segment_id>')
def view_segment(segment_id):
    """View a specific segment and its leads."""
    segment = Segment.query.get_or_404(segment_id)
    
    # Get segment type
    segment_type = 'custom'
    if segment.criteria:
        first_criterion = segment.criteria[0]
        if first_criterion.field.startswith('interest_'):
            segment_type = 'interest'
        elif first_criterion.field.startswith('budget_'):
            segment_type = 'budget'
        elif first_criterion.field.startswith('timeline_'):
            segment_type = 'timeline'
    
    # Get criteria with display names
    criteria = []
    for criterion in segment.criteria:
        field_display = criterion.field.replace('_', ' ').title()
        operator_display = criterion.operator.replace('_', ' ').title()
        
        criteria.append({
            'field': criterion.field,
            'field_display': field_display,
            'operator': criterion.operator,
            'operator_display': operator_display,
            'value': criterion.value
        })
    
    # Get leads in segment
    leads = segment.leads
    
    return render_template('leads/view_segment.html',
                          segment=segment,
                          segment_type=segment_type,
                          criteria=criteria,
                          criteria_logic=segment.criteria_logic,
                          leads=leads)

@segmentation_bp.route('/leads/segment/<segment_id>/edit')
def edit_segment(segment_id):
    """Edit a specific segment."""
    segment = Segment.query.get_or_404(segment_id)
    
    # Get segment type
    segment_type = 'custom'
    if segment.criteria:
        first_criterion = segment.criteria[0]
        if first_criterion.field.startswith('interest_'):
            segment_type = 'interest'
        elif first_criterion.field.startswith('budget_'):
            segment_type = 'budget'
        elif first_criterion.field.startswith('timeline_'):
            segment_type = 'timeline'
    
    custom_fields = CustomSegmentField.query.all()
    
    return render_template('leads/segment_editor.html',
                          segment=segment,
                          segment_type=segment_type,
                          criteria=segment.criteria,
                          criteria_logic=segment.criteria_logic,
                          custom_fields=custom_fields)

@segmentation_bp.route('/leads/segment/save/<segment_id>', methods=['POST'])
def save_segment(segment_id):
    """Save a new or existing segment."""
    name = request.form.get('name')
    description = request.form.get('description')
    is_dynamic = 'is_dynamic' in request.form
    segment_type = request.form.get('segment_type')
    criteria_logic = request.form.get('criteria_logic', 'and')
    
    if not name:
        flash('Segment name is required.', 'danger')
        return redirect(url_for('segmentation.new_segment'))
    
    # Create or update segment
    if segment_id == 'new':
        segment = Segment(
            name=name,
            description=description,
            is_dynamic=is_dynamic,
            criteria_logic=criteria_logic,
            created_by=1  # Replace with current_user.id in production
        )
        db.session.add(segment)
        flash('Segment created successfully!', 'success')
    else:
        segment = Segment.query.get_or_404(segment_id)
        segment.name = name
        segment.description = description
        segment.is_dynamic = is_dynamic
        segment.criteria_logic = criteria_logic
        segment.updated_at = datetime.utcnow()
        
        # Delete existing criteria
        SegmentCriteria.query.filter_by(segment_id=segment.id).delete()
        flash('Segment updated successfully!', 'success')
    
    db.session.commit()
    
    # Process criteria
    criteria_data = []
    for key, value in request.form.items():
        if key.startswith('criteria[') and key.endswith('][field]'):
            index = key.split('[')[1].split(']')[0]
            field = request.form.get(f'criteria[{index}][field]')
            operator = request.form.get(f'criteria[{index}][operator]')
            value = request.form.get(f'criteria[{index}][value]')
            
            if field and operator and value:
                criteria_data.append({
                    'field': field,
                    'operator': operator,
                    'value': value
                })
    
    # Add criteria to segment
    for criterion_data in criteria_data:
        criterion = SegmentCriteria(
            segment_id=segment.id,
            field=criterion_data['field'],
            operator=criterion_data['operator'],
            value=criterion_data['value']
        )
        db.session.add(criterion)
    
    db.session.commit()
    
    # If dynamic segment, update leads immediately
    if segment.is_dynamic:
        update_segment_leads(segment)
    
    return redirect(url_for('segmentation.view_segment', segment_id=segment.id))

@segmentation_bp.route('/leads/segment/<segment_id>/delete')
def delete_segment(segment_id):
    """Delete a segment."""
    segment = Segment.query.get_or_404(segment_id)
    
    # Delete criteria first
    SegmentCriteria.query.filter_by(segment_id=segment.id).delete()
    
    # Delete segment
    db.session.delete(segment)
    db.session.commit()
    
    flash('Segment deleted successfully!', 'success')
    return redirect(url_for('segmentation.lead_segmentation'))

@segmentation_bp.route('/leads/segment/<segment_id>/update', methods=['POST'])
def update_segment(segment_id):
    """Update a dynamic segment's leads."""
    segment = Segment.query.get_or_404(segment_id)
    
    if not segment.is_dynamic:
        return jsonify({'success': False, 'message': 'This is not a dynamic segment.'})
    
    success = update_segment_leads(segment)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Failed to update segment leads.'})

@segmentation_bp.route('/leads/segment/<segment_id>/leads')
def get_segment_leads(segment_id):
    """Get leads for a segment (AJAX)."""
    segment = Segment.query.get_or_404(segment_id)
    leads = segment.leads
    
    return render_template('leads/segment_leads_table.html', leads=leads)

@segmentation_bp.route('/leads/segment/<segment_id>/preview', methods=['POST'])
def preview_segment(segment_id):
    """Preview leads that would match segment criteria (AJAX)."""
    segment_id = segment_id
    criteria_logic = request.form.get('criteria_logic', 'and')
    
    # Process criteria
    criteria_data = []
    for key, value in request.form.items():
        if key.startswith('criteria[') and key.endswith('][field]'):
            index = key.split('[')[1].split(']')[0]
            field = request.form.get(f'criteria[{index}][field]')
            operator = request.form.get(f'criteria[{index}][operator]')
            value = request.form.get(f'criteria[{index}][value]')
            
            if field and operator and value:
                criteria_data.append({
                    'field': field,
                    'operator': operator,
                    'value': value
                })
    
    # Find matching leads
    leads = find_matching_leads(criteria_data, criteria_logic)
    
    return render_template('leads/segment_leads_table.html', leads=leads, is_preview=True)

@segmentation_bp.route('/leads/segment/<segment_id>/export')
def export_segment_leads(segment_id):
    """Export leads in a segment to CSV."""
    segment = Segment.query.get_or_404(segment_id)
    leads = segment.leads
    
    # Implementation for CSV export would go here
    # Similar to the export_search_results function
    
    flash('Export functionality will be implemented soon.', 'info')
    return redirect(url_for('segmentation.view_segment', segment_id=segment.id))

@segmentation_bp.route('/leads/segment/<segment_id>/search', methods=['GET'])
def search_leads_for_segment(segment_id):
    """Search for leads to add to a static segment (AJAX)."""
    segment = Segment.query.get_or_404(segment_id)
    query = request.args.get('query', '')
    
    if not query or len(query) < 2:
        return jsonify({'leads': []})
    
    # Find leads that match the search query but are not in the segment
    segment_lead_ids = [lead.id for lead in segment.leads]
    
    leads = Lead.query.filter(
        Lead.id.notin_(segment_lead_ids),
        or_(
            Lead.first_name.ilike(f'%{query}%'),
            Lead.last_name.ilike(f'%{query}%'),
            Lead.email.ilike(f'%{query}%'),
            Lead.phone.ilike(f'%{query}%')
        )
    ).limit(50).all()
    
    lead_data = []
    for lead in leads:
        lead_data.append({
            'id': lead.id,
            'first_name': lead.first_name,
            'last_name': lead.last_name,
            'email': lead.email,
            'phone': lead.phone,
            'status': lead.status
        })
    
    return jsonify({'leads': lead_data})

@segmentation_bp.route('/leads/segment/<segment_id>/add_leads', methods=['POST'])
def add_leads_to_segment(segment_id):
    """Add selected leads to a static segment."""
    segment = Segment.query.get_or_404(segment_id)
    
    if segment.is_dynamic:
        flash('Cannot manually add leads to a dynamic segment.', 'danger')
        return redirect(url_for('segmentation.view_segment', segment_id=segment.id))
    
    lead_ids = request.form.getlist('lead_ids[]')
    
    if not lead_ids:
        flash('No leads selected.', 'warning')
        return redirect(url_for('segmentation.view_segment', segment_id=segment.id))
    
    added_count = 0
    for lead_id in lead_ids:
        lead = Lead.query.get(lead_id)
        if lead and lead not in segment.leads:
            segment.leads.append(lead)
            added_count += 1
    
    db.session.commit()
    
    flash(f'Added {added_count} leads to the segment.', 'success')
    return redirect(url_for('segmentation.view_segment', segment_id=segment.id))

@segmentation_bp.route('/leads/segment/<segment_id>/remove_lead', methods=['POST'])
def remove_lead_from_segment(segment_id):
    """Remove a lead from a static segment (AJAX)."""
    segment = Segment.query.get_or_404(segment_id)
    lead_id = request.form.get('lead_id')
    
    if segment.is_dynamic:
        return jsonify({'success': False, 'message': 'Cannot manually remove leads from a dynamic segment.'})
    
    lead = Lead.query.get(lead_id)
    if lead and lead in segment.leads:
        segment.leads.remove(lead)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Lead not found in segment.'})

@segmentation_bp.route('/leads/custom_fields')
def custom_segment_fields():
    """Display custom segment fields."""
    custom_fields = CustomSegmentField.query.all()
    return render_template('leads/custom_segment_fields.html', custom_fields=custom_fields)

@segmentation_bp.route('/leads/custom_field/add', methods=['POST'])
def add_custom_field():
    """Add a new custom segment field."""
    name = request.form.get('name')
    display_name = request.form.get('display_name')
    field_type = request.form.get('field_type')
    
    if not name or not display_name or not field_type:
        flash('All fields are required.', 'danger')
        return redirect(url_for('segmentation.custom_segment_fields'))
    
    # Check if field already exists
    existing_field = CustomSegmentField.query.filter_by(name=name).first()
    if existing_field:
        flash('A field with this name already exists.', 'danger')
        return redirect(url_for('segmentation.custom_segment_fields'))
    
    # Create new field
    custom_field = CustomSegmentField(
        name=name,
        display_name=display_name,
        field_type=field_type
    )
    db.session.add(custom_field)
    db.session.commit()
    
    flash('Custom field added successfully!', 'success')
    return redirect(url_for('segmentation.custom_segment_fields'))

@segmentation_bp.route('/leads/custom_field/<field_id>/delete')
def delete_custom_field(field_id):
    """Delete a custom segment field."""
    custom_field = CustomSegmentField.query.get_or_404(field_id)
    
    # Delete all values for this field
    CustomSegmentValue.query.filter_by(field_id=custom_field.id).delete()
    
    # Delete the field
    db.session.delete(custom_field)
    db.session.commit()
    
    flash('Custom field deleted successfully!', 'success')
    return redirect(url_for('segmentation.custom_segment_fields'))

# Helper function to find leads matching criteria
def find_matching_leads(criteria_data, criteria_logic='and'):
    """Find leads that match the given criteria."""
    if not criteria_data:
        return []
    
    filters = []
    for criterion in criteria_data:
        field = criterion['field']
        operator = criterion['operator']
        value = criterion['value']
        
        # Basic lead fields
        if field in ['first_name', 'last_name', 'email', 'phone', 'source', 'status']:
            column = getattr(Lead, field)
            
            if operator == 'equals':
                filters.append(column == value)
            elif operator == 'not_equals':
                filters.append(column != value)
            elif operator == 'contains':
                filters.append(column.ilike(f'%{value}%'))
            elif operator == 'starts_with':
                filters.append(column.ilike(f'{value}%'))
            elif operator == 'ends_with':
                filters.append(column.ilike(f'%{value}'))
        
        # Interest fields
        elif field.startswith('interest_'):
            interest_field = field.replace('interest_', '')
            subquery = db.session.query(LeadInterest.lead_id).filter(
                getattr(LeadInterest, interest_field).ilike(f'%{value}%')
            ).subquery()
            filters.append(Lead.id.in_(subquery))
        
        # Budget fields
        elif field.startswith('budget_'):
            budget_field = field.replace('budget_', '')
            
            if budget_field in ['min_amount', 'max_amount', 'down_payment', 'monthly_payment']:
                try:
                    value_num = float(value)
                    
                    if operator == 'equals':
                        subquery = db.session.query(LeadBudget.lead_id).filter(
                            getattr(LeadBudget, budget_field) == value_num
                        ).subquery()
                    elif operator == 'greater_than':
                        subquery = db.session.query(LeadBudget.lead_id).filter(
                            getattr(LeadBudget, budget_field) > value_num
                        ).subquery()
                    elif operator == 'less_than':
                        subquery = db.session.query(LeadBudget.lead_id).filter(
                            getattr(LeadBudget, budget_field) < value_num
                        ).subquery()
                    else:
                        subquery = db.session.query(LeadBudget.lead_id).filter(
                            getattr(LeadBudget, budget_field).ilike(f'%{value}%')
                        ).subquery()
                    
                    filters.append(Lead.id.in_(subquery))
                except ValueError:
                    # Handle non-numeric value for numeric field
                    pass
            else:
                subquery = db.session.query(LeadBudget.lead_id).filter(
                    getattr(LeadBudget, budget_field).ilike(f'%{value}%')
                ).subquery()
                filters.append(Lead.id.in_(subquery))
        
        # Timeline fields
        elif field.startswith('timeline_'):
            timeline_field = field.replace('timeline_', '')
            subquery = db.session.query(LeadTimeline.lead_id).filter(
                getattr(LeadTimeline, timeline_field).ilike(f'%{value}%')
            ).subquery()
            filters.append(Lead.id.in_(subquery))
        
        # Custom fields
        elif field.startswith('custom_'):
            custom_field_name = field.replace('custom_', '')
            custom_field = CustomSegmentField.query.filter_by(name=custom_field_name).first()
            
            if custom_field:
                subquery = db.session.query(CustomSegmentValue.lead_id).filter(
                    CustomSegmentValue.field_id == custom_field.id,
                    CustomSegmentValue.value.ilike(f'%{value}%')
                ).subquery()
                filters.append(Lead.id.in_(subquery))
    
    # Apply filters based on logic
    if criteria_logic == 'and':
        query = Lead.query.filter(and_(*filters))
    else:  # 'or'
        query = Lead.query.filter(or_(*filters))
    
    return query.all()

# Helper function to update segment leads
def update_segment_leads(segment):
    """Update the leads in a dynamic segment based on criteria."""
    if not segment.is_dynamic:
        return False
    
    try:
        # Get criteria data
        criteria_data = []
        for criterion in segment.criteria:
            criteria_data.append({
                'field': criterion.field,
                'operator': criterion.operator,
                'value': criterion.value
            })
        
        # Find matching leads
        matching_leads = find_matching_leads(criteria_data, segment.criteria_logic)
        
        # Update segment leads
        segment.leads = matching_leads
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        return False
