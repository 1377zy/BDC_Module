from flask import current_app
from flask_mail import Message
from app import mail
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Error sending email: {str(e)}")

def send_email(subject, recipients, text_body, html_body, sender=None, attachments=None):
    app = current_app._get_current_object()
    msg = Message(subject, recipients=recipients, sender=sender or app.config['MAIL_DEFAULT_SENDER'])
    msg.body = text_body
    msg.html = html_body
    
    if attachments:
        for attachment in attachments:
            if isinstance(attachment, tuple) and len(attachment) == 2:
                filename, data = attachment
                msg.attach(filename=filename, content_type='application/octet-stream', data=data)
            elif isinstance(attachment, dict) and 'filename' in attachment and 'data' in attachment:
                msg.attach(
                    filename=attachment['filename'], 
                    content_type=attachment.get('content_type', 'application/octet-stream'), 
                    data=attachment['data']
                )
    
    Thread(target=send_async_email, args=(app, msg)).start()
    return True
