"""
Forms para o app Barbers.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Barber, WorkSchedule, TimeOff


class BarberForm(forms.ModelForm):
    """Form para barbeiro."""
    
    class Meta:
        model = Barber
        fields = [
            'user', 'registration_number', 'specialty', 'bio',
            'experience_years', 'commission_percentage', 'status',
            'image', 'is_active'  # Adicionado campo image
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specialty': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'commission_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WorkScheduleForm(forms.ModelForm):
    """Form para horário de trabalho."""
    
    class Meta:
        model = WorkSchedule
        fields = [
            'barber', 'day_of_week', 'start_time', 'end_time',
            'break_start', 'break_end', 'is_available', 'order'
        ]
        widgets = {
            'barber': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'break_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'break_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TimeOffForm(forms.ModelForm):
    """Form para afastamento."""
    
    class Meta:
        model = TimeOff
        fields = [
            'barber', 'type', 'start_date', 'end_date',
            'description', 'is_approved'
        ]
        widgets = {
            'barber': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
