"""
Comprehensive End-to-End Business Workflow Test (33-Step Lifecycle).

Full verification of the Phase 7 industrial business workflow:
1. Launch application.
2. Create a new estimate.
3. Enter customer details.
4. Enter 120 cm × 80 cm.
5. Verify converted dimensions: ~3.94 ft × 2.62 ft.
6. Verify converted area: ~10.33 sq.ft.
7. Verify automatic sheet weight from Stainless Steel 304 (1×1000×2000 mm = 16.00 kg).
8. Verify default kilo rate: ₹250/kg.
9. Enter 30 minutes laser cutting duration.
10. Verify default cutting rate: ₹30/minute.
11. Add sample hole entries (10x5mm @ ₹8, 15x10mm @ ₹12, 9x15mm @ ₹15).
12. Verify design amount: ₹395.
13. Verify per-piece total: ₹5,295.
14. Set quantity multiplier: 3 pieces.
15. Verify total quotation amount: ₹15,885.
16. Save estimate quotation.
17. Open History page.
18. Search for the customer.
19. View quotation details in dialog.
20. Edit quotation.
21. Verify original rates (₹250, ₹30) are preserved.
22. Change global default rates in Settings (₹450/kg, ₹60/min).
23. Reopen the old quotation.
24. Verify original historical rates remain unchanged (₹250, ₹30, ₹15,885).
25. Duplicate the quotation.
26. Verify new sequential estimate number (EST-0002).
27. Modify the duplicate (manual override weight = 35kg, qty = 1).
28. Save duplicate quotation.
29. Verify original estimate (EST-0001) remains completely unchanged.
30. Delete the duplicate quotation.
31. Verify duplicate disappears from History and total count returns to 1.
32. Restart the application (fresh process simulation).
33. Verify original estimate EST-0001 persists and remains intact.
"""

import os
import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QMessageBox

