from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Transaction, CashRegister, Commission


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fields = ['transaction_type', 'payment_method', 'amount', 'description', 'transaction_date']
    readonly_fields = ['transaction_date']
    can_delete = False
    max_num = 0


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_type', 'amount', 'payment_method', 
        'customer', 'barber', 'transaction_date'
    ]
    
    list_filter = ['transaction_type', 'payment_method', 'transaction_date']
    search_fields = ['description', 'reference', 'customer__full_name']
    
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        (_('Informações da Transação'), {
            'fields': ('transaction_type', 'payment_method', 'amount', 'description')
        }),
        (_('Relacionamentos'), {
            'fields': ('appointment', 'customer', 'barber', 'cash_register')
        }),
        (_('Data'), {
            'fields': ('transaction_date',)
        }),
        (_('Comissão'), {
            'fields': ('commission_amount', 'commission_paid')
        }),
        (_('Referência'), {
            'fields': ('reference',)
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'status', 'opened_at', 'closed_at',
        'opening_balance', 'closing_balance', 'opened_by'
    ]
    
    list_filter = ['status', 'opened_at']
    search_fields = ['opened_by__username']
    
    readonly_fields = [
        'opened_at', 'closed_at', 'total_income', 'total_expense',
        'total_commission', 'expected_balance', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Abertura'), {
            'fields': ('opened_at', 'opened_by', 'opening_balance')
        }),
        (_('Fechamento'), {
            'fields': ('closed_at', 'closed_by', 'closing_balance', 'expected_balance')
        }),
        (_('Totais'), {
            'fields': ('total_income', 'total_expense', 'total_commission')
        }),
        (_('Observações'), {
            'fields': ('notes',)
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    inlines = [TransactionInline]


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['barber', 'amount', 'percentage', 'status']
    list_filter = ['status']
    search_fields = ['barber__user__first_name', 'barber__user__last_name']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Informações'), {
            'fields': ('barber', 'appointment', 'amount', 'percentage')
        }),
        (_('Status'), {
            'fields': ('status', 'paid_at', 'paid_by')
        }),
        (_('Período'), {
            'fields': ('period_start', 'period_end')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
