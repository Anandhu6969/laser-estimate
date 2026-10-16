"""
Number and currency formatters.

Indian comma formatting for currency (e.g. ₹1,23,456).
Whole rupees by default.
"""

import re


def format_indian_currency(amount: float, symbol: str = "₹") -> str:
    """Format a number as Indian currency with comma grouping.

    Indian system: last 3 digits grouped, then groups of 2.
    Examples:
        1000       → ₹1,000
        12345      → ₹12,345
        123456     → ₹1,23,456
        1234567    → ₹12,34,567
        7545.50    → ₹7,546  (rounded to whole)

    Args:
        amount: The numeric amount.
        symbol: Currency symbol (default ₹).

    Returns:
        Formatted currency string with Indian comma grouping.
    """
    # Round to whole rupees
    rounded = round(amount)

    # Handle negative
    negative = rounded < 0
    rounded = abs(rounded)

    # Convert to string
    s = str(rounded)

    # Apply Indian grouping: last 3 digits, then groups of 2
    if len(s) <= 3:
        formatted = s
    else:
        last_three = s[-3:]
        remaining = s[:-3]
        # Group remaining digits in pairs from the right
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted = ",".join(groups) + "," + last_three

    prefix = "-" if negative else ""
    return f"{prefix}{symbol}{formatted}"


def format_number(value: float, decimals: int = 2) -> str:
    """Format a number to a fixed number of decimal places.

    Args:
        value: The numeric value.
        decimals: Number of decimal places (default 2).

    Returns:
        Formatted string.
    """
    return f"{value:.{decimals}f}"


def format_area(area_sqft: float) -> str:
    """Format an area value for display.

    Args:
        area_sqft: Area in square feet.

    Returns:
        Formatted string like '10.33 sq.ft'.
    """
    return f"{area_sqft:.2f} sq.ft"


def format_dimensions_ft(length_ft: float, width_ft: float) -> str:
    """Format converted dimensions for display.

    Args:
        length_ft: Length in feet.
        width_ft: Width in feet.

    Returns:
        Formatted string like '3.94 ft × 2.63 ft'.
    """
    return f"{length_ft:.2f} ft × {width_ft:.2f} ft"


def format_weight(weight_kg: float) -> str:
    """Format weight for display.

    Args:
        weight_kg: Weight in kilograms.

    Returns:
        Formatted string like '25 kg' or '25.5 kg'.
    """
    if weight_kg == int(weight_kg):
        return f"{int(weight_kg)} kg"
    return f"{weight_kg:.2f} kg"


def format_time(total_minutes: float) -> str:
    """Format cutting time for display.

    Args:
        total_minutes: Total minutes.

    Returns:
        Formatted string like '30 minutes' or '1 hr 20 min'.
    """
    total = int(total_minutes)
    if total < 60:
        return f"{total} minutes"
    hours = total // 60
    mins = total % 60
    if mins == 0:
        return f"{hours} hr"
    return f"{hours} hr {mins} min"
