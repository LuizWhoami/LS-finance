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

from apps.services.models import Service
from apps.barbers.models import Barber
from apps.customers.models import Customer
from apps.appointments.models import Appointment

from .forms import ClientAppointmentForm, ClientRegistrationForm

User = get_user_model()


class ClientHomeView(TemplateView):
    """Página inicial da área do cliente."""
    template_name = 'client/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Buscar serviços ativos
        context['services'] = Service.objects.filter(
            status='active', 
            is_active=True
        )[:6]  # Mostrar apenas 6 serviços na home
        # Buscar barbeiros ativos
        context['barbers'] = Barber.objects.filter(
            status='active', 
            is_active=True
        )[:4]  # Mostrar apenas 4 barbeiros na home
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
    """Cliente cria um agendamento (com ou sem login)."""
    model = Appointment
    form_class = ClientAppointmentForm
    template_name = 'client/appointment_create.html'
    success_url = reverse_lazy('client:appointments')

    def get_initial(self):
        initial = super().get_initial()
        # Preencher serviço se passado via GET
        service_id = self.request.GET.get('service')
        if service_id:
            try:
                service = Service.objects.get(id=service_id, is_active=True)
                initial['service'] = service
            except Service.DoesNotExist:
                pass
        # Preencher barbeiro se passado via GET
        barber_id = self.request.GET.get('barber')
        if barber_id:
            try:
                barber = Barber.objects.get(id=barber_id, is_active=True)
                initial['barber'] = barber
            except Barber.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        customer_name = form.cleaned_data.get('customer_name')
        customer_phone = form.cleaned_data.get('customer_phone')
        
        # Tentar encontrar cliente pelo telefone
        customer = Customer.objects.filter(phone=customer_phone).first()
        
        # Se não encontrou e usuário está logado, criar vinculado ao usuário
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
            # Cliente visitante - criar sem usuário
            customer = Customer.objects.create(
                full_name=customer_name,
                phone=customer_phone,
                email='',
                status='active'
            )
        
        # Se cliente existe e usuário está logado, vincular se não estiver vinculado
        if customer and self.request.user.is_authenticated and not customer.user:
            customer.user = self.request.user
            customer.save()
        
        # Atualizar nome se mudou
        if customer.full_name != customer_name:
            customer.full_name = customer_name
            customer.save()
        
        # Criar o agendamento
        appointment = form.save(commit=False)
        appointment.customer = customer
        
        # Se não estiver logado, salvar session_key
        if not self.request.user.is_authenticated:
            appointment.session_key = self.request.session.session_key
            if not appointment.session_key:
                self.request.session.create()
                appointment.session_key = self.request.session.session_key
        
        appointment.service_price = appointment.service.price
        appointment.final_price = appointment.service.price
        appointment.end_time = form.cleaned_data.get('end_time')
        appointment.start_time = form.cleaned_data.get('start_time')
        appointment.save()
        
        messages.success(self.request, _('Agendamento realizado com sucesso!'))
        return super().form_valid(form)


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
                    customer=customer
                ).select_related('barber', 'service').order_by('-start_time')
        else:
            session_key = self.request.session.session_key
            if session_key:
                return Appointment.objects.filter(
                    session_key=session_key
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
                return Appointment.objects.filter(customer=customer)
        else:
            session_key = self.request.session.session_key
            if session_key:
                return Appointment.objects.filter(session_key=session_key)
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
