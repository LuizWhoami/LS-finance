from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'billing_cycle', 'price', 'status', 'total_subscribers', 'is_active']
    list_filter = ['billing_cycle', 'status', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['total_subscribers', 'created_at', 'updated_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'plan', 'start_date', 'end_date', 'status', 'price_paid']
    list_filter = ['status', 'plan', 'start_date']
    search_fields = ['customer__full_name', 'customer__phone', 'plan__name']
    readonly_fields = ['created_at', 'updated_at']
