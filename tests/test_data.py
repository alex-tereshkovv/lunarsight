import json
from pathlib import Path

import pandas as pd
import pytest

from horizons import EPHEMERIS_COLUMNS, EphemerisValidationError, load_ephemeris_csv, validate_ephemeris

ROOT = Path(__file__).resolve().parents[1]


def test_demo_ephemeris_loads_and_matches_contract():
    frame = load_ephemeris_csv(str(ROOT / "data" / "demo_ephemeris.csv"))
    assert tuple(frame.columns) == EPHEMERIS_COLUMNS
    assert str(frame["time_utc"].dt.tz) == "UTC"
    assert len(frame) == 13


def test_validation_rejects_out_of_range_elevation():
    frame = pd.DataFrame([{"time_utc": "2026-01-01T00:00:00Z", "sun_az": 0,
                           "sun_el": 91, "earth_az": 180, "earth_el": 0}])
    with pytest.raises(EphemerisValidationError, match="sun_el"):
        validate_ephemeris(frame)


def test_sites_are_explicitly_unverified_demonstrations():
    catalog = json.loads((ROOT / "sites.json").read_text(encoding="utf-8"))
    assert catalog["sites"]
    assert all(site["verified"] is False for site in catalog["sites"])
    assert all("Synthetic" in site["scientific_source"] for site in catalog["sites"])
