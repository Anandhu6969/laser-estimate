"""
Estimate View Dialog — displays a formatted, professional quotation summary for a saved estimate.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
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
    QMessageBox,
)

from app.calculations.sheet_calculator import calculate_sheet_weight
from app.models.estimate import Estimate
from app.services.pricing_service import PricingService
from app.services.quotation_pdf_service import (
    QuotationPdfService,
    ensure_pdf_extension,
    quotation_filename,
)
from app.ui.assets import load_logo_pixmap
from app.ui.styles import APP_STYLESHEET
from app.ui.theme import PRIMARY_BLUE, apply_class
from app.ui.widgets.card import CardWidget
from app.utils.formatters import (
    format_area,
    format_dimensions_ft,
    format_indian_currency,
    format_time,
    format_weight,
)


class EstimateViewDialog(QDialog):
    """Quotation-style read-only view dialog for an estimate."""

    edit_requested = Signal(int)       # Emits estimate_id
    duplicate_requested = Signal(int)  # Emits estimate_id

    def __init__(
        self,
        estimate: Estimate,
        pricing_service: PricingService,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._estimate = estimate
        self._pricing_service = pricing_service

        self._init_window()
        self._init_ui()

    def _init_window(self):
        self.setWindowTitle(f"Estimate Quotation — {self._estimate.estimate_number}")
        self.setMinimumSize(820, 700)
        self.resize(900, 800)
        # A history page can carry its own stacked-page background stylesheet.
        # Make labels transparent within this dialog so that ancestor colors
        # cannot paint opaque bands behind quotation values.
        self.setStyleSheet(
            APP_STYLESHEET + "\nQDialog QLabel { background-color: transparent; }"
        )

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll area for quotation content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # ── Quotation Document Header ───────────────────────────
        header_card = QFrame(content_widget)
        header_card.setProperty("class", "card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(16)

        logo = load_logo_pixmap(120, 56)
        if logo is not None:
            logo_label = QLabel()
            logo_label.setPixmap(logo)
            header_layout.addWidget(logo_label)

        company_col = QVBoxLayout()
        company_col.setSpacing(2)

        company_name = self._pricing_service.get_setting("company_name", "LASER ESTIMATE")
        if not company_name:
            company_name = "LASER ESTIMATE"

        lbl_company = QLabel(company_name)
        lbl_company.setStyleSheet("color: #070799; font-size: 18px; font-weight: 800;")
        company_col.addWidget(lbl_company)

        company_phone = self._pricing_service.get_setting("company_phone", "")
        company_addr = self._pricing_service.get_setting("company_address", "")
        if company_phone or company_addr:
            details = " • ".join(filter(None, [company_phone, company_addr]))
            lbl_comp_details = QLabel(details)
            lbl_comp_details.setStyleSheet("color: #64748B; font-size: 12px;")
            company_col.addWidget(lbl_comp_details)

        header_layout.addLayout(company_col)
        header_layout.addStretch()

        quot_col = QVBoxLayout()
        quot_col.setSpacing(2)
        quot_col.setAlignment(Qt.AlignRight)

        lbl_doc_type = QLabel("QUOTATION")
        lbl_doc_type.setStyleSheet("color: #BF0C10; font-size: 12px; font-weight: 800; letter-spacing: 1.4px;")
        lbl_doc_type.setAlignment(Qt.AlignRight)
        quot_col.addWidget(lbl_doc_type)

        lbl_num = QLabel(self._estimate.estimate_number)
        lbl_num.setStyleSheet("color: #070799; font-size: 20px; font-weight: 800;")
        lbl_num.setAlignment(Qt.AlignRight)
        quot_col.addWidget(lbl_num)

        lbl_date = QLabel(f"Date: {self._estimate.date}")
        lbl_date.setStyleSheet("color: #64748B; font-size: 12px;")
        lbl_date.setAlignment(Qt.AlignRight)
        quot_col.addWidget(lbl_date)

        header_layout.addLayout(quot_col)
        layout.addWidget(header_card)

        # ── Quotation Type Badge ────────────────────────────────
        mode_badge = QLabel(f"MODE: {('SIMPLE CUTTING' if self._estimate.calculation_mode == 'simple' else 'DESIGN HEAVY')}")
        mode_badge.setStyleSheet(
            "background-color: #EEF2FF; color: #070799; font-weight: 800; font-size: 11px; "
            "padding: 4px 10px; border-radius: 4px; border: 1px solid #C7D2FE; max-width: 140px;"
        )
        layout.addWidget(mode_badge)

        # ── Customer Details Card ───────────────────────────────
        cust_card = CardWidget(title="Customer & Job Details", parent=content_widget)
        cust_grid = QGridLayout()
        cust_grid.setSpacing(12)

        cust_grid.addWidget(self._create_field_label("Customer Name:"), 0, 0)
        cust_grid.addWidget(self._create_val_label(self._estimate.customer_name or "—"), 0, 1)

        cust_grid.addWidget(self._create_field_label("Phone Number:"), 0, 2)
        cust_grid.addWidget(self._create_val_label(self._estimate.phone or "—"), 0, 3)

        cust_grid.addWidget(self._create_field_label("Job Description:"), 1, 0)
        cust_grid.addWidget(self._create_val_label(self._estimate.description or "—"), 1, 1, 1, 3)

        cust_card.content_layout.addLayout(cust_grid)
        layout.addWidget(cust_card)

        if self._estimate.calculation_mode == "simple":
            # ── Simple Cutting Specifications Card ──────────────
            specs_card = CardWidget(title="Simple Cutting Specifications", parent=content_widget)
            specs_grid = QGridLayout()
            specs_grid.setSpacing(12)

            dim_raw = f"{self._estimate.length:g} {self._estimate.length_unit} × {self._estimate.width:g} {self._estimate.width_unit}"
            dim_ft = format_dimensions_ft(self._estimate.length_ft, self._estimate.width_ft)
            specs_grid.addWidget(self._create_field_label("Part Dimensions:"), 0, 0)
            specs_grid.addWidget(self._create_val_label(f"{dim_raw} ({dim_ft})"), 0, 1)

            specs_grid.addWidget(self._create_field_label("Total Area:"), 0, 2)
            specs_grid.addWidget(self._create_val_label(format_area(self._estimate.area_sqft)), 0, 3)

            specs_grid.addWidget(self._create_field_label("Material:"), 1, 0)
            specs_grid.addWidget(self._create_val_label(self._estimate.material or "—"), 1, 1)

            thick_str = f"{self._estimate.thickness:g} {self._estimate.thickness_unit}" if self._estimate.thickness else "—"
            specs_grid.addWidget(self._create_field_label("Thickness:"), 1, 2)
            specs_grid.addWidget(self._create_val_label(thick_str), 1, 3)

            rate_sqft_val = getattr(self._estimate, "rate_per_sqft", 0.0) or 0.0
            specs_grid.addWidget(self._create_field_label("Rate per Sq.Ft:"), 2, 0)
            specs_grid.addWidget(self._create_val_label(f"₹{rate_sqft_val:g} / sq.ft"), 2, 1)

            specs_grid.addWidget(self._create_field_label("Formula:"), 2, 2)
            specs_grid.addWidget(self._create_val_label(f"{self._estimate.area_sqft:.2f} sq.ft × ₹{rate_sqft_val:g}/sq.ft"), 2, 3)

            specs_card.content_layout.addLayout(specs_grid)
            layout.addWidget(specs_card)
        else:
            # ── Design Heavy Specifications & Breakdown ─────────
            specs_card = CardWidget(title="Part Specifications & Weight", parent=content_widget)
            specs_grid = QGridLayout()
            specs_grid.setSpacing(12)

            dim_raw = f"{self._estimate.length:g} {self._estimate.length_unit} × {self._estimate.width:g} {self._estimate.width_unit}"
            dim_ft = format_dimensions_ft(self._estimate.length_ft, self._estimate.width_ft)
            specs_grid.addWidget(self._create_field_label("Cutting Dimensions:"), 0, 0)
            specs_grid.addWidget(self._create_val_label(f"{dim_raw} ({dim_ft})"), 0, 1)

            specs_grid.addWidget(self._create_field_label("Calculated Area:"), 0, 2)
            specs_grid.addWidget(self._create_val_label(format_area(self._estimate.area_sqft)), 0, 3)

            thick_str = f"{self._estimate.thickness:g} {self._estimate.thickness_unit}" if self._estimate.thickness else "—"
            specs_grid.addWidget(self._create_field_label("Material / Grade:"), 1, 0)
            specs_grid.addWidget(self._create_val_label(self._estimate.material or "—"), 1, 1)

            specs_grid.addWidget(self._create_field_label("Thickness:"), 1, 2)
            specs_grid.addWidget(self._create_val_label(thick_str), 1, 3)

            specs_grid.addWidget(self._create_field_label("Part Weight:"), 2, 0)
            specs_grid.addWidget(self._create_val_label(format_weight(self._estimate.sheet_weight)), 2, 1)

            specs_grid.addWidget(self._create_field_label("Material Density:"), 2, 2)
            density_val = getattr(self._estimate, "material_density", 7.85) or 7.85
            specs_grid.addWidget(self._create_val_label(f"{density_val:g} kg/L"), 2, 3)

            rate_text = f"₹{self._estimate.kilo_rate:g}/kg  →  {format_indian_currency(self._estimate.material_amount)}"
            specs_grid.addWidget(self._create_field_label("Kilo Rate & Amount:"), 3, 0)
            specs_grid.addWidget(self._create_val_label(rate_text), 3, 1, 1, 3)

            specs_card.content_layout.addLayout(specs_grid)
            layout.addWidget(specs_card)

            # ── Laser Cutting Operation ─────────────────────────
            cutting_card = CardWidget(title="Laser Cutting Operation", parent=content_widget)
            cut_grid = QGridLayout()
            cut_grid.setSpacing(12)

            method = getattr(self._estimate, "cutting_method", "air") or "air"
            cut_grid.addWidget(self._create_field_label("Cutting Method:"), 0, 0)
            cut_grid.addWidget(self._create_val_label(method.upper()), 0, 1)

            cut_time_str = format_time(self._estimate.total_cutting_min)
            cut_grid.addWidget(self._create_field_label("Cutting Time:"), 0, 2)
            cut_grid.addWidget(self._create_val_label(cut_time_str), 0, 3)

            hourly_rate = getattr(self._estimate, "cutting_rate_per_hour", 0.0) or (self._estimate.cutting_rate * 60.0)
            cut_rate_text = f"₹{hourly_rate:g}/hour  →  {format_indian_currency(self._estimate.cutting_amount)}"
            cut_grid.addWidget(self._create_field_label("Hourly Rate & Cost:"), 1, 0)
            cut_grid.addWidget(self._create_val_label(cut_rate_text), 1, 1, 1, 3)

            cutting_card.content_layout.addLayout(cut_grid)
            layout.addWidget(cutting_card)

        # ── Laser Holes / Design Charges Table (Legacy fallback) ──
        if self._estimate.holes:
            holes_card = CardWidget(title="Laser Hole / Pierce Charges (Legacy)", parent=content_widget)
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Hole Diameter", "Unit", "Quantity", "Rate (₹/hole)", "Amount (₹)"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setRowCount(len(self._estimate.holes))
            table.setMinimumHeight(120)

            for r_idx, h in enumerate(self._estimate.holes):
                item_dia = QTableWidgetItem(f"{h.diameter:g}")
                item_unit = QTableWidgetItem(h.diameter_unit)
                item_qty = QTableWidgetItem(str(h.quantity))
                item_rate = QTableWidgetItem(f"₹{h.rate:g}")
                item_amt = QTableWidgetItem(format_indian_currency(h.amount))

                item_unit.setTextAlignment(Qt.AlignCenter)
                item_qty.setTextAlignment(Qt.AlignCenter)
                item_rate.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                table.setItem(r_idx, 0, item_dia)
                table.setItem(r_idx, 1, item_unit)
                table.setItem(r_idx, 2, item_qty)
                table.setItem(r_idx, 3, item_rate)
                table.setItem(r_idx, 4, item_amt)

            holes_card.content_layout.addWidget(table)

            # Hole total row
            hole_tot_row = QHBoxLayout()
            hole_tot_row.addStretch()
            lbl_htot = QLabel(f"Total Design / Hole Charges: {format_indian_currency(self._estimate.design_amount)}")
            lbl_htot.setStyleSheet("color: #1E40AF; font-weight: 700; font-size: 13px;")
            hole_tot_row.addWidget(lbl_htot)
            holes_card.content_layout.addLayout(hole_tot_row)

            layout.addWidget(holes_card)

        # ── Final Quotation Breakdown Box ───────────────────────
        summary_banner = QFrame()
        summary_banner.setObjectName("estimateViewTotalPanel")
        summary_banner.setProperty("class", "total-panel")
        # The class property is assigned after the dialog stylesheet is active.
        # Give this dynamic-property widget an explicit style so its blue
        # background does not depend on stylesheet repolishing in the parent.
        summary_banner.setStyleSheet(
            f"QFrame#estimateViewTotalPanel {{ background-color: {PRIMARY_BLUE}; "
            f"border: 1px solid {PRIMARY_BLUE}; border-radius: 6px; }}"
        )
        sum_layout = QVBoxLayout(summary_banner)
        sum_layout.setSpacing(8)
        sum_layout.setContentsMargins(18, 14, 18, 14)

        qty_line = QHBoxLayout()
        lbl_pp = QLabel(f"Per Piece: {format_indian_currency(self._estimate.per_piece_amount)}")
        lbl_pp.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600;")
        qty_line.addWidget(lbl_pp)
        qty_line.addStretch()
        lbl_qty = QLabel(f"Quantity: {self._estimate.quantity}")
        lbl_qty.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600;")
        qty_line.addWidget(lbl_qty)
        sum_layout.addLayout(qty_line)

        final_line = QHBoxLayout()
        lbl_fin_title = QLabel("TOTAL ESTIMATE")
        lbl_fin_title.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800; letter-spacing: 1px;")
        final_line.addWidget(lbl_fin_title)
        final_line.addStretch()
        lbl_fin_amt = QLabel(format_indian_currency(self._estimate.final_amount))
        lbl_fin_amt.setStyleSheet("color: #FFFFFF; font-size: 32px; font-weight: 800;")
        final_line.addWidget(lbl_fin_amt)
        sum_layout.addLayout(final_line)

        layout.addWidget(summary_banner)

        scroll_area.setWidget(content_widget)
        root_layout.addWidget(scroll_area, 1)

        # ── Bottom Action Bar ───────────────────────────────────
        action_bar = QFrame()
        action_bar.setStyleSheet("background-color: #FFFFFF; border-top: 1px solid #E2E8F0; padding: 14px 24px;")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setSpacing(12)

        btn_edit = QPushButton("Edit Estimate")
        apply_class(btn_edit, "btn-primary")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setMinimumHeight(38)
        btn_edit.clicked.connect(self._on_edit)
        action_layout.addWidget(btn_edit)

        btn_dup = QPushButton("Duplicate")
        apply_class(btn_dup, "btn-secondary")
        btn_dup.setCursor(Qt.PointingHandCursor)
        btn_dup.setMinimumHeight(38)
        btn_dup.clicked.connect(self._on_duplicate)
        action_layout.addWidget(btn_dup)

        btn_pdf = QPushButton("Generate PDF")
        apply_class(btn_pdf, "btn-primary")
        btn_pdf.setCursor(Qt.PointingHandCursor)
        btn_pdf.setMinimumHeight(38)
        btn_pdf.clicked.connect(self._generate_pdf)
        action_layout.addWidget(btn_pdf)

        action_layout.addStretch()

        btn_close = QPushButton("Close")
        apply_class(btn_close, "btn-ghost")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setMinimumHeight(38)
        btn_close.clicked.connect(self.accept)
        action_layout.addWidget(btn_close)

        root_layout.addWidget(action_bar)

        # Dynamic class selectors need a polish pass after all unparented
        # children are attached to this dialog's stylesheet scope.
        for widget in (self, *self.findChildren(QWidget)):
            if widget.property("class"):
                style = widget.style()
                style.unpolish(widget)
                style.polish(widget)
                widget.update()

    def _generate_pdf(self):
        filename = quotation_filename(self._estimate.estimate_number)
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Quotation",
            filename,
            "PDF Files (*.pdf)",
        )
        if not selected_path:
            return
        path = ensure_pdf_extension(selected_path)
        settings = self._pricing_service.get_all_settings()
        try:
            QuotationPdfService.generate(self._estimate, settings, path)
        except Exception as exc:
            QMessageBox.critical(self, "PDF Generation Failed", f"Could not generate the quotation PDF.\n\n{exc}")
            return
        QMessageBox.information(self, "PDF Generated", f"Quotation PDF generated successfully.\n\nSaved to:\n{path}")

    def _create_field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        return lbl

    def _create_val_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #0F172A; font-size: 13px; font-weight: 700;")
        return lbl

    def _on_edit(self):
        self.accept()
        if self._estimate.id:
            self.edit_requested.emit(self._estimate.id)

    def _on_duplicate(self):
        self.accept()
        if self._estimate.id:
            self.duplicate_requested.emit(self._estimate.id)
