"""Tests for EstimateService."""

import os
import pytest
from app.services.database_service import DatabaseService
from app.services.estimate_service import EstimateService
from app.models.estimate import Estimate, HoleEntry


@pytest.fixture
def db_service(tmp_path):
    db_path = os.path.join(str(tmp_path), "test.db")
    db = DatabaseService(db_path)
    db.initialize()
    yield db
    db.close()


@pytest.fixture
def estimate_svc(db_service):
    return EstimateService(db_service)


def _make_estimate(**overrides) -> Estimate:
    """Create a test estimate with sensible defaults."""
    defaults = dict(
        estimate_number="EST-0001",
        customer_name="Test Customer",
        phone="9876543210",
        date="20/09/2026",
        description="Test job",
        length=120.0,
        length_unit="cm",
        width=80.0,
        width_unit="cm",
        length_ft=3.937,
        width_ft=2.625,
        area_sqft=10.33,
        material="MS",
        thickness=2.0,
        thickness_unit="mm",
        sheet_weight=25.0,
        kilo_rate=250.0,
        cutting_hours=0,
        cutting_minutes=30,
        total_cutting_min=30.0,
        cutting_rate=30.0,
        material_amount=6250.0,
        cutting_amount=900.0,
        design_amount=395.0,
        quantity=1,
        per_piece_amount=7545.0,
        final_amount=7545.0,
    )
    defaults.update(overrides)
    return Estimate(**defaults)


class TestEstimateNumbering:
    def test_first_estimate_number(self, estimate_svc):
        assert estimate_svc.get_next_estimate_number() == "EST-0001"

    def test_sequential_numbering(self, estimate_svc):
        est = _make_estimate(estimate_number="EST-0001")
        estimate_svc.save_estimate(est)
        assert estimate_svc.get_next_estimate_number() == "EST-0002"

    def test_numbering_after_multiple(self, estimate_svc):
        for i in range(1, 4):
            est = _make_estimate(estimate_number=f"EST-{i:04d}")
            estimate_svc.save_estimate(est)
        assert estimate_svc.get_next_estimate_number() == "EST-0004"

    def test_numbering_uses_max_not_latest_id(self, estimate_svc):
        """A later row with a lower number must not cause EST-0001 reuse."""
        estimate_svc.save_estimate(_make_estimate(estimate_number="EST-0005"))
        estimate_svc.save_estimate(_make_estimate(estimate_number="EST-0001"))
        assert estimate_svc.get_next_estimate_number() == "EST-0006"

    def test_save_assigns_unused_number_on_collision(self, estimate_svc):
        estimate_svc.save_estimate(_make_estimate(estimate_number="EST-0001"))
        second_id = estimate_svc.save_estimate(
            _make_estimate(estimate_number="EST-0001", customer_name="Second")
        )
        second = estimate_svc.get_estimate_by_id(second_id)
        assert second.estimate_number == "EST-0002"
        first = estimate_svc.get_all_estimates()
        numbers = {e.estimate_number for e in first}
        assert numbers == {"EST-0001", "EST-0002"}

    def test_update_retains_existing_number(self, estimate_svc):
        est_id = estimate_svc.save_estimate(_make_estimate(estimate_number="EST-0001"))
        loaded = estimate_svc.get_estimate_by_id(est_id)
        loaded.customer_name = "Edited"
        estimate_svc.update_estimate(loaded)
        reloaded = estimate_svc.get_estimate_by_id(est_id)
        assert reloaded.estimate_number == "EST-0001"
        assert estimate_svc.get_total_count() == 1


class TestSaveAndLoad:
    def test_save_estimate(self, estimate_svc):
        est = _make_estimate()
        est_id = estimate_svc.save_estimate(est)
        assert est_id is not None
        assert est_id > 0

    def test_load_estimate(self, estimate_svc):
        est = _make_estimate(
            customer_address="Unit 4, Industrial Estate",
            employee_name="Anand",
        )
        est.holes = [
            HoleEntry(diameter=10, diameter_unit="mm", quantity=20, rate=12, amount=240),
        ]
        est_id = estimate_svc.save_estimate(est)

        loaded = estimate_svc.get_estimate_by_id(est_id)
        assert loaded is not None
        assert loaded.customer_name == "Test Customer"
        assert loaded.customer_address == "Unit 4, Industrial Estate"
        assert loaded.employee_name == "Anand"
        assert loaded.date == "20/09/2026"
        assert loaded.final_amount == 7545.0
        assert loaded.quantity == 1
        assert len(loaded.holes) == 1
        assert loaded.holes[0].diameter == 10
        assert loaded.holes[0].quantity == 20

    def test_old_estimate_schema_migrates_optional_customer_fields(
        self, estimate_svc, db_service
    ):
        estimate_id = estimate_svc.save_estimate(_make_estimate())
        conn = db_service.get_connection()
        conn.execute("ALTER TABLE estimates DROP COLUMN customer_address")
        conn.execute("ALTER TABLE estimates DROP COLUMN employee_name")
        conn.commit()

        db_service.initialize()
        loaded = estimate_svc.get_estimate_by_id(estimate_id)
        assert loaded.customer_address == ""
        assert loaded.employee_name == ""

    def test_load_nonexistent(self, estimate_svc):
        assert estimate_svc.get_estimate_by_id(9999) is None

    def test_preserves_rates(self, estimate_svc):
        """Saved estimate preserves the rates used at creation time."""
        est = _make_estimate(kilo_rate=250.0, cutting_rate=30.0)
        est_id = estimate_svc.save_estimate(est)

        loaded = estimate_svc.get_estimate_by_id(est_id)
        assert loaded.kilo_rate == 250.0
        assert loaded.cutting_rate == 30.0

    def test_quantity_saved(self, estimate_svc):
        est = _make_estimate(quantity=3, per_piece_amount=7545.0, final_amount=22635.0)
        est_id = estimate_svc.save_estimate(est)
        loaded = estimate_svc.get_estimate_by_id(est_id)
        assert loaded.quantity == 3
        assert loaded.per_piece_amount == 7545.0
        assert loaded.final_amount == 22635.0


