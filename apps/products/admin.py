"""
Configuração do admin para o app Products.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import ProductCategory, Product, InventoryMovement


class InventoryMovementInline(admin.TabularInline):
    """Inline para movimentações de estoque."""
    model = InventoryMovement
    extra = 0
    fields = ['movement_type', 'quantity', 'reason', 'created_at']
    readonly_fields = ['created_at']
    can_delete = False
    max_num = 0


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """Admin para o modelo ProductCategory."""
    
    list_display = ['name', 'order', 'is_active']
    search_fields = ['name']
    ordering = ['order', 'name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin para o modelo Product."""
    
    list_display = [
        'name', 'category', 'quantity', 'unit',
        'sale_price', 'is_low_stock_indicator', 'is_active'
    ]
    
    list_filter = ['category', 'unit', 'is_active']
    search_fields = ['name', 'description']
    
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'category', 'description')
        }),
        (_('Estoque'), {
            'fields': ('unit', 'quantity', 'minimum_stock')
        }),
        (_('Valores'), {
            'fields': ('cost_price', 'sale_price')
        }),
        (_('Imagem'), {
            'fields': ('image',)
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    inlines = [InventoryMovementInline]
    
    def is_low_stock_indicator(self, obj):
        """Indicador visual de estoque baixo."""
        if obj.is_low_stock:
            return _('⚠️ Baixo')
        return _('✅ Normal')
    is_low_stock_indicator.short_description = _('Estoque')
    is_low_stock_indicator.admin_order_field = 'quantity'


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    """Admin para o modelo InventoryMovement."""
    
    list_display = ['product', 'movement_type', 'quantity', 'reason', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reason']
    readonly_fields = ['created_at', 'updated_at']
