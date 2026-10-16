"""
Brand theme constants for Laser Estimate.

All visual tokens live here so pages do not scatter hex values.
"""

from PySide6.QtWidgets import QPushButton, QWidget

# ── Brand ──────────────────────────────────────────────────────
PRIMARY_BLUE = "#070799"
PRIMARY_BLUE_HOVER = "#0A0ACC"
PRIMARY_BLUE_PRESSED = "#05056B"
PRIMARY_BLUE_SOFT = "#EEF2FF"

PRIMARY_RED = "#BF0C10"
PRIMARY_RED_HOVER = "#A40A0E"
PRIMARY_RED_PRESSED = "#8A080C"

WHITE = "#FFFFFF"

# ── Neutrals ───────────────────────────────────────────────────
TEXT_PRIMARY = "#1F2937"
TEXT_SECONDARY = "#64748B"
TEXT_ON_BLUE = "#FFFFFF"
BACKGROUND = "#F5F7FA"
SURFACE = "#FFFFFF"
BORDER = "#D9DEE7"
ROW_HOVER = "#EEF2FF"
TABLE_HEADER = "#F8FAFC"

# ── Status ─────────────────────────────────────────────────────
SUCCESS = "#15803D"
SUCCESS_BG = "#ECFDF5"
WARNING = "#D97706"
WARNING_BG = "#FFFBEB"
ERROR = "#B91C1C"
ERROR_BG = "#FEF2F2"

SIDEBAR_WIDTH = 236
APP_VERSION = "1.0"

_BUTTON_QSS = {
    "btn-primary": f"""
        QPushButton {{
            background-color: {PRIMARY_BLUE};
            color: {WHITE};
            border: 1px solid {PRIMARY_BLUE};
            border-radius: 4px;
            padding: 8px 14px;
            min-height: 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_BLUE_HOVER};
            border-color: {PRIMARY_BLUE_HOVER};
            color: {WHITE};
        }}
        QPushButton:pressed {{
            background-color: {PRIMARY_BLUE_PRESSED};
            border-color: {PRIMARY_BLUE_PRESSED};
            color: {WHITE};
        }}
        QPushButton:disabled {{
            background-color: {BORDER};
            border-color: {BORDER};
            color: {TEXT_SECONDARY};
        }}
    """,
    "btn-secondary": f"""
        QPushButton {{
            background-color: {WHITE};
            color: {PRIMARY_BLUE};
            border: 1px solid {PRIMARY_BLUE};
            border-radius: 4px;
            padding: 8px 14px;
            min-height: 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_BLUE_SOFT};
            color: {PRIMARY_BLUE};
        }}
        QPushButton:pressed {{
            background-color: {ROW_HOVER};
        }}
        QPushButton:disabled {{
            background-color: {BACKGROUND};
            color: {TEXT_SECONDARY};
            border-color: {BORDER};
        }}
    """,
    "btn-danger": f"""
        QPushButton {{
            background-color: {PRIMARY_RED};
            color: {WHITE};
            border: 1px solid {PRIMARY_RED};
            border-radius: 4px;
            padding: 8px 14px;
            min-height: 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_RED_HOVER};
            color: {WHITE};
        }}
        QPushButton:pressed {{
            background-color: {PRIMARY_RED_PRESSED};
            color: {WHITE};
        }}
    """,
    "btn-ghost": f"""
        QPushButton {{
            background-color: {WHITE};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 14px;
            min-height: 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {BACKGROUND};
            border-color: {TEXT_SECONDARY};
        }}
    """,
    "nav-btn": f"""
        QPushButton {{
            background-color: transparent;
            color: {TEXT_ON_BLUE};
            border: none;
            border-radius: 6px;
            padding: 11px 14px;
            text-align: left;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.14);
            color: {TEXT_ON_BLUE};
        }}
        QPushButton:checked {{
            background-color: {WHITE};
            color: {PRIMARY_BLUE};
            font-weight: 700;
            border-left: 4px solid {PRIMARY_RED};
            padding-left: 10px;
        }}
    """,
}


def apply_class(widget: QWidget, class_name: str) -> None:
    """Apply a role class and, for buttons, an explicit stylesheet.

    Windows native styles often ignore QSS background-color on QPushButton
    unless the widget has its own stylesheet.
    """
    widget.setProperty("class", class_name)
    if isinstance(widget, QPushButton) and class_name in _BUTTON_QSS:
        widget.setStyleSheet(_BUTTON_QSS[class_name])
        widget.setAutoFillBackground(True)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()
