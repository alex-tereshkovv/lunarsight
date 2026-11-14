import json
from pathlib import Path

import pytest

from rover_geo import (
    MAP_BOUNDS_M,
    VERIFIED_STATIONS,
    project_south_polar_stereographic,
    scale_bar_fraction,
    station_map_position,
    stations_within_map,
)


EXPECTED_COORDINATES = {
    "CR1": (-89.468, 222.6),
    "CR2": (-89.500, 222.1),
    "CR3": (-89.418, 221.3),
    "SR1": (-89.685, 196.7),
    "SR2": (-89.740, 201.2),
    "SR3": (-89.808, 205.9),
    "PSR1": (-89.575, 196.7),
}


def test_verified_station_catalog_uses_published_east_positive_coordinates():
    assert {
        station.id: (station.latitude_deg, station.longitude_deg_east)
        for station in VERIFIED_STATIONS
    } == EXPECTED_COORDINATES


def test_station_projection_is_metric_and_every_station_is_inside_map_crop():
    cr1 = next(station for station in VERIFIED_STATIONS if station.id == "CR1")
    x_m, y_m = project_south_polar_stereographic(
        cr1.latitude_deg,
        cr1.longitude_deg_east,
    )
    assert x_m == pytest.approx(-10919.5, abs=0.1)
    assert y_m == pytest.approx(-11874.8, abs=0.1)
    assert stations_within_map()
    assert all(
        0.0 <= map_x <= 1.0 and 0.0 <= map_y <= 1.0
        for map_x, map_y in map(station_map_position, VERIFIED_STATIONS)
    )


def test_scale_bar_is_derived_from_projected_map_width():
    x_min, _, x_max, _ = MAP_BOUNDS_M
    assert scale_bar_fraction(2.0) == pytest.approx(2000.0 / (x_max - x_min))


def test_committed_hillshade_manifest_records_projection_and_processing():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "data" / "rover_map_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["source_resolution_m_per_pixel"] == 5.0
    assert manifest["projection"]["reference_frame"] == "MOON_ME, DE421"
    assert manifest["projection"]["longitude_direction"] == "east-positive"
    assert manifest["projected_bounds_m"] == {
        "x_min": MAP_BOUNDS_M[0],
        "y_min": MAP_BOUNDS_M[1],
        "x_max": MAP_BOUNDS_M[2],
        "y_max": MAP_BOUNDS_M[3],
    }
    assert "not timestamp-specific illumination" in manifest["processing"]
    assert (root / "static" / "assets" / manifest["image"]).is_file()
