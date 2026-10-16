"""
Pricing service — manages configurable business rates.

Reads and writes settings and hole rates from/to the database.
No hardcoded prices — all rates are retrieved from persistent storage.
"""

import logging
from typing import Dict, List, Optional, Tuple
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class PricingService:
    """Service for managing configurable pricing and settings."""

    def __init__(self, db_service: DatabaseService):
        self._db = db_service

    # ── Settings CRUD ──────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        """Get a single setting value by key.

        Args:
            key: The setting key.
            default: Default value if key not found.

        Returns:
            The setting value as a string.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        """Set a single setting value. Inserts or updates.

        Args:
            key: The setting key.
            value: The value to store (as string).
        """
        conn = self._db.get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()

    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings as a dictionary.

        Returns:
            Dict mapping setting keys to values.
        """
        conn = self._db.get_connection()
        cursor = conn.execute("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in cursor.fetchall()}

    # ── Convenience methods for common rates ────────────────────

    def get_default_kilo_rate(self) -> float:
        """Get the default kilo rate (₹/kg)."""
        return float(self.get_setting("default_kilo_rate", "250"))

    def set_default_kilo_rate(self, rate: float):
        """Set the default kilo rate."""
        self.set_setting("default_kilo_rate", str(rate))

    def get_default_cutting_rate(self) -> float:
        """Get the default cutting rate (₹/minute)."""
        return float(self.get_setting("default_cutting_rate", "30"))

    def set_default_cutting_rate(self, rate: float):
        """Set the default cutting rate."""
        self.set_setting("default_cutting_rate", str(rate))

    def get_air_cutting_rate(self) -> float:
        """Get the default Air cutting rate (₹/hour). Default is 1500."""
        return float(self.get_setting("default_air_cutting_rate", "1500"))

    def set_air_cutting_rate(self, rate: float):
        """Set the default Air cutting rate (₹/hour)."""
        self.set_setting("default_air_cutting_rate", str(rate))

    def get_oxygen_cutting_rate(self) -> float:
        """Get the default Oxygen cutting rate (₹/hour). Default is 1800."""
        return float(self.get_setting("default_oxygen_cutting_rate", "1800"))

    def set_oxygen_cutting_rate(self, rate: float):
        """Set the default Oxygen cutting rate (₹/hour)."""
        self.set_setting("default_oxygen_cutting_rate", str(rate))

    # ── Material Kilo Rates ────────────────────────────────────

    def get_material_kilo_rate(self, material_name: str) -> float:
        """Get the configured kilo rate (₹/kg) for a specific material.

        Falls back to the global default kilo rate if no material-specific rate is set.
        """
        if not material_name:
            return self.get_default_kilo_rate()

        key = f"kilo_rate_{material_name.strip()}"
        val = self.get_setting(key, "")
        if val:
            try:
                return float(val)
            except ValueError:
                pass

        # Case-insensitive check
        all_settings = self.get_all_settings()
        mat_clean = material_name.strip().lower()
        for k, v in all_settings.items():
            if k.startswith("kilo_rate_"):
                mat_key = k[len("kilo_rate_"):].strip().lower()
                if mat_key == mat_clean or mat_key in mat_clean or mat_clean in mat_key:
                    try:
                        return float(v)
                    except ValueError:
                        pass

        return self.get_default_kilo_rate()

    def set_material_kilo_rate(self, material_name: str, rate: float):
        """Set material-specific kilo rate."""
        key = f"kilo_rate_{material_name.strip()}"
        self.set_setting(key, str(rate))

    def get_all_material_kilo_rates(self) -> Dict[str, float]:
        """Get all configured material kilo rates."""
        result = {}
        all_settings = self.get_all_settings()
        for k, v in all_settings.items():
            if k.startswith("kilo_rate_"):
                mat_name = k[len("kilo_rate_"):]
                try:
                    result[mat_name] = float(v)
                except ValueError:
                    pass
        return result

    # ── Material Density Settings ─────────────────────────────

    def get_material_density(self, material_name: str) -> float:
        """Get density (kg/L) for a given material name."""
        from app.calculations.sheet_calculator import get_material_density as default_density_lookup

        if not material_name:
            return default_density_lookup(material_name)

        # Check DB setting first
        key = f"density_{material_name.strip()}"
        val = self.get_setting(key, "")
        if val:
            try:
                return float(val)
            except ValueError:
                pass

        # Try case-insensitive check against settings
        all_settings = self.get_all_settings()
        mat_clean = material_name.strip().lower()
        for k, v in all_settings.items():
            if k.startswith("density_"):
                mat_key = k[len("density_"):].strip().lower()
                if mat_key == mat_clean or mat_key in mat_clean or mat_clean in mat_key:
                    try:
                        return float(v)
                    except ValueError:
                        pass

        # Fallback to standard calculator lookup
        return default_density_lookup(material_name)

    def set_material_density(self, material_name: str, density: float):
        """Set density for a material name."""
        key = f"density_{material_name.strip()}"
        self.set_setting(key, str(density))

    def get_all_material_densities(self) -> Dict[str, float]:
        """Get all configured material densities."""
        from app.calculations.sheet_calculator import STANDARD_MATERIAL_DENSITIES

        result = dict(STANDARD_MATERIAL_DENSITIES)
        all_settings = self.get_all_settings()
        for k, v in all_settings.items():
            if k.startswith("density_"):
                mat_name = k[len("density_"):]
                try:
                    result[mat_name] = float(v)
                except ValueError:
                    pass
        return result

    def get_configured_materials(self) -> List[str]:
        """Return the unique materials available through Settings.

        Standard calculator materials remain available by default; materials
        added to either Settings matrix are included as well.
        """
        from app.calculations.sheet_calculator import STANDARD_MATERIALS

        names = list(STANDARD_MATERIALS)
        names.extend(rate["material"] for rate in self.get_simple_cutting_rates())
        names.extend(self.get_all_material_densities().keys())
        names.extend(self.get_all_material_kilo_rates().keys())
        return list(dict.fromkeys(name.strip() for name in names if name and name.strip()))

    # ── Simple Cutting Rates CRUD ──────────────────────────────

    def get_simple_cutting_rates(self) -> List[Dict]:
        """Get all configured Simple Cutting rates from matrix.

        Returns:
            List of dicts with keys: id, material, thickness, thickness_unit, rate_per_sqft.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT id, material, thickness, thickness_unit, rate_per_sqft "
            "FROM simple_cutting_rates ORDER BY material, thickness"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_simple_cutting_rate(
        self, material: str, thickness: float, thickness_unit: str = "mm"
    ) -> Optional[float]:
        """Look up configured Simple Cutting rate per sq.ft for a material and thickness.

        Args:
            material: Material name.
            thickness: Thickness value.
            thickness_unit: Thickness unit (default 'mm').

        Returns:
            Rate per sq.ft if found, None otherwise.
        """
        if not material or thickness <= 0:
            return None

        conn = self._db.get_connection()
        # Direct match
        cursor = conn.execute(
            "SELECT rate_per_sqft FROM simple_cutting_rates "
            "WHERE LOWER(material) = LOWER(?) AND thickness = ? AND LOWER(thickness_unit) = LOWER(?)",
            (material.strip(), thickness, thickness_unit.strip()),
        )
        row = cursor.fetchone()
        if row:
            return float(row["rate_per_sqft"])

        # Case / partial material match
        cursor = conn.execute(
            "SELECT material, thickness, thickness_unit, rate_per_sqft FROM simple_cutting_rates"
        )
        mat_clean = material.strip().lower()
        for r in cursor.fetchall():
            r_mat = r["material"].strip().lower()
            if (r_mat == mat_clean or r_mat in mat_clean or mat_clean in r_mat) and (
                abs(float(r["thickness"]) - thickness) < 0.001
            ) and (r["thickness_unit"].strip().lower() == thickness_unit.strip().lower()):
                return float(r["rate_per_sqft"])

        return None

    def add_simple_cutting_rate(
        self, material: str, thickness: float, thickness_unit: str, rate_per_sqft: float
    ) -> int:
        """Add or replace a simple cutting rate matrix entry.

        Args:
            material: Material name.
            thickness: Thickness value.
            thickness_unit: Thickness unit.
            rate_per_sqft: Price per sq.ft.

        Returns:
            The row ID.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            """INSERT OR REPLACE INTO simple_cutting_rates
               (material, thickness, thickness_unit, rate_per_sqft)
               VALUES (?, ?, ?, ?)""",
            (material.strip(), thickness, thickness_unit.strip(), rate_per_sqft),
        )
        conn.commit()
        return cursor.lastrowid

    def update_simple_cutting_rate(
        self, rate_id: int, material: str, thickness: float, thickness_unit: str, rate_per_sqft: float
    ):
        """Update an existing simple cutting rate entry."""
        conn = self._db.get_connection()
        conn.execute(
            """UPDATE simple_cutting_rates
               SET material = ?, thickness = ?, thickness_unit = ?, rate_per_sqft = ?
               WHERE id = ?""",
            (material.strip(), thickness, thickness_unit.strip(), rate_per_sqft, rate_id),
        )
        conn.commit()

    def delete_simple_cutting_rate(self, rate_id: int):
        """Delete a simple cutting rate matrix entry."""
        conn = self._db.get_connection()
        conn.execute("DELETE FROM simple_cutting_rates WHERE id = ?", (rate_id,))
        conn.commit()

    # ── Hole Rates CRUD (Legacy / Backward Compatibility) ─────

    def get_hole_rates(self) -> List[Dict]:
        """Get all configured hole rates.

        Returns:
            List of dicts with keys: id, diameter, unit, rate.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT id, diameter, unit, rate FROM hole_rates ORDER BY diameter"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_hole_rate_for_diameter(
        self, diameter: float, unit: str = "mm"
    ) -> Optional[float]:
        """Look up the configured rate for a specific hole diameter.

        Args:
            diameter: The hole diameter.
            unit: The diameter unit (default 'mm').

        Returns:
            The rate if found, None otherwise.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT rate FROM hole_rates WHERE diameter = ? AND unit = ?",
            (diameter, unit),
        )
        row = cursor.fetchone()
        return row["rate"] if row else None

    def add_hole_rate(self, diameter: float, unit: str, rate: float) -> int:
        """Add a new hole rate entry.

        Args:
            diameter: Hole diameter.
            unit: Diameter unit.
            rate: Price per hole.

        Returns:
            The ID of the newly inserted row.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "INSERT INTO hole_rates (diameter, unit, rate) VALUES (?, ?, ?)",
            (diameter, unit, rate),
        )
        conn.commit()
        return cursor.lastrowid

    def update_hole_rate(self, rate_id: int, diameter: float, unit: str, rate: float):
        """Update an existing hole rate.

        Args:
            rate_id: The database ID of the hole rate to update.
            diameter: New diameter value.
            unit: New unit value.
            rate: New price per hole.
        """
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE hole_rates SET diameter = ?, unit = ?, rate = ? WHERE id = ?",
            (diameter, unit, rate, rate_id),
        )
        conn.commit()

    def delete_hole_rate(self, rate_id: int):
        """Delete a hole rate entry.

        Args:
            rate_id: The database ID of the hole rate to delete.
        """
        conn = self._db.get_connection()
        conn.execute("DELETE FROM hole_rates WHERE id = ?", (rate_id,))
        conn.commit()


