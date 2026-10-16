"""
Estimate service — CRUD operations for estimates.

Handles saving, loading, searching, auto-numbering, and duplicate/delete.
Stores the rates used at the time of creation to preserve original quotations.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from app.models.estimate import Estimate, HoleEntry
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class EstimateService:
    """Service for managing estimates in the database."""

    def __init__(self, db_service: DatabaseService):
        self._db = db_service

    # ── Auto-numbering ─────────────────────────────────────────

    def get_next_estimate_number(self) -> str:
        """Generate the next unused estimate number (EST-0001, EST-0002, ...).

        Uses the highest existing numeric suffix so numbering stays continuous
        and never collides with a number that is already saved (including when
        ids and numbers are out of order after edits/duplicates/deletes).

        Returns:
            The next unused estimate number string.
        """
        conn = self._db.get_connection()
        cursor = conn.execute("SELECT estimate_number FROM estimates")
        used = set()
        max_num = 0
        for row in cursor.fetchall():
            number = row["estimate_number"] or ""
            used.add(number)
            try:
                num = int(str(number).split("-")[1])
            except (IndexError, ValueError):
                continue
            if num > max_num:
                max_num = num

        next_num = max_num + 1
        while True:
            candidate = f"EST-{next_num:04d}"
            if candidate not in used:
                return candidate
            next_num += 1

    # ── Save / Update ──────────────────────────────────────────

    def save_estimate(self, estimate: Estimate) -> int:
        """Save a new estimate to the database.

        Args:
            estimate: The Estimate dataclass to save.

        Returns:
            The database ID of the saved estimate.
        """
        conn = self._db.get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # New rows must never reuse an existing UNIQUE estimate_number.
        # Editing keeps its number via update_estimate(); this path is insert-only.
        if not estimate.estimate_number or self._estimate_number_exists(
            conn, estimate.estimate_number
        ):
            estimate.estimate_number = self.get_next_estimate_number()

        placeholders = ", ".join("?" for _ in range(40))
        cursor = conn.execute(
            f"""INSERT INTO estimates (
                estimate_number, calculation_mode, customer_name, customer_address, phone,
                employee_name, date, description,
                length, length_unit, width, width_unit,
                length_ft, width_ft, area_sqft, rate_per_sqft,
                material, thickness, thickness_unit,
                sheet_length, sheet_width, sheet_weight, kilo_rate,
                is_weight_overridden, manual_sheet_weight, material_density,
                cutting_method, cutting_hours, cutting_minutes, total_cutting_min,
                cutting_rate, cutting_rate_per_hour,
                material_amount, cutting_amount, design_amount,
                quantity, per_piece_amount, final_amount,
                created_at, updated_at
            ) VALUES ({placeholders})""",
            (
                estimate.estimate_number, estimate.calculation_mode, estimate.customer_name,
                estimate.customer_address, estimate.phone, estimate.employee_name,
                estimate.date, estimate.description,
                estimate.length, estimate.length_unit,
                estimate.width, estimate.width_unit,
                estimate.length_ft, estimate.width_ft, estimate.area_sqft, estimate.rate_per_sqft,
                estimate.material, estimate.thickness, estimate.thickness_unit,
                estimate.sheet_length, estimate.sheet_width,
                estimate.sheet_weight, estimate.kilo_rate,
                1 if estimate.is_weight_overridden else 0,
                estimate.manual_sheet_weight,
                estimate.material_density,
                estimate.cutting_method,
                estimate.cutting_hours, estimate.cutting_minutes,
                estimate.total_cutting_min,
                estimate.cutting_rate,
                estimate.cutting_rate_per_hour,
                estimate.material_amount, estimate.cutting_amount,
                estimate.design_amount,
                estimate.quantity, estimate.per_piece_amount,
                estimate.final_amount,
                now, now,
            ),
        )
        estimate_id = cursor.lastrowid

        # Save holes
        self._save_holes(conn, estimate_id, estimate.holes)

        conn.commit()
        logger.info(f"Saved estimate {estimate.estimate_number} (id={estimate_id})")
        return estimate_id

    def update_estimate(self, estimate: Estimate):
        """Update an existing estimate.

        Args:
            estimate: The Estimate with id set.
        """
        if estimate.id is None:
            raise ValueError("Cannot update an estimate without an id.")

        conn = self._db.get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """UPDATE estimates SET
                estimate_number = ?, calculation_mode = ?, customer_name = ?,
                customer_address = ?, phone = ?, employee_name = ?, date = ?, description = ?,
                length = ?, length_unit = ?, width = ?, width_unit = ?,
                length_ft = ?, width_ft = ?, area_sqft = ?, rate_per_sqft = ?,
                material = ?, thickness = ?, thickness_unit = ?,
                sheet_length = ?, sheet_width = ?,
                sheet_weight = ?, kilo_rate = ?,
                is_weight_overridden = ?, manual_sheet_weight = ?, material_density = ?,
                cutting_method = ?, cutting_hours = ?, cutting_minutes = ?,
                total_cutting_min = ?, cutting_rate = ?, cutting_rate_per_hour = ?,
                material_amount = ?, cutting_amount = ?, design_amount = ?,
                quantity = ?, per_piece_amount = ?, final_amount = ?,
                updated_at = ?
            WHERE id = ?""",
            (
                estimate.estimate_number, estimate.calculation_mode, estimate.customer_name,
                estimate.customer_address, estimate.phone, estimate.employee_name,
                estimate.date, estimate.description,
                estimate.length, estimate.length_unit,
                estimate.width, estimate.width_unit,
                estimate.length_ft, estimate.width_ft, estimate.area_sqft, estimate.rate_per_sqft,
                estimate.material, estimate.thickness, estimate.thickness_unit,
                estimate.sheet_length, estimate.sheet_width,
                estimate.sheet_weight, estimate.kilo_rate,
                1 if estimate.is_weight_overridden else 0,
                estimate.manual_sheet_weight,
                estimate.material_density,
                estimate.cutting_method,
                estimate.cutting_hours, estimate.cutting_minutes,
                estimate.total_cutting_min,
                estimate.cutting_rate,
                estimate.cutting_rate_per_hour,
                estimate.material_amount, estimate.cutting_amount,
                estimate.design_amount,
                estimate.quantity, estimate.per_piece_amount,
                estimate.final_amount,
                now,
                estimate.id,
            ),
        )



        # Replace holes: delete old, insert new
        conn.execute(
            "DELETE FROM estimate_holes WHERE estimate_id = ?", (estimate.id,)
        )
        self._save_holes(conn, estimate.id, estimate.holes)

        conn.commit()
        logger.info(f"Updated estimate {estimate.estimate_number} (id={estimate.id})")

    def _save_holes(self, conn, estimate_id: int, holes: List[HoleEntry]):
        """Insert hole entries for an estimate."""
        for hole in holes:
            conn.execute(
                """INSERT INTO estimate_holes
                   (estimate_id, diameter, diameter_unit, quantity, rate, amount)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    estimate_id,
                    hole.diameter, hole.diameter_unit,
                    hole.quantity, hole.rate, hole.amount,
                ),
            )

    # ── Read ───────────────────────────────────────────────────

    def get_estimate_by_id(self, estimate_id: int) -> Optional[Estimate]:
        """Load a single estimate by its database ID.

        Returns:
            Estimate with holes populated, or None if not found.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM estimates WHERE id = ?", (estimate_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None

        estimate = self._row_to_estimate(row)

        # Load holes
        holes_cursor = conn.execute(
            "SELECT * FROM estimate_holes WHERE estimate_id = ? ORDER BY id",
            (estimate_id,),
        )
        estimate.holes = [self._row_to_hole(h) for h in holes_cursor.fetchall()]

        return estimate

    def get_all_estimates(self) -> List[Estimate]:
        """Get all estimates, newest first.

        Returns:
            List of Estimate objects (without holes loaded for performance).
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM estimates ORDER BY id DESC"
        )
        return [self._row_to_estimate(row) for row in cursor.fetchall()]

    def search_estimates(self, query: str) -> List[Estimate]:
        """Search estimates by customer name, estimate number, or description.

        Args:
            query: Search text.

        Returns:
            List of matching estimates.
        """
        conn = self._db.get_connection()
        search = f"%{query}%"
        cursor = conn.execute(
            """SELECT * FROM estimates
               WHERE customer_name LIKE ?
                  OR estimate_number LIKE ?
                  OR description LIKE ?
                  OR phone LIKE ?
               ORDER BY id DESC""",
            (search, search, search, search),
        )
        return [self._row_to_estimate(row) for row in cursor.fetchall()]

    def get_today_count(self) -> int:
        """Get the number of estimates created today.

        Returns:
            Count of today's estimates.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM estimates WHERE date(created_at) = ?",
            (today,),
        )
        return cursor.fetchone()[0]

    def get_total_count(self) -> int:
        """Get the total number of estimates.

        Returns:
            Total estimate count.
        """
        conn = self._db.get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM estimates")
        return cursor.fetchone()[0]

    def get_recent_estimates(self, limit: int = 5) -> List[Estimate]:
        """Get the most recent estimates.

        Args:
            limit: Maximum number to return.

        Returns:
            List of recent estimates.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM estimates ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [self._row_to_estimate(row) for row in cursor.fetchall()]

    # ── Delete / Duplicate ────────────────────────────────────

    def delete_estimate(self, estimate_id: int):
        """Delete an estimate and its hole entries.

        Args:
            estimate_id: The database ID of the estimate to delete.
        """
        conn = self._db.get_connection()
        conn.execute("DELETE FROM estimate_holes WHERE estimate_id = ?", (estimate_id,))
        conn.execute("DELETE FROM estimates WHERE id = ?", (estimate_id,))
        conn.commit()
        logger.info(f"Deleted estimate id={estimate_id}")

    def duplicate_estimate(self, estimate_id: int) -> Optional[int]:
        """Duplicate an existing estimate with a new estimate number.

        Args:
            estimate_id: The ID of the estimate to duplicate.

        Returns:
            The ID of the new estimate, or None if source not found.
        """
        original = self.get_estimate_by_id(estimate_id)
        if original is None:
            return None

        # Assign new number and clear ID
        original.id = None
        original.estimate_number = self.get_next_estimate_number()
        original.date = datetime.now().strftime("%d/%m/%Y")

        # Clear hole IDs
        for hole in original.holes:
            hole.id = None
            hole.estimate_id = None

        new_id = self.save_estimate(original)
        logger.info(
            f"Duplicated estimate id={estimate_id} → "
            f"{original.estimate_number} (id={new_id})"
        )
        return new_id

    # ── Materials autocomplete ────────────────────────────────

    def get_used_materials(self) -> List[str]:
        """Get distinct material names previously used.

        Returns:
            List of unique material strings for autocomplete.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "SELECT DISTINCT material FROM estimates "
            "WHERE material != '' ORDER BY material"
        )
        return [row["material"] for row in cursor.fetchall()]

    # ── Internal helpers ──────────────────────────────────────

    @staticmethod
    def _estimate_number_exists(conn, estimate_number: str) -> bool:
        cursor = conn.execute(
            "SELECT 1 FROM estimates WHERE estimate_number = ? LIMIT 1",
            (estimate_number,),
        )
        return cursor.fetchone() is not None

    @staticmethod
    def _row_to_estimate(row) -> Estimate:
        """Convert a database row to an Estimate dataclass."""
        keys = row.keys() if hasattr(row, "keys") else []
        return Estimate(
            id=row["id"],
            estimate_number=row["estimate_number"],
            calculation_mode=str(row["calculation_mode"]) if "calculation_mode" in keys and row["calculation_mode"] else "design_heavy",
            customer_name=row["customer_name"] or "",
            customer_address=(row["customer_address"] or "") if "customer_address" in keys else "",
            phone=row["phone"] or "",
            employee_name=(row["employee_name"] or "") if "employee_name" in keys else "",
            date=row["date"] or "",
            description=row["description"] or "",
            length=row["length"] or 0.0,
            length_unit=row["length_unit"] or "cm",
            width=row["width"] or 0.0,
            width_unit=row["width_unit"] or "cm",
            length_ft=row["length_ft"] or 0.0,
            width_ft=row["width_ft"] or 0.0,
            area_sqft=row["area_sqft"] or 0.0,
            rate_per_sqft=float(row["rate_per_sqft"]) if "rate_per_sqft" in keys and row["rate_per_sqft"] is not None else 0.0,
            material=row["material"] or "",
            thickness=row["thickness"] or 0.0,
            thickness_unit=row["thickness_unit"] or "mm",
            sheet_length=row["sheet_length"] or 0.0,
            sheet_width=row["sheet_width"] or 0.0,
            sheet_weight=row["sheet_weight"] or 0.0,
            kilo_rate=row["kilo_rate"] or 0.0,
            is_weight_overridden=bool(row["is_weight_overridden"]) if "is_weight_overridden" in keys else False,
            manual_sheet_weight=float(row["manual_sheet_weight"]) if "manual_sheet_weight" in keys and row["manual_sheet_weight"] is not None else 0.0,
            material_density=float(row["material_density"]) if "material_density" in keys and row["material_density"] is not None else 7.85,
            cutting_method=str(row["cutting_method"]) if "cutting_method" in keys and row["cutting_method"] else "Air",
            cutting_hours=row["cutting_hours"] or 0,
            cutting_minutes=row["cutting_minutes"] or 0,
            total_cutting_min=row["total_cutting_min"] or 0.0,
            cutting_rate=row["cutting_rate"] or 0.0,
            cutting_rate_per_hour=float(row["cutting_rate_per_hour"]) if "cutting_rate_per_hour" in keys and row["cutting_rate_per_hour"] is not None else 1500.0,
            material_amount=row["material_amount"] or 0.0,
            cutting_amount=row["cutting_amount"] or 0.0,
            design_amount=row["design_amount"] or 0.0,
            quantity=row["quantity"] or 1,
            per_piece_amount=row["per_piece_amount"] or 0.0,
            final_amount=row["final_amount"] or 0.0,
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )



    @staticmethod
    def _row_to_hole(row) -> HoleEntry:
        """Convert a database row to a HoleEntry dataclass."""
        return HoleEntry(
            id=row["id"],
            estimate_id=row["estimate_id"],
            diameter=row["diameter"],
            diameter_unit=row["diameter_unit"],
            quantity=row["quantity"],
            rate=row["rate"],
            amount=row["amount"],
        )
