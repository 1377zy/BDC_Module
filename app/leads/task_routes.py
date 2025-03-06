"""
Lead Task Management Routes

This module provides routes for managing tasks related to leads:
1. Viewing tasks (my tasks, team tasks, completed tasks)
2. Creating new tasks
3. Editing existing tasks
4. Completing tasks
5. Deleting tasks
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.leads import bp
from app.models import Task, Lead, User
from app.utils.decorators import admin_required, manager_required, role_required
from datetime import datetime, timedelta

@bp.route('/leads/tasks')
@login_required
def tasks():
    """View task management dashboard"""
    # Get my tasks (assigned to current user)
    my_tasks = Task.query.filter_by(
        assigned_to_id=current_user.id,
        status='open'
    ).order_by(Task.due_date.asc()).all()
    
    # Get team tasks (for managers and admins)
    team_tasks = []
    if current_user.role in ['manager', 'admin']:
        # Get tasks assigned to team members
        team_tasks = Task.query.filter(
            Task.assigned_to_id != current_user.id,
            Task.status == 'open'
        ).order_by(Task.due_date.asc()).all()
    
    # Get completed tasks
    completed_tasks = Task.query.filter_by(
        status='completed'
    ).order_by(Task.completed_at.desc()).limit(50).all()
    
    # Get users for task assignment
    users = User.query.all()
    
    # Get leads for task creation
    leads = Lead.query.order_by(Lead.first_name).all()
    
    return render_template('leads/tasks.html',
                          my_tasks=my_tasks,
                          team_tasks=team_tasks,
                          completed_tasks=completed_tasks,
                          users=users,
                          leads=leads)

@bp.route('/leads/tasks/create', methods=['POST'])
@login_required
def create_task():
    """Create a new task"""
    title = request.form.get('title')
    description = request.form.get('description')
    priority = request.form.get('priority', 'medium')
    due_date_str = request.form.get('due_date')
    assigned_to_id = request.form.get('assigned_to_id')
    related_entity_type = request.form.get('related_entity_type')
    related_entity_id = request.form.get('related_entity_id')
    
    # Validate required fields
    if not title:
        flash('Task title is required', 'danger')
        return redirect(url_for('leads.tasks'))
    
    # Parse due date
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid due date format', 'danger')
            return redirect(url_for('leads.tasks'))
    
    # Create new task
    task = Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        assigned_to_id=assigned_to_id or current_user.id,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id
    )
    
    db.session.add(task)
    db.session.commit()
    
    flash('Task created successfully', 'success')
    return redirect(url_for('leads.tasks'))

@bp.route('/leads/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task"""
    task = Task.query.get_or_404(task_id)
    
    # Check permissions - only task owner, assignee, or managers/admins can edit
    if (task.assigned_to_id != current_user.id and 
        current_user.role not in ['manager', 'admin']):
        flash('You do not have permission to edit this task', 'danger')
        return redirect(url_for('leads.tasks'))
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.priority = request.form.get('priority', 'medium')
        
        due_date_str = request.form.get('due_date')
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid due date format', 'danger')
                return redirect(url_for('leads.edit_task', task_id=task.id))
        else:
            task.due_date = None
        
        task.assigned_to_id = request.form.get('assigned_to_id') or task.assigned_to_id
        
        db.session.commit()
        flash('Task updated successfully', 'success')
        return redirect(url_for('leads.tasks'))
    
    # GET request - return task data as JSON
    users = User.query.all()
    leads = Lead.query.all()
    
    return render_template('leads/edit_task.html',
                          task=task,
                          users=users,
                          leads=leads)

@bp.route('/leads/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark a task as complete"""
    task = Task.query.get_or_404(task_id)
    
    # Check permissions - only task assignee or managers/admins can complete
    if (task.assigned_to_id != current_user.id and 
        current_user.role not in ['manager', 'admin']):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    task.status = 'completed'
    task.completed_at = datetime.utcnow()
    db.session.commit()
    
    # If this is an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('Task marked as complete', 'success')
    return redirect(url_for('leads.tasks'))

@bp.route('/leads/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    
    # Check permissions - only managers/admins can delete tasks
    if current_user.role not in ['manager', 'admin']:
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    db.session.delete(task)
    db.session.commit()
    
    # If this is an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('Task deleted', 'success')
    return redirect(url_for('leads.tasks'))

@bp.route('/leads/tasks/get/<int:task_id>')
@login_required
def get_task(task_id):
    """Get task details as JSON for AJAX editing"""
    task = Task.query.get_or_404(task_id)
    
    # Check permissions
    if (task.assigned_to_id != current_user.id and 
        current_user.role not in ['manager', 'admin']):
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    # Format due date for form
    due_date = None
    if task.due_date:
        due_date = task.due_date.strftime('%Y-%m-%d')
    
    # Get related entity info
    related_entity = None
    if task.related_entity_type == 'lead' and task.related_entity_id:
        lead = Lead.query.get(task.related_entity_id)
        if lead:
            related_entity = {
                'id': lead.id,
                'name': lead.get_full_name()
            }
    
    return jsonify({
        'success': True,
        'task': {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'due_date': due_date,
            'assigned_to_id': task.assigned_to_id,
            'related_entity_type': task.related_entity_type,
            'related_entity_id': task.related_entity_id,
            'related_entity': related_entity
        }
    })