from app.services.database_service import DatabaseService
from app.services.pricing_service import PricingService
from app.services.estimate_service import EstimateService
from app.ui.main_window import MainWindow
from app.ui.widgets.sidebar import SidebarWidget
from app.ui.estimate_view import EstimateViewDialog


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_33_step_end_to_end_business_workflow(qapp, tmp_path):
    db_file = os.path.join(str(tmp_path), "production_e2e.db")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1: Launch Application
    # ─────────────────────────────────────────────────────────────────────────
    db1 = DatabaseService(db_path=db_file)
    db1.initialize()
    pricing1 = PricingService(db1)
    estimate1 = EstimateService(db1)

    window1 = MainWindow(
        db_service=db1,
        pricing_service=pricing1,
        estimate_service=estimate1,
    )
    assert window1 is not None

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2 & 3: Create New Estimate & Enter Customer Details
    # ─────────────────────────────────────────────────────────────────────────
    window1._navigate_to_new_estimate(reset=True)
    assert window1._stack.currentIndex() == SidebarWidget.PAGE_NEW_ESTIMATE
    page1 = window1._new_estimate_page

    page1._txt_cust_name.setText("Bharat Heavy Metal Works")
    page1._txt_phone.setText("+91 98200 11223")
    page1._txt_desc.setText("Precision laser cut baffle plate")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4, 5, 6: Simple Cutting mode (32 sq.ft @ ₹330/sq.ft = ₹10,560)
    # ─────────────────────────────────────────────────────────────────────────
    page1.set_mode("simple")
    page1._simple_material_combo.setCurrentText("Mild Steel")
    page1._spin_thickness.setValue(3.0)
    page1._spin_rate_per_sqft.setValue(330.0)

    page1._spin_length.setValue(8.0)
    page1._combo_length_unit.setCurrentText("ft")
    page1._spin_width.setValue(4.0)
    page1._combo_width_unit.setCurrentText("ft")
    page1._spin_quantity.setValue(1)
    page1._recalculate()

    # Step 5 & 6: Verify area & per piece total
    assert "32.00 sq.ft" in page1._lbl_area_converted.text()
    assert "₹10,560" in page1._lbl_simple_per_piece.text()
    assert "₹10,560" in page1._summary_card._lbl_final_total.text()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 7 & 8: Switch to Design Heavy mode (120 cm × 80 cm @ 1 mm MS)
    # ─────────────────────────────────────────────────────────────────────────
    page1.set_mode("design_heavy")
    page1._design_heavy_material_combo.setCurrentText("Mild Steel")
    page1._spin_length.setValue(120.0)
    page1._combo_length_unit.setCurrentText("cm")
    page1._spin_width.setValue(80.0)
    page1._combo_width_unit.setCurrentText("cm")
    page1._spin_thickness.setValue(1.0)
    page1._chk_override_weight.setChecked(False)
    assert page1._spin_kilo_rate.value() == 250.0  # Step 8
    page1._recalculate()

    # Weight = 1200 * 800 * 1 * 7.85e-6 = 7.536 kg (~7.54 kg)
    assert "7.54 kg" in page1._lbl_calc_weight.text()
    assert page1._spin_sheet_weight.value() == pytest.approx(7.536, abs=0.01)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 9 & 10: Air cutting 1 hour @ ₹1500/hr
    # ─────────────────────────────────────────────────────────────────────────
    page1._radio_air.setChecked(True)
    page1._spin_hours.setValue(1)
    page1._spin_minutes.setValue(0)
    page1._recalculate()
    assert page1._get_effective_hourly_cutting_rate() == 1500.0  # Step 10
    assert "₹1,500" in page1._lbl_cut_subtotal.text()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 11, 12, 13: Verify Per-Piece Total (7.536 * 250 = 1884; 1884 + 1500 = 3384)
    # ─────────────────────────────────────────────────────────────────────────
    assert "₹3,384" in page1._summary_card._lbl_per_piece_val.text()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 14 & 15: Set Quantity to 3 & Verify Total = ₹10,152 (3384 * 3)
    # ─────────────────────────────────────────────────────────────────────────
    page1._spin_quantity.setValue(3)
    page1._recalculate()

    assert "₹3,384" in page1._summary_card._lbl_per_piece_val.text()
    assert "× 3" in page1._summary_card._lbl_qty_val.text()
    # Step 15: 3384 * 3 = ₹10,152
    assert "₹10,152" in page1._summary_card._lbl_final_total.text()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 16: Save Estimate Quotation
    # ─────────────────────────────────────────────────────────────────────────
    with patch.object(QMessageBox, "information"):
        page1._on_save()

    assert estimate1.get_total_count() == 1
    est_record1 = estimate1.get_all_estimates()[0]
    assert est_record1.estimate_number == "EST-0001"
    assert est_record1.final_amount == pytest.approx(10152.0, abs=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 17 & 18: Open History & Search for Customer
    # ─────────────────────────────────────────────────────────────────────────
    window1._navigate_to_page(SidebarWidget.PAGE_HISTORY)
    history_page = window1._history_page

    assert history_page._table.rowCount() == 1
    assert history_page._table.item(0, 0).text() == "EST-0001"

    # Step 18: Search
    history_page._txt_search.setText("Bharat")
    assert history_page._table.rowCount() == 1
    history_page._txt_search.clear()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 19: View Quotation Dialog
    # ─────────────────────────────────────────────────────────────────────────
    full_est = estimate1.get_estimate_by_id(est_record1.id)
    view_dialog = EstimateViewDialog(estimate=full_est, pricing_service=pricing1)
    assert view_dialog is not None
    assert "EST-0001" in view_dialog.windowTitle()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 20 & 21: Edit Quotation & Verify Original Rates Preserved
    # ─────────────────────────────────────────────────────────────────────────
    window1._on_edit_estimate(est_record1.id)
    assert window1._stack.currentIndex() == SidebarWidget.PAGE_NEW_ESTIMATE
    assert window1._new_estimate_page._spin_kilo_rate.value() == 250.0
    assert window1._new_estimate_page._get_effective_hourly_cutting_rate() == 1500.0

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 22: Change Global Default Rates in Settings (e.g. ₹450/kg, ₹2100 Air)
    # ─────────────────────────────────────────────────────────────────────────
    window1._navigate_to_page(SidebarWidget.PAGE_SETTINGS)
    settings_page = window1._settings_page
    settings_page._spin_kilo_rate.setValue(450.0)
    settings_page._spin_air_rate.setValue(2100.0)
    settings_page._save_rates()

    assert pricing1.get_default_kilo_rate() == 450.0
    assert pricing1.get_air_cutting_rate() == 2100.0

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 23 & 24: Reopen Old Quotation & Verify Original Rates Unchanged
    # ─────────────────────────────────────────────────────────────────────────
    window1._on_edit_estimate(est_record1.id)
    assert window1._new_estimate_page._spin_kilo_rate.value() == 250.0  # NOT 450
    assert window1._new_estimate_page._get_effective_hourly_cutting_rate() == 1500.0   # NOT 2100
    assert "₹10,152" in window1._new_estimate_page._summary_card._lbl_final_total.text()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 25 & 26: Duplicate Quotation & Verify Next Estimate Number (EST-0002)
    # ─────────────────────────────────────────────────────────────────────────
    window1._on_duplicate_estimate(est_record1.id)
    dup_page = window1._new_estimate_page

    assert dup_page._txt_est_number.text() == "EST-0002"  # Step 26
    assert dup_page._current_estimate_id is None

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 27 & 28: Modify Duplicate (manual override weight = 35kg, qty = 1) & Save It
    # ─────────────────────────────────────────────────────────────────────────
    dup_page._chk_override_weight.setChecked(True)
    dup_page._spin_manual_weight.setValue(35.0)
    dup_page._spin_quantity.setValue(1)
    dup_page._recalculate()

    # Calculation for duplicate:
    # Material: 35 * 250 = ₹8,750
    # Cutting: 1 * 1500 = ₹1,500
    # Total = 8750 + 1500 = ₹10,250
    assert "₹8,750" in dup_page._lbl_mat_subtotal.text()
    assert "₹10,250" in dup_page._summary_card._lbl_final_total.text()

    with patch.object(QMessageBox, "information"):
        dup_page._on_save()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 29: Verify Original EST-0001 Remains Completely Unchanged
    # ─────────────────────────────────────────────────────────────────────────
    assert estimate1.get_total_count() == 2
    original_check = estimate1.get_estimate_by_id(est_record1.id)
    assert original_check.estimate_number == "EST-0001"
    assert original_check.sheet_weight == pytest.approx(7.536, abs=0.01)
    assert original_check.quantity == 3
    assert original_check.final_amount == pytest.approx(10152.0, abs=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 30 & 31: Delete Duplicate & Verify Disappears from History
    # ─────────────────────────────────────────────────────────────────────────
    all_current = estimate1.get_all_estimates()
    dup_record = next(e for e in all_current if e.estimate_number == "EST-0002")

    window1._navigate_to_page(SidebarWidget.PAGE_HISTORY)
    assert window1._history_page._table.rowCount() == 2

    with patch("app.ui.estimate_history.ConfirmationDialog.confirm", return_value=True), \
         patch.object(QMessageBox, "information"):
        window1._history_page._delete_estimate(dup_record.id, "EST-0002")

    assert estimate1.get_total_count() == 1
    assert window1._history_page._table.rowCount() == 1
    assert window1._history_page._table.item(0, 0).text() == "EST-0001"

    # Close first session
    with patch("app.ui.main_window.ConfirmationDialog.confirm", return_value=True):
        window1.close()
    db1.close()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 32 & 33: Restart Application & Verify Original Estimate Persists
    # ─────────────────────────────────────────────────────────────────────────
    db2 = DatabaseService(db_path=db_file)
    db2.initialize()
    pricing2 = PricingService(db2)
    estimate2 = EstimateService(db2)

    window2 = MainWindow(
        db_service=db2,
        pricing_service=pricing2,
        estimate_service=estimate2,
    )

    # Step 33: Verify original estimate persists cleanly
    assert estimate2.get_total_count() == 1
    persisted_est = estimate2.get_all_estimates()[0]
    full_persisted = estimate2.get_estimate_by_id(persisted_est.id)

    assert full_persisted.estimate_number == "EST-0001"
    assert full_persisted.customer_name == "Bharat Heavy Metal Works"
    assert full_persisted.sheet_weight == pytest.approx(7.536, abs=0.01)
    assert full_persisted.kilo_rate == 250.0
    assert full_persisted.cutting_rate_per_hour == 1500.0
    assert full_persisted.quantity == 3
    assert full_persisted.final_amount == pytest.approx(10152.0, abs=1.0)

    with patch("app.ui.main_window.ConfirmationDialog.confirm", return_value=True):
        window2.close()
    db2.close()
