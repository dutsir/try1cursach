import logging

from celery import shared_task

from apps.products.models import Product

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    max_retries=2,
)
def task_detect_anomalies(self, product_id: int) -> dict:
    from .detector import run_full_detection

    anomalies = run_full_detection(product_id)
    return {
        'product_id': product_id,
        'anomalies_found': len(anomalies),
    }


@shared_task
def task_detect_all_anomalies() -> dict:
    products = Product.objects.filter(is_active=True).values_list('pk', flat=True)
    count = 0
    for pk in products:
        task_detect_anomalies.delay(product_id=pk)
        count += 1
    logger.info('Поставлено задач детекции аномалий: %d', count)
    return {'queued': count}
