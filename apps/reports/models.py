"""
Modelos do app Reports.
Gerencia relatórios e análises do sistema.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class ReportTemplate(BaseModel):
    """
    Modelo que representa um template de relatório.
    """
    
    class ReportType(models.TextChoices):
        FINANCIAL = 'financial', 'Financeiro'
        SALES = 'sales', 'Vendas'
        APPOINTMENTS = 'appointments', 'Agendamentos'
        CUSTOMERS = 'customers', 'Clientes'
        BARBERS = 'barbers', 'Barbeiros'
        SERVICES = 'services', 'Serviços'
        PRODUCTS = 'products', 'Produtos'
        SUBSCRIPTIONS = 'subscriptions', 'Assinaturas'
        CUSTOM = 'custom', 'Personalizado'
    
    class ReportFormat(models.TextChoices):
        HTML = 'html', 'HTML'
        PDF = 'pdf', 'PDF'
        CSV = 'csv', 'CSV'
        EXCEL = 'excel', 'Excel'
        JSON = 'json', 'JSON'
    
    name = models.CharField(
        _('Nome'),
        max_length=100,
        db_index=True
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=500,
        blank=True,
        help_text='Descrição do relatório'
    )
    
    report_type = models.CharField(
        _('Tipo de Relatório'),
        max_length=20,
        choices=ReportType.choices,
        db_index=True
    )
    
    format = models.CharField(
        _('Formato'),
        max_length=10,
        choices=ReportFormat.choices,
        default=ReportFormat.HTML
    )
    
    query = models.TextField(
        _('Query'),
        blank=True,
        help_text='Query SQL personalizada (para relatórios customizados)'
    )
    
    fields = models.JSONField(
        _('Campos'),
        default=list,
        help_text='Lista de campos a serem exibidos no relatório'
    )
    
    filters = models.JSONField(
        _('Filtros'),
        default=dict,
        blank=True,
        help_text='Filtros disponíveis para o relatório'
    )
    
    is_active = models.BooleanField(
        _('Ativo'),
        default=True,
        db_index=True
    )
    
    is_system = models.BooleanField(
        _('Sistema'),
        default=False,
        help_text='Relatório padrão do sistema'
    )
    
    class Meta:
        verbose_name = _('Template de Relatório')
        verbose_name_plural = _('Templates de Relatórios')
        ordering = ['report_type', 'name']
    
    def __str__(self):
        return f'{self.name} ({self.get_report_type_display()})'


class ReportExecution(BaseModel):
    """
    Histórico de execuções de relatórios.
    """
    
    class ExecutionStatus(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PROCESSING = 'processing', 'Processando'
        COMPLETED = 'completed', 'Concluído'
        FAILED = 'failed', 'Falhou'
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.PROTECT,
        related_name='executions',
        verbose_name=_('Template')
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
        db_index=True
    )
    
    parameters = models.JSONField(
        _('Parâmetros'),
        default=dict,
        help_text='Parâmetros usados na execução'
    )
    
    result_file = models.FileField(
        _('Arquivo Resultado'),
        upload_to='reports/%Y/%m/',
        blank=True,
        null=True,
        help_text='Arquivo gerado pelo relatório'
    )
    
    result_data = models.JSONField(
        _('Dados Resultado'),
        blank=True,
        null=True,
        help_text='Dados do relatório em formato JSON'
    )
    
    rows_count = models.PositiveIntegerField(
        _('Linhas Geradas'),
        default=0,
        help_text='Número de linhas no relatório'
    )
    
    execution_time = models.DurationField(
        _('Tempo de Execução'),
        blank=True,
        null=True,
        help_text='Tempo gasto para gerar o relatório'
    )
    
    error_message = models.TextField(
        _('Mensagem de Erro'),
        blank=True,
        help_text='Mensagem de erro se a execução falhou'
    )
    
    executed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_executed',
        verbose_name=_('Executado por')
    )
    
    class Meta:
        verbose_name = _('Execução de Relatório')
        verbose_name_plural = _('Execuções de Relatórios')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.template} - {self.created_at} ({self.get_status_display()})'
