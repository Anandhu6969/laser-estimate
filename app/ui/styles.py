"""Centralized QSS stylesheet for Laser Estimate.

Uses brand tokens from app.ui.theme. Selectors use Qt property
attributes ([class="..."]) so button/card styles actually apply.
"""

from app.ui.theme import (
    BACKGROUND,
    BORDER,
    ERROR,
    PRIMARY_BLUE,
    PRIMARY_BLUE_HOVER,
    PRIMARY_BLUE_PRESSED,
    PRIMARY_BLUE_SOFT,
    PRIMARY_RED,
    PRIMARY_RED_HOVER,
    PRIMARY_RED_PRESSED,
    ROW_HOVER,
    SIDEBAR_WIDTH,
    SUCCESS,
    SUCCESS_BG,
    SURFACE,
    TABLE_HEADER,
    TEXT_ON_BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
    WHITE,
)
from app.runtime_paths import resource_path

_SPIN_UP_ARROW = resource_path("app", "ui", "assets", "spin_up.svg").as_posix()
_SPIN_DOWN_ARROW = resource_path("app", "ui", "assets", "spin_down.svg").as_posix()
_COMBO_DOWN_ARROW = resource_path("app", "ui", "assets", "combo_down.svg").as_posix()
_CHECKMARK = resource_path("app", "ui", "assets", "checkbox_check.svg").as_posix()

