"""NASA JPL Horizons client and LunarSight ephemeris data contract.

Horizons quantity 4 returns apparent topocentric azimuth and elevation.
Azimuth is measured clockwise from local north through east. Elevation is
measured from the ideal plane perpendicular to local zenith. Both are degrees.
The result does not model local lunar terrain obstruction.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Final

import pandas as pd
import requests

HORIZONS_API_URL: Final = "https://ssd.jpl.nasa.gov/api/horizons.api"
EPHEMERIS_COLUMNS: Final = ("time_utc", "sun_az", "sun_el", "earth_az", "earth_el")
TARGET_IDS: Final = {"sun": "10", "earth": "399"}


class EphemerisValidationError(ValueError):
    """Raised when a table violates the shared data contract."""


class HorizonsError(RuntimeError):
    """Base error for a failed Horizons operation."""


class HorizonsNetworkError(HorizonsError):
    """Raised when the Horizons service cannot be reached."""


class HorizonsResponseError(HorizonsError):
    """Raised when Horizons returns an invalid or unsuccessful response."""


def validate_ephemeris(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a validated copy with UTC timestamps and numeric angles."""
    if frame.empty:
        raise EphemerisValidationError(
            "Ephemeris table must contain at least one observation"
        )
    missing = [column for column in EPHEMERIS_COLUMNS if column not in frame.columns]
    if missing:
        raise EphemerisValidationError(f"Missing columns: {', '.join(missing)}")
    result = frame.loc[:, EPHEMERIS_COLUMNS].copy()
    result["time_utc"] = pd.to_datetime(result["time_utc"], utc=True, errors="coerce")
    if result["time_utc"].isna().any():
        raise EphemerisValidationError("time_utc must contain valid ISO 8601 timestamps")
    for column in EPHEMERIS_COLUMNS[1:]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    if result[list(EPHEMERIS_COLUMNS[1:])].isna().any().any():
        raise EphemerisValidationError("Angle columns must be numeric and non-null")
    if not result["time_utc"].is_monotonic_increasing or result["time_utc"].duplicated().any():
        raise EphemerisValidationError("time_utc must be unique and increasing")
    for column in ("sun_az", "earth_az"):
        if not result[column].between(0, 360, inclusive="left").all():
            raise EphemerisValidationError(f"{column} must be in [0, 360) degrees")
    for column in ("sun_el", "earth_el"):
        if not result[column].between(-90, 90).all():
            raise EphemerisValidationError(f"{column} must be in [-90, 90] degrees")
    return result


def load_ephemeris_csv(path: str) -> pd.DataFrame:
    """Load and validate a LunarSight CSV file."""
    return validate_ephemeris(pd.read_csv(path))


def build_observer_parameters(
    target: str,
    latitude_deg: float,
    longitude_deg_east: float,
    start_utc: datetime,
    stop_utc: datetime,
    step_minutes: int = 60,
) -> dict[str, str]:
    """Build documented parameters for a topocentric lunar observer table."""
    if target not in TARGET_IDS:
        raise ValueError("target must be 'sun' or 'earth'")
    if not -90 <= latitude_deg <= 90:
        raise ValueError("latitude_deg must be in [-90, 90]")
    if not 0 <= longitude_deg_east < 360:
        raise ValueError("longitude_deg_east must be in [0, 360)")
    if step_minutes < 1:
        raise ValueError("step_minutes must be positive")
    start, stop = _as_utc(start_utc), _as_utc(stop_utc)
    if stop <= start:
        raise ValueError("stop_utc must be after start_utc")
    quote = lambda value: f"'{value}'"
    return {
        "format": "json",
        "COMMAND": quote(TARGET_IDS[target]),
        "OBJ_DATA": quote("NO"),
        "MAKE_EPHEM": quote("YES"),
        "EPHEM_TYPE": quote("OBSERVER"),
        "CENTER": quote("coord@301"),
        "COORD_TYPE": quote("GEODETIC"),
        "SITE_COORD": quote(f"{longitude_deg_east},{latitude_deg},0"),
        "START_TIME": quote(start.strftime("%Y-%m-%d %H:%M")),
        "STOP_TIME": quote(stop.strftime("%Y-%m-%d %H:%M")),
        "STEP_SIZE": quote(f"{step_minutes}m"),
        "QUANTITIES": quote("4"),
        "TIME_TYPE": quote("UT"),
        "TIME_ZONE": quote("+00:00"),
        "TIME_DIGITS": quote("MINUTES"),
        "ANG_FORMAT": quote("DEG"),
        "APPARENT": quote("AIRLESS"),
        "CSV_FORMAT": quote("YES"),
    }


