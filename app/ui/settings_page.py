# -*- coding: utf-8 -*-
"""
Settings and Pricing Configuration page for Laser Estimate desktop application.
Organized into clear sections:
1. Company Information
2. Simple Cutting Rate Matrix (Material, Thickness, Rate/sq.ft, Actions)
3. Design Heavy Material Rates & Densities (Material, Density kg/L, Kilo Rate ₹/kg)
4. Laser Cutting Rates (Air & Oxygen defaults)
5. Legacy Hole Rates Matrix
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.pricing_service import PricingService
from app.ui.theme import apply_class
from app.ui.widgets.confirmation_dialog import ConfirmationDialog
from app.ui.widgets.card import CardWidget
from app.ui.widgets.no_wheel_spinbox import NoWheelDoubleSpinBox
from app.utils.formatters import format_indian_currency


class SettingsPage(QWidget):
    """Settings page for managing company profile, simple cutting matrix, material densities, and cutting defaults."""

    settings_updated = Signal()

    def __init__(
        self,
        pricing_service: PricingService,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
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

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Settings")
        title.setProperty("class", "page-title")
        title_col.addWidget(title)
        subtitle = QLabel("Quotation contacts, bank details, material rates, and cutting defaults")
        subtitle.setProperty("class", "page-subtitle")
        title_col.addWidget(subtitle)
        self._layout.addLayout(title_col)

        # ── Notification Banner ────────────────────────────────
        self._banner = QFrame()
        self._banner.setProperty("class", "banner-success")
        banner_layout = QHBoxLayout(self._banner)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        self._banner_label = QLabel("Settings saved successfully.")
        self._banner_label.setStyleSheet("color: #065F46; font-weight: 600;")
        banner_layout.addWidget(self._banner_label)
        self._banner.setVisible(False)
        self._layout.addWidget(self._banner)

        # ── SECTION 1: Company Information ─────────────────────
        self._create_company_section()
        self._create_quotation_terms_section()
        self._create_bank_details_section()

        # ── SECTION 2: Simple Cutting Rate Matrix ──────────────
        self._create_simple_cutting_section()

        # ── SECTION 3: Design Heavy Material Rates & Densities ──
        self._create_material_rates_section()

        # ── SECTION 4: Laser Cutting Defaults ───────────────────
        self._create_cutting_defaults_section()

        # ── SECTION 5: Legacy Hole / Pierce Rates ──────────────
        self._layout.addStretch()

        scroll_area.setWidget(scroll_content)
        root_layout.addWidget(scroll_area)

        # Load initial values
        self.load_settings()

    # ── Section 1: Company Info ────────────────────────────────

    def _create_company_section(self):
        company_card = CardWidget(
            title="1. Company Information",
            subtitle="Contact information printed in the quotation header.",
        )
        company_form = QFormLayout()
        company_form.setSpacing(14)
        company_form.setLabelAlignment(Qt.AlignLeft)

        self._company_fields = {
            "company_gstin": "GSTIN",
            "company_mobile": "Mobile",
            "company_phone": "Phone",
            "company_email": "Email",
        }
        self._company_inputs = {}
        for key, label_text in self._company_fields.items():
            field = QLineEdit()
            field.setFixedHeight(36)
            self._company_inputs[key] = field
            label = QLabel(label_text + ":")
            label.setProperty("class", "form-label")
            company_form.addRow(label, field)

        company_card.content_layout.addLayout(company_form)
        button = QPushButton("Save Company Details")
        apply_class(button, "btn-primary")
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedWidth(240)
        button.setMinimumHeight(36)
        button.clicked.connect(self._save_company_info)
        save_layout = QHBoxLayout()
        save_layout.addWidget(button)
        save_layout.addStretch()
        company_card.content_layout.addLayout(save_layout)
        self._layout.addWidget(company_card)

    def _create_quotation_terms_section(self):
        card = CardWidget(
            title="Quotation Terms",
            subtitle="Optional terms shown in the quotation.",
        )
        self._txt_quotation_terms = QLineEdit()
        self._txt_quotation_terms.setFixedHeight(36)
        card.content_layout.addWidget(self._txt_quotation_terms)
        button = QPushButton("Save Quotation Terms")
        apply_class(button, "btn-secondary")
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedWidth(240)
        button.setMinimumHeight(36)
        button.clicked.connect(self._save_quotation_terms)
        save_layout = QHBoxLayout()
        save_layout.addWidget(button)
        save_layout.addStretch()
        card.content_layout.addLayout(save_layout)
        self._layout.addWidget(card)

    def _create_bank_details_section(self):
        card = CardWidget(
            title="Bank Details",
            subtitle="Optional bank information printed at the bottom of quotations.",
        )
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft)
        self._bank_fields = {
            "bank_account_name": "Account Name",
            "bank_name": "Bank Name",
            "bank_account_number": "Account Number",
            "bank_branch": "Branch Name",
            "bank_ifsc": "IFSC Code",
        }
        self._bank_inputs = {}
        for key, label_text in self._bank_fields.items():
            field = QLineEdit()
            field.setFixedHeight(36)
            self._bank_inputs[key] = field
            label = QLabel(label_text + ":")
            label.setProperty("class", "form-label")
            form.addRow(label, field)
        card.content_layout.addLayout(form)
        button = QPushButton("Save Bank Details")
        apply_class(button, "btn-secondary")
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedWidth(240)
        button.setMinimumHeight(36)
        button.clicked.connect(self._save_bank_details)
        save_layout = QHBoxLayout()
        save_layout.addWidget(button)
        save_layout.addStretch()
        card.content_layout.addLayout(save_layout)
        self._layout.addWidget(card)

    def _create_simple_cutting_section(self):
        self._simple_card = CardWidget(
            title="2. Simple Cutting Rate Matrix",
            subtitle="Configurable price per sq.ft based on Material + Thickness. Drives automatic rate lookup in Simple mode.",
        )

        # Rates Table
        self._simple_table = QTableWidget()
        self._simple_table.setColumnCount(4)
        self._simple_table.setHorizontalHeaderLabels(["Material", "Thickness", "Rate / sq.ft", "Action"])
        self._simple_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._simple_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self._simple_table.setColumnWidth(3, 105)
        self._simple_table.verticalHeader().setVisible(False)
        self._simple_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._simple_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._simple_table.setMinimumHeight(180)
        self._simple_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._simple_card.content_layout.addWidget(self._simple_table)

        # Add Rate Inline Box
        add_box = QFrame()
        add_box.setStyleSheet(
            "background-color: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 12px;"
        )
        add_layout = QHBoxLayout(add_box)
        add_layout.setContentsMargins(10, 8, 10, 8)
        add_layout.setSpacing(12)

        lbl_add = QLabel("Add New Rate:")
        lbl_add.setProperty("class", "form-label")
        add_layout.addWidget(lbl_add)

        self._combo_new_simple_mat = QComboBox()
        self._combo_new_simple_mat.addItems(self._pricing_service.get_configured_materials())
        self._combo_new_simple_mat.setEditable(True)
        self._combo_new_simple_mat.setMinimumWidth(140)
        self._combo_new_simple_mat.setFixedHeight(34)
        add_layout.addWidget(self._combo_new_simple_mat)

        self._spin_new_simple_thick = NoWheelDoubleSpinBox()
        self._spin_new_simple_thick.setRange(0.1, 100.0)
        self._spin_new_simple_thick.setDecimals(1)
        self._spin_new_simple_thick.setValue(3.0)
        self._spin_new_simple_thick.setSuffix(" mm")
        self._spin_new_simple_thick.setFixedWidth(110)
        self._spin_new_simple_thick.setFixedHeight(34)
        add_layout.addWidget(self._spin_new_simple_thick)

        self._spin_new_simple_rate = NoWheelDoubleSpinBox()
        self._spin_new_simple_rate.setRange(0.0, 100000.0)
        self._spin_new_simple_rate.setDecimals(2)
        self._spin_new_simple_rate.setPrefix("₹ ")
        self._spin_new_simple_rate.setSuffix(" / sq.ft")
        self._spin_new_simple_rate.setValue(330.0)
        self._spin_new_simple_rate.setFixedWidth(210)
        self._spin_new_simple_rate.setFixedHeight(34)
        add_layout.addWidget(self._spin_new_simple_rate)

        btn_add = QPushButton("Add Rate")
        apply_class(btn_add, "btn-secondary")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setMinimumHeight(34)
        btn_add.clicked.connect(self._add_simple_rate)
        add_layout.addWidget(btn_add)

        add_layout.addStretch()
        self._simple_card.content_layout.addWidget(add_box)
        self._layout.addWidget(self._simple_card)

    # ── Section 3: Material Rates & Densities ──────────────────

    def _create_material_rates_section(self):
        mat_card = CardWidget(
            title="3. Design Heavy Material Rates & Densities",
            subtitle="Configure material density (kg/L) for weight calculations and standard market kilo rates (₹/kg).",
        )

        self._material_table = QTableWidget()
        self._material_table.setColumnCount(3)
        self._material_table.setHorizontalHeaderLabels(["Material", "Density (kg/L)", "Kilo Rate (₹/kg)"])
        self._material_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._material_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self._material_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self._material_table.setColumnWidth(1, 205)
        self._material_table.setColumnWidth(2, 240)
        self._material_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._material_table.verticalHeader().setVisible(False)
        self._material_table.setMinimumHeight(280)
        mat_card.content_layout.addWidget(self._material_table)

        btn_save_mat = QPushButton("Save Material Rates && Densities")
        apply_class(btn_save_mat, "btn-primary")
        btn_save_mat.setCursor(Qt.PointingHandCursor)
        btn_save_mat.setMinimumWidth(240)
        btn_save_mat.setMinimumHeight(38)
        btn_save_mat.setFixedWidth(280)
        btn_save_mat.clicked.connect(self._save_material_rates)
        save_layout = QHBoxLayout()
        save_layout.addWidget(btn_save_mat)
        save_layout.addStretch()
        mat_card.content_layout.addLayout(save_layout)

        self._layout.addWidget(mat_card)

    # ── Section 4: Laser Cutting Defaults ──────────────────────

    def _create_cutting_defaults_section(self):
        cut_card = CardWidget(
            title="4. Default Laser Cutting Hourly Rates",
            subtitle="Default hourly rates for Air and Oxygen cutting used across Design Heavy quotations.",
        )

        cut_form = QFormLayout()
        cut_form.setSpacing(14)
        cut_form.setLabelAlignment(Qt.AlignLeft)

        self._spin_air_rate = NoWheelDoubleSpinBox()
        self._spin_air_rate.setRange(0.0, 100000.0)
        self._spin_air_rate.setDecimals(2)
        self._spin_air_rate.setPrefix("₹ ")
        self._spin_air_rate.setSuffix(" / hour")
        self._spin_air_rate.setFixedWidth(220)
        self._spin_air_rate.setFixedHeight(36)
        lbl_air = QLabel("Default Air Cutting Rate:")
        lbl_air.setProperty("class", "form-label")
        cut_form.addRow(lbl_air, self._spin_air_rate)

        self._spin_oxygen_rate = NoWheelDoubleSpinBox()
        self._spin_oxygen_rate.setRange(0.0, 100000.0)
        self._spin_oxygen_rate.setDecimals(2)
        self._spin_oxygen_rate.setPrefix("₹ ")
        self._spin_oxygen_rate.setSuffix(" / hour")
        self._spin_oxygen_rate.setFixedWidth(220)
        self._spin_oxygen_rate.setFixedHeight(36)
        lbl_oxy = QLabel("Default Oxygen Cutting Rate:")
        lbl_oxy.setProperty("class", "form-label")
        cut_form.addRow(lbl_oxy, self._spin_oxygen_rate)

        # Global default kilo rate fallback
        self._spin_kilo_rate = NoWheelDoubleSpinBox()
        self._spin_kilo_rate.setRange(0.0, 100000.0)
        self._spin_kilo_rate.setDecimals(2)
        self._spin_kilo_rate.setPrefix("₹ ")
        self._spin_kilo_rate.setSuffix(" / kg")
        self._spin_kilo_rate.setFixedWidth(220)
        self._spin_kilo_rate.setFixedHeight(36)
        lbl_kilo = QLabel("Global Fallback Kilo Rate:")
        lbl_kilo.setProperty("class", "form-label")
        cut_form.addRow(lbl_kilo, self._spin_kilo_rate)

        # Legacy minute cutting rate fallback
        self._spin_cutting_rate = NoWheelDoubleSpinBox()
        self._spin_cutting_rate.setRange(0.0, 10000.0)
        self._spin_cutting_rate.setDecimals(2)
        self._spin_cutting_rate.setPrefix("₹ ")
        self._spin_cutting_rate.setSuffix(" / minute")
        self._spin_cutting_rate.setFixedWidth(220)
        self._spin_cutting_rate.setFixedHeight(36)
        self._spin_cutting_rate.setVisible(False)  # kept for backward compatibility

        cut_card.content_layout.addLayout(cut_form)

        btn_save_cut = QPushButton("Save Cutting && Pricing Defaults")
        apply_class(btn_save_cut, "btn-primary")
        btn_save_cut.setCursor(Qt.PointingHandCursor)
        btn_save_cut.setMinimumWidth(240)
        btn_save_cut.setFixedWidth(280)
        btn_save_cut.setMinimumHeight(38)
        btn_save_cut.clicked.connect(self._save_rates)
        cut_save_layout = QHBoxLayout()
        cut_save_layout.addWidget(btn_save_cut)
        cut_save_layout.addStretch()
        cut_card.content_layout.addLayout(cut_save_layout)

        self._layout.addWidget(cut_card)

    # ── Section 5: Hole Rates (Legacy / Backward Compatibility) 

    def _create_hole_rates_section(self):
        self._hole_card = CardWidget(
            title="5. Hole / Pierce Rate Matrix (Legacy)",
            subtitle="Preserved for historical quotations that used hole-based pricing.",
        )

        self._hole_table = QTableWidget()
        self._hole_table.setColumnCount(4)
        self._hole_table.setHorizontalHeaderLabels(["Diameter", "Unit", "Rate (₹/hole)", "Action"])
        self._hole_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._hole_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self._hole_table.setColumnWidth(3, 105)
        self._hole_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._hole_table.verticalHeader().setVisible(False)
        self._hole_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._hole_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._hole_table.setMinimumHeight(250)
        self._hole_card.content_layout.addWidget(self._hole_table)

        # Add New Hole Rate Inline Form
        add_box = QFrame()
        add_box.setStyleSheet("background-color: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 10px;")
        add_layout = QHBoxLayout(add_box)
        add_layout.setContentsMargins(10, 6, 10, 6)
        add_layout.setSpacing(12)

        lbl_hole_add = QLabel("Add Hole Rate:")
        lbl_hole_add.setProperty("class", "form-label")
        add_layout.addWidget(lbl_hole_add)

        self._spin_new_diameter = NoWheelDoubleSpinBox()
        self._spin_new_diameter.setRange(0.1, 1000.0)
        self._spin_new_diameter.setValue(25.0)
        self._spin_new_diameter.setFixedWidth(100)
        self._spin_new_diameter.setFixedHeight(32)
        add_layout.addWidget(self._spin_new_diameter)

        self._combo_new_unit = QComboBox()
        self._combo_new_unit.addItems(["mm", "cm", "in"])
        self._combo_new_unit.setFixedWidth(75)
        self._combo_new_unit.setFixedHeight(32)
        add_layout.addWidget(self._combo_new_unit)

        self._spin_new_rate = NoWheelDoubleSpinBox()
        self._spin_new_rate.setRange(0.0, 10000.0)
        self._spin_new_rate.setPrefix("₹ ")
        self._spin_new_rate.setValue(25.0)
        self._spin_new_rate.setFixedWidth(110)
        self._spin_new_rate.setFixedHeight(32)
        add_layout.addWidget(self._spin_new_rate)

        btn_add_hole = QPushButton("Add Rate")
        apply_class(btn_add_hole, "btn-secondary")
        btn_add_hole.setCursor(Qt.PointingHandCursor)
        btn_add_hole.setMinimumHeight(32)
        btn_add_hole.clicked.connect(self._add_hole_rate)
        add_layout.addWidget(btn_add_hole)
        add_layout.addStretch()

        self._hole_card.content_layout.addWidget(add_box)
        self._layout.addWidget(self._hole_card)

    # ── Data Load & Save Handlers ──────────────────────────────

    def load_settings(self):
        """Load all settings from persistent database."""
        # Company
        for key, field in self._company_inputs.items():
            field.setText(self._pricing_service.get_setting(key, ""))
        self._txt_quotation_terms.setText(
            self._pricing_service.get_setting("quotation_terms", "")
        )
        for key, field in self._bank_inputs.items():
            field.setText(self._pricing_service.get_setting(key, ""))

        # Cutting defaults
        self._spin_air_rate.setValue(self._pricing_service.get_air_cutting_rate())
        self._spin_oxygen_rate.setValue(self._pricing_service.get_oxygen_cutting_rate())
        self._spin_kilo_rate.setValue(self._pricing_service.get_default_kilo_rate())
        self._spin_cutting_rate.setValue(self._pricing_service.get_default_cutting_rate())

        # Tables
        self._load_simple_rates()
        self._load_material_rates()

    def _load_simple_rates(self):
        """Populate Simple Cutting Matrix table."""
        rates = self._pricing_service.get_simple_cutting_rates()
        self._simple_table.setRowCount(len(rates))

        for row_idx, r in enumerate(rates):
            # Material
            item_mat = QTableWidgetItem(r["material"])
            item_mat.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._simple_table.setItem(row_idx, 0, item_mat)

            # Thickness
            item_thick = QTableWidgetItem(f"{r['thickness']:g} {r['thickness_unit']}")
            item_thick.setTextAlignment(Qt.AlignCenter)
            self._simple_table.setItem(row_idx, 1, item_thick)

            # Rate
            item_rate = QTableWidgetItem(format_indian_currency(r["rate_per_sqft"]) + " / sq.ft")
            item_rate.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_rate.setForeground(Qt.darkBlue)
            self._simple_table.setItem(row_idx, 2, item_rate)

            # Delete button
            btn_del = QPushButton("Delete")
            apply_class(btn_del, "btn-danger")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setMinimumHeight(28)
            btn_del.setMinimumWidth(72)
            rate_id = r["id"]
            btn_del.clicked.connect(lambda checked=False, rid=rate_id: self._delete_simple_rate(rid))
            self._simple_table.setCellWidget(row_idx, 3, btn_del)
            self._simple_table.setRowHeight(row_idx, 44)

    def _load_material_rates(self):
        """Populate Material Densities & Kilo Rates aligned grid."""
        densities = self._pricing_service.get_all_material_densities()
        kilo_rates = self._pricing_service.get_all_material_kilo_rates()
        default_kilo = self._pricing_service.get_default_kilo_rate()

        # Merge standard materials with any extra materials
        all_materials = self._pricing_service.get_configured_materials()
        self._material_table.setRowCount(len(all_materials))

        for idx, name in enumerate(all_materials):
            # Column 0: Material Name (Read-only)
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            item_name.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._material_table.setItem(idx, 0, item_name)

            # Column 1: Density Spinbox
            spin_density = NoWheelDoubleSpinBox()
            spin_density.setRange(0.01, 30.0)
            spin_density.setDecimals(2)
            density_val = densities.get(name, self._pricing_service.get_material_density(name))
            spin_density.setValue(float(density_val) if density_val else 7.85)
            spin_density.setSuffix(" kg/L")
            spin_density.setMinimumWidth(175)
            spin_density.setFixedHeight(34)
            self._material_table.setCellWidget(idx, 1, spin_density)

            # Column 2: Kilo Rate Spinbox
            spin_kilo = NoWheelDoubleSpinBox()
            spin_kilo.setRange(0.0, 100000.0)
            spin_kilo.setDecimals(2)
            spin_kilo.setPrefix("₹ ")
            spin_kilo.setSuffix(" / kg")
            kilo_val = kilo_rates.get(name, default_kilo)
            spin_kilo.setValue(float(kilo_val) if kilo_val else default_kilo)
            spin_kilo.setMinimumWidth(205)
            spin_kilo.setFixedHeight(34)
            self._material_table.setCellWidget(idx, 2, spin_kilo)
            self._material_table.setRowHeight(idx, 44)

    def _load_hole_rates(self):
        """Populate Hole Rates table."""
        rates = self._pricing_service.get_hole_rates()
        self._hole_table.setRowCount(len(rates))

        for row_idx, r in enumerate(rates):
            item_dia = QTableWidgetItem(f"{r['diameter']:g}")
            item_dia.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._hole_table.setItem(row_idx, 0, item_dia)

            item_unit = QTableWidgetItem(r["unit"])
            item_unit.setTextAlignment(Qt.AlignCenter)
            self._hole_table.setItem(row_idx, 1, item_unit)

            item_rate = QTableWidgetItem(f"₹{r['rate']:g}")
            item_rate.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._hole_table.setItem(row_idx, 2, item_rate)

            btn_del = QPushButton("Delete")
            apply_class(btn_del, "btn-danger")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setMinimumHeight(28)
            btn_del.setMinimumWidth(80)
            rate_id = r["id"]
            btn_del.clicked.connect(lambda checked=False, rid=rate_id: self._delete_hole_rate(rid))
            self._hole_table.setCellWidget(row_idx, 3, btn_del)
            self._hole_table.setRowHeight(row_idx, 44)

    # ── Save Action Implementations ────────────────────────────

    def _save_company_info(self):
        for key, field in self._company_inputs.items():
            self._pricing_service.set_setting(key, field.text().strip())
        self._show_banner("Company information saved successfully.")
        self.settings_updated.emit()

    def _save_quotation_terms(self):
        self._pricing_service.set_setting(
            "quotation_terms", self._txt_quotation_terms.text().strip()
        )
        self._show_banner("Quotation terms saved successfully.")
        self.settings_updated.emit()

    def _save_bank_details(self):
        for key, field in self._bank_inputs.items():
            self._pricing_service.set_setting(key, field.text().strip())
        self._show_banner("Bank details saved successfully.")
        self.settings_updated.emit()

    def _add_simple_rate(self):
        material = self._combo_new_simple_mat.currentText().strip()
        thickness = self._spin_new_simple_thick.value()
        rate = self._spin_new_simple_rate.value()

        if not material:
            QMessageBox.warning(self, "Validation Error", "Material name cannot be empty.")
            return

        self._pricing_service.add_simple_cutting_rate(material, thickness, "mm", rate)
        self._load_simple_rates()
        self._show_banner(f"Added rate for {material} ({thickness:g} mm) at ₹{rate:g}/sq.ft.")
        self.settings_updated.emit()

    def _delete_simple_rate(self, rate_id: int):
        confirmed = ConfirmationDialog.confirm(
            self,
            "Delete Simple Cutting Rate",
            "Are you sure you want to delete this simple cutting rate?",
            confirm_text="Delete",
            destructive=True,
        )
        if confirmed:
            self._pricing_service.delete_simple_cutting_rate(rate_id)
            self._load_simple_rates()
            self._show_banner("Simple cutting rate deleted.")
            self.settings_updated.emit()

    def _save_material_rates(self):
        """Save densities and material-specific kilo rates from grid rows."""
        for row in range(self._material_table.rowCount()):
            name_item = self._material_table.item(row, 0)
            spin_dens = self._material_table.cellWidget(row, 1)
            spin_kilo = self._material_table.cellWidget(row, 2)
            if name_item and spin_dens and spin_kilo:
                mat_name = name_item.text().strip()
                self._pricing_service.set_material_density(mat_name, spin_dens.value())
                self._pricing_service.set_material_kilo_rate(mat_name, spin_kilo.value())

        self._show_banner("Material densities and kilo rates saved successfully.")
        self.settings_updated.emit()

    def _save_densities(self):
        """Alias for backward compatibility with tests."""
        self._save_material_rates()

    def _save_rates(self):
        """Save default cutting rates and global kilo rate."""
        air = self._spin_air_rate.value()
        oxy = self._spin_oxygen_rate.value()
        kilo = self._spin_kilo_rate.value()
        cut = self._spin_cutting_rate.value()

        self._pricing_service.set_air_cutting_rate(air)
        self._pricing_service.set_oxygen_cutting_rate(oxy)
        self._pricing_service.set_default_kilo_rate(kilo)
        self._pricing_service.set_default_cutting_rate(cut)

        self._show_banner("Cutting defaults and pricing defaults saved successfully.")
        self.settings_updated.emit()

    def _add_hole_rate(self):
        diameter = self._spin_new_diameter.value()
        unit = self._combo_new_unit.currentText()
        rate = self._spin_new_rate.value()

        existing = self._pricing_service.get_hole_rate_for_diameter(diameter, unit)
        if existing is not None:
            QMessageBox.warning(
                self,
                "Duplicate Entry",
                f"A rate for {diameter:g} {unit} already exists (₹{existing:g}).",
            )
            return

        self._pricing_service.add_hole_rate(diameter, unit, rate)
        self._show_banner(f"Added hole rate for {diameter:g} {unit} at ₹{rate:g}.")
        self.settings_updated.emit()

    def _delete_hole_rate(self, rate_id: int):
        confirmed = ConfirmationDialog.confirm(
            self,
            "Delete Hole Rate",
            "Are you sure you want to delete this hole rate?",
            confirm_text="Delete",
            destructive=True,
        )
        if confirmed:
            self._pricing_service.delete_hole_rate(rate_id)
            self._load_hole_rates()
            self._show_banner("Hole rate deleted.")
            self.settings_updated.emit()

    def _show_banner(self, message: str):
        self._banner_label.setText(f"✓  {message}")
        self._banner.setVisible(True)
