from django.contrib import admin
from .models import ConnectionProfile


@admin.register(ConnectionProfile)
class ConnectionProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "connection_type", "host", "database", "created_at")
    list_filter = ("connection_type",)
