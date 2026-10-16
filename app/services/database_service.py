"""
Database service — SQLite connection management and schema initialization.

All database operations go through this service.
Source runs use the project data folder; packaged runs use the current user's
LaserEstimate application-data folder.
"""

import sqlite3
import os
import logging
from app.runtime_paths import database_path

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = str(database_path())

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hole_rates (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    diameter REAL    NOT NULL,
    unit     TEXT    NOT NULL DEFAULT 'mm',
    rate     REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS simple_cutting_rates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    material       TEXT    NOT NULL,
    thickness      REAL    NOT NULL,
    thickness_unit TEXT    NOT NULL DEFAULT 'mm',
    rate_per_sqft  REAL    NOT NULL,
    UNIQUE(material, thickness, thickness_unit)
);

CREATE TABLE IF NOT EXISTS material_rates (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    material   TEXT    NOT NULL UNIQUE,
    density    REAL    DEFAULT NULL,
    kilo_rate  REAL    DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS estimates (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_number   TEXT    NOT NULL UNIQUE,
    calculation_mode  TEXT    DEFAULT 'simple',
    customer_name     TEXT    DEFAULT '',
    customer_address  TEXT    DEFAULT '',
    phone             TEXT    DEFAULT '',
    employee_name     TEXT    DEFAULT '',
    date              TEXT    NOT NULL,
    description       TEXT    DEFAULT '',

    length            REAL    DEFAULT 0,
    length_unit       TEXT    DEFAULT 'cm',
    width             REAL    DEFAULT 0,
    width_unit        TEXT    DEFAULT 'cm',

    length_ft         REAL    DEFAULT 0,
    width_ft          REAL    DEFAULT 0,
    area_sqft         REAL    DEFAULT 0,
    rate_per_sqft     REAL    DEFAULT 0,

    material          TEXT    DEFAULT '',
    thickness         REAL    DEFAULT 0,
    thickness_unit    TEXT    DEFAULT 'mm',
    sheet_length      REAL    DEFAULT 0,
    sheet_width       REAL    DEFAULT 0,
    sheet_weight      REAL    DEFAULT 0,
    kilo_rate         REAL    DEFAULT 0,

    is_weight_overridden INTEGER DEFAULT 0,
    manual_sheet_weight  REAL    DEFAULT 0,
    material_density     REAL    DEFAULT 7.85,

    cutting_method        TEXT    DEFAULT 'Air',
    cutting_hours         INTEGER DEFAULT 0,
    cutting_minutes       INTEGER DEFAULT 0,
    total_cutting_min     REAL    DEFAULT 0,
    cutting_rate          REAL    DEFAULT 0,
    cutting_rate_per_hour REAL    DEFAULT 1500,

    material_amount   REAL    DEFAULT 0,
    cutting_amount    REAL    DEFAULT 0,
    design_amount     REAL    DEFAULT 0,
    quantity          INTEGER DEFAULT 1,
    per_piece_amount  REAL    DEFAULT 0,
    final_amount      REAL    DEFAULT 0,

    created_at        TEXT    NOT NULL,
    updated_at        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS estimate_holes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id   INTEGER NOT NULL,
    diameter      REAL    NOT NULL,
    diameter_unit TEXT    NOT NULL DEFAULT 'mm',
    quantity      INTEGER NOT NULL,
    rate          REAL    NOT NULL,
    amount        REAL    NOT NULL,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE
);
"""

# Default settings to seed on first run
_DEFAULT_SETTINGS = {
    "default_kilo_rate": "250",
    "default_cutting_rate": "30",
    "default_air_cutting_rate": "1500",
    "default_oxygen_cutting_rate": "1800",
    "company_name": "",
    "company_phone": "",
    "company_address": "",
    "company_gstin": "",
    "company_mobile": "",
    "company_email": "",
    "quotation_terms": "",
    "bank_account_name": "",
    "bank_name": "",
    "bank_account_number": "",
    "bank_branch": "",
    "bank_ifsc": "",
    "currency_symbol": "₹",
    "density_Mild Steel": "7.85",
    "density_SS 202": "7.80",
    "density_Stainless Steel": "8.00",
    "density_C45": "7.85",
    "density_Japan Sheet": "7.85",
    "density_GI": "7.85",
    "density_Aluminium": "2.70",
    "density_Brass": "8.50",
    "density_Copper": "8.96",
}

# Default hole rates to seed on first run
_DEFAULT_HOLE_RATES = [
    (5.0, "mm", 8.0),
    (10.0, "mm", 12.0),
    (15.0, "mm", 15.0),
    (20.0, "mm", 20.0),
]

# Default simple cutting rates to seed on first run (from client specification)
_DEFAULT_SIMPLE_RATES = [
    ("Mild Steel", 3.0, "mm", 330.0),
]


class DatabaseService:
    """Manages the SQLite database connection and schema."""

    def __init__(self, db_path: str = None):
        """Initialize the database service.

        Args:
            db_path: Path to the SQLite database file.
                     Defaults to the development database in source runs or
                     the per-user application database in packaged runs.
        """
        self.db_path = db_path or _DEFAULT_DB_PATH
        self._connection = None

    def get_connection(self) -> sqlite3.Connection:
        """Get or create the database connection.

        Returns:
            sqlite3.Connection with row_factory set to sqlite3.Row.
        """
        if self._connection is None:
            # Ensure the directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Database connected: {self.db_path}")

        return self._connection

    def initialize(self):
        """Create database tables and seed default data if needed."""
        conn = self.get_connection()
        conn.executescript(_SCHEMA_SQL)

        # Migration: ensure new columns exist in estimates table for older DB files
        cursor = conn.execute("PRAGMA table_info(estimates)")
        existing_cols = {row["name"] for row in cursor.fetchall()}

        if "customer_address" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN customer_address TEXT DEFAULT ''")
        if "employee_name" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN employee_name TEXT DEFAULT ''")
        if "is_weight_overridden" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN is_weight_overridden INTEGER DEFAULT 0")
        if "manual_sheet_weight" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN manual_sheet_weight REAL DEFAULT 0")
        if "material_density" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN material_density REAL DEFAULT 7.85")
        if "calculation_mode" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN calculation_mode TEXT DEFAULT 'design_heavy'")
        if "rate_per_sqft" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN rate_per_sqft REAL DEFAULT 0")
        if "cutting_method" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN cutting_method TEXT DEFAULT 'Air'")
        if "cutting_rate_per_hour" not in existing_cols:
            conn.execute("ALTER TABLE estimates ADD COLUMN cutting_rate_per_hour REAL DEFAULT 1500")

        # Seed default settings if missing
        for key, value in _DEFAULT_SETTINGS.items():
            cursor = conn.execute("SELECT COUNT(*) FROM settings WHERE key = ?", (key,))
            if cursor.fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    (key, value),
                )

        # Seed default hole rates if table is empty
        cursor = conn.execute("SELECT COUNT(*) FROM hole_rates")
        if cursor.fetchone()[0] == 0:
            for diameter, unit, rate in _DEFAULT_HOLE_RATES:
                conn.execute(
                    "INSERT INTO hole_rates (diameter, unit, rate) VALUES (?, ?, ?)",
                    (diameter, unit, rate),
                )
            logger.info("Default hole rates seeded.")

        # Seed default simple cutting rates if table is empty
        cursor = conn.execute("SELECT COUNT(*) FROM simple_cutting_rates")
        if cursor.fetchone()[0] == 0:
            for mat, thick, unit, rate in _DEFAULT_SIMPLE_RATES:
                conn.execute(
                    """INSERT OR IGNORE INTO simple_cutting_rates
                       (material, thickness, thickness_unit, rate_per_sqft)
                       VALUES (?, ?, ?, ?)""",
                    (mat, thick, unit, rate),
                )
            logger.info("Default simple cutting rates seeded.")

        conn.commit()
        logger.info("Database initialized.")



    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed.")
