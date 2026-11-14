"""Build the small committed rover basemap from official NASA LOLA DEMs.

This is an offline maintainer tool, not application runtime code.  Download
Site01 and Site04 ``*_surf.tif`` files from NASA PGDA, place them in an input
directory, then run ``python -m scripts.build_rover_basemap <directory>``. It validates the embedded projection tags,
blends the overlapping DEMs, and creates a terrain hillshade crop.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from rover_geo import (
    LOLA_LOCAL_DEM_URL,
    MAP_BOUNDS_M,
    MAP_PIXEL_SIZE_M,
    MOON_RADIUS_M,
)

EXPECTED_FILES = (
    "Site01_final_adj_5mpp_surf.tif",
    "Site04_final_adj_5mpp_surf.tif",
)


def read_dem(path: Path) -> tuple[np.ndarray, float, float]:
    """Read one expected GeoTIFF and return values plus its top-left centre."""
    with Image.open(path) as image:
        scale = tuple(float(value) for value in image.tag_v2[33550])
        tiepoint = tuple(float(value) for value in image.tag_v2[33922])
        projection = tuple(float(value) for value in image.tag_v2[34736])
        if image.size != (3200, 3200) or scale[:2] != (5.0, 5.0):
            raise ValueError(f"Unexpected dimensions or pixel scale in {path.name}")
        if projection[0] != -90.0 or projection[2] != 1.0:
            raise ValueError(f"Unexpected polar-stereographic parameters in {path.name}")
        if projection[5:7] != (MOON_RADIUS_M, MOON_RADIUS_M):
            raise ValueError(f"Unexpected lunar radius in {path.name}")
        values = np.asarray(image, dtype=np.float32)
    return values, tiepoint[3], tiepoint[4]


def mosaic_crop(source_dir: Path) -> np.ndarray:
    """Blend Site01/Site04 onto the fixed projected crop."""
    x_min, y_min, x_max, y_max = MAP_BOUNDS_M
    width = int(round((x_max - x_min) / MAP_PIXEL_SIZE_M))
    height = int(round((y_max - y_min) / MAP_PIXEL_SIZE_M))
    total = np.zeros((height, width), dtype=np.float64)
    weight_sum = np.zeros((height, width), dtype=np.float64)

    target_x = x_min + MAP_PIXEL_SIZE_M / 2.0
    target_y = y_max - MAP_PIXEL_SIZE_M / 2.0
    for filename in EXPECTED_FILES:
        values, source_x, source_y = read_dem(source_dir / filename)
        col_start = int(round((target_x - source_x) / MAP_PIXEL_SIZE_M))
        row_start = int(round((source_y - target_y) / MAP_PIXEL_SIZE_M))
        rows = np.arange(height) + row_start
        cols = np.arange(width) + col_start
        valid_rows = (rows >= 0) & (rows < values.shape[0])
        valid_cols = (cols >= 0) & (cols < values.shape[1])
        target_rows = np.flatnonzero(valid_rows)
        target_cols = np.flatnonzero(valid_cols)
        sampled = values[np.ix_(rows[valid_rows], cols[valid_cols])]
        valid = np.isfinite(sampled)
        source_rows = rows[valid_rows]
        source_cols = cols[valid_cols]
        row_distance = np.minimum(source_rows, values.shape[0] - 1 - source_rows)
        col_distance = np.minimum(source_cols, values.shape[1] - 1 - source_cols)
        edge_distance = np.minimum.outer(row_distance, col_distance)
        weights = np.clip(edge_distance / 400.0, 0.02, 1.0)
        region = np.ix_(target_rows, target_cols)
        total_region = total[region]
        weight_region = weight_sum[region]
        total_region[valid] += sampled[valid] * weights[valid]
        weight_region[valid] += weights[valid]
        total[region] = total_region
        weight_sum[region] = weight_region

    if np.any(weight_sum == 0):
        raise ValueError("The selected LOLA products do not fully cover the map crop")
    return (total / weight_sum).astype(np.float32)


def hillshade(elevation_m: np.ndarray) -> np.ndarray:
    """Create a display-only 315°/45° terrain hillshade."""
    elevation_m = elevation_m.copy()
    local_mean = (
        np.roll(elevation_m, 1, axis=0)
        + np.roll(elevation_m, -1, axis=0)
        + np.roll(elevation_m, 1, axis=1)
        + np.roll(elevation_m, -1, axis=1)
    ) / 4.0
    residual = np.abs(elevation_m - local_mean)
    bad_rows = np.flatnonzero((residual > 20.0).sum(axis=1) > 100)
    bad_rows = bad_rows[(bad_rows > 0) & (bad_rows < elevation_m.shape[0] - 1)]
    if bad_rows.size:
        groups = np.split(bad_rows, np.flatnonzero(np.diff(bad_rows) > 1) + 1)
        for group in groups:
            before, after = int(group[0] - 1), int(group[-1] + 1)
            for row in group:
                fraction = (row - before) / (after - before)
                elevation_m[row] = (
                    elevation_m[before] * (1.0 - fraction)
                    + elevation_m[after] * fraction
                )

    kernel = np.asarray([1.0, 4.0, 6.0, 4.0, 1.0], dtype=np.float32) / 16.0
    padded_x = np.pad(elevation_m, ((0, 0), (2, 2)), mode="edge")
    smoothed_x = sum(
        weight * padded_x[:, offset : offset + elevation_m.shape[1]]
        for offset, weight in enumerate(kernel)
    )
    padded_y = np.pad(smoothed_x, ((2, 2), (0, 0)), mode="edge")
    smoothed = sum(
        weight * padded_y[offset : offset + elevation_m.shape[0], :]
        for offset, weight in enumerate(kernel)
    )
    gradient_y, gradient_x = np.gradient(smoothed, MAP_PIXEL_SIZE_M)
    gradient_x = np.clip(gradient_x, -2.0, 2.0)
    gradient_y = np.clip(gradient_y, -2.0, 2.0)
    slope = np.arctan(np.hypot(gradient_x, gradient_y))
    aspect = np.arctan2(-gradient_x, gradient_y)
    azimuth = np.deg2rad(315.0)
    altitude = np.deg2rad(45.0)
    illumination = (
        np.sin(altitude) * np.cos(slope)
        + np.cos(altitude) * np.sin(slope) * np.cos(azimuth - aspect)
    )
    low, high = np.percentile(illumination, (1.0, 99.0))
    normalized = np.clip((illumination - low) / (high - low), 0.0, 1.0)
    # A little ambient light preserves crater detail without pretending this is sunlight.
    return np.asarray((28.0 + normalized * 215.0), dtype=np.uint8)


def build(source_dir: Path, image_path: Path, manifest_path: Path) -> None:
    elevation = mosaic_crop(source_dir)
    shaded = hillshade(elevation)
    image = Image.fromarray(shaded, mode="L").resize((1840, 800), Image.Resampling.LANCZOS)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(image_path, format="WEBP", quality=90, method=6)

    manifest = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "image": image_path.name,
        "image_size_px": [1840, 800],
        "source_resolution_m_per_pixel": MAP_PIXEL_SIZE_M,
        "projected_bounds_m": {
            "x_min": MAP_BOUNDS_M[0],
            "y_min": MAP_BOUNDS_M[1],
            "x_max": MAP_BOUNDS_M[2],
            "y_max": MAP_BOUNDS_M[3],
        },
        "projection": {
            "name": "Lunar south polar stereographic",
            "latitude_of_origin_deg": -90.0,
            "central_meridian_deg": 0.0,
            "scale_factor": 1.0,
            "false_easting_m": 0.0,
            "false_northing_m": 0.0,
            "moon_radius_m": MOON_RADIUS_M,
            "reference_frame": "MOON_ME, DE421",
            "longitude_direction": "east-positive",
        },
        "sources": [
            f"{LOLA_LOCAL_DEM_URL}Site01/Site01_final_adj_5mpp_surf.tif",
            f"{LOLA_LOCAL_DEM_URL}Site04/Site04_final_adj_5mpp_surf.tif",
        ],
        "processing": (
            "Site01/Site04 overlap feather-blended; long nonphysical raster-line "
            "spikes removed for display; terrain hillshade uses azimuth 315° and "
            "elevation 45°. Hillshade is not timestamp-specific illumination."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument(
        "--image",
        type=Path,
        default=Path("static/assets/lola-shackleton-hillshade.webp"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/rover_map_manifest.json"),
    )
    arguments = parser.parse_args()
    build(arguments.source_dir, arguments.image, arguments.manifest)


if __name__ == "__main__":
    main()
