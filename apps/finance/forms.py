"""
Forms para o app Finance.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Transaction, CashRegister, Commission


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'transaction_type', 'payment_method', 'amount',
            'description', 'transaction_date', 'customer',
            'barber', 'appointment', 'cash_register'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'transaction_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'barber': forms.Select(attrs={'class': 'form-select'}),
            'appointment': forms.Select(attrs={'class': 'form-select'}),
            'cash_register': forms.Select(attrs={'class': 'form-select'}),
        }


class CashRegisterForm(forms.ModelForm):
    class Meta:
        model = CashRegister
        fields = ['opening_balance', 'opened_by', 'notes']
        widgets = {
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'opened_by': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
