"""Tests for SheetCalculator."""

import pytest
from app.calculations.sheet_calculator import (
    STANDARD_MATERIAL_DENSITIES,
    calculate_material_cost,
    calculate_sheet_weight,
    get_material_density,
)


class TestCalculateSheetWeight:
    def test_standard_material_densities_are_in_kg_per_liter(self):
        assert STANDARD_MATERIAL_DENSITIES == {
            "Mild Steel": 7.85,
            "SS 202": 7.80,
            "Stainless Steel": 8.00,
            "C45": 7.85,
            "Japan Sheet": 7.85,
            "GI": 7.85,
            "Aluminium": 2.70,
            "Brass": 8.50,
            "Copper": 8.96,
        }

    def test_aluminium_density_kg_per_liter_calculates_sheet_weight(self):
        # 2.70 kg/L is numerically equal to 2.70 g/cm³.
        assert calculate_sheet_weight(1.0, 1000.0, 2000.0, 2.70) == pytest.approx(5.40)

    def test_mild_steel_default_sheet(self):
        """1 mm × 1000 mm × 2000 mm × 7.85 = 15.70 kg."""
        assert calculate_sheet_weight(1.0, 1000.0, 2000.0, 7.85) == pytest.approx(15.70)

    def test_stainless_steel_default_sheet(self):
        assert calculate_sheet_weight(1.0, 1000.0, 2000.0, 8.00) == pytest.approx(16.00)

    def test_mild_steel_density_lookup(self):
        assert get_material_density("Mild Steel") == pytest.approx(7.85)


class TestCalculateMaterialCost:
    """Test material cost calculations."""

    def test_spec_example(self):
        """25 kg × ₹250/kg = ₹6,250."""
        assert calculate_material_cost(25, 250) == pytest.approx(6250.0)

    def test_zero_weight(self):
        assert calculate_material_cost(0, 250) == pytest.approx(0.0)

    def test_zero_rate(self):
        assert calculate_material_cost(25, 0) == pytest.approx(0.0)

    def test_fractional_weight(self):
        """12.5 kg × ₹200/kg = ₹2,500."""
        assert calculate_material_cost(12.5, 200) == pytest.approx(2500.0)

    def test_large_values(self):
        """100 kg × ₹500/kg = ₹50,000."""
        assert calculate_material_cost(100, 500) == pytest.approx(50000.0)

    def test_negative_weight_raises(self):
        with pytest.raises(ValueError, match="Sheet weight cannot be negative"):
            calculate_material_cost(-5, 250)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="Kilo rate cannot be negative"):
            calculate_material_cost(25, -100)

    def test_different_rates(self):
        """Verify different configurable rates produce correct results."""
        assert calculate_material_cost(10, 300) == pytest.approx(3000.0)
        assert calculate_material_cost(10, 350) == pytest.approx(3500.0)
        assert calculate_material_cost(10, 200) == pytest.approx(2000.0)
