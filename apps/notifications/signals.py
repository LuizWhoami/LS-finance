"""
Signals para notificações.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.appointments.models import Appointment
from .services import AppointmentNotificationService, StockNotificationService


@receiver(post_save, sender=Appointment)
def appointment_notification_handler(sender, instance, created, **kwargs):
    """Handler para notificações de agendamento."""
    if created:
        # Quando um agendamento é criado, enviar confirmação
        AppointmentNotificationService.send_appointment_confirmation(instance)
    
    # Se o status mudou para CANCELLED
    if hasattr(instance, '_original_status'):
        if instance._original_status != instance.status:
            if instance.status == Appointment.AppointmentStatus.CANCELLED:
                AppointmentNotificationService.send_appointment_cancelled(
                    instance, 
                    instance.cancellation_reason or 'Cancelado'
                )


# Salvar status original para comparar depois
@receiver(post_save, sender=Appointment)
def save_original_status(sender, instance, **kwargs):
    """Salva o status original antes de salvar."""
    if hasattr(instance, '_original_status'):
        instance._original_status = instance.status


# Verificar estoque baixo periodicamente (chamado por um agendador)
def check_stock_notifications():
    """Função para ser chamada por agendador (Celery)"""
    StockNotificationService.check_low_stock()
