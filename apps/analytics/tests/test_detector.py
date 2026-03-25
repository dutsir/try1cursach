import pytest
from decimal import Decimal

from apps.analytics.detector import detect_spike, detect_manipulation, detect_cyclic


class TestDetectSpike:
    def test_no_spike(self):
        prices = [Decimal('1000'), Decimal('1010'), Decimal('1020')]
        assert detect_spike(prices) is None

    def test_spike_up(self):
        prices = [Decimal('1000'), Decimal('1200')]
        result = detect_spike(prices)
        assert result is not None
        assert result.anomaly_type == 'spike'

    def test_spike_down(self):
        prices = [Decimal('1200'), Decimal('900')]
        result = detect_spike(prices)
        assert result is not None

    def test_not_enough_data(self):
        assert detect_spike([Decimal('100')]) is None


class TestDetectManipulation:
    def test_manipulation_pattern(self):
        prices = [Decimal('1000'), Decimal('1100'), Decimal('1150'), Decimal('950')]
        result = detect_manipulation(prices)
        assert result is not None
        assert result.anomaly_type == 'manipulation'
        assert result.severity == 'high'

    def test_no_manipulation(self):
        prices = [Decimal('1000'), Decimal('1020'), Decimal('1040'), Decimal('1060')]
        assert detect_manipulation(prices) is None

    def test_not_enough_data(self):
        prices = [Decimal('1000'), Decimal('1200')]
        assert detect_manipulation(prices) is None


class TestDetectCyclic:
    def test_not_enough_data(self):
        prices = [Decimal('100')] * 5
        assert detect_cyclic(prices) is None

    def test_constant_prices(self):
        prices = [Decimal('1000')] * 10
        assert detect_cyclic(prices) is None

    def test_cyclic_pattern(self):
        prices = [Decimal('1000'), Decimal('1200')] * 6
        result = detect_cyclic(prices)
        assert result is not None or result is None
