from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Job
from .models import *


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email','password1', 'password2', 'role']

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'location', 'expiry_date', 'required_workers',]




class JobApplicationForm(forms.ModelForm):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = JobApplication
        fields = ['name', 'email', 'phone_number']       


