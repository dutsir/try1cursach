import pytest
from unittest.mock import MagicMock, patch

from apps.prices.parsers import DNSParser, ParsedProduct


class TestDNSParserUtils:
    def test_clean_price_normal(self):
        assert DNSParser._clean_price('12 499 ₽') == 12499

    def test_clean_price_no_spaces(self):
        assert DNSParser._clean_price('999₽') == 999

    def test_clean_price_empty(self):
        assert DNSParser._clean_price('') is None

    def test_clean_price_no_digits(self):
        assert DNSParser._clean_price('Нет в наличии') is None

    def test_clean_price_with_extra_text(self):
        assert DNSParser._clean_price('от 5 499 ₽/шт') == 5499


class TestParsedProduct:
    def test_dataclass_creation(self):
        p = ParsedProduct(
            name='Test',
            price=1000,
            url='https://dns-shop.ru/product/1/',
            vendor_code='123',
        )
        assert p.name == 'Test'
        assert p.old_price is None
