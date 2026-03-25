import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def task_check_subscriptions() -> dict:
    from apps.prices.models import PriceHistory
    from .models import Notification, Subscription

    subscriptions = (
        Subscription.objects
        .filter(is_active=True)
        .select_related('user', 'product')
    )

    notified = 0
    for sub in subscriptions:
        last_price = (
            PriceHistory.objects
            .filter(product=sub.product, is_actual=True)
            .order_by('-timestamp')
            .first()
        )
        if not last_price:
            continue

        if last_price.price <= sub.target_price:
            message = (
                f'Цена на «{sub.product.name}» упала до {last_price.price}₽ '
                f'(ваша целевая: {sub.target_price}₽). '
                f'Ссылка: {sub.product.url}'
            )
            Notification.objects.create(
                user=sub.user,
                subscription=sub,
                message=message,
            )
            sub.is_active = False
            sub.save(update_fields=['is_active', 'updated_at'])
            notified += 1
            logger.info(
                'Уведомление для %s: %s — %s₽',
                sub.user.username, sub.product.name, last_price.price,
            )

    logger.info('Проверка подписок завершена: уведомлений создано %d', notified)
    return {'notified': notified}
