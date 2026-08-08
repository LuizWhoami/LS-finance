from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Barber, WorkSchedule, TimeOff


class WorkScheduleInline(admin.TabularInline):
    model = WorkSchedule
    extra = 1
    fields = ['day_of_week', 'start_time', 'end_time', 'break_start', 'break_end', 'is_available']


class TimeOffInline(admin.TabularInline):
    model = TimeOff
    extra = 0
    fields = ['type', 'start_date', 'end_date', 'description', 'is_approved']
    readonly_fields = ['approved_by', 'approved_at']


@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'full_name', 'phone', 'specialty', 'status',
        'total_services', 'is_active'
    ]
    
    list_filter = [
        'status', 'is_active', 'experience_years',
    ]
    
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'user__email', 'user__phone', 'registration_number'
    ]
    
    readonly_fields = [
        'total_services', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        (_('Informações Pessoais'), {
            'fields': ('user', 'registration_number')
        }),
        (_('Informações Profissionais'), {
            'fields': ('specialty', 'bio', 'experience_years')
        }),
        (_('Imagem'), {
            'fields': ('image',)
        }),
        (_('Comissão'), {
            'fields': ('commission_percentage',)
        }),
        (_('Status'), {
            'fields': ('status', 'is_active')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    inlines = [WorkScheduleInline, TimeOffInline]
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = _('Nome Completo')
    
    def phone(self, obj):
        return obj.phone
    phone.short_description = _('Telefone')


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['barber', 'day_of_week', 'start_time', 'end_time', 'is_available']
    list_filter = ['day_of_week', 'is_available']
    search_fields = ['barber__user__first_name', 'barber__user__last_name']


@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ['barber', 'type', 'start_date', 'end_date', 'is_approved']
    list_filter = ['type', 'is_approved', 'start_date']
    search_fields = ['barber__user__first_name', 'barber__user__last_name', 'description']
    readonly_fields = ['approved_by', 'approved_at']
