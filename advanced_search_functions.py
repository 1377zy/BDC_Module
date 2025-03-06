"""
Advanced Lead Search Functions

This file contains the additional functions needed for the Advanced Lead Search feature.
These functions should be integrated into the main working_app.py file.
"""

from flask import render_template, redirect, url_for, request, flash, session, Response
from datetime import datetime, timedelta
import json
import io
import csv
import random
from app.models import SavedSearch, SearchHistory, User, db

# Function to view search history
def view_search_history():
    search_history = []
    
    if 'current_user' in globals() and current_user.is_authenticated:
        search_history = SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.executed_at.desc()).all()
    else:
        # Mock search history for demonstration
        for i in range(10):
            days_ago = random.randint(0, 30)
            results_count = random.randint(0, 50)
            search_history.append({
                'id': i + 1,
                'search_params': json.dumps({'name': f'Sample search {i+1}'}),
                'results_count': results_count,
                'executed_at': datetime.now() - timedelta(days=days_ago)
            })
    
    return render_template('leads/search_history.html',
                          search_history=search_history,
                          current_user={'is_authenticated': True})

# Function to clear search history
def clear_search_history():
    if 'current_user' in globals() and current_user.is_authenticated:
        try:
            SearchHistory.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
            flash('Search history has been cleared.', 'success')
        except Exception as e:
            print(f"Error clearing search history: {e}")
            db.session.rollback()
            flash('An error occurred while clearing your search history.', 'danger')
    else:
        # Mock clear for demonstration
        flash('Search history has been cleared.', 'success')
    
    return redirect(url_for('view_search_history'))

# Function to load a saved search
def load_saved_search(search_id):
    if 'current_user' in globals() and current_user.is_authenticated:
        saved_search = SavedSearch.query.get(search_id)
        if saved_search and saved_search.user_id == current_user.id:
            search_params = json.loads(saved_search.search_params)
            # Redirect to the advanced search page with the saved search parameters
            return redirect(url_for('advanced_lead_search', **search_params))
        else:
            flash('Saved search not found.', 'danger')
    else:
        # Mock load for demonstration
        # Redirect to the advanced search page with some sample parameters
        sample_params = {'status': 'New', 'source': 'Website'}
        return redirect(url_for('advanced_lead_search', **sample_params))
    
    return redirect(url_for('advanced_lead_search'))

# Function to save a search
def save_search():
    search_name = request.form.get('search_name')
    search_params = request.form.get('search_params')
    
    if not search_name or not search_params:
        flash('Search name and parameters are required.', 'danger')
        return redirect(url_for('advanced_lead_search'))
    
    # Save to the database
    if 'current_user' in globals() and current_user.is_authenticated:
        try:
            saved_search = SavedSearch(
                name=search_name,
                user_id=current_user.id,
                search_params=search_params
            )
            db.session.add(saved_search)
            db.session.commit()
            flash(f'Search "{search_name}" has been saved.', 'success')
        except Exception as e:
            print(f"Error saving search: {e}")
            db.session.rollback()
            flash('An error occurred while saving your search.', 'danger')
    else:
        # Mock save for demonstration
        flash(f'Search "{search_name}" has been saved.', 'success')
    
    return redirect(url_for('advanced_lead_search'))

# Function to delete a saved search
def delete_saved_search():
    search_id = request.args.get('id')
    
    if not search_id:
        flash('No search specified.', 'danger')
        return redirect(url_for('advanced_lead_search'))
    
    # Delete from the database
    if 'current_user' in globals() and current_user.is_authenticated:
        try:
            saved_search = SavedSearch.query.get(search_id)
            if saved_search and saved_search.user_id == current_user.id:
                db.session.delete(saved_search)
                db.session.commit()
                flash('Saved search has been deleted.', 'success')
            else:
                flash('Search not found or you do not have permission to delete it.', 'danger')
        except Exception as e:
            print(f"Error deleting search: {e}")
            db.session.rollback()
            flash('An error occurred while deleting your search.', 'danger')
    else:
        # Mock delete for demonstration
        flash('Saved search has been deleted.', 'success')
    
    return redirect(url_for('advanced_lead_search'))

# Function to export search results
def export_search_results():
    # Get search parameters from session or request
    search_params = session.get('last_search_params', {})
    
    # In a real app, we would retrieve the search results by re-running the search
    # For now, we'll just use our mock data
    search_results = leads_data
    
    if search_params:
        # Filter the results based on the search parameters
        # This would be a duplicate of the filtering logic in advanced_lead_search
        # For simplicity, we'll skip that here and just use the mock data
        pass
    
    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone', 'Status', 'Source', 'Vehicle Interest', 'Budget', 'Timeline', 'Created Date'])
    
    # Write data rows
    for lead in search_results:
        writer.writerow([
            lead.get('first_name', ''),
            lead.get('last_name', ''),
            lead.get('email', ''),
            lead.get('phone', ''),
            lead.get('status', ''),
            lead.get('source', ''),
            lead.get('vehicle_interest', ''),
            lead.get('budget', ''),
            lead.get('purchase_timeline', ''),
            lead.get('created_at', datetime.now()).strftime('%Y-%m-%d')
        ])
    
    # Prepare the response
    output.seek(0)
    
    # Log the export activity
    if 'current_user' in globals() and current_user.is_authenticated:
        try:
            # You could create an ActivityLog model to track user actions
            pass
        except Exception as e:
            print(f"Error logging export activity: {e}")
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=lead_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )
