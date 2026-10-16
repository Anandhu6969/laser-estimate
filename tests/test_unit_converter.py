"""Tests for UnitConverter."""

import pytest
from app.calculations.unit_converter import to_feet, from_feet, SUPPORTED_UNITS


class TestToFeet:
    """Test conversions to feet."""

    def test_mm_to_feet(self):
        # 304.8 mm = 1 ft
        assert to_feet(304.8, "mm") == pytest.approx(1.0)

    def test_cm_to_feet(self):
        # 30.48 cm = 1 ft
        assert to_feet(30.48, "cm") == pytest.approx(1.0)

    def test_inch_to_feet(self):
        # 12 in = 1 ft
        assert to_feet(12, "in") == pytest.approx(1.0)

    def test_feet_to_feet(self):
        assert to_feet(5.0, "ft") == pytest.approx(5.0)

    def test_120cm_to_feet(self):
        # 120 / 30.48 ≈ 3.937007874
        result = to_feet(120, "cm")
        assert result == pytest.approx(3.937007874, rel=1e-6)

    def test_80cm_to_feet(self):
        # 80 / 30.48 ≈ 2.624671916
        result = to_feet(80, "cm")
        assert result == pytest.approx(2.624671916, rel=1e-6)

    def test_1000mm_to_feet(self):
        # 1000 / 304.8 ≈ 3.280839895
        result = to_feet(1000, "mm")
        assert result == pytest.approx(3.280839895, rel=1e-6)

    def test_24inch_to_feet(self):
        assert to_feet(24, "in") == pytest.approx(2.0)

    def test_zero_value(self):
        assert to_feet(0, "cm") == 0.0

    def test_unit_case_insensitive(self):
        assert to_feet(30.48, "CM") == pytest.approx(1.0)
        assert to_feet(304.8, "MM") == pytest.approx(1.0)
        assert to_feet(12, "IN") == pytest.approx(1.0)
        assert to_feet(1, "FT") == pytest.approx(1.0)

    def test_unit_with_whitespace(self):
        assert to_feet(30.48, " cm ") == pytest.approx(1.0)

    def test_unsupported_unit_raises(self):
        with pytest.raises(ValueError, match="Unsupported unit"):
            to_feet(100, "meter")

    def test_unsupported_unit_empty(self):
        with pytest.raises(ValueError):
            to_feet(100, "")


class TestFromFeet:
    """Test conversions from feet."""

    def test_feet_to_mm(self):
        assert from_feet(1.0, "mm") == pytest.approx(304.8)

    def test_feet_to_cm(self):
        assert from_feet(1.0, "cm") == pytest.approx(30.48)

    def test_feet_to_inch(self):
        assert from_feet(1.0, "in") == pytest.approx(12.0)

    def test_feet_to_feet(self):
        assert from_feet(1.0, "ft") == pytest.approx(1.0)

    def test_roundtrip_mm(self):
        original = 500.0
        ft = to_feet(original, "mm")
        back = from_feet(ft, "mm")
        assert back == pytest.approx(original)

    def test_roundtrip_cm(self):
        original = 120.0
        ft = to_feet(original, "cm")
        back = from_feet(ft, "cm")
        assert back == pytest.approx(original)

    def test_unsupported_unit_raises(self):
        with pytest.raises(ValueError, match="Unsupported unit"):
            from_feet(1.0, "meter")


class TestSupportedUnits:
    """Test that SUPPORTED_UNITS is correct."""

    def test_contains_expected(self):
        assert "mm" in SUPPORTED_UNITS
        assert "cm" in SUPPORTED_UNITS
        assert "in" in SUPPORTED_UNITS
        assert "ft" in SUPPORTED_UNITS

    def test_length(self):
        assert len(SUPPORTED_UNITS) == 4
