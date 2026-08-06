from django.contrib import admin
from .models import Barber, WorkSchedule, TimeOff

@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'status', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__username']

@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['barber', 'day_of_week', 'start_time', 'end_time']

@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ['barber', 'type', 'start_date', 'end_date', 'is_approved']
