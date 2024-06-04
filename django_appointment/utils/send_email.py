import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def send_forgot_password_mail(to, context):
    template = 'email/password_reset.html'
    html_content = render_to_string(template, context)

    msg = EmailMultiAlternatives(context['subject'], "", settings.DEFAULT_FROM_EMAIL, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def send_appointment_confirm_mail(to, context):
    template = 'appointment_confirmation.html'
    html_content = render_to_string(template, context)
    msg = EmailMultiAlternatives(context['subject'], "", settings.DEFAULT_FROM_EMAIL, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()