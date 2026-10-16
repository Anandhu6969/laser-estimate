"""
Reusable page header: title, subtitle, optional right-side action.
"""

from typing import Optional
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class PageHeader(QWidget):
    """Consistent page title block used across application pages."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        action: Optional[QWidget] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        self._title_label = QLabel(title)
        self._title_label.setProperty("class", "page-title")
        title_col.addWidget(self._title_label)

        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setProperty("class", "page-subtitle")
        self._subtitle_label.setVisible(bool(subtitle))
        title_col.addWidget(self._subtitle_label)

        layout.addLayout(title_col, 1)
        if action is not None:
            layout.addWidget(action)

    def set_title(self, title: str):
        self._title_label.setText(title)

    def set_subtitle(self, subtitle: str):
        self._subtitle_label.setText(subtitle)
        self._subtitle_label.setVisible(bool(subtitle))
