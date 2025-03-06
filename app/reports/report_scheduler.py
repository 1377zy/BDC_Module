import os
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from flask import current_app, render_template, url_for
from app import db
from app.models import ScheduledReport, User, Task, Lead
from app.reports.pdf_generator import generate_pdf_report

class ReportScheduler:
    """
    Utility class for handling scheduled report generation and sending
    """
    
    @staticmethod
    def check_and_send_reports():
        """
        Check for reports that need to be sent and process them
        """
        now = datetime.datetime.now()
        today = now.date()
        
        # Get all active scheduled reports
        scheduled_reports = ScheduledReport.query.filter_by(is_active=True).all()
        
        for report in scheduled_reports:
            if ReportScheduler._should_send_report(report, today):
                try:
                    ReportScheduler.generate_and_send_report(report)
                    
                    # Update last sent date
                    report.last_sent_at = now
                    db.session.commit()
                    
                    current_app.logger.info(f"Successfully sent scheduled report {report.id} - {report.name}")
                except Exception as e:
                    current_app.logger.error(f"Failed to send scheduled report {report.id} - {report.name}: {str(e)}")
    
    @staticmethod
    def send_report(report):
        """
        Send a specific report immediately, regardless of schedule
        
        Args:
            report: The ScheduledReport object
        """
        return ReportScheduler.generate_and_send_report(report, force_send=True)
    
    @staticmethod
    def generate_and_send_report(report, force_send=False):
        """
        Generate and send a specific report
        
        Args:
            report: The ScheduledReport object
            force_send: If True, send regardless of schedule
        """
        # Generate PDF based on report type
        pdf_path = ReportScheduler._generate_report_pdf(report)
        
        if pdf_path:
            # Send email with PDF attachment
            ReportScheduler._send_email(report, pdf_path)
            
            # Clean up the temporary PDF file
            try:
                os.remove(pdf_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to remove temporary PDF file {pdf_path}: {str(e)}")
        else:
            raise Exception("Failed to generate PDF report")
    
    @staticmethod
    def _should_send_report(report, today):
        """
        Determine if a report should be sent today based on its schedule
        
        Args:
            report: The ScheduledReport object
            today: Current date
        
        Returns:
            bool: True if the report should be sent today
        """
        # If report was never sent or if force_send is True
        if report.last_sent_at is None:
            return True
        
        last_sent_date = report.last_sent_at.date()
        
        # Check based on frequency
        if report.frequency == 'daily':
            return last_sent_date < today
        
        elif report.frequency == 'weekly':
            # If it's been at least 7 days since last sent
            return (today - last_sent_date).days >= 7 and today.weekday() == report.day_of_week
        
        elif report.frequency == 'monthly':
            # If it's the same day of month and at least a month has passed
            return (today.day == report.day_of_month and 
                   (today.year > last_sent_date.year or 
                    (today.year == last_sent_date.year and today.month > last_sent_date.month)))
        
        return False
    
    @staticmethod
    def _generate_report_pdf(report):
        """
        Generate a PDF report based on the report type
        
        Args:
            report: The ScheduledReport object
        
        Returns:
            str: Path to the generated PDF file
        """
        # Calculate date range based on report settings
        end_date = datetime.datetime.now().date()
        
        if report.date_range == 'last_7_days':
            start_date = end_date - datetime.timedelta(days=7)
        elif report.date_range == 'last_30_days':
            start_date = end_date - datetime.timedelta(days=30)
        elif report.date_range == 'last_90_days':
            start_date = end_date - datetime.timedelta(days=90)
        elif report.date_range == 'custom':
            start_date = report.custom_start_date
            end_date = report.custom_end_date
        else:
            # Default to last 30 days
            start_date = end_date - datetime.timedelta(days=30)
        
        # Generate report data based on type
        if report.report_type == 'inventory':
            data = ReportScheduler._generate_inventory_report_data(start_date, end_date)
        elif report.report_type == 'leads':
            data = ReportScheduler._generate_leads_report_data(start_date, end_date)
        elif report.report_type == 'sales':
            data = ReportScheduler._generate_sales_report_data(start_date, end_date)
        elif report.report_type == 'performance':
            data = ReportScheduler._generate_performance_report_data(start_date, end_date)
        elif report.report_type == 'tasks':
            data = ReportScheduler._generate_task_report_data(start_date, end_date)
        else:
            raise ValueError(f"Unknown report type: {report.report_type}")
        
        # Add metadata
        data['title'] = report.name
        data['date_range'] = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        data['generated_by'] = 'System'
        data['generated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Generate PDF
        pdf_content = generate_pdf_report(
            report.report_type, 
            data, 
            report.include_charts,
            report.template_id
        )
        
        # Write to temporary file
        temp_dir = current_app.config.get('TEMP_DIR', '/tmp')
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f"{report.report_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(temp_dir, filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        return pdf_path
    
    @staticmethod
    def _generate_inventory_report_data(start_date, end_date):
        """Generate data for inventory report"""
        from app.reports.routes import generate_inventory_report_data
        return generate_inventory_report_data(start_date, end_date)
    
    @staticmethod
    def _generate_leads_report_data(start_date, end_date):
        """Generate data for leads report"""
        from app.reports.routes import generate_leads_report_data
        return generate_leads_report_data(start_date, end_date)
    
    @staticmethod
    def _generate_sales_report_data(start_date, end_date):
        """Generate data for sales report"""
        from app.reports.routes import generate_sales_report_data
        return generate_sales_report_data(start_date, end_date)
    
    @staticmethod
    def _generate_performance_report_data(start_date, end_date):
        """Generate data for performance report"""
        from app.reports.routes import generate_performance_report_data
        return generate_performance_report_data(start_date, end_date)
    
    @staticmethod
    def _generate_task_report_data(start_date, end_date):
        """
        Generate data for task report
        
        Args:
            start_date (date): Start date for the report
            end_date (date): End date for the report
            
        Returns:
            dict: Data for the report
        """
        from app.models import Task, User, Lead
        from app import db
        from sqlalchemy import func
        
        # Base query for tasks
        query = Task.query.filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )
        
        # Get tasks
        tasks = query.all()
        
        # Count tasks by status
        open_tasks_count = sum(1 for task in tasks if task.status == 'open')
        completed_tasks_count = sum(1 for task in tasks if task.status == 'completed')
        
        # Count tasks by priority
        high_priority_tasks_count = sum(1 for task in tasks if task.priority == 'high')
        medium_priority_tasks_count = sum(1 for task in tasks if task.priority == 'medium')
        low_priority_tasks_count = sum(1 for task in tasks if task.priority == 'low')
        
        # Count overdue tasks
        now = datetime.datetime.now().date()
        overdue_tasks_count = sum(1 for task in tasks if task.due_date and task.due_date < now and task.status != 'completed')
        
        # Get tasks by user
        users = User.query.all()
        user_labels = [user.get_full_name() for user in users]
        user_open_tasks = []
        user_completed_tasks = []
        
        for user in users:
            user_open_tasks.append(sum(1 for task in tasks if task.assigned_to_id == user.id and task.status == 'open'))
            user_completed_tasks.append(sum(1 for task in tasks if task.assigned_to_id == user.id and task.status == 'completed'))
        
        # Helper function to get lead for a task
        def get_lead(lead_id):
            return Lead.query.get(lead_id)
        
        return {
            'tasks': tasks,
            'open_tasks_count': open_tasks_count,
            'completed_tasks_count': completed_tasks_count,
            'high_priority_tasks_count': high_priority_tasks_count,
            'medium_priority_tasks_count': medium_priority_tasks_count,
            'low_priority_tasks_count': low_priority_tasks_count,
            'overdue_tasks_count': overdue_tasks_count,
            'user_labels': user_labels,
            'user_open_tasks': user_open_tasks,
            'user_completed_tasks': user_completed_tasks,
            'get_lead': get_lead,
            'now': datetime.datetime.now()
        }
    
    @staticmethod
    def _send_email(report, pdf_path):
        """
        Send an email with the PDF report attached
        
        Args:
            report: The ScheduledReport object
            pdf_path: Path to the PDF file to attach
        """
        # Get SMTP settings from config
        smtp_server = current_app.config['MAIL_SERVER']
        smtp_port = current_app.config['MAIL_PORT']
        smtp_username = current_app.config['MAIL_USERNAME']
        smtp_password = current_app.config['MAIL_PASSWORD']
        sender_email = current_app.config['MAIL_DEFAULT_SENDER']
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        
        # Get recipient list
        recipients = []
        
        # Add specific recipients if any
        if report.recipients:
            recipients.extend(report.recipients.split(','))
        
        # Add users by role if specified
        if report.recipient_roles:
            role_list = report.recipient_roles.split(',')
            users = User.query.filter(User.role.in_(role_list)).all()
            for user in users:
                if user.email and user.email not in recipients:
                    recipients.append(user.email)
        
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"{report.name} - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        
        # Email body
        body = render_template('emails/scheduled_report.html', 
                              report_name=report.name,
                              report_type=report.report_type.capitalize(),
                              generated_at=datetime.datetime.now())
        msg.attach(MIMEText(body, 'html'))
        
        # Attach PDF
        with open(pdf_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='pdf')
            attachment.add_header('Content-Disposition', 'attachment', 
                                 filename=os.path.basename(pdf_path))
            msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
