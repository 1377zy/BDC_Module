from twilio.rest import Client
from flask import current_app
from threading import Thread
from datetime import datetime

def send_async_sms(app, to_number, body, twilio_sid, twilio_token, from_number):
    with app.app_context():
        try:
            client = Client(twilio_sid, twilio_token)
            message = client.messages.create(
                body=body,
                from_=from_number,
                to=to_number
            )
            return message.sid
        except Exception as e:
            app.logger.error(f"Failed to send SMS: {str(e)}")
            raise

def send_sms(to_number, body):
    """
    Send an SMS to the specified phone number.
    """
    app = current_app._get_current_object()
    
    # Get Twilio credentials from config
    twilio_sid = app.config['TWILIO_ACCOUNT_SID']
    twilio_token = app.config['TWILIO_AUTH_TOKEN']
    from_number = app.config['TWILIO_PHONE_NUMBER']
    
    # Format the phone number if needed
    if to_number.startswith('+') is False:
        # Add US country code if not present
        to_number = '+1' + to_number.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
    
    # Send SMS asynchronously
    Thread(
        target=send_async_sms,
        args=(app, to_number, body, twilio_sid, twilio_token, from_number)
    ).start()

def send_appointment_confirmation_sms(lead, appointment):
    """
    Send an appointment confirmation SMS to a lead.
    """
    app = current_app._get_current_object()
    dealership_name = app.config['DEALERSHIP_NAME']
    dealership_phone = app.config['DEALERSHIP_PHONE']
    
    # Format the date and time
    formatted_date = appointment.date.strftime('%A, %b %d')
    formatted_time = appointment.time.strftime('%I:%M %p')
    
    # Generate the SMS body
    body = f"Hi {lead.first_name}, your appointment at {dealership_name} is confirmed for {formatted_date} at {formatted_time}. Call {dealership_phone} with questions. Reply Y to confirm."
    
    send_sms(lead.phone, body)

def send_appointment_reminder_sms(lead, appointment):
    """
    Send an appointment reminder SMS to a lead.
    """
    app = current_app._get_current_object()
    dealership_name = app.config['DEALERSHIP_NAME']
    dealership_phone = app.config['DEALERSHIP_PHONE']
    
    # Format the date and time
    formatted_date = appointment.date.strftime('%A, %b %d')
    formatted_time = appointment.time.strftime('%I:%M %p')
    
    # Generate the SMS body
    body = f"Hi {lead.first_name}, reminder: your appointment at {dealership_name} is tomorrow, {formatted_date} at {formatted_time}. Call {dealership_phone} with questions. Reply Y to confirm."
    
    send_sms(lead.phone, body)

def send_appointment_update_sms(lead, appointment):
    """
    Send an appointment update SMS to a lead.
    """
    app = current_app._get_current_object()
    dealership_name = app.config['DEALERSHIP_NAME']
    dealership_phone = app.config['DEALERSHIP_PHONE']
    
    # Format the date and time
    formatted_date = appointment.date.strftime('%A, %b %d')
    formatted_time = appointment.time.strftime('%I:%M %p')
    
    # Generate the SMS body
    body = f"Hi {lead.first_name}, your appointment at {dealership_name} for {formatted_date} at {formatted_time} has been updated to {appointment.status}. Call {dealership_phone} with questions."
    
    send_sms(lead.phone, body)
