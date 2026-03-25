from django.contrib import admin

from .models import Notification, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'target_price', 'is_active', 'created_at')
    list_filter = ('is_active',)
    raw_id_fields = ('user', 'product')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription', 'sent_at')
    list_filter = ('sent_at',)
    raw_id_fields = ('user', 'subscription')
