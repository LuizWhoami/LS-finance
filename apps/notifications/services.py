"""
Serviços de notificações.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class NotificationService:
    """Serviço para envio de notificações."""
    
    @staticmethod
    def create_notification(user, notification_type, title, message, link='', priority='medium', metadata=None):
        """Cria uma notificação no sistema."""
        if not user:
            return None
        
        from .models import Notification
        return Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            link=link,
            priority=priority,
            metadata=metadata or {}
        )
    
    @staticmethod
    def send_email_notification(user, notification_type, subject, template_name, context):
        """Envia uma notificação por email."""
        if not user or not user.email:
            return False
        
        try:
            html_message = render_to_string(template_name, context)
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            return False


class AppointmentNotificationService:
    """Serviço específico para notificações de agendamentos."""
    
    @staticmethod
    def send_appointment_confirmation(appointment):
        """Envia confirmação de agendamento."""
        # Tentar obter o nome do serviço
        service_name = 'Serviço'
        if hasattr(appointment, '_service') and appointment._service:
            service_name = appointment._service.name
        elif hasattr(appointment, 'service') and appointment.service:
            service_name = appointment.service.name
        else:
            items = appointment.items.all()
            if items.exists():
                service_name = ', '.join([item.service.name for item in items])
        
        user = appointment.customer.user if appointment.customer else None
        
        if user:
            NotificationService.create_notification(
                user=user,
                notification_type='appointment_confirmation',
                title='Agendamento Confirmado!',
                message=f'Seu agendamento para {service_name} foi confirmado para {appointment.start_time.strftime("%d/%m/%Y às %H:%M")}.',
                link='/cliente/agendamentos/',
                priority='high',
                metadata={
                    'appointment_id': appointment.id,
                    'service': service_name,
                    'barber': str(appointment.barber),
                    'date': appointment.start_time.isoformat()
                }
            )
            
            context = {
                'appointment': appointment,
                'customer': appointment.customer,
                'service_name': service_name,
                'barber': appointment.barber,
                'site_url': 'http://127.0.0.1:8000',
            }
            NotificationService.send_email_notification(
                user=user,
                notification_type='appointment_confirmation',
                subject='Confirmação de Agendamento - Barbearia LS',
                template_name='emails/appointment_confirmation.html',
                context=context
            )
    
    @staticmethod
    def send_appointment_reminder(appointment):
        """Envia lembrete de agendamento."""
        user = appointment.customer.user if appointment.customer else None
        
        if user:
            NotificationService.create_notification(
                user=user,
                notification_type='appointment_reminder',
                title='Lembrete: Você tem um agendamento!',
                message=f'Lembrete: seu agendamento é amanhã às {appointment.start_time.strftime("%H:%M")}.',
                link='/cliente/agendamentos/',
                priority='high'
            )
    
    @staticmethod
    def send_appointment_cancelled(appointment, reason=''):
        """Envia notificação de cancelamento."""
        user = appointment.customer.user if appointment.customer else None
        
        if user:
            NotificationService.create_notification(
                user=user,
                notification_type='appointment_cancelled',
                title='Agendamento Cancelado',
                message=f'Seu agendamento foi cancelado. Motivo: {reason or "Não informado"}',
                link='/cliente/agendamentos/',
                priority='high'
            )


class StockNotificationService:
    """Serviço para notificações de estoque."""
    
    @staticmethod
    def check_low_stock():
        """Verifica produtos com estoque baixo e notifica admins."""
        from apps.products.models import Product
        
        low_stock_products = Product.objects.filter(
            is_active=True,
            quantity__lte=models.F('minimum_stock')
        )
        
        admins = User.objects.filter(is_staff=True)
        
        for product in low_stock_products:
            for admin in admins:
                NotificationService.create_notification(
                    user=admin,
                    notification_type='low_stock',
                    title=f'Estoque Baixo: {product.name}',
                    message=f'O produto {product.name} está com estoque baixo. Atual: {product.quantity} | Mínimo: {product.minimum_stock}',
                    link='/products/',
                    priority='high'
                )


# Alias para manter compatibilidade
ClientNotificationService = NotificationService
