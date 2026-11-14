# LunarSight

**Lunar South Pole Landing Site Navigator**

LunarSight is an interactive Streamlit application for comparing the apparent
positions of the Sun and Earth above candidate locations near the lunar south
pole. It combines NASA JPL Horizons observer ephemerides with an offline
demonstration mode for reliable hackathon presentations.

LunarSight is a NASA Space Apps-style educational prototype. It is not
affiliated with or endorsed by NASA and is not a flight-certified mission
planning or landing-safety system.

## Scientific problem

Long-duration operations near the lunar south pole depend on when the Sun and
Earth are geometrically visible from a surface location. LunarSight helps a
mission-planning team inspect that geometry over a shared UTC interval and
compare candidate coordinates without presenting an arbitrary suitability
score.

## Main features

- Live Sun and Earth azimuth/elevation from NASA JPL Horizons.
- Clearly labelled synthetic demo mode that works without a network.
- Landing-site, UTC start-date, and 24/48/72-hour mission configuration.
- Interactive Plotly elevation and direction visualizations.
- Matched-period comparison of two lunar surface observers.
- UTC-preserving CSV export of the exact displayed ephemeris table.
- Graceful API-error handling and one-hour caching of successful live results.
- Responsive dark mission-control dashboard.

## Technology

- Python 3.12 (Python 3.11+ is supported locally)
- Streamlit
- pandas
- Plotly
- Requests
- NASA JPL Horizons API

## Run locally on Windows

From PowerShell in the cloned repository:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If the `py` launcher is unavailable, replace `py -3.12` with `python`.
Activation is optional because the commands use the virtual-environment Python
directly. Streamlit normally opens `http://localhost:8501`.

Run the automated checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py comparison.py horizons.py ephemeris_export.py tests
```

## Streamlit Community Cloud deployment

The production entry point is `app.py`. The deployment requires no secrets,
database, Docker image, or operating-system packages.

1. Push an approved stable branch to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select **Create app** and **Yup, I have an app**.
4. Choose repository `alex-tereshkovv/lunarsight`.
5. Choose the approved deployment branch.
6. Set the main file path to `app.py`.
7. In **Advanced settings**, select Python `3.12`.
8. Leave the secrets field empty and deploy.

Community Cloud reads `requirements.txt` and `.streamlit/config.toml` from the
repository root. Static visual assets are committed under `static/assets/` and
served through Streamlit's static-file handler. Pushing a new commit to the
configured stable branch triggers Streamlit Community Cloud's normal app
update process.

## Five-minute demonstration workflow

1. Open **Mission Control** in `Demo (Synthetic)` mode to show the dashboard,
   observation-time control, data table, and CSV export without relying on the
   network.
2. Point out the synthetic source label and `SYNTHETIC_DEMO` filename marker.
3. Switch to `Live NASA (Horizons)` and run one configured observation period.
4. Open **Site Comparison**, select two locations, and compare the same UTC
   interval for both observers.
5. Open **Data & Sources** and **About** to explain provenance and limitations.

If Horizons is unavailable, Mission Control reports the error and changes to a
clearly labelled `Demo (Fallback)` dataset. Site Comparison never mixes live
NASA data for one site with synthetic data for the other.

## Data contract and coordinate convention

Each validated ephemeris row has this schema:

```text
time_utc,sun_az,sun_el,earth_az,earth_el
```

- `time_utc`: timezone-aware ISO 8601 UTC timestamp.
- `sun_az`, `earth_az`: degrees in `[0, 360)`, clockwise from local north
  through east.
- `sun_el`, `earth_el`: degrees in `[-90, 90]`, relative to the ideal local
  horizontal plane.
- Site coordinates: lunar geodetic latitude and east-positive longitude.

The lunar surface observer is `coord@301`. Live requests use target ID `10`
for the Sun, target ID `399` for Earth, observer quantity `4`, one-hour steps,
UTC, and the airless apparent-elevation model. Successful results are cached
for one hour with a bounded cache size.

The API request syntax follows the official
[NASA JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
and [Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html).

## Scientific limitations

LunarSight reports geometric target-center visibility relative to an ideal
zero-degree local horizon:

- Local lunar topography, crater walls, ridges, and terrain shadowing are not
  modeled. Positive Sun elevation is not proof of surface illumination.
- Positive Earth elevation is not proof of a reliable communication link.
  Antenna patterns, margins, relay geometry, and link budgets are not modeled.
- Elevation describes the center of the Sun or Earth, not its full disk.
- Landing hazards, slopes, thermal conditions, navigation uncertainty, and
  operational safety margins are outside the current model.
- Catalog coordinates are explicitly demonstration locations and are not
  verified landing sites.
- Pending mission metrics remain placeholders until `analysis.py` is
  implemented and scientifically reviewed.

## Project structure

- `app.py` — Streamlit navigation, source orchestration, and presentation.
- `horizons.py` — Horizons request construction, parsing, and validation.
- `comparison.py` — aligned site-comparison helpers and charts.
- `ephemeris_export.py` — UTC-safe CSV serialization and filenames.
- `analysis.py` — reserved interface for mission-analysis algorithms.
- `sites.json` — demonstration landing-site catalog.
- `data/demo_ephemeris.csv` — bundled offline synthetic data.
- `static/assets/` — decorative dashboard image assets.
- `.streamlit/config.toml` — theme and static-serving configuration.
- `tests/` — offline unit and Streamlit regression tests.

## Team contributions

- **Developer 1:** architecture, Horizons integration, Streamlit application,
  deployment, and integration.
- **Developer 2:** mission-analysis calculations and visibility windows.
- **Developer 3:** landing-site research, scientific documentation,
  validation, and presentation.

Contributions should be developed in focused branches and reviewed before
being promoted to the stable deployment branch.
