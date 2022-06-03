from django.views.generic.base import RedirectView, TemplateView
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.views.generic.edit import FormView
from django.contrib.auth import login, logout
from .models import VerifyEmailToken
from django.urls import reverse_lazy
from django.contrib import messages
from .utils import send_email
from . import forms
import secrets

class LoginView(FormView):
	form_class = forms.LoginForm
	template_name = "accounts/login.html"
	success_url = reverse_lazy("organization:index")

	def form_valid(self, form):
		user = form.get_authenticated_user()
		if user is not None:
			login(self.request, user)

		organization_user = form.get_current_organization_user()
		organization_user_id = organization_user.pk if organization_user is not None else ''
		self.request.session["organization_user_id"] = organization_user_id
		return super().form_valid(form)

class LogoutView(RedirectView):
	permanent = False
	url = reverse_lazy("accounts:login")

	def get_redirect_url(self, *args, **kwargs):
		logout(self.request)
		return super(LogoutView, self).get_redirect_url(*args, **kwargs)

class RegisterView(FormView):
	form_class = forms.RegisterForm
	template_name = "accounts/register.html"
	success_url = reverse_lazy("accounts:verify")

	def form_valid(self, form):
		user = form.get_authenticated_user()
		if user is not None:
			login(self.request, user)

		organization_user = form.get_current_organization_user()
		organization_user_id = organization_user.pk if organization_user is not None else ''
		self.request.session["organization_user_id"] = organization_user_id

		return super().form_valid(form)


class VerifyEmailRedirectView(RedirectView):
	permanent = False
	url = reverse_lazy('dashboard')

	def get_redirect_url(self, *args, **kwargs):
		verify_token = get_object_or_404(
			VerifyEmailToken, 
			token=kwargs['token'],
			deleted = False
		)
		user = verify_token.user
		user.is_active  = True
		user.is_email_verified  = True
		user.save()
		messages.add_message(self.request, messages.INFO, f'Email <b>{user.email}</b> has been verified')
		return super().get_redirect_url(*args, **kwargs)


class SendVerifyEmailView(RedirectView):
	permanent = False
	url = reverse_lazy('dashboard')

	def get_redirect_url(self, *args, **kwargs):
		user = self.request.user
		verify_token, created = VerifyEmailToken.objects.get_or_create(user=user)
		verify_token.token = secrets.token_hex(32)
		verify_token.save()


		template_path_html = 'accounts/email/verify_email.html'
		template_path_txt = 'accounts/email/verify_email.txt'
		subject = "Verify your email"
		email = user.email

		scheme = self.request.scheme
		host = self.request.META['HTTP_HOST']
		url = f'{scheme}://{host}'
		verify_url = "%s%s" % (url , reverse_lazy('accounts:verify', kwargs={'token' : verify_token.token}))

		data = {"name" : user.first_name, 'verify_url' : verify_url }
		r = send_email(template_path_html, template_path_txt, subject, email, data)

		messages.add_message(self.request, messages.INFO, f'We have sent you a verification email')

		return super().get_redirect_url(*args, **kwargs)


class DevelopersView(TemplateView):
	template_name = "accounts/developers.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		token, created = Token.objects.get_or_create(user=user)
		context['token'] = token
		return context
