"""Streamlit dashboard for exoplanet transit light-curve analysis."""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

from core.bls import phase_fold, run_bls
from core.detrending import clean_and_flatten
from core.fetcher import fetch_target_lightcurve
from core.physics import estimate_planet_parameters


PRESET_TARGETS = {
    "Kepler-10": "Kepler-10",
    "Kepler-8b": "Kepler-8",
    "WASP-12": "WASP-12",
    "TOI-700": "TOI-700",
}

st.set_page_config(page_title="Exo Transit Analyzer", page_icon="🪐", layout="wide")
st.title("Exoplanet Transit Analyzer")
st.caption(
    "Explore mission light curves, search for periodic transits, and estimate "
    "candidate properties."
)

with st.sidebar:
    st.header("Analysis settings")
    selected_target = st.selectbox("Preset target", ["Custom", *PRESET_TARGETS])
    target_id = (
        st.text_input("Target identifier", value="")
        if selected_target == "Custom"
        else PRESET_TARGETS[selected_target]
    )
    mission = st.selectbox("Mission", ["Kepler", "TESS", "K2"], index=0)
    author = st.text_input("Data author", value=mission)
    st.subheader("Detrending and period search")
    window_length = st.slider("Flattening window (cadences)", 11, 1001, 101, step=2)
    sigma = st.slider("Outlier sigma threshold", 2.0, 10.0, 5.0, step=0.5)
    period_min = st.number_input(
        "Minimum period (days)", min_value=0.05, value=0.5, step=0.1
    )
    period_max = st.number_input(
        "Maximum period (days)", min_value=0.1, value=20.0, step=0.5
    )
    st.subheader("Stellar parameters")
    star_radius = st.number_input(
        "Stellar radius (R☉)", min_value=0.01, value=1.0, step=0.1
    )
    star_mass = st.number_input(
        "Stellar mass (M☉)", min_value=0.01, value=1.0, step=0.1
    )
    analyze = st.button(
        "Analyze target", type="primary", disabled=not target_id.strip()
    )

if analyze:
    if period_max <= period_min:
        st.error("Maximum period must be greater than minimum period.")
    else:
        try:
            with st.spinner(f"Fetching and analyzing {target_id}..."):
                raw_lc = fetch_target_lightcurve(
                    target_id.strip(), mission=mission, author=author
                )
                flat_lc = clean_and_flatten(
                    raw_lc, window_length=window_length, sigma=sigma
                )
                periodogram, best_fit = run_bls(
                    flat_lc, period_min=period_min, period_max=period_max
                )
                folded_lc = phase_fold(
                    flat_lc, best_fit["period"], best_fit["epoch"]
                )
                estimates = estimate_planet_parameters(
                    best_fit["depth"],
                    star_radius_solar=star_radius,
                    period_days=best_fit["period"],
                    star_mass_solar=star_mass,
                )
        except (ValueError, RuntimeError, OSError) as exc:
            st.error(f"Analysis could not be completed: {exc}")
        else:
            metric_columns = st.columns(4)
            metric_columns[0].metric("Detected period", f"{best_fit['period']:.5f} d")
            metric_columns[1].metric(
                "Transit depth", f"{estimates['transit_depth_ppm']:.1f} ppm"
            )
            metric_columns[2].metric(
                "Estimated radius",
                f"{estimates['planet_radius_earth']:.2f} R⊕",
            )
            metric_columns[3].metric(
                "Semi-major axis", f"{estimates['semi_major_axis_au']:.4f} AU"
            )

            raw_tab, bls_tab, transit_tab = st.tabs(
                ["Raw vs. flattened", "BLS periodogram", "Phase-folded transit"]
            )
            with raw_tab:
                figure = go.Figure()
                figure.add_trace(
                    go.Scatter(
                        x=raw_lc.time.value,
                        y=raw_lc.flux.value,
                        mode="markers",
                        name="Raw",
                        marker={"size": 3, "opacity": 0.45},
                    )
                )
                figure.add_trace(
                    go.Scatter(
                        x=flat_lc.time.value,
                        y=flat_lc.flux.value,
                        mode="markers",
                        name="Flattened",
                        marker={"size": 3},
                    )
                )
                figure.update_layout(
                    xaxis_title="Time (BJD)", yaxis_title="Normalized flux"
                )
                st.plotly_chart(figure, use_container_width=True)

            with bls_tab:
                figure = go.Figure()
                figure.add_trace(
                    go.Scatter(
                        x=periodogram.period.value,
                        y=periodogram.power.value,
                        mode="lines",
                        name="BLS power",
                    )
                )
                figure.add_vline(
                    x=best_fit["period"], line_dash="dash", line_color="red",
                    annotation_text=f"Best period: {best_fit['period']:.5f} d",
                )
                figure.update_layout(
                    xaxis_title="Period (days)", yaxis_title="BLS power"
                )
                st.plotly_chart(figure, use_container_width=True)

            with transit_tab:
                phase = folded_lc.time.value
                flux = folded_lc.flux.value
                figure = go.Figure()
                figure.add_trace(
                    go.Scatter(
                        x=phase,
                        y=flux,
                        mode="markers",
                        name="Folded data",
                        marker={"size": 3, "opacity": 0.3},
                    )
                )
                binned = folded_lc.bin(time_bin_size=5 / (24 * 60))
                figure.add_trace(
                    go.Scatter(
                        x=binned.time.value,
                        y=binned.flux.value,
                        mode="markers",
                        name="5-minute bins",
                        marker={"size": 7, "color": "orange"},
                    )
                )
                duration_days = best_fit["duration"]
                model_x = [
                    -best_fit["period"] / 2,
                    -duration_days / 2,
                    -duration_days / 2,
                    duration_days / 2,
                    duration_days / 2,
                    best_fit["period"] / 2,
                ]
                model_y = [
                    1.0,
                    1.0,
                    1.0 - best_fit["depth"],
                    1.0 - best_fit["depth"],
                    1.0,
                    1.0,
                ]
                figure.add_trace(
                    go.Scatter(
                        x=model_x,
                        y=model_y,
                        mode="lines",
                        name="Box transit model",
                    )
                )
                figure.update_layout(
                    xaxis_title="Time from transit (days)",
                    yaxis_title="Normalized flux",
                )
                st.plotly_chart(figure, use_container_width=True)
            st.caption(
                f"Transit midpoint: {best_fit['epoch']:.5f} BJD · "
                f"Duration: {best_fit['duration'] * 24:.2f} hours"
            )
else:
    st.info("Choose a target and click **Analyze target** to begin.")
