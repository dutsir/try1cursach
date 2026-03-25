import pytest

from apps.products.models import Category, Product


@pytest.mark.django_db
class TestCategoryModel:
    def test_create_category(self):
        cat = Category.objects.create(
            name='Оперативная память',
            slug='operativnaya-pamyat',
            dns_category_slug='17a89a3916404e77/operativnaya-pamyat',
        )
        assert cat.pk is not None
        assert cat.is_active is True
        assert str(cat) == 'Оперативная память'

    def test_auto_slug(self):
        cat = Category.objects.create(name='Мониторы')
        assert cat.slug != ''


@pytest.mark.django_db
class TestProductModel:
    @pytest.fixture
    def category(self):
        return Category.objects.create(name='ОЗУ', slug='ozu')

    def test_create_product(self, category):
        product = Product.objects.create(
            name='Kingston FURY Beast 16GB DDR5',
            slug='kingston-fury-beast-16gb',
            category=category,
            vendor_code='5046553',
            url='https://www.dns-shop.ru/product/5046553/',
        )
        assert product.pk is not None
        assert product.is_active is True
        assert str(product) == 'Kingston FURY Beast 16GB DDR5'
