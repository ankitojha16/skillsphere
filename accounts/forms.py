from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
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

        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error('password', error)

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
        fields = ['full_name', 'avatar', 'avatar_url_external', 'education_level', 'institution', 'learning_level', 'career_goal', 'analytics_opt_out']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'avatar_url_external': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://avatars.githubusercontent.com/u/... or any photo URL'}),
            'education_level': forms.Select(attrs={'class': 'form-select'}),
            'institution': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College, University, or Self-study'}),
            'learning_level': forms.Select(attrs={'class': 'form-select'}),
            'career_goal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Full-Stack Developer, AI Engineer, Data Scientist'}),
            'analytics_opt_out': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['selected_interests'].initial = self.instance.get_interests_list()

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar

        # 1. Strict File Size Limit: 5 MB
        max_size = 5 * 1024 * 1024
        if avatar.size > max_size:
            raise ValidationError("Avatar image file size must not exceed 5 MB.")

        # 2. Decompression Bomb Protection (Limit total pixels)
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 10_000_000

        # 3. Deep Image Integrity Verification using Pillow
        try:
            avatar.seek(0)
            img = Image.open(avatar)
            img.verify()
        except Exception:
            raise ValidationError("The uploaded file is corrupt, truncated, or not a valid image.")

        # 4. Check Allowed Image Formats & Dimensions
        try:
            avatar.seek(0)
            img = Image.open(avatar)
            allowed_formats = {'JPEG', 'PNG', 'WEBP'}
            img_format = (img.format or '').upper()
            if img_format not in allowed_formats:
                raise ValidationError(f"Unsupported image format: {img_format or 'Unknown'}. Please upload a JPEG, PNG, or WebP image.")

            if img.width > 4096 or img.height > 4096:
                raise ValidationError(f"Image dimensions ({img.width}×{img.height}) exceed maximum allowed limit of 4096×4096 pixels.")
        except ValidationError:
            raise
        except Exception:
            raise ValidationError("Unable to decode the uploaded image. Please ensure it is a valid JPEG, PNG, or WebP file.")
        finally:
            avatar.seek(0)

        return avatar

    def save(self, commit=True):
        import os
        import base64
        import io
        from django.conf import settings

        instance = super().save(commit=False)
        selected = self.cleaned_data.get('selected_interests', [])
        instance.set_interests_list(selected)

        # Safely convert uploaded avatar into optimized base64 Data URI
        avatar_file = self.cleaned_data.get('avatar')
        if avatar_file and hasattr(avatar_file, 'read'):
            try:
                from PIL import Image
                avatar_file.seek(0)
                img = Image.open(avatar_file)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85, optimize=True)
                encoded = base64.b64encode(buf.getvalue()).decode('ascii')
                instance.avatar_data_uri = f"data:image/jpeg;base64,{encoded}"
            except Exception:
                try:
                    avatar_file.seek(0)
                    encoded = base64.b64encode(avatar_file.read()).decode('ascii')
                    content_type = getattr(avatar_file, 'content_type', 'image/jpeg')
                    instance.avatar_data_uri = f"data:{content_type};base64,{encoded}"
                except Exception:
                    pass

            # In production or serverless environments, don't write to disk
            if os.environ.get('VERCEL') or not settings.DEBUG:
                instance.avatar = None

        if commit:
            instance.save()
        return instance
