"""
Forms para o app Customers.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Customer, CustomerHistory


class CustomerForm(forms.ModelForm):
    """Form para cliente."""
    
    class Meta:
        model = Customer
        fields = [
            'user', 'full_name', 'cpf', 'phone', 'email', 'birth_date',
            'address', 'city', 'state', 'zip_code',
            'status', 'preferred_barber', 'preferred_services', 'notes'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'cpf'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'phone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'preferred_barber': forms.Select(attrs={'class': 'form-select'}),
            'preferred_services': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CustomerHistoryForm(forms.ModelForm):
    """Form para histórico do cliente."""
    
    class Meta:
        model = CustomerHistory
        fields = ['type', 'description', 'metadata']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'metadata': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
