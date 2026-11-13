"""Shared ephemeris contract and future NASA JPL Horizons adapter.

Azimuth is clockwise from north through east. Elevation is measured from the
ideal local horizontal plane. Terrain obstruction is not represented.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

import pandas as pd

HORIZONS_API_URL: Final = "https://ssd-api.jpl.nasa.gov/api/horizons.api"
EPHEMERIS_COLUMNS: Final = ("time_utc", "sun_az", "sun_el", "earth_az", "earth_el")
TARGET_IDS: Final = {"sun": "10", "earth": "399"}


class EphemerisValidationError(ValueError):
    """Raised when a table violates the shared data contract."""


def validate_ephemeris(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a validated copy with UTC timestamps and numeric angles."""
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


def build_observer_parameters(target: str, latitude_deg: float, longitude_deg_east: float,
                              start_utc: datetime, stop_utc: datetime,
                              step_minutes: int = 60) -> dict[str, str]:
    """Build, but do not send, a lunar topocentric Horizons API request."""
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
        "format": "json", "COMMAND": quote(TARGET_IDS[target]), "OBJ_DATA": quote("NO"),
        "MAKE_EPHEM": quote("YES"), "EPHEM_TYPE": quote("OBSERVER"),
        "CENTER": quote("coord@301"), "COORD_TYPE": quote("GEODETIC"),
        "SITE_COORD": quote(f"{longitude_deg_east},{latitude_deg},0"),
        "START_TIME": quote(start.strftime("%Y-%m-%d %H:%M")),
        "STOP_TIME": quote(stop.strftime("%Y-%m-%d %H:%M")),
        "STEP_SIZE": quote(f"{step_minutes}m"), "QUANTITIES": quote("4"),
        "TIME_TYPE": quote("UT"), "TIME_DIGITS": quote("MINUTES"),
        "ANG_FORMAT": quote("DEG"), "APPARENT": quote("AIRLESS"),
        "CSV_FORMAT": quote("YES"),
    }


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime values must be timezone-aware")
    return value.astimezone(timezone.utc)
