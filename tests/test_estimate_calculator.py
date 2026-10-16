"""Tests for EstimateCalculator."""

import pytest
from app.calculations.estimate_calculator import (
    calculate_estimate,
    calculate_simple_estimate,
    calculate_design_heavy_estimate,
)


class TestCalculateEstimate:
    """Test final estimate calculations."""

    def test_spec_example(self):
        """
        Material: ₹6,250
        Cutting: ₹900
        Design: ₹395
        Total: ₹7,545
        """
        result = calculate_estimate(
            material_amount=6250,
            cutting_amount=900,
            design_amount=395,
        )
        assert result["per_piece_amount"] == pytest.approx(7545.0)
        assert result["quantity"] == 1
        assert result["final_amount"] == pytest.approx(7545.0)

    def test_no_design_charges(self):
        """Simple sheet job — no holes."""
        result = calculate_estimate(
            material_amount=6250,
            cutting_amount=900,
        )
        assert result["per_piece_amount"] == pytest.approx(7150.0)
        assert result["final_amount"] == pytest.approx(7150.0)

    def test_design_amount_zero(self):
        result = calculate_estimate(
            material_amount=6250,
            cutting_amount=900,
            design_amount=0,
        )
        assert result["final_amount"] == pytest.approx(7150.0)

    def test_quantity_multiplier(self):
        """3 identical pieces at ₹7,545 each = ₹22,635."""
        result = calculate_estimate(
            material_amount=6250,
            cutting_amount=900,
            design_amount=395,
            quantity=3,
        )
        assert result["per_piece_amount"] == pytest.approx(7545.0)
        assert result["quantity"] == 3
        assert result["final_amount"] == pytest.approx(22635.0)

    def test_quantity_one(self):
        result = calculate_estimate(
            material_amount=1000,
            cutting_amount=500,
            design_amount=100,
            quantity=1,
        )
        assert result["per_piece_amount"] == pytest.approx(1600.0)
        assert result["final_amount"] == pytest.approx(1600.0)

    def test_all_zero_amounts(self):
        result = calculate_estimate(
            material_amount=0,
            cutting_amount=0,
            design_amount=0,
        )
        assert result["final_amount"] == pytest.approx(0.0)

    def test_negative_material_raises(self):
        with pytest.raises(ValueError, match="Material amount cannot be negative"):
            calculate_estimate(-100, 900, 395)

    def test_negative_cutting_raises(self):
        with pytest.raises(ValueError, match="Cutting amount cannot be negative"):
            calculate_estimate(6250, -100, 395)

    def test_negative_design_raises(self):
        with pytest.raises(ValueError, match="Design amount cannot be negative"):
            calculate_estimate(6250, 900, -50)

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="Quantity must be at least 1"):
            calculate_estimate(6250, 900, 395, quantity=0)

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="Quantity must be at least 1"):
            calculate_estimate(6250, 900, 395, quantity=-1)

    def test_returns_dict_keys(self):
        result = calculate_estimate(1000, 500, 100)
        assert "per_piece_amount" in result
        assert "quantity" in result
        assert "final_amount" in result


