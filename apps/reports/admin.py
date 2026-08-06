"""
Configuração do admin para o app Reports.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ReportTemplate, ReportExecution


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Admin para o modelo ReportTemplate."""
    
    list_display = [
        'name', 'report_type', 'format', 'is_active', 'is_system'
    ]
    
    list_filter = ['report_type', 'format', 'is_active', 'is_system']
    search_fields = ['name', 'description']
    
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'description', 'report_type', 'format')
        }),
        (_('Configuração'), {
            'fields': ('query', 'fields', 'filters')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_system')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )


@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    """Admin para o modelo ReportExecution."""
    
    list_display = [
        'template', 'status', 'rows_count', 'execution_time', 'created_at'
    ]
    
    list_filter = ['status', 'created_at']
    search_fields = ['template__name', 'executed_by__username']
    
    readonly_fields = [
        'created_at', 'updated_at', 'deleted_at',
        'result_file', 'result_data', 'execution_time'
    ]
    
    fieldsets = (
        (_('Informações'), {
            'fields': ('template', 'status')
        }),
        (_('Parâmetros'), {
            'fields': ('parameters',)
        }),
        (_('Resultado'), {
            'fields': ('result_file', 'result_data', 'rows_count')
        }),
        (_('Execução'), {
            'fields': ('execution_time', 'executed_by')
        }),
        (_('Erro'), {
            'fields': ('error_message',)
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
