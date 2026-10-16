"""Tests for HoleCalculator."""

import pytest
from app.calculations.hole_calculator import (
    calculate_hole_cost,
    calculate_total_hole_cost,
)


class TestCalculateHoleCost:
    """Test single hole type cost."""

    def test_spec_example(self):
        """20 × ₹12 = ₹240 (from spec)."""
        assert calculate_hole_cost(20, 12) == pytest.approx(240.0)

    def test_zero_quantity(self):
        assert calculate_hole_cost(0, 12) == pytest.approx(0.0)

    def test_zero_rate(self):
        assert calculate_hole_cost(20, 0) == pytest.approx(0.0)

    def test_single_hole(self):
        assert calculate_hole_cost(1, 10) == pytest.approx(10.0)

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="Hole quantity cannot be negative"):
            calculate_hole_cost(-5, 12)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="Hole rate cannot be negative"):
            calculate_hole_cost(20, -10)


class TestCalculateTotalHoleCost:
    """Test multiple hole types total."""

    def test_spec_example(self):
        """
        5mm: 10 × ₹8 = ₹80
        10mm: 20 × ₹12 = ₹240
        15mm: 5 × ₹15 = ₹75
        Total: ₹395
        """
        holes = [
            {"quantity": 10, "rate": 8},
            {"quantity": 20, "rate": 12},
            {"quantity": 5, "rate": 15},
        ]
        assert calculate_total_hole_cost(holes) == pytest.approx(395.0)

    def test_empty_list(self):
        assert calculate_total_hole_cost([]) == pytest.approx(0.0)

    def test_single_entry(self):
        holes = [{"quantity": 20, "rate": 12}]
        assert calculate_total_hole_cost(holes) == pytest.approx(240.0)

    def test_invalid_entry_raises(self):
        holes = [{"quantity": -5, "rate": 12}]
        with pytest.raises(ValueError):
            calculate_total_hole_cost(holes)

    def test_many_entries(self):
        holes = [
            {"quantity": 100, "rate": 5},
            {"quantity": 50, "rate": 10},
            {"quantity": 25, "rate": 20},
            {"quantity": 10, "rate": 50},
        ]
        # 500 + 500 + 500 + 500 = 2000
        assert calculate_total_hole_cost(holes) == pytest.approx(2000.0)
