"""
Reusable Card Container Widget for Laser Estimate UI.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme import PRIMARY_BLUE


class CardWidget(QFrame):
    """A styled card container with header and content area."""

    def __init__(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        header_action: Optional[QWidget] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setObjectName("cardWidget")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(20, 16, 20, 18)
        self._main_layout.setSpacing(12)

        if title or subtitle or header_action:
            self._header_layout = QHBoxLayout()
            self._header_layout.setContentsMargins(0, 0, 0, 0)
            self._header_layout.setSpacing(12)

            title_col = QVBoxLayout()
            title_col.setSpacing(2)

            if title:
                self._title_label = QLabel(title)
                self._title_label.setProperty("class", "card-title")
                title_col.addWidget(self._title_label)
            else:
                self._title_label = None

            if subtitle:
                self._subtitle_label = QLabel(subtitle)
                self._subtitle_label.setProperty("class", "card-subtitle")
                self._subtitle_label.setWordWrap(True)
                title_col.addWidget(self._subtitle_label)
            else:
                self._subtitle_label = None

            self._header_layout.addLayout(title_col, 1)

            if header_action:
                self._header_layout.addWidget(header_action)

            self._main_layout.addLayout(self._header_layout)

            divider = QFrame()
            divider.setFrameShape(QFrame.Shape.HLine)
            divider.setFixedHeight(1)
            divider.setStyleSheet("background-color: #D9DEE7; border: none;")
            self._main_layout.addWidget(divider)

        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 4, 0, 0)
        self._content_layout.setSpacing(12)
        self._main_layout.addWidget(self._content_widget)

    @property
    def content_layout(self) -> QVBoxLayout:
        """Get the inner content layout to add child widgets."""
        return self._content_layout

    def set_title(self, title: str):
        """Update the card title."""
        if self._title_label:
            self._title_label.setText(title)


class MetricCardWidget(QFrame):
    """A styled metric/stat card for dashboard overview metrics."""

    def __init__(
        self,
        title: str,
        value: str,
        description: str = "",
        icon_text: str = "",
        accent_color: str = PRIMARY_BLUE,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setProperty("class", "stat-card")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        accent = QFrame()
        accent.setFixedWidth(4)
        accent.setStyleSheet(f"background-color: {accent_color}; border: none;")
        outer.addWidget(accent)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        title_label = QLabel(title.upper())
        title_label.setProperty("class", "stat-title")
        top_row.addWidget(title_label)
        top_row.addStretch()

        if icon_text:
            icon_badge = QLabel(icon_text)
            icon_badge.setStyleSheet(
                f"background-color: {accent_color}18; color: {accent_color}; "
                "font-size: 13px; font-weight: bold; border-radius: 4px; padding: 3px 7px;"
            )
            top_row.addWidget(icon_badge)

        layout.addLayout(top_row)

        self._val_label = QLabel(value)
        self._val_label.setProperty("class", "stat-value")
        layout.addWidget(self._val_label)

        if description:
            self._desc_label = QLabel(description)
            self._desc_label.setProperty("class", "stat-desc")
            self._desc_label.setWordWrap(True)
            layout.addWidget(self._desc_label)
        else:
            self._desc_label = None

        outer.addLayout(layout, 1)

    def set_value(self, value: str):
        """Update the metric value."""
        self._val_label.setText(value)

    def set_description(self, description: str):
        """Update the metric description."""
        if self._desc_label:
            self._desc_label.setText(description)
