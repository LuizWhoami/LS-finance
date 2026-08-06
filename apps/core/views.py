"""
Views para o app Core.
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.appointments.models import Appointment
from apps.customers.models import Customer
from apps.barbers.models import Barber
from apps.services.models import Service
from apps.products.models import Product


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin para verificar se o usuário é admin/staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        from django.shortcuts import redirect
        return redirect('client:home')


class HomeView(AdminRequiredMixin, TemplateView):
    """Dashboard principal para administradores."""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        
        # Métricas do Dia
        context['appointments_today'] = Appointment.objects.filter(
            start_time__date=today
        ).count()
        
        context['appointments_completed_today'] = Appointment.objects.filter(
            start_time__date=today,
            status=Appointment.AppointmentStatus.COMPLETED
        ).count()
        
        context['revenue_today'] = Appointment.objects.filter(
            start_time__date=today,
            status=Appointment.AppointmentStatus.COMPLETED
        ).aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
        
        # Métricas do Mês
        context['revenue_month'] = Appointment.objects.filter(
            start_time__date__gte=start_of_month,
            start_time__date__lte=end_of_month,
            status=Appointment.AppointmentStatus.COMPLETED
        ).aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
        
        context['appointments_month'] = Appointment.objects.filter(
            start_time__date__gte=start_of_month,
            start_time__date__lte=end_of_month
        ).count()
        
        # Métricas Gerais
        context['total_customers'] = Customer.objects.filter(is_active=True).count()
        context['active_customers'] = Customer.objects.filter(
            is_active=True,
            last_visit__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        context['total_barbers'] = Barber.objects.filter(is_active=True, status='active').count()
        context['total_services'] = Service.objects.filter(is_active=True, status='active').count()
        
        # Serviços Mais Vendidos
        top_services = Appointment.objects.filter(
            status=Appointment.AppointmentStatus.COMPLETED,
            start_time__date__gte=start_of_month
        ).values('service__name').annotate(
            total=Count('id'),
            revenue=Sum('final_price')
        ).order_by('-total')[:5]
        
        context['top_services'] = top_services
        
        # Gráfico: Faturamento Diário
        daily_revenue = []
        for i in range(30):
            date = today - timedelta(days=i)
            daily_total = Appointment.objects.filter(
                start_time__date=date,
                status=Appointment.AppointmentStatus.COMPLETED
            ).aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
            daily_revenue.append({
                'date': date.strftime('%d/%m'),
                'total': float(daily_total)
            })
        
        context['daily_revenue'] = list(reversed(daily_revenue))
        
        # Gráfico: Agendamentos por Dia da Semana
        weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        weekday_counts = []
        
        for i in range(7):
            day_start = start_of_week + timedelta(days=i)
            count = Appointment.objects.filter(
                start_time__date=day_start
            ).count()
            weekday_counts.append(count)
        
        context['weekday_labels'] = weekdays
        context['weekday_counts'] = weekday_counts
        
        # Gráfico: Distribuição de Status
        status_counts = {}
        for status in Appointment.AppointmentStatus.choices:
            status_counts[status[1]] = Appointment.objects.filter(
                status=status[0]
            ).count()
        
        context['status_counts'] = status_counts
        
        # Próximos Agendamentos
        context['upcoming_appointments'] = Appointment.objects.filter(
            start_time__gte=timezone.now(),
            status__in=[
                Appointment.AppointmentStatus.SCHEDULED,
                Appointment.AppointmentStatus.CONFIRMED
            ]
        ).select_related('customer', 'barber', 'service').order_by('start_time')[:5]
        
        # Alertas
        alerts = []
        
        low_stock_products = Product.objects.filter(
            is_active=True,
            quantity__lte=models.F('minimum_stock')
        )[:5]
        
        for product in low_stock_products:
            alerts.append({
                'type': 'warning',
                'message': f'Estoque baixo: {product.name} (atual: {product.quantity})'
            })
        
        birthday_customers = Customer.objects.filter(
            is_active=True,
            birth_date__month=today.month
        )[:5]
        
        for customer in birthday_customers:
            alerts.append({
                'type': 'info',
                'message': f'Aniversariante: {customer.full_name} - {customer.birth_date.strftime("%d/%m")}'
            })
        
        context['alerts'] = alerts
        context['page_title'] = 'Dashboard'
        
        return context


class AboutView(TemplateView):
    """Página Sobre."""
    template_name = 'core/about.html'
