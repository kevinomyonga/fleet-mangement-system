from django.db import models
import logging
from django.conf import settings

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.template.loader import get_template

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

class Appointment(models.Model):
    name = models.CharField(max_length=150)
    job_title = models.CharField(max_length=150)
    email = models.EmailField()
    company = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=10)
    number_of_orders=models.CharField(max_length=100, blank=True, null=True)
    interest = models.CharField(max_length=150, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    appointment_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Appointment Id: {self.id} Date: {self.appointment_date}'

@receiver(post_save, sender=Appointment)
def send_mail_to_user(sender, instance, created, **kwargs):

    if created:
        # ==================================send email to the client===========================
        subject = 'APPOINTMENT BOOKED'
        
        appointment = instance

        data = {
            'appointment': appointment
        }

        client_email_html = get_template('appointments/client_appointment_email.html').render(data)
        client_email_txt = get_template('appointments/client_appointment_email.txt').render(data)

        to = appointment.email

        message = Mail(	
            subject=subject,
            to_emails=to,
            html_content=client_email_html,
            plain_text_content=client_email_txt,
            from_email=settings.DEFAULT_FROM_EMAIL
        )

        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            logger.debug(response)
        except Exception as e:
            logger.debug(e)


        # ==================================send email to the CEO and sales people===========================
        
        admin_subject = 'NEW APPOINTMENT'

        admin_email_html = get_template("appointments/admin_appointment_email.html").render(data)
        admin_email_txt = get_template("appointments/admin_appointment_email.txt").render(data)

        message = Mail(	
            subject=admin_subject,
            to_emails=['leon@getboda.co.ke', 'amiller@getboda.co.ke', 'kevin@getboda.co.ke', 'developers@getboda.co.ke'],
            # to_emails=['developers@getboda.co.ke'],
            html_content=admin_email_html,
            plain_text_content=admin_email_txt,
            from_email=settings.DEFAULT_FROM_EMAIL
        )

        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
        except Exception as e:
            logger.debug(e)
        
