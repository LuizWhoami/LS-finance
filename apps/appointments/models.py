"""
Modelos do app Appointments.
Gerencia os agendamentos da barbearia.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.core.models import BaseModel
from apps.core.exceptions import AppointmentConflictError, InvalidStatusTransition
from apps.barbers.models import Barber
from apps.customers.models import Customer
from apps.services.models import Service


class Appointment(BaseModel):
    """
    Modelo que representa um agendamento.
    """
    
    class AppointmentStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Agendado'
        CONFIRMED = 'confirmed', 'Confirmado'
        IN_PROGRESS = 'in_progress', 'Em Andamento'
        COMPLETED = 'completed', 'Concluído'
        CANCELLED = 'cancelled', 'Cancelado'
        NO_SHOW = 'no_show', 'Não Compareceu'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PAID = 'paid', 'Pago'
        PARTIAL = 'partial', 'Parcial'
        CANCELLED = 'cancelled', 'Cancelado'
    
    # Relacionamentos
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name=_('Cliente')
    )
    
    barber = models.ForeignKey(
        Barber,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name=_('Barbeiro')
    )
    
    # Datas e horários
    start_time = models.DateTimeField(
        _('Data e Hora de Início'),
        db_index=True,
        help_text='Data e hora de início do agendamento'
    )
    
    end_time = models.DateTimeField(
        _('Data e Hora de Término'),
        db_index=True,
        help_text='Data e hora de término do agendamento'
    )
    
    total_duration = models.PositiveIntegerField(
        _('Duração Total'),
        default=0,
        help_text='Duração total em minutos'
    )
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
        db_index=True
    )
    
    payment_status = models.CharField(
        _('Status do Pagamento'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    
    # Valores
    service_price = models.DecimalField(
        _('Preço do Serviço'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Preço do serviço no momento do agendamento'
    )
    
    discount = models.DecimalField(
        _('Desconto'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Desconto aplicado ao agendamento'
    )
    
    final_price = models.DecimalField(
        _('Preço Final'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Preço final após descontos'
    )
    
    # Comissão
    commission_amount = models.DecimalField(
        _('Valor da Comissão'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Valor da comissão para o barbeiro'
    )
    
    # Avaliação
    rating = models.DecimalField(
        _('Avaliação'),
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Avaliação do cliente (0-5)'
    )
    
    feedback = models.TextField(
        _('Feedback'),
        max_length=500,
        blank=True,
        help_text='Feedback do cliente sobre o serviço'
    )
    
    # Informações adicionais
    notes = models.TextField(
        _('Observações'),
        max_length=500,
        blank=True,
        help_text='Observações sobre o agendamento'
    )
    
    cancelled_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_appointments',
        verbose_name=_('Cancelado por')
    )
    
    cancelled_at = models.DateTimeField(
        _('Cancelado em'),
        blank=True,
        null=True
    )
    
    cancellation_reason = models.TextField(
        _('Motivo do Cancelamento'),
        max_length=200,
        blank=True,
        help_text='Motivo do cancelamento do agendamento'
    )
    
    completed_at = models.DateTimeField(
        _('Concluído em'),
        blank=True,
        null=True
    )
    
    # Session key para agendamentos sem login
    session_key = models.CharField(
        _('Chave de Sessão'),
        max_length=40,
        blank=True,
        null=True,
        db_index=True,
        help_text='Chave da sessão para agendamentos de visitantes'
    )
    
    class Meta:
        verbose_name = _('Agendamento')
        verbose_name_plural = _('Agendamentos')
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['barber', 'start_time', 'status']),
            models.Index(fields=['customer', 'start_time']),
            models.Index(fields=['status', 'start_time']),
        ]
        # REMOVIDO: unique_together - a validação agora é feita via código
        # A restrição de unicidade era a CAUSA do bug, pois impedia
        # criar novos agendamentos mesmo quando o anterior estava CANCELADO
    
    def __str__(self):
        items = self.items.all()
        if items.exists():
            services_names = ', '.join([item.service.name for item in items])
            return f'{self.customer} - {services_names} ({self.start_time})'
        return f'{self.customer} - Agendamento ({self.start_time})'
    
    def save(self, *args, **kwargs):
        """Valida e salva o agendamento."""
        from decimal import Decimal
        
        if hasattr(self, 'service_price') and self.service_price:
            self.service_price = Decimal(str(self.service_price))
        else:
            self.service_price = Decimal('0.00')
        
        if hasattr(self, 'discount') and self.discount:
            self.discount = Decimal(str(self.discount))
        else:
            self.discount = Decimal('0.00')
        
        if kwargs.get('update_fields') and 'is_active' in kwargs.get('update_fields', []):
            super().save(*args, **kwargs)
            return
        
        if not self.pk or self.is_active:
            self._validate_dates()
            self._validate_conflicts()
            self._calculate_final_price()
            self._calculate_commission()
        
        super().save(*args, **kwargs)
    
    def _validate_dates(self):
        """Valida se as datas são consistentes."""
        if self.start_time is None or self.end_time is None:
            raise ValidationError(
                _('Data e hora são obrigatórias.')
            )
        
        if self.start_time >= self.end_time:
            raise ValidationError(
                _('O horário de início deve ser anterior ao horário de término.')
            )
        
        now = timezone.now()
        if self.start_time < now - timezone.timedelta(minutes=5):
            raise ValidationError(
                _('Não é possível agendar no passado.')
            )
    
    def _validate_conflicts(self):
        """
        Valida conflitos de horário.
        APENAS agendamentos com status ATIVO bloqueiam o horário.
        CANCELADO NÃO bloqueia.
        """
        # Status que bloqueiam o horário
        active_statuses = [
            self.AppointmentStatus.SCHEDULED,
            self.AppointmentStatus.CONFIRMED,
            self.AppointmentStatus.IN_PROGRESS,
        ]
        
        # Verificar conflito com o barbeiro
        barber_conflicts = Appointment.objects.filter(
            barber=self.barber,
            is_active=True,
            status__in=active_statuses,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )
        
        if self.pk:
            barber_conflicts = barber_conflicts.exclude(pk=self.pk)
        
        if barber_conflicts.exists():
            conflict = barber_conflicts.first()
            raise AppointmentConflictError(
                _('O barbeiro já possui um agendamento das {} às {} neste dia.').format(
                    conflict.start_time.strftime('%H:%M'),
                    conflict.end_time.strftime('%H:%M')
                )
            )
        
        # Verificar conflito com o cliente
        customer_conflicts = Appointment.objects.filter(
            customer=self.customer,
            is_active=True,
            status__in=active_statuses,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )
        
        if self.pk:
            customer_conflicts = customer_conflicts.exclude(pk=self.pk)
        
        if customer_conflicts.exists():
            conflict = customer_conflicts.first()
            raise AppointmentConflictError(
                _('O cliente já possui um agendamento das {} às {} neste dia.').format(
                    conflict.start_time.strftime('%H:%M'),
                    conflict.end_time.strftime('%H:%M')
                )
            )
    
    def _calculate_final_price(self):
        """Calcula o preço final com desconto."""
        from decimal import Decimal
        
        service_price = Decimal(str(self.service_price)) if self.service_price else Decimal('0.00')
        discount = Decimal(str(self.discount)) if self.discount else Decimal('0.00')
        
        self.final_price = service_price - discount
        if self.final_price < Decimal('0.00'):
            self.final_price = Decimal('0.00')
    
    def _calculate_commission(self):
        """Calcula o valor da comissão do barbeiro."""
        from decimal import Decimal
        
        if self.barber and self.barber.commission_percentage:
            percentage = Decimal(str(self.barber.commission_percentage))
            self.commission_amount = (self.final_price * percentage) / Decimal('100.00')
        else:
            self.commission_amount = Decimal('0.00')
    
    def confirm(self):
        """Confirma o agendamento."""
        if self.status != self.AppointmentStatus.SCHEDULED:
            raise InvalidStatusTransition(
                _('Apenas agendamentos com status "Agendado" podem ser confirmados.')
            )
        self.status = self.AppointmentStatus.CONFIRMED
        self.save(update_fields=['status'])
    
    def start(self):
        """Inicia o atendimento."""
        if self.status not in [self.AppointmentStatus.SCHEDULED, self.AppointmentStatus.CONFIRMED]:
            raise InvalidStatusTransition(
                _('Apenas agendamentos confirmados podem ser iniciados.')
            )
        self.status = self.AppointmentStatus.IN_PROGRESS
        self.save(update_fields=['status'])
    
    def complete(self):
        """Conclui o atendimento."""
        if self.status != self.AppointmentStatus.IN_PROGRESS:
            raise InvalidStatusTransition(
                _('Apenas agendamentos em andamento podem ser concluídos.')
            )
        self.status = self.AppointmentStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
        
        self.customer.increment_visits()
        self.barber.increment_services()
    
    def cancel_appointment(self, user=None, reason=''):
        """
        Cancela o agendamento (soft delete) - mantém o registro no banco.
        O horário fica disponível para novos agendamentos.
        """
        if self.status in [self.AppointmentStatus.COMPLETED, self.AppointmentStatus.CANCELLED]:
            raise InvalidStatusTransition(
                _('Agendamentos concluídos ou já cancelados não podem ser cancelados.')
            )
        
        if self.customer.user and user == self.customer.user:
            time_until = self.start_time - timezone.now()
            if time_until.total_seconds() < 7200:
                raise InvalidStatusTransition(
                    _('Cancelamentos devem ser feitos com pelo menos 2 horas de antecedência.')
                )
        
        self.status = self.AppointmentStatus.CANCELLED
        self.cancelled_by = user
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancelled_by', 'cancelled_at', 'cancellation_reason', 'updated_at'])
        
        return True
    
    def mark_no_show(self):
        """Marca como não compareceu."""
        if self.status not in [self.AppointmentStatus.SCHEDULED, self.AppointmentStatus.CONFIRMED]:
            raise InvalidStatusTransition(
                _('Apenas agendamentos agendados/confirmados podem ser marcados como não compareceu.')
            )
        
        if self.start_time > timezone.now():
            raise ValidationError(
                _('Não é possível marcar como não compareceu um agendamento futuro.')
            )
        
        self.status = self.AppointmentStatus.NO_SHOW
        self.save(update_fields=['status'])
    
    def calculate_totals(self):
        """Calcula o total de preço e duração dos itens."""
        from decimal import Decimal
        total_price = Decimal('0.00')
        total_duration = 0
        
        for item in self.items.all():
            total_price += item.price
            total_duration += item.duration_minutes
        
        self.final_price = total_price
        self.total_duration = total_duration
        self.service_price = total_price
        self.save(update_fields=['final_price', 'total_duration', 'service_price'])
        
        return total_price, total_duration
    
    def send_notifications(self):
        """Envia notificações para o cliente."""
        from apps.notifications.services import ClientNotificationService
        
        ClientNotificationService.send_appointment_confirmation(self)
        ClientNotificationService.send_whatsapp_notification(self)
        
        if self.customer.user:
            from apps.notifications.services import NotificationService
            NotificationService.create_notification(
                user=self.customer.user,
                notification_type='appointment_confirmation',
                title='Agendamento Confirmado!',
                message=f'Seu agendamento foi confirmado para {self.start_time.strftime("%d/%m/%Y às %H:%M")}.',
                link='/cliente/agendamentos/',
                priority='high'
            )
    
    @property
    def duration_minutes(self):
        """Retorna a duração do agendamento em minutos."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    @property
    def is_past(self):
        """Verifica se o agendamento já passou."""
        return self.end_time < timezone.now()
    
    @property
    def is_upcoming(self):
        """Verifica se o agendamento é futuro."""
        return self.start_time > timezone.now()
    
    @property
    def can_cancel(self):
        """Verifica se o agendamento pode ser cancelado."""
        if self.status in [self.AppointmentStatus.COMPLETED, self.AppointmentStatus.CANCELLED]:
            return False
        
        if self.status == self.AppointmentStatus.IN_PROGRESS:
            return False
        
        time_until = self.start_time - timezone.now()
        return time_until.total_seconds() >= 7200


class AppointmentItem(BaseModel):
    """
    Modelo para itens de um agendamento (múltiplos serviços).
    """
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Agendamento')
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='appointment_items',
        verbose_name=_('Serviço')
    )
    
    price = models.DecimalField(
        _('Preço'),
        max_digits=10,
        decimal_places=2,
        help_text='Preço do serviço no momento do agendamento'
    )
    
    duration_minutes = models.PositiveIntegerField(
        _('Duração (minutos)'),
        default=30,
        help_text='Duração do serviço'
    )
    
    class Meta:
        verbose_name = _('Item do Agendamento')
        verbose_name_plural = _('Itens do Agendamento')
        ordering = ['id']
    
    def __str__(self):
        return f'{self.service.name} - {self.appointment}'
