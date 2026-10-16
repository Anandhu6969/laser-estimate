"""
Unit and integration tests for Phase 4 UI Foundation.
"""

import os
from pathlib import Path
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from app.services.database_service import DatabaseService
from app.services.pricing_service import PricingService
from app.services.estimate_service import EstimateService
from app.ui.widgets.card import CardWidget, MetricCardWidget
from app.ui.widgets.sidebar import SidebarWidget
from app.ui.dashboard import DashboardPage
from app.ui.settings_page import SettingsPage
from app.ui.main_window import MainWindow
from app.ui.styles import APP_STYLESHEET
from app.ui.assets import load_logo_pixmap, logo_path
from app.models.estimate import Estimate


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a clean temporary DatabaseService using pytest's tmp_path."""
    db_path = os.path.join(str(tmp_path), "test_ui.db")
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


class TestSidebarWidget:
    def test_company_logo_uses_project_asset_and_loads(self, qapp):
        path = logo_path()
        assert path is not None
        assert Path(path).name == "universallogo.png"
        pixmap = load_logo_pixmap(168, 72)
        assert pixmap is not None and not pixmap.isNull()
        assert pixmap.width() <= 168 and pixmap.height() <= 72

    def test_sidebar_initialization(self, qapp):
        sidebar = SidebarWidget()
        assert sidebar is not None
        assert sidebar.objectName() == "sidebar"
        logo_label = next(
            label for label in sidebar.findChildren(QLabel)
            if label.pixmap() is not None and not label.pixmap().isNull()
        )
        assert int(logo_label.alignment()) & int(Qt.AlignHCenter)

    def test_sidebar_navigation_signals(self, qapp):
        sidebar = SidebarWidget()
        emitted_pages = []
        sidebar.page_selected.connect(emitted_pages.append)

        sidebar._btn_new.click()
        assert emitted_pages == [SidebarWidget.PAGE_NEW_ESTIMATE]

        sidebar._btn_settings.click()
        assert emitted_pages == [SidebarWidget.PAGE_NEW_ESTIMATE, SidebarWidget.PAGE_SETTINGS]

    def test_sidebar_set_active_page(self, qapp):
        sidebar = SidebarWidget()
        sidebar.set_active_page(SidebarWidget.PAGE_SETTINGS)
        assert sidebar._btn_settings.isChecked()
        assert not sidebar._btn_dashboard.isChecked()


class TestCardWidgets:
    def test_card_widget_title(self, qapp):
        card = CardWidget(title="Test Title", subtitle="Test Subtitle")
        assert card._title_label.text() == "Test Title"
        assert card._subtitle_label.text() == "Test Subtitle"

    def test_metric_card_widget(self, qapp):
        metric = MetricCardWidget(
            title="Total Revenue",
            value="₹1,000",
            description="All time",
        )
        assert metric._val_label.text() == "₹1,000"
        metric.set_value("₹5,000")
        assert metric._val_label.text() == "₹5,000"


class TestDashboardPage:
    def test_dashboard_initialization(self, qapp, estimate_service, pricing_service):
        dashboard = DashboardPage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        assert dashboard is not None
        assert dashboard._card_total_estimates._val_label.text() == "0"
        assert "₹250" in dashboard._card_kilo_rate._val_label.text()
        assert "₹30" in dashboard._card_cutting_rate._val_label.text()
        for card in (
            dashboard._card_total_estimates,
            dashboard._card_today_estimates,
            dashboard._card_kilo_rate,
            dashboard._card_cutting_rate,
        ):
            assert not any(label.text() in {"#", "T", "kg", "min"}
                           for label in card.findChildren(QLabel))
        assert "/ kg" in dashboard._card_kilo_rate._val_label.text()
        assert "/ min" in dashboard._card_cutting_rate._val_label.text()

    def test_dashboard_refresh(self, qapp, estimate_service, pricing_service):
        dashboard = DashboardPage(
            estimate_service=estimate_service,
            pricing_service=pricing_service,
        )
        pricing_service.set_default_kilo_rate(300.0)
        pricing_service.set_default_cutting_rate(45.0)

        dashboard.refresh_data()
        assert "₹300" in dashboard._card_kilo_rate._val_label.text()
        assert "₹45" in dashboard._card_cutting_rate._val_label.text()

    def test_recent_estimate_view_action_is_sized_in_its_row(
        self, qapp, estimate_service, pricing_service
    ):
        estimate_service.save_estimate(Estimate(estimate_number="EST-0001", customer_name="Client"))
        dashboard = DashboardPage(estimate_service, pricing_service)
        button = dashboard._table.cellWidget(0, 5)
        assert button.text() == "View"
        assert button.minimumWidth() >= 76
        assert dashboard._table.rowHeight(0) >= button.minimumHeight()
        assert button.maximumHeight() == 32
        assert dashboard._table.rowHeight(0) >= button.maximumHeight()


