"""
Forms para o app Appointments.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Appointment
from apps.services.models import Service
from apps.barbers.models import Barber
from apps.customers.models import Customer


class AppointmentForm(forms.ModelForm):
    """Form para agendamento."""
    
    class Meta:
        model = Appointment
        fields = [
            'customer', 'barber', 'service', 'start_time', 'end_time',
            'status', 'payment_status', 'discount', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'barber': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas barbeiros ativos
        self.fields['barber'].queryset = Barber.objects.filter(is_active=True)
        
        # Filtrar apenas serviços ativos
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        
        # MOSTRAR TODOS OS CLIENTES (COM E SEM USUÁRIO)
        # Ordenar por nome
        self.fields['customer'].queryset = Customer.objects.filter(
            is_active=True
        ).order_by('full_name')
        
        # Adicionar um texto de ajuda para mostrar que clientes sem login também aparecem
        self.fields['customer'].help_text = "Clientes com e sem cadastro"
        
        # Definir valor padrão para data/hora
        if not self.instance.pk:
            now = timezone.now()
            # Arredondar para a próxima hora cheia
            next_hour = now.replace(minute=0, second=0, microsecond=0) + timezone.timedelta(hours=1)
            self.fields['start_time'].initial = next_hour
            self.fields['end_time'].initial = next_hour + timezone.timedelta(minutes=30)
