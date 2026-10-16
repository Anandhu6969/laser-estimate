"""Resolve bundled resources and writable runtime paths."""

import os
import sys
from pathlib import Path


def is_packaged() -> bool:
    """Whether the process is running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Return the source project root when running from Python."""
    return Path(__file__).resolve().parent.parent


def resource_path(*parts) -> Path:
    """Resolve a read-only resource from source or a PyInstaller bundle."""
    root = Path(getattr(sys, "_MEIPASS", project_root())) if is_packaged() else project_root()
    return root.joinpath(*parts)


def application_data_dir() -> Path:
    """Return writable application data location without touching source data."""
    if not is_packaged():
        return project_root()

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "LaserEstimate"
    return Path.home() / "AppData" / "Local" / "LaserEstimate"


def database_path() -> Path:
    """Return the source database path or isolated packaged-user database."""
    if is_packaged():
        return application_data_dir() / "laser_estimate.db"
    return project_root() / "data" / "laser_estimate.db"


def log_path() -> Path:
    """Return the log path appropriate for the current runtime."""
    return application_data_dir() / "logs" / "app.log"
