from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ServiceCategory, Service


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    search_fields = ['name']
    ordering = ['order', 'name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration_minutes', 'status', 'is_active']
    list_filter = ['category', 'status', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['total_performed', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'category', 'description')
        }),
        (_('Valores'), {
            'fields': ('price', 'duration_minutes', 'commission_percentage')
        }),
        (_('Imagem'), {
            'fields': ('image',)
        }),
        (_('Status'), {
            'fields': ('status', 'is_active')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
