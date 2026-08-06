from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Subscription


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['customer', 'plan', 'start_date', 'end_date', 'payment_method', 'auto_renew']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'auto_renew': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
