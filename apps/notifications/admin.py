from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Notification, NotificationSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'type', 'is_read', 'priority', 'created_at']
    list_filter = ['type', 'is_read', 'priority']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user']
    search_fields = ['user__username', 'user__email']
