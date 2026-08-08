"""
Modelos do app Customers.
Gerencia os clientes da barbearia.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel
from apps.core.validators import validate_cpf, validate_phone
from apps.accounts.models import User


class Customer(BaseModel):
    """
    Modelo que representa um cliente da barbearia.
    """
    
    class CustomerStatus(models.TextChoices):
        ACTIVE = 'active', 'Ativo'
        INACTIVE = 'inactive', 'Inativo'
        BLOCKED = 'blocked', 'Bloqueado'
    
    # Relacionamento com o usuário (opcional - cliente pode ser visitante)
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='customer_profile',
        verbose_name=_('Usuário'),
        null=True,
        blank=True,
        help_text='Usuário associado ao cliente (opcional)'
    )
    
    # Informações pessoais
    full_name = models.CharField(
        _('Nome Completo'),
        max_length=150,
        db_index=True
    )
    
    cpf = models.CharField(
        _('CPF'),
        max_length=14,
        unique=True,
        validators=[validate_cpf],
        blank=True,
        null=True,
        help_text='CPF do cliente (apenas números)'
    )
    
    phone = models.CharField(
        _('Telefone'),
        max_length=15,
        validators=[validate_phone],
        db_index=True,
        help_text='Telefone com DDD (apenas números)'
    )
    
    email = models.EmailField(
        _('Email'),
        max_length=254,
        blank=True,
        db_index=True
    )
    
    birth_date = models.DateField(
        _('Data de Nascimento'),
        blank=True,
        null=True
    )
    
    # Endereço
    address = models.TextField(
        _('Endereço'),
        max_length=200,
        blank=True
    )
    
    city = models.CharField(
        _('Cidade'),
        max_length=100,
        blank=True
    )
    
    state = models.CharField(
        _('Estado'),
        max_length=2,
        blank=True
    )
    
    zip_code = models.CharField(
        _('CEP'),
        max_length=10,
        blank=True
    )
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=CustomerStatus.choices,
        default=CustomerStatus.ACTIVE,
        db_index=True
    )
    
    # Fidelidade
    loyalty_points = models.PositiveIntegerField(
        _('Pontos de Fidelidade'),
        default=0,
        help_text='Pontos acumulados no programa de fidelidade'
    )
    
    total_visits = models.PositiveIntegerField(
        _('Total de Visitas'),
        default=0,
        help_text='Número total de visitas à barbearia'
    )
    
    last_visit = models.DateTimeField(
        _('Última Visita'),
        blank=True,
        null=True,
        db_index=True
    )
    
    # Observações
    notes = models.TextField(
        _('Observações'),
        max_length=500,
        blank=True,
        help_text='Observações gerais sobre o cliente'
    )
    
    # Preferências
    preferred_barber = models.ForeignKey(
        'barbers.Barber',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_customers',
        verbose_name=_('Barbeiro Preferido'),
        help_text='Barbeiro que o cliente prefere'
    )
    
    preferred_services = models.ManyToManyField(
        'services.Service',
        blank=True,
        related_name='preferred_by_customers',
        verbose_name=_('Serviços Preferidos'),
        help_text='Serviços que o cliente mais utiliza'
    )
    
    class Meta:
        verbose_name = _('Cliente')
        verbose_name_plural = _('Clientes')
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['full_name', 'phone']),
            models.Index(fields=['status', 'last_visit']),
            models.Index(fields=['loyalty_points']),
        ]
    
    def __str__(self):
        return self.full_name
    
    def increment_visits(self):
        """Incrementa o contador de visitas."""
        from django.utils import timezone
        self.total_visits += 1
        self.last_visit = timezone.now()
        self.save(update_fields=['total_visits', 'last_visit'])
    
    def add_loyalty_points(self, points):
        """Adiciona pontos de fidelidade."""
        if points > 0:
            self.loyalty_points += points
            self.save(update_fields=['loyalty_points'])
    
    def use_loyalty_points(self, points):
        """Utiliza pontos de fidelidade."""
        if points > 0 and self.loyalty_points >= points:
            self.loyalty_points -= points
            self.save(update_fields=['loyalty_points'])
            return True
        return False
    
    @property
    def age(self):
        """Calcula a idade do cliente."""
        from apps.core.utils import calculate_age
        if self.birth_date:
            return calculate_age(self.birth_date)
        return None
    
    @property
    def formatted_phone(self):
        """Retorna o telefone formatado."""
        from apps.core.utils import format_phone
        return format_phone(self.phone)
    
    @property
    def formatted_cpf(self):
        """Retorna o CPF formatado."""
        from apps.core.utils import format_cpf
        if self.cpf:
            return format_cpf(self.cpf)
        return None


class CustomerHistory(BaseModel):
    """
    Histórico de atividades do cliente.
    """
    
    class HistoryType(models.TextChoices):
        APPOINTMENT = 'appointment', 'Agendamento'
        VISIT = 'visit', 'Visita'
        POINTS_EARNED = 'points_earned', 'Pontos Ganhos'
        POINTS_USED = 'points_used', 'Pontos Utilizados'
        FEEDBACK = 'feedback', 'Feedback'
        OTHER = 'other', 'Outro'
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('Cliente')
    )
    
    type = models.CharField(
        _('Tipo'),
        max_length=20,
        choices=HistoryType.choices,
        db_index=True
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=200,
        help_text='Descrição da atividade'
    )
    
    metadata = models.JSONField(
        _('Metadados'),
        default=dict,
        blank=True,
        help_text='Dados adicionais em formato JSON'
    )
    
    class Meta:
        verbose_name = _('Histórico do Cliente')
        verbose_name_plural = _('Históricos dos Clientes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.customer} - {self.get_type_display()} ({self.created_at})'
    # Adicionar unique=True no telefone
    phone = models.CharField(
        _('Telefone'),
        max_length=15,
        validators=[validate_phone],
        db_index=True,
        unique=True,  # ADICIONAR ESTA LINHA
        help_text='Telefone com DDD (apenas números)'
    )
