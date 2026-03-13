"""
Django Forms for AI-Driven Personal Preference Identifier.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterForm(forms.Form):
    name     = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"placeholder": "Jane Smith", "autocomplete": "name"}))
    email    = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}))
    password = forms.CharField(min_length=6, widget=forms.PasswordInput(attrs={"placeholder": "Min. 6 characters"}))

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email


class LoginForm(forms.Form):
    email    = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "autocomplete": "current-password"}))
