"""
Views para o app Finance.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect

from .models import Transaction, CashRegister, Commission
from .forms import TransactionForm, CashRegisterForm


class FinanceDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard financeiro."""
    template_name = 'finance/dashboard.html'
    permission_required = 'finance.view_transaction'


class TransactionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de transações."""
    model = Transaction
    template_name = 'finance/transaction_list.html'
    context_object_name = 'transactions'
    permission_required = 'finance.view_transaction'
    paginate_by = 20


class TransactionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Cria uma nova transação."""
    model = Transaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    permission_required = 'finance.add_transaction'
    success_url = reverse_lazy('finance:transactions')


class CashRegisterView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de caixas."""
    model = CashRegister
    template_name = 'finance/cash_register.html'
    context_object_name = 'registers'
    permission_required = 'finance.view_cashregister'
    paginate_by = 20


class CashRegisterOpenView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Abre um caixa."""
    model = CashRegister
    form_class = CashRegisterForm
    template_name = 'finance/cash_register_open.html'
    permission_required = 'finance.add_cashregister'
    success_url = reverse_lazy('finance:cash_register')


class CashRegisterCloseView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Fecha um caixa."""
    model = CashRegister
    template_name = 'finance/cash_register_close.html'
    permission_required = 'finance.change_cashregister'

    def post(self, request, *args, **kwargs):
        register = self.get_object()
        try:
            register.close(request.user)
            messages.success(request, _('Caixa fechado com sucesso!'))
        except Exception as e:
            messages.error(request, str(e))
        return redirect('finance:cash_register')


class CommissionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de comissões."""
    model = Commission
    template_name = 'finance/commission_list.html'
    context_object_name = 'commissions'
    permission_required = 'finance.view_commission'
    paginate_by = 20
