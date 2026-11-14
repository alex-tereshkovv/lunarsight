"""Fetch and manifest a fixed offline NASA Horizons rover dataset."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from horizons import HORIZONS_API_URL, fetch_ephemeris
from rover_geo import VERIFIED_STATIONS
from rover_planner import SOURCE_NASA_CACHED, downsample_ephemeris


def build_cache(output_dir: Path, start_utc: datetime, duration_days: int) -> None:
    """Fetch aligned hourly tables and save a compact three-hour cache."""
    if start_utc.tzinfo is None:
        raise ValueError("start_utc must be timezone-aware")
    start_utc = start_utc.astimezone(timezone.utc)
    stop_utc = start_utc + timedelta(days=duration_days)
    output_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}

    for station in VERIFIED_STATIONS:
        frame = fetch_ephemeris(
            station.latitude_deg,
            station.longitude_deg_east,
            start_utc,
            stop_utc,
            timeout_seconds=60,
        )
        frame = downsample_ephemeris(frame, step_hours=3)
        filename = f"{station.id}.csv"
        frame.to_csv(
            output_dir / filename,
            index=False,
            date_format="%Y-%m-%dT%H:%M:%SZ",
            float_format="%.8f",
            encoding="utf-8",
        )
        files[station.id] = filename

    manifest = {
        "schema_version": 2,
        "source_label": SOURCE_NASA_CACHED,
        "source_url": HORIZONS_API_URL,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "observation_start_utc": start_utc.isoformat().replace("+00:00", "Z"),
        "observation_end_utc": stop_utc.isoformat().replace("+00:00", "Z"),
        "sample_interval_hours": 3,
        "observer": "Lunar surface coord@301",
        "coordinate_convention": (
            "Lunar geodetic latitude and east-positive longitude, degrees"
        ),
        "targets": {"sun": "10", "earth": "399"},
        "quantities": "4 (apparent azimuth and elevation, AIRLESS)",
        "stations": {
            station.id: {
                "latitude_deg": station.latitude_deg,
                "longitude_deg_east": station.longitude_deg_east,
            }
            for station in VERIFIED_STATIONS
        },
        "files": files,
        "scientific_note": (
            "Object-centre geometry relative to an ideal horizon; terrain, power, "
            "link budget, traversability, and hazards are not modeled."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/rover_nasa_cache"))
    parser.add_argument("--start", default="2026-11-14T00:00:00+00:00")
    parser.add_argument("--days", type=int, default=7)
    arguments = parser.parse_args()
    build_cache(
        arguments.output,
        datetime.fromisoformat(arguments.start),
        arguments.days,
    )


if __name__ == "__main__":
    main()
