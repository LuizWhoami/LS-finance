"""
Views para a área do cliente.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError
from django.http import JsonResponse
from datetime import datetime, timedelta

from apps.services.models import Service
from apps.barbers.models import Barber, WorkSchedule
from apps.customers.models import Customer
from apps.appointments.models import Appointment
from apps.core.exceptions import AppointmentConflictError

from .forms import ClientAppointmentForm, ClientRegistrationForm

User = get_user_model()


class ClientHomeView(TemplateView):
    """Página inicial da área do cliente."""
    template_name = 'client/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = Service.objects.filter(
            status='active', 
            is_active=True
        )[:6]
        context['barbers'] = Barber.objects.filter(
            status='active', 
            is_active=True
        )[:4]
        return context


class ClientServiceListView(ListView):
    """Lista de serviços para o cliente."""
    model = Service
    template_name = 'client/services.html'
    context_object_name = 'services'
    paginate_by = 12

    def get_queryset(self):
        return Service.objects.filter(status='active', is_active=True)


class ClientBarberListView(ListView):
    """Lista de barbeiros para o cliente."""
    model = Barber
    template_name = 'client/barbers.html'
    context_object_name = 'barbers'
    paginate_by = 12

    def get_queryset(self):
        return Barber.objects.filter(status='active', is_active=True)


class ClientAppointmentCreateView(CreateView):
    """Cliente cria um agendamento com validação."""
    model = Appointment
    form_class = ClientAppointmentForm
    template_name = 'client/appointment_create.html'
    success_url = reverse_lazy('client:appointments')

    def get_initial(self):
        initial = super().get_initial()
        service_id = self.request.GET.get('service')
        if service_id:
            try:
                service = Service.objects.get(id=service_id, is_active=True)
                initial['service'] = service
            except Service.DoesNotExist:
                pass
        barber_id = self.request.GET.get('barber')
        if barber_id:
            try:
                barber = Barber.objects.get(id=barber_id, is_active=True)
                initial['barber'] = barber
            except Barber.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        try:
            customer_name = form.cleaned_data.get('customer_name')
            customer_phone = form.cleaned_data.get('customer_phone')
            
            customer = Customer.objects.filter(phone=customer_phone).first()
            
            if not customer and self.request.user.is_authenticated:
                customer, created = Customer.objects.get_or_create(
                    user=self.request.user,
                    defaults={
                        'full_name': customer_name,
                        'phone': customer_phone,
                        'email': self.request.user.email or '',
                        'status': 'active'
                    }
                )
            elif not customer:
                customer = Customer.objects.create(
                    full_name=customer_name,
                    phone=customer_phone,
                    email='',
                    status='active'
                )
            
            if customer and self.request.user.is_authenticated and not customer.user:
                customer.user = self.request.user
                customer.save()
            
            if customer.full_name != customer_name:
                customer.full_name = customer_name
                customer.save()
            
            appointment = form.save(commit=False)
            appointment.customer = customer
            
            if not self.request.user.is_authenticated:
                appointment.session_key = self.request.session.session_key
                if not appointment.session_key:
                    self.request.session.create()
                    appointment.session_key = self.request.session.session_key
            
            appointment.service_price = appointment.service.price
            appointment.final_price = appointment.service.price
            appointment.end_time = form.cleaned_data.get('end_time')
            appointment.start_time = form.cleaned_data.get('start_time')
            
            try:
                appointment.save()
            except IntegrityError:
                messages.error(
                    self.request, 
                    _('Este horário já está ocupado para este barbeiro. Por favor, escolha outro horário.')
                )
                return self.form_invalid(form)
            
            messages.success(self.request, _('Agendamento realizado com sucesso!'))
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(self.request, f'Erro ao criar agendamento: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)


class ClientAppointmentListView(ListView):
    """Lista de agendamentos do cliente (com ou sem login)."""
    model = Appointment
    template_name = 'client/appointments.html'
    context_object_name = 'appointments'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_authenticated:
            customer = Customer.objects.filter(user=self.request.user).first()
            if customer:
                return Appointment.objects.filter(
                    customer=customer,
                    is_active=True
                ).select_related('barber', 'service').order_by('-start_time')
        else:
            session_key = self.request.session.session_key
            if session_key:
                return Appointment.objects.filter(
                    session_key=session_key,
                    is_active=True
                ).select_related('barber', 'service').order_by('-start_time')
        return Appointment.objects.none()


class ClientAppointmentCancelView(DetailView):
    """Cliente cancela um agendamento (com ou sem login)."""
    model = Appointment
    template_name = 'client/appointment_cancel.html'
    context_object_name = 'appointment'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            customer = Customer.objects.filter(user=self.request.user).first()
            if customer:
                return Appointment.objects.filter(customer=customer, is_active=True)
        else:
            session_key = self.request.session.session_key
            if session_key:
                return Appointment.objects.filter(session_key=session_key, is_active=True)
        return Appointment.objects.none()

    def post(self, request, *args, **kwargs):
        appointment = self.get_object()
        reason = request.POST.get('reason', 'Cancelado pelo cliente')
        
        try:
            appointment.cancel(user=request.user if request.user.is_authenticated else None, reason=reason)
            messages.success(request, _('Agendamento cancelado com sucesso!'))
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('client:appointments')


class ClientProfileView(LoginRequiredMixin, UpdateView):
    """Perfil do cliente."""
    model = Customer
    template_name = 'client/profile.html'
    fields = ['full_name', 'phone', 'email', 'birth_date', 'address', 'city', 'state', 'zip_code']
    success_url = reverse_lazy('client:profile')

    def get_object(self):
        customer, _ = Customer.objects.get_or_create(
            user=self.request.user,
            defaults={
                'full_name': self.request.user.get_full_name(),
                'email': self.request.user.email,
                'phone': self.request.user.phone or '',
                'status': 'active'
            }
        )
        return customer

    def form_valid(self, form):
        messages.success(self.request, _('Perfil atualizado com sucesso!'))
        return super().form_valid(form)


class ClientLoginView(LoginView):
    """Login do cliente."""
    template_name = 'client/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('client:home')


class ClientRegisterView(CreateView):
    """Registro de novo cliente."""
    template_name = 'client/register.html'
    success_url = reverse_lazy('client:login')
    form_class = ClientRegistrationForm

    def form_valid(self, form):
        messages.success(self.request, _('Cadastro realizado com sucesso! Faça login para continuar.'))
        return super().form_valid(form)


def get_available_slots(request):
    """API para buscar horários disponíveis baseado nos horários de trabalho."""
    date_str = request.GET.get('date')
    barber_id = request.GET.get('barber')
    service_id = request.GET.get('service')
    
    if not all([date_str, barber_id, service_id]):
        return JsonResponse({'error': 'Parâmetros incompletos'}, status=400)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        barber = Barber.objects.get(id=barber_id)
        service = Service.objects.get(id=service_id)
    except (ValueError, Barber.DoesNotExist, Service.DoesNotExist):
        return JsonResponse({'error': 'Dados inválidos'}, status=400)
    
    # Verificar horário de trabalho do barbeiro para este dia
    day_of_week = date.isoweekday()
    schedule = WorkSchedule.objects.filter(
        barber=barber,
        day_of_week=day_of_week,
        is_available=True,
        is_active=True
    ).first()
    
    if not schedule:
        return JsonResponse({
            'slots': [],
            'message': 'Barbeiro não trabalha neste dia'
        })
    
    # Gerar slots de horário com timezone-aware
    slots = []
    current_time = timezone.make_aware(datetime.combine(date, schedule.start_time))
    end_time = timezone.make_aware(datetime.combine(date, schedule.end_time))
    service_duration = service.duration_minutes
    interval_minutes = 30
    now = timezone.now()
    
    while current_time < end_time:
        slot_end = current_time + timedelta(minutes=service_duration)
        
        if slot_end > end_time:
            break
        
        # Verificar intervalo
        is_lunch = False
        if schedule.break_start and schedule.break_end:
            break_start = timezone.make_aware(datetime.combine(date, schedule.break_start))
            break_end = timezone.make_aware(datetime.combine(date, schedule.break_end))
            if current_time >= break_start and slot_end <= break_end:
                is_lunch = True
            elif current_time < break_start and slot_end > break_start:
                is_lunch = True
            elif current_time >= break_start and current_time < break_end:
                is_lunch = True
        
        # Verificar conflitos
        has_conflict = Appointment.objects.filter(
            barber=barber,
            is_active=True,
            status__in=[
                Appointment.AppointmentStatus.SCHEDULED,
                Appointment.AppointmentStatus.CONFIRMED,
                Appointment.AppointmentStatus.IN_PROGRESS
            ],
            start_time__lt=slot_end,
            end_time__gt=current_time
        ).exists()
        
        # Determinar status
        if is_lunch:
            status = 'lunch'
            label = '🍽️ Intervalo'
        elif has_conflict:
            status = 'unavailable'
            label = '❌ Ocupado'
        else:
            status = 'available'
            label = '✅ Disponível'
        
        # Verificar se é futuro
        is_future = current_time > now
        
        if is_future and status == 'available':
            slots.append({
                'time': current_time.strftime('%H:%M'),
                'status': status,
                'label': label,
                'start': current_time.isoformat(),
                'end': slot_end.isoformat()
            })
        
        current_time += timedelta(minutes=interval_minutes)
    
    return JsonResponse({
        'slots': slots,
        'schedule': {
            'start': schedule.start_time.strftime('%H:%M'),
            'end': schedule.end_time.strftime('%H:%M'),
            'break_start': schedule.break_start.strftime('%H:%M') if schedule.break_start else None,
            'break_end': schedule.break_end.strftime('%H:%M') if schedule.break_end else None
        }
    })
