"""Tests for CuttingCalculator."""

import pytest
from app.calculations.cutting_calculator import (
    time_to_minutes,
    calculate_cutting_cost,
)


class TestTimeToMinutes:
    """Test time conversion."""

    def test_hours_only(self):
        assert time_to_minutes(hours=2) == 120.0

    def test_minutes_only(self):
        assert time_to_minutes(minutes=30) == 30.0

    def test_hours_and_minutes(self):
        """1 hour 20 minutes = 80 minutes (from spec)."""
        assert time_to_minutes(hours=1, minutes=20) == 80.0

    def test_zero(self):
        assert time_to_minutes(hours=0, minutes=0) == 0.0

    def test_negative_hours_raises(self):
        with pytest.raises(ValueError, match="Hours cannot be negative"):
            time_to_minutes(hours=-1, minutes=0)

    def test_negative_minutes_raises(self):
        with pytest.raises(ValueError, match="Minutes cannot be negative"):
            time_to_minutes(hours=0, minutes=-5)


class TestCalculateCuttingCost:
    """Test cutting cost calculations."""

    def test_spec_examples(self):
        """All examples from the spec."""
        assert calculate_cutting_cost(10, 30) == pytest.approx(300.0)
        assert calculate_cutting_cost(30, 30) == pytest.approx(900.0)
        assert calculate_cutting_cost(60, 30) == pytest.approx(1800.0)
        assert calculate_cutting_cost(90, 30) == pytest.approx(2700.0)

    def test_zero_minutes(self):
        assert calculate_cutting_cost(0, 30) == pytest.approx(0.0)

    def test_zero_rate(self):
        assert calculate_cutting_cost(30, 0) == pytest.approx(0.0)

    def test_different_rates(self):
        """Verify configurable rates work correctly."""
        assert calculate_cutting_cost(30, 25) == pytest.approx(750.0)
        assert calculate_cutting_cost(30, 35) == pytest.approx(1050.0)
        assert calculate_cutting_cost(30, 40) == pytest.approx(1200.0)

    def test_negative_minutes_raises(self):
        with pytest.raises(ValueError, match="Cutting time cannot be negative"):
            calculate_cutting_cost(-10, 30)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="Cutting rate cannot be negative"):
            calculate_cutting_cost(30, -10)

    def test_fractional_minutes(self):
        """15.5 minutes × ₹30 = ₹465."""
        assert calculate_cutting_cost(15.5, 30) == pytest.approx(465.0)
