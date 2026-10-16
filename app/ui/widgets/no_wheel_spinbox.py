"""Spin box for values that should not change while the user scrolls."""

from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox


class NoWheelSpinBox(QSpinBox):
    """Keep wheel scrolling from changing a value and allow it to reach a parent."""

    def wheelEvent(self, event: QWheelEvent):
        event.ignore()


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    """Double spin box that lets wheel scrolling reach its parent container."""

    def wheelEvent(self, event: QWheelEvent):
        event.ignore()
