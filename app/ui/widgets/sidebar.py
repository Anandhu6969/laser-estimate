"""
Sidebar navigation widget for Laser Estimate desktop application.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.assets import load_logo_pixmap
from app.ui.theme import APP_VERSION, apply_class


class SidebarWidget(QWidget):
    """Left navigation sidebar with branding, navigation links, and version."""

    page_selected = Signal(int)

    PAGE_DASHBOARD = 0
    PAGE_NEW_ESTIMATE = 1
    PAGE_HISTORY = 2
    PAGE_SETTINGS = 3

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("sidebarHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 20, 16, 16)
        header_layout.setSpacing(10)

        logo = load_logo_pixmap(168, 72)
        if logo is not None:
            logo_label = QLabel()
            logo_label.setPixmap(logo)
            logo_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            header_layout.addWidget(logo_label)

        title = QLabel("Laser Estimate")
        title.setObjectName("sidebarTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("INDUSTRIAL QUOTATIONS")
        subtitle.setObjectName("sidebarSubtitle")
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        nav_container = QWidget()
        nav_container.setObjectName("sidebarNav")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(6)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        self._btn_dashboard = self._create_nav_button("Dashboard", self.PAGE_DASHBOARD)
        self._btn_new = self._create_nav_button("+  New Estimate", self.PAGE_NEW_ESTIMATE)
        self._btn_history = self._create_nav_button("Estimates", self.PAGE_HISTORY)
        self._btn_settings = self._create_nav_button("Settings", self.PAGE_SETTINGS)

        nav_layout.addWidget(self._btn_dashboard)
        nav_layout.addWidget(self._btn_new)
        nav_layout.addWidget(self._btn_history)
        nav_layout.addWidget(self._btn_settings)
        nav_layout.addStretch()

        layout.addWidget(nav_container, 1)

        footer = QFrame()
        footer.setObjectName("sidebarFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 14, 16, 16)
        footer_layout.setSpacing(4)

        self._lbl_company = QLabel("Laser Estimate")
        self._lbl_company.setObjectName("sidebarFooterText")
        self._lbl_company.setWordWrap(True)
        footer_layout.addWidget(self._lbl_company)

        ver_text = QLabel(f"Version {APP_VERSION}")
        ver_text.setObjectName("sidebarFooterMuted")
        footer_layout.addWidget(ver_text)

        layout.addWidget(footer)

        self.set_active_page(self.PAGE_DASHBOARD)

    def _create_nav_button(self, text: str, page_index: int) -> QPushButton:
        btn = QPushButton(text)
        apply_class(btn, "nav-btn")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(40)
        self._btn_group.addButton(btn, page_index)
        btn.clicked.connect(lambda: self.page_selected.emit(page_index))
        return btn

    def set_active_page(self, page_index: int):
        button = self._btn_group.button(page_index)
        if button:
            button.setChecked(True)

    def set_company_name(self, name: str):
        self._lbl_company.setText(name.strip() or "Laser Estimate")
