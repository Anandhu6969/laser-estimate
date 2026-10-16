"""
Cutting cost calculator.

Computes cutting amount from time and configurable rate.
Rate is always passed in — never hardcoded.
"""


def time_to_minutes(hours: int = 0, minutes: int = 0) -> float:
    """Convert hours + minutes to total minutes.

    Args:
        hours: Number of hours (>= 0).
        minutes: Number of minutes (>= 0).

    Returns:
        Total minutes as a float.

    Raises:
        ValueError: If hours or minutes is negative.
    """
    if hours < 0:
        raise ValueError("Hours cannot be negative.")
    if minutes < 0:
        raise ValueError("Minutes cannot be negative.")
    return float(hours * 60 + minutes)


def time_to_hours(hours: int = 0, minutes: int = 0) -> float:
    """Convert hours + minutes to total hours.

    Args:
        hours: Number of hours (>= 0).
        minutes: Number of minutes (>= 0).

    Returns:
        Total hours as a float.

    Raises:
        ValueError: If hours or minutes is negative.
    """
    if hours < 0:
        raise ValueError("Hours cannot be negative.")
    if minutes < 0:
        raise ValueError("Minutes cannot be negative.")
    return float(hours + minutes / 60.0)


def calculate_cutting_cost(total_minutes: float, cutting_rate: float) -> float:
    """Calculate the cutting cost.

    Args:
        total_minutes: Total cutting time in minutes.
        cutting_rate: Price per minute (configurable, from settings or override).

    Returns:
        Cutting amount (total_minutes × cutting_rate).

    Raises:
        ValueError: If total_minutes or cutting_rate is negative.
    """
    if total_minutes < 0:
        raise ValueError("Cutting time cannot be negative.")
    if cutting_rate < 0:
        raise ValueError("Cutting rate cannot be negative.")

    return total_minutes * cutting_rate


def calculate_cutting_cost_hourly(total_hours: float, rate_per_hour: float) -> float:
    """Calculate cutting cost from total hours and hourly cutting rate.

    Args:
        total_hours: Total cutting time in hours.
        rate_per_hour: Price per hour (₹/hour).

    Returns:
        Cutting amount (total_hours × rate_per_hour).

    Raises:
        ValueError: If total_hours or rate_per_hour is negative.
    """
    if total_hours < 0:
        raise ValueError("Cutting time cannot be negative.")
    if rate_per_hour < 0:
        raise ValueError("Cutting rate cannot be negative.")

    return total_hours * rate_per_hour

