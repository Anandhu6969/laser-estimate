"""
Dashboard page for Laser Estimate desktop application.
"""

from typing import Optional
from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.estimate_service import EstimateService
from app.services.pricing_service import PricingService
from app.ui.theme import PRIMARY_BLUE, PRIMARY_RED, apply_class
from app.ui.widgets.card import CardWidget, MetricCardWidget
from app.utils.formatters import format_indian_currency


class DashboardPage(QWidget):
    """Dashboard page showing system overview, stats, and recent estimates."""

    request_new_estimate = Signal()
    request_view_history = Signal()
    request_settings = Signal()
    request_view_estimate = Signal(int)

    def __init__(
        self,
        estimate_service: EstimateService,
        pricing_service: PricingService,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._estimate_service = estimate_service
        self._pricing_service = pricing_service
        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self._layout = QVBoxLayout(scroll_content)
        self._layout.setContentsMargins(24, 20, 24, 24)
        self._layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("Dashboard")
        title.setProperty("class", "page-title")
        title_col.addWidget(title)

        subtitle = QLabel("Quotation overview and recent estimates")
        subtitle.setProperty("class", "page-subtitle")
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col, 1)

        btn_new = QPushButton("+ New Estimate")
        apply_class(btn_new, "btn-primary")
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setMinimumHeight(40)
        btn_new.setMinimumWidth(160)
        btn_new.clicked.connect(self.request_new_estimate.emit)
        header_layout.addWidget(btn_new)

        self._layout.addLayout(header_layout)

        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)

        self._card_total_estimates = MetricCardWidget(
            title="Total Estimates",
            value="0",
            description="Saved quotations",
            accent_color=PRIMARY_BLUE,
        )
        self._card_today_estimates = MetricCardWidget(
            title="Today's Estimates",
            value="0",
            description="Created today",
            accent_color=PRIMARY_RED,
        )
        self._card_kilo_rate = MetricCardWidget(
            title="Material Rate",
            value="₹250 / kg",
            description="Default kilo rate",
            accent_color=PRIMARY_BLUE,
        )
        self._card_cutting_rate = MetricCardWidget(
            title="Cutting Rate",
            value="₹30 / min",
            description="Default laser rate",
            accent_color=PRIMARY_RED,
        )

        metrics_grid.addWidget(self._card_total_estimates, 0, 0)
        metrics_grid.addWidget(self._card_today_estimates, 0, 1)
        metrics_grid.addWidget(self._card_kilo_rate, 0, 2)
        metrics_grid.addWidget(self._card_cutting_rate, 0, 3)
        self._layout.addLayout(metrics_grid)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        btn_new2 = QPushButton("+ New Estimate")
        apply_class(btn_new2, "btn-primary")
        btn_new2.setCursor(Qt.PointingHandCursor)
        btn_new2.setMinimumHeight(40)
        btn_new2.clicked.connect(self.request_new_estimate.emit)
        actions.addWidget(btn_new2)

        btn_view_all = QPushButton("View Estimates")
        apply_class(btn_view_all, "btn-secondary")
        btn_view_all.setCursor(Qt.PointingHandCursor)
        btn_view_all.setMinimumHeight(40)
        btn_view_all.clicked.connect(self.request_view_history.emit)
        actions.addWidget(btn_view_all)
        actions.addStretch()
        self._layout.addLayout(actions)

        header_action_btn = QPushButton("View Estimates")
        apply_class(header_action_btn, "btn-secondary")
        header_action_btn.setCursor(Qt.PointingHandCursor)
        header_action_btn.setMinimumSize(140, 38)
        header_action_btn.clicked.connect(self.request_view_history.emit)

        self._recent_card = CardWidget(
            title="Recent Estimates",
            subtitle="Latest quotations",
            header_action=header_action_btn,
        )

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Estimate No.", "Date", "Customer", "Material", "Amount", "Action"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self._table.setColumnWidth(5, 100)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(240)
        self._recent_card.content_layout.addWidget(self._table)

        self._empty_label = QLabel("No estimates yet\nCreate your first quotation")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: #64748B; padding: 28px; font-size: 14px;")
        self._recent_card.content_layout.addWidget(self._empty_label)

        btn_empty = QPushButton("Create New Estimate")
        apply_class(btn_empty, "btn-primary")
        btn_empty.setCursor(Qt.PointingHandCursor)
        btn_empty.setMinimumHeight(40)
        btn_empty.clicked.connect(self.request_new_estimate.emit)
        self._btn_empty_create = btn_empty
        self._recent_card.content_layout.addWidget(btn_empty, 0, Qt.AlignCenter)

        self._layout.addWidget(self._recent_card)

        rates_card = CardWidget(
            title="Pricing defaults",
            subtitle="Global rates used when a new estimate is created",
        )
        info_banner = QFrame()
        info_banner.setProperty("class", "banner-info")
        info_layout = QVBoxLayout(info_banner)
        info_title = QLabel("Per-estimate rates do not change these defaults")
        info_title.setStyleSheet("font-weight: 700; color: #070799;")
        info_desc = QLabel(
            "Historical quotations keep the kilo rate and cutting rate saved on that job."
        )
        info_desc.setWordWrap(True)
        info_desc.setStyleSheet("color: #1F2937; font-size: 12px;")
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_desc)

        rates_row = QHBoxLayout()
        rates_row.addWidget(info_banner, 2)
        btn_manage_rates = QPushButton("Open Settings")
        apply_class(btn_manage_rates, "btn-secondary")
        btn_manage_rates.setCursor(Qt.PointingHandCursor)
        btn_manage_rates.setMinimumHeight(40)
        btn_manage_rates.clicked.connect(self.request_settings.emit)
        rates_row.addWidget(btn_manage_rates, 0)
        rates_card.content_layout.addLayout(rates_row)
        self._layout.addWidget(rates_card)

        self._layout.addStretch()
        scroll_area.setWidget(scroll_content)
        root_layout.addWidget(scroll_area)
        self.refresh_data()

    def refresh_data(self):
        total_count = self._estimate_service.get_total_count()
        today_count = self._estimate_service.get_today_count()
        kilo_rate = self._pricing_service.get_default_kilo_rate()
        cutting_rate = self._pricing_service.get_default_cutting_rate()

        self._card_total_estimates.set_value(str(total_count))
        self._card_today_estimates.set_value(str(today_count))
        self._card_kilo_rate.set_value(f"₹{kilo_rate:g} / kg")
        self._card_cutting_rate.set_value(f"₹{cutting_rate:g} / min")

        recent = self._estimate_service.get_recent_estimates(limit=5)

        if not recent:
            self._table.setVisible(False)
            self._empty_label.setVisible(True)
            self._btn_empty_create.setVisible(True)
        else:
            self._table.setVisible(True)
            self._empty_label.setVisible(False)
            self._btn_empty_create.setVisible(False)
            self._table.setRowCount(len(recent))
            self._table.clearContents()
            self._table.setRowCount(len(recent))

            for row_idx, est in enumerate(recent):
                item_num = QTableWidgetItem(est.estimate_number)
                item_num.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self._table.setItem(row_idx, 0, item_num)

                item_date = QTableWidgetItem(est.date or "-")
                item_date.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row_idx, 1, item_date)

                cust_name = est.customer_name if est.customer_name else "(Unnamed Customer)"
                item_cust = QTableWidgetItem(cust_name)
                self._table.setItem(row_idx, 2, item_cust)

                item_mat = QTableWidgetItem(est.material if est.material else "-")
                self._table.setItem(row_idx, 3, item_mat)

                item_amt = QTableWidgetItem(format_indian_currency(est.final_amount))
                item_amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self._table.setItem(row_idx, 4, item_amt)

                btn_view = QPushButton("View")
                apply_class(btn_view, "btn-secondary")
                btn_view.setCursor(Qt.PointingHandCursor)
                btn_view.setMinimumWidth(76)
                btn_view.setStyleSheet(btn_view.styleSheet().replace("padding: 8px 14px;", "padding: 3px 8px;"))
                btn_view.setFixedHeight(32)
                est_id = est.id
                btn_view.clicked.connect(lambda checked=False, eid=est_id: self.request_view_estimate.emit(eid))
                self._table.setCellWidget(row_idx, 5, btn_view)
                self._table.setRowHeight(row_idx, 44)
