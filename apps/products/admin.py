from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.contrib import messages

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
    
    actions = ['register_sale']
    
    def register_sale(self, request, queryset):
        """Ação para registrar venda de produtos."""
        from apps.finance.models import Transaction
        count = 0
        for product in queryset:
            if product.quantity > 0:
                Transaction.objects.create(
                    transaction_type='income',
                    payment_method='cash',
                    amount=product.sale_price,
                    description=f'Venda de Produto: {product.name}',
                    transaction_date=timezone.now(),
                    reference=f'product_{product.id}'
                )
                # Reduzir estoque
                product.quantity -= 1
                product.save(update_fields=['quantity'])
                count += 1
        self.message_user(request, f'{count} venda(s) de produtos registradas com sucesso!')
    register_sale.short_description = 'Registrar venda do(s) produto(s) selecionado(s)'


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'reason', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reason']
    readonly_fields = ['created_at', 'updated_at']
