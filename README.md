# LunarSight

## [OPEN LUNARSIGHT — LIVE DEMO](https://lunarsight.streamlit.app/)

**Lunar South Pole Landing Site Navigator**

LunarSight is an interactive Streamlit application for comparing the apparent
positions of the Sun and Earth above candidate locations near the lunar south
pole. It combines NASA JPL Horizons observer ephemerides with an offline,
explicitly synthetic reference profile for reliable hackathon presentations.

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
- Clearly labelled synthetic reference profile that works without a network.
- Landing-site, UTC start-date, and 24/48/72-hour mission configuration.
- Interactive Plotly elevation and direction visualizations.
- Matched-period comparison of two lunar surface observers.
- Synchronized Solar Rover Planner with seven published NASA representative-
  traverse stations, UTC scrubbing, loop playback, and separate Visibility
  Optimization and conceptual Continuous Exploration modes.
- Georeferenced terrain hillshade preprocessed from NASA PGDA Site01/Site04
  LOLA 5 m/pixel DEMs in lunar south-polar stereographic metres.
- Explicitly manifested offline NASA cache for the seven rover stations over
  2026-11-14 through 2026-11-21 UTC; never substituted for another period.
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

1. Open **Mission Control** with `Reference Profile (Synthetic)` to show the dashboard,
   observation-time control, data table, and CSV export without relying on the
   network.
2. Point out the synthetic source label and `SYNTHETIC_DEMO` filename marker.
3. Switch to `Live NASA (Horizons)` and run one configured observation period.
4. Open **Site Comparison**, select two locations, and compare the same UTC
   interval for both observers.
5. Open **Solar Rover Planner**. The default fixed-period dataset is a real,
   locally cached NASA Horizons result. In **Visibility Optimization**, press
   Play and scrub the scientific timeline to confirm that the rover, chart,
   UTC cursor, and status panel stay synchronized. Then select **Continuous
   Exploration** to demonstrate a clearly labelled conceptual closed route and
   loop playback. The optional live mode makes separate Sun and Earth requests
   for each of seven verified stations.
6. Open **Data & Sources** and **About** to explain provenance and limitations.

If Horizons is unavailable, Mission Control reports the error and changes to a
clearly labelled `Reference Profile (Synthetic Fallback)` dataset. Site Comparison never mixes live
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

## Solar Rover Planner data provenance