class TestCalculateSimpleEstimate:
    """Test Part 3, 4, 32 Simple Cutting calculations."""

    def test_client_example_single_piece(self):
        """Client sample: 32 sq.ft x ₹330 = ₹10,560."""
        res = calculate_simple_estimate(area_sqft=32.0, rate_per_sqft=330.0, quantity=1)
        assert res["per_piece_amount"] == pytest.approx(10560.0)
        assert res["quantity"] == 1
        assert res["final_amount"] == pytest.approx(10560.0)

    def test_client_example_quantity_three(self):
        """Client sample qty 3: ₹10,560 x 3 = ₹31,680."""
        res = calculate_simple_estimate(area_sqft=32.0, rate_per_sqft=330.0, quantity=3)
        assert res["per_piece_amount"] == pytest.approx(10560.0)
        assert res["quantity"] == 3
        assert res["final_amount"] == pytest.approx(31680.0)

    def test_zero_area_or_rate(self):
        res = calculate_simple_estimate(area_sqft=0.0, rate_per_sqft=330.0)
        assert res["final_amount"] == pytest.approx(0.0)

        res2 = calculate_simple_estimate(area_sqft=32.0, rate_per_sqft=0.0)
        assert res2["final_amount"] == pytest.approx(0.0)

    def test_negative_area_raises(self):
        with pytest.raises(ValueError, match="Area cannot be negative"):
            calculate_simple_estimate(area_sqft=-5.0, rate_per_sqft=330.0)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="Rate per sq.ft cannot be negative"):
            calculate_simple_estimate(area_sqft=32.0, rate_per_sqft=-10.0)

    def test_invalid_quantity_raises(self):
        with pytest.raises(ValueError, match="Quantity must be at least 1"):
            calculate_simple_estimate(area_sqft=32.0, rate_per_sqft=330.0, quantity=0)


class TestCalculateDesignHeavyEstimate:
    """Test Part 5, 6, 7, 8, 32 Design Heavy calculations."""

    def test_design_heavy_air_cutting(self):
        """
        120cm x 80cm x 1mm MS (density 7.85) = 7.536 kg.
        Kilo rate = 250 -> Material = 1884.0.
        Air cutting 1 hr @ 1500 -> Cutting = 1500.0.
        Per piece = 3384.0.
        """
        res = calculate_design_heavy_estimate(
            weight_kg=7.536,
            kilo_rate=250.0,
            cutting_time_hours=1.0,
            cutting_rate_per_hour=1500.0,
            quantity=1,
        )
        assert res["material_amount"] == pytest.approx(1884.0)
        assert res["cutting_amount"] == pytest.approx(1500.0)
        assert res["per_piece_amount"] == pytest.approx(3384.0)
        assert res["final_amount"] == pytest.approx(3384.0)

    def test_design_heavy_oxygen_cutting(self):
        """Oxygen cutting 1 hr @ ₹1800/hr."""
        res = calculate_design_heavy_estimate(
            weight_kg=7.536,
            kilo_rate=250.0,
            cutting_time_hours=1.0,
            cutting_rate_per_hour=1800.0,
            quantity=1,
        )
        assert res["cutting_amount"] == pytest.approx(1800.0)
        assert res["per_piece_amount"] == pytest.approx(3684.0)

    def test_design_heavy_custom_rate(self):
        """Custom cutting 1.5 hr @ ₹2000/hr = ₹3000."""
        res = calculate_design_heavy_estimate(
            weight_kg=10.0,
            kilo_rate=200.0,
            cutting_time_hours=1.5,
            cutting_rate_per_hour=2000.0,
            quantity=2,
        )
        assert res["material_amount"] == pytest.approx(2000.0)
        assert res["cutting_amount"] == pytest.approx(3000.0)
        assert res["per_piece_amount"] == pytest.approx(5000.0)
        assert res["final_amount"] == pytest.approx(10000.0)

    def test_negative_values_raise(self):
        with pytest.raises(ValueError, match="Weight cannot be negative"):
            calculate_design_heavy_estimate(weight_kg=-1.0, kilo_rate=250.0, cutting_time_hours=1.0, cutting_rate_per_hour=1500.0)

        with pytest.raises(ValueError, match="Kilo rate cannot be negative"):
            calculate_design_heavy_estimate(weight_kg=1.0, kilo_rate=-250.0, cutting_time_hours=1.0, cutting_rate_per_hour=1500.0)

        with pytest.raises(ValueError, match="Cutting time cannot be negative"):
            calculate_design_heavy_estimate(weight_kg=1.0, kilo_rate=250.0, cutting_time_hours=-1.0, cutting_rate_per_hour=1500.0)

        with pytest.raises(ValueError, match="Cutting rate cannot be negative"):
            calculate_design_heavy_estimate(weight_kg=1.0, kilo_rate=250.0, cutting_time_hours=1.0, cutting_rate_per_hour=-1500.0)
