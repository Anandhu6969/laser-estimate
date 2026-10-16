# -*- coding: utf-8 -*-
"""
New Estimate form page for Laser Estimate desktop application.
Supports two quotation modes:
1. Simple Cutting: Final price = Area (sq.ft) * Rate per sq.ft
2. Design Heavy: Final price = Weight (from customer dims) * Kilo Rate + Cutting Time * Hourly Rate
"""

from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.calculations.area_calculator import calculate_area
from app.calculations.cutting_calculator import (
    calculate_cutting_cost,
    calculate_cutting_cost_hourly,
    time_to_hours,
    time_to_minutes,
)
from app.calculations.estimate_calculator import (
    calculate_design_heavy_estimate,
    calculate_estimate,
    calculate_simple_estimate,
)
from app.calculations.hole_calculator import calculate_total_hole_cost
from app.calculations.sheet_calculator import (
    DEFAULT_DENSITY,
    calculate_material_cost,
    calculate_part_weight,
    calculate_sheet_weight,
    get_material_density,
)
from app.calculations.unit_converter import to_feet, to_mm
from app.models.estimate import Estimate, HoleEntry
from app.runtime_paths import resource_path
from app.services.estimate_service import EstimateService
from app.services.pricing_service import PricingService
from app.ui.theme import PRIMARY_BLUE, PRIMARY_RED, WHITE, apply_class
from app.ui.widgets.card import CardWidget
from app.ui.widgets.hole_table import HoleTableWidget
from app.ui.widgets.no_wheel_spinbox import NoWheelDoubleSpinBox, NoWheelSpinBox
from app.ui.widgets.summary_card import SummaryCardWidget
from app.utils.formatters import (
    format_area,
    format_dimensions_ft,
    format_indian_currency,
    format_time,
    format_weight,
)
from app.utils.validators import (
    validate_non_negative_number,
    validate_positive_integer,
    validate_positive_number,
)


