"""
Tests for Phase 6 — Estimate History, View Dialog, Search, Edit, Duplicate, and Delete.
"""

import os
import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QLabel, QMessageBox, QWidget

from app.services.database_service import DatabaseService
from app.services.pricing_service import PricingService
from app.services.estimate_service import EstimateService
from app.models.estimate import Estimate, HoleEntry
from app.ui.estimate_history import EstimateHistoryPage
from app.ui.estimate_view import EstimateViewDialog
from app.ui.main_window import MainWindow
from app.ui.styles import APP_STYLESHEET
from app.ui.widgets.sidebar import SidebarWidget
from app.ui.widgets.confirmation_dialog import ConfirmationDialog
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
    db_path = os.path.join(str(tmp_path), "test_history.db")
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


@pytest.fixture
def sample_estimate(estimate_service):
    """Create and save a sample estimate for testing."""
    est = Estimate(
        estimate_number="EST-0001",
        customer_name="Apollo Steel Fabricators",
        phone="+91 98765 00001",
        date="20/09/2026",
        description="Bracket enclosure panel",
        length=120.0,
        length_unit="cm",
        width=80.0,
        width_unit="cm",
        length_ft=3.937,
        width_ft=2.625,
        area_sqft=10.33,
        material="SS 304",
        thickness=3.0,
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
        holes=[
            HoleEntry(diameter=5.0, diameter_unit="mm", quantity=10, rate=8.0, amount=80.0),
            HoleEntry(diameter=10.0, diameter_unit="mm", quantity=15, rate=12.0, amount=180.0),
            HoleEntry(diameter=15.0, diameter_unit="mm", quantity=9, rate=15.0, amount=135.0),
        ],
    )
    est_id = estimate_service.save_estimate(est)
    est.id = est_id
    return est


class TestEstimateViewDialog:
    def test_view_dialog_rendering(self, qapp, sample_estimate, pricing_service):
        dialog = EstimateViewDialog(
            estimate=sample_estimate,
            pricing_service=pricing_service,
        )
        assert dialog is not None
        assert sample_estimate.estimate_number in dialog.windowTitle()

    def test_total_panel_is_styled_independently_of_opening_parent(
        self, qapp, sample_estimate, pricing_service
    ):
        dashboard_parent = QWidget()
        dashboard_parent.setStyleSheet(APP_STYLESHEET)
        history_parent = QWidget()
        history_parent.setStyleSheet(APP_STYLESHEET)
        dialogs = [
            EstimateViewDialog(sample_estimate, pricing_service, parent=parent)
            for parent in (dashboard_parent, history_parent)
        ]

        panels = [
            next(frame for frame in dialog.findChildren(QFrame)
                 if frame.property("class") == "total-panel")
            for dialog in dialogs
        ]
        assert dialogs[0].styleSheet() == dialogs[1].styleSheet()
        assert panels[0].styleSheet() == panels[1].styleSheet()
        assert "#070799" in panels[0].styleSheet()
        assert "border-top" not in panels[0].styleSheet()
        for dialog in dialogs:
            dialog.resize(1000, 760)
            dialog.show()
        qapp.processEvents()
        assert dialogs[0].grab().toImage() == dialogs[1].grab().toImage()
        for dialog in dialogs:
            labels = {label.text(): label.styleSheet() for label in dialog.findChildren(QLabel)}
            assert "color: #FFFFFF" in labels[
                f"Per Piece: {format_indian_currency(sample_estimate.per_piece_amount)}"
            ]
            assert "color: #FFFFFF" in labels[
                format_indian_currency(sample_estimate.final_amount)
            ]

    def test_history_view_dialog_uses_top_level_window_parent(
        self, qapp, sample_estimate, estimate_service, pricing_service
    ):
        top_level = QWidget()
        stack_page = QWidget(top_level)
        history_page = EstimateHistoryPage(estimate_service, pricing_service, parent=stack_page)
        dialog = Mock()

        with patch("app.ui.estimate_history.EstimateViewDialog", return_value=dialog) as factory:
            history_page._open_view_dialog(sample_estimate.id)

        assert factory.call_args.kwargs["parent"] is top_level


