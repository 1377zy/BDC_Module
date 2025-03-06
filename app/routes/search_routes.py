from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Lead, VehicleInterest, SavedSearch, SearchHistory, LeadBudget, LeadTimeline, Segment
from app.forms.search_forms import AdvancedSearchForm, SavedSearchForm
import json
from datetime import datetime
import csv
import io
from sqlalchemy import or_, and_, func

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/advanced', methods=['GET', 'POST'])
@login_required
def advanced_search():
    """Advanced search page with multiple criteria"""
    form = AdvancedSearchForm()
    
    # Populate segments dropdown
    segments = Segment.query.all()
    form.segments.choices = [(s.id, s.name) for s in segments]
    
    # Get saved searches for the user
    saved_searches = SavedSearch.query.filter_by(user_id=current_user.id).all()
    
    # Check if we need to load a saved search
    saved_search_id = request.args.get('saved_search_id')
    if saved_search_id:
        saved_search = SavedSearch.query.get(saved_search_id)
        if saved_search and saved_search.user_id == current_user.id:
            # Load the saved search parameters
            search_params = json.loads(saved_search.search_params)
            for key, value in search_params.items():
                if key in form._fields and value is not None:
                    if key == 'segments' and isinstance(value, list):
                        form._fields[key].data = [int(v) for v in value]
                    else:
                        form._fields[key].data = value
    
    # Process form submission
    if form.validate_on_submit():
        # Build the query
        query = Lead.query
        
        # Basic information filters
        if form.first_name.data:
            query = query.filter(Lead.first_name.ilike(f'%{form.first_name.data}%'))
        if form.last_name.data:
            query = query.filter(Lead.last_name.ilike(f'%{form.last_name.data}%'))
        if form.email.data:
            query = query.filter(Lead.email.ilike(f'%{form.email.data}%'))
        if form.phone.data:
            query = query.filter(Lead.phone.ilike(f'%{form.phone.data}%'))
        
        # Status and source filters
        if form.status.data:
            query = query.filter(Lead.status == form.status.data)
        if form.source.data:
            query = query.filter(Lead.source == form.source.data)
        
        # Date range filters
        if form.created_from.data:
            query = query.filter(Lead.created_at >= form.created_from.data)
        if form.created_to.data:
            query = query.filter(Lead.created_at <= form.created_to.data)
        if form.updated_from.data:
            query = query.filter(Lead.updated_at >= form.updated_from.data)
        if form.updated_to.data:
            query = query.filter(Lead.updated_at <= form.updated_to.data)
        
        # Vehicle interest filters
        if any([form.vehicle_make.data, form.vehicle_model.data, 
                form.vehicle_year_min.data, form.vehicle_year_max.data, 
                form.new_or_used.data]):
            vehicle_subquery = VehicleInterest.query.with_entities(VehicleInterest.lead_id)
            
            if form.vehicle_make.data:
                vehicle_subquery = vehicle_subquery.filter(
                    VehicleInterest.make.ilike(f'%{form.vehicle_make.data}%')
                )
            if form.vehicle_model.data:
                vehicle_subquery = vehicle_subquery.filter(
                    VehicleInterest.model.ilike(f'%{form.vehicle_model.data}%')
                )
            if form.vehicle_year_min.data:
                vehicle_subquery = vehicle_subquery.filter(
                    VehicleInterest.year >= form.vehicle_year_min.data
                )
            if form.vehicle_year_max.data:
                vehicle_subquery = vehicle_subquery.filter(
                    VehicleInterest.year <= form.vehicle_year_max.data
                )
            if form.new_or_used.data:
                vehicle_subquery = vehicle_subquery.filter(
                    VehicleInterest.new_or_used == form.new_or_used.data
                )
                
            query = query.filter(Lead.id.in_(vehicle_subquery.subquery()))
        
        # Budget filters
        if form.budget_min.data or form.budget_max.data or form.preferred_payment.data:
            budget_subquery = LeadBudget.query.with_entities(LeadBudget.lead_id)
            
            if form.budget_min.data:
                budget_subquery = budget_subquery.filter(
                    LeadBudget.max_amount >= form.budget_min.data
                )
            if form.budget_max.data:
                budget_subquery = budget_subquery.filter(
                    LeadBudget.min_amount <= form.budget_max.data
                )
            if form.preferred_payment.data:
                budget_subquery = budget_subquery.filter(
                    LeadBudget.preferred_payment_type == form.preferred_payment.data
                )
                
            query = query.filter(Lead.id.in_(budget_subquery.subquery()))
        
        # Timeline filters
        if form.timeline.data:
            timeline_mapping = {
                'immediate': 'immediate',
                'short': 'short_term',
                'medium': 'medium_term',
                'long': 'long_term'
            }
            timeline_value = timeline_mapping.get(form.timeline.data)
            if timeline_value:
                timeline_subquery = LeadTimeline.query.with_entities(LeadTimeline.lead_id).filter(
                    LeadTimeline.timeline_type == timeline_value
                )
                query = query.filter(Lead.id.in_(timeline_subquery.subquery()))
        
        # Workflow and engagement filters
        if form.in_workflow.data:
            query = query.filter(Lead.workflows.any())
        if form.has_appointment.data:
            query = query.filter(Lead.appointments.any())
        if form.has_communication.data:
            query = query.filter(Lead.communications.any())
        
        # Segment filters
        if form.segments.data:
            for segment_id in form.segments.data:
                query = query.filter(Lead.segments.any(id=segment_id))
        
        # Apply sorting
        sort_column = getattr(Lead, form.sort_by.data)
        if form.sort_order.data == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Execute the query
        results = query.all()
        
        # Save search history
        search_history = SearchHistory(
            user_id=current_user.id,
            search_params=json.dumps({
                field: getattr(form, field).data 
                for field in form._fields 
                if field not in ['submit', 'save', 'export', 'csrf_token']
            }),
            results_count=len(results)
        )
        db.session.add(search_history)
        db.session.commit()
        
        # Handle export if requested
        if form.export.data:
            return export_search_results(results)
        
        # Handle save if requested
        if form.save.data:
            # Store search parameters in session for the save form
            session['search_params'] = {
                field: getattr(form, field).data 
                for field in form._fields 
                if field not in ['submit', 'save', 'export', 'csrf_token']
            }
            return redirect(url_for('search.save_search'))
        
        return render_template(
            'search/results.html', 
            results=results, 
            count=len(results), 
            form=form,
            saved_searches=saved_searches
        )
    
    # Initial page load or form validation failed
    return render_template(
        'search/advanced.html', 
        form=form, 
        saved_searches=saved_searches
    )

