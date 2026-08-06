"""
Views para o app Finance.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Transaction, CashRegister, Commission
from .forms import TransactionForm, CashRegisterForm


class FinanceDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard financeiro com filtros por período."""
    template_name = 'finance/dashboard.html'
    permission_required = 'finance.view_transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obter período da URL
        period = self.request.GET.get('period', 'month')
        today = timezone.now().date()
        
        # Definir datas de início e fim
        if period == 'day':
            start_date = today
            end_date = today
            period_label = 'Hoje'
        elif period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            period_label = 'Esta Semana'
        elif period == 'month':
            start_date = today.replace(day=1)
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
            period_label = 'Este Mês'
        else:  # custom
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')
            if start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                start_date = today.replace(day=1)
                next_month = start_date.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)
            period_label = f'{start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}'
        
        context['period'] = period
        context['period_label'] = period_label
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # Buscar transações no período
        transactions = Transaction.objects.filter(
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        # Totais
        total_income = transactions.filter(
            transaction_type=Transaction.TransactionType.INCOME
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_expense = transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_commission = transactions.filter(
            transaction_type=Transaction.TransactionType.COMMISSION
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        net_profit = total_income - total_expense - total_commission
        
        context['total_income'] = total_income
        context['total_expense'] = total_expense
        context['total_commission'] = total_commission
        context['net_profit'] = net_profit
        
        # Últimas transações
        context['recent_transactions'] = transactions.order_by('-transaction_date')[:10]
        
        # Transações por dia (para gráfico)
        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            daily_total = transactions.filter(
                transaction_date__date=current_date,
                transaction_type=Transaction.TransactionType.INCOME
            ).aggregate(total=Sum('amount'))['total'] or 0
            daily_data.append({
                'date': current_date.strftime('%d/%m'),
                'total': float(daily_total)
            })
            current_date += timedelta(days=1)
        
        context['daily_data'] = daily_data
        
        # Transações por forma de pagamento
        payment_methods = transactions.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        context['payment_methods'] = payment_methods
        
        # Transações por categoria (tipo)
        transaction_types = transactions.values('transaction_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        context['transaction_types'] = transaction_types
        
        return context


class TransactionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de transações com filtros."""
    model = Transaction
    template_name = 'finance/transaction_list.html'
    context_object_name = 'transactions'
    permission_required = 'finance.view_transaction'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('customer', 'barber', 'appointment')
        
        # Filtros
        transaction_type = self.request.GET.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        start_date = self.request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(transaction_date__date__gte=start_date)
        
        end_date = self.request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(transaction_date__date__lte=end_date)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(customer__full_name__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or 0
        context['transaction_types'] = Transaction.TransactionType.choices
        context['payment_methods'] = Transaction.PaymentMethod.choices
        return context


class TransactionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Cria uma nova transação."""
    model = Transaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    permission_required = 'finance.add_transaction'
    success_url = reverse_lazy('finance:transactions')

    def form_valid(self, form):
        messages.success(self.request, _('Transação criada com sucesso!'))
        return super().form_valid(form)


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
