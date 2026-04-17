"""
Forms for user authentication and profile management.
"""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.accounts.models import UserProfile, AuditLog


class LoginForm(forms.Form):
    """Login form for user authentication."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })
    )


class RegistrationForm(forms.Form):
    """User registration form."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password (minimum 8 characters)',
        })
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
        })
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        initial='staff',
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Department',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number',
        })
    )
    base_wage = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'})
    )
    shift_start = forms.TimeField(
        required=False, 
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    shift_end = forms.TimeField(
        required=False, 
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    def clean_username(self):
        """Validate that username is unique."""
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username
    
    def clean_email(self):
        """Validate that email is unique."""
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean(self):
        """Validate that passwords match."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Passwords do not match.')
            if len(password) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
        
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile."""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['department', 'phone', 'address']
        widgets = {
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Address',
                'rows': 3,
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with user data."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        """Save profile and update user information."""
        profile = super().save(commit=False)
        profile.user.first_name = self.cleaned_data.get('first_name', '')
        profile.user.last_name = self.cleaned_data.get('last_name', '')
        profile.user.email = self.cleaned_data.get('email', '')
        
        if commit:
            profile.user.save()
            profile.save()
        return profile


class AuditLogModelForm(forms.ModelForm):
    """Form for audit log (display only)."""
    class Meta:
        model = AuditLog
        fields = ['user', 'action', 'model_name', 'object_id', 'ip_address']
        widgets = {
            field: forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
            for field in fields
        }
