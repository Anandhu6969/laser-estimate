# -*- coding: utf-8 -*-
"""
Estimate calculator.

Computes the final estimate total from component amounts.
Supports an optional quantity multiplier for identical pieces.
"""


def calculate_simple_estimate(
    area_sqft: float,
    rate_per_sqft: float,
    quantity: int = 1,
) -> dict:
    """Calculate the estimate for Simple Cutting mode.

    Formula:
        per_piece_amount = area_sqft * rate_per_sqft
        final_amount = per_piece_amount * quantity

    Args:
        area_sqft: Part area in square feet.
        rate_per_sqft: Configured or custom price per sq.ft.
        quantity: Number of identical pieces (default 1).

    Returns:
        dict with keys:
            per_piece_amount: Total for a single piece.
            quantity: Number of pieces.
            final_amount: per_piece_amount * quantity.

    Raises:
        ValueError: If area or rate is negative or quantity < 1.
    """
    if area_sqft < 0:
        raise ValueError("Area cannot be negative.")
    if rate_per_sqft < 0:
        raise ValueError("Rate per sq.ft cannot be negative.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    per_piece = area_sqft * rate_per_sqft
    final = per_piece * quantity

    return {
        "per_piece_amount": per_piece,
        "quantity": quantity,
        "final_amount": final,
    }


def calculate_design_heavy_estimate(
    material_amount: float = 0.0,
    cutting_amount: float = 0.0,
    design_amount: float = 0.0,
    quantity: int = 1,
    weight_kg: float = None,
    kilo_rate: float = None,
    cutting_time_hours: float = None,
    cutting_rate_per_hour: float = None,
) -> dict:
    """Calculate the estimate for Design Heavy mode.

    Formula:
        material_amount = weight_kg * kilo_rate (or provided directly)
        cutting_amount = cutting_time_hours * cutting_rate_per_hour (or provided directly)
        per_piece_amount = material_amount + cutting_amount + design_amount
        final_amount = per_piece_amount * quantity
    """
    if weight_kg is not None and kilo_rate is not None:
        if weight_kg < 0:
            raise ValueError("Weight cannot be negative.")
        if kilo_rate < 0:
            raise ValueError("Kilo rate cannot be negative.")
        material_amount = weight_kg * kilo_rate
    elif material_amount < 0:
        raise ValueError("Material amount cannot be negative.")

    if cutting_time_hours is not None and cutting_rate_per_hour is not None:
        if cutting_time_hours < 0:
            raise ValueError("Cutting time cannot be negative.")
        if cutting_rate_per_hour < 0:
            raise ValueError("Cutting rate cannot be negative.")
        cutting_amount = cutting_time_hours * cutting_rate_per_hour
    elif cutting_amount < 0:
        raise ValueError("Cutting amount cannot be negative.")

    return calculate_estimate(
        material_amount=material_amount,
        cutting_amount=cutting_amount,
        design_amount=design_amount,
        quantity=quantity,
    )


def calculate_estimate(
    material_amount: float,
    cutting_amount: float,
    design_amount: float = 0.0,
    quantity: int = 1,
) -> dict:
    """Calculate the final estimate.

    Args:
        material_amount: Cost from sheet weight * kilo rate.
        cutting_amount: Cost from cutting time * cutting rate.
        design_amount: Cost from hole/design charges (default 0).
        quantity: Number of identical pieces (default 1).

    Returns:
        dict with keys:
            per_piece_amount: Total for a single piece.
            quantity: Number of pieces.
            final_amount: per_piece_amount * quantity.

    Raises:
        ValueError: If any amount is negative or quantity < 1.
    """
    if material_amount < 0:
        raise ValueError("Material amount cannot be negative.")
    if cutting_amount < 0:
        raise ValueError("Cutting amount cannot be negative.")
    if design_amount < 0:
        raise ValueError("Design amount cannot be negative.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    per_piece = material_amount + cutting_amount + design_amount
    final = per_piece * quantity

    return {
        "material_amount": material_amount,
        "cutting_amount": cutting_amount,
        "design_amount": design_amount,
        "per_piece_amount": per_piece,
        "quantity": quantity,
        "final_amount": final,
    }



