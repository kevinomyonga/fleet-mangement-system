from django import forms
from django.forms import ModelForm

from .models import OrganizationSmsProvider, OrganizationMpesaDetails

class AddSmsGatewayForm(ModelForm):
    provider = forms.ChoiceField(label='Provider', choices=OrganizationSmsProvider.PROVIDERS,
                               widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Provider'}))
    sender_id = forms.CharField(max_length=150, label='Sender id',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sender id'}))
    api_key = forms.CharField(required=False, max_length=200, label='Api key',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'api key' }))
    username = forms.CharField(required=False, max_length=150, label='Username',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    base_url = forms.URLField(required=False, max_length=200, label='Base url',
                               widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'base url'}))
    api_secret = forms.CharField(required=False, max_length=200, label='Api secret',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Api secret'}))
    account_sid = forms.CharField(required=False, max_length=200, label='Account SID',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'account sid'}))
    auth_token = forms.CharField(required=False, max_length=200, label='Auth token',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auth token'}))
    phone_number = forms.CharField(required=False, max_length=200, label='Phone _number',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '254712345670'}))
    class Meta:
        model = OrganizationSmsProvider
        exclude = ['verified']
        widgets = {
            'organization': forms.HiddenInput(),
            'verification_code': forms.HiddenInput()
            }


class SmsDetailsVerificationForm(forms.ModelForm):
    verification_code = forms.CharField(max_length=150, label='verification code',
                               widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': 'verification code'}))
    class Meta:
        model = OrganizationSmsProvider
        fields = ['verification_code']


class AddMpesaDetailsForm(forms.ModelForm):
    implementation = forms.ChoiceField(label='Implementation', choices=OrganizationMpesaDetails.IMPLEMENTATIONS,
                               widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Provider'}))
    business_short_code = forms.CharField(required=False, max_length=20, label='Business short code',
                                widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': 'Short code'}))
    consumer_key = forms.CharField(required=False, max_length=300, label='Consumer key',
                                widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': 'Consumer key'}))
    consumer_secret = forms.CharField(required=False, max_length=300, label='Consumer secret',
                                widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': 'consumer secret'}))
    pass_key = forms.CharField(required=False, max_length=300, label='Pass key',
                                widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': 'Pass key'}))
    # phone_number = forms.CharField(required=False, max_length=300, label='Phone number',
    #                             widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': '254712345678'}))
    client_id = forms.CharField(required=False, max_length=300, label='Client Id',
                                widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': 'client id'}))
    client_secret = forms.CharField(required=False, max_length=300, label='Client secret',
                                widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': 'client secret'}))
    till_number = forms.CharField(required=False, max_length=20, label='Till number',
                                widget=forms.TextInput(attrs={'class': 'form-control with-border', 'placeholder': 'kopo kopo till'}))
    class Meta:
        model =OrganizationMpesaDetails
        fields = '__all__'
        widgets = {'organization': forms.HiddenInput()}
        
