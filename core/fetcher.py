"""MAST light-curve search and ingestion helpers."""

from __future__ import annotations

from typing import Any

import lightkurve as lk


def fetch_target_lightcurve(
    target_id: str, mission: str = "Kepler", author: str = "Kepler"
) -> Any:
    """Search MAST for a target's light curves, download them, and stitch segments.

    Args:
        target_id: Target name or catalog identifier understood by MAST.
        mission: Mission to search, such as ``"Kepler"`` or ``"TESS"``.
        author: Data-product author to pass to Lightkurve's MAST search.

    Returns:
        A stitched ``LightCurve`` containing all available search results.

    Raises:
        ValueError: If a required identifier is empty.
        RuntimeError: If MAST is unavailable, no products exist, or download fails.
    """
    if not target_id.strip():
        raise ValueError("target_id must not be empty.")
    try:
        search_result = lk.search_lightcurve(
            target_id, mission=mission, author=author
        )
        if len(search_result) == 0:
            raise RuntimeError(
                f"No {mission} light-curve products were found for {target_id!r}."
            )
        collection = search_result.download_all()
        if collection is None or len(collection) == 0:
            raise RuntimeError(
                f"MAST returned no downloadable light curves for {target_id!r}."
            )
        return collection.stitch()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Could not fetch light curves for {target_id!r} from MAST: {exc}"
        ) from exc
