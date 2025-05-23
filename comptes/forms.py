from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2', 'profession']