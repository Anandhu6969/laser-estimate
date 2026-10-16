"""
Area calculator.

Computes area in square feet from length and width in any supported unit.
Uses UnitConverter internally for consistent conversions.
"""

from app.calculations.unit_converter import to_feet


def calculate_area(
    length: float,
    length_unit: str,
    width: float,
    width_unit: str,
) -> dict:
    """Calculate area in square feet from length and width.

    Args:
        length: Numeric length value.
        length_unit: Unit of the length (mm, cm, in, ft).
        width: Numeric width value.
        width_unit: Unit of the width (mm, cm, in, ft).

    Returns:
        dict with keys:
            length_ft: Length converted to feet (full precision).
            width_ft: Width converted to feet (full precision).
            area_sqft: Area in square feet (full precision).

    Raises:
        ValueError: If length or width is not positive, or unit is invalid.
    """
    if length <= 0:
        raise ValueError("Length must be greater than zero.")
    if width <= 0:
        raise ValueError("Width must be greater than zero.")

    length_ft = to_feet(length, length_unit)
    width_ft = to_feet(width, width_unit)
    area_sqft = length_ft * width_ft

    return {
        "length_ft": length_ft,
        "width_ft": width_ft,
        "area_sqft": area_sqft,
    }