@search_bp.route('/save', methods=['GET', 'POST'])
@login_required
def save_search():
    """Save a search for future use"""
    form = SavedSearchForm()
    
    if form.validate_on_submit():
        # Get search parameters from session
        search_params = session.get('search_params', {})
        
        # Create new saved search
        saved_search = SavedSearch(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id,
            search_params=json.dumps(search_params)
        )
        
        # If this is set as default, clear other defaults
        if form.is_default.data:
            default_searches = SavedSearch.query.filter_by(
                user_id=current_user.id, 
                is_default=True
            ).all()
            for search in default_searches:
                search.is_default = False
            saved_search.is_default = True
        
        db.session.add(saved_search)
        db.session.commit()
        
        flash('Search saved successfully!', 'success')
        return redirect(url_for('search.advanced_search'))
    
    return render_template('search/save_search.html', form=form)

@search_bp.route('/saved', methods=['GET'])
@login_required
def saved_searches():
    """View and manage saved searches"""
    searches = SavedSearch.query.filter_by(user_id=current_user.id).order_by(SavedSearch.name).all()
    return render_template('search/saved_searches.html', searches=searches)

@search_bp.route('/saved/<int:search_id>/delete', methods=['POST'])
@login_required
def delete_saved_search(search_id):
    """Delete a saved search"""
    search = SavedSearch.query.get_or_404(search_id)
    
    # Check ownership
    if search.user_id != current_user.id:
        flash('You do not have permission to delete this search.', 'danger')
        return redirect(url_for('search.saved_searches'))
    
    db.session.delete(search)
    db.session.commit()
    
    flash('Saved search deleted successfully.', 'success')
    return redirect(url_for('search.saved_searches'))

@search_bp.route('/history', methods=['GET'])
@login_required
def search_history():
    """View search history"""
    history = SearchHistory.query.filter_by(user_id=current_user.id).order_by(
        SearchHistory.executed_at.desc()
    ).limit(50).all()
    
    return render_template('search/history.html', history=history)

@search_bp.route('/export', methods=['POST'])
@login_required
def export_search_results(results=None):
    """Export search results to CSV"""
    if results is None:
        # If no results provided, get from form data
        form_data = request.form
        # ... rebuild query from form data ...
        # This would be a duplicate of the search logic in advanced_search
        # For simplicity, we'll just redirect to advanced search
        flash('Please perform a search before exporting.', 'warning')
        return redirect(url_for('search.advanced_search'))
    
    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow([
        'ID', 'First Name', 'Last Name', 'Email', 'Phone', 
        'Source', 'Status', 'Created At', 'Updated At'
    ])
    
    # Write data rows
    for lead in results:
        writer.writerow([
            lead.id, lead.first_name, lead.last_name, lead.email, lead.phone,
            lead.source, lead.status, lead.created_at, lead.updated_at
        ])
    
    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return current_app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=lead_export_{timestamp}.csv'
        }
    )
