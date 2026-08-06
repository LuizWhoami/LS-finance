"""
Modelos do app Subscriptions.
Gerencia planos e assinaturas de clientes.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from apps.core.models import BaseModel
from apps.core.validators import validate_percentage, validate_positive
from apps.core.exceptions import InvalidStatusTransition


class Plan(BaseModel):
    """
    Modelo que representa um plano de assinatura.
    """
    
    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', 'Mensal'
        QUARTERLY = 'quarterly', 'Trimestral'
        SEMESTER = 'semester', 'Semestral'
        ANNUAL = 'annual', 'Anual'
    
    class PlanStatus(models.TextChoices):
        ACTIVE = 'active', 'Ativo'
        INACTIVE = 'inactive', 'Inativo'
        DISCONTINUED = 'discontinued', 'Descontinuado'
    
    # Informações básicas
    name = models.CharField(
        _('Nome do Plano'),
        max_length=100,
        db_index=True
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=500,
        blank=True,
        help_text='Descrição dos benefícios do plano'
    )
    
    billing_cycle = models.CharField(
        _('Ciclo de Cobrança'),
        max_length=20,
        choices=BillingCycle.choices,
        db_index=True
    )
    
    # Valores
    price = models.DecimalField(
        _('Preço'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive],
        help_text='Preço do plano por ciclo'
    )
    
    setup_fee = models.DecimalField(
        _('Taxa de Ativação'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Taxa única de ativação do plano'
    )
    
    # Benefícios
    discount_percentage = models.DecimalField(
        _('Desconto em Serviços'),
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[validate_percentage],
        help_text='Percentual de desconto em serviços'
    )
    
    free_services_per_month = models.PositiveIntegerField(
        _('Serviços Gratuitos por Mês'),
        default=0,
        help_text='Número de serviços gratuitos por mês'
    )
    
    priority_booking = models.BooleanField(
        _('Agendamento Prioritário'),
        default=False,
        help_text='Cliente tem prioridade no agendamento'
    )
    
    exclusive_services = models.ManyToManyField(
        'services.Service',
        blank=True,
        related_name='exclusive_plans',
        verbose_name=_('Serviços Exclusivos'),
        help_text='Serviços disponíveis apenas para este plano'
    )
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=PlanStatus.choices,
        default=PlanStatus.ACTIVE,
        db_index=True
    )
    
    # Métricas
    total_subscribers = models.PositiveIntegerField(
        _('Total de Assinantes'),
        default=0,
        help_text='Número total de assinantes ativos'
    )
    
    class Meta:
        verbose_name = _('Plano')
        verbose_name_plural = _('Planos')
        ordering = ['price', 'name']
        indexes = [
            models.Index(fields=['name', 'status']),
            models.Index(fields=['billing_cycle', 'status']),
        ]
    
    def __str__(self):
        return f'{self.name} - {self.get_billing_cycle_display()} (R$ {self.price})'
    
    @property
    def annual_price(self):
        """Retorna o valor anual do plano."""
        multipliers = {
            self.BillingCycle.MONTHLY: 12,
            self.BillingCycle.QUARTERLY: 4,
            self.BillingCycle.SEMESTER: 2,
            self.BillingCycle.ANNUAL: 1,
        }
        return self.price * multipliers.get(self.billing_cycle, 1)
    
    @property
    def price_per_month(self):
        """Retorna o valor mensal do plano."""
        if self.billing_cycle == self.BillingCycle.MONTHLY:
            return self.price
        elif self.billing_cycle == self.BillingCycle.QUARTERLY:
            return self.price / 3
        elif self.billing_cycle == self.BillingCycle.SEMESTER:
            return self.price / 6
        elif self.billing_cycle == self.BillingCycle.ANNUAL:
            return self.price / 12
        return self.price
    
    def increment_subscribers(self):
        """Incrementa o contador de assinantes."""
        self.total_subscribers += 1
        self.save(update_fields=['total_subscribers'])
    
    def decrement_subscribers(self):
        """Decrementa o contador de assinantes."""
        if self.total_subscribers > 0:
            self.total_subscribers -= 1
            self.save(update_fields=['total_subscribers'])


class Subscription(BaseModel):
    """
    Modelo que representa a assinatura de um cliente.
    """
    
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'Ativa'
        SUSPENDED = 'suspended', 'Suspensa'
        CANCELLED = 'cancelled', 'Cancelada'
        EXPIRED = 'expired', 'Expirada'
        PENDING = 'pending', 'Pendente'
    
    # Relacionamentos
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('Cliente')
    )
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('Plano')
    )
    
    # Datas
    start_date = models.DateField(
        _('Data de Início'),
        db_index=True,
        help_text='Data de início da assinatura'
    )
    
    end_date = models.DateField(
        _('Data de Término'),
        db_index=True,
        help_text='Data de término da assinatura'
    )
    
    next_billing_date = models.DateField(
        _('Próxima Cobrança'),
        db_index=True,
        help_text='Data da próxima cobrança'
    )
    
    cancelled_at = models.DateField(
        _('Cancelado em'),
        blank=True,
        null=True,
        help_text='Data de cancelamento da assinatura'
    )
    
    # Valores
    price_paid = models.DecimalField(
        _('Preço Pago'),
        max_digits=10,
        decimal_places=2,
        help_text='Preço pago no momento da assinatura'
    )
    
    setup_fee_paid = models.DecimalField(
        _('Taxa de Ativação Paga'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Taxa de ativação paga'
    )
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.PENDING,
        db_index=True
    )
    
    # Benefícios
    free_services_used = models.PositiveIntegerField(
        _('Serviços Gratuitos Utilizados'),
        default=0,
        help_text='Quantos serviços gratuitos já foram utilizados'
    )
    
    last_free_service_used = models.DateField(
        _('Último Serviço Gratuito'),
        blank=True,
        null=True,
        help_text='Data do último serviço gratuito utilizado'
    )
    
    # Pagamento
    payment_method = models.CharField(
        _('Forma de Pagamento'),
        max_length=20,
        choices=[
            ('credit_card', 'Cartão de Crédito'),
            ('debit_card', 'Cartão Débito'),
            ('pix', 'PIX'),
            ('bank_slip', 'Boleto'),
            ('cash', 'Dinheiro'),
        ],
        default='credit_card'
    )
    
    # Renovação
    auto_renew = models.BooleanField(
        _('Renovação Automática'),
        default=True,
        help_text='Renovar a assinatura automaticamente'
    )
    
    # Observações
    notes = models.TextField(
        _('Observações'),
        max_length=500,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Assinatura')
        verbose_name_plural = _('Assinaturas')
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['plan', 'status']),
            models.Index(fields=['end_date', 'status']),
            models.Index(fields=['next_billing_date']),
        ]
        unique_together = [['customer', 'plan', 'status']]
    
    def __str__(self):
        return f'{self.customer} - {self.plan} ({self.get_status_display()})'
    
    def save(self, *args, **kwargs):
        """Valida e salva a assinatura."""
        if not self.pk:
            self._validate_dates()
        super().save(*args, **kwargs)
    
    def _validate_dates(self):
        """Valida as datas da assinatura."""
        if self.start_date >= self.end_date:
            raise ValidationError(
                _('A data de início deve ser anterior à data de término.')
            )
        
        if self.next_billing_date < self.start_date:
            raise ValidationError(
                _('A próxima cobrança deve ser após a data de início.')
            )
        
        if self.next_billing_date > self.end_date:
            raise ValidationError(
                _('A próxima cobrança deve ser antes da data de término.')
            )
    
    def activate(self):
        """Ativa a assinatura."""
        if self.status != self.SubscriptionStatus.PENDING:
            raise InvalidStatusTransition(
                _('Apenas assinaturas pendentes podem ser ativadas.')
            )
        
        self.status = self.SubscriptionStatus.ACTIVE
        self.save(update_fields=['status'])
        
        # Atualizar contador do plano
        self.plan.increment_subscribers()
    
    def suspend(self, reason=''):
        """Suspende a assinatura."""
        if self.status not in [self.SubscriptionStatus.ACTIVE, self.SubscriptionStatus.PENDING]:
            raise InvalidStatusTransition(
                _('Apenas assinaturas ativas ou pendentes podem ser suspensas.')
            )
        
        self.status = self.SubscriptionStatus.SUSPENDED
        self.notes = reason
        self.save(update_fields=['status', 'notes'])
    
    def cancel(self, reason=''):
        """Cancela a assinatura."""
        if self.status in [self.SubscriptionStatus.CANCELLED, self.SubscriptionStatus.EXPIRED]:
            raise InvalidStatusTransition(
                _('Assinatura já está cancelada ou expirada.')
            )
        
        self.status = self.SubscriptionStatus.CANCELLED
        self.cancelled_at = timezone.now().date()
        self.notes = reason
        self.save(update_fields=['status', 'cancelled_at', 'notes'])
        
        # Atualizar contador do plano
        self.plan.decrement_subscribers()
    
    def renew(self):
        """Renova a assinatura."""
        if self.status != self.SubscriptionStatus.ACTIVE:
            raise InvalidStatusTransition(
                _('Apenas assinaturas ativas podem ser renovadas.')
            )
        
        # Calcular nova data de término
        if self.plan.billing_cycle == Plan.BillingCycle.MONTHLY:
            months = 1
        elif self.plan.billing_cycle == Plan.BillingCycle.QUARTERLY:
            months = 3
        elif self.plan.billing_cycle == Plan.BillingCycle.SEMESTER:
            months = 6
        else:  # ANNUAL
            months = 12
        
        # Atualizar datas
        from dateutil.relativedelta import relativedelta
        self.start_date = timezone.now().date()
        self.end_date = self.start_date + relativedelta(months=months)
        self.next_billing_date = self.end_date
        self.free_services_used = 0
        self.last_free_service_used = None
        self.save(update_fields=[
            'start_date', 'end_date', 'next_billing_date',
            'free_services_used', 'last_free_service_used'
        ])
    
    def use_free_service(self):
        """Utiliza um serviço gratuito."""
        if self.status != self.SubscriptionStatus.ACTIVE:
            raise InvalidStatusTransition(
                _('Apenas assinaturas ativas podem utilizar serviços gratuitos.')
            )
        
        free_available = self.plan.free_services_per_month - self.free_services_used
        if free_available <= 0:
            raise ValidationError(
                _('Você já utilizou todos os serviços gratuitos deste mês.')
            )
        
        self.free_services_used += 1
        self.last_free_service_used = timezone.now().date()
        self.save(update_fields=['free_services_used', 'last_free_service_used'])
    
    @property
    def free_services_remaining(self):
        """Retorna quantos serviços gratuitos ainda estão disponíveis."""
        return self.plan.free_services_per_month - self.free_services_used
    
    @property
    def days_remaining(self):
        """Retorna quantos dias faltam para o término."""
        if self.status != self.SubscriptionStatus.ACTIVE:
            return 0
        delta = self.end_date - timezone.now().date()
        return delta.days if delta.days > 0 else 0
    
    @property
    def is_expired(self):
        """Verifica se a assinatura expirou."""
        return self.end_date < timezone.now().date() and self.status == self.SubscriptionStatus.ACTIVE
    
    def check_and_expire(self):
        """Verifica e expira a assinatura se necessário."""
        if self.is_expired:
            self.status = self.SubscriptionStatus.EXPIRED
            self.save(update_fields=['status'])
            self.plan.decrement_subscribers()
            return True
        return False


class SubscriptionHistory(BaseModel):
    """
    Histórico de mudanças na assinatura.
    """
    
    class ActionType(models.TextChoices):
        CREATED = 'created', 'Criada'
        ACTIVATED = 'activated', 'Ativada'
        SUSPENDED = 'suspended', 'Suspensa'
        CANCELLED = 'cancelled', 'Cancelada'
        RENEWED = 'renewed', 'Renovada'
        EXPIRED = 'expired', 'Expirada'
        PAYMENT = 'payment', 'Pagamento'
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('Assinatura')
    )
    
    action = models.CharField(
        _('Ação'),
        max_length=20,
        choices=ActionType.choices,
        db_index=True
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=500,
        blank=True,
        help_text='Descrição detalhada da ação'
    )
    
    metadata = models.JSONField(
        _('Metadados'),
        default=dict,
        blank=True,
        help_text='Dados adicionais em formato JSON'
    )
    
    performed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_actions',
        verbose_name=_('Realizado por')
    )
    
    class Meta:
        verbose_name = _('Histórico da Assinatura')
        verbose_name_plural = _('Históricos das Assinaturas')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.subscription} - {self.get_action_display()} ({self.created_at})'