The planner uses the following east-positive station coordinates from NASA's
[Lunar Surface Data Book, M2M-30044 (2025)](https://ntrs.nasa.gov/api/citations/20250002845/downloads/M2M-30044%20Lunar%20Surface%20Data%20Book%20Baseline_Final.pdf):

| Station | Latitude | Longitude |
| --- | ---: | ---: |
| CR1 | -89.468° | 222.6° E |
| CR2 | -89.500° | 222.1° E |
| CR3 | -89.418° | 221.3° E |
| SR1 | -89.685° | 196.7° E |
| SR2 | -89.740° | 201.2° E |
| SR3 | -89.808° | 205.9° E |
| PSR1 | -89.575° | 196.7° E |

The terrain backdrop is a display hillshade built offline from NASA PGDA
[Site01 Connecting Ridge and Site04 Shackleton Rim LOLA products](https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/).
The source GeoTIFFs are 5 m/pixel, use south-polar stereographic X/Y metres,
and reference `MOON_ME`/DE421. The committed crop, projection parameters,
processing note, and source URLs are recorded in
`data/rover_map_manifest.json`. The scale bar and station positions are derived
from that projected coordinate system. The hillshade uses a fixed display
light direction and is not a timestamp-specific sunlight or shadow simulation.

The main map is the georeferenced Site01/Site04 route crop. The current
[IAU/USGS control-network centre for Shackleton](https://planetarynames.wr.usgs.gov/Feature/5450)
is `89.67° S, 129.78° E`, just outside that crop, so LunarSight does not attach
the crater name to an unrelated dark feature. Instead, the compact inset uses
NASA's separate-scale
[multi-temporal south-pole overview](https://science.nasa.gov/resource/illumination-map-of-the-moons-south-pole/)
with Shackleton at its published centre. The inset is context only, not the
route-map scale and not timestamp-specific sunlight.

Visibility Optimization uses the real station ephemerides to make conservative
geometric visibility decisions. Continuous Exploration is a conceptual
closed walk along explicit graph links and does not claim optimality. Because
the NASA traverse polylines have not been digitized into LunarSight, all drawn
links remain straight conceptual connectors between published stations. Their
display length is not a published NASA traverse length, a terrain-safe path, or
verified traversability.

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
- Catalog coordinates are NASA-published representative traverse stations from
  M2M-30044 (2025), not validated landing sites or terrain-safe route points.
- Solar Rover Planner station coordinates are published NASA representative-
  traverse locations. The dashed connector is conceptual and is not the NASA
  route polyline or a terrain/traversability product.
- Continuous Exploration selects a closed conceptual station walk that fits the
  selected mission period. Its repeated playback is an interface visualization,
  not a visibility optimum or an autonomous-navigation result.
- The LOLA-derived background is a terrain hillshade, not real-time sunlight.
  The historical NASA
  [south-pole illumination reference](https://science.nasa.gov/photojournal/south-pole-illumination-map/)
  is multi-temporal and is not used as a timestamp-specific shadow model.
- Rover planning uses a spherical-Moon distance estimate, configured maximum
  speed, explicit local links, and a conservative visibility-window heuristic.
  It does not model slope, wheel slip, energy storage, thermal constraints,
  hazards, or optimal real-world navigation.

## Project structure

- `app.py` — Streamlit navigation, source orchestration, and presentation.
- `horizons.py` — Horizons request construction, parsing, and validation.
- `comparison.py` — aligned site-comparison helpers and charts.
- `ephemeris_export.py` — UTC-safe CSV serialization and filenames.
- `rover_planner.py` — verified station models, visibility evaluation,
  travel-time constrained conceptual routing, interpolation, and payloads.
- `rover_geo.py` — verified station catalog, lunar south-polar projection, map
  normalization, and projected scale-bar helpers.
- `rover_component.py` — Streamlit Components v2 map/timeline renderer using a
  single client-side simulation clock.
- `sites.json` — NASA-published representative traverse-station catalog.
- `data/demo_ephemeris.csv` — bundled offline synthetic data.
- `data/rover_nasa_cache/` — validated, locally stored Horizons tables and a
  provenance manifest for the fixed 2026-11-14 seven-day rover scenario.
- `data/rover_map_manifest.json` — LOLA crop, projection, processing, and source
  provenance for the rover hillshade.
- `static/assets/` — decorative dashboard image assets.
- `static/assets/lola-shackleton-hillshade.webp` — compact display hillshade
  preprocessed from NASA PGDA Site01/Site04 LOLA elevation products.
- `scripts/` — reproducible offline tools for rebuilding the basemap and fixed
  Horizons cache; the application never downloads multi-gigabyte rasters at
  runtime.
- `.streamlit/config.toml` — theme and static-serving configuration.
- `tests/` — offline unit and Streamlit regression tests.

## Team Contributions

LunarSight was developed by a two-person team.

### Alexandr Tereshkov — Team Lead & Lead Developer

- Project leadership and technical decision-making.
- Software architecture and system design.
- Core Python development and implementation.
- NASA JPL Horizons API integration.
- Streamlit application development.
- Scientific data processing and system integration.
- Testing, debugging, GitHub management, and cloud deployment.

### Ramazan Kabayev — Research & Documentation

- Research into lunar South Pole exploration and NASA mission requirements.
- Collection and analysis of scientific sources.
- Preparation of research materials and documentation.
- Development of the project presentation.
- Preparation of the official NASA Space Apps Project Page.
