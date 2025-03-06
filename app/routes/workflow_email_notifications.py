from flask import url_for
from datetime import datetime, timedelta
from app import app, db
from app.models import (
    Lead, LeadWorkflow, LeadWorkflowStep, WorkflowStep, WorkflowTemplate,
    WorkflowNotificationSettings
)

def send_daily_workflow_email():
    """
    Send a daily email with upcoming workflow tasks.
    This would be called by a scheduler in production.
    """
    # Get notification settings
    settings = WorkflowNotificationSettings.query.first()
    if not settings or not settings.email_notifications:
        return "Email notifications disabled"
    
    # Calculate date range based on settings
    now = datetime.utcnow()
    today = now.date()
    
    # Default to today if no advance notice is set
    advance_notice = settings.advance_notice or 0
    end_date = today + timedelta(days=advance_notice)
    
    # Query upcoming steps within the date range
    steps_query = db.session.query(
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
        LeadWorkflowStep.scheduled_date <= end_date
    ).order_by(LeadWorkflowStep.scheduled_date)
    
    steps = steps_query.all()
    
    if not steps:
        return "No upcoming tasks to notify about"
    
    # Organize steps by type
    steps_by_type = {
        'Email': [],
        'SMS': [],
        'Call': [],
        'Task': []
    }
    
    for lead_step, workflow_step, lead_workflow, lead, workflow in steps:
        days_until = (lead_step.scheduled_date.date() - today).days
        
        if days_until == 0:
            due_text = "Today"
        elif days_until == 1:
            due_text = "Tomorrow"
        else:
            due_text = f"In {days_until} days"
        
        step_data = {
            'lead_name': f"{lead.first_name} {lead.last_name}",
            'workflow_name': workflow.name,
            'step_type': workflow_step.step_type,
            'subject': workflow_step.subject,
            'content': workflow_step.content,
            'scheduled_date': lead_step.scheduled_date,
            'due_text': due_text
        }
        
        steps_by_type[workflow_step.step_type].append(step_data)
    
    # Count steps by type
    counts = {
        'Email': len(steps_by_type['Email']),
        'SMS': len(steps_by_type['SMS']),
        'Call': len(steps_by_type['Call']),
        'Task': len(steps_by_type['Task']),
        'Total': len(steps)
    }
    
    # Build email content
    email_subject = f"Daily Workflow Tasks Summary - {counts['Total']} tasks"
    
    email_body = f"""
    <h2>Your Daily Workflow Tasks Summary</h2>
    <p>You have {counts['Total']} tasks scheduled for the next {advance_notice if advance_notice > 0 else 'day'}.</p>
    
    <div style="margin-bottom: 20px;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; text-align: center; background-color: #4e73df; color: white; border-radius: 5px;">
                    <strong>Total Tasks:</strong> {counts['Total']}
                </td>
                <td style="padding: 10px; text-align: center; background-color: #1cc88a; color: white; border-radius: 5px;">
                    <strong>Emails:</strong> {counts['Email']}
                </td>
                <td style="padding: 10px; text-align: center; background-color: #36b9cc; color: white; border-radius: 5px;">
                    <strong>Calls:</strong> {counts['Call']}
                </td>
                <td style="padding: 10px; text-align: center; background-color: #f6c23e; color: white; border-radius: 5px;">
                    <strong>SMS:</strong> {counts['SMS']}
                </td>
                <td style="padding: 10px; text-align: center; background-color: #858796; color: white; border-radius: 5px;">
                    <strong>Tasks:</strong> {counts['Task']}
                </td>
            </tr>
        </table>
    </div>
    """
    
    # Add task sections
    if counts['Call'] > 0:
        email_body += f"""
        <h3>Calls ({counts['Call']})</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #f8f9fc;">
                <th style="padding: 10px; text-align: left; border: 1px solid #e3e6f0;">Lead</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #e3e6f0;">Workflow</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #e3e6f0;">Notes</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #e3e6f0;">Due</th>
            </tr>
        """
        
        for step in steps_by_type['Call']:
            email_body += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #e3e6f0;">{step['lead_name']}</td>
                <td style="padding: 10px; border: 1px solid #e3e6f0;">{step['workflow_name']}</td>
                <td style="padding: 10px; border: 1px solid #e3e6f0;">{step['content']}</td>
                <td style="padding: 10px; border: 1px solid #e3e6f0;">{step['due_text']}</td>
            </tr>
            """
        
        email_body += "</table>"
    
    if counts['Email'] > 0:
        email_body += f"""
        <h3>Emails ({counts['Email']})</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #f8f9fc;">
                <th style="padding: 10px; text-align: left; border: 1px solid #e3e6f0;">Lead</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #e3e6f0;">Workflow</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #e3e6f0;">Subject</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #e3e6f0;">Due</th>
            </tr>
        """
        
        for step in steps_by_type['Email']:
            email_body += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #e3e6f0;">{step['lead_name']}</td>
                <td style="padding: 10px; border: 1px solid #e3e6f0;">{step['workflow_name']}</td>
                <td style="padding: 10px; border: 1px solid #e3e6f0;">{step['subject']}</td>
                <td style="padding: 10px; border: 1px solid #e3e6f0;">{step['due_text']}</td>
            </tr>
            """
        
        email_body += "</table>"
    
    # Add view all tasks button
    app_url = "http://localhost:5001"  # This would be your actual app URL in production
    tasks_url = f"{app_url}{url_for('upcoming_workflow_steps')}"
    
    email_body += f"""
    <div style="text-align: center; margin-top: 30px;">
        <a href="{tasks_url}" style="background-color: #4e73df; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
            View All Tasks
        </a>
    </div>
    
    <p style="margin-top: 30px; color: #858796; font-size: 12px;">
        This is an automated email from your BDC Module. To change your notification settings, 
        <a href="{app_url}{url_for('workflow_notifications')}">click here</a>.
    </p>
    """
    
    # In a real app, this would send an actual email
    # For now, just print it
    print(f"Would send email with subject: {email_subject}")
    print(f"Email body: {email_body}")
    
    return f"Would send email notification for {counts['Total']} tasks"

# This function could be called by a scheduler in production
def schedule_daily_workflow_emails():
    """
    Schedule daily workflow emails based on notification settings.
    In a real app, this would be called by a scheduler like Celery.
    """
    settings = WorkflowNotificationSettings.query.first()
    if not settings or not settings.email_notifications:
        return "Email notifications disabled"
    
    # Get the notification time from settings
    notification_time = settings.notification_time or "08:00"
    
    # In a real app, you would schedule this to run at the specified time
    # For now, just print when it would run
    print(f"Would schedule daily workflow emails to run at {notification_time}")
    
    return f"Scheduled daily workflow emails to run at {notification_time}"
