"""
Views para o app Appointments.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404

from .models import Appointment, AppointmentItem
from .forms import AppointmentForm


class AppointmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointments/appointment_list.html'
    context_object_name = 'appointments'
    permission_required = 'appointments.view_appointment'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'customer', 'barber', 'barber__user'
        ).prefetch_related('items', 'items__service')
        queryset = queryset.filter(is_active=True).exclude(
            status=Appointment.AppointmentStatus.CANCELLED
        )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer__full_name__icontains=search) |
                Q(barber__user__first_name__icontains=search) |
                Q(barber__user__last_name__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Appointment.AppointmentStatus.choices
        return context


class AppointmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    permission_required = 'appointments.add_appointment'
    success_url = reverse_lazy('appointments:list')

    def form_valid(self, form):
        messages.success(self.request, _('Agendamento criado com sucesso!'))
        return super().form_valid(form)


class AppointmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    permission_required = 'appointments.change_appointment'
    success_url = reverse_lazy('appointments:list')

    def form_valid(self, form):
        messages.success(self.request, _('Agendamento atualizado com sucesso!'))
        return super().form_valid(form)


class AppointmentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Appointment
    template_name = 'appointments/appointment_confirm_delete.html'
    permission_required = 'appointments.delete_appointment'
    success_url = reverse_lazy('appointments:list')

    def delete(self, request, *args, **kwargs):
        appointment = self.get_object()
        
        from apps.finance.models import Transaction
        transactions = Transaction.objects.filter(appointment=appointment)
        
        if transactions.exists():
            transactions.update(appointment=None)
            messages.warning(request, f'Agendamento tinha {transactions.count()} transações que foram desvinculadas.')
        
        appointment.is_active = False
        appointment.save(update_fields=['is_active', 'updated_at'])
        
        messages.success(request, _('Agendamento cancelado com sucesso!'))
        return redirect(self.success_url)


class AppointmentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'
    permission_required = 'appointments.view_appointment'


class AppointmentConfirmView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
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
    model = Appointment
    template_name = 'appointments/appointment_cancel.html'
    permission_required = 'appointments.change_appointment'

    def post(self, request, *args, **kwargs):
        appointment = self.get_object()
        reason = request.POST.get('reason', '')
        try:
            appointment.cancel_appointment(user=request.user, reason=reason)
            messages.success(request, _('Agendamento cancelado com sucesso!'))
        except Exception as e:
            messages.error(request, str(e))
        return redirect('appointments:detail', pk=appointment.pk)


class AppointmentCalendarView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointments/appointment_calendar.html'
    context_object_name = 'appointments'
    permission_required = 'appointments.view_appointment'

    def get_queryset(self):
        now = timezone.now()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Appointment.objects.filter(
            start_time__gte=start,
            is_active=True,
            status__in=[
                Appointment.AppointmentStatus.SCHEDULED,
                Appointment.AppointmentStatus.CONFIRMED,
                Appointment.AppointmentStatus.IN_PROGRESS
            ]
        ).select_related('customer', 'barber').prefetch_related('items', 'items__service')


class QuickStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'appointments.change_appointment'

    def post(self, request, pk, status):
        appointment = get_object_or_404(Appointment, pk=pk)
        
        valid_statuses = [choice[0] for choice in Appointment.AppointmentStatus.choices]
        if status not in valid_statuses:
            messages.error(request, _('Status inválido.'))
            return redirect('appointments:list')
        
        try:
            appointment.status = status
            
            if status == Appointment.AppointmentStatus.COMPLETED:
                appointment.completed_at = timezone.now()
                appointment.customer.increment_visits()
                appointment.barber.increment_services()
                
                # Buscar serviços do agendamento
                items = appointment.items.all()
                services_names = ', '.join([item.service.name for item in items]) if items.exists() else 'Serviço'
                
                from apps.finance.models import Transaction
                Transaction.objects.create(
                    appointment=appointment,
                    customer=appointment.customer,
                    barber=appointment.barber,
                    transaction_type=Transaction.TransactionType.INCOME,
                    payment_method=Transaction.PaymentMethod.CASH,
                    amount=appointment.final_price,
                    description=f'Serviço: {services_names} - Cliente: {appointment.customer.full_name}',
                    transaction_date=timezone.now(),
                    commission_amount=appointment.commission_amount,
                    commission_paid=False
                )
                
                from apps.finance.models import Commission
                Commission.objects.create(
                    barber=appointment.barber,
                    appointment=appointment,
                    amount=appointment.commission_amount,
                    percentage=appointment.barber.commission_percentage,
                    status=Commission.CommissionStatus.PENDING,
                    period_start=timezone.now().date(),
                    period_end=timezone.now().date()
                )
                
                messages.success(request, _('Agendamento concluído com sucesso! Transações e comissões geradas.'))
            
            elif status == Appointment.AppointmentStatus.CANCELLED:
                appointment.cancelled_at = timezone.now()
                appointment.cancellation_reason = 'Cancelado pelo administrador'
                messages.success(request, _('Agendamento cancelado com sucesso!'))
            
            elif status == Appointment.AppointmentStatus.CONFIRMED:
                messages.success(request, _('Agendamento confirmado com sucesso!'))
            
            elif status == Appointment.AppointmentStatus.IN_PROGRESS:
                messages.success(request, _('Agendamento marcado como em andamento!'))
            
            elif status == Appointment.AppointmentStatus.NO_SHOW:
                messages.success(request, _('Cliente marcado como não compareceu!'))
            
            elif status == Appointment.AppointmentStatus.SCHEDULED:
                messages.success(request, _('Agendamento marcado como agendado!'))
            
            appointment.save()
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar status: {str(e)}')
        
        return redirect('appointments:list')
