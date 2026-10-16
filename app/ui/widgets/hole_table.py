"""
Dynamic Hole/Design Charge Table Widget for Laser Estimate.
"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.calculations.hole_calculator import calculate_hole_cost
from app.models.estimate import HoleEntry
from app.services.pricing_service import PricingService
from app.ui.theme import apply_class
from app.ui.widgets.no_wheel_spinbox import NoWheelDoubleSpinBox, NoWheelSpinBox
from app.utils.formatters import format_indian_currency


class HoleTableWidget(QWidget):
    """Dynamic table for adding, editing, and deleting hole/design charges."""

    # Emitted whenever any hole quantity, rate, diameter, or row count changes
    holes_changed = Signal()

    def __init__(
        self,
        pricing_service: PricingService,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._pricing_service = pricing_service
        self._is_updating = False

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header action row
        header_row = QHBoxLayout()
        hint = QLabel("Diameter, unit, quantity and rate per pierce.")
        hint.setProperty("class", "form-hint")
        header_row.addWidget(hint)
        header_row.addStretch()

        btn_add = QPushButton("+ Add Hole")
        apply_class(btn_add, "btn-secondary")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setMinimumHeight(32)
        btn_add.clicked.connect(self.add_row)
        header_row.addWidget(btn_add)

        layout.addLayout(header_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Diameter", "Unit", "Quantity", "Rate / Hole", "Amount", "Delete"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(180)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setMinimumHeight(160)

        layout.addWidget(self._table)

    def add_row(
        self,
        diameter: float = 10.0,
        unit: str = "mm",
        quantity: int = 1,
        rate: Optional[float] = None,
    ) -> int:
        """Add a new hole entry row to the table."""
        row_idx = self._table.rowCount()
        self._table.insertRow(row_idx)

        # Look up default rate for diameter if not explicitly provided
        if rate is None:
            looked_up_rate = self._pricing_service.get_hole_rate_for_diameter(diameter, unit)
            rate = looked_up_rate if looked_up_rate is not None else 10.0

        # 1. Diameter SpinBox
        spin_dia = NoWheelDoubleSpinBox()
        spin_dia.setRange(0.1, 1000.0)
        spin_dia.setDecimals(1)
        spin_dia.setValue(diameter)
        spin_dia.setFixedWidth(90)
        spin_dia.setFixedHeight(30)

        # 2. Unit ComboBox
        combo_unit = QComboBox()
        combo_unit.addItems(["mm", "cm", "in"])
        combo_unit.setCurrentText(unit)
        combo_unit.setFixedWidth(70)
        combo_unit.setFixedHeight(30)

        # 3. Quantity SpinBox
        spin_qty = NoWheelSpinBox()
        spin_qty.setRange(1, 100000)
        spin_qty.setValue(quantity)
        spin_qty.setFixedWidth(80)
        spin_qty.setFixedHeight(30)

        # 4. Rate SpinBox (Allows per-estimate rate override)
        spin_rate = NoWheelDoubleSpinBox()
        spin_rate.setRange(0.0, 10000.0)
        spin_rate.setDecimals(2)
        spin_rate.setPrefix("₹ ")
        spin_rate.setValue(rate)
        spin_rate.setFixedWidth(100)
        spin_rate.setFixedHeight(30)

        # 5. Amount Item (Read-only formatted)
        initial_amount = calculate_hole_cost(quantity, rate)
        item_amt = QTableWidgetItem(format_indian_currency(initial_amount))
        item_amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_amt.setForeground(Qt.darkBlue)

        # 6. Delete Button
        btn_del = QPushButton("Delete")
        apply_class(btn_del, "btn-danger")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setMinimumHeight(28)

        # Set cell widgets
        self._table.setCellWidget(row_idx, 0, spin_dia)
        self._table.setCellWidget(row_idx, 1, combo_unit)
        self._table.setCellWidget(row_idx, 2, spin_qty)
        self._table.setCellWidget(row_idx, 3, spin_rate)
        self._table.setItem(row_idx, 4, item_amt)
        self._table.setCellWidget(row_idx, 5, btn_del)

        # Event connections
        spin_dia.valueChanged.connect(lambda: self._on_diameter_or_unit_changed(row_idx))
        combo_unit.currentTextChanged.connect(lambda: self._on_diameter_or_unit_changed(row_idx))
        spin_qty.valueChanged.connect(lambda: self._on_qty_or_rate_changed(row_idx))
        spin_rate.valueChanged.connect(lambda: self._on_qty_or_rate_changed(row_idx))
        btn_del.clicked.connect(lambda: self._on_delete_row(btn_del))

        if not self._is_updating:
            self.holes_changed.emit()

        return row_idx

    def _on_diameter_or_unit_changed(self, row_idx: int):
        """Lookup default rate when diameter or unit changes if rate hasn't been custom overridden."""
        spin_dia = self._table.cellWidget(row_idx, 0)
        combo_unit = self._table.cellWidget(row_idx, 1)
        spin_rate = self._table.cellWidget(row_idx, 3)

        if spin_dia and combo_unit and spin_rate:
            dia = spin_dia.value()
            unit = combo_unit.currentText()
            rate = self._pricing_service.get_hole_rate_for_diameter(dia, unit)
            if rate is not None:
                spin_rate.setValue(rate)
            self._on_qty_or_rate_changed(row_idx)

    def _on_qty_or_rate_changed(self, row_idx: int):
        """Update amount column and emit change signal."""
        spin_qty = self._table.cellWidget(row_idx, 2)
        spin_rate = self._table.cellWidget(row_idx, 3)
        item_amt = self._table.item(row_idx, 4)

        if spin_qty and spin_rate and item_amt:
            qty = spin_qty.value()
            rate = spin_rate.value()
            amt = calculate_hole_cost(qty, rate)
            item_amt.setText(format_indian_currency(amt))

        if not self._is_updating:
            self.holes_changed.emit()

    def _on_delete_row(self, button: QPushButton):
        """Find row index of button and remove it."""
        for r in range(self._table.rowCount()):
            if self._table.cellWidget(r, 5) == button:
                self._table.removeRow(r)
                break
        if not self._is_updating:
            self.holes_changed.emit()

    def get_holes(self) -> List[HoleEntry]:
        """Extract all hole entries from table rows."""
        entries = []
        for r in range(self._table.rowCount()):
            spin_dia = self._table.cellWidget(r, 0)
            combo_unit = self._table.cellWidget(r, 1)
            spin_qty = self._table.cellWidget(r, 2)
            spin_rate = self._table.cellWidget(r, 3)

            if spin_dia and combo_unit and spin_qty and spin_rate:
                dia = spin_dia.value()
                unit = combo_unit.currentText()
                qty = spin_qty.value()
                rate = spin_rate.value()
                amt = calculate_hole_cost(qty, rate)

                entries.append(
                    HoleEntry(
                        diameter=dia,
                        diameter_unit=unit,
                        quantity=qty,
                        rate=rate,
                        amount=amt,
                    )
                )
        return entries

    def set_holes(self, holes: List[HoleEntry]):
        """Populate table with a list of hole entries."""
        self._is_updating = True
        self._table.setRowCount(0)
        for h in holes:
            self.add_row(
                diameter=h.diameter,
                unit=h.diameter_unit,
                quantity=h.quantity,
                rate=h.rate,
            )
        self._is_updating = False
        self.holes_changed.emit()

    def clear(self):
        """Clear all rows."""
        self._table.setRowCount(0)
        self.holes_changed.emit()
