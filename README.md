# Exo Transit Analyzer

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest%20suite-brightgreen.svg)](tests/)

An interactive research-oriented dashboard for retrieving mission photometry,
cleaning light curves, detecting periodic transit candidates, and estimating
basic planet properties. It is built with Python, Lightkurve, NumPy, Astropy,
Plotly, and Streamlit.

## Problem statement

When a planet crosses in front of its host star, it blocks a small fraction of
the stellar flux. Repeating dips in a time-series light curve can reveal an
orbital period and an approximate planet-to-star radius ratio. This tool
retrieves Kepler, K2, or TESS light curves from MAST and provides an interactive
workflow for inspecting candidate signals. The output is an exploratory
estimate, not a validated planet detection or a substitute for a full
astrophysical model.

## Architecture

```text
app.py                 Streamlit dashboard and plots
core/fetcher.py        MAST search, download, and stitching
core/detrending.py     Quality filtering, normalization, and flattening
core/bls.py            Box Least Squares search and phase folding
core/physics.py        Approximate radius and orbital estimates
tests/test_pipeline.py Physics, detrending, and synthetic BLS tests
```

## Mathematical formulation

For a small planet transiting a uniformly bright stellar disk, the fractional
transit depth is approximately the squared radius ratio:

$$
\delta = \frac{F_{\mathrm{out}}-F_{\mathrm{in}}}{F_{\mathrm{out}}}
       \approx \left(\frac{R_p}{R_*}\right)^2,
\qquad
\frac{R_p}{R_*} \approx \sqrt{\delta}.
$$

The flux ratio during transit is $F_{\mathrm{in}}/F_{\mathrm{out}} \approx
1-\delta$. The estimated planet radius is therefore

$$
R_p \approx R_* \sqrt{\delta}
    = 109.1\,R_\oplus\left(\frac{R_*}{R_\odot}\right)\sqrt{\delta}.
$$

The transit depth in parts per million is $\delta_{\rm ppm}=10^6\delta$.
Assuming a circular orbit and a planet much less massive than its host, Kepler's
third law gives the semi-major axis:

$$
a = \left(\frac{G M_* P^2}{4\pi^2}\right)^{1/3}.
$$

The analysis does not model limb darkening, impact parameter, eccentricity,
stellar variability physics, or dilution. Those effects can bias these simple
estimates.

## Setup and installation

Python 3.10 or newer is required.

```bash
git clone https://github.com/<your-account>/exo-transit-analyzer.git
cd exo-transit-analyzer
python -m venv venv
```

Activate the environment:

```bash
# macOS/Linux
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

Install dependencies, run the tests, and launch the app:

```bash
python -m pip install -r requirements.txt
pytest
streamlit run app.py
```

The first analysis for a target downloads products from the Mikulski Archive
for Space Telescopes (MAST), so an internet connection is required.

## Example analysis: Kepler-10b

1. Select **Kepler-10**, keep the mission set to **Kepler**, and click
   **Analyze target**.
2. Inspect the raw and flattened data to check that long-term variability has
   been removed without erasing the transit signal.
3. Review the BLS periodogram peak and adjust the period bounds if needed.
4. Inspect the phase-folded transit and its binned points. Set stellar radius
   and mass from a trusted stellar catalog for improved estimates.

For a representative Kepler-10-like transit depth of roughly 150 ppm and a
period near 0.84 days, a solar-radius input gives an approximate planet radius
of 1.34 Earth radii. This is a walkthrough value, not a guaranteed live result:
the returned candidate depends on the available MAST products, detrending
choices, and period search bounds. Replace the default stellar parameters with
literature values before interpreting physical estimates.

## Limitations and scientific use

The BLS module searches the supplied period grid and reports its highest-power
candidate; harmonics and instrumental/systematic signals may also produce
peaks. Flattening and outlier rejection settings can affect measured transit
depths. Confirm candidates with independent data and a more complete transit
model before making scientific claims.

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
