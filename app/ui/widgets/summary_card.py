"""
Summary Card Widget for displaying real-time calculation breakdown and final quotation.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme import apply_class
from app.utils.formatters import format_indian_currency


class SummaryCardWidget(QWidget):
    """Real-time quotation summary with prominent final amount and dual-mode support."""

    save_requested = Signal()
    reset_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None, show_actions: bool = True):
        super().__init__(parent)
        self._mode = "simple"
        self._show_actions = show_actions
        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        card = QFrame()
        card.setProperty("class", "card")
        self._card_layout = QVBoxLayout(card)
        self._card_layout.setContentsMargins(14, 10, 14, 10)
        self._card_layout.setSpacing(6)

        # Header with Title & Mode Badge
        header_row = QHBoxLayout()
        self._lbl_title = QLabel("QUOTATION SUMMARY")
        self._lbl_title.setStyleSheet("color: #070799; font-size: 13px; font-weight: 800; letter-spacing: 0.8px;")
        header_row.addWidget(self._lbl_title)
        header_row.addStretch()

        self._lbl_mode_badge = QLabel("SIMPLE")
        self._lbl_mode_badge.setStyleSheet(
            "background-color: #EEF2FF; color: #070799; font-size: 11px; "
            "font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid #C7D2FE;"
        )
        header_row.addWidget(self._lbl_mode_badge)
        self._card_layout.addLayout(header_row)

        # ── Common: Dimensions & Area ──────────────────────────
        self._lbl_dim_val = self._create_value_label("0.00 ft × 0.00 ft")
        self._lbl_area_val = self._create_value_label("0.00 sq.ft")
        self._row_dim = self._row("Dimensions", self._lbl_dim_val)
        self._row_area = self._row("Area", self._lbl_area_val)
        self._card_layout.addLayout(self._row_dim)
        self._card_layout.addLayout(self._row_area)

        self._div_common = self._divider()
        self._card_layout.addWidget(self._div_common)

        # ── Simple Mode Specific ───────────────────────────────
        self._widget_simple = QWidget()
        layout_simple = QVBoxLayout(self._widget_simple)
        layout_simple.setContentsMargins(0, 0, 0, 0)
        layout_simple.setSpacing(4)

        self._lbl_simple_mat = self._create_value_label("Mild Steel · 3 mm")
        layout_simple.addLayout(self._row("Material & Thick", self._lbl_simple_mat))

        self._lbl_simple_rate = self._create_amount_label("₹330.00 / sq.ft")
        layout_simple.addLayout(self._row("Rate / sq.ft", self._lbl_simple_rate))

        self._card_layout.addWidget(self._widget_simple)

        # ── Design Heavy Specific ──────────────────────────────
        self._widget_heavy = QWidget()
        layout_heavy = QVBoxLayout(self._widget_heavy)
        layout_heavy.setContentsMargins(0, 0, 0, 0)
        layout_heavy.setSpacing(4)

        # Material Section
        self._cap_mat = QLabel("Material Cost")
        self._cap_mat.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 700;")
        layout_heavy.addWidget(self._cap_mat)

        self._lbl_weight_val = self._create_value_label("0 kg")
        self._lbl_mat_detail = QLabel("0 kg × ₹0")
        self._lbl_mat_detail.setStyleSheet("color: #64748B; font-size: 12px;")
        layout_heavy.addWidget(self._lbl_mat_detail)
        self._lbl_mat_val = self._create_amount_label("₹0")
        layout_heavy.addWidget(self._lbl_mat_val, 0, Qt.AlignRight)

        layout_heavy.addWidget(self._divider())

        # Cutting Section
        self._cap_cut = QLabel("Laser Cutting")
        self._cap_cut.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 700;")
        layout_heavy.addWidget(self._cap_cut)

        self._lbl_cut_time_val = self._create_value_label("0 min")
        self._lbl_cut_detail = QLabel("0 min × ₹0")
        self._lbl_cut_detail.setStyleSheet("color: #64748B; font-size: 12px;")
        layout_heavy.addWidget(self._lbl_cut_detail)
        self._lbl_cut_amt_val = self._create_amount_label("₹0")
        layout_heavy.addWidget(self._lbl_cut_amt_val, 0, Qt.AlignRight)

        # Hole Section (Legacy fallback display if non-zero)
        self._widget_design = QWidget()
        layout_des = QVBoxLayout(self._widget_design)
        layout_des.setContentsMargins(0, 0, 0, 0)
        layout_des.setSpacing(4)
        layout_des.addWidget(self._divider())
        self._cap_des = QLabel("Hole / Design")
        self._cap_des.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 700;")
        layout_des.addWidget(self._cap_des)
        self._lbl_design_val = self._create_amount_label("₹0")
        layout_des.addWidget(self._lbl_design_val, 0, Qt.AlignRight)
        self._widget_design.setVisible(False)
        layout_heavy.addWidget(self._widget_design)

        self._card_layout.addWidget(self._widget_heavy)

        # ── Divider before totals ──────────────────────────────
        self._div_totals = self._divider()
        self._card_layout.addWidget(self._div_totals)

        # ── Per Piece & Quantity ───────────────────────────────
        row_pp = QHBoxLayout()
        lbl_pp_cap = QLabel("PER PIECE")
        lbl_pp_cap.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: 700;")
        row_pp.addWidget(lbl_pp_cap)
        row_pp.addStretch()
        self._lbl_per_piece_val = QLabel("₹0")
        self._lbl_per_piece_val.setStyleSheet("color: #070799; font-size: 16px; font-weight: 800;")
        row_pp.addWidget(self._lbl_per_piece_val)
        self._card_layout.addLayout(row_pp)

        self._lbl_qty_val = self._create_value_label("× 1")
        self._card_layout.addLayout(self._row("QUANTITY", self._lbl_qty_val))

        # ── Prominent Total Banner ─────────────────────────────
        total_banner = QFrame()
        total_banner.setProperty("class", "total-panel")
        total_banner.setStyleSheet(
            "background-color: #070799; border: 1px solid #070799; "
            "border-radius: 6px;"
        )
        total_layout = QVBoxLayout(total_banner)
        total_layout.setContentsMargins(12, 8, 12, 8)
        total_layout.setSpacing(2)

        lbl_total_caption = QLabel("TOTAL ESTIMATE")
        lbl_total_caption.setStyleSheet(
            "color: #FFFFFF; font-size: 11px; font-weight: 700; letter-spacing: 1.2px;"
        )
        lbl_total_caption.setAlignment(Qt.AlignCenter)
        total_layout.addWidget(lbl_total_caption)

        self._lbl_final_total = QLabel("₹0")
        self._lbl_final_total.setStyleSheet(
            "color: #FFFFFF; font-size: 32px; font-weight: 900;"
        )
        self._lbl_final_total.setAlignment(Qt.AlignCenter)
        total_layout.addWidget(self._lbl_final_total)

        self._total_banner = total_banner
        if self._show_actions:
            self._card_layout.addWidget(total_banner)

        # ── Buttons ────────────────────────────────────────────
        self._btn_save = None
        self._btn_reset = None
        if self._show_actions:
            self._btn_save = QPushButton("Save Estimate")
            apply_class(self._btn_save, "btn-primary")
            self._btn_save.setCursor(Qt.PointingHandCursor)
            self._btn_save.setMinimumSize(160, 44)
            self._btn_save.clicked.connect(self.save_requested.emit)
            self._card_layout.addWidget(self._btn_save)

            self._btn_reset = QPushButton("Cancel / Reset")
            apply_class(self._btn_reset, "btn-secondary")
            self._btn_reset.setCursor(Qt.PointingHandCursor)
            self._btn_reset.setMinimumSize(160, 38)
            self._btn_reset.clicked.connect(self.reset_requested.emit)
            self._card_layout.addWidget(self._btn_reset)

        root_layout.addWidget(card)
        self.set_mode("simple")

    def take_total_banner(self):
        """Detach the total panel so a page can keep it visible outside a scroller."""
        if self._show_actions:
            return None
        self._total_banner.setParent(None)
        return self._total_banner

    def set_mode(self, mode: str):
        """Switch view between 'simple' and 'design_heavy' modes."""
        self._mode = mode.lower()
        if self._mode == "simple":
            self._lbl_mode_badge.setText("SIMPLE CUTTING")
            self._lbl_mode_badge.setStyleSheet(
                "background-color: #EEF2FF; color: #070799; font-size: 11px; "
                "font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid #C7D2FE;"
            )
            self._widget_simple.setVisible(True)
            self._widget_heavy.setVisible(False)
        else:
            self._lbl_mode_badge.setText("DESIGN HEAVY")
            self._lbl_mode_badge.setStyleSheet(
                "background-color: #FEF2F2; color: #BF0C10; font-size: 11px; "
                "font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid #FECACA;"
            )
            self._widget_simple.setVisible(False)
            self._widget_heavy.setVisible(True)

    def _row(self, caption: str, value: Optional[QLabel]) -> QHBoxLayout:
        row = QHBoxLayout()
        cap = QLabel(caption)
        cap.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        row.addWidget(cap)
        row.addStretch()
        if value is not None:
            row.addWidget(value)
        return row

    def _create_value_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: 700;")
        return lbl

    def _create_amount_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #070799; font-size: 14px; font-weight: 800;")
        return lbl

    def _divider(self) -> QFrame:
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #E2E8F0; border: none;")
        return divider

    def update_simple_summary(
        self,
        dimensions_text: str,
        area_text: str,
        material_text: str,
        rate_per_sqft: float,
        per_piece_cost: float,
        quantity: int,
        final_total: float,
    ):
        """Update summary in Simple Cutting mode."""
        self.set_mode("simple")
        self._lbl_dim_val.setText(dimensions_text)
        self._lbl_area_val.setText(area_text)
        self._lbl_simple_mat.setText(material_text)
        self._lbl_simple_rate.setText(f"{format_indian_currency(rate_per_sqft)} / sq.ft")
        self._lbl_per_piece_val.setText(format_indian_currency(per_piece_cost))
        self._lbl_qty_val.setText(f"× {quantity}")
        self._lbl_final_total.setText(format_indian_currency(final_total))

    def update_design_heavy_summary(
        self,
        dimensions_text: str,
        area_text: str,
        weight_text: str,
        material_cost: float,
        cutting_time_text: str,
        cutting_cost: float,
        per_piece_cost: float,
        quantity: int,
        final_total: float,
        kilo_rate: Optional[float] = None,
        cutting_rate: Optional[float] = None,
        cutting_method: str = "Air",
        design_cost: float = 0.0,
    ):
        """Update summary in Design Heavy mode."""
        self.set_mode("design_heavy")
        self._lbl_dim_val.setText(dimensions_text)
        self._lbl_area_val.setText(area_text)
        self._lbl_weight_val.setText(weight_text)
        self._lbl_mat_val.setText(format_indian_currency(material_cost))
        if kilo_rate is not None:
            self._lbl_mat_detail.setText(f"{weight_text} × {format_indian_currency(kilo_rate)}/kg")
        else:
            self._lbl_mat_detail.setText(weight_text)

        self._lbl_cut_time_val.setText(cutting_time_text)
        self._lbl_cut_amt_val.setText(format_indian_currency(cutting_cost))
        if cutting_rate is not None:
            self._lbl_cut_detail.setText(f"{cutting_time_text} ({cutting_method}) @ {format_indian_currency(cutting_rate)}/hr")
        else:
            self._lbl_cut_detail.setText(f"{cutting_time_text} ({cutting_method})")

        if design_cost > 0:
            self._widget_design.setVisible(True)
            self._lbl_design_val.setText(format_indian_currency(design_cost))
        else:
            self._widget_design.setVisible(False)

        self._lbl_per_piece_val.setText(format_indian_currency(per_piece_cost))
        self._lbl_qty_val.setText(f"× {quantity}")
        self._lbl_final_total.setText(format_indian_currency(final_total))

    def update_summary(
        self,
        dimensions_text: str,
        area_text: str,
        weight_text: str,
        material_cost: float,
        cutting_time_text: str,
        cutting_cost: float,
        design_cost: float = 0.0,
        per_piece_cost: float = 0.0,
        quantity: int = 1,
        final_total: float = 0.0,
        kilo_rate: Optional[float] = None,
        cutting_rate: Optional[float] = None,
        mode: str = "design_heavy",
        material_text: str = "",
        rate_per_sqft: float = 0.0,
        cutting_method: str = "Air",
    ):
        """Unified update summary for backward compatibility and flexible calling."""
        if mode == "simple":
            self.update_simple_summary(
                dimensions_text=dimensions_text,
                area_text=area_text,
                material_text=material_text,
                rate_per_sqft=rate_per_sqft,
                per_piece_cost=per_piece_cost,
                quantity=quantity,
                final_total=final_total,
            )
        else:
            self.update_design_heavy_summary(
                dimensions_text=dimensions_text,
                area_text=area_text,
                weight_text=weight_text,
                material_cost=material_cost,
                cutting_time_text=cutting_time_text,
                cutting_cost=cutting_cost,
                per_piece_cost=per_piece_cost,
                quantity=quantity,
                final_total=final_total,
                kilo_rate=kilo_rate,
                cutting_rate=cutting_rate,
                cutting_method=cutting_method,
                design_cost=design_cost,
            )

