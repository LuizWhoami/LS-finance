"""
Serviços para geração de relatórios.
"""

from django.db import models
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta

from apps.appointments.models import Appointment
from apps.customers.models import Customer
from apps.barbers.models import Barber
from apps.services.models import Service
from apps.finance.models import Transaction, CashRegister
from apps.products.models import Product, InventoryMovement
from apps.subscriptions.models import Subscription


class ReportService:
    """
    Serviço para geração de relatórios.
    """
    
    @staticmethod
    def get_financial_report(start_date, end_date):
        """
        Relatório financeiro.
        """
        transactions = Transaction.objects.filter(
            transaction_date__date__gte=start_date,
            transaction_date__date__lte=end_date
        )
        
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
        
        by_payment_method = transactions.values(
            'payment_method'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'totals': {
                'income': total_income,
                'expense': total_expense,
                'commission': total_commission,
                'net_profit': net_profit
            },
            'by_payment_method': by_payment_method,
            'transactions_count': transactions.count()
        }
    
    @staticmethod
    def get_appointments_report(start_date, end_date):
        """
        Relatório de agendamentos.
        """
        appointments = Appointment.objects.filter(
            start_time__date__gte=start_date,
            start_time__date__lte=end_date
        )
        
        total = appointments.count()
        
        by_status = appointments.values('status').annotate(
            count=Count('id')
        )
        
        by_barber = appointments.values(
            'barber__user__first_name',
            'barber__user__last_name'
        ).annotate(
            total=Count('id'),
            revenue=Sum('final_price'),
            avg_rating=Avg('rating')
        )
        
        by_service = appointments.values(
            'service__name'
        ).annotate(
            total=Count('id'),
            revenue=Sum('final_price')
        ).order_by('-total')[:10]
        
        completed = appointments.filter(
            status=Appointment.AppointmentStatus.COMPLETED
        )
        
        total_revenue = completed.aggregate(
            total=Sum('final_price')
        )['total'] or 0
        
        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'totals': {
                'total': total,
                'completed': completed.count(),
                'cancelled': appointments.filter(
                    status=Appointment.AppointmentStatus.CANCELLED
                ).count(),
                'no_show': appointments.filter(
                    status=Appointment.AppointmentStatus.NO_SHOW
                ).count(),
                'revenue': total_revenue,
                'avg_ticket': total_revenue / completed.count() if completed.count() > 0 else 0
            },
            'by_status': by_status,
            'by_barber': by_barber,
            'by_service': by_service
        }
    
    @staticmethod
    def get_customers_report():
        """
        Relatório de clientes.
        """
        total_customers = Customer.objects.filter(
            is_active=True
        ).count()
        
        active_customers = Customer.objects.filter(
            is_active=True,
            last_visit__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        new_customers = Customer.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        top_customers = Customer.objects.filter(
            is_active=True
        ).annotate(
            total_visits=models.F('total_visits')
        ).order_by('-total_visits')[:10]
        
        loyalty_points = Customer.objects.aggregate(
            total=Sum('loyalty_points')
        )['total'] or 0
        
        return {
            'totals': {
                'total': total_customers,
                'active': active_customers,
                'new': new_customers,
                'loyalty_points': loyalty_points
            },
            'top_customers': [
                {
                    'name': c.full_name,
                    'visits': c.total_visits,
                    'points': c.loyalty_points,
                    'last_visit': c.last_visit
                }
                for c in top_customers
            ]
        }
    
    @staticmethod
    def get_barbers_report(start_date, end_date):
        """
        Relatório de barbeiros.
        """
        barbers = Barber.objects.filter(is_active=True)
        
        performance = []
        for barber in barbers:
            appointments = Appointment.objects.filter(
                barber=barber,
                status=Appointment.AppointmentStatus.COMPLETED,
                start_time__date__gte=start_date,
                start_time__date__lte=end_date
            )
            
            completed = appointments.count()
            revenue = appointments.aggregate(
                total=Sum('final_price')
            )['total'] or 0
            
            rating = barber.rating
            
            performance.append({
                'name': barber.full_name,
                'completed': completed,
                'revenue': revenue,
                'avg_ticket': revenue / completed if completed > 0 else 0,
                'rating': rating
            })
        
        # Ordenar por receita
        performance.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'performance': performance,
            'total_barbers': len(performance)
        }
    
    @staticmethod
    def get_products_report():
        """
        Relatório de produtos e estoque.
        """
        products = Product.objects.filter(is_active=True)
        
        total_products = products.count()
        low_stock = products.filter(quantity__lte=models.F('minimum_stock')).count()
        
        top_products = products.annotate(
            total_usage=Count('product_services')
        ).order_by('-total_usage')[:10]
        
        movements = InventoryMovement.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        total_in = movements.filter(
            movement_type=InventoryMovement.MovementType.IN
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        total_out = movements.filter(
            movement_type=InventoryMovement.MovementType.OUT
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        return {
            'totals': {
                'total_products': total_products,
                'low_stock': low_stock,
                'total_in': total_in,
                'total_out': total_out
            },
            'top_products': [
                {
                    'name': p.name,
                    'usage': p.total_usage,
                    'stock': p.quantity,
                    'minimum': p.minimum_stock
                }
                for p in top_products
            ]
        }
    
    @staticmethod
    def get_subscriptions_report():
        """
        Relatório de assinaturas.
        """
        total = Subscription.objects.filter(
            status=Subscription.SubscriptionStatus.ACTIVE
        ).count()
        
        by_plan = Subscription.objects.filter(
            status=Subscription.SubscriptionStatus.ACTIVE
        ).values('plan__name').annotate(
            total=Count('id'),
            revenue=Sum('price_paid')
        )
        
        new_subscriptions = Subscription.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        cancelled = Subscription.objects.filter(
            status=Subscription.SubscriptionStatus.CANCELLED,
            cancelled_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        renewal_rate = (total / (total + cancelled) * 100) if (total + cancelled) > 0 else 0
        
        return {
            'totals': {
                'active': total,
                'new': new_subscriptions,
                'cancelled': cancelled,
                'renewal_rate': round(renewal_rate, 2)
            },
            'by_plan': by_plan
        }
    
    @staticmethod
    def get_dashboard_metrics():
        """
        Métricas para o dashboard.
        """
        today = timezone.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # Agendamentos de hoje
        today_appointments = Appointment.objects.filter(
            start_time__date=today
        )
        
        appointments_today = today_appointments.count()
        appointments_completed = today_appointments.filter(
            status=Appointment.AppointmentStatus.COMPLETED
        ).count()
        
        # Faturamento de hoje
        today_transactions = Transaction.objects.filter(
            transaction_date__date=today,
            transaction_type=Transaction.TransactionType.INCOME
        )
        revenue_today = today_transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Clientes ativos
        active_customers = Customer.objects.filter(
            is_active=True,
            last_visit__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Assinaturas ativas
        active_subscriptions = Subscription.objects.filter(
            status=Subscription.SubscriptionStatus.ACTIVE
        ).count()
        
        # Produtos com estoque baixo
        low_stock_products = Product.objects.filter(
            is_active=True,
            quantity__lte=models.F('minimum_stock')
        ).count()
        
        return {
            'appointments_today': appointments_today,
            'appointments_completed': appointments_completed,
            'revenue_today': revenue_today,
            'active_customers': active_customers,
            'active_subscriptions': active_subscriptions,
            'low_stock_products': low_stock_products,
            'date': today
        }
