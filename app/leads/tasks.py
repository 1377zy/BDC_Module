"""
Lead Management Tasks

This module contains background tasks for lead management:
1. Processing follow-up sequences
2. Lead scoring updates
3. Lead lifecycle management
"""

from app import db, create_app
from app.models import (
    Lead, LeadActivity, LeadFollowUpSequence, FollowUpStep, 
    LeadSequenceAssignment, EmailTemplate, SMSTemplate, User
)
from app.email.email import send_email
from app.sms.sms import send_sms
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def process_follow_up_sequences():
    """
    Process all due follow-up sequence steps
    
    This function:
    1. Finds all active sequence assignments with due steps
    2. Processes each step based on its action type (email, SMS, task)
    3. Updates the assignment with the next step information
    
    Returns the number of steps processed
    """
    app = create_app()
    with app.app_context():
        now = datetime.utcnow()
        processed_count = 0
        
        # Find all active assignments with due steps
        due_assignments = LeadSequenceAssignment.query.filter(
            LeadSequenceAssignment.is_active == True,
            LeadSequenceAssignment.next_step_due_at <= now,
            LeadSequenceAssignment.completed_at == None
        ).all()
        
        logger.info(f"Found {len(due_assignments)} due sequence assignments")
        
        for assignment in due_assignments:
            lead = Lead.query.get(assignment.lead_id)
            sequence = LeadFollowUpSequence.query.get(assignment.sequence_id)
            
            if not lead or not sequence:
                logger.warning(f"Invalid lead or sequence for assignment {assignment.id}")
                continue
            
            # Get the next step
            next_step_number = assignment.current_step + 1
            next_step = FollowUpStep.query.filter_by(
                sequence_id=sequence.id,
                step_number=next_step_number,
                is_active=True
            ).first()
            
            if not next_step:
                # No more steps, mark the sequence as completed
                logger.info(f"Completing sequence {sequence.id} for lead {lead.id}")
                assignment.is_active = False
                assignment.completed_at = now
                
                # Record activity
                activity = LeadActivity(
                    lead=lead,
                    activity_type='sequence_completed',
                    description=f'Completed follow-up sequence: {sequence.name}',
                    created_at=now
                )
                db.session.add(activity)
                continue
            
            # Process the step based on action type
            try:
                process_step(lead, next_step, assignment)
                processed_count += 1
                
                # Update the assignment
                assignment.current_step = next_step_number
                assignment.last_step_completed_at = now
                
                # Calculate next step due date
                next_next_step = FollowUpStep.query.filter_by(
                    sequence_id=sequence.id,
                    step_number=next_step_number + 1,
                    is_active=True
                ).first()
                
                if next_next_step:
                    assignment.next_step_due_at = now + timedelta(
                        days=next_next_step.delay_days,
                        hours=next_next_step.delay_hours
                    )
                else:
                    # This was the last step
                    assignment.is_active = False
                    assignment.completed_at = now
                    
                    # Record activity
                    activity = LeadActivity(
                        lead=lead,
                        activity_type='sequence_completed',
                        description=f'Completed follow-up sequence: {sequence.name}',
                        created_at=now
                    )
                    db.session.add(activity)
            except Exception as e:
                logger.error(f"Error processing step {next_step.id} for lead {lead.id}: {str(e)}")
        
        db.session.commit()
        return processed_count

def process_step(lead, step, assignment):
    """Process a single follow-up step"""
    now = datetime.utcnow()
    
    if step.action_type == 'email':
        # Send email
        template = EmailTemplate.query.get(step.template_id)
        if not template:
            raise ValueError(f"Email template {step.template_id} not found")
        
        if not lead.email:
            raise ValueError(f"Lead {lead.id} has no email address")
        
        # Replace placeholders in template
        subject = template.subject.replace('{lead_name}', lead.get_full_name())
        body = template.body.replace('{lead_name}', lead.get_full_name())
        
        # Send the email
        send_email(subject, lead.email, body)
        
        # Record activity
        activity = LeadActivity(
            lead=lead,
            activity_type='email_sent',
            description=f'Automated email sent: {template.name}',
            created_at=now,
            related_entity_type='email_template',
            related_entity_id=template.id
        )
        db.session.add(activity)
        
        # Update lead's last activity date
        lead.last_activity_date = now
        
    elif step.action_type == 'sms':
        # Send SMS
        template = SMSTemplate.query.get(step.template_id)
        if not template:
            raise ValueError(f"SMS template {step.template_id} not found")
        
        if not lead.phone:
            raise ValueError(f"Lead {lead.id} has no phone number")
        
        # Replace placeholders in template
        body = template.body.replace('{lead_name}', lead.get_full_name())
        
        # Send the SMS
        send_sms(lead.phone, body)
        
        # Record activity
        activity = LeadActivity(
            lead=lead,
            activity_type='sms_sent',
            description=f'Automated SMS sent: {template.name}',
            created_at=now,
            related_entity_type='sms_template',
            related_entity_id=template.id
        )
        db.session.add(activity)
        
        # Update lead's last activity date
        lead.last_activity_date = now
        
    elif step.action_type == 'task':
        # Create a task for a user
        from app.models import Task
        
        # Find assignee based on role
        assignee = None
        if step.task_assignee_role == 'lead_owner':
            assignee = User.query.get(lead.assigned_to_id)
        else:
            # Assign to first user with the specified role
            assignee = User.query.filter_by(role=step.task_assignee_role).first()
        
        if not assignee:
            raise ValueError(f"No assignee found for task with role {step.task_assignee_role}")
        
        # Replace placeholders in task description
        description = step.task_description.replace('{lead_name}', lead.get_full_name())
        
        # Create the task
        task = Task(
            title=f"Follow up with {lead.get_full_name()}",
            description=description,
            due_date=datetime.utcnow() + timedelta(days=1),
            priority='high',
            assigned_to=assignee,
            related_entity_type='lead',
            related_entity_id=lead.id,
            status='open'
        )
        db.session.add(task)
        
        # Record activity
        activity = LeadActivity(
            lead=lead,
            activity_type='task_created',
            description=f'Follow-up task created: {task.title}',
            created_at=now,
            related_entity_type='task',
            related_entity_id=task.id
        )
        db.session.add(activity)
    
    # Update lead score
    lead.calculate_score()
    
    # Update lifecycle stage
    lead.update_lifecycle_stage()

def update_lead_scores():
    """Update scores for all leads"""
    app = create_app()
    with app.app_context():
        leads = Lead.query.all()
        for lead in leads:
            lead.calculate_score()
        db.session.commit()
        return len(leads)

def update_lead_lifecycle_stages():
    """Update lifecycle stages for all leads"""
    app = create_app()
    with app.app_context():
        leads = Lead.query.all()
        for lead in leads:
            lead.update_lifecycle_stage()
        db.session.commit()
        return len(leads)

if __name__ == '__main__':
    # This allows running the tasks directly from the command line
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m app.leads.tasks [process_sequences|update_scores|update_lifecycle]")
        sys.exit(1)
    
    task = sys.argv[1]
    
    if task == 'process_sequences':
        count = process_follow_up_sequences()
        print(f"Processed {count} follow-up steps")
    elif task == 'update_scores':
        count = update_lead_scores()
        print(f"Updated scores for {count} leads")
    elif task == 'update_lifecycle':
        count = update_lead_lifecycle_stages()
        print(f"Updated lifecycle stages for {count} leads")
    else:
        print(f"Unknown task: {task}")
        sys.exit(1)
