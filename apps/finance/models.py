"""
Modelos para o app Finance.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.core.models import BaseModel
from apps.core.validators import validate_positive
from apps.core.exceptions import InvalidStatusTransition


class Transaction(BaseModel):
    """Modelo que representa uma transação financeira."""
    
    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Receita'
        EXPENSE = 'expense', 'Despesa'
        COMMISSION = 'commission', 'Comissão'
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Dinheiro'
        CARD_DEBIT = 'card_debit', 'Cartão Débito'
        CARD_CREDIT = 'card_credit', 'Cartão Crédito'
        PIX = 'pix', 'PIX'
        TRANSFER = 'transfer', 'Transferência'
        OTHER = 'other', 'Outro'
    
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('Agendamento')
    )
    
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('Cliente')
    )
    
    barber = models.ForeignKey(
        'barbers.Barber',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('Barbeiro')
    )
    
    transaction_type = models.CharField(
        _('Tipo de Transação'),
        max_length=20,
        choices=TransactionType.choices,
        db_index=True
    )
    
    payment_method = models.CharField(
        _('Forma de Pagamento'),
        max_length=20,
        choices=PaymentMethod.choices,
        db_index=True
    )
    
    amount = models.DecimalField(
        _('Valor'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive],
        help_text='Valor da transação'
    )
    
    description = models.CharField(
        _('Descrição'),
        max_length=200,
        help_text='Descrição da transação'
    )
    
    transaction_date = models.DateTimeField(
        _('Data da Transação'),
        default=timezone.now,
        db_index=True
    )
    
    cash_register = models.ForeignKey(
        'CashRegister',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('Caixa')
    )
    
    reference = models.CharField(
        _('Referência'),
        max_length=100,
        blank=True,
        help_text='Número de referência ou código'
    )
    
    commission_amount = models.DecimalField(
        _('Valor da Comissão'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Valor da comissão para o barbeiro'
    )
    
    commission_paid = models.BooleanField(
        _('Comissão Paga'),
        default=False,
        help_text='Se a comissão já foi paga'
    )
    
    class Meta:
        verbose_name = _('Transação')
        verbose_name_plural = _('Transações')
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_type', 'transaction_date']),
            models.Index(fields=['customer', 'transaction_date']),
            models.Index(fields=['barber', 'commission_paid']),
        ]
    
    def __str__(self):
        return f'{self.get_transaction_type_display()} - {self.amount} ({self.transaction_date})'
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self._validate_cash_register()
        super().save(*args, **kwargs)
    
    def _validate_cash_register(self):
        if self.cash_register and not self.cash_register.is_open:
            raise ValidationError(_('O caixa está fechado. Abra o caixa primeiro.'))


class CashRegister(BaseModel):
    """Modelo que representa o caixa da barbearia."""
    
    class Status(models.TextChoices):
        OPEN = 'open', 'Aberto'
        CLOSED = 'closed', 'Fechado'
    
    opened_at = models.DateTimeField(
        _('Aberto em'),
        default=timezone.now,
        db_index=True
    )
    
    closed_at = models.DateTimeField(
        _('Fechado em'),
        blank=True,
        null=True
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True
    )
    
    opening_balance = models.DecimalField(
        _('Saldo Inicial'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Saldo inicial em dinheiro'
    )
    
    closing_balance = models.DecimalField(
        _('Saldo Final'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Saldo final em dinheiro'
    )
    
    total_income = models.DecimalField(
        _('Total de Receitas'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    total_expense = models.DecimalField(
        _('Total de Despesas'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    total_commission = models.DecimalField(
        _('Total de Comissões'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    expected_balance = models.DecimalField(
        _('Saldo Esperado'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Saldo esperado = Saldo Inicial + Receitas - Despesas'
    )
    
    opened_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='opened_registers',
        verbose_name=_('Aberto por')
    )
    
    closed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_registers',
        verbose_name=_('Fechado por')
    )
    
    notes = models.TextField(
        _('Observações'),
        max_length=500,
        blank=True,
        help_text='Observações sobre o caixa'
    )
    
    class Meta:
        verbose_name = _('Caixa')
        verbose_name_plural = _('Caixas')
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['status', 'opened_at']),
        ]
    
    def __str__(self):
        return f'Caixa {self.id} - {self.get_status_display()} ({self.opened_at})'
    
    @property
    def is_open(self):
        return self.status == self.Status.OPEN
    
    def close(self, user, notes=''):
        if not self.is_open:
            raise InvalidStatusTransition(_('O caixa já está fechado.'))
        
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.closed_by = user
        self.expected_balance = self.opening_balance + self.total_income - self.total_expense
        self.notes = notes
        self.save(update_fields=['status', 'closed_at', 'closed_by', 'expected_balance', 'notes'])
    
    def update_totals(self):
        transactions = self.transactions.all()
        
        self.total_income = transactions.filter(
            transaction_type=Transaction.TransactionType.INCOME
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        self.total_expense = transactions.filter(
            transaction_type=Transaction.TransactionType.EXPENSE
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        self.total_commission = transactions.filter(
            transaction_type=Transaction.TransactionType.COMMISSION
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        self.save(update_fields=['total_income', 'total_expense', 'total_commission'])


class Commission(BaseModel):
    """Modelo que representa a comissão de um barbeiro."""
    
    class CommissionStatus(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PAID = 'paid', 'Pago'
        CANCELLED = 'cancelled', 'Cancelado'
    
    barber = models.ForeignKey(
        'barbers.Barber',
        on_delete=models.PROTECT,
        related_name='commissions',
        verbose_name=_('Barbeiro')
    )
    
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.PROTECT,
        related_name='commission',
        verbose_name=_('Agendamento')
    )
    
    amount = models.DecimalField(
        _('Valor'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive]
    )
    
    percentage = models.DecimalField(
        _('Percentual'),
        max_digits=5,
        decimal_places=2,
        help_text='Percentual aplicado'
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=CommissionStatus.choices,
        default=CommissionStatus.PENDING,
        db_index=True
    )
    
    paid_at = models.DateTimeField(
        _('Pago em'),
        blank=True,
        null=True
    )
    
    paid_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paid_commissions',
        verbose_name=_('Pago por')
    )
    
    period_start = models.DateField(
        _('Período Início'),
        help_text='Início do período de competência'
    )
    
    period_end = models.DateField(
        _('Período Fim'),
        help_text='Fim do período de competência'
    )
    
    class Meta:
        verbose_name = _('Comissão')
        verbose_name_plural = _('Comissões')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['barber', 'status']),
            models.Index(fields=['status', 'paid_at']),
        ]
    
    def __str__(self):
        return f'Comissão de {self.barber} - R$ {self.amount}'
    
    def mark_as_paid(self, user):
        if self.status != self.CommissionStatus.PENDING:
            raise InvalidStatusTransition(_('Apenas comissões pendentes podem ser pagas.'))
        
        self.status = self.CommissionStatus.PAID
        self.paid_at = timezone.now()
        self.paid_by = user
        self.save(update_fields=['status', 'paid_at', 'paid_by'])


class FixedExpense(BaseModel):
    """Modelo para gastos fixos da barbearia."""
    
    class ExpenseCategory(models.TextChoices):
        RENT = 'rent', 'Aluguel'
        SALARY = 'salary', 'Salário'
        WATER = 'water', 'Água'
        ELECTRICITY = 'electricity', 'Energia'
        INTERNET = 'internet', 'Internet'
        SUPPLIES = 'supplies', 'Suprimentos'
        MARKETING = 'marketing', 'Marketing'
        MAINTENANCE = 'maintenance', 'Manutenção'
        INSURANCE = 'insurance', 'Seguro'
        OTHER = 'other', 'Outros'
    
    class Frequency(models.TextChoices):
        MONTHLY = 'monthly', 'Mensal'
        QUARTERLY = 'quarterly', 'Trimestral'
        SEMESTER = 'semester', 'Semestral'
        ANNUAL = 'annual', 'Anual'
        ONCE = 'once', 'Única'
    
    name = models.CharField(
        _('Nome do Gasto'),
        max_length=100,
        db_index=True
    )
    
    category = models.CharField(
        _('Categoria'),
        max_length=20,
        choices=ExpenseCategory.choices,
        db_index=True
    )
    
    amount = models.DecimalField(
        _('Valor'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive],
        help_text='Valor do gasto'
    )
    
    frequency = models.CharField(
        _('Frequência'),
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.MONTHLY,
        db_index=True
    )
    
    due_day = models.PositiveSmallIntegerField(
        _('Dia de Vencimento'),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Dia do mês para vencimento (1-31)'
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=300,
        blank=True,
        help_text='Detalhes adicionais do gasto'
    )
    
    is_active = models.BooleanField(
        _('Ativo'),
        default=True,
        db_index=True
    )
    
    last_charged = models.DateField(
        _('Última Cobrança'),
        blank=True,
        null=True,
        help_text='Data da última cobrança realizada'
    )
    
    next_charge = models.DateField(
        _('Próxima Cobrança'),
        blank=True,
        null=True,
        help_text='Data da próxima cobrança'
    )
    
    class Meta:
        verbose_name = _('Gasto Fixo')
        verbose_name_plural = _('Gastos Fixos')
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['next_charge']),
        ]
    
    def __str__(self):
        return f'{self.name} - R$ {self.amount} ({self.get_frequency_display()})'
    
    def calculate_next_charge(self):
        """Calcula a próxima data de cobrança."""
        from dateutil.relativedelta import relativedelta
        from datetime import date
        
        today = date.today()
        
        if self.last_charged:
            base_date = self.last_charged
        else:
            base_date = self.created_at.date() if self.created_at else today
        
        if self.frequency == self.Frequency.MONTHLY:
            next_date = base_date + relativedelta(months=1)
        elif self.frequency == self.Frequency.QUARTERLY:
            next_date = base_date + relativedelta(months=3)
        elif self.frequency == self.Frequency.SEMESTER:
            next_date = base_date + relativedelta(months=6)
        elif self.frequency == self.Frequency.ANNUAL:
            next_date = base_date + relativedelta(years=1)
        else:  # ONCE
            next_date = None
        
        if next_date:
            try:
                next_date = next_date.replace(day=self.due_day)
            except ValueError:
                next_date = next_date.replace(day=28) + relativedelta(days=4)
                next_date = next_date - relativedelta(days=next_date.day)
        
        return next_date
    
    def charge(self):
        """Registra a cobrança do gasto fixo."""
        from .models import Transaction
        
        transaction = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.EXPENSE,
            payment_method=Transaction.PaymentMethod.CASH,
            amount=self.amount,
            description=f'Gasto Fixo: {self.name} ({self.get_category_display()})',
            transaction_date=timezone.now(),
            reference=f'fixed_expense_{self.id}'
        )
        
        self.last_charged = timezone.now().date()
        self.next_charge = self.calculate_next_charge()
        self.save(update_fields=['last_charged', 'next_charge'])
        
        return transaction
