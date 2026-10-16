"""Tests for validators."""

import pytest
from app.utils.validators import (
    validate_positive_number,
    validate_non_negative_number,
    validate_positive_integer,
    validate_non_negative_integer,
    validate_required_text,
    validate_unit,
)


class TestValidatePositiveNumber:
    def test_valid(self):
        is_valid, msg = validate_positive_number(10.5, "Length")
        assert is_valid is True
        assert msg is None

    def test_string_number(self):
        is_valid, msg = validate_positive_number("25.5", "Weight")
        assert is_valid is True

    def test_zero_rejected(self):
        is_valid, msg = validate_positive_number(0, "Length")
        assert is_valid is False
        assert "greater than zero" in msg

    def test_negative_rejected(self):
        is_valid, msg = validate_positive_number(-5, "Length")
        assert is_valid is False
        assert "greater than zero" in msg

    def test_non_numeric_rejected(self):
        is_valid, msg = validate_positive_number("abc", "Length")
        assert is_valid is False
        assert "valid number" in msg

    def test_none_rejected(self):
        is_valid, msg = validate_positive_number(None, "Length")
        assert is_valid is False

    def test_empty_string_rejected(self):
        is_valid, msg = validate_positive_number("", "Length")
        assert is_valid is False


class TestValidateNonNegativeNumber:
    def test_positive_valid(self):
        is_valid, msg = validate_non_negative_number(10, "Rate")
        assert is_valid is True

    def test_zero_valid(self):
        is_valid, msg = validate_non_negative_number(0, "Rate")
        assert is_valid is True

    def test_negative_rejected(self):
        is_valid, msg = validate_non_negative_number(-1, "Rate")
        assert is_valid is False
        assert "cannot be negative" in msg


class TestValidatePositiveInteger:
    def test_valid(self):
        is_valid, msg = validate_positive_integer(5, "Quantity")
        assert is_valid is True

    def test_string_int(self):
        is_valid, msg = validate_positive_integer("10", "Quantity")
        assert is_valid is True

    def test_zero_rejected(self):
        is_valid, msg = validate_positive_integer(0, "Quantity")
        assert is_valid is False

    def test_negative_rejected(self):
        is_valid, msg = validate_positive_integer(-3, "Quantity")
        assert is_valid is False

    def test_float_string_rejected(self):
        is_valid, msg = validate_positive_integer("5.5", "Quantity")
        assert is_valid is False


class TestValidateNonNegativeInteger:
    def test_zero_valid(self):
        is_valid, msg = validate_non_negative_integer(0, "Hours")
        assert is_valid is True

    def test_positive_valid(self):
        is_valid, msg = validate_non_negative_integer(5, "Hours")
        assert is_valid is True

    def test_negative_rejected(self):
        is_valid, msg = validate_non_negative_integer(-1, "Hours")
        assert is_valid is False


class TestValidateRequiredText:
    def test_valid(self):
        is_valid, msg = validate_required_text("ABC Industries", "Customer Name")
        assert is_valid is True

    def test_empty_rejected(self):
        is_valid, msg = validate_required_text("", "Customer Name")
        assert is_valid is False
        assert "required" in msg

    def test_whitespace_only_rejected(self):
        is_valid, msg = validate_required_text("   ", "Customer Name")
        assert is_valid is False


class TestValidateUnit:
    def test_valid_units(self):
        for unit in ["mm", "cm", "in", "ft"]:
            is_valid, msg = validate_unit(unit)
            assert is_valid is True, f"Unit '{unit}' should be valid"

    def test_invalid_unit(self):
        is_valid, msg = validate_unit("meter")
        assert is_valid is False
        assert "Invalid unit" in msg

    def test_empty_unit(self):
        is_valid, msg = validate_unit("")
        assert is_valid is False
