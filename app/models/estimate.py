"""
Data models for estimates and holes.

Uses dataclasses for clean, typed data structures.
These are pure data containers — no business logic.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HoleEntry:
    """A single hole/design charge entry within an estimate."""

    diameter: float
    diameter_unit: str = "mm"
    quantity: int = 0
    rate: float = 0.0
    amount: float = 0.0
    id: Optional[int] = None
    estimate_id: Optional[int] = None


@dataclass
class Estimate:
    """A complete laser cutting estimate."""

    # Calculation mode: "simple" (Simple Cutting) or "design_heavy" (Design Heavy)
    calculation_mode: str = "design_heavy"


    # Customer details
    estimate_number: str = ""
    customer_name: str = ""
    phone: str = ""
    date: str = ""
    description: str = ""

    # Dimensions (customer input)
    length: float = 0.0
    length_unit: str = "cm"
    width: float = 0.0
    width_unit: str = "cm"

    # Dimensions (converted)
    length_ft: float = 0.0
    width_ft: float = 0.0
    area_sqft: float = 0.0

    # Simple Cutting pricing
    rate_per_sqft: float = 0.0

    # Sheet / Part information (Design Heavy)
    material: str = ""
    thickness: float = 0.0
    thickness_unit: str = "mm"
    sheet_length: float = 0.0
    sheet_width: float = 0.0
    sheet_weight: float = 0.0
    kilo_rate: float = 0.0
    is_weight_overridden: bool = False
    manual_sheet_weight: float = 0.0
    material_density: float = 7.85

    # Cutting (Design Heavy)
    cutting_method: str = "Air"  # "Air", "Oxygen", "Custom"
    cutting_hours: int = 0
    cutting_minutes: int = 0
    total_cutting_min: float = 0.0
    cutting_rate: float = 0.0  # Legacy / per-minute rate
    cutting_rate_per_hour: float = 1500.0  # Hourly rate (Air=1500, Oxygen=1800, or custom)

    # Amounts
    material_amount: float = 0.0
    cutting_amount: float = 0.0
    design_amount: float = 0.0
    quantity: int = 1
    per_piece_amount: float = 0.0
    final_amount: float = 0.0

    # Holes (Legacy / backward compatibility)
    holes: List[HoleEntry] = field(default_factory=list)

    # Database
    id: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""

    # Optional customer quotation details added after the original schema.
    customer_address: str = ""
    employee_name: str = ""

