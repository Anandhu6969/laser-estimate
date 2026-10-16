"""Reusable themed confirmation dialog for user decisions."""

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_class


class ConfirmationDialog(QDialog):
    """A small application-styled dialog with explicit confirm/cancel actions."""

    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        destructive: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setStyleSheet(
            "QDialog { background: #FFFFFF; }"
            "QLabel#dialogTitle { color: #1F2937; font-size: 16px; font-weight: 700; }"
            "QLabel#dialogMessage { color: #475569; font-size: 13px; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)
        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")
        message_label = QLabel(message)
        message_label.setObjectName("dialogMessage")
        message_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(message_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = QPushButton(cancel_text)
        self.confirm_button = QPushButton(confirm_text)
        apply_class(self.cancel_button, "btn-secondary")
        apply_class(self.confirm_button, "btn-danger" if destructive else "btn-primary")
        self.cancel_button.clicked.connect(self.reject)
        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.setAutoDefault(False)
        self.confirm_button.setDefault(True)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.confirm_button)
        layout.addLayout(buttons)

    @classmethod
    def confirm(
        cls,
        parent: QWidget,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        destructive: bool = False,
    ) -> bool:
        dialog = cls(title, message, confirm_text, cancel_text, destructive, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
