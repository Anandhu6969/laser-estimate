"""Tests for PricingService and DatabaseService."""

import os
import tempfile
import pytest
from app.services.database_service import DatabaseService
from app.services.pricing_service import PricingService


@pytest.fixture
def db_service(tmp_path):
    """Create a fresh in-memory-like DB for each test."""
    db_path = os.path.join(str(tmp_path), "test.db")
    db = DatabaseService(db_path)
    db.initialize()
    yield db
    db.close()


@pytest.fixture
def pricing(db_service):
    return PricingService(db_service)


class TestDatabaseService:
    def test_initialize_creates_tables(self, db_service):
        conn = db_service.get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        assert "settings" in tables
        assert "estimates" in tables
        assert "estimate_holes" in tables
        assert "hole_rates" in tables

    def test_default_settings_seeded(self, db_service):
        conn = db_service.get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM settings")
        assert cursor.fetchone()[0] > 0

    def test_default_hole_rates_seeded(self, db_service):
        conn = db_service.get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM hole_rates")
        assert cursor.fetchone()[0] == 4

    def test_double_initialize_no_duplicate(self, db_service):
        """Calling initialize twice should not duplicate data."""
        db_service.initialize()
        conn = db_service.get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM hole_rates")
        assert cursor.fetchone()[0] == 4


class TestPricingServiceSettings:
    def test_standard_density_settings_match_defaults(self, pricing):
        expected = {
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
        assert {name: pricing.get_material_density(name) for name in expected} == expected

    def test_initialization_preserves_custom_material_density(self, pricing, db_service):
        pricing.set_material_density("Aluminium", 2.63)
        db_service.initialize()
        assert pricing.get_material_density("Aluminium") == 2.63

    def test_get_default_kilo_rate(self, pricing):
        assert pricing.get_default_kilo_rate() == 250.0

    def test_get_default_cutting_rate(self, pricing):
        assert pricing.get_default_cutting_rate() == 30.0

    def test_set_kilo_rate(self, pricing):
        pricing.set_default_kilo_rate(300)
        assert pricing.get_default_kilo_rate() == 300.0

    def test_set_cutting_rate(self, pricing):
        pricing.set_default_cutting_rate(35)
        assert pricing.get_default_cutting_rate() == 35.0

    def test_setting_persists(self, pricing, db_service):
        """Verify settings persist across PricingService instances."""
        pricing.set_default_cutting_rate(45)
        pricing2 = PricingService(db_service)
        assert pricing2.get_default_cutting_rate() == 45.0

    def test_get_all_settings(self, pricing):
        settings = pricing.get_all_settings()
        assert "default_kilo_rate" in settings
        assert "default_cutting_rate" in settings

    def test_get_set_arbitrary_setting(self, pricing):
        pricing.set_setting("company_name", "Test Corp")
        assert pricing.get_setting("company_name") == "Test Corp"

    def test_get_missing_setting_default(self, pricing):
        assert pricing.get_setting("nonexistent", "fallback") == "fallback"


class TestPricingServiceHoleRates:
    def test_get_default_hole_rates(self, pricing):
        rates = pricing.get_hole_rates()
        assert len(rates) == 4
        diameters = [r["diameter"] for r in rates]
        assert 5.0 in diameters
        assert 10.0 in diameters
        assert 15.0 in diameters
        assert 20.0 in diameters

    def test_get_hole_rate_for_diameter(self, pricing):
        rate = pricing.get_hole_rate_for_diameter(10.0, "mm")
        assert rate == 12.0

    def test_get_hole_rate_not_found(self, pricing):
        rate = pricing.get_hole_rate_for_diameter(99.0, "mm")
        assert rate is None

    def test_add_hole_rate(self, pricing):
        new_id = pricing.add_hole_rate(25.0, "mm", 25.0)
        assert new_id is not None
        rates = pricing.get_hole_rates()
        assert len(rates) == 5
        rate = pricing.get_hole_rate_for_diameter(25.0, "mm")
        assert rate == 25.0

    def test_update_hole_rate(self, pricing):
        rates = pricing.get_hole_rates()
        first = rates[0]
        pricing.update_hole_rate(first["id"], first["diameter"], first["unit"], 99.0)
        updated = pricing.get_hole_rate_for_diameter(first["diameter"], first["unit"])
        assert updated == 99.0

    def test_delete_hole_rate(self, pricing):
        rates = pricing.get_hole_rates()
        pricing.delete_hole_rate(rates[0]["id"])
        remaining = pricing.get_hole_rates()
        assert len(remaining) == 3

    def test_rates_ordered_by_diameter(self, pricing):
        rates = pricing.get_hole_rates()
        diameters = [r["diameter"] for r in rates]
        assert diameters == sorted(diameters)
