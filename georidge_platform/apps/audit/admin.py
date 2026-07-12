from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "project", "ip_address")
    list_filter = ("action", "timestamp")
    search_fields = ("user__email", "action")
    readonly_fields = ("timestamp",)
