"""Verified lunar south-pole station and map-projection helpers.

The station coordinates come from the NASA Lunar Surface Data Book,
M2M-30044 (2025), section 7.3.  Longitudes are east-positive degrees.
The projection matches the NASA PGDA LOLA 5 m/pixel local GeoTIFFs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, radians, sin, tan
from typing import Final

MOON_RADIUS_M: Final = 1_737_400.0
MAP_BOUNDS_M: Final = (-16_002.5, -14_997.5, 6_997.5, -4_997.5)
MAP_PIXEL_SIZE_M: Final = 5.0

LUNAR_SURFACE_DATA_BOOK_URL: Final = (
    "https://ntrs.nasa.gov/api/citations/20250002845/downloads/"
    "M2M-30044%20Lunar%20Surface%20Data%20Book%20Baseline_Final.pdf"
)
LOLA_LOCAL_DEM_URL: Final = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/"
SHACKLETON_FEATURE_URL: Final = "https://planetarynames.wr.usgs.gov/Feature/5450"
SHACKLETON_OVERVIEW_URL: Final = (
    "https://science.nasa.gov/resource/illumination-map-of-the-moons-south-pole/"
)
# Current IAU/USGS control-network values. The older nominal pole coordinate is
# retained by the Gazetteer too, so recording the control network matters here.
SHACKLETON_CENTER_LATITUDE_DEG: Final = -89.67
SHACKLETON_CENTER_LONGITUDE_DEG_EAST: Final = 129.78
SHACKLETON_DIAMETER_KM: Final = 20.92


@dataclass(frozen=True)
class VerifiedStation:
    """A station published in NASA's representative traverse material."""

    id: str
    label: str
    latitude_deg: float
    longitude_deg_east: float


VERIFIED_STATIONS: Final[tuple[VerifiedStation, ...]] = (
    VerifiedStation("CR1", "Connecting Ridge 1", -89.468, 222.6),
    VerifiedStation("CR2", "Connecting Ridge 2", -89.500, 222.1),
    VerifiedStation("CR3", "Connecting Ridge 3", -89.418, 221.3),
    VerifiedStation("SR1", "Shackleton Rim 1", -89.685, 196.7),
    VerifiedStation("SR2", "Shackleton Rim 2", -89.740, 201.2),
    VerifiedStation("SR3", "Shackleton Rim 3", -89.808, 205.9),
    VerifiedStation("PSR1", "Permanently Shadowed Region 1", -89.575, 196.7),
)


def project_south_polar_stereographic(
    latitude_deg: float,
    longitude_deg_east: float,
) -> tuple[float, float]:
    """Project lunar geodetic degrees to NASA LOLA south-polar X/Y metres.

    This is the spherical polar-stereographic definition encoded in the PGDA
    GeoTIFFs: latitude of origin -90 degrees, central meridian 0 degrees,
    scale factor 1, false easting/northing 0, and radius 1,737,400 metres.
    """
    latitude = float(latitude_deg)
    if not -90.0 <= latitude <= 0.0:
        raise ValueError("latitude must be between -90 and 0 degrees")
    longitude = float(longitude_deg_east) % 360.0

    # The Moon is round; the dashboard stubbornly is not. Keep the transform explicit.
    rho = 2.0 * MOON_RADIUS_M * tan(pi / 4.0 + radians(latitude) / 2.0)
    longitude_rad = radians(longitude)
    return rho * sin(longitude_rad), rho * cos(longitude_rad)


def normalize_projected_position(
    x_m: float,
    y_m: float,
    bounds_m: tuple[float, float, float, float] = MAP_BOUNDS_M,
) -> tuple[float, float]:
    """Convert projected metres into normalized image coordinates."""
    x_min, y_min, x_max, y_max = bounds_m
    if x_max <= x_min or y_max <= y_min:
        raise ValueError("map bounds must have positive width and height")
    map_x = (float(x_m) - x_min) / (x_max - x_min)
    map_y = (y_max - float(y_m)) / (y_max - y_min)
    return map_x, map_y


def station_map_position(station: VerifiedStation) -> tuple[float, float]:
    """Return the station's normalized position in the committed map crop."""
    return normalize_projected_position(
        *project_south_polar_stereographic(
            station.latitude_deg,
            station.longitude_deg_east,
        )
    )


def shackleton_map_position() -> tuple[float, float]:
    """Return the IAU Shackleton centre in the committed crop coordinates."""
    return normalize_projected_position(
        *project_south_polar_stereographic(
            SHACKLETON_CENTER_LATITUDE_DEG,
            SHACKLETON_CENTER_LONGITUDE_DEG_EAST,
        )
    )


def shackleton_within_map() -> bool:
    """Return whether the named crater centre lies inside the route-map crop."""
    map_x, map_y = shackleton_map_position()
    return 0.0 <= map_x <= 1.0 and 0.0 <= map_y <= 1.0


def scale_bar_fraction(distance_km: float) -> float:
    """Return a horizontal scale-bar length as a fraction of map width."""
    if distance_km <= 0:
        raise ValueError("scale-bar distance must be positive")
    x_min, _, x_max, _ = MAP_BOUNDS_M
    return distance_km * 1_000.0 / (x_max - x_min)


def stations_within_map() -> bool:
    """Return whether every verified station lies inside the committed crop."""
    return all(
        0.0 <= map_x <= 1.0 and 0.0 <= map_y <= 1.0
        for map_x, map_y in map(station_map_position, VERIFIED_STATIONS)
    )
