"""Light-curve quality filtering, normalization, and flattening."""

from __future__ import annotations

from typing import Any


def clean_and_flatten(
    lc: Any,
    window_length: int = 101,
    polyorder: int = 2,
    sigma: float = 5.0,
) -> Any:
    """Remove invalid cadences and trends while preserving transit signals.

    Args:
        lc: Lightkurve-compatible light curve.
        window_length: Savitzky-Golay filter window in cadences. It is adjusted
            downward when necessary to fit the available data.
        polyorder: Polynomial order used by the flattening filter.
        sigma: Symmetric sigma threshold for outlier rejection.

    Returns:
        A normalized, outlier-cleaned, flattened light curve.

    Raises:
        ValueError: If filter settings are invalid or too little data remains.
    """
    if window_length < 3 or polyorder < 0 or sigma <= 0:
        raise ValueError("window_length must be >= 3, polyorder >= 0, and sigma > 0.")
    if window_length <= polyorder:
        raise ValueError("window_length must be greater than polyorder.")

    cleaned = lc.remove_nans()
    quality = getattr(cleaned, "quality", None)
    if quality is not None:
        try:
            cleaned = cleaned[quality == 0]
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError(f"Could not filter bad-quality cadences: {exc}") from exc
    if len(cleaned) < 3:
        raise ValueError("At least three valid cadences are required.")

    normalized = cleaned.normalize()
    normalized = normalized.remove_outliers(sigma=sigma)
    if len(normalized) < 3:
        raise ValueError("At least three cadences must remain after outlier rejection.")

    effective_window = min(window_length, len(normalized))
    if effective_window % 2 == 0:
        effective_window -= 1
    minimum_window = polyorder + 2
    if minimum_window % 2 == 0:
        minimum_window += 1
    if effective_window < minimum_window:
        raise ValueError(
            "Too few cadences remain for the requested flattening polynomial order."
        )
    return normalized.flatten(
        window_length=effective_window, polyorder=polyorder
    )
