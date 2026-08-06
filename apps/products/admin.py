from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ProductCategory, Product, InventoryMovement


class InventoryMovementInline(admin.TabularInline):
    model = InventoryMovement
    extra = 0
    fields = ['movement_type', 'quantity', 'reason', 'created_at']
    readonly_fields = ['created_at']
    can_delete = False
    max_num = 0


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    search_fields = ['name']
    ordering = ['order', 'name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'quantity', 'unit',
        'sale_price', 'is_low_stock_indicator', 'is_active'
    ]
    
    list_filter = ['category', 'unit', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
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
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    inlines = [InventoryMovementInline]
    
    def is_low_stock_indicator(self, obj):
        if obj.is_low_stock:
            return '⚠️ Baixo'
        return '✅ Normal'
    is_low_stock_indicator.short_description = 'Estoque'
