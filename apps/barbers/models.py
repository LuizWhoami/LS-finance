"""
Modelos do app Barbers.
Gerencia os barbeiros/profissionais da barbearia.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel, BaseModelWithOrder
from apps.core.validators import validate_phone, validate_percentage
from apps.accounts.models import User


class Barber(BaseModel):
    """
    Modelo que representa um barbeiro/profissional.
    """
    
    class BarberStatus(models.TextChoices):
        ACTIVE = 'active', 'Ativo'
        INACTIVE = 'inactive', 'Inativo'
        ON_VACATION = 'on_vacation', 'Em Férias'
        ON_LEAVE = 'on_leave', 'Afastado'
    
    # Relacionamento com o usuário
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='barber_profile',
        verbose_name=_('Usuário')
    )
    
    # Informações profissionais
    registration_number = models.CharField(
        _('Número de Registro'),
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text='Número de registro profissional (se aplicável)'
    )
    
    specialty = models.CharField(
        _('Especialidade'),
        max_length=100,
        blank=True,
        help_text='Especialidade principal do barbeiro'
    )
    
    bio = models.TextField(
        _('Biografia'),
        max_length=500,
        blank=True,
        help_text='Breve descrição sobre o barbeiro'
    )
    
    experience_years = models.PositiveIntegerField(
        _('Anos de Experiência'),
        default=0,
        help_text='Anos de experiência profissional'
    )
    
    # Comissão
    commission_percentage = models.DecimalField(
        _('Percentual de Comissão'),
        max_digits=5,
        decimal_places=2,
        default=30.00,
        validators=[validate_percentage],
        help_text='Percentual de comissão sobre os serviços'
    )
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=BarberStatus.choices,
        default=BarberStatus.ACTIVE,
        db_index=True
    )
    
    total_services = models.PositiveIntegerField(
        _('Total de Serviços'),
        default=0,
        help_text='Total de serviços realizados'
    )
    
    # Imagem do barbeiro
    image = models.ImageField(
        _('Imagem'),
        upload_to='barbers/%Y/%m/',
        blank=True,
        null=True,
        help_text='Foto do barbeiro'
    )
    
    class Meta:
        verbose_name = _('Barbeiro')
        verbose_name_plural = _('Barbeiros')
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def full_name(self):
        """Retorna o nome completo do barbeiro."""
        return self.user.get_full_name()
    
    @property
    def phone(self):
        """Retorna o telefone do barbeiro."""
        return self.user.phone
    
    @property
    def email(self):
        """Retorna o email do barbeiro."""
        return self.user.email
    
    def increment_services(self):
        """Incrementa o contador de serviços realizados."""
        self.total_services += 1
        self.save(update_fields=['total_services'])


class WorkSchedule(BaseModelWithOrder):
    """
    Horário de trabalho do barbeiro.
    """
    
    class WeekDay(models.IntegerChoices):
        MONDAY = 1, 'Segunda-feira'
        TUESDAY = 2, 'Terça-feira'
        WEDNESDAY = 3, 'Quarta-feira'
        THURSDAY = 4, 'Quinta-feira'
        FRIDAY = 5, 'Sexta-feira'
        SATURDAY = 6, 'Sábado'
        SUNDAY = 7, 'Domingo'
    
    barber = models.ForeignKey(
        Barber,
        on_delete=models.CASCADE,
        related_name='work_schedules',
        verbose_name=_('Barbeiro')
    )
    
    day_of_week = models.PositiveSmallIntegerField(
        _('Dia da Semana'),
        choices=WeekDay.choices,
        db_index=True
    )
    
    start_time = models.TimeField(
        _('Horário de Início'),
        help_text='Horário que o barbeiro começa a trabalhar'
    )
    
    end_time = models.TimeField(
        _('Horário de Término'),
        help_text='Horário que o barbeiro termina de trabalhar'
    )
    
    break_start = models.TimeField(
        _('Início do Intervalo'),
        blank=True,
        null=True,
        help_text='Horário de início do intervalo'
    )
    
    break_end = models.TimeField(
        _('Fim do Intervalo'),
        blank=True,
        null=True,
        help_text='Horário de fim do intervalo'
    )
    
    is_available = models.BooleanField(
        _('Disponível'),
        default=True,
        help_text='Se o barbeiro está disponível neste dia'
    )
    
    class Meta:
        verbose_name = _('Horário de Trabalho')
        verbose_name_plural = _('Horários de Trabalho')
        ordering = ['barber', 'day_of_week', 'order']
        unique_together = [['barber', 'day_of_week']]
    
    def __str__(self):
        return f'{self.barber} - {self.get_day_of_week_display()}'
    
    @property
    def work_duration(self):
        """Retorna a duração total do expediente em horas."""
        delta = self.end_time - self.start_time
        return delta.seconds / 3600
    
    @property
    def break_duration(self):
        """Retorna a duração do intervalo em horas."""
        if self.break_start and self.break_end:
            delta = self.break_end - self.break_start
            return delta.seconds / 3600
        return 0
    
    @property
    def effective_work_hours(self):
        """Retorna as horas efetivas de trabalho (expediente - intervalo)."""
        return self.work_duration - self.break_duration


class TimeOff(BaseModel):
    """
    Períodos de folga, férias ou afastamento do barbeiro.
    """
    
    class TimeOffType(models.TextChoices):
        VACATION = 'vacation', 'Férias'
        SICK_LEAVE = 'sick_leave', 'Licença Médica'
        PERSONAL = 'personal', 'Assunto Pessoal'
        HOLIDAY = 'holiday', 'Feriado'
        OTHER = 'other', 'Outro'
    
    barber = models.ForeignKey(
        Barber,
        on_delete=models.CASCADE,
        related_name='time_offs',
        verbose_name=_('Barbeiro')
    )
    
    type = models.CharField(
        _('Tipo'),
        max_length=20,
        choices=TimeOffType.choices,
        db_index=True
    )
    
    start_date = models.DateField(
        _('Data de Início'),
        db_index=True
    )
    
    end_date = models.DateField(
        _('Data de Término'),
        db_index=True
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=200,
        blank=True,
        help_text='Motivo ou descrição do afastamento'
    )
    
    is_approved = models.BooleanField(
        _('Aprovado'),
        default=False,
        help_text='Se o afastamento foi aprovado'
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_offs',
        verbose_name=_('Aprovado por')
    )
    
    approved_at = models.DateTimeField(
        _('Aprovado em'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('Afastamento')
        verbose_name_plural = _('Afastamentos')
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['barber', 'start_date', 'end_date']),
            models.Index(fields=['type', 'is_approved']),
        ]
    
    def __str__(self):
        return f'{self.barber} - {self.get_type_display()} ({self.start_date} a {self.end_date})'
    
    @property
    def duration_days(self):
        """Retorna o número de dias de afastamento."""
        return (self.end_date - self.start_date).days + 1
