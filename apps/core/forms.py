from django import forms
from django.contrib.auth.forms import AuthenticationForm


class ERPAuthenticationForm(AuthenticationForm):
    """Formulario de ingreso propio del ERP."""

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "Ingresá tu usuario",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "current-password",
                "placeholder": "Ingresá tu contraseña",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos.",
        "inactive": "Esta cuenta se encuentra inactiva.",
    }
