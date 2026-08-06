from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'barber', 'service', 
        'start_time_formatted', 'end_time_formatted',
        'status', 'payment_status', 'final_price'
    ]
    
    list_filter = ['status', 'payment_status', 'start_time']
    search_fields = ['customer__full_name', 'customer__phone', 'service__name']
    readonly_fields = ['created_at', 'updated_at', 'cancelled_at', 'completed_at']
    
    fieldsets = (
        (_('Informações do Agendamento'), {
            'fields': ('customer', 'barber', 'service')
        }),
        (_('Data e Horário'), {
            'fields': ('start_time', 'end_time')
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
    
    def start_time_formatted(self, obj):
        return obj.start_time.strftime('%d/%m/%Y %H:%M')
    start_time_formatted.short_description = _('Início')
    
    def end_time_formatted(self, obj):
        return obj.end_time.strftime('%d/%m/%Y %H:%M')
    end_time_formatted.short_description = _('Término')
