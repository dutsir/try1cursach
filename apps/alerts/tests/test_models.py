import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from apps.alerts.models import Subscription, Notification
from apps.products.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
class TestSubscriptionModel:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='sub_user', email='sub@test.com', password='pass123',
        )

    @pytest.fixture
    def product(self):
        cat = Category.objects.create(name='ОЗУ', slug='ozu')
        return Product.objects.create(
            name='Test RAM', slug='test-ram', category=cat,
            url='https://dns-shop.ru/product/1/',
        )

    def test_create_subscription(self, user, product):
        sub = Subscription.objects.create(
            user=user, product=product, target_price=Decimal('3000.00'),
        )
        assert sub.is_active is True
        assert 'Test RAM' in str(sub)

    def test_unique_together(self, user, product):
        Subscription.objects.create(
            user=user, product=product, target_price=Decimal('3000.00'),
        )
        with pytest.raises(Exception):
            Subscription.objects.create(
                user=user, product=product, target_price=Decimal('2000.00'),
            )
