from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Appointment, AppointmentItem


class AppointmentItemInline(admin.TabularInline):
    model = AppointmentItem
    extra = 1
    fields = ['service', 'price', 'duration_minutes']
    readonly_fields = ['price', 'duration_minutes']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'barber', 'services_list',
        'start_time_formatted', 'end_time_formatted',
        'status', 'payment_status', 'final_price'
    ]
    
    list_filter = ['status', 'payment_status', 'start_time']
    search_fields = ['customer__full_name', 'customer__phone', 'customer__email']
    readonly_fields = ['created_at', 'updated_at', 'cancelled_at', 'completed_at', 'total_duration']
    
    fieldsets = (
        (_('Informações do Agendamento'), {
            'fields': ('customer', 'barber')
        }),
        (_('Data e Horário'), {
            'fields': ('start_time', 'end_time', 'total_duration')
        }),
        (_('Valores'), {
            'fields': ('service_price', 'discount', 'final_price', 'commission_amount')
        }),
        (_('Status'), {
            'fields': ('status', 'payment_status')
        }),
        (_('Avaliação'), {
            'fields': ('rating', 'feedback')
        }),
        (_('Cancelamento'), {
            'fields': ('cancelled_by', 'cancelled_at', 'cancellation_reason')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    inlines = [AppointmentItemInline]
    
    def services_list(self, obj):
        items = obj.items.all()
        if items.exists():
            return ', '.join([item.service.name for item in items])
        return '-'
    services_list.short_description = _('Serviços')
    
    def start_time_formatted(self, obj):
        return obj.start_time.strftime('%d/%m/%Y %H:%M')
    start_time_formatted.short_description = _('Início')
    
    def end_time_formatted(self, obj):
        return obj.end_time.strftime('%d/%m/%Y %H:%M')
    end_time_formatted.short_description = _('Término')


@admin.register(AppointmentItem)
class AppointmentItemAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'service', 'price', 'duration_minutes']
    list_filter = ['service']
    search_fields = ['appointment__customer__full_name', 'service__name']
