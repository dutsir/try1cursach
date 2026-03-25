from django.contrib import admin

from .models import Anomaly


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ('product', 'anomaly_type', 'severity', 'detected_at', 'resolved')
    list_filter = ('severity', 'anomaly_type', 'resolved', 'detected_at')
    search_fields = ('product__name', 'description')
    raw_id_fields = ('product',)
