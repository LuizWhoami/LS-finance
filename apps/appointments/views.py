"""
Views para o app Appointments.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import redirect

from .models import Appointment
from .forms import AppointmentForm


class AppointmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de agendamentos."""
    model = Appointment
    template_name = 'appointments/appointment_list.html'
    context_object_name = 'appointments'
    permission_required = 'appointments.view_appointment'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'customer', 'barber', 'barber__user', 'service'
        )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer__full_name__icontains=search) |
                Q(barber__user__first_name__icontains=search) |
                Q(barber__user__last_name__icontains=search) |
                Q(service__name__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Appointment.AppointmentStatus.choices
        return context


class AppointmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Cria um novo agendamento."""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    permission_required = 'appointments.add_appointment'
    success_url = reverse_lazy('appointments:list')

    def form_valid(self, form):
        messages.success(self.request, _('Agendamento criado com sucesso!'))
        return super().form_valid(form)


class AppointmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edita um agendamento."""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    permission_required = 'appointments.change_appointment'
    success_url = reverse_lazy('appointments:list')

    def form_valid(self, form):
        messages.success(self.request, _('Agendamento atualizado com sucesso!'))
        return super().form_valid(form)


class AppointmentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Remove um agendamento."""
    model = Appointment
    template_name = 'appointments/appointment_confirm_delete.html'
    permission_required = 'appointments.delete_appointment'
    success_url = reverse_lazy('appointments:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Agendamento removido com sucesso!'))
        return super().delete(request, *args, **kwargs)


class AppointmentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detalhes de um agendamento."""
    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'
    permission_required = 'appointments.view_appointment'


class AppointmentConfirmView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Confirma um agendamento."""
    model = Appointment
    template_name = 'appointments/appointment_confirm.html'
    permission_required = 'appointments.change_appointment'

    def post(self, request, *args, **kwargs):
        appointment = self.get_object()
        try:
            appointment.confirm()
            messages.success(request, _('Agendamento confirmado com sucesso!'))
        except Exception as e:
            messages.error(request, str(e))
        return redirect('appointments:detail', pk=appointment.pk)


class AppointmentCancelView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Cancela um agendamento."""
    model = Appointment
    template_name = 'appointments/appointment_cancel.html'
    permission_required = 'appointments.change_appointment'

    def post(self, request, *args, **kwargs):
        appointment = self.get_object()
        reason = request.POST.get('reason', '')
        try:
            appointment.cancel(user=request.user, reason=reason)
            messages.success(request, _('Agendamento cancelado com sucesso!'))
        except Exception as e:
            messages.error(request, str(e))
        return redirect('appointments:detail', pk=appointment.pk)


class AppointmentCalendarView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Calendário de agendamentos."""
    model = Appointment
    template_name = 'appointments/appointment_calendar.html'
    context_object_name = 'appointments'
    permission_required = 'appointments.view_appointment'

    def get_queryset(self):
        now = timezone.now()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Appointment.objects.filter(
            start_time__gte=start,
            status__in=[
                Appointment.AppointmentStatus.SCHEDULED,
                Appointment.AppointmentStatus.CONFIRMED,
                Appointment.AppointmentStatus.IN_PROGRESS
            ]
        ).select_related('customer', 'barber', 'service')
