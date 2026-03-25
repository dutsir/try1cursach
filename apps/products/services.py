import logging
from typing import Any

from django.utils import timezone
from django.utils.text import slugify

from .models import Category, Product

logger = logging.getLogger(__name__)


def get_or_create_product(
    category: Category,
    name: str,
    url: str,
    vendor_code: str = '',
    image_url: str = '',
) -> tuple[Product, bool]:
    product, created = Product.objects.get_or_create(
        url=url,
        defaults={
            'name': name,
            'slug': _make_unique_slug(name, vendor_code),
            'category': category,
            'vendor_code': vendor_code,
            'image_url': image_url,
            'is_active': True,
            'last_parsed_at': timezone.now(),
        },
    )

    if not created:
        product.name = name
        product.last_parsed_at = timezone.now()
        if vendor_code:
            product.vendor_code = vendor_code
        if image_url:
            product.image_url = image_url
        product.save(update_fields=['name', 'last_parsed_at', 'vendor_code', 'image_url', 'updated_at'])

    action = 'Создан' if created else 'Обновлён'
    logger.info('%s товар: %s (id=%d)', action, product.name, product.pk)

    return product, created


def _make_unique_slug(name: str, vendor_code: str) -> str:
    base = slugify(name, allow_unicode=True)[:480]
    slug = f'{base}-{vendor_code}' if vendor_code else base
    if Product.objects.filter(slug=slug).exists():
        slug = f'{slug}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
    return slug


def bulk_update_products(parsed_items: list[dict[str, Any]], category: Category) -> list[Product]:
    products: list[Product] = []
    for item in parsed_items:
        product, _ = get_or_create_product(
            category=category,
            name=item['name'],
            url=item['url'],
            vendor_code=item.get('vendor_code', ''),
            image_url=item.get('image_url', ''),
        )
        products.append(product)
    return products
