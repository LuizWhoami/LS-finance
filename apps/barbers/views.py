"""
Views para o app Barbers.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Barber, WorkSchedule, TimeOff
from .forms import BarberForm, WorkScheduleForm, TimeOffForm


class BarberListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de barbeiros."""
    model = Barber
    template_name = 'barbers/barber_list.html'
    context_object_name = 'barbers'
    permission_required = 'barbers.view_barber'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        
        # Busca
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search) |
                Q(specialty__icontains=search)
            )
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        is_active = self.request.GET.get('is_active')
        if is_active == 'yes':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'no':
            queryset = queryset.filter(is_active=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Barber.BarberStatus.choices
        return context


class BarberCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Cria um novo barbeiro."""
    model = Barber
    form_class = BarberForm
    template_name = 'barbers/barber_form.html'
    permission_required = 'barbers.add_barber'
    success_url = reverse_lazy('barbers:list')

    def form_valid(self, form):
        messages.success(self.request, _('Barbeiro criado com sucesso!'))
        return super().form_valid(form)


class BarberUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edita um barbeiro."""
    model = Barber
    form_class = BarberForm
    template_name = 'barbers/barber_form.html'
    permission_required = 'barbers.change_barber'
    success_url = reverse_lazy('barbers:list')

    def form_valid(self, form):
        messages.success(self.request, _('Barbeiro atualizado com sucesso!'))
        return super().form_valid(form)


class BarberDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Remove um barbeiro."""
    model = Barber
    template_name = 'barbers/barber_confirm_delete.html'
    permission_required = 'barbers.delete_barber'
    success_url = reverse_lazy('barbers:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Barbeiro removido com sucesso!'))
        return super().delete(request, *args, **kwargs)


class BarberDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detalhes de um barbeiro."""
    model = Barber
    template_name = 'barbers/barber_detail.html'
    context_object_name = 'barber'
    permission_required = 'barbers.view_barber'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['work_schedules'] = self.object.work_schedules.filter(is_available=True)
        context['time_offs'] = self.object.time_offs.filter(is_approved=True)
        context['appointments_today'] = self.object.appointments.filter(
            start_time__date=timezone.now().date()
        )
        return context


class WorkScheduleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de horários de trabalho."""
    model = WorkSchedule
    template_name = 'barbers/work_schedule_list.html'
    context_object_name = 'schedules'
    permission_required = 'barbers.view_workschedule'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset().select_related('barber', 'barber__user')
        
        barber = self.request.GET.get('barber')
        if barber:
            queryset = queryset.filter(barber_id=barber)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['barbers'] = Barber.objects.filter(is_active=True)
        return context


class WorkScheduleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Cria um novo horário de trabalho."""
    model = WorkSchedule
    form_class = WorkScheduleForm
    template_name = 'barbers/work_schedule_form.html'
    permission_required = 'barbers.add_workschedule'
    success_url = reverse_lazy('barbers:schedule_list')

    def form_valid(self, form):
        messages.success(self.request, _('Horário criado com sucesso!'))
        return super().form_valid(form)


class WorkScheduleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edita um horário de trabalho."""
    model = WorkSchedule
    form_class = WorkScheduleForm
    template_name = 'barbers/work_schedule_form.html'
    permission_required = 'barbers.change_workschedule'
    success_url = reverse_lazy('barbers:schedule_list')

    def form_valid(self, form):
        messages.success(self.request, _('Horário atualizado com sucesso!'))
        return super().form_valid(form)


class WorkScheduleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Remove um horário de trabalho."""
    model = WorkSchedule
    template_name = 'barbers/work_schedule_confirm_delete.html'
    permission_required = 'barbers.delete_workschedule'
    success_url = reverse_lazy('barbers:schedule_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Horário removido com sucesso!'))
        return super().delete(request, *args, **kwargs)