APP_STYLESHEET = f"""
/* ─── Global ─── */
QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

QMainWindow {{
    background-color: {BACKGROUND};
}}

QDialog {{
    background-color: {BACKGROUND};
}}

QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

QScrollBar:vertical {{
    border: none;
    background: {BACKGROUND};
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    min-height: 28px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {TEXT_SECONDARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    border: none;
    background: {BACKGROUND};
    height: 10px;
    margin: 0px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER};
    min-width: 28px;
    border-radius: 5px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ─── Sidebar ─── */
#sidebar {{
    background-color: {PRIMARY_BLUE};
    min-width: {SIDEBAR_WIDTH}px;
    max-width: {SIDEBAR_WIDTH}px;
}}

#sidebarHeader {{
    background-color: {PRIMARY_BLUE};
    border-bottom: 1px solid rgba(255, 255, 255, 0.18);
}}

#sidebarTitle {{
    color: {TEXT_ON_BLUE};
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}

#sidebarSubtitle {{
    color: rgba(255, 255, 255, 0.78);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
}}

#sidebarNav {{
    background-color: {PRIMARY_BLUE};
}}

QPushButton[class="nav-btn"] {{
    background-color: transparent;
    color: {TEXT_ON_BLUE};
    border: none;
    border-radius: 6px;
    padding: 11px 14px;
    text-align: left;
    font-size: 14px;
    font-weight: 600;
}}

QPushButton[class="nav-btn"]:hover {{
    background-color: rgba(255, 255, 255, 0.14);
    color: {TEXT_ON_BLUE};
}}

QPushButton[class="nav-btn"]:focus {{
    border: 1px solid rgba(255, 255, 255, 0.55);
}}

QPushButton[class="nav-btn"]:checked {{
    background-color: {WHITE};
    color: {PRIMARY_BLUE};
    font-weight: 700;
    border-left: 4px solid {PRIMARY_RED};
    padding-left: 10px;
}}

#sidebarFooter {{
    background-color: {PRIMARY_BLUE_PRESSED};
    border-top: 1px solid rgba(255, 255, 255, 0.18);
}}

#sidebarFooterText {{
    color: rgba(255, 255, 255, 0.82);
    font-size: 12px;
    font-weight: 600;
}}

#sidebarFooterMuted {{
    color: rgba(255, 255, 255, 0.62);
    font-size: 11px;
}}

/* ─── Cards ─── */
QFrame[class="card"] {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}

QLabel[class="card-title"] {{
    color: {TEXT_PRIMARY};
    font-size: 16px;
    font-weight: 700;
}}

QLabel[class="card-subtitle"] {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 500;
}}

QFrame[class="stat-card"] {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}

QLabel[class="stat-title"] {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.4px;
}}

QLabel[class="stat-value"] {{
    color: {TEXT_PRIMARY};
    font-size: 24px;
    font-weight: 700;
}}

QLabel[class="stat-desc"] {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}

QLabel[class="page-title"] {{
    color: {PRIMARY_BLUE};
    font-size: 24px;
    font-weight: 700;
}}

QLabel[class="page-subtitle"] {{
    color: {TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 500;
}}

QLabel[class="form-label"] {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    font-weight: 600;
}}

QLabel[class="form-hint"] {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}

QLabel[class="meta-chip"] {{
    color: {PRIMARY_BLUE};
    background-color: {PRIMARY_BLUE_SOFT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    font-weight: 700;
}}

/* ─── Inputs ─── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 7px 10px;
    font-size: 13px;
    color: {TEXT_PRIMARY};
    min-height: 20px;
    selection-background-color: {PRIMARY_BLUE};
    selection-color: {WHITE};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
    border: 2px solid {PRIMARY_BLUE};
    padding: 6px 9px;
    background-color: {WHITE};
}}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QTextEdit:disabled {{
    background-color: {BACKGROUND};
    color: {TEXT_SECONDARY};
    border-color: {BORDER};
}}

QLineEdit:read-only {{
    background-color: {BACKGROUND};
    color: {PRIMARY_BLUE};
    font-weight: 700;
}}

/* Keep the native spin arrows visible when the input fields use QSS. */
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid {BORDER};
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid {BORDER};
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{_SPIN_UP_ARROW}");
    width: 9px;
    height: 6px;
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{_SPIN_DOWN_ARROW}");
    width: 9px;
    height: 6px;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid {BORDER};
}}

QComboBox::down-arrow {{
    image: url("{_COMBO_DOWN_ARROW}");
    width: 10px;
    height: 7px;
}}

QComboBox QAbstractItemView {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    selection-background-color: {PRIMARY_BLUE_SOFT};
    selection-color: {PRIMARY_BLUE};
    padding: 4px;
    outline: none;
}}

QCheckBox {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    font-weight: 600;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 3px;
    background: {WHITE};
}}

QCheckBox::indicator:checked {{
    background: {PRIMARY_BLUE};
    border-color: {PRIMARY_BLUE};
    image: url("{_CHECKMARK}");
}}

/* ─── Buttons ─── */
QPushButton {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    font-weight: 600;
    border-radius: 4px;
    padding: 8px 16px;
    min-height: 20px;
}}

QPushButton[class="btn-primary"] {{
    background-color: {PRIMARY_BLUE};
    color: {WHITE};
    border: 1px solid {PRIMARY_BLUE};
}}

QPushButton[class="btn-primary"]:hover {{
    background-color: {PRIMARY_BLUE_HOVER};
    border-color: {PRIMARY_BLUE_HOVER};
    color: {WHITE};
}}

QPushButton[class="btn-primary"]:pressed {{
    background-color: {PRIMARY_BLUE_PRESSED};
    border-color: {PRIMARY_BLUE_PRESSED};
    color: {WHITE};
}}

QPushButton[class="btn-primary"]:disabled {{
    background-color: {BORDER};
    border-color: {BORDER};
    color: {TEXT_SECONDARY};
}}

QPushButton[class="btn-primary"]:focus {{
    border: 2px solid {PRIMARY_BLUE_PRESSED};
}}

QPushButton[class="btn-danger"] {{
    background-color: {PRIMARY_RED};
    color: {WHITE};
    border: 1px solid {PRIMARY_RED};
}}

QPushButton[class="btn-danger"]:hover {{
    background-color: {PRIMARY_RED_HOVER};
    color: {WHITE};
}}

QPushButton[class="btn-danger"]:pressed {{
    background-color: {PRIMARY_RED_PRESSED};
    color: {WHITE};
}}

QPushButton[class="btn-danger"]:disabled {{
    background-color: {BORDER};
    color: {TEXT_SECONDARY};
    border-color: {BORDER};
}}

QPushButton[class="btn-secondary"] {{
    background-color: {WHITE};
    color: {PRIMARY_BLUE};
    border: 1px solid {PRIMARY_BLUE};
}}

QPushButton[class="btn-secondary"]:hover {{
    background-color: {PRIMARY_BLUE_SOFT};
    color: {PRIMARY_BLUE};
    border-color: {PRIMARY_BLUE};
}}

QPushButton[class="btn-secondary"]:pressed {{
    background-color: {ROW_HOVER};
    color: {PRIMARY_BLUE_PRESSED};
}}

QPushButton[class="btn-secondary"]:disabled {{
    background-color: {BACKGROUND};
    color: {TEXT_SECONDARY};
    border-color: {BORDER};
}}

QPushButton[class="btn-secondary"]:focus {{
    border: 2px solid {PRIMARY_BLUE};
}}

QPushButton[class="btn-ghost"] {{
    background-color: {WHITE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
}}

QPushButton[class="btn-ghost"]:hover {{
    background-color: {BACKGROUND};
    border-color: {TEXT_SECONDARY};
}}

/* ─── Tables ─── */
QTableWidget, QTableView {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BACKGROUND};
    selection-background-color: {ROW_HOVER};
    selection-color: {TEXT_PRIMARY};
    font-size: 13px;
    alternate-background-color: {TABLE_HEADER};
}}

QHeaderView::section {{
    background-color: {TABLE_HEADER};
    color: {TEXT_PRIMARY};
    font-size: 12px;
    font-weight: 700;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid {BORDER};
}}

QTableWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {BACKGROUND};
}}

QTableWidget::item:hover {{
    background-color: {ROW_HOVER};
}}

QTableWidget::item:selected {{
    background-color: {ROW_HOVER};
    color: {PRIMARY_BLUE};
}}

/* ─── Banners ─── */
QFrame[class="banner-info"] {{
    background-color: {PRIMARY_BLUE_SOFT};
    border: 1px solid #C7D2FE;
    border-radius: 6px;
}}

QFrame[class="banner-success"] {{
    background-color: {SUCCESS_BG};
    border: 1px solid #A7F3D0;
    border-radius: 6px;
}}

QFrame[class="banner-warning"] {{
    background-color: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 6px;
}}

QFrame[class="weight-panel"] {{
    background-color: {PRIMARY_BLUE_SOFT};
    border: 1px solid #C7D2FE;
    border-radius: 6px;
}}

QFrame[class="total-panel"] {{
    background-color: {PRIMARY_BLUE};
    border: 1px solid {PRIMARY_BLUE};
    border-radius: 6px;
}}

/* ─── Dialogs / Message boxes ─── */
QMessageBox {{
    background-color: {SURFACE};
}}

QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}

QMessageBox QPushButton {{
    min-width: 88px;
    background-color: {WHITE};
    color: {PRIMARY_BLUE};
    border: 1px solid {PRIMARY_BLUE};
    padding: 6px 14px;
}}

QMessageBox QPushButton:hover {{
    background-color: {PRIMARY_BLUE_SOFT};
}}
"""