class TestUpdateEstimate:
    def test_update(self, estimate_svc):
        est = _make_estimate()
        est_id = estimate_svc.save_estimate(est)

        loaded = estimate_svc.get_estimate_by_id(est_id)
        loaded.customer_name = "Updated Customer"
        loaded.final_amount = 8000.0
        estimate_svc.update_estimate(loaded)

        reloaded = estimate_svc.get_estimate_by_id(est_id)
        assert reloaded.customer_name == "Updated Customer"
        assert reloaded.final_amount == 8000.0

    def test_update_without_id_raises(self, estimate_svc):
        est = _make_estimate()
        with pytest.raises(ValueError, match="without an id"):
            estimate_svc.update_estimate(est)

    def test_update_holes(self, estimate_svc):
        est = _make_estimate()
        est.holes = [
            HoleEntry(diameter=10, quantity=20, rate=12, amount=240),
        ]
        est_id = estimate_svc.save_estimate(est)

        loaded = estimate_svc.get_estimate_by_id(est_id)
        loaded.holes = [
            HoleEntry(diameter=5, quantity=10, rate=8, amount=80),
            HoleEntry(diameter=15, quantity=5, rate=15, amount=75),
        ]
        estimate_svc.update_estimate(loaded)

        reloaded = estimate_svc.get_estimate_by_id(est_id)
        assert len(reloaded.holes) == 2


class TestListAndSearch:
    def test_get_all(self, estimate_svc):
        for i in range(3):
            est = _make_estimate(estimate_number=f"EST-{i+1:04d}")
            estimate_svc.save_estimate(est)
        all_est = estimate_svc.get_all_estimates()
        assert len(all_est) == 3

    def test_search_by_name(self, estimate_svc):
        estimate_svc.save_estimate(_make_estimate(
            estimate_number="EST-0001", customer_name="ABC Industries"
        ))
        estimate_svc.save_estimate(_make_estimate(
            estimate_number="EST-0002", customer_name="XYZ Fabrication"
        ))
        results = estimate_svc.search_estimates("ABC")
        assert len(results) == 1
        assert results[0].customer_name == "ABC Industries"

    def test_search_by_number(self, estimate_svc):
        estimate_svc.save_estimate(_make_estimate(estimate_number="EST-0001"))
        results = estimate_svc.search_estimates("EST-0001")
        assert len(results) == 1

    def test_search_no_results(self, estimate_svc):
        results = estimate_svc.search_estimates("nonexistent")
        assert len(results) == 0

    def test_recent_estimates(self, estimate_svc):
        for i in range(10):
            est = _make_estimate(estimate_number=f"EST-{i+1:04d}")
            estimate_svc.save_estimate(est)
        recent = estimate_svc.get_recent_estimates(5)
        assert len(recent) == 5

    def test_total_count(self, estimate_svc):
        assert estimate_svc.get_total_count() == 0
        estimate_svc.save_estimate(_make_estimate())
        assert estimate_svc.get_total_count() == 1


class TestDeleteAndDuplicate:
    def test_delete(self, estimate_svc):
        est_id = estimate_svc.save_estimate(_make_estimate())
        estimate_svc.delete_estimate(est_id)
        assert estimate_svc.get_estimate_by_id(est_id) is None

    def test_delete_cascades_holes(self, estimate_svc):
        est = _make_estimate()
        est.holes = [HoleEntry(diameter=10, quantity=20, rate=12, amount=240)]
        est_id = estimate_svc.save_estimate(est)
        estimate_svc.delete_estimate(est_id)

        # Verify holes are also deleted
        conn = estimate_svc._db.get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM estimate_holes WHERE estimate_id = ?",
            (est_id,),
        )
        assert cursor.fetchone()[0] == 0

    def test_duplicate(self, estimate_svc):
        original_id = estimate_svc.save_estimate(_make_estimate(
            estimate_number="EST-0001",
            customer_name="Original Customer",
        ))
        new_id = estimate_svc.duplicate_estimate(original_id)
        assert new_id is not None
        assert new_id != original_id

        dup = estimate_svc.get_estimate_by_id(new_id)
        assert dup.estimate_number == "EST-0002"
        assert dup.customer_name == "Original Customer"

    def test_duplicate_nonexistent(self, estimate_svc):
        assert estimate_svc.duplicate_estimate(9999) is None


class TestMaterials:
    def test_get_used_materials(self, estimate_svc):
        estimate_svc.save_estimate(_make_estimate(
            estimate_number="EST-0001", material="MS"
        ))
        estimate_svc.save_estimate(_make_estimate(
            estimate_number="EST-0002", material="SS 304"
        ))
        estimate_svc.save_estimate(_make_estimate(
            estimate_number="EST-0003", material="MS"
        ))
        materials = estimate_svc.get_used_materials()
        assert "MS" in materials
        assert "SS 304" in materials
        assert len(materials) == 2  # Distinct
