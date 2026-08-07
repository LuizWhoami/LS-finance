"""
Forms para a área do cliente.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.services.models import Service
from apps.barbers.models import Barber

User = get_user_model()


class ClientAppointmentForm(forms.ModelForm):
    """Formulário de agendamento para o cliente (com ou sem login)."""
    
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
    
    class Meta:
        model = Appointment
        fields = ['customer_name', 'customer_phone', 'service', 'barber', 'appointment_date', 'appointment_time', 'notes']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'barber': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Alguma observação? (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(
            status='active', is_active=True
        )
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
        service = cleaned_data.get('service')
        
        if appointment_date and appointment_time and service:
            start_time = timezone.datetime.combine(appointment_date, appointment_time)
            start_time = timezone.make_aware(start_time)
            
            end_time = start_time + timezone.timedelta(minutes=service.duration_minutes)
            
            cleaned_data['start_time'] = start_time
            cleaned_data['end_time'] = end_time
            
            if appointment_time.hour < 8 or appointment_time.hour >= 20:
                raise forms.ValidationError(
                    _('Horário de funcionamento: 08:00 às 20:00. Por favor, escolha um horário dentro deste período.')
                )
        
        return cleaned_data


class ClientRegistrationForm(UserCreationForm):
    """Formulário de registro para cliente usando o modelo User customizado."""
    
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

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        service = cleaned_data.get('service')
        barber = cleaned_data.get('barber')
        
        if appointment_date and appointment_time and service and barber:
            # Combinar data e hora
            start_time = timezone.datetime.combine(appointment_date, appointment_time)
            start_time = timezone.make_aware(start_time)
            
            # Calcular end_time
            end_time = start_time + timezone.timedelta(minutes=service.duration_minutes)
            
            cleaned_data['start_time'] = start_time
            cleaned_data['end_time'] = end_time
            
            # Validar horário de funcionamento
            if appointment_time.hour < 8 or appointment_time.hour >= 20:
                raise forms.ValidationError(
                    _('Horário de funcionamento: 08:00 às 20:00. Por favor, escolha um horário dentro deste período.')
                )
            
            # Validar disponibilidade do barbeiro
            from apps.barbers.models import WorkSchedule
            day_of_week = appointment_date.weekday() + 1  # Django: 0=Segunda
            
            schedule = WorkSchedule.objects.filter(
                barber=barber,
                day_of_week=day_of_week,
                is_available=True,
                is_active=True
            ).first()
            
            if not schedule:
                raise forms.ValidationError(
                    _('O barbeiro não trabalha neste dia da semana.')
                )
            
            # Verificar horário de início e término
            if appointment_time < schedule.start_time or appointment_time > schedule.end_time:
                raise forms.ValidationError(
                    _('O barbeiro trabalha das {} às {} neste dia.').format(
                        schedule.start_time.strftime('%H:%M'),
                        schedule.end_time.strftime('%H:%M')
                    )
                )
            
            # Verificar intervalo
            if schedule.break_start and schedule.break_end:
                if appointment_time >= schedule.break_start and appointment_time < schedule.break_end:
                    raise forms.ValidationError(
                        _('O barbeiro está em intervalo das {} às {}.').format(
                            schedule.break_start.strftime('%H:%M'),
                            schedule.break_end.strftime('%H:%M')
                        )
                    )
            
            # Verificar conflitos com outros agendamentos
            from apps.appointments.models import Appointment
            conflicts = Appointment.objects.filter(
                barber=barber,
                is_active=True,
                status__in=[
                    Appointment.AppointmentStatus.SCHEDULED,
                    Appointment.AppointmentStatus.CONFIRMED,
                    Appointment.AppointmentStatus.IN_PROGRESS
                ],
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()
            
            if conflicts:
                raise forms.ValidationError(
                    _('O barbeiro já possui um agendamento neste horário.')
                )
        
        return cleaned_data
