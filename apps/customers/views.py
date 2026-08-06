"""
Views para o app Customers.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Customer, CustomerHistory
from .forms import CustomerForm, CustomerHistoryForm


class CustomerListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de clientes."""
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    permission_required = 'customers.view_customer'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'preferred_barber')
        
        # Busca
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(cpf__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        has_user = self.request.GET.get('has_user')
        if has_user == 'yes':
            queryset = queryset.filter(user__isnull=False)
        elif has_user == 'no':
            queryset = queryset.filter(user__isnull=True)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Customer.CustomerStatus.choices
        return context


class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Cria um novo cliente."""
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    permission_required = 'customers.add_customer'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        messages.success(self.request, _('Cliente criado com sucesso!'))
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edita um cliente."""
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    permission_required = 'customers.change_customer'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        messages.success(self.request, _('Cliente atualizado com sucesso!'))
        return super().form_valid(form)


class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Remove um cliente."""
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    permission_required = 'customers.delete_customer'
    success_url = reverse_lazy('customers:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Cliente removido com sucesso!'))
        return super().delete(request, *args, **kwargs)


class CustomerDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detalhes de um cliente."""
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'
    permission_required = 'customers.view_customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Buscar histórico do cliente
        context['history'] = self.object.history.all()[:10]
        # Buscar agendamentos do cliente
        context['appointments'] = self.object.appointments.all()[:10]
        return context


class CustomerHistoryView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Histórico de atividades do cliente."""
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
