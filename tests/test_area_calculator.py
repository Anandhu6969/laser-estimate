"""Tests for AreaCalculator."""

import pytest
from app.calculations.area_calculator import calculate_area


class TestCalculateArea:
    """Test area calculations."""

    def test_spec_example_cm(self):
        """120 cm × 80 cm → ~10.33 sq.ft (from spec)."""
        result = calculate_area(120, "cm", 80, "cm")
        assert result["length_ft"] == pytest.approx(3.937007874, rel=1e-6)
        assert result["width_ft"] == pytest.approx(2.624671916, rel=1e-6)
        assert result["area_sqft"] == pytest.approx(10.334, rel=1e-2)

    def test_feet_direct(self):
        """4 ft × 3 ft = 12 sq.ft exactly."""
        result = calculate_area(4, "ft", 3, "ft")
        assert result["length_ft"] == pytest.approx(4.0)
        assert result["width_ft"] == pytest.approx(3.0)
        assert result["area_sqft"] == pytest.approx(12.0)

    def test_inches(self):
        """24 in × 12 in = 2 ft × 1 ft = 2 sq.ft."""
        result = calculate_area(24, "in", 12, "in")
        assert result["area_sqft"] == pytest.approx(2.0)

    def test_mm(self):
        """304.8 mm × 304.8 mm = 1 ft × 1 ft = 1 sq.ft."""
        result = calculate_area(304.8, "mm", 304.8, "mm")
        assert result["area_sqft"] == pytest.approx(1.0)

    def test_mixed_units(self):
        """1 ft × 12 in = 1 ft × 1 ft = 1 sq.ft."""
        result = calculate_area(1, "ft", 12, "in")
        assert result["area_sqft"] == pytest.approx(1.0)

    def test_mixed_cm_inch(self):
        """30.48 cm × 12 in = 1 ft × 1 ft = 1 sq.ft."""
        result = calculate_area(30.48, "cm", 12, "in")
        assert result["area_sqft"] == pytest.approx(1.0)

    def test_zero_length_raises(self):
        with pytest.raises(ValueError, match="Length must be greater than zero"):
            calculate_area(0, "cm", 80, "cm")

    def test_zero_width_raises(self):
        with pytest.raises(ValueError, match="Width must be greater than zero"):
            calculate_area(120, "cm", 0, "cm")

    def test_negative_length_raises(self):
        with pytest.raises(ValueError, match="Length must be greater than zero"):
            calculate_area(-10, "cm", 80, "cm")

    def test_negative_width_raises(self):
        with pytest.raises(ValueError, match="Width must be greater than zero"):
            calculate_area(120, "cm", -5, "cm")

    def test_invalid_unit_raises(self):
        with pytest.raises(ValueError, match="Unsupported unit"):
            calculate_area(120, "meter", 80, "cm")

    def test_returns_dict_keys(self):
        result = calculate_area(100, "cm", 50, "cm")
        assert "length_ft" in result
        assert "width_ft" in result
        assert "area_sqft" in result

    def test_precision_not_lost(self):
        """Verify full precision is maintained, not prematurely rounded."""
        result = calculate_area(120, "cm", 80, "cm")
        # Should not be exactly 10.33 (that's rounded)
        assert result["area_sqft"] != 10.33
        # But should be close
        assert abs(result["area_sqft"] - 10.33) < 0.01
