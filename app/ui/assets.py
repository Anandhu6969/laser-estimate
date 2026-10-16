"""
Application asset helpers (logo paths, pixmaps).
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from app.runtime_paths import resource_path

ASSETS_DIR = resource_path("assets")
LOGO_CANDIDATES = (
    "universallogo.png",
    "logo.png",
    "logo.jpg",
    "logo.jpeg",
    "logo.webp",
    "logo.bmp",
)


def logo_path() -> Optional[str]:
    """Return the first existing company logo path, or None."""
    for name in LOGO_CANDIDATES:
        path = ASSETS_DIR / name
        if path.is_file():
            return str(path)
    return None


def load_logo_pixmap(max_width: int = 160, max_height: int = 56) -> Optional[QPixmap]:
    """Load the company logo scaled with aspect ratio preserved."""
    path = logo_path()
    if not path:
        return None
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return None
    return pixmap.scaled(
        max_width,
        max_height,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )


def company_logo_path() -> Optional[str]:
    """Explicit name for the selected company branding image."""
    return logo_path()
