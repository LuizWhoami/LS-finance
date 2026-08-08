from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin personalizado para o modelo User."""
    
    list_display = [
        'username', 'email', 'get_full_name', 'user_type',
        'phone', 'is_active', 'is_staff', 'date_joined'
    ]
    
    list_filter = [
        'user_type', 'is_active', 'is_staff', 'is_superuser',
        'date_joined'
    ]
    
    search_fields = [
        'username', 'email', 'first_name', 'last_name', 'cpf', 'phone'
    ]
    
    readonly_fields = [
        'last_login', 'date_joined', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informações Pessoais'), {
            'fields': (
                'first_name', 'last_name', 'email', 'cpf',
                'phone', 'birth_date', 'avatar', 'bio'
            )
        }),
        (_('Permissões'), {
            'fields': (
                'user_type', 'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        (_('Datas Importantes'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    ordering = ['-date_joined']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para o modelo UserProfile."""
    
    list_display = ['user', 'get_user_email', 'email_notifications', 'whatsapp_notifications']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    list_filter = ['email_notifications', 'sms_notifications', 'whatsapp_notifications', 'language']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Usuário'), {
            'fields': ('user',)
        }),
        (_('Preferências de Notificação'), {
            'fields': ('email_notifications', 'sms_notifications', 'whatsapp_notifications')
        }),
        (_('Preferências do Sistema'), {
            'fields': ('language', 'theme')
        }),
        (_('Informações de Endereço'), {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
