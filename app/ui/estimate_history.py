"""
Estimate History Page — searchable archive and management of all quotations.
"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.estimate import Estimate
from app.services.estimate_service import EstimateService
from app.services.pricing_service import PricingService
from app.ui.estimate_view import EstimateViewDialog
from app.ui.theme import apply_class
from app.ui.widgets.confirmation_dialog import ConfirmationDialog
from app.ui.widgets.card import CardWidget
from app.utils.formatters import format_indian_currency


class EstimateHistoryPage(QWidget):
    """Estimate history page with real-time search, table listing, and action controls."""

    request_new_estimate = Signal()
    request_edit_estimate = Signal(int)       # estimate_id
    request_duplicate_estimate = Signal(int)  # estimate_id

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
        self._layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("Estimates")
        title.setProperty("class", "page-title")
        title_col.addWidget(title)

        subtitle = QLabel("Search and manage previous quotations")
        subtitle.setProperty("class", "page-subtitle")
        title_col.addWidget(subtitle)

        header_layout.addLayout(title_col, 1)

        btn_new = QPushButton("+ New Estimate")
        apply_class(btn_new, "btn-primary")
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setMinimumHeight(40)
        btn_new.clicked.connect(self.request_new_estimate.emit)
        header_layout.addWidget(btn_new)

        self._layout.addLayout(header_layout)

        # ── Search & Filter Bar Card ────────────────────────────
        search_card = CardWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(12)

        lbl_search_icon = QLabel("🔍")
        lbl_search_icon.setStyleSheet("font-size: 16px;")
        search_layout.addWidget(lbl_search_icon)

        self._txt_search = QLineEdit()
        self._txt_search.setPlaceholderText("Search estimates...")
        self._txt_search.setMinimumHeight(38)
        self._txt_search.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._txt_search, 1)

        btn_clear_search = QPushButton("Clear")
        apply_class(btn_clear_search, "btn-secondary")
        btn_clear_search.setCursor(Qt.PointingHandCursor)
        btn_clear_search.setMinimumHeight(38)
        btn_clear_search.clicked.connect(self._txt_search.clear)
        search_layout.addWidget(btn_clear_search)

        search_card.content_layout.addLayout(search_layout)
        self._layout.addWidget(search_card)

        # ── Table Card ──────────────────────────────────────────
        self._table_card = CardWidget(
            title="Quotations",
            subtitle="Search by estimate number, customer, phone, material, or description",
        )

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Estimate", "Date", "Customer", "Phone", "Material", "Qty", "Amount", "Actions"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self._table.setColumnWidth(7, 388)
        self._table.setMinimumWidth(900)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setMinimumHeight(400)
        self._table_card.content_layout.addWidget(self._table)

        # Empty state label
        self._empty_label = QLabel(
            "No estimates yet. Create your first quotation."
        )
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: #64748B; padding: 48px; font-size: 13px;")
        self._table_card.content_layout.addWidget(self._empty_label)

        self._layout.addWidget(self._table_card)

        scroll_area.setWidget(scroll_content)
        root_layout.addWidget(scroll_area)

        # Initial load
        self.refresh_data()

    def refresh_data(self):
        """Reload estimate records according to current search query."""
        query = self._txt_search.text().strip()
        if query:
            estimates = self._estimate_service.search_estimates(query)
        else:
            estimates = self._estimate_service.get_all_estimates()

        self._populate_table(estimates)

    def _on_search_changed(self, query: str):
        """Filter table reactively as user types."""
        self.refresh_data()

    def _populate_table(self, estimates: List[Estimate]):
        """Render estimate rows in table."""
        if not estimates:
            self._table.setVisible(False)
            self._empty_label.setVisible(True)
            if self._txt_search.text().strip():
                self._empty_label.setText(f"No estimates matching '{self._txt_search.text().strip()}'.")
            else:
                self._empty_label.setText("No estimates created yet. Click '+ New Estimate' to get started.")
        else:
            self._table.setVisible(True)
            self._empty_label.setVisible(False)
            self._table.setRowCount(len(estimates))
            self._table.clearContents()
            self._table.setRowCount(len(estimates))

            for row_idx, est in enumerate(estimates):
                est_id = est.id

                # 0: Estimate #
                item_num = QTableWidgetItem(est.estimate_number)
                item_num.setFont(self.font())
                item_num.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self._table.setItem(row_idx, 0, item_num)

                # 1: Date
                item_date = QTableWidgetItem(est.date or "-")
                item_date.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row_idx, 1, item_date)

                # 2: Customer Name
                cust_name = est.customer_name if est.customer_name else "(Unnamed Customer)"
                item_cust = QTableWidgetItem(cust_name)
                item_cust.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self._table.setItem(row_idx, 2, item_cust)

                # 3: Phone
                item_phone = QTableWidgetItem(est.phone or "-")
                item_phone.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row_idx, 3, item_phone)

                # 4: Material
                item_mat = QTableWidgetItem(est.material or "-")
                item_mat.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self._table.setItem(row_idx, 4, item_mat)

                # 5: Quantity
                item_qty = QTableWidgetItem(str(est.quantity))
                item_qty.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row_idx, 5, item_qty)

                # 6: Final Amount
                amt_str = format_indian_currency(est.final_amount)
                item_amt = QTableWidgetItem(amt_str)
                item_amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_amt.setForeground(Qt.darkGreen)
                self._table.setItem(row_idx, 6, item_amt)

                # 7: Action Buttons Group (View, Edit, Duplicate, Delete)
                actions_widget = QWidget()
                actions_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 0, 4, 0)
                actions_layout.setSpacing(6)
                actions_layout.setAlignment(Qt.AlignVCenter)

                btn_view = QPushButton("View")
                apply_class(btn_view, "btn-secondary")
                btn_view.setCursor(Qt.PointingHandCursor)
                btn_view.setMinimumWidth(80)
                btn_view.setStyleSheet(btn_view.styleSheet().replace("padding: 8px 14px;", "padding: 3px 8px;"))
                btn_view.setFixedHeight(32)
                btn_view.clicked.connect(lambda checked=False, eid=est_id: self._open_view_dialog(eid))
                actions_layout.addWidget(btn_view)

                btn_edit = QPushButton("Edit")
                apply_class(btn_edit, "btn-secondary")
                btn_edit.setCursor(Qt.PointingHandCursor)
                btn_edit.setMinimumWidth(80)
                btn_edit.setStyleSheet(btn_edit.styleSheet().replace("padding: 8px 14px;", "padding: 3px 8px;"))
                btn_edit.setFixedHeight(32)
                btn_edit.clicked.connect(lambda checked=False, eid=est_id: self.request_edit_estimate.emit(eid))
                actions_layout.addWidget(btn_edit)

                btn_dup = QPushButton("Duplicate")
                apply_class(btn_dup, "btn-secondary")
                btn_dup.setCursor(Qt.PointingHandCursor)
                btn_dup.setMinimumWidth(100)
                btn_dup.setStyleSheet(btn_dup.styleSheet().replace("padding: 8px 14px;", "padding: 3px 8px;"))
                btn_dup.setFixedHeight(32)
                btn_dup.clicked.connect(lambda checked=False, eid=est_id: self.request_duplicate_estimate.emit(eid))
                actions_layout.addWidget(btn_dup)

                btn_del = QPushButton("Delete")
                apply_class(btn_del, "btn-danger")
                btn_del.setCursor(Qt.PointingHandCursor)
                btn_del.setToolTip("Delete Estimate")
                btn_del.setMinimumWidth(84)
                btn_del.setStyleSheet(btn_del.styleSheet().replace("padding: 8px 14px;", "padding: 3px 8px;"))
                btn_del.setFixedHeight(32)
                btn_del.clicked.connect(lambda checked=False, eid=est_id, enum=est.estimate_number: self._delete_estimate(eid, enum))
                actions_layout.addWidget(btn_del)

                self._table.setCellWidget(row_idx, 7, actions_widget)
                self._table.setRowHeight(row_idx, 48)

    def _open_view_dialog(self, estimate_id: int):
        """Open quotation view dialog for an estimate."""
        est = self._estimate_service.get_estimate_by_id(estimate_id)
        if est:
            dialog = EstimateViewDialog(
                estimate=est,
                pricing_service=self._pricing_service,
                parent=self.window(),
            )
            dialog.edit_requested.connect(self.request_edit_estimate.emit)
            dialog.duplicate_requested.connect(self.request_duplicate_estimate.emit)
            dialog.exec()

    def _delete_estimate(self, estimate_id: int, estimate_number: str):
        """Prompt confirmation and delete estimate and its hole entries."""
        confirmed = ConfirmationDialog.confirm(
            self,
            "Delete Estimate",
            f"Are you sure you want to delete estimate {estimate_number}?\nThis cannot be undone.",
            confirm_text="Delete",
            destructive=True,
        )
        if confirmed:
            self._estimate_service.delete_estimate(estimate_id)
            self.refresh_data()
            QMessageBox.information(
                self,
                "Deleted",
                f"Quotation {estimate_number} has been deleted.",
            )
