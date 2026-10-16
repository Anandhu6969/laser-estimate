"""Tests for formatters."""

import pytest
from app.utils.formatters import (
    format_indian_currency,
    format_number,
    format_area,
    format_dimensions_ft,
    format_weight,
    format_time,
)


class TestFormatIndianCurrency:
    """Test Indian comma-style currency formatting."""

    def test_small_amount(self):
        assert format_indian_currency(500) == "₹500"

    def test_thousands(self):
        assert format_indian_currency(1000) == "₹1,000"

    def test_spec_example(self):
        assert format_indian_currency(7545) == "₹7,545"

    def test_ten_thousands(self):
        assert format_indian_currency(12345) == "₹12,345"

    def test_lakhs(self):
        # 1,23,456
        assert format_indian_currency(123456) == "₹1,23,456"

    def test_ten_lakhs(self):
        # 12,34,567
        assert format_indian_currency(1234567) == "₹12,34,567"

    def test_crores(self):
        # 1,23,45,678
        assert format_indian_currency(12345678) == "₹1,23,45,678"

    def test_zero(self):
        assert format_indian_currency(0) == "₹0"

    def test_rounds_to_whole(self):
        assert format_indian_currency(7545.50) == "₹7,546"
        assert format_indian_currency(7545.49) == "₹7,545"

    def test_negative(self):
        assert format_indian_currency(-1000) == "-₹1,000"

    def test_custom_symbol(self):
        assert format_indian_currency(1000, "$") == "$1,000"

    def test_material_amount(self):
        assert format_indian_currency(6250) == "₹6,250"

    def test_large_estimate(self):
        assert format_indian_currency(50000) == "₹50,000"

    def test_very_large(self):
        assert format_indian_currency(100000) == "₹1,00,000"


class TestFormatNumber:
    def test_two_decimals(self):
        assert format_number(3.937007874, 2) == "3.94"

    def test_three_decimals(self):
        assert format_number(3.937007874, 3) == "3.937"

    def test_zero_decimals(self):
        assert format_number(10.33, 0) == "10"

    def test_whole_number(self):
        assert format_number(5.0, 2) == "5.00"


class TestFormatArea:
    def test_spec_example(self):
        assert format_area(10.33) == "10.33 sq.ft"

    def test_whole_number(self):
        assert format_area(12.0) == "12.00 sq.ft"

    def test_small_area(self):
        assert format_area(0.5) == "0.50 sq.ft"


class TestFormatDimensionsFt:
    def test_spec_example(self):
        # 80 cm / 30.48 = 2.62467... rounds to 2.62 (spec showed ~2.63 as approx)
        result = format_dimensions_ft(3.937007874, 2.624671916)
        assert result == "3.94 ft × 2.62 ft"


class TestFormatWeight:
    def test_whole_number(self):
        assert format_weight(25) == "25 kg"

    def test_fractional(self):
        assert format_weight(12.5) == "12.50 kg"

    def test_float_whole(self):
        assert format_weight(25.0) == "25 kg"


class TestFormatTime:
    def test_minutes_only(self):
        assert format_time(30) == "30 minutes"

    def test_one_hour(self):
        assert format_time(60) == "1 hr"

    def test_hours_and_minutes(self):
        assert format_time(80) == "1 hr 20 min"

    def test_zero(self):
        assert format_time(0) == "0 minutes"

    def test_two_hours(self):
        assert format_time(120) == "2 hr"

    def test_large_time(self):
        assert format_time(150) == "2 hr 30 min"