class NewEstimatePage(QWidget):
    """New / Edit Estimate page with reactive calculations for Simple Cutting and Design Heavy modes."""

    estimate_saved = Signal(int)  # Emits saved estimate ID

    def __init__(
        self,
        estimate_service: EstimateService,
        pricing_service: PricingService,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._estimate_service = estimate_service
        self._pricing_service = pricing_service
        self._current_estimate_id: Optional[int] = None
        self._calculation_mode = "simple"
        self._is_calculating = False
        self._user_edited_simple_rate = False

        self._init_ui()
        self._setup_keyboard_navigation()
        self.reset_form()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 16, 16, 16)
        root_layout.setSpacing(12)

        # ── Page Header ────────────────────────────────────────
        header_layout = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        self._lbl_page_title = QLabel("New Estimate")
        self._lbl_page_title.setProperty("class", "page-title")
        title_col.addWidget(self._lbl_page_title)

        self._lbl_page_subtitle = QLabel("Create a quotation for laser cutting work")
        self._lbl_page_subtitle.setProperty("class", "page-subtitle")
        title_col.addWidget(self._lbl_page_subtitle)

        header_layout.addLayout(title_col, 1)

        meta_col = QVBoxLayout()
        meta_col.setSpacing(8)

        est_row = QHBoxLayout()
        lbl_est = QLabel("Estimate No.")
        lbl_est.setProperty("class", "form-label")
        self._txt_est_number = QLineEdit()
        self._txt_est_number.setReadOnly(True)
        self._txt_est_number.setMinimumWidth(150)
        self._txt_est_number.setFixedHeight(32)
        est_row.addWidget(lbl_est)
        est_row.addWidget(self._txt_est_number)
        meta_col.addLayout(est_row)

        date_row = QHBoxLayout()
        self._lbl_date = QLabel("Date")
        self._lbl_date.setProperty("class", "form-label")
        self._date_edit = QDateEdit()
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_edit.setCalendarPopup(False)
        self._date_edit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._date_edit.setMinimumWidth(150)
        self._date_edit.setFixedHeight(32)
        self._date_edit.setDate(QDate.currentDate())
        self._txt_date = self._date_edit  # Backward-compatible field alias.

        calendar_icon_path = resource_path("app", "ui", "assets", "calendar.svg")
        self._date_calendar_action = self._date_edit.lineEdit().addAction(
            QIcon(str(calendar_icon_path)), QLineEdit.TrailingPosition
        )
        self._date_calendar_action.setToolTip("Select estimate date")
        self._date_calendar_action.triggered.connect(self._open_date_picker)
        date_row.addWidget(self._lbl_date)
        date_row.addWidget(self._date_edit)
        meta_col.addLayout(date_row)

        header_layout.addLayout(meta_col)
        root_layout.addLayout(header_layout)

        # ── Notification Banner ────────────────────────────────
        self._banner = QFrame()
        self._banner.setProperty("class", "banner-success")
        banner_layout = QHBoxLayout(self._banner)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        self._banner_label = QLabel("Estimate saved successfully.")
        self._banner_label.setStyleSheet("color: #065F46; font-weight: 600;")
        banner_layout.addWidget(self._banner_label)
        self._banner.setVisible(False)
        root_layout.addWidget(self._banner)

        # ── Mode Selector Bar ──────────────────────────────────
        mode_card = QFrame()
        mode_card.setStyleSheet(
            "background-color: #FFFFFF; border: 1px solid #D9DEE7; "
            "border-radius: 8px; padding: 6px 12px;"
        )
        mode_layout = QHBoxLayout(mode_card)
        mode_layout.setContentsMargins(12, 6, 12, 6)
        mode_layout.setSpacing(16)

        lbl_mode = QLabel("Quotation Type:")
        lbl_mode.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: 700;")
        mode_layout.addWidget(lbl_mode)

        self._btn_mode_simple = QPushButton("  Simple Cutting (Area × ₹/sq.ft)  ")
        self._btn_mode_simple.setCursor(Qt.PointingHandCursor)
        self._btn_mode_simple.setMinimumHeight(36)
        self._btn_mode_simple.setCheckable(True)
        self._btn_mode_simple.setChecked(True)
        self._btn_mode_simple.clicked.connect(lambda: self.set_calculation_mode("simple"))
        mode_layout.addWidget(self._btn_mode_simple)

        self._btn_mode_heavy = QPushButton("  Design Heavy (Weight + Machine Time)  ")
        self._btn_mode_heavy.setCursor(Qt.PointingHandCursor)
        self._btn_mode_heavy.setMinimumHeight(36)
        self._btn_mode_heavy.setCheckable(True)
        self._btn_mode_heavy.setChecked(False)
        self._btn_mode_heavy.clicked.connect(lambda: self.set_calculation_mode("design_heavy"))
        mode_layout.addWidget(self._btn_mode_heavy)

        mode_layout.addStretch()
        root_layout.addWidget(mode_card)

        # ── Main Workspace ─────────────────────────────────────
        workspace = QHBoxLayout()
        workspace.setSpacing(16)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_content = QWidget()
        left_col = QVBoxLayout(left_content)
        left_col.setContentsMargins(0, 0, 8, 8)
        left_col.setSpacing(16)

        # Section Cards
        left_col.addWidget(self._create_customer_card())
        left_col.addWidget(self._create_dimensions_card())

        # Simple mode card
        self._card_simple_pricing = self._create_simple_pricing_card()
        left_col.addWidget(self._card_simple_pricing)

        # Design Heavy mode cards
        self._card_heavy_material = self._create_heavy_material_card()
        left_col.addWidget(self._card_heavy_material)

        self._card_heavy_pricing = self._create_heavy_pricing_card()
        left_col.addWidget(self._card_heavy_pricing)

        self._card_heavy_cutting = self._create_heavy_cutting_card()
        left_col.addWidget(self._card_heavy_cutting)

        # Legacy / hidden holes card for backward compatibility
        self._card_holes = self._create_holes_card()
        self._card_holes.setVisible(False)
        left_col.addWidget(self._card_holes)

        left_col.addStretch()
        left_scroll.setWidget(left_content)
        workspace.addWidget(left_scroll, 75)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        right_scroll.setMinimumWidth(340)
        right_scroll.setMaximumWidth(420)
        right_content = QWidget()
        right_col = QVBoxLayout(right_content)
        right_col.setContentsMargins(0, 0, 4, 8)
        right_col.setSpacing(10)

        right_col.addWidget(self._create_quantity_card())
        self._summary_card = SummaryCardWidget(show_actions=False)
        self._summary_card.save_requested.connect(self._on_save)
        self._summary_card.reset_requested.connect(self.reset_form)
        right_col.addWidget(self._summary_card)
        right_scroll.setWidget(right_content)

        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 4, 8)
        right_panel_layout.setSpacing(10)
        right_panel_layout.addWidget(right_scroll, 1)
        right_panel_layout.addWidget(self._summary_card.take_total_banner())

        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        btn_save_estimate = QPushButton("Save Estimate")
        apply_class(btn_save_estimate, "btn-primary")
        btn_save_estimate.setCursor(Qt.PointingHandCursor)
        btn_save_estimate.setMinimumSize(155, 42)
        btn_save_estimate.clicked.connect(self._summary_card.save_requested.emit)
        action_layout.addWidget(btn_save_estimate, 1)

        btn_reset_estimate = QPushButton("Cancel / Reset")
        apply_class(btn_reset_estimate, "btn-secondary")
        btn_reset_estimate.setCursor(Qt.PointingHandCursor)
        btn_reset_estimate.setMinimumSize(155, 42)
        btn_reset_estimate.clicked.connect(self._summary_card.reset_requested.emit)
        action_layout.addWidget(btn_reset_estimate, 1)
        right_panel_layout.addLayout(action_layout)
        workspace.addWidget(right_panel, 25)

        root_layout.addLayout(workspace, 1)

        self._layout = left_col
        self._update_mode_ui_state()

    def _setup_keyboard_navigation(self):
        """Configure seamless tab ordering across active inputs."""
        QWidget.setTabOrder(self._txt_cust_name, self._txt_cust_address)
        QWidget.setTabOrder(self._txt_cust_address, self._txt_phone)
        QWidget.setTabOrder(self._txt_phone, self._txt_employee_name)
        QWidget.setTabOrder(self._txt_employee_name, self._txt_desc)
        QWidget.setTabOrder(self._txt_desc, self._spin_length)
        QWidget.setTabOrder(self._spin_length, self._combo_length_unit)
        QWidget.setTabOrder(self._combo_length_unit, self._spin_width)
        QWidget.setTabOrder(self._spin_width, self._combo_width_unit)
        QWidget.setTabOrder(self._combo_width_unit, self._simple_material_combo)
        QWidget.setTabOrder(self._simple_material_combo, self._spin_thickness)
        QWidget.setTabOrder(self._spin_thickness, self._spin_rate_per_sqft)
        QWidget.setTabOrder(self._spin_rate_per_sqft, self._spin_quantity)

        # Return key auto-advance
        self._txt_cust_name.returnPressed.connect(self._txt_cust_address.setFocus)
        self._txt_phone.returnPressed.connect(self._txt_employee_name.setFocus)
        self._txt_employee_name.returnPressed.connect(self._txt_desc.setFocus)
        self._txt_desc.returnPressed.connect(self._spin_length.setFocus)

    # ── Section Card Builders ───────────────────────────────────

    def _create_customer_card(self) -> QWidget:
        card = CardWidget(
            title="Customer & Job Details",
            subtitle="Client identification for this quotation",
        )

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)

        lbl_cust = QLabel("Customer Name")
        lbl_cust.setProperty("class", "form-label")
        self._txt_cust_name = QLineEdit()
        self._txt_cust_name.setPlaceholderText("e.g. Bharat Heavy Metal Works")
        self._txt_cust_name.setMinimumWidth(180)
        self._txt_cust_name.setMinimumHeight(34)
        grid.addWidget(lbl_cust, 0, 0)
        grid.addWidget(self._txt_cust_name, 0, 1)

        lbl_address = QLabel("Customer Address")
        lbl_address.setProperty("class", "form-label")
        self._txt_cust_address = QTextEdit()
        self._txt_cust_address.setPlaceholderText("Customer address")
        self._txt_cust_address.setFixedHeight(62)
        self._txt_cust_address.setTabChangesFocus(True)
        grid.addWidget(lbl_address, 1, 0)
        grid.addWidget(self._txt_cust_address, 1, 1)

        lbl_phone = QLabel("Customer Phone")
        lbl_phone.setProperty("class", "form-label")
        self._txt_phone = QLineEdit()
        self._txt_phone.setPlaceholderText("e.g. +91 98200 11223")
        self._txt_phone.setMinimumWidth(180)
        self._txt_phone.setMinimumHeight(34)
        grid.addWidget(lbl_phone, 2, 0)
        grid.addWidget(self._txt_phone, 2, 1)

        lbl_employee = QLabel("Employee Name / Generated By")
        lbl_employee.setProperty("class", "form-label")
        self._txt_employee_name = QLineEdit()
        self._txt_employee_name.setMinimumHeight(34)
        grid.addWidget(lbl_employee, 3, 0)
        grid.addWidget(self._txt_employee_name, 3, 1)

        lbl_desc = QLabel("Job Description")
        lbl_desc.setProperty("class", "form-label")
        self._txt_desc = QLineEdit()
        self._txt_desc.setPlaceholderText("e.g. Precision laser cut baffle plate")
        self._txt_desc.setMinimumHeight(34)
        grid.addWidget(lbl_desc, 4, 0)
        grid.addWidget(self._txt_desc, 4, 1)

        card.content_layout.addLayout(grid)
        return card

    def _create_dimensions_card(self) -> QWidget:
        card = CardWidget(
            title="Part Dimensions",
            subtitle="Enter part size in customer's unit — automatic live conversion to sq.ft",
        )

        grid = QGridLayout()
        grid.setSpacing(14)

        # Length Input + Unit
        lbl_len = QLabel("Length")
        lbl_len.setProperty("class", "form-label")
        self._spin_length = NoWheelDoubleSpinBox()
        self._spin_length.setRange(0.01, 100000.0)
        self._spin_length.setDecimals(2)
        self._spin_length.setMinimumWidth(145)
        self._spin_length.setValue(120.0)
        self._spin_length.setFixedHeight(34)
        self._spin_length.valueChanged.connect(self._on_dimensions_changed)

        self._combo_length_unit = QComboBox()
        self._combo_length_unit.addItems(["cm", "mm", "in", "ft"])
        self._combo_length_unit.setCurrentText("cm")
        self._combo_length_unit.setFixedHeight(34)
        self._combo_length_unit.setFixedWidth(80)
        self._combo_length_unit.currentTextChanged.connect(self._on_dimensions_changed)

        len_box = QHBoxLayout()
        len_box.addWidget(self._spin_length, 1)
        len_box.addWidget(self._combo_length_unit)

        grid.addWidget(lbl_len, 0, 0)
        grid.addLayout(len_box, 0, 1)

        # Width Input + Unit
        lbl_width = QLabel("Width")
        lbl_width.setProperty("class", "form-label")
        self._spin_width = NoWheelDoubleSpinBox()
        self._spin_width.setRange(0.01, 100000.0)
        self._spin_width.setDecimals(2)
        self._spin_width.setMinimumWidth(145)
        self._spin_width.setValue(80.0)
        self._spin_width.setFixedHeight(34)
        self._spin_width.valueChanged.connect(self._on_dimensions_changed)

        self._combo_width_unit = QComboBox()
        self._combo_width_unit.addItems(["cm", "mm", "in", "ft"])
        self._combo_width_unit.setCurrentText("cm")
        self._combo_width_unit.setFixedHeight(34)
        self._combo_width_unit.setFixedWidth(80)
        self._combo_width_unit.currentTextChanged.connect(self._on_dimensions_changed)

        width_box = QHBoxLayout()
        width_box.addWidget(self._spin_width, 1)
        width_box.addWidget(self._combo_width_unit)

        grid.addWidget(lbl_width, 0, 2)
        grid.addLayout(width_box, 0, 3)

        card.content_layout.addLayout(grid)

        # Converted Dimensions Live Banner
        live_conv_box = QFrame()
        live_conv_box.setProperty("class", "banner-info")
        live_layout = QVBoxLayout(live_conv_box)
        live_layout.setContentsMargins(14, 10, 14, 10)
        live_layout.setSpacing(6)

        dimensions_row = QHBoxLayout()
        lbl_conv_title = QLabel("Converted Dimensions:")
        lbl_conv_title.setStyleSheet("color: #070799; font-weight: 700; font-size: 12px;")
        dimensions_row.addWidget(lbl_conv_title)

        self._lbl_dim_converted = QLabel("3.94 ft × 2.62 ft")
        self._lbl_dim_converted.setStyleSheet("color: #070799; font-weight: 700; font-size: 14px;")
        dimensions_row.addWidget(self._lbl_dim_converted)
        dimensions_row.addStretch()
        live_layout.addLayout(dimensions_row)

        area_row = QHBoxLayout()
        lbl_area_title = QLabel("Area:")
        lbl_area_title.setStyleSheet("color: #070799; font-weight: 700; font-size: 12px;")
        area_row.addWidget(lbl_area_title)

        self._lbl_area_converted = QLabel("10.33 sq.ft")
        self._lbl_area_converted.setStyleSheet("color: #070799; font-weight: 800; font-size: 14px;")
        area_row.addWidget(self._lbl_area_converted)
        area_row.addStretch()
        live_layout.addLayout(area_row)

        card.content_layout.addWidget(live_conv_box)
        return card

    def _create_simple_pricing_card(self) -> QWidget:
        """Card for Simple Cutting mode: Material + Thickness -> Rate/sq.ft."""
        card = CardWidget(
            title="Material & Simple Cutting Pricing",
            subtitle="Rate per square foot looked up automatically from configured matrix",
        )

        grid = QGridLayout()
        grid.setSpacing(14)

        # Material
        lbl_mat = QLabel("Material:")
        lbl_mat.setProperty("class", "form-label")
        self._simple_material_combo = QComboBox()
        self._simple_material_combo.addItems(self._pricing_service.get_configured_materials())
        self._simple_material_combo.setCurrentText("Mild Steel")
        self._simple_material_combo.setFixedHeight(34)
        self._simple_material_combo.currentTextChanged.connect(self._on_material_or_thickness_changed)
        grid.addWidget(lbl_mat, 0, 0)
        grid.addWidget(self._simple_material_combo, 0, 1)

        # Thickness
        lbl_thick = QLabel("Thickness (mm)")
        lbl_thick.setProperty("class", "form-label")
        self._spin_thickness = NoWheelDoubleSpinBox()
        self._spin_thickness.setRange(0.01, 1000.0)
        self._spin_thickness.setDecimals(2)
        self._spin_thickness.setMinimumWidth(145)
        self._spin_thickness.setValue(3.0)
        self._spin_thickness.setFixedHeight(34)
        self._spin_thickness.setSuffix(" mm")
        self._spin_thickness.valueChanged.connect(self._on_material_or_thickness_changed)

        self._combo_thick_unit = QComboBox()
        self._combo_thick_unit.addItems(["mm", "cm", "in", "gauge"])
        self._combo_thick_unit.setCurrentText("mm")
        self._combo_thick_unit.setFixedHeight(34)
        self._combo_thick_unit.setVisible(False)  # keep for backward compatibility

        grid.addWidget(lbl_thick, 0, 2)
        grid.addWidget(self._spin_thickness, 0, 3)

        # Rate per sq.ft
        lbl_sqft_rate = QLabel("Rate / sq.ft")
        lbl_sqft_rate.setProperty("class", "form-label")
        self._spin_rate_per_sqft = NoWheelDoubleSpinBox()
        self._spin_rate_per_sqft.setRange(0.0, 100000.0)
        self._spin_rate_per_sqft.setDecimals(2)
        self._spin_rate_per_sqft.setMinimumWidth(225)
        self._spin_rate_per_sqft.setPrefix("₹ ")
        self._spin_rate_per_sqft.setSuffix(" / sq.ft")
        self._spin_rate_per_sqft.setValue(330.0)
        self._spin_rate_per_sqft.setFixedHeight(36)
        self._spin_rate_per_sqft.valueChanged.connect(self._on_simple_rate_user_edited)
        grid.addWidget(lbl_sqft_rate, 1, 0)
        grid.addWidget(self._spin_rate_per_sqft, 1, 1)

        self._lbl_rate_source = QLabel("Rate source: Settings matrix")
        self._lbl_rate_source.setStyleSheet("color: #070799; font-size: 12px; font-weight: 600;")
        self._lbl_rate_source.setWordWrap(True)
        grid.addWidget(self._lbl_rate_source, 1, 2, 1, 2)

        card.content_layout.addLayout(grid)

        # Simple Subtotal Banner
        sub_box = QFrame()
        sub_box.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 10px;"
        )
        sub_layout = QHBoxLayout(sub_box)
        sub_layout.setContentsMargins(12, 8, 12, 8)

        lbl_simple_formula = QLabel("Formula: Area (sq.ft) × Rate per sq.ft")
        lbl_simple_formula.setStyleSheet("color: #64748B; font-weight: 600; font-size: 12px;")
        sub_layout.addWidget(lbl_simple_formula)
        sub_layout.addStretch()

        self._lbl_simple_subtotal = QLabel("Per Piece: ₹0")
        self._lbl_simple_subtotal.setStyleSheet("color: #070799; font-weight: 800; font-size: 16px;")
        self._lbl_simple_per_piece = self._lbl_simple_subtotal
        sub_layout.addWidget(self._lbl_simple_subtotal)

        card.content_layout.addWidget(sub_box)
        return card

    def _create_heavy_material_card(self) -> QWidget:
        """Card for Design Heavy mode: Material, Density, Part Weight from dimensions."""
        card = CardWidget(
            title="Material & Part Weight (Design Heavy)",
            subtitle="Weight calculated from customer dimensions & configured density",
        )

        grid = QGridLayout()
        grid.setSpacing(14)

        material_row = QHBoxLayout()
        material_label = QLabel("Material:")
        material_label.setProperty("class", "form-label")
        material_row.addWidget(material_label)
        self._design_heavy_material_combo = QComboBox()
        self._design_heavy_material_combo.addItems(self._pricing_service.get_configured_materials())
        self._design_heavy_material_combo.setCurrentText("Mild Steel")
        self._design_heavy_material_combo.setMinimumWidth(220)
        self._design_heavy_material_combo.setFixedHeight(34)
        self._design_heavy_material_combo.currentTextChanged.connect(
            self._on_design_heavy_material_changed
        )
        material_row.addWidget(self._design_heavy_material_combo)
        material_row.addStretch()
        card.content_layout.addLayout(material_row)

        # Calculated Weight Banner
        calc_weight_box = QFrame()
        calc_weight_box.setProperty("class", "weight-panel")
        calc_layout = QVBoxLayout(calc_weight_box)
        calc_layout.setContentsMargins(16, 12, 16, 12)
        calc_layout.setSpacing(4)

        top_w = QHBoxLayout()
        lbl_calc_title = QLabel("Calculated Part Weight (Customer Dimensions)")
        lbl_calc_title.setStyleSheet("color: #070799; font-weight: 700; font-size: 13px;")
        top_w.addWidget(lbl_calc_title)
        top_w.addStretch()
        self._lbl_density_info = QLabel("Density: 7.85 kg/L (Mild Steel)")
        self._lbl_density_info.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        top_w.addWidget(self._lbl_density_info)
        calc_layout.addLayout(top_w)

        self._lbl_calc_weight = QLabel("7.54 kg")
        self._lbl_calc_weight.setStyleSheet("color: #070799; font-weight: 800; font-size: 28px;")
        calc_layout.addWidget(self._lbl_calc_weight)

        self._lbl_effective_weight = QLabel("Effective weight: 7.54 kg")
        self._lbl_effective_weight.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: 600;")
        calc_layout.addWidget(self._lbl_effective_weight)

        card.content_layout.addWidget(calc_weight_box)

        # Manual Override Box
        override_box = QFrame()
        override_box.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; "
            "border-radius: 8px; padding: 10px;"
        )
        override_layout = QHBoxLayout(override_box)
        override_layout.setContentsMargins(12, 6, 12, 6)
        override_layout.setSpacing(16)

        self._chk_override_weight = QCheckBox("Override calculated weight manually")
        self._chk_override_weight.setStyleSheet("font-weight: 600; color: #1F2937;")
        self._chk_override_weight.toggled.connect(self._on_override_toggled)
        override_layout.addWidget(self._chk_override_weight)

        self._lbl_override_status = QLabel("Using calculated weight")
        self._lbl_override_status.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        override_layout.addWidget(self._lbl_override_status)

        lbl_manual = QLabel("Manual Weight:")
        lbl_manual.setProperty("class", "form-label")
        override_layout.addWidget(lbl_manual)

        self._spin_manual_weight = NoWheelDoubleSpinBox()
        self._spin_manual_weight.setRange(0.0, 100000.0)
        self._spin_manual_weight.setDecimals(2)
        self._spin_manual_weight.setSuffix(" kg")
        self._spin_manual_weight.setValue(7.54)
        self._spin_manual_weight.setFixedHeight(34)
        self._spin_manual_weight.setFixedWidth(130)
        self._spin_manual_weight.setMinimumWidth(145)
        self._spin_manual_weight.setEnabled(False)
        self._spin_manual_weight.valueChanged.connect(self._recalculate)
        override_layout.addWidget(self._spin_manual_weight)

        override_layout.addStretch()
        card.content_layout.addWidget(override_box)

        # Hidden stock sheet length/width spinboxes for backward compatibility with old tests
        self._spin_sheet_len = QDoubleSpinBox()
        self._spin_sheet_len.setRange(0.0, 100000.0)
        self._spin_sheet_len.setValue(2000.0)
        self._spin_sheet_len.setVisible(False)
        self._spin_sheet_width = QDoubleSpinBox()
        self._spin_sheet_width.setRange(0.0, 100000.0)
        self._spin_sheet_width.setValue(1000.0)
        self._spin_sheet_width.setVisible(False)
        self._spin_sheet_weight = QDoubleSpinBox()
        self._spin_sheet_weight.setRange(0.0, 100000.0)
        self._spin_sheet_weight.setValue(7.54)
        self._spin_sheet_weight.setVisible(False)

        return card

    def _create_heavy_pricing_card(self) -> QWidget:
        """Material Pricing for Design Heavy mode."""
        card = CardWidget(
            title="Material Pricing",
            subtitle="Weight (kg) × Configured Kilo Rate",
        )

        grid = QGridLayout()
        grid.setSpacing(14)

        lbl_kilo_rate = QLabel("Kilo Rate")
        lbl_kilo_rate.setProperty("class", "form-label")
        self._spin_kilo_rate = NoWheelDoubleSpinBox()
        self._spin_kilo_rate.setRange(0.0, 100000.0)
        self._spin_kilo_rate.setDecimals(2)
        self._spin_kilo_rate.setMinimumWidth(220)
        self._spin_kilo_rate.setPrefix("₹ ")
        self._spin_kilo_rate.setSuffix(" / kg")
        self._spin_kilo_rate.setValue(
            self._pricing_service.get_material_kilo_rate(
                self._design_heavy_material_combo.currentText()
            )
        )
        self._spin_kilo_rate.setFixedHeight(34)
        self._spin_kilo_rate.valueChanged.connect(self._recalculate)
        grid.addWidget(lbl_kilo_rate, 0, 0)
        grid.addWidget(self._spin_kilo_rate, 0, 1)

        self._lbl_kilo_default = QLabel("Loaded from Settings. You can edit for this estimate.")
        self._lbl_kilo_default.setProperty("class", "form-hint")
        grid.addWidget(self._lbl_kilo_default, 0, 2, 1, 2)

        card.content_layout.addLayout(grid)

        # Material Subtotal Banner
        mat_sub_box = QFrame()
        mat_sub_box.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 10px;"
        )
        mat_sub_layout = QHBoxLayout(mat_sub_box)
        mat_sub_layout.setContentsMargins(10, 6, 10, 6)

        lbl_sub = QLabel("Material Cost Subtotal:")
        lbl_sub.setStyleSheet("color: #475569; font-weight: 600; font-size: 12px;")
        mat_sub_layout.addWidget(lbl_sub)
        mat_sub_layout.addStretch()

        self._lbl_mat_subtotal = QLabel("₹0")
        self._lbl_mat_subtotal.setStyleSheet("color: #0F172A; font-weight: 700; font-size: 14px;")
        mat_sub_layout.addWidget(self._lbl_mat_subtotal)

        card.content_layout.addWidget(mat_sub_box)
        return card

    def _create_heavy_cutting_card(self) -> QWidget:
        """Laser Cutting Card for Design Heavy mode."""
        card = CardWidget(
            title="Laser Cutting Operation",
            subtitle="Machine cutting time and cutting rate (Air / Oxygen / Custom)",
        )

        grid = QGridLayout()
        grid.setSpacing(14)

        # Cutting Method Selector
        lbl_method = QLabel("Cutting Method:")
        lbl_method.setProperty("class", "form-label")
        grid.addWidget(lbl_method, 0, 0)

        method_layout = QHBoxLayout()
        method_layout.setSpacing(14)
        self._radio_air = QRadioButton("Air (₹1,500/hr)")
        self._radio_air.setChecked(True)
        self._radio_air.toggled.connect(self._on_cutting_method_changed)
        method_layout.addWidget(self._radio_air)

        self._radio_oxygen = QRadioButton("Oxygen (₹1,800/hr)")
        self._radio_oxygen.toggled.connect(self._on_cutting_method_changed)
        method_layout.addWidget(self._radio_oxygen)

        self._radio_custom = QRadioButton("Custom Rate")
        self._radio_custom.toggled.connect(self._on_cutting_method_changed)
        method_layout.addWidget(self._radio_custom)
        self._update_cutting_method_labels()

        self._spin_custom_rate = NoWheelDoubleSpinBox()
        self._spin_custom_rate.setRange(0.0, 100000.0)
        self._spin_custom_rate.setDecimals(2)
        self._spin_custom_rate.setPrefix("₹ ")
        self._spin_custom_rate.setSuffix(" / hr")
        self._spin_custom_rate.setValue(2000.0)
        self._spin_custom_rate.setFixedHeight(34)
        self._spin_custom_rate.setFixedWidth(130)
        self._spin_custom_rate.setMinimumWidth(170)
        self._spin_custom_rate.setEnabled(False)
        self._spin_custom_rate.valueChanged.connect(self._recalculate)
        self._spin_cutting_rate_hourly = self._spin_custom_rate
        method_layout.addWidget(self._spin_custom_rate)
        method_layout.addStretch()

        grid.addLayout(method_layout, 0, 1, 1, 3)

        # Hours & Minutes
        lbl_time = QLabel("Cutting Time:")
        lbl_time.setProperty("class", "form-label")

        time_box = QHBoxLayout()
        self._spin_hours = NoWheelSpinBox()
        self._spin_hours.setRange(0, 1000)
        self._spin_hours.setMinimumWidth(110)
        self._spin_hours.setSuffix(" hrs")
        self._spin_hours.setValue(0)
        self._spin_hours.setFixedHeight(34)
        self._spin_hours.valueChanged.connect(self._recalculate)

        self._spin_minutes = NoWheelSpinBox()
        self._spin_minutes.setRange(0, 59)
        self._spin_minutes.setMinimumWidth(115)
        self._spin_minutes.setSuffix(" mins")
        self._spin_minutes.setValue(30)
        self._spin_minutes.setFixedHeight(34)
        self._spin_minutes.valueChanged.connect(self._recalculate)

        time_box.addWidget(self._spin_hours)
        time_box.addWidget(self._spin_minutes)

        grid.addWidget(lbl_time, 1, 0)
        grid.addLayout(time_box, 1, 1)

        self._lbl_effective_cut_rate = QLabel("Effective Rate: ₹1,500 / hour")
        self._lbl_effective_cut_rate.setStyleSheet("color: #070799; font-size: 13px; font-weight: 700;")
        grid.addWidget(self._lbl_effective_cut_rate, 1, 2, 1, 2)

        # Hidden legacy minute rate spinbox for backward compatibility with old tests
        self._spin_cutting_rate = QDoubleSpinBox()
        self._spin_cutting_rate.setRange(0.0, 10000.0)
        self._spin_cutting_rate.setValue(30.0)
        self._spin_cutting_rate.setVisible(False)
        self._spin_cutting_rate.valueChanged.connect(self._recalculate)

        card.content_layout.addLayout(grid)

        # Cutting Subtotal Banner
        cut_sub_box = QFrame()
        cut_sub_box.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 10px;"
        )
        cut_sub_layout = QHBoxLayout(cut_sub_box)
        cut_sub_layout.setContentsMargins(10, 6, 10, 6)

        lbl_cut_sub = QLabel("Total cutting time / Cutting amount:")
        lbl_cut_sub.setStyleSheet("color: #64748B; font-weight: 600; font-size: 12px;")
        cut_sub_layout.addWidget(lbl_cut_sub)
        self._lbl_cut_time_info = QLabel("30 minutes")
        self._lbl_cut_time_info.setStyleSheet("color: #1F2937; font-weight: 700; font-size: 13px;")
        cut_sub_layout.addWidget(self._lbl_cut_time_info)
        cut_sub_layout.addStretch()

        self._lbl_cut_subtotal = QLabel("₹750")
        self._lbl_cut_subtotal.setStyleSheet("color: #070799; font-weight: 800; font-size: 16px;")
        cut_sub_layout.addWidget(self._lbl_cut_subtotal)

        card.content_layout.addWidget(cut_sub_box)
        return card

    def _create_holes_card(self) -> QWidget:
        """Legacy Hole Table widget container — kept for backward compatibility."""
        card = CardWidget(
            title="Hole / Design Charges (Legacy)",
            subtitle="Kept for backward compatibility",
        )
        self._hole_table = HoleTableWidget(pricing_service=self._pricing_service)
        self._hole_table.holes_changed.connect(self._recalculate)
        card.content_layout.addWidget(self._hole_table)
        self._lbl_hole_subtotal = QLabel("₹0")
        return card

    def _create_quantity_card(self) -> QWidget:
        card = CardWidget(
            title="Quantity",
            subtitle="Identical pieces on this quotation",
        )

        q_layout = QHBoxLayout()
        lbl_qty = QLabel("Quantity")
        lbl_qty.setProperty("class", "form-label")
        q_layout.addWidget(lbl_qty)

        self._spin_quantity = NoWheelSpinBox()
        self._spin_quantity.setRange(1, 100000)
        self._spin_quantity.setValue(1)
        self._spin_quantity.setMinimumWidth(100)
        self._spin_quantity.setFixedHeight(36)
        self._spin_quantity.valueChanged.connect(self._recalculate)
        q_layout.addWidget(self._spin_quantity)
        q_layout.addStretch()

        card._main_layout.setContentsMargins(14, 10, 14, 10)
        card._main_layout.setSpacing(8)
        card.content_layout.setSpacing(8)

        card.content_layout.addLayout(q_layout)

        self._lbl_qty_breakdown = QLabel("Per piece  ₹0    ·    Batch total  ₹0")
        self._lbl_qty_breakdown.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: 600;")
        card.content_layout.addWidget(self._lbl_qty_breakdown)
        return card

    # ── Mode Switching ──────────────────────────────────────────

    def set_mode(self, mode: str):
        """Convenience alias for set_calculation_mode."""
        self.set_calculation_mode(mode)

    def get_mode(self) -> str:
        """Get current calculation mode ('simple' or 'design_heavy')."""
        return self._calculation_mode

    def set_calculation_mode(self, mode: str):
        """Set calculation mode: 'simple' or 'design_heavy'."""
        self._calculation_mode = mode
        self._update_mode_ui_state()
        self._lookup_and_set_simple_rate()
        self._recalculate()

    def _update_mode_ui_state(self):
        """Toggle active button styles and show/hide corresponding cards."""
        is_simple = (self._calculation_mode == "simple")
        self._btn_mode_simple.setChecked(is_simple)
        self._btn_mode_heavy.setChecked(not is_simple)

        if is_simple:
            apply_class(self._btn_mode_simple, "btn-primary")
            apply_class(self._btn_mode_heavy, "btn-secondary")
            self._card_simple_pricing.setVisible(True)
            self._card_heavy_material.setVisible(False)
            self._card_heavy_pricing.setVisible(False)
            self._card_heavy_cutting.setVisible(False)
            self._summary_card.set_mode("simple")
        else:
            apply_class(self._btn_mode_simple, "btn-secondary")
            apply_class(self._btn_mode_heavy, "btn-primary")
            self._card_simple_pricing.setVisible(False)
            self._card_heavy_material.setVisible(True)
            self._card_heavy_pricing.setVisible(True)
            self._card_heavy_cutting.setVisible(True)
            self._summary_card.set_mode("design_heavy")

    def _on_dimensions_changed(self):
        """Triggered when length, width, or units change."""
        self._recalculate()

    def _on_material_or_thickness_changed(self):
        """Triggered when Simple Cutting material or thickness changes."""
        self._lookup_and_set_simple_rate()
        self._recalculate()

    def _on_design_heavy_material_changed(self, material_name: str):
        """Use Settings pricing for the independently selected heavy material."""
        if hasattr(self, "_spin_kilo_rate"):
            self._spin_kilo_rate.blockSignals(True)
            self._spin_kilo_rate.setValue(
                self._pricing_service.get_material_kilo_rate(material_name)
            )
            self._spin_kilo_rate.blockSignals(False)
        self._recalculate()

    def refresh_material_options(self):
        """Refresh both mode-specific selectors while retaining each selection."""
        configured = self._pricing_service.get_configured_materials()
        for combo in (self._simple_material_combo, self._design_heavy_material_combo):
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(configured)
            if current and current not in configured:
                combo.addItem(current)
            combo.setCurrentText(current or (configured[0] if configured else "Mild Steel"))
            combo.blockSignals(False)

        if self._current_estimate_id is None:
            self._lookup_and_set_simple_rate()
            self._on_design_heavy_material_changed(self._design_heavy_material_combo.currentText())
        else:
            self._recalculate()

    def _on_simple_rate_user_edited(self):
        """Triggered when user manually changes the rate/sq.ft in Simple mode."""
        self._user_edited_simple_rate = True
        self._recalculate()

    def _lookup_and_set_simple_rate(self):
        """Look up Simple Cutting rate from matrix and prefill if not manually edited."""
        mat_name = self._simple_material_combo.currentText().strip() or "Mild Steel"
        thickness = self._spin_thickness.value()
        rate = self._pricing_service.get_simple_cutting_rate(mat_name, thickness, "mm")

        if rate is not None:
            self._spin_rate_per_sqft.blockSignals(True)
            self._spin_rate_per_sqft.setValue(rate)
            self._spin_rate_per_sqft.blockSignals(False)
            self._lbl_rate_source.setText(f"✓ Configured in Settings: ₹{rate:g}/sq.ft")
            self._lbl_rate_source.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 600;")
        else:
            self._lbl_rate_source.setText("⚠ Rate not configured in Settings — enter manually")
            self._lbl_rate_source.setStyleSheet("color: #D97706; font-size: 12px; font-weight: 600;")

    def _on_override_toggled(self, checked: bool):
        """Enable or disable manual weight override input."""
        self._spin_manual_weight.setEnabled(checked)
        self._recalculate()

    def _on_cutting_method_changed(self):
        """Triggered when Air, Oxygen, or Custom cutting method changes."""
        self._spin_custom_rate.setEnabled(self._radio_custom.isChecked())
        self._recalculate()

    def refresh_cutting_rate_labels(self):
        """Refresh displayed defaults after Settings changes."""
        self._update_cutting_method_labels()
        self._recalculate()

    def _update_cutting_method_labels(self):
        """Keep method captions synchronized with configurable global rates."""
        air_rate = self._pricing_service.get_air_cutting_rate()
        oxygen_rate = self._pricing_service.get_oxygen_cutting_rate()
        self._radio_air.setText(f"Air ({format_indian_currency(air_rate)}/hr)")
        self._radio_oxygen.setText(f"Oxygen ({format_indian_currency(oxygen_rate)}/hr)")

    def _get_effective_hourly_cutting_rate(self) -> float:
        """Return effective hourly cutting rate based on selected method."""
        method = "Air" if self._radio_air.isChecked() else ("Oxygen" if self._radio_oxygen.isChecked() else "Custom")
        loaded_method = getattr(self, "_loaded_cutting_method", None)
        loaded_rate = getattr(self, "_loaded_cutting_rate_per_hour", None)
        if loaded_method == method and loaded_rate is not None:
            self._lbl_effective_cut_rate.setText(
                f"Effective Rate: {format_indian_currency(loaded_rate)} / hour ({method})"
            )
            return loaded_rate
        if self._radio_air.isChecked():
            rate = self._pricing_service.get_air_cutting_rate()
            self._lbl_effective_cut_rate.setText(f"Effective Rate: {format_indian_currency(rate)} / hour (Air)")
            return rate
        elif self._radio_oxygen.isChecked():
            rate = self._pricing_service.get_oxygen_cutting_rate()
            self._lbl_effective_cut_rate.setText(f"Effective Rate: {format_indian_currency(rate)} / hour (Oxygen)")
            return rate
        else:
            rate = self._spin_custom_rate.value()
            self._lbl_effective_cut_rate.setText(f"Effective Rate: {format_indian_currency(rate)} / hour (Custom)")
            return rate

    # ── Live Recalculation ──────────────────────────────────────

    def _recalculate(self):
        """Perform full live calculations and update all UI labels."""
        if self._is_calculating:
            return

        self._is_calculating = True
        try:
            # 1. Dimensions & Area (converted to ft & sq.ft)
            length = self._spin_length.value()
            length_unit = self._combo_length_unit.currentText()
            width = self._spin_width.value()
            width_unit = self._combo_width_unit.currentText()

            try:
                area_res = calculate_area(length, length_unit, width, width_unit)
                length_ft = area_res["length_ft"]
                width_ft = area_res["width_ft"]
                area_sqft = area_res["area_sqft"]
                dim_str = format_dimensions_ft(length_ft, width_ft)
                area_str = format_area(area_sqft)
            except Exception:
                length_ft = 0.0
                width_ft = 0.0
                area_sqft = 0.0
                dim_str = "0.00 ft × 0.00 ft"
                area_str = "0.00 sq.ft"

            self._lbl_dim_converted.setText(dim_str)
            self._lbl_area_converted.setText(area_str)

            mat_name = (
                self._simple_material_combo.currentText().strip()
                if self._calculation_mode == "simple"
                else self._design_heavy_material_combo.currentText().strip()
            ) or "Mild Steel"
            thickness = self._spin_thickness.value()
            quantity = self._spin_quantity.value()

            if self._calculation_mode == "simple":
                # ── Simple Cutting Calculation ──
                rate_per_sqft = self._spin_rate_per_sqft.value()
                simple_res = calculate_simple_estimate(area_sqft, rate_per_sqft, quantity)
                per_piece_cost = simple_res["per_piece_amount"]
                final_total = simple_res["final_amount"]

                self._lbl_simple_subtotal.setText(f"Per Piece: {format_indian_currency(per_piece_cost)}")
                self._lbl_qty_breakdown.setText(
                    f"Per piece {format_indian_currency(per_piece_cost)}  ·  "
                    f"Qty {quantity}  ·  Total {format_indian_currency(final_total)}"
                )

                self._summary_card.update_summary(
                    dimensions_text=dim_str,
                    area_text=area_str,
                    weight_text="",
                    material_cost=0.0,
                    cutting_time_text="",
                    cutting_cost=0.0,
                    design_cost=0.0,
                    per_piece_cost=per_piece_cost,
                    quantity=quantity,
                    final_total=final_total,
                    mode="simple",
                    material_text=f"{mat_name} · {thickness:g} mm",
                    rate_per_sqft=rate_per_sqft,
                )

            else:
                # ── Design Heavy Calculation ──
                density = self._pricing_service.get_material_density(mat_name)
                self._lbl_density_info.setText(f"Density: {density:.2f} kg/L ({mat_name})")

                # Weight calculated from customer dimensions
                try:
                    length_mm = to_mm(length, length_unit)
                    width_mm = to_mm(width, width_unit)
                    if length_mm > 0 and width_mm > 0 and thickness > 0 and density > 0:
                        calc_weight = calculate_part_weight(length_mm, width_mm, thickness, density)
                    else:
                        calc_weight = 0.0
                except Exception:
                    calc_weight = 0.0

                self._calculated_weight = calc_weight
                self._lbl_calc_weight.setText(f"{calc_weight:.2f} kg")
                is_override = self._chk_override_weight.isChecked()
                if is_override:
                    effective_weight = self._spin_manual_weight.value()
                    self._lbl_override_status.setText("Override active")
                    self._lbl_effective_weight.setText(
                        f"Calculated: {calc_weight:.2f} kg    ·    Using manual override: {effective_weight:.2f} kg"
                    )
                else:
                    effective_weight = calc_weight
                    self._lbl_override_status.setText("Using calculated weight")
                    self._lbl_effective_weight.setText(f"Effective weight: {effective_weight:.2f} kg")

                self._spin_sheet_weight.setValue(effective_weight)

                # Material Cost
                kilo_rate = self._spin_kilo_rate.value()
                mat_cost = calculate_material_cost(effective_weight, kilo_rate)
                self._lbl_mat_subtotal.setText(format_indian_currency(mat_cost))

                # Cutting Cost
                hours = self._spin_hours.value()
                minutes = self._spin_minutes.value()
                total_hours = time_to_hours(hours, minutes)
                total_minutes = time_to_minutes(hours, minutes)
                hourly_rate = self._get_effective_hourly_cutting_rate()
                cut_cost = calculate_cutting_cost_hourly(total_hours, hourly_rate)
                self._lbl_cut_time_info.setText(format_time(total_minutes))
                self._lbl_cut_subtotal.setText(format_indian_currency(cut_cost))

                # Legacy holes check (if present in loaded estimate)
                holes = self._hole_table.get_holes()
                hole_dicts = [{"quantity": h.quantity, "rate": h.rate} for h in holes]
                design_cost = calculate_total_hole_cost(hole_dicts) if holes else 0.0
                if design_cost > 0:
                    self._lbl_hole_subtotal.setText(format_indian_currency(design_cost))

                # Final Estimate Total
                heavy_res = calculate_design_heavy_estimate(
                    material_amount=mat_cost,
                    cutting_amount=cut_cost,
                    design_amount=design_cost,
                    quantity=quantity,
                )
                per_piece_cost = heavy_res["per_piece_amount"]
                final_total = heavy_res["final_amount"]

                self._lbl_qty_breakdown.setText(
                    f"Per piece {format_indian_currency(per_piece_cost)}  ·  "
                    f"Qty {quantity}  ·  Total {format_indian_currency(final_total)}"
                )

                cutting_method_name = "Air" if self._radio_air.isChecked() else ("Oxygen" if self._radio_oxygen.isChecked() else "Custom")

                self._summary_card.update_summary(
                    dimensions_text=dim_str,
                    area_text=area_str,
                    weight_text=format_weight(effective_weight),
                    material_cost=mat_cost,
                    cutting_time_text=format_time(total_minutes),
                    cutting_cost=cut_cost,
                    design_cost=design_cost,
                    per_piece_cost=per_piece_cost,
                    quantity=quantity,
                    final_total=final_total,
                    kilo_rate=kilo_rate,
                    cutting_rate=hourly_rate,
                    mode="design_heavy",
                    cutting_method=cutting_method_name,
                )

        finally:
            self._is_calculating = False

    # ── Form Management & Persistence ───────────────────────────

    def _open_date_picker(self):
        """Open a calendar dialog and apply the selected estimate date."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Estimate Date")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        calendar = QCalendarWidget(dialog)
        calendar.setGridVisible(True)
        calendar.setSelectedDate(self._date_edit.date())
        calendar.setMinimumSize(300, 240)
        layout.addWidget(calendar)

        def apply_selected_date(selected_date):
            self._date_edit.setDate(selected_date)
            dialog.accept()

        calendar.clicked.connect(apply_selected_date)
        dialog.exec()

    def reset_form(self):
        """Reset form fields to start a new estimate with fresh defaults."""
        self._current_estimate_id = None
        self._user_edited_simple_rate = False
        self._lbl_page_title.setText("New Estimate")
        self._lbl_page_subtitle.setText("Create a quotation for laser cutting work")

        # Auto-generate next estimate number & today date
        next_num = self._estimate_service.get_next_estimate_number()
        self._txt_est_number.setText(next_num)
        self._date_edit.setDate(QDate.currentDate())

        # Clear text inputs
        self._txt_cust_name.clear()
        self._txt_cust_address.clear()
        self._txt_phone.clear()
        self._txt_employee_name.clear()
        self._txt_desc.clear()
        self.refresh_material_options()
        self._simple_material_combo.setCurrentText("Mild Steel")
        self._design_heavy_material_combo.setCurrentText("Mild Steel")

        # Defaults for dimensions
        self._spin_length.setValue(120.0)
        self._combo_length_unit.setCurrentText("cm")
        self._spin_width.setValue(80.0)
        self._combo_width_unit.setCurrentText("cm")

        # Defaults for Simple Cutting
        self._spin_thickness.setValue(3.0)
        self._lookup_and_set_simple_rate()

        # Defaults for Design Heavy
        self._loaded_cutting_method = None
        self._loaded_cutting_rate_per_hour = None
        self._chk_override_weight.setChecked(False)
        self._spin_manual_weight.setValue(7.54)
        self._spin_kilo_rate.setValue(
            self._pricing_service.get_material_kilo_rate(
                self._design_heavy_material_combo.currentText()
            )
        )
        self._radio_air.setChecked(True)
        self._spin_hours.setValue(0)
        self._spin_minutes.setValue(30)
        self._spin_custom_rate.setValue(2000.0)

        # Clear holes table
        self._hole_table.clear()

        # Quantity
        self._spin_quantity.setValue(1)

        self._banner.setVisible(False)
        self.set_calculation_mode("simple")

    def load_estimate(self, estimate: Estimate, is_edit: bool = True):
        """Load an existing estimate into the form."""
        if estimate.calculation_mode == "design_heavy":
            self._loaded_cutting_method = (estimate.cutting_method or "Air").strip().title()
            self._loaded_cutting_rate_per_hour = estimate.cutting_rate_per_hour
        else:
            # Simple estimates store zero for unused cutting fields. Do not let
            # that sentinel override the configured Air rate in the form.
            self._loaded_cutting_method = None
            self._loaded_cutting_rate_per_hour = None
        self._current_estimate_id = estimate.id if is_edit else None
        title_text = f"Edit Estimate {estimate.estimate_number}" if is_edit else "New Estimate (Duplicated)"
        self._lbl_page_title.setText(title_text)
        self._lbl_page_subtitle.setText(
            "Update this quotation" if is_edit else "Save as a new quotation with a new estimate number"
        )

        self._txt_est_number.setText(estimate.estimate_number)
        saved_date = QDate.fromString(estimate.date or "", "dd/MM/yyyy")
        if not saved_date.isValid():
            # Accept ISO dates from older/imported estimates without changing
            # the database representation of estimates saved by this app.
            saved_date = QDate.fromString(estimate.date or "", "yyyy-MM-dd")
        if saved_date.isValid():
            self._date_edit.setDate(saved_date)
        self._txt_cust_name.setText(estimate.customer_name)
        self._txt_cust_address.setPlainText(getattr(estimate, "customer_address", "") or "")
        self._txt_phone.setText(estimate.phone)
        self._txt_employee_name.setText(getattr(estimate, "employee_name", "") or "")
        self._txt_desc.setText(estimate.description)

        # Dimensions
        self._spin_length.setValue(estimate.length if estimate.length > 0 else 120.0)
        self._combo_length_unit.setCurrentText(estimate.length_unit or "cm")
        self._spin_width.setValue(estimate.width if estimate.width > 0 else 80.0)
        self._combo_width_unit.setCurrentText(estimate.width_unit or "cm")

        # Material is stored per estimate; load it into that mode's selector.
        material_combo = (
            self._simple_material_combo
            if estimate.calculation_mode == "simple"
            else self._design_heavy_material_combo
        )
        material_name = estimate.material or "Mild Steel"
        if material_combo.findText(material_name) < 0:
            material_combo.addItem(material_name)
        material_combo.setCurrentText(material_name)
        self._spin_thickness.setValue(estimate.thickness if estimate.thickness > 0 else 1.0)
        self._combo_thick_unit.setCurrentText(estimate.thickness_unit or "mm")

        # Simple rate
        if estimate.rate_per_sqft > 0:
            self._spin_rate_per_sqft.setValue(estimate.rate_per_sqft)

        # Design Heavy values
        self._spin_sheet_len.setValue(estimate.sheet_length if estimate.sheet_length > 0 else 2000.0)
        self._spin_sheet_width.setValue(estimate.sheet_width if estimate.sheet_width > 0 else 1000.0)
        self._chk_override_weight.setChecked(estimate.is_weight_overridden)
        if estimate.is_weight_overridden:
            self._spin_manual_weight.setValue(estimate.manual_sheet_weight or estimate.sheet_weight)
        else:
            self._spin_manual_weight.setValue(estimate.sheet_weight if estimate.sheet_weight > 0 else 7.54)
        self._spin_kilo_rate.setValue(
            estimate.kilo_rate if estimate.kilo_rate > 0
            else self._pricing_service.get_material_kilo_rate(
                self._design_heavy_material_combo.currentText()
            )
        )

        # Cutting method & time
        method = (estimate.cutting_method or "Air").strip().title()
        if method == "Oxygen":
            self._radio_oxygen.setChecked(True)
        elif method == "Custom":
            self._radio_custom.setChecked(True)
            self._spin_custom_rate.setValue(estimate.cutting_rate_per_hour or 2000.0)
        else:
            self._radio_air.setChecked(True)

        self._spin_hours.setValue(estimate.cutting_hours)
        self._spin_minutes.setValue(estimate.cutting_minutes)

        # Holes (if any)
        self._hole_table.set_holes(estimate.holes)

        # Quantity
        self._spin_quantity.setValue(estimate.quantity if estimate.quantity > 0 else 1)

        # Mode
        mode = estimate.calculation_mode or "design_heavy"
        self.set_calculation_mode(mode)
        self._banner.setVisible(False)
        self._recalculate()

    def _on_save(self):
        """Validate all fields and save the estimate quotation to the database."""
        # 1. Dimensions Validation
        valid, msg = validate_positive_number(self._spin_length.value(), "Length")
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return

        valid, msg = validate_positive_number(self._spin_width.value(), "Width")
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return

        valid, msg = validate_positive_integer(self._spin_quantity.value(), "Quantity")
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return

        length = self._spin_length.value()
        length_unit = self._combo_length_unit.currentText()
        width = self._spin_width.value()
        width_unit = self._combo_width_unit.currentText()
        area_res = calculate_area(length, length_unit, width, width_unit)

        mat_name = (
            self._simple_material_combo.currentText().strip()
            if self._calculation_mode == "simple"
            else self._design_heavy_material_combo.currentText().strip()
        ) or "Mild Steel"
        thickness = self._spin_thickness.value()
        quantity = self._spin_quantity.value()

        if self._calculation_mode == "simple":
            rate_per_sqft = self._spin_rate_per_sqft.value()
            valid, msg = validate_non_negative_number(rate_per_sqft, "Rate per sq.ft")
            if not valid:
                QMessageBox.warning(self, "Validation Error", msg)
                return

            simple_res = calculate_simple_estimate(area_res["area_sqft"], rate_per_sqft, quantity)
            per_piece_cost = simple_res["per_piece_amount"]
            final_amount = simple_res["final_amount"]

            est = Estimate(
                id=self._current_estimate_id,
                estimate_number=self._txt_est_number.text().strip(),
                calculation_mode="simple",
                customer_name=self._txt_cust_name.text().strip(),
                customer_address=self._txt_cust_address.toPlainText().strip(),
                phone=self._txt_phone.text().strip(),
                employee_name=self._txt_employee_name.text().strip(),
                date=self._date_edit.date().toString("dd/MM/yyyy"),
                description=self._txt_desc.text().strip(),
                length=length,
                length_unit=length_unit,
                width=width,
                width_unit=width_unit,
                length_ft=area_res["length_ft"],
                width_ft=area_res["width_ft"],
                area_sqft=area_res["area_sqft"],
                rate_per_sqft=rate_per_sqft,
                material=mat_name,
                thickness=thickness,
                thickness_unit="mm",
                sheet_length=0.0,
                sheet_width=0.0,
                sheet_weight=0.0,
                kilo_rate=0.0,
                is_weight_overridden=False,
                manual_sheet_weight=0.0,
                material_density=self._pricing_service.get_material_density(mat_name),
                cutting_method="",
                cutting_hours=0,
                cutting_minutes=0,
                total_cutting_min=0.0,
                cutting_rate=0.0,
                cutting_rate_per_hour=0.0,
                material_amount=0.0,
                cutting_amount=0.0,
                design_amount=0.0,
                quantity=quantity,
                per_piece_amount=per_piece_cost,
                final_amount=final_amount,
                holes=[],
            )

        else:
            # Design Heavy
            valid, msg = validate_non_negative_number(self._spin_sheet_weight.value(), "Part Weight")
            if not valid:
                QMessageBox.warning(self, "Validation Error", msg)
                return

            valid, msg = validate_non_negative_number(self._spin_kilo_rate.value(), "Kilo Rate")
            if not valid:
                QMessageBox.warning(self, "Validation Error", msg)
                return

            density = self._pricing_service.get_material_density(mat_name)
            is_override = self._chk_override_weight.isChecked()
            manual_weight = self._spin_manual_weight.value() if is_override else 0.0
            weight = manual_weight if is_override else getattr(self, "_calculated_weight", self._spin_sheet_weight.value())
            kilo_rate = self._spin_kilo_rate.value()
            mat_amount = calculate_material_cost(weight, kilo_rate)

            hours = self._spin_hours.value()
            minutes = self._spin_minutes.value()
            total_hours = time_to_hours(hours, minutes)
            total_cut_min = time_to_minutes(hours, minutes)
            hourly_rate = self._get_effective_hourly_cutting_rate()
            cut_amount = calculate_cutting_cost_hourly(total_hours, hourly_rate)

            holes = self._hole_table.get_holes()
            hole_dicts = [{"quantity": h.quantity, "rate": h.rate} for h in holes]
            design_amount = calculate_total_hole_cost(hole_dicts) if holes else 0.0

            heavy_res = calculate_design_heavy_estimate(mat_amount, cut_amount, design_amount, quantity)
            per_piece_cost = heavy_res["per_piece_amount"]
            final_amount = heavy_res["final_amount"]

            method_name = "Air" if self._radio_air.isChecked() else ("Oxygen" if self._radio_oxygen.isChecked() else "Custom")

            est = Estimate(
                id=self._current_estimate_id,
                estimate_number=self._txt_est_number.text().strip(),
                calculation_mode="design_heavy",
                customer_name=self._txt_cust_name.text().strip(),
                customer_address=self._txt_cust_address.toPlainText().strip(),
                phone=self._txt_phone.text().strip(),
                employee_name=self._txt_employee_name.text().strip(),
                date=self._date_edit.date().toString("dd/MM/yyyy"),
                description=self._txt_desc.text().strip(),
                length=length,
                length_unit=length_unit,
                width=width,
                width_unit=width_unit,
                length_ft=area_res["length_ft"],
                width_ft=area_res["width_ft"],
                area_sqft=area_res["area_sqft"],
                rate_per_sqft=0.0,
                material=mat_name,
                thickness=thickness,
                thickness_unit="mm",
                sheet_length=self._spin_sheet_len.value(),
                sheet_width=self._spin_sheet_width.value(),
                sheet_weight=weight,
                kilo_rate=kilo_rate,
                is_weight_overridden=is_override,
                manual_sheet_weight=manual_weight,
                material_density=density,
                cutting_method=method_name,
                cutting_hours=hours,
                cutting_minutes=minutes,
                total_cutting_min=total_cut_min,
                cutting_rate=self._spin_cutting_rate.value(),
                cutting_rate_per_hour=hourly_rate,
                material_amount=mat_amount,
                cutting_amount=cut_amount,
                design_amount=design_amount,
                quantity=quantity,
                per_piece_amount=per_piece_cost,
                final_amount=final_amount,
                holes=holes,
            )

        # 3. Save via Service
        if self._current_estimate_id:
            self._estimate_service.update_estimate(est)
            saved_id = self._current_estimate_id
            self._banner_label.setText(f"✓  Estimate {est.estimate_number} updated successfully!")
        else:
            saved_id = self._estimate_service.save_estimate(est)
            self._current_estimate_id = saved_id
            self._txt_est_number.setText(est.estimate_number)
            self._banner_label.setText(f"✓  Estimate {est.estimate_number} saved successfully!")

        self._banner.setVisible(True)
        self.estimate_saved.emit(saved_id)

        mode_desc = "Simple Cutting" if est.calculation_mode == "simple" else "Design Heavy"
        QMessageBox.information(
            self,
            "Quotation Saved",
            f"Quotation {est.estimate_number} ({mode_desc}) for {est.customer_name or 'Customer'} "
            f"saved with total amount {format_indian_currency(est.final_amount)}.",
        )
