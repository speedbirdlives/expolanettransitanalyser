"""Box Least Squares period search and phase-folding helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
from astropy import units as u
from astropy.time import Time


def _scalar(value: Any, unit: Any | None = None) -> float:
    """Convert an Astropy quantity or scalar to a Python float."""
    if isinstance(value, Time):
        return float(value.value)
    if hasattr(value, "to_value") and unit is not None:
        return float(value.to_value(unit))
    if hasattr(value, "value"):
        value = value.value
    return float(np.asarray(value))


def run_bls(
    flat_lc: Any,
    period_min: float = 0.5,
    period_max: float = 20.0,
    num_periods: int = 10000,
) -> tuple[Any, dict[str, float]]:
    """Run a Box Least Squares search over a linear period grid.

    Args:
        flat_lc: Detrended Lightkurve-compatible light curve.
        period_min: Lower period search bound in days.
        period_max: Upper period search bound in days.
        num_periods: Number of trial periods in the search grid.

    Returns:
        The BLS periodogram and a mapping with ``period``, ``epoch``,
        ``duration``, and fractional ``depth``.
    """
    if not np.isfinite(period_min) or not np.isfinite(period_max) or period_min <= 0:
        raise ValueError("Period bounds must be finite and positive.")
    if period_max <= period_min:
        raise ValueError("period_max must be greater than period_min.")
    if num_periods < 2:
        raise ValueError("num_periods must be at least 2.")

    periods = np.linspace(period_min, period_max, num_periods)
    duration_max = min(0.3, period_min * 0.2)
    duration_min = min(0.02, duration_max / 2)
    durations = np.linspace(duration_min, duration_max, 10)
    periodogram = flat_lc.to_periodogram(
        method="bls", period=periods, duration=durations
    )
    best_fit = {
        "period": _scalar(periodogram.period_at_max_power, u.day),
        "epoch": _scalar(periodogram.transit_time_at_max_power, u.day),
        "duration": _scalar(periodogram.duration_at_max_power, u.day),
        "depth": _scalar(periodogram.depth_at_max_power),
    }
    return periodogram, best_fit


def phase_fold(flat_lc: Any, period: float, epoch: float) -> Any:
    """Fold a light curve on a period and bin the result into five-minute bins.

    Args:
        flat_lc: Detrended Lightkurve-compatible light curve.
        period: Orbital period in days.
        epoch: Transit midpoint in the light curve's time system, in days.

    Returns:
        A five-minute-binned folded light curve.
    """
    if not np.isfinite(period) or period <= 0 or not np.isfinite(epoch):
        raise ValueError("period must be positive and epoch must be finite.")
    folded = flat_lc.fold(period=period * u.day, epoch_time=epoch)
    return folded.bin(time_bin_size=5 * u.minute)
