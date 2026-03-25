import pytest
from decimal import Decimal
from django.utils import timezone

from apps.prices.models import PriceHistory
from apps.products.models import Category, Product


@pytest.mark.django_db
class TestPriceHistoryModel:
    @pytest.fixture
    def product(self):
        cat = Category.objects.create(name='ОЗУ', slug='ozu')
        return Product.objects.create(
            name='Test RAM',
            slug='test-ram',
            category=cat,
            url='https://dns-shop.ru/product/123/',
        )

    def test_create_price_record(self, product):
        record = PriceHistory.objects.create(
            product=product,
            price=Decimal('4999.00'),
            timestamp=timezone.now(),
        )
        assert record.pk is not None
        assert record.is_actual is True
        assert record.source == 'dns'
        assert '4999' in str(record)
