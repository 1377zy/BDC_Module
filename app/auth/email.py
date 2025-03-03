from flask import current_app, render_template
from app.email import send_email
import jwt
from time import time

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        subject='[BDC Module] Reset Your Password',
        recipients=[user.email],
        text_body=render_template('auth/email/reset_password.txt', user=user, token=token),
        html_body=render_template('auth/email/reset_password.html', user=user, token=token)
    )
