"""
Serviços de notificações.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import Notification, NotificationSettings

User = get_user_model()


class NotificationService:
    """Serviço para envio de notificações."""
    
    @staticmethod
    def create_notification(user, notification_type, title, message, link='', priority='medium', metadata=None):
        """Cria uma notificação no sistema."""
        if not user:
            return None
        
        # Verificar se o usuário quer receber este tipo de notificação
        try:
            settings_obj = user.notification_settings
        except NotificationSettings.DoesNotExist:
            settings_obj = NotificationSettings.objects.create(user=user)
        
        # Mapear tipo de notificação para configuração
        setting_map = {
            'appointment_confirmation': 'system_appointment_confirmation',
            'appointment_reminder': 'system_appointment_reminder',
            'appointment_cancelled': 'system_appointment_cancelled',
            'appointment_completed': 'system_appointment_completed',
            'low_stock': 'system_low_stock',
        }
        
        setting_name = setting_map.get(notification_type)
        if setting_name and not getattr(settings_obj, setting_name, True):
            return None
        
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
        
        # Verificar se o usuário quer receber email
        try:
            settings_obj = user.notification_settings
        except NotificationSettings.DoesNotExist:
            settings_obj = NotificationSettings.objects.create(user=user)
        
        # Mapear tipo de notificação para configuração de email
        email_setting_map = {
            'appointment_confirmation': 'email_appointment_confirmation',
            'appointment_reminder': 'email_appointment_reminder',
            'appointment_cancelled': 'email_appointment_cancelled',
            'appointment_completed': 'email_appointment_cancelled',
            'payment_received': 'email_payment_received',
            'low_stock': 'email_low_stock',
        }
        
        setting_name = email_setting_map.get(notification_type)
        if setting_name and not getattr(settings_obj, setting_name, True):
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
        user = appointment.customer.user if appointment.customer else None
        
        if user:
            # Notificação no sistema
            NotificationService.create_notification(
                user=user,
                notification_type='appointment_confirmation',
                title='Agendamento Confirmado!',
                message=f'Seu agendamento para {appointment.service.name} foi confirmado para {appointment.start_time.strftime("%d/%m/%Y às %H:%M")}.',
                link=f'/cliente/agendamentos/',
                priority='high',
                metadata={
                    'appointment_id': appointment.id,
                    'service': appointment.service.name,
                    'barber': str(appointment.barber),
                    'date': appointment.start_time.isoformat()
                }
            )
            
            # Email
            context = {
                'appointment': appointment,
                'customer': appointment.customer,
                'service': appointment.service,
                'barber': appointment.barber,
            }
            NotificationService.send_email_notification(
                user=user,
                notification_type='appointment_confirmation',
                subject=f'Confirmação de Agendamento - Barbearia LS',
                template_name='notifications/emails/appointment_confirmation.html',
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
                message=f'Lembrete: seu agendamento para {appointment.service.name} é amanhã às {appointment.start_time.strftime("%H:%M")}.',
                link=f'/cliente/agendamentos/',
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
                message=f'Seu agendamento para {appointment.service.name} foi cancelado. Motivo: {reason or "Não informado"}',
                link=f'/cliente/agendamentos/',
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
