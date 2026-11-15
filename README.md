# LunarSight

## [Open the live app](https://lunarsight.streamlit.app/)

**A lunar south-pole mission-planning prototype built for a NASA Space Apps-style hackathon.**

LunarSight started with a simple question: *if you were planning work near the
Moon's south pole, when would you be able to see the Sun and Earth from a
specific location?*

The app turns that question into an interactive dashboard. You can choose a
lunar surface station, select a UTC observation period, inspect Sun and Earth
angles, compare two locations, export the displayed ephemeris table, and explore
a conceptual rover scenario.

We built LunarSight as an educational prototype, not as a flight tool. It is not
affiliated with or endorsed by NASA, and it must not be used for landing safety
or operational mission decisions.

## What you can do

- Request real topocentric Sun and Earth ephemerides from NASA JPL Horizons.
- Work offline with a clearly labelled synthetic reference profile.
- Explore 24, 48, or 72 hours of azimuth and elevation data.
- Compare two lunar surface observers over exactly the same UTC interval.
- Scrub through a compass view and see where the Sun and Earth are relative to
  an ideal local horizon.
- Download the exact displayed ephemeris table as a UTC-preserving CSV file.
- Explore a synchronized Solar Rover Planner built around seven published NASA
  representative-traverse stations.
- Use a bundled, validated Horizons cache for a reliable presentation when the
  network is unavailable.

## A quick tour

### Mission Control

Choose a station, date, duration, and data source. The main chart shows Sun and
Earth elevation through time, while the compass shows their current azimuth and
elevation at the selected timestamp.

### Site Comparison

Select two stations and compare them over one shared observation period. Live
mode requests separate ephemerides for each location. LunarSight never quietly
mixes NASA data for one site with synthetic data for another.

### Solar Rover Planner

The rover view combines published station coordinates, geometric visibility,
and a conceptual movement timeline. The rover, chart cursor, status panel, and
map position all follow the same mission clock.

The route overlay is intentionally described as conceptual. Straight station
links are not NASA traverse polylines and are not claims of terrain safety or
verified traversability.

## Where the data comes from

### NASA JPL Horizons

Live Sun and Earth angles come from the official
[NASA JPL Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html) and
[Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html).

LunarSight uses:

- lunar surface observer: `coord@301`;
- Sun target: `10`;
- Earth target: `399`;
- observer quantity: `4`;
- one-hour steps;
- UTC timestamps;
- airless apparent azimuth and elevation in degrees.

Successful live results are cached for one hour to avoid unnecessary API calls.

### Published lunar stations

