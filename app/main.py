"""
Main entry point for Laser Estimate desktop application.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.services.database_service import DatabaseService
from app.services.pricing_service import PricingService
from app.services.estimate_service import EstimateService
from app.ui.main_window import MainWindow
from app.runtime_paths import is_packaged, log_path


def setup_logging():
    """Configure file and console logging."""
    log_file = log_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handlers = [logging.FileHandler(log_file, encoding="utf-8")]
    if not is_packaged():
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def main():
    """Initialize services and launch the GUI application."""
    setup_logging()
    logger = logging.getLogger("LaserEstimate")
    logger.info("Starting Laser Estimate application...")

    # Initialize Database & Services
    db_service = DatabaseService()
    db_service.initialize()
    pricing_service = PricingService(db_service)
    estimate_service = EstimateService(db_service)

    # Initialize Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Laser Estimate")
    app.setOrganizationName("LaserEstimate")
    app.setStyle("Fusion")

    # Create & display Main Window
    window = MainWindow(
        db_service=db_service,
        pricing_service=pricing_service,
        estimate_service=estimate_service,
    )
    window.show()

    logger.info("Application main window launched.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
