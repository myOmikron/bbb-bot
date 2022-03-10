from django.contrib import admin

from api.models import Bot


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ("__str__", "pid")