class TestEstimateHistoryPage:
    def test_action_buttons_fit_inside_fixed_actions_column(
        self, qapp, sample_estimate, estimate_service, pricing_service
    ):
        history_page = EstimateHistoryPage(estimate_service, pricing_service)
        for index in (2, 3):
            estimate_service.save_estimate(Estimate(estimate_number=f"EST-000{index + 1}"))
        history_page.refresh_data()
        history_page.resize(1500, 900)
        history_page.show()
        qapp.processEvents()

        assert history_page._table.rowCount() == 3
        assert history_page._table.columnWidth(7) >= 370
        for row in range(history_page._table.rowCount()):
            actions = history_page._table.cellWidget(row, 7)
            assert actions.layout().spacing() == 6
            buttons = [actions.layout().itemAt(i).widget()
                       for i in range(actions.layout().count())]
            widths = [button.minimumWidth() for button in buttons if button is not None]
            assert [button.text() for button in buttons] == ["View", "Edit", "Duplicate", "Delete"]
            assert widths == [80, 80, 100, 84]
            assert history_page._table.rowHeight(row) == 48
            assert actions.height() <= history_page._table.rowHeight(row)
            for button in buttons:
                assert button.geometry().top() >= 0
                assert button.geometry().bottom() < actions.height()
                assert button.height() > 0

    def test_history_empty_state(self, qapp, estimate_service, pricing_service):
        history_page = EstimateHistoryPage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        assert history_page._table.isHidden() is True
        assert history_page._empty_label.isHidden() is False

    def test_history_table_population(self, qapp, sample_estimate, estimate_service, pricing_service):
        history_page = EstimateHistoryPage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        history_page.refresh_data()
        assert history_page._table.isHidden() is False
        assert history_page._table.rowCount() == 1
        assert history_page._table.item(0, 0).text() == "EST-0001"
        assert history_page._table.item(0, 2).text() == "Apollo Steel Fabricators"
        assert "₹7,545" in history_page._table.item(0, 6).text()

    def test_history_search_filter(self, qapp, sample_estimate, estimate_service, pricing_service):
        history_page = EstimateHistoryPage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        # Search match
        history_page._txt_search.setText("Apollo")
        assert history_page._table.rowCount() == 1

        # Search no match
        history_page._txt_search.setText("NonExistentClient")
        assert history_page._table.isHidden() is True
        assert history_page._empty_label.isHidden() is False

        # Clear search
        history_page._txt_search.clear()
        assert history_page._table.isHidden() is False
        assert history_page._table.rowCount() == 1

    def test_history_delete_estimate(self, qapp, sample_estimate, estimate_service, pricing_service):
        history_page = EstimateHistoryPage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        history_page.refresh_data()
        assert history_page._table.rowCount() == 1

        # Mock confirm dialog as Yes
        with patch("app.ui.estimate_history.ConfirmationDialog.confirm", return_value=True), \
             patch.object(QMessageBox, "information"):
            history_page._delete_estimate(sample_estimate.id, sample_estimate.estimate_number)

        assert history_page._table.isHidden() is True
        assert estimate_service.get_total_count() == 0


class TestMainWindowHistoryIntegration:
    def test_confirmation_dialog_buttons_and_brand_styling(self, qapp):
        dialog = ConfirmationDialog(
            "Delete Estimate", "Remove EST-0001?", "Delete", destructive=True
        )
        assert dialog.windowTitle() == "Delete Estimate"
        assert dialog.findChild(QLabel, "dialogMessage").text() == "Remove EST-0001?"
        assert "#FFFFFF" in dialog.styleSheet()
        assert "#BF0C10" in dialog.confirm_button.styleSheet()
        assert "#070799" in dialog.cancel_button.styleSheet()
        dialog.cancel_button.click()
        assert dialog.result() == QDialog.DialogCode.Rejected

        dialog = ConfirmationDialog("Exit", "Close?", "Close")
        assert "#070799" in dialog.confirm_button.styleSheet()
        dialog.confirm_button.click()
        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_canceling_delete_keeps_estimate(self, qapp, sample_estimate, estimate_service, pricing_service):
        history_page = EstimateHistoryPage(estimate_service, pricing_service)
        history_page.refresh_data()
        with patch("app.ui.estimate_history.ConfirmationDialog.confirm", return_value=False) as confirm:
            history_page._delete_estimate(sample_estimate.id, sample_estimate.estimate_number)
        confirm.assert_called_once()
        assert estimate_service.get_total_count() == 1

    def test_main_window_close_requires_confirmation(self, qapp, temp_db, pricing_service, estimate_service):
        window = MainWindow(temp_db, pricing_service, estimate_service)
        window.show()
        with patch("app.ui.main_window.ConfirmationDialog.confirm", return_value=False) as confirm:
            assert not window.close()
            assert window.isVisible()
        confirm.assert_called_once()

        with patch("app.ui.main_window.ConfirmationDialog.confirm", return_value=True) as confirm:
            assert window.close()
            assert not window.isVisible()
        confirm.assert_called_once()

    def test_edit_flow_rate_preservation(self, qapp, temp_db, pricing_service, estimate_service, sample_estimate):
        """Editing an estimate loads historical rates without replacing them with current Settings."""
        # Change global setting rates
        pricing_service.set_default_kilo_rate(999.0)
        pricing_service.set_default_cutting_rate(888.0)

        window = MainWindow(
            db_service=temp_db,
            pricing_service=pricing_service,
            estimate_service=estimate_service,
        )

        # Trigger edit
        window._on_edit_estimate(sample_estimate.id)
        assert window._stack.currentIndex() == SidebarWidget.PAGE_NEW_ESTIMATE

        # Verify preserved rates
        assert window._new_estimate_page._spin_kilo_rate.value() == 250.0
        assert window._new_estimate_page._spin_cutting_rate.value() == 30.0

        # Update description and save edit
        window._new_estimate_page._txt_desc.setText("Updated description")
        with patch.object(QMessageBox, "information"):
            window._new_estimate_page._on_save()

        # Check that it updated the existing record, did not create duplicate
        assert estimate_service.get_total_count() == 1
        updated = estimate_service.get_estimate_by_id(sample_estimate.id)
        assert updated.description == "Updated description"
        assert updated.kilo_rate == 250.0

    def test_duplicate_flow(self, qapp, temp_db, pricing_service, estimate_service, sample_estimate):
        """Duplicating an estimate creates a new estimate number and increments total."""
        window = MainWindow(
            db_service=temp_db,
            pricing_service=pricing_service,
            estimate_service=estimate_service,
        )

        # Trigger duplicate
        window._on_duplicate_estimate(sample_estimate.id)
        assert window._stack.currentIndex() == SidebarWidget.PAGE_NEW_ESTIMATE

        # Should have new number EST-0002
        assert window._new_estimate_page._txt_est_number.text() == "EST-0002"
        assert window._new_estimate_page._current_estimate_id is None
        assert window._new_estimate_page._date_edit.date() == QDate.currentDate()

        # Save duplicate
        with patch.object(QMessageBox, "information"):
            window._new_estimate_page._on_save()

        assert estimate_service.get_total_count() == 2