class TestSettingsPage:
    def test_company_and_bank_settings_save_without_fixed_template_fields(
        self, qapp, pricing_service
    ):
        settings = SettingsPage(pricing_service=pricing_service)
        assert list(settings._company_fields.values()) == ["GSTIN", "Mobile", "Phone", "Email"]
        assert not hasattr(settings, "_txt_company_name")
        assert not hasattr(settings, "_txt_company_address")

        company_values = {
            "company_gstin": "GST-123",
            "company_mobile": "9000000001",
            "company_phone": "9000000002",
            "company_email": "quotes@example.test",
        }
        for key, value in company_values.items():
            settings._company_inputs[key].setText(value)
        settings._save_company_info()
        assert {key: pricing_service.get_setting(key) for key in company_values} == company_values
        reloaded = SettingsPage(pricing_service=pricing_service)
        assert {key: field.text() for key, field in reloaded._company_inputs.items()} == company_values

        reloaded._txt_quotation_terms.setText("Delivery as agreed")
        reloaded._save_quotation_terms()
        assert pricing_service.get_setting("quotation_terms") == "Delivery as agreed"

        bank_values = {
            "bank_account_name": "Universal Agrico",
            "bank_name": "Canara Bank",
            "bank_account_number": "1234567890",
            "bank_branch": "Shornur",
            "bank_ifsc": "CNRB0002554",
        }
        for key, value in bank_values.items():
            settings._bank_inputs[key].setText(value)
        settings._save_bank_details()
        bank_reloaded = SettingsPage(pricing_service=pricing_service)
        assert {key: field.text() for key, field in bank_reloaded._bank_inputs.items()} == bank_values

    def test_global_combo_arrows_and_checkbox_mark_are_styled(self):
        assert "QComboBox::down-arrow" in APP_STYLESHEET
        assert "combo_down.svg" in APP_STYLESHEET
        assert "QCheckBox::indicator:checked" in APP_STYLESHEET
        assert "checkbox_check.svg" in APP_STYLESHEET

    def test_material_rate_grid_rows_and_inputs_are_aligned(self, qapp, pricing_service):
        settings = SettingsPage(pricing_service=pricing_service)
        assert settings._material_table.rowCount() > 0
        for row in range(settings._material_table.rowCount()):
            density = settings._material_table.cellWidget(row, 1)
            kilo = settings._material_table.cellWidget(row, 2)
            assert density.minimumWidth() >= 175
            assert kilo.minimumWidth() >= 205
            assert settings._material_table.rowHeight(row) >= density.minimumHeight()
        assert settings._material_table.columnWidth(1) >= 205
        assert settings._material_table.columnWidth(2) >= 240
        save_button = next(button for button in settings.findChildren(QPushButton)
                           if button.text() == "Save Material Rates && Densities")
        assert save_button.width() <= 280
        assert save_button.minimumHeight() >= 36

    def test_settings_load(self, qapp, pricing_service):
        settings = SettingsPage(pricing_service=pricing_service)
        assert settings._spin_kilo_rate.value() == 250.0
        assert settings._spin_cutting_rate.value() == 30.0

    def test_settings_save_rates(self, qapp, pricing_service):
        settings = SettingsPage(pricing_service=pricing_service)
        settings._spin_kilo_rate.setValue(275.0)
        settings._spin_cutting_rate.setValue(35.0)
        settings._save_rates()

        assert pricing_service.get_default_kilo_rate() == 275.0
        assert pricing_service.get_default_cutting_rate() == 35.0

    def test_settings_hole_rate_controls_are_removed_but_legacy_rates_remain(self, qapp, pricing_service):
        settings = SettingsPage(pricing_service=pricing_service)
        assert not hasattr(settings, "_hole_table")
        assert "Hole / Pierce Rate Matrix (Legacy)" not in [
            label.text() for label in settings.findChildren(QLabel)
        ]
        pricing_service.add_hole_rate(30.0, "mm", 40.0)
        rate = pricing_service.get_hole_rate_for_diameter(30.0, "mm")
        assert rate == 40.0


class TestMainWindow:
    def test_main_window_assembly(self, qapp, temp_db, pricing_service, estimate_service):
        window = MainWindow(
            db_service=temp_db,
            pricing_service=pricing_service,
            estimate_service=estimate_service,
        )
        assert window is not None
        assert window._stack.count() == 4
        assert window._stack.currentIndex() == SidebarWidget.PAGE_DASHBOARD

        # Test page navigation
        window._navigate_to_page(SidebarWidget.PAGE_SETTINGS)
        assert window._stack.currentIndex() == SidebarWidget.PAGE_SETTINGS
        assert window._sidebar._btn_settings.isChecked()
