import logging
from datetime import datetime
from decimal import Decimal

from celery import shared_task
from django.utils import timezone

from apps.products.models import Category, Product
from apps.products.services import get_or_create_product

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    max_retries=3,
    acks_late=True,
)
def task_parse_category(self, category_id: int) -> dict:
    from .parsers import DNSParser

    try:
        category = Category.objects.get(pk=category_id, is_active=True)
    except Category.DoesNotExist:
        logger.warning('Категория id=%d не найдена или неактивна', category_id)
        return {'status': 'skipped', 'reason': 'category_not_found'}

    logger.info('Начинаем парсинг категории: %s', category.name)

    with DNSParser() as parser:
        parsed_products = parser.parse_category(category.dns_category_slug)

    if not parsed_products:
        logger.warning('Парсер не вернул товаров для категории %s', category.slug)
        return {'status': 'empty', 'category': category.slug}

    saved_count = 0
    for item in parsed_products:
        product, _ = get_or_create_product(
            category=category,
            name=item.name,
            url=item.url,
            vendor_code=item.vendor_code,
            image_url=item.image_url,
        )
        task_save_price.delay(
            product_id=product.pk,
            price=item.price,
            old_price=item.old_price,
            timestamp=timezone.now().isoformat(),
        )
        saved_count += 1

    logger.info(
        'Категория %s: спарсено %d, поставлено задач сохранения цен: %d',
        category.slug, len(parsed_products), saved_count,
    )
    return {'status': 'ok', 'category': category.slug, 'parsed': len(parsed_products)}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_backoff_max=120,
    max_retries=5,
)
def task_save_price(
    self,
    product_id: int,
    price: int,
    old_price: int | None = None,
    timestamp: str | None = None,
) -> dict:
    from .models import PriceHistory

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        logger.warning('Товар id=%d не найден', product_id)
        return {'status': 'skipped'}

    ts = datetime.fromisoformat(timestamp) if timestamp else timezone.now()

    last_record = (
        PriceHistory.objects
        .filter(product=product, is_actual=True)
        .order_by('-timestamp')
        .first()
    )

    price_decimal = Decimal(str(price))
    old_price_decimal = Decimal(str(old_price)) if old_price else None

    if last_record and last_record.price == price_decimal:
        logger.debug('Цена товара %s не изменилась (%s₽)', product.name, price_decimal)
        return {'status': 'unchanged', 'product_id': product_id}

    if last_record:
        last_record.is_actual = False
        last_record.save(update_fields=['is_actual', 'updated_at'])

    PriceHistory.objects.create(
        product=product,
        price=price_decimal,
        old_price=old_price_decimal,
        timestamp=ts,
        is_actual=True,
        source=PriceHistory.Source.DNS,
    )

    logger.info('Сохранена цена для %s: %s₽', product.name, price_decimal)

    from apps.analytics.tasks import task_detect_anomalies
    task_detect_anomalies.delay(product_id=product.pk)

    return {'status': 'saved', 'product_id': product_id, 'price': str(price_decimal)}


@shared_task
def task_parse_all_categories() -> dict:
    categories = Category.objects.filter(is_active=True)
    count = 0
    for cat in categories:
        task_parse_category.delay(cat.pk)
        count += 1
    logger.info('Поставлено задач парсинга для %d категорий', count)
    return {'queued': count}
