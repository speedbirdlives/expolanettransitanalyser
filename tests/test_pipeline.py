"""Unit tests for transit physics, detrending, and BLS recovery."""

from __future__ import annotations

import numpy as np
import pytest
from astropy import units as u
from lightkurve import LightCurve

from core.bls import run_bls
from core.detrending import clean_and_flatten
from core.physics import estimate_planet_parameters


def test_earth_sized_transit_depth_and_radius() -> None:
    """An Earth-sized planet across a Sun-like star produces about 84 ppm."""
    earth_radius_ratio = 1 / 109.1
    depth = earth_radius_ratio**2
    result = estimate_planet_parameters(depth)
    assert result["transit_depth_ppm"] == pytest.approx(84.0, rel=0.01)
    assert result["planet_radius_earth"] == pytest.approx(1.0, rel=0.01)


def test_keplers_third_law_gives_one_au_for_earth() -> None:
    """A one-year orbit around one solar mass has a one-AU semi-major axis."""
    result = estimate_planet_parameters(0.01, period_days=365.25)
    assert result["semi_major_axis_au"] == pytest.approx(1.0, rel=1e-4)


def test_physics_rejects_nonphysical_depth() -> None:
    with pytest.raises(ValueError, match="transit_depth"):
        estimate_planet_parameters(0)


def test_clean_and_flatten_removes_nan_and_normalizes() -> None:
    time = np.arange(301, dtype=float)
    flux = 1 + 0.001 * np.sin(time / 25)
    flux[20] = np.nan
    lc = LightCurve(time=time * u.day, flux=flux)
    cleaned = clean_and_flatten(lc, window_length=51)
    assert len(cleaned) == len(time) - 1
    assert np.all(np.isfinite(cleaned.flux.value))
    assert np.nanmedian(cleaned.flux.value) == pytest.approx(1.0, abs=0.01)


def test_bls_recovers_injected_square_wave_period() -> None:
    """The BLS search recovers the period of a synthetic box-shaped transit."""
    cadence_days = 0.02
    time = np.arange(0, 30, cadence_days)
    period = 3.0
    phase = ((time - 1.0 + period / 2) % period) - period / 2
    flux = np.ones_like(time)
    flux[np.abs(phase) < 0.08] -= 0.01
    flux += np.random.default_rng(13).normal(0, 0.0005, len(time))
    lc = LightCurve(time=time * u.day, flux=flux)

    _, result = run_bls(lc, period_min=2.5, period_max=3.5, num_periods=2000)
    assert result["period"] == pytest.approx(period, abs=0.03)
    assert result["depth"] == pytest.approx(0.01, abs=0.003)
