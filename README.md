# LunarSight

Lunar South Pole Landing Site Navigator is an offline-first Streamlit prototype for comparing the Sun and Earth above a candidate site's local lunar horizon.

This hackathon MVP uses clearly labelled synthetic data. It is not a flight-dynamics or landing-safety system. Geometric elevation does not account for terrain, link budgets, or operational constraints.

## Quick start

Use Python 3.11 or newer:

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    streamlit run app.py

The demo works without internet access. Run checks with python -m pytest and python -m compileall app.py horizons.py analysis.py tests.

## Data contract

Every ephemeris row has time_utc (ISO 8601 UTC), sun_az, sun_el, earth_az, and earth_el (degrees). Azimuth is in [0, 360), clockwise from local north through east. Elevation is in [-90, 90], relative to the ideal local horizontal plane.

Coordinates in sites.json are lunar geodetic latitude and east-positive longitude in degrees. The Moon is Horizons body 301. All bundled sites are demonstrations, not verified landing coordinates.

## Architecture and status

- app.py: Streamlit UI and offline demo loading.
- horizons.py: validation, JPL Horizons HTTP client, response parser, and Sun/Earth table merger.
- analysis.py: stable interface for Developer 2; algorithms intentionally remain unimplemented.
- sites.json: demonstration catalog.
- data/demo_ephemeris.csv: synthetic 72-hour profile, rebased to the selected date.
- tests/: loading, validation, request, and catalog checks.

The request syntax follows the official [Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html) and [system manual](https://ssd.jpl.nasa.gov/horizons/manual.html): lunar surface observers use CENTER='coord@301', geodetic SITE_COORD ordered east longitude, latitude, height-km, and observer quantity 4 for apparent azimuth/elevation.

The sidebar can switch between offline Demo Data and Live NASA Data. Live mode requests the Sun and Earth sequentially (target IDs 10 and 399), merges them by UTC timestamp, and caches successful results for one hour. If the network or service fails, the UI reports the cause and falls back to demo data. Bundled site coordinates remain synthetic and unverified even when their ephemerides are computed from live Horizons data.
