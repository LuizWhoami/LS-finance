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
        
        # ============================================================
        # AGENDAMENTOS DE HOJE (APENAS ATIVOS)
        # ============================================================
        appointments_today = Appointment.objects.filter(
            start_time__date=today,
            is_active=True  # APENAS ATIVOS
        )
        context['appointments_today'] = appointments_today.count()
        
        # Agendamentos concluídos hoje
        context['appointments_completed_today'] = appointments_today.filter(
            status=Appointment.AppointmentStatus.COMPLETED,
            is_active=True
        ).count()
        
        # Faturamento de hoje (apenas concluídos e ativos)
        revenue_today = Appointment.objects.filter(
            start_time__date=today,
            status=Appointment.AppointmentStatus.COMPLETED,
            is_active=True
        ).aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
        context['revenue_today'] = revenue_today
        
        # ============================================================
        # FATURAMENTO DO MÊS (APENAS CONCLUÍDOS E ATIVOS)
        # ============================================================
        context['revenue_month'] = Appointment.objects.filter(
            start_time__date__gte=start_of_month,
            start_time__date__lte=end_of_month,
            status=Appointment.AppointmentStatus.COMPLETED,
            is_active=True
        ).aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
        
        context['appointments_month'] = Appointment.objects.filter(
            start_time__date__gte=start_of_month,
            start_time__date__lte=end_of_month,
            is_active=True
        ).count()
        
        # ============================================================
        # CLIENTES (APENAS ATIVOS)
        # ============================================================
        context['total_customers'] = Customer.objects.filter(is_active=True).count()
        context['active_customers'] = Customer.objects.filter(
            is_active=True,
            last_visit__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # ============================================================
        # BARBEIROS E SERVIÇOS (APENAS ATIVOS)
        # ============================================================
        context['total_barbers'] = Barber.objects.filter(is_active=True, status='active').count()
        context['total_services'] = Service.objects.filter(is_active=True, status='active').count()
        
        # ============================================================
        # SERVIÇOS MAIS VENDIDOS (APENAS ATIVOS E CONCLUÍDOS)
        # ============================================================
        top_services = Appointment.objects.filter(
            status=Appointment.AppointmentStatus.COMPLETED,
            start_time__date__gte=start_of_month,
            is_active=True
        ).values('service__name').annotate(
            total=Count('id'),
            revenue=Sum('final_price')
        ).order_by('-total')[:5]
        context['top_services'] = top_services
        
        # ============================================================
        # PRÓXIMOS AGENDAMENTOS (APENAS ATIVOS E FUTUROS)
        # ============================================================
        context['upcoming_appointments'] = Appointment.objects.filter(
            start_time__gte=timezone.now(),
            is_active=True,
            status__in=[
                Appointment.AppointmentStatus.SCHEDULED,
                Appointment.AppointmentStatus.CONFIRMED
            ]
        ).select_related('customer', 'barber', 'service').order_by('start_time')[:5]
        
        # ============================================================
        # GRÁFICO: FATURAMENTO DIÁRIO (ÚLTIMOS 30 DIAS)
        # ============================================================
        daily_revenue = []
        for i in range(30):
            date = today - timedelta(days=i)
            daily_total = Appointment.objects.filter(
                start_time__date=date,
                status=Appointment.AppointmentStatus.COMPLETED,
                is_active=True
            ).aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
            daily_revenue.append({
                'date': date.strftime('%d/%m'),
                'total': float(daily_total)
            })
        context['daily_revenue'] = list(reversed(daily_revenue))
        
        # ============================================================
        # GRÁFICO: AGENDAMENTOS POR DIA DA SEMANA (APENAS ATIVOS)
        # ============================================================
        weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        weekday_counts = []
        for i in range(7):
            day_start = start_of_week + timedelta(days=i)
            count = Appointment.objects.filter(
                start_time__date=day_start,
                is_active=True
            ).count()
            weekday_counts.append(count)
        context['weekday_labels'] = weekdays
        context['weekday_counts'] = weekday_counts
        
        # ============================================================
        # GRÁFICO: DISTRIBUIÇÃO DE STATUS (APENAS ATIVOS)
        # ============================================================
        status_counts = {}
        for status in Appointment.AppointmentStatus.choices:
            status_counts[status[1]] = Appointment.objects.filter(
                status=status[0],
                is_active=True
            ).count()
        context['status_counts'] = status_counts
        
        # ============================================================
        # ALERTAS (APENAS DADOS VÁLIDOS)
        # ============================================================
        alerts = []
        
        # Estoque baixo (apenas produtos ativos)
        low_stock_products = Product.objects.filter(
            is_active=True,
            quantity__lte=models.F('minimum_stock')
        )[:5]
        for product in low_stock_products:
            alerts.append({
                'type': 'warning',
                'message': f'Estoque baixo: {product.name} (atual: {product.quantity})'
            })
        
        # Aniversariantes do mês (apenas clientes ativos)
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


def check_ip_status(request):
    """Endpoint para verificar se o IP atual está bloqueado."""
    from django.core.cache import cache
    from django.http import JsonResponse
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    block_key = f'blocked_ip:{ip}'
    is_blocked = cache.get(block_key, False)
    
    return JsonResponse({
        'ip': ip,
        'blocked': is_blocked,
        'message': 'IP bloqueado' if is_blocked else 'IP liberado'
    })


# Páginas de erro
def handler404(request, exception):
    """Página 404 personalizada."""
    from django.shortcuts import render
    return render(request, '404.html', status=404)


def handler500(request):
    """Página 500 personalizada."""
    from django.shortcuts import render
    return render(request, '500.html', status=500)


def handler403(request, exception):
    """Página 403 personalizada."""
    from django.shortcuts import render
    return render(request, '403.html', status=403)
