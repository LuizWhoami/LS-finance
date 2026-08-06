"""
Modelos para o app Notifications.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Notification(BaseModel):
    """
    Modelo que representa uma notificação no sistema.
    """
    
    class NotificationType(models.TextChoices):
        APPOINTMENT_CONFIRMATION = 'appointment_confirmation', 'Confirmação de Agendamento'
        APPOINTMENT_REMINDER = 'appointment_reminder', 'Lembrete de Agendamento'
        APPOINTMENT_CANCELLED = 'appointment_cancelled', 'Agendamento Cancelado'
        APPOINTMENT_COMPLETED = 'appointment_completed', 'Agendamento Concluído'
        PAYMENT_RECEIVED = 'payment_received', 'Pagamento Recebido'
        LOW_STOCK = 'low_stock', 'Estoque Baixo'
        CUSTOMER_BIRTHDAY = 'customer_birthday', 'Aniversário do Cliente'
        SYSTEM_ALERT = 'system_alert', 'Alerta do Sistema'
        PROMOTIONAL = 'promotional', 'Promocional'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Baixa'
        MEDIUM = 'medium', 'Média'
        HIGH = 'high', 'Alta'
        URGENT = 'urgent', 'Urgente'
    
    # Quem recebe
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Usuário'),
        null=True,
        blank=True
    )
    
    # Conteúdo
    type = models.CharField(
        _('Tipo'),
        max_length=30,
        choices=NotificationType.choices,
        db_index=True
    )
    
    title = models.CharField(
        _('Título'),
        max_length=200
    )
    
    message = models.TextField(
        _('Mensagem'),
        max_length=1000
    )
    
    link = models.CharField(
        _('Link'),
        max_length=200,
        blank=True,
        help_text='Link para redirecionar ao clicar na notificação'
    )
    
    # Status
    is_read = models.BooleanField(
        _('Lida'),
        default=False,
        db_index=True
    )
    
    read_at = models.DateTimeField(
        _('Lida em'),
        blank=True,
        null=True
    )
    
    priority = models.CharField(
        _('Prioridade'),
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    
    # Dados adicionais (JSON)
    metadata = models.JSONField(
        _('Metadados'),
        default=dict,
        blank=True,
        help_text='Dados adicionais da notificação'
    )
    
    class Meta:
        verbose_name = _('Notificação')
        verbose_name_plural = _('Notificações')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['type', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.title} - {self.user}'
    
    def mark_as_read(self):
        """Marca a notificação como lida."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_unread(self):
        """Marca a notificação como não lida."""
        self.is_read = False
        self.read_at = None
        self.save(update_fields=['is_read', 'read_at'])


class NotificationSettings(BaseModel):
    """
    Configurações de notificação por usuário.
    """
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name=_('Usuário')
    )
    
    # Notificações por Email
    email_appointment_confirmation = models.BooleanField(
        _('Email - Confirmação de Agendamento'),
        default=True
    )
    email_appointment_reminder = models.BooleanField(
        _('Email - Lembrete de Agendamento'),
        default=True
    )
    email_appointment_cancelled = models.BooleanField(
        _('Email - Agendamento Cancelado'),
        default=True
    )
    email_payment_received = models.BooleanField(
        _('Email - Pagamento Recebido'),
        default=True
    )
    email_low_stock = models.BooleanField(
        _('Email - Estoque Baixo'),
        default=True
    )
    email_promotional = models.BooleanField(
        _('Email - Promocionais'),
        default=False
    )
    
    # Notificações no Sistema
    system_appointment_confirmation = models.BooleanField(
        _('Sistema - Confirmação de Agendamento'),
        default=True
    )
    system_appointment_reminder = models.BooleanField(
        _('Sistema - Lembrete de Agendamento'),
        default=True
    )
    system_appointment_cancelled = models.BooleanField(
        _('Sistema - Agendamento Cancelado'),
        default=True
    )
    system_appointment_completed = models.BooleanField(
        _('Sistema - Agendamento Concluído'),
        default=True
    )
    system_low_stock = models.BooleanField(
        _('Sistema - Estoque Baixo'),
        default=True
    )
    
    class Meta:
        verbose_name = _('Configuração de Notificação')
        verbose_name_plural = _('Configurações de Notificações')
    
    def __str__(self):
        return f'Configurações de {self.user}'
