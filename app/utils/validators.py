"""
Input validators for the Laser Estimate application.

Returns user-friendly error messages rather than raising raw exceptions.
Each validator returns (is_valid: bool, error_message: str | None).
"""

from typing import Optional, Tuple


def validate_positive_number(
    value, field_name: str
) -> Tuple[bool, Optional[str]]:
    """Validate that a value is a positive number.

    Returns:
        (True, None) if valid, (False, message) if invalid.
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False, f"Please enter a valid number for {field_name}."

    if num <= 0:
        return False, f"{field_name} must be greater than zero."

    return True, None


def validate_non_negative_number(
    value, field_name: str
) -> Tuple[bool, Optional[str]]:
    """Validate that a value is a non-negative number (zero allowed).

    Returns:
        (True, None) if valid, (False, message) if invalid.
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False, f"Please enter a valid number for {field_name}."

    if num < 0:
        return False, f"{field_name} cannot be negative."

    return True, None


def validate_positive_integer(
    value, field_name: str
) -> Tuple[bool, Optional[str]]:
    """Validate that a value is a positive integer.

    Returns:
        (True, None) if valid, (False, message) if invalid.
    """
    try:
        num = int(value)
    except (TypeError, ValueError):
        return False, f"Please enter a valid whole number for {field_name}."

    if num <= 0:
        return False, f"{field_name} must be greater than zero."

    return True, None


def validate_non_negative_integer(
    value, field_name: str
) -> Tuple[bool, Optional[str]]:
    """Validate that a value is a non-negative integer.

    Returns:
        (True, None) if valid, (False, message) if invalid.
    """
    try:
        num = int(value)
    except (TypeError, ValueError):
        return False, f"Please enter a valid whole number for {field_name}."

    if num < 0:
        return False, f"{field_name} cannot be negative."

    return True, None


def validate_required_text(
    value: str, field_name: str
) -> Tuple[bool, Optional[str]]:
    """Validate that a text field is not empty.

    Returns:
        (True, None) if valid, (False, message) if invalid.
    """
    if not value or not str(value).strip():
        return False, f"{field_name} is required."

    return True, None


def validate_unit(unit: str) -> Tuple[bool, Optional[str]]:
    """Validate that a unit is supported.

    Returns:
        (True, None) if valid, (False, message) if invalid.
    """
    from app.calculations.unit_converter import SUPPORTED_UNITS

    if not unit or unit.strip().lower() not in SUPPORTED_UNITS:
        return False, (
            f"Invalid unit '{unit}'. "
            f"Supported: {', '.join(SUPPORTED_UNITS)}"
        )

    return True, None
