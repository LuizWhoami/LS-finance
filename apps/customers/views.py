"""
Views para o app Customers.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.db import transaction
from django.shortcuts import redirect

from .models import Customer, CustomerHistory
from .forms import CustomerForm, CustomerHistoryForm


class CustomerListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    permission_required = 'customers.view_customer'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'preferred_barber')
        queryset = queryset.filter(is_active=True)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(cpf__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Customer.CustomerStatus.choices
        return context


class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    permission_required = 'customers.add_customer'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        messages.success(self.request, _('Cliente criado com sucesso!'))
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    permission_required = 'customers.change_customer'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        messages.success(self.request, _('Cliente atualizado com sucesso!'))
        return super().form_valid(form)


class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    permission_required = 'customers.delete_customer'
    success_url = reverse_lazy('customers:list')

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        customer = self.get_object()
        
        # Verificar se tem agendamentos
        from apps.appointments.models import Appointment
        appointments = Appointment.objects.filter(customer=customer)
        
        if appointments.exists():
            # Desvincular agendamentos
            appointments.update(customer=None)
            messages.warning(request, f'Cliente tinha {appointments.count()} agendamentos que foram desvinculados.')
        
        # Soft delete - apenas desativar
        customer.is_active = False
        customer.status = Customer.CustomerStatus.INACTIVE
        customer.save(update_fields=['is_active', 'status', 'updated_at'])
        
        messages.success(request, _('Cliente desativado com sucesso!'))
        return redirect(self.success_url)


class CustomerDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'
    permission_required = 'customers.view_customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.history.all()[:10]
        context['appointments'] = self.object.appointments.filter(is_active=True)[:10]
        return context


class CustomerHistoryView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CustomerHistory
    template_name = 'customers/customer_history.html'
    context_object_name = 'history'
    permission_required = 'customers.view_customer'
    paginate_by = 30

    def get_queryset(self):
        customer_id = self.kwargs.get('customer_id')
        return CustomerHistory.objects.filter(
            customer_id=customer_id
        ).select_related('customer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = Customer.objects.get(pk=self.kwargs.get('customer_id'))
        return context
