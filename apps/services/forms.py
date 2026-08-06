"""
Forms para o app Services.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ServiceCategory, Service


class ServiceCategoryForm(forms.ModelForm):
    """Form para categoria de serviço."""
    
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description', 'icon', 'color', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-cut'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ServiceForm(forms.ModelForm):
    """Form para serviço."""
    
    class Meta:
        model = Service
        fields = [
            'name', 'category', 'description', 'price', 'duration_minutes',
            'commission_percentage', 'status', 'image', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'commission_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