The rover planner uses east-positive coordinates published in NASA's
[Lunar Surface Data Book, M2M-30044 (2025)](https://ntrs.nasa.gov/api/citations/20250002845/downloads/M2M-30044%20Lunar%20Surface%20Data%20Book%20Baseline_Final.pdf):

| Station | Latitude | East longitude |
| --- | ---: | ---: |
| CR1 | -89.468° | 222.6° E |
| CR2 | -89.500° | 222.1° E |
| CR3 | -89.418° | 221.3° E |
| SR1 | -89.685° | 196.7° E |
| SR2 | -89.740° | 201.2° E |
| SR3 | -89.808° | 205.9° E |
| PSR1 | -89.575° | 196.7° E |

These are representative traverse stations, not certified landing sites.

### Terrain background

The rover map hillshade was preprocessed offline from NASA PGDA
[Site01 Connecting Ridge and Site04 Shackleton Rim LOLA products](https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/).
The original GeoTIFFs are 5 m/pixel and use lunar south-polar stereographic
coordinates in metres. Projection details, processing notes, and source URLs are
recorded in `data/rover_map_manifest.json`.

The hillshade is terrain visualization, not a real-time sunlight simulation.
The overview inset uses NASA's historical
[south-pole illumination reference](https://science.nasa.gov/resource/illumination-map-of-the-moons-south-pole/)
for regional context only.

### Decorative visual assets

The lunar mountain illustration in the page header and the lunar landscape in
the left sidebar are **AI-generated decorative backgrounds**. They are labelled
inside the app and are not scientific imagery or analysis inputs.

This is separate from the Solar Rover Planner hillshade, which is derived from
NASA LOLA elevation products and is documented in the map manifest.

## Run LunarSight locally on Windows

Open PowerShell in the repository folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If the `py` launcher is unavailable, use `python` instead of `py -3.12`.
Activating the virtual environment is optional because the commands above call
its Python executable directly.

Streamlit normally opens the app at `http://localhost:8501`.

Run the checks with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py comparison.py horizons.py ephemeris_export.py tests
```

Python 3.11 or newer is supported locally. The deployed app uses Python 3.12.

## A short presentation flow

1. Start in **Mission Control** with the synthetic reference profile so the
   demonstration does not depend on the network.
2. Move the UTC slider and show that the compass and Sun/Earth cards update
   together.
3. Open the observation table and export its CSV file. The filename clearly
   identifies synthetic data as `SYNTHETIC_DEMO`.
4. Switch to **Live NASA (Horizons)** and request a real observation period.
5. Open **Site Comparison** and compare two stations over the same timestamps.
6. Open **Solar Rover Planner**, play the cached NASA scenario, and scrub the
   timeline to show that the rover and scientific panels remain synchronized.
7. Finish on **Data & Sources** to explain provenance and limitations.

If Horizons is unavailable, Mission Control reports the network error and uses
the explicitly labelled `Reference Profile (Synthetic Fallback)`. Live Site
Comparison shows no partial result rather than mixing sources.

## Ephemeris format

Every validated row follows this schema:

```text
time_utc,sun_az,sun_el,earth_az,earth_el
```

- `time_utc` is a timezone-aware ISO 8601 UTC timestamp.
- `sun_az` and `earth_az` are degrees in `[0, 360)`, measured clockwise from
  local north through east.
- `sun_el` and `earth_el` are degrees in `[-90, 90]`, measured relative to an
  ideal local horizontal plane.
- Station coordinates use lunar geodetic latitude and east-positive longitude.

## What LunarSight does not model

This is the part we do not want to hide behind a polished interface:

- A positive Sun elevation means geometric visibility of the Sun's center. It
  does not guarantee surface illumination because nearby terrain and shadows
  are not modeled.
- A positive Earth elevation does not guarantee a reliable radio link. Antenna
  patterns, margins, relay geometry, and link budgets are outside the model.
- Elevation refers to the center of the Sun or Earth, not the full disk.
- Lunar slopes, landing hazards, wheel slip, energy storage, thermal limits,
  localization uncertainty, and operational safety margins are not modeled.
- The route overlay connects published stations conceptually. It is not a
  terrain-safe path, an autonomous-navigation result, or a published NASA
  traverse length.
- Continuous Exploration is a repeatable visualization mode, not an optimal
  route or visibility solution.
- The map hillshade uses a fixed display light direction and does not represent
  timestamp-specific illumination.

## Project structure

- `app.py` — Streamlit interface, navigation, and data-source orchestration.
- `horizons.py` — Horizons request construction, parsing, and validation.
- `comparison.py` — aligned site-comparison helpers and charts.
- `ephemeris_export.py` — UTC-safe CSV serialization and filenames.
- `rover_planner.py` — station models, conceptual routing, and synchronized
  simulation payloads.
- `rover_geo.py` — lunar projection and map-coordinate helpers.
- `rover_component.py` — Streamlit Components v2 rover map and timeline.
- `sites.json` — NASA-published representative-station catalog.
- `data/demo_ephemeris.csv` — bundled synthetic reference data.
- `data/rover_nasa_cache/` — fixed-period validated Horizons tables and
  provenance manifest.
- `data/rover_map_manifest.json` — LOLA crop and projection provenance.
- `static/assets/` — decorative interface assets and the processed rover map.
- `scripts/` — offline tools for rebuilding the map and Horizons cache.
- `tests/` — offline unit and Streamlit regression tests.

## Deployment

The production entry point is `app.py`. Streamlit Community Cloud reads
`requirements.txt` and `.streamlit/config.toml` from the repository root. The
app needs no secrets, database, Docker image, or operating-system packages.

Pushing to the configured stable branch triggers the normal Community Cloud
update process.

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
