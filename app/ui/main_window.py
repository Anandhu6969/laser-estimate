"""
Main Window for Laser Estimate desktop application.
"""

from typing import Optional
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.database_service import DatabaseService
from app.services.estimate_service import EstimateService
from app.services.pricing_service import PricingService
from app.ui.dashboard import DashboardPage
from app.ui.estimate_history import EstimateHistoryPage
from app.ui.estimate_view import EstimateViewDialog
from app.ui.new_estimate import NewEstimatePage
from app.ui.settings_page import SettingsPage
from app.ui.assets import logo_path
from app.ui.styles import APP_STYLESHEET
from app.ui.widgets.sidebar import SidebarWidget
from app.ui.widgets.confirmation_dialog import ConfirmationDialog


class MainWindow(QMainWindow):
    """Primary application window with sidebar navigation and stacked workspace."""

    def __init__(
        self,
        db_service: DatabaseService,
        pricing_service: PricingService,
        estimate_service: EstimateService,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._db_service = db_service
        self._pricing_service = pricing_service
        self._estimate_service = estimate_service

        self._init_window()
        self._init_ui()

    def _init_window(self):
        """Configure main window properties."""
        self.setWindowTitle("Laser Estimate — Industrial Quotation System")
        self.setMinimumSize(1180, 740)
        self.resize(1360, 860)
        self.setStyleSheet(APP_STYLESHEET)
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.setStyle("Fusion")
        icon_file = logo_path()
        if icon_file:
            self.setWindowIcon(QIcon(icon_file))

    def _init_ui(self):
        """Assemble main layout with sidebar and stacked pages."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ─────────────────────────────────────────────
        self._sidebar = SidebarWidget()
        self._sidebar.page_selected.connect(self._navigate_to_page)
        main_layout.addWidget(self._sidebar)

        # ── Stacked Workspace Pages ─────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background-color: #F5F7FA;")

        # Page 0: Dashboard
        self._dashboard_page = DashboardPage(
            estimate_service=self._estimate_service,
            pricing_service=self._pricing_service,
        )
        self._dashboard_page.request_new_estimate.connect(
            lambda: self._navigate_to_new_estimate(reset=True)
        )
        self._dashboard_page.request_view_history.connect(
            lambda: self._navigate_to_page(SidebarWidget.PAGE_HISTORY)
        )
        self._dashboard_page.request_settings.connect(
            lambda: self._navigate_to_page(SidebarWidget.PAGE_SETTINGS)
        )
        self._dashboard_page.request_view_estimate.connect(self._on_view_estimate_from_dashboard)
        self._stack.addWidget(self._dashboard_page)

        # Page 1: New Estimate Page
        self._new_estimate_page = NewEstimatePage(
            estimate_service=self._estimate_service,
            pricing_service=self._pricing_service,
        )
        self._new_estimate_page.estimate_saved.connect(self._on_estimate_saved)
        self._stack.addWidget(self._new_estimate_page)

        # Page 2: Estimate History Page (Phase 6)
        self._history_page = EstimateHistoryPage(
            estimate_service=self._estimate_service,
            pricing_service=self._pricing_service,
        )
        self._history_page.request_new_estimate.connect(
            lambda: self._navigate_to_new_estimate(reset=True)
        )
        self._history_page.request_edit_estimate.connect(self._on_edit_estimate)
        self._history_page.request_duplicate_estimate.connect(self._on_duplicate_estimate)
        self._stack.addWidget(self._history_page)

        # Page 3: Settings
        self._settings_page = SettingsPage(
            pricing_service=self._pricing_service,
        )
        self._settings_page.settings_updated.connect(self._on_settings_updated)
        self._stack.addWidget(self._settings_page)

        main_layout.addWidget(self._stack, 1)

        # Start on dashboard
        self._navigate_to_page(SidebarWidget.PAGE_DASHBOARD)

    def _navigate_to_page(self, index: int):
        """Switch active page and update sidebar selection."""
        self._stack.setCurrentIndex(index)
        self._sidebar.set_active_page(index)

        # Refresh page data upon navigation
        if index == SidebarWidget.PAGE_DASHBOARD:
            self._dashboard_page.refresh_data()
        elif index == SidebarWidget.PAGE_HISTORY:
            self._history_page.refresh_data()
        elif index == SidebarWidget.PAGE_SETTINGS:
            self._settings_page.load_settings()

        company = self._pricing_service.get_setting("company_name", "")
        self._sidebar.set_company_name(company or "Laser Estimate")

    def _navigate_to_new_estimate(self, reset: bool = True):
        """Navigate to new estimate page with optional form reset."""
        if reset:
            self._new_estimate_page.reset_form()
        self._navigate_to_page(SidebarWidget.PAGE_NEW_ESTIMATE)

    def _on_view_estimate_from_dashboard(self, estimate_id: int):
        """Open quotation view dialog directly from dashboard."""
        est = self._estimate_service.get_estimate_by_id(estimate_id)
        if est:
            dialog = EstimateViewDialog(
                estimate=est,
                pricing_service=self._pricing_service,
                parent=self,
            )
            dialog.edit_requested.connect(self._on_edit_estimate)
            dialog.duplicate_requested.connect(self._on_duplicate_estimate)
            dialog.exec()

    def _on_edit_estimate(self, estimate_id: int):
        """Load an existing estimate into the form preserving all original rates."""
        est = self._estimate_service.get_estimate_by_id(estimate_id)
        if est:
            self._new_estimate_page.load_estimate(est, is_edit=True)
            self._navigate_to_page(SidebarWidget.PAGE_NEW_ESTIMATE)

    def _on_duplicate_estimate(self, estimate_id: int):
        """Load a copy of an existing estimate with a new estimate number for editing."""
        original = self._estimate_service.get_estimate_by_id(estimate_id)
        if original:
            original.id = None
            original.estimate_number = self._estimate_service.get_next_estimate_number()
            original.date = datetime.now().strftime("%d/%m/%Y")
            self._new_estimate_page.load_estimate(original, is_edit=False)
            self._navigate_to_page(SidebarWidget.PAGE_NEW_ESTIMATE)

    def _on_estimate_saved(self, estimate_id: int):
        """Callback when an estimate is saved or updated."""
        self._dashboard_page.refresh_data()
        self._history_page.refresh_data()

    def _on_settings_updated(self):
        """Callback when settings are updated."""
        self._dashboard_page.refresh_data()
        self._new_estimate_page.refresh_material_options()
        self._new_estimate_page.refresh_cutting_rate_labels()
        company = self._pricing_service.get_setting("company_name", "")
        self._sidebar.set_company_name(company or "Laser Estimate")

    def closeEvent(self, event: QCloseEvent):
        """Ask once before closing the main application window."""
        if ConfirmationDialog.confirm(
            self,
            "Exit Application",
            "Are you sure you want to close the application?",
            confirm_text="Close",
            cancel_text="Cancel",
        ):
            event.accept()
        else:
            event.ignore()
