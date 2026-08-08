"""
Forms para a área do cliente.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal

from apps.appointments.models import Appointment, AppointmentItem
from apps.services.models import Service
from apps.barbers.models import Barber

User = get_user_model()


class ClientAppointmentForm(forms.ModelForm):
    """Formulário de agendamento para o cliente."""
    
    customer_name = forms.CharField(
        label='Seu Nome',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu nome completo'
        })
    )
    
    customer_phone = forms.CharField(
        label='Seu Telefone',
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(11) 99999-9999'
        })
    )
    
    customer_email = forms.EmailField(
        label='Seu Email',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemplo.com (opcional)'
        })
    )
    
    appointment_date = forms.DateField(
        label='Data',
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    appointment_time = forms.TimeField(
        label='Horário',
        required=True,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    
    # Campos para múltiplos serviços (serão preenchidos dinamicamente)
    service_items = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = Appointment
        fields = ['customer_name', 'customer_phone', 'customer_email', 'barber', 'appointment_date', 'appointment_time', 'notes']
        widgets = {
            'barber': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Alguma observação? (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['barber'].queryset = Barber.objects.filter(
            status='active', is_active=True
        )
        
        if not self.instance.pk:
            now = timezone.now()
            if now.hour >= 18:
                default_date = (now + timezone.timedelta(days=1)).date()
            else:
                default_date = now.date()
            
            next_hour = now.replace(minute=0, second=0, microsecond=0) + timezone.timedelta(hours=1)
            if next_hour.hour < 8:
                next_hour = next_hour.replace(hour=8)
            elif next_hour.hour > 20:
                next_hour = next_hour.replace(hour=8) + timezone.timedelta(days=1)
            
            self.fields['appointment_date'].initial = default_date
            self.fields['appointment_time'].initial = next_hour.time()
    
    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        service_items = cleaned_data.get('service_items')
        
        if appointment_date and appointment_time:
            start_time = timezone.datetime.combine(appointment_date, appointment_time)
            start_time = timezone.make_aware(start_time)
            
            # Validar horário de funcionamento
            if appointment_time.hour < 8 or appointment_time.hour >= 20:
                raise forms.ValidationError(
                    _('Horário de funcionamento: 08:00 às 20:00.')
                )
            
            cleaned_data['start_time'] = start_time
        
        return cleaned_data


class ClientRegistrationForm(UserCreationForm):
    """Formulário de registro para cliente."""
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].help_text = 'Obrigatório. 150 caracteres ou menos. Letras, números e @/./+/-/_ apenas.'
        self.fields['password1'].help_text = 'Sua senha deve ter pelo menos 8 caracteres.'
