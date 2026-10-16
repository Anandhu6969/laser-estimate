"""
Centralized unit conversion service.

All conversions go through this module. Do NOT scatter conversion
formulas in the UI or other modules.

Supported units: mm, cm, in, ft
Internal standard unit: feet (ft)
"""

# Conversion factors: how many of each unit per foot
_TO_FEET_DIVISORS = {
    "mm": 304.8,
    "cm": 30.48,
    "in": 12.0,
    "ft": 1.0,
}

SUPPORTED_UNITS = list(_TO_FEET_DIVISORS.keys())


def to_feet(value: float, unit: str) -> float:
    """Convert a measurement value from the given unit to feet.

    Args:
        value: The numeric measurement.
        unit: One of 'mm', 'cm', 'in', 'ft'.

    Returns:
        The value converted to feet (full precision, no rounding).

    Raises:
        ValueError: If the unit is not supported.
    """
    unit = unit.strip().lower()
    if unit not in _TO_FEET_DIVISORS:
        raise ValueError(
            f"Unsupported unit '{unit}'. "
            f"Supported units: {', '.join(SUPPORTED_UNITS)}"
        )
    return value / _TO_FEET_DIVISORS[unit]


def to_mm(value: float, unit: str) -> float:
    """Convert a measurement value from the given unit to millimeters.

    Args:
        value: The numeric measurement.
        unit: One of 'mm', 'cm', 'in', 'ft'.

    Returns:
        The value converted to millimeters (full precision, no rounding).

    Raises:
        ValueError: If the unit is not supported.
    """
    unit = unit.strip().lower()
    if unit not in _TO_FEET_DIVISORS:
        raise ValueError(
            f"Unsupported unit '{unit}'. "
            f"Supported units: {', '.join(SUPPORTED_UNITS)}"
        )
    # Convert to feet then to mm: (value / divisor) * 304.8
    return (value / _TO_FEET_DIVISORS[unit]) * 304.8


def from_feet(value_ft: float, target_unit: str) -> float:
    """Convert a value in feet to the target unit.

    Args:
        value_ft: The value in feet.
        target_unit: One of 'mm', 'cm', 'in', 'ft'.

    Returns:
        The value in the target unit (full precision, no rounding).

    Raises:
        ValueError: If the target unit is not supported.
    """
    target_unit = target_unit.strip().lower()
    if target_unit not in _TO_FEET_DIVISORS:
        raise ValueError(
            f"Unsupported unit '{target_unit}'. "
            f"Supported units: {', '.join(SUPPORTED_UNITS)}"
        )
    return value_ft * _TO_FEET_DIVISORS[target_unit]

