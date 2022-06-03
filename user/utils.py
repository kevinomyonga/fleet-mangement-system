from django.template.loader import get_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.conf import settings


def anonymous_required(func):
	def as_view(request, *args, **kwargs):
		redirect_to = kwargs.get('next', request.path )
		if request.user.is_authenticated:
			return redirect('/')
		response = func(request, *args, **kwargs)
		return response
	return as_view

def send_email(template_path_html, template_path_txt, subject, email, data):
	email_txt = get_template(template_path_txt).render(data)
	email_html = get_template(template_path_html).render(data)

	message = Mail(	
		subject=subject,
		to_emails=email,
		html_content=email_html,
		plain_text_content=email_txt,
		from_email=settings.DEFAULT_FROM_EMAIL
	)
	try:
		sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
		response = sg.send(message)
	except Exception as e:
		response = None
	
	return response

