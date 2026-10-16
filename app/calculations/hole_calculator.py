"""
Hole / design charges calculator.

Computes costs for laser-cut holes and design elements.
Rates are always passed in — never hardcoded.
"""

from typing import List


def calculate_hole_cost(quantity: int, rate: float) -> float:
    """Calculate cost for a single hole type.

    Args:
        quantity: Number of holes.
        rate: Price per hole (configurable).

    Returns:
        Amount for this hole type (quantity × rate).

    Raises:
        ValueError: If quantity or rate is negative.
    """
    if quantity < 0:
        raise ValueError("Hole quantity cannot be negative.")
    if rate < 0:
        raise ValueError("Hole rate cannot be negative.")

    return quantity * rate


def calculate_total_hole_cost(holes: List[dict]) -> float:
    """Calculate total design/hole charges from a list of hole entries.

    Args:
        holes: List of dicts, each with 'quantity' (int) and 'rate' (float).

    Returns:
        Sum of all hole costs.

    Raises:
        ValueError: If any entry has invalid quantity or rate.
    """
    total = 0.0
    for entry in holes:
        total += calculate_hole_cost(entry["quantity"], entry["rate"])
    return total