def parse_observer_result(result: str, target: str) -> pd.DataFrame:
    """Parse one Horizons observer-table result into UTC, azimuth, elevation."""
    if target not in TARGET_IDS:
        raise ValueError("target must be 'sun' or 'earth'")
    if "$$SOE" not in result or "$$EOE" not in result:
        raise HorizonsResponseError("Horizons response has no ephemeris data markers")
    table = result.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    rows: list[dict[str, object]] = []

    for raw_row in csv.reader(io.StringIO(table)):
        values = [value.strip() for value in raw_row]
        if not values or not values[0]:
            continue
        try:
            timestamp = datetime.strptime(values[0], "%Y-%b-%d %H:%M").replace(
                tzinfo=timezone.utc
            )
        except ValueError as error:
            raise HorizonsResponseError(
                f"Unexpected Horizons timestamp: {values[0]!r}"
            ) from error

        numeric_values: list[float] = []
        for value in values[1:]:
            try:
                numeric_values.append(float(value))
            except ValueError:
                continue
        if len(numeric_values) < 2:
            raise HorizonsResponseError(
                f"Horizons returned no numeric azimuth/elevation at {values[0]}"
            )
        rows.append({
            "time_utc": timestamp,
            f"{target}_az": numeric_values[-2],
            f"{target}_el": numeric_values[-1],
        })

    if not rows:
        raise HorizonsResponseError("Horizons returned an empty ephemeris table")
    return pd.DataFrame(rows)


def fetch_target_ephemeris(
    target: str,
    latitude_deg: float,
    longitude_deg_east: float,
    start_utc: datetime,
    stop_utc: datetime,
    *,
    timeout_seconds: float = 30,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch and parse Sun or Earth azimuth/elevation from Horizons."""
    params = build_observer_parameters(
        target,
        latitude_deg,
        longitude_deg_east,
        start_utc,
        stop_utc,
        step_minutes=60,
    )
    http = session or requests
    try:
        response = http.get(HORIZONS_API_URL, params=params, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as error:
        raise HorizonsNetworkError(f"Horizons request failed: {error}") from error

    try:
        payload = response.json()
    except ValueError as error:
        raise HorizonsResponseError("Horizons returned invalid JSON") from error
    if payload.get("error"):
        raise HorizonsResponseError(f"Horizons error: {payload['error']}")
    result = payload.get("result")
    if not isinstance(result, str):
        raise HorizonsResponseError("Horizons JSON has no text result")
    return parse_observer_result(result, target)


def fetch_ephemeris(
    latitude_deg: float,
    longitude_deg_east: float,
    start_utc: datetime,
    stop_utc: datetime,
    *,
    timeout_seconds: float = 30,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch Sun then Earth tables and return the validated LunarSight schema.

    Calls are deliberately sequential to respect the JPL API fair-use policy.
    """
    sun = fetch_target_ephemeris(
        "sun", latitude_deg, longitude_deg_east, start_utc, stop_utc,
        timeout_seconds=timeout_seconds, session=session,
    )
    earth = fetch_target_ephemeris(
        "earth", latitude_deg, longitude_deg_east, start_utc, stop_utc,
        timeout_seconds=timeout_seconds, session=session,
    )
    if set(sun["time_utc"]) != set(earth["time_utc"]):
        raise HorizonsResponseError("Sun and Earth ephemerides have different timestamps")
    try:
        merged = sun.merge(earth, on="time_utc", how="inner", validate="one_to_one")
        return validate_ephemeris(merged)
    except (pd.errors.MergeError, EphemerisValidationError) as error:
        raise HorizonsResponseError(
            f"Horizons data violates the LunarSight schema: {error}"
        ) from error


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime values must be timezone-aware")
    return value.astimezone(timezone.utc)
