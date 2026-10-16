"""
Sheet / material cost calculator.

Computes material amount from sheet weight and kilo rate.
Rate is always passed in — never hardcoded.
"""


STANDARD_MATERIALS = [
    "Mild Steel",
    "SS 202",
    "Stainless Steel",
    "C45",
    "Japan Sheet",
    "GI",
    "Aluminium",
    "Brass",
    "Copper",
]

STANDARD_MATERIAL_DENSITIES = {
    "Mild Steel": 7.85,
    "SS 202": 7.80,
    "Stainless Steel": 8.00,
    "C45": 7.85,
    "Japan Sheet": 7.85,
    "GI": 7.85,
    "Aluminium": 2.70,
    "Brass": 8.50,
    "Copper": 8.96,
}

DEFAULT_DENSITY = 7.85


def get_material_density(material_name: str) -> float:
    """Look up default density (kg/L) for a given material name.

    Case-insensitive search. Defaults to 7.85 (Mild Steel) if unknown.
    """
    if not material_name:
        return DEFAULT_DENSITY

    mat_clean = material_name.strip().lower()
    for name, density in STANDARD_MATERIAL_DENSITIES.items():
        if name.lower() in mat_clean or mat_clean in name.lower():
            return density

    return DEFAULT_DENSITY


def calculate_part_weight(
    length_mm: float,
    width_mm: float,
    thickness_mm: float,
    density_kg_per_l: float = DEFAULT_DENSITY,
) -> float:
    """Calculate physical weight of a part in kg using customer dimensions in mm.

    Args:
        length_mm: Part length in millimeters.
        width_mm: Part width in millimeters.
        thickness_mm: Part thickness in millimeters.
        density_kg_per_l: Material density in kg/L (g/cm3). Default 7.85 for Mild Steel.

    Returns:
        Part weight in kilograms.

    Raises:
        ValueError: If any dimension or density is <= 0.
    """
    if length_mm <= 0:
        raise ValueError("Length must be greater than zero.")
    if width_mm <= 0:
        raise ValueError("Width must be greater than zero.")
    if thickness_mm <= 0:
        raise ValueError("Thickness must be greater than zero.")
    if density_kg_per_l <= 0:
        raise ValueError("Material density must be greater than zero.")

    return length_mm * width_mm * thickness_mm * density_kg_per_l * 1e-6


def calculate_sheet_weight(
    thickness_mm: float,
    width_mm: float,
    length_mm: float,
    density_kg_per_l: float = DEFAULT_DENSITY,
) -> float:
    """Calculate physical weight of a stock sheet in kg.

    Args:
        thickness_mm: Sheet thickness in millimeters.
        width_mm: Sheet width in millimeters.
        length_mm: Sheet length in millimeters.
        density_kg_per_l: Material density in kg/L (g/cm3). Default 7.85 for Mild Steel.

    Returns:
        Sheet weight in kilograms.

    Raises:
        ValueError: If any dimension or density is <= 0.
    """
    if thickness_mm <= 0:
        raise ValueError("Thickness must be greater than zero.")
    if width_mm <= 0:
        raise ValueError("Sheet width must be greater than zero.")
    if length_mm <= 0:
        raise ValueError("Sheet length must be greater than zero.")
    if density_kg_per_l <= 0:
        raise ValueError("Material density must be greater than zero.")

    # Formula: volume_cm3 = (thickness_mm/10) * (width_mm/10) * (length_mm/10)
    # weight_kg = volume_cm3 * (density_g_per_cm3 / 1000)
    # = thickness_mm * width_mm * length_mm * density_kg_per_l * 1e-6
    return thickness_mm * width_mm * length_mm * density_kg_per_l * 1e-6



def calculate_material_cost(sheet_weight: float, kilo_rate: float) -> float:
    """Calculate the material cost.

    Args:
        sheet_weight: Weight of the sheet in kg.
        kilo_rate: Price per kg (configurable, from settings or override).

    Returns:
        Material amount (sheet_weight × kilo_rate).

    Raises:
        ValueError: If sheet_weight or kilo_rate is negative.
    """
    if sheet_weight < 0:
        raise ValueError("Sheet weight cannot be negative.")
    if kilo_rate < 0:
        raise ValueError("Kilo rate cannot be negative.")

    return sheet_weight * kilo_rate

