from django.contrib import admin

from .models import PriceHistory


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'price', 'old_price', 'source', 'is_actual', 'timestamp')
    list_filter = ('source', 'is_actual', 'timestamp')
    search_fields = ('product__name',)
    raw_id_fields = ('product',)
    date_hierarchy = 'timestamp'
