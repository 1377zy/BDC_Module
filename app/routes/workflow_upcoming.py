from flask import render_template, request
from datetime import datetime, timedelta
from sqlalchemy import func
from app import app, db
from app.models import Lead, LeadWorkflow, LeadWorkflowStep, WorkflowStep, WorkflowTemplate

@app.route('/workflow/upcoming', methods=['GET'])
def upcoming_workflow_steps():
    """Display upcoming workflow steps that need attention."""
    # Get time range for filtering
    time_range = request.args.get('time_range', 'today')
    
    # Calculate date ranges
    now = datetime.utcnow()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    if time_range == 'today':
        start_date = today
        end_date = tomorrow
        title = "Today's Tasks"
    elif time_range == 'tomorrow':
        start_date = tomorrow
        end_date = tomorrow + timedelta(days=1)
        title = "Tomorrow's Tasks"
    elif time_range == 'week':
        start_date = today
        end_date = next_week
        title = "This Week's Tasks"
    else:  # 'all' or any other value
        start_date = today
        end_date = None
        title = "All Upcoming Tasks"
    
    # Query upcoming steps
    query = db.session.query(
        LeadWorkflowStep, 
        LeadWorkflow, 
        Lead, 
        WorkflowStep,
        WorkflowTemplate
    ).join(
        LeadWorkflow, LeadWorkflowStep.lead_workflow_id == LeadWorkflow.id
    ).join(
        Lead, LeadWorkflow.lead_id == Lead.id
    ).join(
        WorkflowStep, LeadWorkflowStep.workflow_step_id == WorkflowStep.id
    ).join(
        WorkflowTemplate, LeadWorkflow.workflow_template_id == WorkflowTemplate.id
    ).filter(
        LeadWorkflowStep.status == 'pending',
        LeadWorkflow.status == 'active'
    )
    
    if end_date:
        query = query.filter(
            LeadWorkflowStep.scheduled_date >= start_date,
            LeadWorkflowStep.scheduled_date < end_date
        )
    else:
        query = query.filter(LeadWorkflowStep.scheduled_date >= start_date)
    
    # Order by scheduled date (soonest first)
    query = query.order_by(LeadWorkflowStep.scheduled_date)
    
    results = query.all()
    
    # Organize steps by type
    steps_by_type = {
        'Email': [],
        'SMS': [],
        'Call': [],
        'Task': []
    }
    
    for lead_step, lead_workflow, lead, workflow_step, workflow in results:
        step_data = {
            'lead_step_id': lead_step.id,
            'lead_workflow_id': lead_workflow.id,
            'lead': lead,
            'lead_name': f"{lead.first_name} {lead.last_name}",
            'workflow_name': workflow.name,
            'step_type': workflow_step.step_type,
            'step_order': workflow_step.step_order,
            'subject': workflow_step.subject,
            'content': workflow_step.content,
            'scheduled_date': lead_step.scheduled_date,
            'days_until': (lead_step.scheduled_date.date() - today).days
        }
        
        steps_by_type[workflow_step.step_type].append(step_data)
    
    # Count steps by type
    counts = {
        'Email': len(steps_by_type['Email']),
        'SMS': len(steps_by_type['SMS']),
        'Call': len(steps_by_type['Call']),
        'Task': len(steps_by_type['Task']),
        'Total': len(results)
    }
    
    return render_template(
        'workflows/upcoming.html',
        title=title,
        time_range=time_range,
        steps_by_type=steps_by_type,
        counts=counts
    )
