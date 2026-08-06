from django.contrib import admin
from .models import Customer, CustomerHistory

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'status', 'total_visits']
    search_fields = ['full_name', 'cpf', 'phone', 'email']

@admin.register(CustomerHistory)
class CustomerHistoryAdmin(admin.ModelAdmin):
    list_display = ['customer', 'type', 'description', 'created_at']
