from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import StudentProfile
import json

class UserRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'autocomplete': 'name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'student@university.edu',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password (min 8 characters)',
            'autocomplete': 'new-password'
        })
    )
    confirm_password = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
    )
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ProfileSetupForm(forms.ModelForm):
    INTEREST_CHOICES = StudentProfile.AVAILABLE_INTERESTS

    selected_interests = forms.MultipleChoiceField(
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'btn-check'}),
        required=False
    )

    class Meta:
        model = StudentProfile
        fields = ['full_name', 'avatar', 'education_level', 'institution', 'learning_level', 'career_goal']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'education_level': forms.Select(attrs={'class': 'form-select'}),
            'institution': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College, University, or Self-study'}),
            'learning_level': forms.Select(attrs={'class': 'form-select'}),
            'career_goal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Full-Stack Developer, AI Engineer, Data Scientist'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['selected_interests'].initial = self.instance.get_interests_list()

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected = self.cleaned_data.get('selected_interests', [])
        instance.set_interests_list(selected)
        if commit:
            instance.save()
        return instance
