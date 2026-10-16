"""
Tests for Phase 5 — Estimate UI & NewEstimatePage workflow.
"""

import os
import pytest
from unittest.mock import patch
from PySide6.QtCore import QDate, QPoint, QPointF, QSize, QTimer, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.database_service import DatabaseService
from app.services.pricing_service import PricingService
from app.services.estimate_service import EstimateService
from app.models.estimate import Estimate, HoleEntry
from app.ui.widgets.hole_table import HoleTableWidget
from app.ui.widgets.summary_card import SummaryCardWidget
from app.ui.new_estimate import NewEstimatePage
from app.ui.settings_page import SettingsPage
from app.ui.widgets.no_wheel_spinbox import NoWheelDoubleSpinBox
from app.utils.formatters import format_indian_currency


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a clean temporary DatabaseService."""
    db_path = os.path.join(str(tmp_path), "test_new_estimate.db")
    db = DatabaseService(db_path=db_path)
    db.initialize()
    yield db
    db.close()


@pytest.fixture
def pricing_service(temp_db):
    return PricingService(temp_db)


@pytest.fixture
def estimate_service(temp_db):
    return EstimateService(temp_db)


def choose_estimate_date(page, selected_date):
    def select_date_in_dialog():
        dialog = QApplication.activeModalWidget()
        calendar = dialog.findChild(QCalendarWidget)
        assert calendar is not None
        calendar.clicked.emit(selected_date)

    QTimer.singleShot(0, select_date_in_dialog)
    page._date_calendar_action.trigger()


class TestHoleTableWidget:
    def test_date_defaults_to_today_in_dd_mm_yyyy(self, qapp, estimate_service, pricing_service):
        page = NewEstimatePage(estimate_service, pricing_service)
        page.show()
        qapp.processEvents()
        assert page._lbl_date.text() == "Date"
        assert page._lbl_date.isVisible()
        assert page._date_edit.isVisible()
        assert page._lbl_date.geometry().width() > 0
        assert page._date_edit.geometry().width() >= 150
        assert page._date_edit.date() == QDate.currentDate()
        assert page._date_edit.displayFormat() == "dd/MM/yyyy"
        assert page._date_edit.lineEdit().text() == QDate.currentDate().toString("dd/MM/yyyy")
        assert page._date_calendar_action in page._date_edit.lineEdit().actions()
        assert not page._date_calendar_action.icon().isNull()
        assert page._date_calendar_action.icon().actualSize(QSize(16, 16)) == QSize(16, 16)
        assert not hasattr(page, "_btn_date_picker")

    def test_calendar_button_selects_date(self, qapp, estimate_service, pricing_service):
        page = NewEstimatePage(estimate_service, pricing_service)
        selected = QDate(2025, 4, 9)
        choose_estimate_date(page, selected)

        assert page._date_edit.date() == selected
        assert page._date_edit.lineEdit().text() == "09/04/2025"

    def test_quantity_spinboxes_ignore_wheel_but_keep_controls(
        self, qapp, estimate_service, pricing_service
    ):
        def send_wheel(spinbox):
            event = QWheelEvent(
                QPointF(1, 1),
                QPointF(1, 1),
                QPoint(0, 0),
                QPoint(0, 120),
                Qt.NoButton,
                Qt.NoModifier,
                Qt.ScrollUpdate,
                False,
            )
            QApplication.sendEvent(spinbox, event)
            return event

        page = NewEstimatePage(estimate_service, pricing_service)
        page._spin_quantity.setValue(5)
        event = send_wheel(page._spin_quantity)
        assert page._spin_quantity.value() == 5
        assert not event.isAccepted()
        page._spin_quantity.stepUp()
        assert page._spin_quantity.value() == 6

        # The same policy applies to double spin boxes and important estimate inputs.
        double_spin = NoWheelDoubleSpinBox()
        double_spin.setRange(0.0, 10000.0)
        double_spin.setDecimals(2)
        double_spin.setSingleStep(0.01)
        double_spin.setValue(250.0)
        event = send_wheel(double_spin)
        assert double_spin.value() == pytest.approx(250.0)
        assert not event.isAccepted()
        double_spin.stepUp()
        assert double_spin.value() == pytest.approx(250.01)
        double_spin.selectAll()
        QTest.keyClicks(double_spin, "275.50")
        assert double_spin.value() == pytest.approx(275.5)

        page._spin_kilo_rate.setValue(250.0)
        event = send_wheel(page._spin_kilo_rate)
        assert page._spin_kilo_rate.value() == pytest.approx(250.0)
        assert not event.isAccepted()
        page._spin_length.setValue(123.0)
        event = send_wheel(page._spin_length)
        assert page._spin_length.value() == pytest.approx(123.0)
        assert not event.isAccepted()

        settings = SettingsPage(pricing_service=pricing_service)
        event = send_wheel(settings._spin_kilo_rate)
        assert settings._spin_kilo_rate.value() == pytest.approx(250.0)
        assert not event.isAccepted()
        ms_row = next(
            row for row in range(settings._material_table.rowCount())
            if settings._material_table.item(row, 0).text() == "Mild Steel"
        )
        density = settings._material_table.cellWidget(ms_row, 1)
        original_density = density.value()
        event = send_wheel(density)
        assert density.value() == pytest.approx(original_density)
        assert not event.isAccepted()

        holes = HoleTableWidget(pricing_service=pricing_service)
        holes.add_row(diameter=5.0, unit="mm", quantity=5)
        hole_quantity = holes._table.cellWidget(0, 2)
        event = send_wheel(hole_quantity)
        assert hole_quantity.value() == 5
        assert not event.isAccepted()
        hole_quantity.stepDown()
        assert hole_quantity.value() == 4

    def test_ignored_spinbox_wheel_reaches_parent_scroll_area(self, qapp):
        area = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        spinbox = NoWheelDoubleSpinBox()
        spinbox.setValue(3.0)
        layout.addWidget(spinbox)
        content.setMinimumHeight(1200)
        area.setWidget(content)
        area.setWidgetResizable(False)
        area.resize(260, 180)
        area.show()
        qapp.processEvents()
        area.verticalScrollBar().setValue(0)

        event = QWheelEvent(
            QPointF(2, 2),
            QPointF(spinbox.mapToGlobal(QPoint(2, 2))),
            QPoint(0, 0),
            QPoint(0, -120),
            Qt.NoButton,
            Qt.NoModifier,
            Qt.ScrollUpdate,
            False,
        )
        QApplication.sendEvent(area.viewport(), event)
        qapp.processEvents()

        assert spinbox.value() == pytest.approx(3.0)
        assert area.verticalScrollBar().value() > 0
        area.close()

    def test_add_and_get_holes(self, qapp, pricing_service):
        widget = HoleTableWidget(pricing_service=pricing_service)
        widget.clear()
        assert len(widget.get_holes()) == 0

        # Add 5mm hole (default seeded rate ₹8)
        widget.add_row(diameter=5.0, unit="mm", quantity=10)
        holes = widget.get_holes()
        assert len(holes) == 1
        assert holes[0].diameter == 5.0
        assert holes[0].quantity == 10
        assert holes[0].rate == 8.0
        assert holes[0].amount == 80.0

    def test_hole_rate_override(self, qapp, pricing_service):
        widget = HoleTableWidget(pricing_service=pricing_service)
        widget.clear()
        widget.add_row(diameter=10.0, unit="mm", quantity=5, rate=20.0)
        holes = widget.get_holes()
        assert holes[0].rate == 20.0
        assert holes[0].amount == 100.0


class TestSummaryCardWidget:
    def test_summary_update_simple(self, qapp):
        card = SummaryCardWidget()
        card.set_mode("simple")
        card.update_simple_summary(
            dimensions_text="3.94 ft × 2.62 ft",
            area_text="32.00 sq.ft",
            material_text="Mild Steel · 3 mm",
            rate_per_sqft=330.0,
            per_piece_cost=10560.0,
            quantity=1,
            final_total=10560.0,
        )
        assert "₹10,560" in card._lbl_final_total.text()
        assert "32.00 sq.ft" in card._lbl_area_val.text()
        assert "₹330" in card._lbl_simple_rate.text()

    def test_summary_update_design_heavy(self, qapp):
        card = SummaryCardWidget()
        card.set_mode("design_heavy")
        card.update_design_heavy_summary(
            dimensions_text="3.94 ft × 2.62 ft",
            area_text="10.33 sq.ft",
            weight_text="7.54 kg",
            material_cost=1885.0,
            cutting_time_text="1.0 hours",
            cutting_cost=1500.0,
            per_piece_cost=3385.0,
            quantity=1,
            final_total=3385.0,
        )
        assert "₹3,385" in card._lbl_final_total.text()
        assert "7.54 kg" in card._lbl_weight_val.text()
        assert "₹1,885" in card._lbl_mat_val.text()
        assert "₹1,500" in card._lbl_cut_amt_val.text()


class TestNewEstimatePage:
    @pytest.mark.parametrize(
        "method,rate,expected",
        [("air", 1500.0, 1250.0), ("oxygen", 1800.0, 1500.0), ("custom", 2000.0, 2000.0 * 50 / 60)],
    )
    def test_design_heavy_hourly_cutting_rates_for_fifty_minutes(
        self, qapp, estimate_service, pricing_service, method, rate, expected
    ):
        page = NewEstimatePage(estimate_service, pricing_service)
        page.set_mode("design_heavy")
        page._spin_hours.setValue(0)
        page._spin_minutes.setValue(50)
        if method == "air":
            page._radio_air.setChecked(True)
        elif method == "oxygen":
            page._radio_oxygen.setChecked(True)
        else:
            page._radio_custom.setChecked(True)
            page._spin_custom_rate.setValue(rate)
        page._recalculate()
        assert page._get_effective_hourly_cutting_rate() == rate
        assert page._lbl_cut_time_info.text() == "50 minutes"
        # UI currency formatting intentionally rounds to whole rupees.
        assert page._lbl_cut_subtotal.text() == format_indian_currency(expected)

    def test_simple_estimate_unused_zero_air_rate_does_not_override_configured_rate(
        self, qapp, estimate_service, pricing_service
    ):
        simple = Estimate(calculation_mode="simple", cutting_method="", cutting_rate_per_hour=0.0)
        page = NewEstimatePage(estimate_service, pricing_service)
        page.load_estimate(simple, is_edit=False)
        page.set_mode("design_heavy")
        page._spin_minutes.setValue(50)
        page._radio_air.setChecked(True)
        page._recalculate()
        assert page._get_effective_hourly_cutting_rate() == 1500.0
        assert "₹1,500 / hour (Air)" in page._lbl_effective_cut_rate.text()
        assert page._lbl_cut_subtotal.text() == "₹1,250"

    def test_new_estimate_uses_current_air_setting_and_loaded_heavy_keeps_saved_rate(
        self, qapp, estimate_service, pricing_service
    ):
        pricing_service.set_air_cutting_rate(2100)
        page = NewEstimatePage(estimate_service, pricing_service)
        assert page._get_effective_hourly_cutting_rate() == 2100.0
        assert "₹2,100/hr" in page._radio_air.text()

        old = Estimate(calculation_mode="design_heavy", cutting_method="Air", cutting_rate_per_hour=1500.0)
        page.load_estimate(old, is_edit=False)
        assert page._get_effective_hourly_cutting_rate() == 1500.0

    def test_simple_cutting_calculation_live(self, qapp, estimate_service, pricing_service):
        """Simple cutting: 32 sq.ft x ₹330/sq.ft = ₹10,560."""
        page = NewEstimatePage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        page.set_mode("simple")
        page._simple_material_combo.setCurrentText("Mild Steel")
        page._spin_thickness.setValue(3.0)
        page._spin_rate_per_sqft.setValue(330.0)

        # 32 sq.ft = 8 ft x 4 ft
        page._spin_length.setValue(8.0)
        page._combo_length_unit.setCurrentText("ft")
        page._spin_width.setValue(4.0)
        page._combo_width_unit.setCurrentText("ft")
        page._spin_quantity.setValue(1)
        page._recalculate()

        assert page._spin_rate_per_sqft.value() == 330.0
        assert "₹10,560" in page._lbl_simple_per_piece.text()
        assert "₹10,560" in page._summary_card._lbl_final_total.text()

    def test_design_heavy_calculation_live(self, qapp, estimate_service, pricing_service):
        """Design heavy: 120 cm x 80 cm x 1 mm MS (7.85 kg/L) = 7.54 kg; Air 1 hr = ₹1500."""
        page = NewEstimatePage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        page.set_mode("design_heavy")
        page._design_heavy_material_combo.setCurrentText("Mild Steel")
        page._spin_length.setValue(120.0)
        page._combo_length_unit.setCurrentText("cm")
        page._spin_width.setValue(80.0)
        page._combo_width_unit.setCurrentText("cm")
        page._spin_thickness.setValue(1.0)
        page._spin_kilo_rate.setValue(250.0)
        page._radio_air.setChecked(True)
        page._spin_hours.setValue(1)
        page._spin_minutes.setValue(0)
        page._spin_quantity.setValue(1)
        page._recalculate()

        # 7.536 kg * 250 = 1884.0; Cutting = 1500.0; Total = 3384.0
        assert "7.54 kg" in page._lbl_calc_weight.text()
        assert page._spin_sheet_weight.value() == pytest.approx(7.536, abs=0.01)
        assert "₹3,384" in page._summary_card._lbl_final_total.text()

    def test_design_heavy_manual_weight_override(self, qapp, estimate_service, pricing_service):
        """Checked override in design heavy uses manual kg; unchecked returns to calculated weight."""
        page = NewEstimatePage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        page.set_mode("design_heavy")
        page._design_heavy_material_combo.setCurrentText("Mild Steel")
        page._spin_length.setValue(120.0)
        page._combo_length_unit.setCurrentText("cm")
        page._spin_width.setValue(80.0)
        page._combo_width_unit.setCurrentText("cm")
        page._spin_thickness.setValue(1.0)
        page._spin_kilo_rate.setValue(250.0)
        page._recalculate()

        assert page._spin_sheet_weight.value() == pytest.approx(7.536, abs=0.01)

        page._chk_override_weight.setChecked(True)
        page._spin_manual_weight.setValue(10.0)
        page._recalculate()
        assert page._spin_sheet_weight.value() == pytest.approx(10.0)
        assert "₹2,500" in page._lbl_mat_subtotal.text()

        page._chk_override_weight.setChecked(False)
        page._recalculate()
        assert page._spin_sheet_weight.value() == pytest.approx(7.536, abs=0.01)

    def test_per_estimate_rate_override_preserves_global_settings(
        self, qapp, estimate_service, pricing_service
    ):
        """Changing rates for an estimate must NOT alter global settings."""
        page = NewEstimatePage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        page.set_mode("design_heavy")
        page._spin_kilo_rate.setValue(400.0)
        page._radio_custom.setChecked(True)
        page._spin_cutting_rate_hourly.setValue(2200.0)
        page._recalculate()

        # Global settings must remain default
        assert pricing_service.get_default_kilo_rate() == 250.0
        assert pricing_service.get_air_cutting_rate() == 1500.0
        assert pricing_service.get_oxygen_cutting_rate() == 1800.0

    def test_quantity_multiplier(self, qapp, estimate_service, pricing_service):
        """Batch quantity multiplies total quotation without altering per-piece amount."""
        page = NewEstimatePage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        page.set_mode("simple")
        page._simple_material_combo.setCurrentText("Mild Steel")
        page._spin_thickness.setValue(3.0)
        page._spin_rate_per_sqft.setValue(330.0)
        page._spin_length.setValue(8.0)
        page._combo_length_unit.setCurrentText("ft")
        page._spin_width.setValue(4.0)
        page._combo_width_unit.setCurrentText("ft")
        page._spin_quantity.setValue(3)
        page._recalculate()

        # 32 sq.ft x 330 = 10,560 per piece; for 3 pcs = 31,680
        assert "₹10,560" in page._summary_card._lbl_per_piece_val.text()
        assert "₹31,680" in page._summary_card._lbl_final_total.text()

    def test_save_and_load_estimate(self, qapp, estimate_service, pricing_service):
        """Saving a simple estimate persists to DB with all details and preserved rates."""
        page = NewEstimatePage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        page.set_mode("simple")
        choose_estimate_date(page, QDate(2025, 4, 9))
        page._txt_cust_name.setText("Industrial Dynamics Ltd")
        page._txt_cust_address.setPlainText("Unit 4, Industrial Estate\nShornur")
        page._txt_phone.setText("+91 99999 88888")
        page._txt_employee_name.setText("Anand")
        page._simple_material_combo.setCurrentText("Mild Steel")
        page._spin_thickness.setValue(3.0)
        page._spin_rate_per_sqft.setValue(330.0)
        page._spin_length.setValue(8.0)
        page._combo_length_unit.setCurrentText("ft")
        page._spin_width.setValue(4.0)
        page._combo_width_unit.setCurrentText("ft")
        page._spin_quantity.setValue(1)

        # Mock QMessageBox so test doesn't block
        with patch.object(QMessageBox, "information") as mock_info:
            page._on_save()
            assert mock_info.called

        # Verify saved in service
        all_est = estimate_service.get_all_estimates()
        assert len(all_est) == 1
        saved = estimate_service.get_estimate_by_id(all_est[0].id)
        assert saved.customer_name == "Industrial Dynamics Ltd"
        assert saved.customer_address == "Unit 4, Industrial Estate\nShornur"
        assert saved.phone == "+91 99999 88888"
        assert saved.employee_name == "Anand"
        assert saved.calculation_mode == "simple"
        assert saved.rate_per_sqft == 330.0
        assert saved.final_amount == pytest.approx(10560.0)
        assert saved.date == "09/04/2025"

        # Load back into form
        page.reset_form()
        assert page._txt_cust_name.text() == ""
        page.load_estimate(saved, is_edit=True)
        assert page._txt_cust_name.text() == "Industrial Dynamics Ltd"
        assert page._txt_cust_address.toPlainText() == "Unit 4, Industrial Estate\nShornur"
        assert page._txt_employee_name.text() == "Anand"
        assert page._date_edit.date() == QDate(2025, 4, 9)
        assert page._spin_rate_per_sqft.value() == 330.0
        assert page.get_mode() == "simple"

        with patch.object(QMessageBox, "information"):
            page._on_save()
        edited = estimate_service.get_estimate_by_id(saved.id)
        assert edited.date == "09/04/2025"
        assert edited.customer_address == "Unit 4, Industrial Estate\nShornur"
        assert edited.employee_name == "Anand"

    def test_optional_customer_details_can_be_blank(self, qapp, estimate_service, pricing_service):
        page = NewEstimatePage(estimate_service, pricing_service)
        page._txt_cust_name.setText("Walk-in Customer")
        with patch.object(QMessageBox, "information"):
            page._on_save()
        saved = estimate_service.get_estimate_by_id(page._current_estimate_id)
        assert saved.customer_address == ""
        assert saved.employee_name == ""

    def test_material_selectors_are_independent_and_use_settings_catalog(
        self, qapp, estimate_service, pricing_service
    ):
        pricing_service.set_material_density("Aluminium", 2.70)
        pricing_service.set_material_kilo_rate("Aluminium", 410.0)
        pricing_service.add_simple_cutting_rate("Brass", 2.0, "mm", 123.0)
        page = NewEstimatePage(estimate_service, pricing_service)

        assert "Brass" in page._simple_material_combo.itemText(
            page._simple_material_combo.findText("Brass")
        )
        assert page._design_heavy_material_combo.findText("Brass") >= 0
        page._simple_material_combo.setCurrentText("Brass")
        assert page._design_heavy_material_combo.currentText() == "Mild Steel"

        page.set_mode("design_heavy")
        page._design_heavy_material_combo.setCurrentText("Aluminium")
        assert page._simple_material_combo.currentText() == "Brass"
        assert page._spin_kilo_rate.value() == pytest.approx(410.0)
        page._spin_length.setValue(120.0)
        page._combo_length_unit.setCurrentText("cm")
        page._spin_width.setValue(80.0)
        page._combo_width_unit.setCurrentText("cm")
        page._spin_thickness.setValue(1.0)
        page._recalculate()
        assert page._spin_sheet_weight.value() == pytest.approx(2.592, abs=0.01)

        pricing_service.add_simple_cutting_rate("Copper", 3.0, "mm", 100.0)
        page.refresh_material_options()
        assert page._simple_material_combo.findText("Copper") >= 0
        assert page._design_heavy_material_combo.findText("Copper") >= 0
