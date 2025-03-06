import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from threading import Thread
from datetime import datetime

def send_async_email(app, msg, recipient, sender, smtp_server, port, username, password, use_tls):
    with app.app_context():
        try:
            with smtplib.SMTP(smtp_server, port) as server:
                if use_tls:
                    server.starttls()
                if username and password:
                    server.login(username, password)
                server.sendmail(sender, recipient, msg.as_string())
        except Exception as e:
            app.logger.error(f"Failed to send email: {str(e)}")
            raise

def send_email(subject, recipient, body, html_body=None, sender=None):
    """
    Send an email to the specified recipient.
    """
    app = current_app._get_current_object()
    
    sender = sender or app.config['MAIL_DEFAULT_SENDER']
    smtp_server = app.config['MAIL_SERVER']
    port = app.config['MAIL_PORT']
    username = app.config['MAIL_USERNAME']
    password = app.config['MAIL_PASSWORD']
    use_tls = app.config['MAIL_USE_TLS']
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    
    # Attach plain text version
    text_part = MIMEText(body, 'plain')
    msg.attach(text_part)
    
    # Attach HTML version if provided
    if html_body:
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
    
    # Send email asynchronously
    Thread(
        target=send_async_email,
        args=(app, msg, recipient, sender, smtp_server, port, username, password, use_tls)
    ).start()

def send_appointment_confirmation_email(lead, appointment):
    """
    Send an appointment confirmation email to a lead.
    """
    app = current_app._get_current_object()
    dealership_name = app.config['DEALERSHIP_NAME']
    dealership_address = app.config['DEALERSHIP_ADDRESS']
    dealership_phone = app.config['DEALERSHIP_PHONE']
    
    subject = f"Your Appointment with {dealership_name}"
    
    # Format the date and time
    formatted_date = appointment.date.strftime('%A, %B %d, %Y')
    formatted_time = appointment.time.strftime('%I:%M %p')
    
    # Generate the email body
    body = f"""Dear {lead.first_name},

Thank you for scheduling an appointment with {dealership_name}. 

Your appointment details:
Date: {formatted_date}
Time: {formatted_time}
Purpose: {appointment.purpose}

Location: {dealership_address}

Please contact us at {dealership_phone} if you need to reschedule or have any questions.

We look forward to seeing you!

Best regards,
The {dealership_name} Team
"""
    
    # Generate HTML version
    html_body = render_template('email/appointment_confirmation.html',
                              lead=lead,
                              appointment=appointment,
                              formatted_date=formatted_date,
                              formatted_time=formatted_time)
    
    send_email(subject, lead.email, body, html_body)

def send_appointment_reminder_email(lead, appointment):
    """
    Send an appointment reminder email to a lead.
    """
    app = current_app._get_current_object()
    dealership_name = app.config['DEALERSHIP_NAME']
    dealership_address = app.config['DEALERSHIP_ADDRESS']
    dealership_phone = app.config['DEALERSHIP_PHONE']
    
    subject = f"Reminder: Your Appointment with {dealership_name} Tomorrow"
    
    # Format the date and time
    formatted_date = appointment.date.strftime('%A, %B %d, %Y')
    formatted_time = appointment.time.strftime('%I:%M %p')
    
    body = f"""Dear {lead.first_name},

This is a friendly reminder about your appointment with {dealership_name} tomorrow.

Your appointment details:
Date: {formatted_date}
Time: {formatted_time}
Purpose: {appointment.purpose}

Location: {dealership_address}

Please contact us at {dealership_phone} if you need to reschedule or have any questions.

We look forward to seeing you!

Best regards,
The {dealership_name} Team
"""

    # Generate HTML version
    html_body = render_template('email/appointment_reminder.html',
                              lead=lead,
                              appointment=appointment,
                              formatted_date=formatted_date,
                              formatted_time=formatted_time)
    
    send_email(subject, lead.email, body, html_body)

def send_appointment_update_email(lead, appointment):
    """
    Send an appointment update email to a lead.
    """
    app = current_app._get_current_object()
    dealership_name = app.config['DEALERSHIP_NAME']
    dealership_phone = app.config['DEALERSHIP_PHONE']
    
    subject = f"Update to Your Appointment with {dealership_name}"
    
    # Format the date and time
    formatted_date = appointment.date.strftime('%A, %B %d, %Y')
    formatted_time = appointment.time.strftime('%I:%M %p')
    
    body = f"""Dear {lead.first_name},

We're writing to inform you about an update to your appointment with {dealership_name}.

Your appointment status has been updated to: {appointment.status}

Current appointment details:
Date: {formatted_date}
Time: {formatted_time}
Purpose: {appointment.purpose}

Please contact us at {dealership_phone} if you have any questions.

Best regards,
The {dealership_name} Team
"""

    # Generate HTML version
    html_body = render_template('email/appointment_update.html',
                              lead=lead,
                              appointment=appointment,
                              formatted_date=formatted_date,
                              formatted_time=formatted_time)
    
    send_email(subject, lead.email, body, html_body)
