"""Approximate physical parameter estimates from transit observables."""

from __future__ import annotations

import math

import numpy as np
from astropy import constants as const
from astropy import units as u


def estimate_planet_parameters(
    transit_depth: float,
    star_radius_solar: float = 1.0,
    period_days: float = 3.5,
    star_mass_solar: float = 1.0,
) -> dict[str, float]:
    """Estimate planet radius and orbital semi-major axis from a transit.

    The radius estimate assumes a small, opaque planet and a uniform stellar
    disk, so the radius ratio is ``sqrt(transit_depth)``. The orbit is assumed
    circular and the planet mass negligible relative to the host star.

    Args:
        transit_depth: Fractional flux decrement (e.g. ``0.01`` for 1%).
        star_radius_solar: Stellar radius in solar radii.
        period_days: Orbital period in days.
        star_mass_solar: Stellar mass in solar masses.

    Returns:
        Dictionary containing planet radius in Earth radii, semi-major axis in
        AU, and transit depth in parts per million.
    """
    values = (transit_depth, star_radius_solar, period_days, star_mass_solar)
    if not all(np.isfinite(value) for value in values):
        raise ValueError("All inputs must be finite.")
    if not 0 < transit_depth <= 1:
        raise ValueError("transit_depth must be in the interval (0, 1].")
    if star_radius_solar <= 0 or period_days <= 0 or star_mass_solar <= 0:
        raise ValueError("Stellar radius, stellar mass, and period must be positive.")

    planet_radius_earth = (
        star_radius_solar * math.sqrt(transit_depth) * 109.1
    )
    period = period_days * u.day
    mass = star_mass_solar * const.M_sun
    semi_major_axis = (
        const.G * mass * period**2 / (4 * math.pi**2)
    ) ** (1 / 3)
    return {
        "planet_radius_earth": float(planet_radius_earth),
        "semi_major_axis_au": float(semi_major_axis.to_value(u.au)),
        "transit_depth_ppm": float(transit_depth * 1_000_000),
    }
