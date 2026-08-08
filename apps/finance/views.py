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
from decimal import Decimal
import json
from django.db import models

from .models import Transaction, CashRegister, Commission, FixedExpense
from .forms import TransactionForm, CashRegisterForm, FixedExpenseForm
from apps.appointments.models import Appointment
from apps.subscriptions.models import Subscription, Plan
from apps.products.models import Product, InventoryMovement


class FinanceDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard financeiro completo com todas as métricas."""
    template_name = 'finance/dashboard.html'
    permission_required = 'finance.view_transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        period = self.request.GET.get('period', 'month')
        today = timezone.now().date()
        
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
        else:
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')
            if start_date and end_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                except ValueError:
                    start_date = today.replace(day=1)
                    next_month = start_date.replace(day=28) + timedelta(days=4)
                    end_date = next_month - timedelta(days=next_month.day)
            else:
                start_date = today.replace(day=1)
                next_month = start_date.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)
            period_label = f'{start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}'
        
        context['period'] = period
        context['period_label'] = period_label
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # ============================================================
        # 1. MÉTRICAS DE AGENDAMENTOS (APENAS NÃO CANCELADOS)
        # ============================================================
        appointments = Appointment.objects.filter(
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
            is_active=True
        ).exclude(
            status=Appointment.AppointmentStatus.CANCELLED
        )
        
        total_appointments = appointments.count()
        completed_appointments = appointments.filter(
            status=Appointment.AppointmentStatus.COMPLETED
        )
        completed_count = completed_appointments.count()
        
        revenue_appointments = completed_appointments.aggregate(
            total=Sum('final_price')
        )['total'] or Decimal('0.00')
        
        commission_appointments = completed_appointments.aggregate(
            total=Sum('commission_amount')
        )['total'] or Decimal('0.00')
        
        profit_appointments = revenue_appointments - commission_appointments
        
        context['total_appointments'] = total_appointments
        context['completed_appointments'] = completed_count
        context['revenue_appointments'] = revenue_appointments
        context['commission_appointments'] = commission_appointments
        context['profit_appointments'] = profit_appointments
        
        # ============================================================
        # 2. MÉTRICAS DE ASSINATURAS
        # ============================================================
        subscriptions = Subscription.objects.filter(
            is_active=True,
            status=Subscription.SubscriptionStatus.ACTIVE
        )
        
        new_subscriptions = subscriptions.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).count()
        
        active_subscriptions = subscriptions.count()
        
        revenue_subscriptions = Transaction.objects.filter(
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date,
            is_active=True,
            description__icontains='Assinatura'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        plans = Plan.objects.filter(status='active', is_active=True)
        
        context['total_subscriptions'] = new_subscriptions
        context['active_subscriptions'] = active_subscriptions
        context['revenue_subscriptions'] = revenue_subscriptions
        context['plans'] = plans
        
        # ============================================================
        # 3. MÉTRICAS DE PRODUTOS (NOVO)
        # ============================================================
        # Produtos em estoque
        products = Product.objects.filter(is_active=True)
        total_products = products.count()
        
        # Produtos com estoque baixo
        low_stock_products = products.filter(
            quantity__lte=models.F('minimum_stock')
        ).count()
        
        # Movimentações de estoque no período
        movements = InventoryMovement.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Entradas e saídas
        total_in = movements.filter(
            movement_type=InventoryMovement.MovementType.IN
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        total_out = movements.filter(
            movement_type=InventoryMovement.MovementType.OUT
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Receita de produtos (vendas)
        revenue_products = Transaction.objects.filter(
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date,
            is_active=True,
            description__icontains='Produto'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Custo dos produtos vendidos (estimado)
        # Buscar produtos que foram vendidos no período
        product_transactions = Transaction.objects.filter(
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date,
            is_active=True,
            description__icontains='Produto'
        )
        
        # Calcular custo total baseado nas movimentações de saída
        total_cost = Decimal('0.00')
        for transaction in product_transactions:
            # Buscar produtos relacionados à transação (via description ou referência)
            product_name = transaction.description.replace('Venda de Produto: ', '').strip()
            product = Product.objects.filter(name__icontains=product_name).first()
            if product:
                # Estimar o custo como 60% do preço de venda (exemplo)
                # Ou usar o cost_price do produto
                total_cost += product.cost_price or (transaction.amount * Decimal('0.6'))
        
        # Lucro de produtos
        profit_products = revenue_products - total_cost
        
        context['total_products'] = total_products
        context['low_stock_products'] = low_stock_products
        context['total_in'] = total_in
        context['total_out'] = total_out
        context['revenue_products'] = revenue_products
        context['cost_products'] = total_cost
        context['profit_products'] = profit_products
        
        # ============================================================
        # 4. MÉTRICAS FINANCEIRAS (EXCLUINDO AGENDAMENTOS, ASSINATURAS E PRODUTOS)
        # ============================================================
        transactions = Transaction.objects.filter(
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date,
            is_active=True
        )
        
        # Receitas de transações (excluindo agendamentos, assinaturas e produtos)
        total_income = transactions.filter(
            transaction_type=Transaction.TransactionType.INCOME,
            is_active=True
        ).exclude(
            Q(description__icontains='Serviço') |
            Q(description__icontains='Assinatura') |
            Q(description__icontains='Produto')
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Despesas
        total_expense = transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE,
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Comissões
        total_commission = transactions.filter(
            transaction_type=Transaction.TransactionType.COMMISSION,
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        net_profit = total_income - total_expense - total_commission
        
        context['total_income'] = total_income
        context['total_expense'] = total_expense
        context['total_commission'] = total_commission
        context['net_profit'] = net_profit
        
        # ============================================================
        # 5. GASTOS FIXOS
        # ============================================================
        fixed_expenses_total = FixedExpense.objects.filter(
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context['fixed_expenses_total'] = fixed_expenses_total
        context['fixed_expenses_count'] = FixedExpense.objects.filter(is_active=True).count()
        
        # ============================================================
        # 6. RESULTADO TOTAL (SEM DUPLICIDADE)
        # ============================================================
        # RECEITA TOTAL = Agendamentos + Assinaturas + Produtos + Outras Receitas
        total_revenue = revenue_appointments + revenue_subscriptions + revenue_products + total_income
        
        # LUCRO TOTAL = Lucro dos Agendamentos + Assinaturas + Lucro dos Produtos + Lucro de Outras Receitas
        total_profit = profit_appointments + revenue_subscriptions + profit_products + net_profit
        
        context['total_revenue'] = total_revenue
        context['total_profit'] = total_profit
        
        # ============================================================
        # 7. MÉTRICAS ADICIONAIS
        # ============================================================
        total_income_aux = total_income + revenue_appointments + revenue_subscriptions + revenue_products
        if total_income_aux > 0:
            context['revenue_percent_appointments'] = float((revenue_appointments / total_income_aux) * 100)
            context['revenue_percent_subscriptions'] = float((revenue_subscriptions / total_income_aux) * 100)
            context['revenue_percent_products'] = float((revenue_products / total_income_aux) * 100)
            context['revenue_percent_other'] = float((total_income / total_income_aux) * 100)
        else:
            context['revenue_percent_appointments'] = 0
            context['revenue_percent_subscriptions'] = 0
            context['revenue_percent_products'] = 0
            context['revenue_percent_other'] = 0
        
        if completed_count > 0:
            context['avg_ticket'] = revenue_appointments / completed_count
        else:
            context['avg_ticket'] = 0
        
        if total_revenue > 0:
            context['profit_margin'] = float((total_profit / total_revenue) * 100)
        else:
            context['profit_margin'] = 0
        
        context['other_expenses'] = total_expense - fixed_expenses_total
        context['other_income'] = total_income - revenue_appointments - revenue_subscriptions - revenue_products
        
        from apps.customers.models import Customer
        context['active_customers'] = Customer.objects.filter(
            is_active=True,
            last_visit__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # ============================================================
        # 8. DADOS PARA GRÁFICOS
        # ============================================================
        source_data = []
        if revenue_appointments > 0:
            source_data.append({'label': 'Agendamentos', 'value': float(revenue_appointments)})
        if revenue_subscriptions > 0:
            source_data.append({'label': 'Assinaturas', 'value': float(revenue_subscriptions)})
        if revenue_products > 0:
            source_data.append({'label': 'Produtos', 'value': float(revenue_products)})
        if total_income > 0:
            source_data.append({'label': 'Outras Receitas', 'value': float(total_income)})
        
        if not source_data:
            source_data = [{'label': 'Sem dados', 'value': 1}]
        
        context['revenue_sources'] = json.dumps(source_data)
        
        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            # Outras receitas (excluindo agendamentos, assinaturas e produtos)
            day_income = transactions.filter(
                transaction_date__date=current_date,
                transaction_type=Transaction.TransactionType.INCOME,
                is_active=True
            ).exclude(
                Q(description__icontains='Serviço') |
                Q(description__icontains='Assinatura') |
                Q(description__icontains='Produto')
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Receita de agendamentos
            day_appointments = Appointment.objects.filter(
                start_time__date=current_date,
                status=Appointment.AppointmentStatus.COMPLETED,
                is_active=True
            ).exclude(
                status=Appointment.AppointmentStatus.CANCELLED
            ).aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
            
            # Receita de assinaturas
            day_subscriptions = transactions.filter(
                transaction_date__date=current_date,
                transaction_type=Transaction.TransactionType.INCOME,
                is_active=True,
                description__icontains='Assinatura'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Receita de produtos
            day_products = transactions.filter(
                transaction_date__date=current_date,
                transaction_type=Transaction.TransactionType.INCOME,
                is_active=True,
                description__icontains='Produto'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            total_day = day_income + day_appointments + day_subscriptions + day_products
            daily_data.append({
                'date': current_date.strftime('%d/%m'),
                'income': float(day_income),
                'appointments': float(day_appointments),
                'subscriptions': float(day_subscriptions),
                'products': float(day_products),
                'total': float(total_day)
            })
            current_date += timedelta(days=1)
        
        context['daily_data'] = json.dumps(daily_data)
        context['recent_transactions'] = transactions.filter(is_active=True).order_by('-transaction_date')[:10]
        context['fixed_expenses'] = FixedExpense.objects.filter(is_active=True)[:5]
        
        return context


class TransactionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Transaction
    template_name = 'finance/transaction_list.html'
    context_object_name = 'transactions'
    permission_required = 'finance.view_transaction'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('customer', 'barber', 'appointment')
        queryset = queryset.filter(is_active=True)
        
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
    model = Transaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    permission_required = 'finance.add_transaction'
    success_url = reverse_lazy('finance:transactions')

    def form_valid(self, form):
        messages.success(self.request, _('Transação criada com sucesso!'))
        return super().form_valid(form)


class TransactionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Transaction
    template_name = 'finance/transaction_detail.html'
    context_object_name = 'transaction'
    permission_required = 'finance.view_transaction'


class TransactionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    permission_required = 'finance.change_transaction'
    success_url = reverse_lazy('finance:transactions')

    def form_valid(self, form):
        messages.success(self.request, _('Transação atualizada com sucesso!'))
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'finance/transaction_confirm_delete.html'
    permission_required = 'finance.delete_transaction'
    success_url = reverse_lazy('finance:transactions')

    def delete(self, request, *args, **kwargs):
        transaction = self.get_object()
        transaction.is_active = False
        transaction.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, _('Transação removida com sucesso!'))
        return redirect(self.success_url)


class CashRegisterView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CashRegister
    template_name = 'finance/cash_register.html'
    context_object_name = 'registers'
    permission_required = 'finance.view_cashregister'
    paginate_by = 20


class CashRegisterOpenView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = CashRegister
    form_class = CashRegisterForm
    template_name = 'finance/cash_register_open.html'
    permission_required = 'finance.add_cashregister'
    success_url = reverse_lazy('finance:cash_register')


class CashRegisterCloseView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
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
    model = Commission
    template_name = 'finance/commission_list.html'
    context_object_name = 'commissions'
    permission_required = 'finance.view_commission'
    paginate_by = 20


class FixedExpenseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = FixedExpense
    template_name = 'finance/fixed_expense_list.html'
    context_object_name = 'expenses'
    permission_required = 'finance.view_fixedexpense'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True)
        
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = FixedExpense.ExpenseCategory.choices
        context['total_expenses'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        context['total_count'] = self.get_queryset().count()
        
        expenses_by_category = self.get_queryset().values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        for item in expenses_by_category:
            item['category_name'] = dict(FixedExpense.ExpenseCategory.choices).get(item['category'], item['category'])
        
        context['expenses_by_category'] = expenses_by_category
        
        return context


class FixedExpenseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FixedExpense
    form_class = FixedExpenseForm
    template_name = 'finance/fixed_expense_form.html'
    permission_required = 'finance.add_fixedexpense'
    success_url = reverse_lazy('finance:fixed_expenses')

    def form_valid(self, form):
        expense = form.save(commit=False)
        expense.next_charge = expense.calculate_next_charge()
        expense.save()
        messages.success(self.request, _('Gasto fixo criado com sucesso!'))
        return super().form_valid(form)


class FixedExpenseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FixedExpense
    form_class = FixedExpenseForm
    template_name = 'finance/fixed_expense_form.html'
    permission_required = 'finance.change_fixedexpense'
    success_url = reverse_lazy('finance:fixed_expenses')

    def form_valid(self, form):
        expense = form.save(commit=False)
        expense.next_charge = expense.calculate_next_charge()
        expense.save()
        messages.success(self.request, _('Gasto fixo atualizado com sucesso!'))
        return super().form_valid(form)


class FixedExpenseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = FixedExpense
    template_name = 'finance/fixed_expense_confirm_delete.html'
    permission_required = 'finance.delete_fixedexpense'
    success_url = reverse_lazy('finance:fixed_expenses')

    def delete(self, request, *args, **kwargs):
        expense = self.get_object()
        expense.is_active = False
        expense.save()
        messages.success(request, _('Gasto fixo removido com sucesso!'))
        return redirect(self.success_url)


class FixedExpenseChargeView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = FixedExpense
    template_name = 'finance/fixed_expense_charge.html'
    permission_required = 'finance.change_fixedexpense'

    def post(self, request, *args, **kwargs):
        expense = self.get_object()
        try:
            transaction = expense.charge()
            messages.success(request, f'Gasto fixo cobrado com sucesso! Transação #{transaction.id}')
        except Exception as e:
            messages.error(request, f'Erro ao cobrar: {str(e)}')
        return redirect('finance:fixed_expenses')


class BarberProfitReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Relatório de lucro por barbeiro."""
    template_name = 'finance/barber_profit.html'
    permission_required = 'finance.view_transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        period = self.request.GET.get('period', 'month')
        today = timezone.now().date()
        
        if period == 'month':
            start_date = today.replace(day=1)
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
            period_label = 'Este Mês'
        elif period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            period_label = 'Esta Semana'
        else:
            start_date = today
            end_date = today
            period_label = 'Hoje'
        
        context['period'] = period
        context['period_label'] = period_label
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        from apps.barbers.models import Barber
        barbers = Barber.objects.filter(is_active=True)
        
        barber_data = []
        total_profit = Decimal('0.00')
        
        for barber in barbers:
            appointments = Appointment.objects.filter(
                barber=barber,
                status=Appointment.AppointmentStatus.COMPLETED,
                start_time__date__gte=start_date,
                start_time__date__lte=end_date,
                is_active=True
            ).exclude(
                status=Appointment.AppointmentStatus.CANCELLED
            )
            
            total_services = appointments.count()
            total_revenue = appointments.aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
            total_commission = appointments.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00')
            
            commissions_paid = Commission.objects.filter(
                barber=barber,
                status=Commission.CommissionStatus.PAID,
                paid_at__date__gte=start_date,
                paid_at__date__lte=end_date,
                is_active=True
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            profit = total_revenue - total_commission
            
            work_days = 22 if period == 'month' else 5 if period == 'week' else 1
            total_hours = work_days * 8
            utilized_hours = total_services * 0.5
            utilization = (utilized_hours / total_hours) * 100 if total_hours > 0 else 0
            
            barber_data.append({
                'barber': barber,
                'total_services': total_services,
                'total_revenue': total_revenue,
                'total_commission': total_commission,
                'commissions_paid': commissions_paid,
                'profit': profit,
                'avg_ticket': total_revenue / total_services if total_services > 0 else 0,
                'utilization': min(utilization, 100),
            })
            
            total_profit += profit
        
        barber_data.sort(key=lambda x: x['profit'], reverse=True)
        
        context['barber_data'] = barber_data
        context['total_profit'] = total_profit
        context['avg_profit'] = total_profit / len(barber_data) if barber_data else 0
        
        return context

class ProductSaleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """View para registrar venda de produto."""
    model = Transaction
    form_class = TransactionForm
    template_name = 'finance/product_sale_form.html'
    permission_required = 'finance.add_transaction'
    success_url = reverse_lazy('finance:dashboard')

    def form_valid(self, form):
        transaction = form.save(commit=False)
        transaction.transaction_type = Transaction.TransactionType.INCOME
        transaction.description = f'Venda de Produto: {form.cleaned_data.get("description")}'
        transaction.save()
        messages.success(self.request, _('Venda de produto registrada com sucesso!'))
        return super().form_valid(form)
