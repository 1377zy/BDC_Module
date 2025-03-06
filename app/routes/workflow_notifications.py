from flask import render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from app import app, db
from app.models import (
    Lead, LeadWorkflow, LeadWorkflowStep, WorkflowStep, WorkflowTemplate,
    WorkflowNotification, WorkflowNotificationSettings, User
)

@app.route('/workflow/notifications', methods=['GET'])
def workflow_notifications():
    """Display workflow notifications and settings."""
    # Get or create notification settings
    settings = WorkflowNotificationSettings.query.first()
    if not settings:
        settings = WorkflowNotificationSettings()
        db.session.add(settings)
        db.session.commit()
    
    # Get recent notifications
    notifications = WorkflowNotification.query.order_by(
        WorkflowNotification.created_at.desc()
    ).limit(10).all()
    
    # Get today's tasks for preview
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    today_tasks_query = db.session.query(
        LeadWorkflowStep, 
        WorkflowStep,
        LeadWorkflow,
        Lead,
        WorkflowTemplate
    ).join(
        WorkflowStep, LeadWorkflowStep.workflow_step_id == WorkflowStep.id
    ).join(
        LeadWorkflow, LeadWorkflowStep.lead_workflow_id == LeadWorkflow.id
    ).join(
        Lead, LeadWorkflow.lead_id == Lead.id
    ).join(
        WorkflowTemplate, LeadWorkflow.workflow_template_id == WorkflowTemplate.id
    ).filter(
        LeadWorkflowStep.status == 'pending',
        LeadWorkflow.status == 'active',
        LeadWorkflowStep.scheduled_date >= today,
        LeadWorkflowStep.scheduled_date < tomorrow
    ).order_by(LeadWorkflowStep.scheduled_date).limit(5)
    
    today_tasks_results = today_tasks_query.all()
    today_tasks = []
    
    for lead_step, workflow_step, lead_workflow, lead, workflow in today_tasks_results:
        task_data = {
            'lead_step_id': lead_step.id,
            'lead_workflow_id': lead_workflow.id,
            'lead_name': f"{lead.first_name} {lead.last_name}",
            'workflow_name': workflow.name,
            'step_type': workflow_step.step_type,
            'scheduled_date': lead_step.scheduled_date
        }
        today_tasks.append(task_data)
    
    return render_template(
        'workflows/notifications.html',
        notification_settings=settings,
        notifications=notifications,
        today_tasks=today_tasks
    )

@app.route('/workflow/notifications/update', methods=['POST'])
def update_workflow_notifications():
    """Update workflow notification settings."""
    settings = WorkflowNotificationSettings.query.first()
    if not settings:
        settings = WorkflowNotificationSettings()
        db.session.add(settings)
    
    # Update settings from form
    settings.email_notifications = 'email_notifications' in request.form
    settings.browser_notifications = 'browser_notifications' in request.form
    settings.notification_time = request.form.get('notification_time', '08:00')
    settings.advance_notice = int(request.form.get('advance_notice', 0))
    
    db.session.commit()
    flash('Notification settings updated successfully!', 'success')
    
    return redirect(url_for('workflow_notifications'))

@app.route('/workflow/notifications/mark_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    notification = WorkflowNotification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    
    return redirect(url_for('workflow_notifications'))

@app.route('/workflow/notifications/mark_all_read', methods=['POST'])
def mark_all_notifications_read():
    """Mark all notifications as read."""
    WorkflowNotification.query.update({WorkflowNotification.is_read: True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    
    return redirect(url_for('workflow_notifications'))

def create_notification(title, message, notification_type, link=None, lead_id=None, 
                       workflow_template_id=None, lead_workflow_id=None, lead_workflow_step_id=None):
    """Helper function to create a new notification."""
    notification = WorkflowNotification(
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        lead_id=lead_id,
        workflow_template_id=workflow_template_id,
        lead_workflow_id=lead_workflow_id,
        lead_workflow_step_id=lead_workflow_step_id
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return notification
