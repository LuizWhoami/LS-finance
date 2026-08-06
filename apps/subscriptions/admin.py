"""
Configuração do admin para o app Subscriptions.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Plan, Subscription, SubscriptionHistory


class SubscriptionInline(admin.TabularInline):
    """Inline para assinaturas do plano."""
    model = Subscription
    extra = 0
    fields = ['customer', 'status', 'start_date', 'end_date']
    readonly_fields = ['start_date', 'end_date']
    can_delete = False
    max_num = 0


class SubscriptionHistoryInline(admin.TabularInline):
    """Inline para histórico da assinatura."""
    model = SubscriptionHistory
    extra = 0
    fields = ['action', 'description', 'created_at']
    readonly_fields = ['created_at']
    can_delete = False
    max_num = 0


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin para o modelo Plan."""
    
    list_display = [
        'name', 'billing_cycle', 'price', 'discount_percentage',
        'free_services_per_month', 'status', 'total_subscribers'
    ]
    
    list_filter = ['billing_cycle', 'status', 'is_active']
    search_fields = ['name', 'description']
    
    readonly_fields = ['total_subscribers', 'created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        (_('Informações do Plano'), {
            'fields': ('name', 'description', 'billing_cycle')
        }),
        (_('Valores'), {
            'fields': ('price', 'setup_fee', 'discount_percentage')
        }),
        (_('Benefícios'), {
            'fields': ('free_services_per_month', 'priority_booking', 'exclusive_services')
        }),
        (_('Status'), {
            'fields': ('status', 'is_active')
        }),
        (_('Métricas'), {
            'fields': ('total_subscribers',)
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    filter_horizontal = ['exclusive_services']
    inlines = [SubscriptionInline]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin para o modelo Subscription."""
    
    list_display = [
        'customer', 'plan', 'status', 'start_date', 'end_date',
        'next_billing_date', 'price_paid'
    ]
    
    list_filter = ['status', 'plan', 'start_date']
    search_fields = ['customer__full_name', 'customer__phone', 'plan__name']
    
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        (_('Informações da Assinatura'), {
            'fields': ('customer', 'plan')
        }),
        (_('Datas'), {
            'fields': ('start_date', 'end_date', 'next_billing_date', 'cancelled_at')
        }),
        (_('Valores'), {
            'fields': ('price_paid', 'setup_fee_paid')
        }),
        (_('Status e Benefícios'), {
            'fields': ('status', 'free_services_used', 'last_free_service_used')
        }),
        (_('Pagamento'), {
            'fields': ('payment_method', 'auto_renew')
        }),
        (_('Observações'), {
            'fields': ('notes',)
        }),
        (_('Datas de Sistema'), {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    inlines = [SubscriptionHistoryInline]
    
    actions = ['activate_subscriptions', 'suspend_subscriptions', 'cancel_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        """Action para ativar assinaturas."""
        count = 0
        for subscription in queryset:
            try:
                subscription.activate()
                count += 1
            except Exception as e:
                self.message_user(request, f'Erro ao ativar {subscription}: {e}')
        self.message_user(request, f'{count} assinatura(s) ativada(s).')
    activate_subscriptions.short_description = _('Ativar assinaturas selecionadas')
    
    def suspend_subscriptions(self, request, queryset):
        """Action para suspender assinaturas."""
        count = 0
        for subscription in queryset:
            try:
                subscription.suspend('Suspenso pelo admin')
                count += 1
            except Exception as e:
                self.message_user(request, f'Erro ao suspender {subscription}: {e}')
        self.message_user(request, f'{count} assinatura(s) suspensa(s).')
    suspend_subscriptions.short_description = _('Suspender assinaturas selecionadas')
    
    def cancel_subscriptions(self, request, queryset):
        """Action para cancelar assinaturas."""
        count = 0
        for subscription in queryset:
            try:
                subscription.cancel('Cancelado pelo admin')
                count += 1
            except Exception as e:
                self.message_user(request, f'Erro ao cancelar {subscription}: {e}')
        self.message_user(request, f'{count} assinatura(s) cancelada(s).')
    cancel_subscriptions.short_description = _('Cancelar assinaturas selecionadas')


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    """Admin para o modelo SubscriptionHistory."""
    
    list_display = ['subscription', 'action', 'description', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['subscription__customer__full_name', 'description']
    readonly_fields = ['created_at']
