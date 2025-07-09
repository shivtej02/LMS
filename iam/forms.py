from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

# 🔹 Signup Form for User
class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']


# 🔹 Edit Form for updating username and email
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


# 🔹 Profile Form for UserProfile (with email)
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['email', 'phone_no', 'photo', 'emergency_contact_no']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'phone_no': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'emergency_contact_no': forms.TextInput(attrs={'placeholder': 'Enter emergency contact number'}),
        }
