"""
Views para o app Barbers.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import timezone

from .models import Barber, WorkSchedule, TimeOff
from .forms import BarberForm, WorkScheduleForm, TimeOffForm


class BarberListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Barber
    template_name = 'barbers/barber_list.html'
    context_object_name = 'barbers'
    permission_required = 'barbers.view_barber'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        queryset = queryset.filter(is_active=True)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search) |
                Q(specialty__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Barber.BarberStatus.choices
        return context


class BarberCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Barber
    form_class = BarberForm
    template_name = 'barbers/barber_form.html'
    permission_required = 'barbers.add_barber'
    success_url = reverse_lazy('barbers:list')

    def form_valid(self, form):
        messages.success(self.request, _('Barbeiro criado com sucesso!'))
        return super().form_valid(form)


class BarberUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Barber
    form_class = BarberForm
    template_name = 'barbers/barber_form.html'
    permission_required = 'barbers.change_barber'
    success_url = reverse_lazy('barbers:list')

    def form_valid(self, form):
        messages.success(self.request, _('Barbeiro atualizado com sucesso!'))
        return super().form_valid(form)


class BarberDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Barber
    template_name = 'barbers/barber_confirm_delete.html'
    permission_required = 'barbers.delete_barber'
    success_url = reverse_lazy('barbers:list')

    def delete(self, request, *args, **kwargs):
        barber = self.get_object()
        barber.is_active = False
        barber.save()
        messages.success(request, _('Barbeiro desativado com sucesso!'))
        return redirect(self.success_url)


class BarberDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Barber
    template_name = 'barbers/barber_detail.html'
    context_object_name = 'barber'
    permission_required = 'barbers.view_barber'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['work_schedules'] = self.object.work_schedules.filter(is_available=True).order_by('day_of_week')
        context['time_offs'] = self.object.time_offs.filter(is_approved=True)
        context['appointments_today'] = self.object.appointments.filter(
            start_time__date=timezone.now().date(),
            is_active=True
        )
        return context


class WorkScheduleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = WorkSchedule
    template_name = 'barbers/work_schedule_list.html'
    context_object_name = 'schedules'
    permission_required = 'barbers.view_workschedule'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset().select_related('barber', 'barber__user')
        queryset = queryset.filter(is_active=True)
        
        barber = self.request.GET.get('barber')
        if barber:
            queryset = queryset.filter(barber_id=barber)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['barbers'] = Barber.objects.filter(is_active=True)
        context['weekdays'] = WorkSchedule.WeekDay.choices
        return context


class WorkScheduleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = WorkSchedule
    form_class = WorkScheduleForm
    template_name = 'barbers/work_schedule_form.html'
    permission_required = 'barbers.add_workschedule'
    success_url = reverse_lazy('barbers:schedule_list')

    def form_valid(self, form):
        messages.success(self.request, _('Horário criado com sucesso!'))
        return super().form_valid(form)


class WorkScheduleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = WorkSchedule
    form_class = WorkScheduleForm
    template_name = 'barbers/work_schedule_form.html'
    permission_required = 'barbers.change_workschedule'
    success_url = reverse_lazy('barbers:schedule_list')

    def form_valid(self, form):
        messages.success(self.request, _('Horário atualizado com sucesso!'))
        return super().form_valid(form)


class WorkScheduleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = WorkSchedule
    template_name = 'barbers/work_schedule_confirm_delete.html'
    permission_required = 'barbers.delete_workschedule'
    success_url = reverse_lazy('barbers:schedule_list')

    def delete(self, request, *args, **kwargs):
        schedule = self.get_object()
        schedule.is_active = False
        schedule.save()
        messages.success(request, _('Horário removido com sucesso!'))
        return redirect(self.success_url)


class WorkScheduleDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard de configuração de horários."""
    template_name = 'barbers/work_schedule_dashboard.html'
    permission_required = 'barbers.view_workschedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['barbers'] = Barber.objects.filter(is_active=True)
        
        # Buscar todos os horários
        all_schedules = WorkSchedule.objects.filter(is_active=True).select_related('barber')
        
        # Organizar por barbeiro
        barber_schedules = {}
        for barber in context['barbers']:
            barber_schedules[barber.id] = {
                'barber': barber,
                'schedules': all_schedules.filter(barber=barber).order_by('day_of_week')
            }
        
        context['barber_schedules'] = barber_schedules
        context['weekdays'] = WorkSchedule.WeekDay.choices
        
        return context

class WorkScheduleDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard de configuração de horários."""
    template_name = 'barbers/work_schedule_dashboard.html'
    permission_required = 'barbers.view_workschedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['barbers'] = Barber.objects.filter(is_active=True)
        
        all_schedules = WorkSchedule.objects.filter(is_active=True).select_related('barber')
        
        barber_schedules = {}
        for barber in context['barbers']:
            barber_schedules[barber.id] = {
                'barber': barber,
                'schedules': all_schedules.filter(barber=barber).order_by('day_of_week')
            }
        
        context['barber_schedules'] = barber_schedules
        context['weekdays'] = WorkSchedule.WeekDay.choices
        
        return context

class WorkScheduleDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard de configuração de horários."""
    template_name = 'barbers/work_schedule_dashboard.html'
    permission_required = 'barbers.view_workschedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['barbers'] = Barber.objects.filter(is_active=True)
        
        all_schedules = WorkSchedule.objects.filter(is_active=True).select_related('barber')
        
        # Estatísticas
        context['total_schedules'] = all_schedules.count()
        context['total_available'] = all_schedules.filter(is_available=True).count()
        context['total_unavailable'] = all_schedules.filter(is_available=False).count()
        
        # Organizar por barbeiro
        barber_schedules = {}
        for barber in context['barbers']:
            barber_schedules[barber.id] = {
                'barber': barber,
                'schedules': all_schedules.filter(barber=barber).order_by('day_of_week')
            }
        
        context['barber_schedules'] = barber_schedules
        context['weekdays'] = WorkSchedule.WeekDay.choices
        
        return context
