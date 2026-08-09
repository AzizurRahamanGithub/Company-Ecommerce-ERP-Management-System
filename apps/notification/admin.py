# yourapp/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, NotificationRecipient
from .services import send_now, schedule

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "notification_title", "target_users", "status", "is_scheduled", "schedule_time", "sent_at", "created_at")
    list_filter = ("status", "is_scheduled", "target_users", "created_at")
    search_fields = ("notification_title", "notification_message")
    actions = ["action_send_now", "action_schedule"]

    @admin.action(description="Send now (instant)")
    def action_send_now(self, request, queryset):
        for n in queryset:
            n.is_scheduled = False
            n.schedule_time = None
            send_now(n)

    @admin.action(description="Queue (use existing schedule_time)")
    def action_schedule(self, request, queryset):
        for n in queryset:
            schedule(n)

@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ("id", "notification", "user", "delivered_at", "read_at", "created_at")
    list_filter = ("delivered_at", "read_at", "created_at")
    search_fields = ("notification__notification_title", "user__email")
