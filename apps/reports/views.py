"""
Views para o app Reports.
"""

from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import datetime, timedelta
from decimal import Decimal
import json

from apps.finance.models import Transaction, Commission
from apps.appointments.models import Appointment
from apps.customers.models import Customer
from apps.barbers.models import Barber
from apps.products.models import Product, InventoryMovement
from apps.subscriptions.models import Subscription


class ReportDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/dashboard.html'
    permission_required = 'reports.view_reporttemplate'


class FinancialReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Relatório Financeiro completo com gráficos."""
    template_name = 'reports/financial.html'
    permission_required = 'reports.view_reporttemplate'

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
        
        transactions = Transaction.objects.filter(
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
        total_income = transactions.filter(
            transaction_type=Transaction.TransactionType.INCOME
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_expense = transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_commission = transactions.filter(
            transaction_type=Transaction.TransactionType.COMMISSION
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        net_profit = total_income - total_expense - total_commission
        
        context['total_income'] = total_income
        context['total_expense'] = total_expense
        context['total_commission'] = total_commission
        context['net_profit'] = net_profit
        
        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            daily_total = transactions.filter(
                transaction_date__date=current_date,
                transaction_type=Transaction.TransactionType.INCOME
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            daily_data.append({
                'date': current_date.strftime('%d/%m'),
                'total': float(daily_total)
            })
            current_date += timedelta(days=1)
        
        if not daily_data:
            daily_data.append({'date': 'Sem dados', 'total': 0})
        
        context['daily_data'] = json.dumps(daily_data)
        
        income_by_day = []
        expense_by_day = []
        dates = []
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%d/%m'))
            income_total = transactions.filter(
                transaction_date__date=current_date,
                transaction_type=Transaction.TransactionType.INCOME
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            expense_total = transactions.filter(
                transaction_date__date=current_date,
                transaction_type=Transaction.TransactionType.EXPENSE
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            income_by_day.append(float(income_total))
            expense_by_day.append(float(expense_total))
            current_date += timedelta(days=1)
        
        if not dates:
            dates = ['Sem dados']
            income_by_day = [0]
            expense_by_day = [0]
        
        context['dates'] = json.dumps(dates)
        context['income_by_day'] = json.dumps(income_by_day)
        context['expense_by_day'] = json.dumps(expense_by_day)
        
        payment_methods = transactions.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        payment_labels = []
        payment_data = []
        
        if payment_methods:
            for idx, method in enumerate(payment_methods):
                payment_labels.append(dict(Transaction.PaymentMethod.choices).get(method['payment_method'], method['payment_method']))
                payment_data.append(float(method['total']))
        else:
            payment_labels = ['Nenhuma transação']
            payment_data = [0]
        
        context['payment_labels'] = json.dumps(payment_labels)
        context['payment_data'] = json.dumps(payment_data)
        
        context['recent_transactions'] = transactions.order_by('-transaction_date')[:10]
        context['transaction_types'] = transactions.values('transaction_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        period_days = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=period_days)
        prev_end = end_date - timedelta(days=period_days)
        
        prev_income = Transaction.objects.filter(
            transaction_date__date__gte=prev_start,
            transaction_date__date__lte=prev_end,
            transaction_type=Transaction.TransactionType.INCOME
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context['prev_income'] = prev_income
        
        if prev_income > 0:
            growth = ((total_income - prev_income) / prev_income) * 100
        else:
            growth = 100 if total_income > 0 else 0
        
        context['growth_percentage'] = round(float(growth), 2)
        
        return context


class BarbersReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Relatório completo de barbeiros."""
    template_name = 'reports/barbers.html'
    permission_required = 'reports.view_reporttemplate'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        period = self.request.GET.get('period', 'month')
        today = timezone.now().date()
        
        if period == 'today':
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
        
        barbers = Barber.objects.filter(is_active=True)
        
        barber_data = []
        total_services = 0
        total_revenue = Decimal('0.00')
        total_commission = Decimal('0.00')
        total_profit = Decimal('0.00')
        
        for barber in barbers:
            appointments = Appointment.objects.filter(
                barber=barber,
                start_time__date__gte=start_date,
                start_time__date__lte=end_date
            )
            
            completed = appointments.filter(
                status=Appointment.AppointmentStatus.COMPLETED
            )
            
            total_services_barber = completed.count()
            revenue = completed.aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
            commission = completed.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00')
            profit = revenue - commission
            
            ratings = completed.filter(rating__isnull=False)
            avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
            
            scheduled = appointments.filter(status=Appointment.AppointmentStatus.SCHEDULED).count()
            confirmed = appointments.filter(status=Appointment.AppointmentStatus.CONFIRMED).count()
            in_progress = appointments.filter(status=Appointment.AppointmentStatus.IN_PROGRESS).count()
            cancelled = appointments.filter(status=Appointment.AppointmentStatus.CANCELLED).count()
            no_show = appointments.filter(status=Appointment.AppointmentStatus.NO_SHOW).count()
            
            avg_ticket = revenue / total_services_barber if total_services_barber > 0 else 0
            
            commissions_paid = Commission.objects.filter(
                barber=barber,
                status=Commission.CommissionStatus.PAID,
                paid_at__date__gte=start_date,
                paid_at__date__lte=end_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            barber_data.append({
                'barber': barber,
                'total_services': total_services_barber,
                'revenue': revenue,
                'commission': commission,
                'profit': profit,
                'avg_ticket': avg_ticket,
                'avg_rating': avg_rating,
                'commissions_paid': commissions_paid,
                'scheduled': scheduled,
                'confirmed': confirmed,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'no_show': no_show,
                'total_appointments': appointments.count(),
                'utilization_rate': (total_services_barber / max(appointments.count(), 1)) * 100 if appointments.count() > 0 else 0,
            })
            
            total_services += total_services_barber
            total_revenue += revenue
            total_commission += commission
            total_profit += profit
        
        barber_data.sort(key=lambda x: x['profit'], reverse=True)
        
        context['barber_data'] = barber_data
        context['total_services'] = total_services
        context['total_revenue'] = total_revenue
        context['total_commission'] = total_commission
        context['total_profit'] = total_profit
        context['total_barbers'] = len(barber_data)
        
        profit_labels = [data['barber'].full_name for data in barber_data]
        profit_data = [float(data['profit']) for data in barber_data]
        context['profit_labels'] = json.dumps(profit_labels)
        context['profit_data'] = json.dumps(profit_data)
        
        services_labels = [data['barber'].full_name for data in barber_data]
        services_data = [data['total_services'] for data in barber_data]
        context['services_labels'] = json.dumps(services_labels)
        context['services_data'] = json.dumps(services_data)
        
        rating_labels = [data['barber'].full_name for data in barber_data]
        rating_data = [float(data['avg_rating']) for data in barber_data]
        context['rating_labels'] = json.dumps(rating_labels)
        context['rating_data'] = json.dumps(rating_data)
        
        return context


class AppointmentsReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/appointments.html'
    permission_required = 'reports.view_reporttemplate'


class CustomersReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/customers.html'
    permission_required = 'reports.view_reporttemplate'


class ProductsReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/products.html'
    permission_required = 'reports.view_reporttemplate'


class SubscriptionsReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/subscriptions.html'
    permission_required = 'reports.view_reporttemplate'
