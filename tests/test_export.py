import csv
from datetime import date
from io import StringIO

import pandas as pd
import pytest

from ephemeris_export import (
    CSV_MIME_TYPE,
    build_ephemeris_export,
    build_export_filename,
    serialize_ephemeris_csv,
)


def sample_ephemeris() -> pd.DataFrame:
    return pd.DataFrame({
        "time_utc": pd.to_datetime(
            ["2026-11-15T00:00:00Z", "2026-11-15T01:00:00Z"],
            utc=True,
        ),
        "sun_az": [114.44285812345678, 113.93528798765432],
        "sun_el": [1.349506123456789, 1.353515987654321],
        "earth_az": [357.3811711234568, 357.3233279876543],
        "earth_el": [-3.053516123456789, -3.004436987654321],
    })


def test_csv_export_preserves_columns_utc_and_float_precision():
    original = sample_ephemeris()
    encoded = serialize_ephemeris_csv(original)

    assert encoded.decode("utf-8").splitlines()[1].startswith(
        "2026-11-15T00:00:00Z,"
    )
    restored_rows = list(csv.DictReader(StringIO(encoded.decode("utf-8"))))
    assert list(restored_rows[0]) == list(original.columns)
    assert len(restored_rows) == len(original)
    for index, row in enumerate(restored_rows):
        assert pd.Timestamp(row["time_utc"]) == original.at[index, "time_utc"]
        for column in ["sun_az", "sun_el", "earth_az", "earth_el"]:
            assert float(row[column]) == original.at[index, column]


@pytest.mark.parametrize(
    ("data_source", "expected_label"),
    [
        ("NASA JPL Horizons (Live)", "NASA_LIVE"),
        ("Reference Profile (Synthetic)", "SYNTHETIC_DEMO"),
        ("Reference Profile (Synthetic Fallback)", "SYNTHETIC_DEMO"),
    ],
)
def test_filename_identifies_actual_source(data_source, expected_label):
    filename = build_export_filename(
        data_source=data_source,
        site_id="demo_plateau_beta",
        start_date=date(2026, 11, 15),
        duration_hours=48,
    )
    assert filename == (
        f"LunarSight_ephemeris_{expected_label}_demo_plateau_beta_"
        "2026-11-15_48h.csv"
    )


def test_unknown_source_is_never_silently_labeled_as_nasa():
    with pytest.raises(ValueError, match="Unsupported ephemeris data source"):
        build_export_filename(
            data_source="Unknown",
            site_id="demo_ridge_alpha",
            start_date=date(2026, 11, 15),
            duration_hours=24,
        )


@pytest.mark.parametrize("duration_hours", [0, -1, 24.5, True])
def test_filename_rejects_invalid_duration(duration_hours):
    with pytest.raises(ValueError, match="positive integer"):
        build_export_filename(
            data_source="Reference Profile (Synthetic)",
            site_id="CR1",
            start_date=date(2026, 11, 15),
            duration_hours=duration_hours,
        )


def test_complete_export_uses_utf8_csv_and_sanitizes_site_identifier():
    export = build_ephemeris_export(
        sample_ephemeris(),
        data_source="Reference Profile (Synthetic)",
        site_id="south pole / candidate 1",
        start_date=date(2026, 11, 15),
        duration_hours=72,
    )
    assert export.mime_type == CSV_MIME_TYPE
    assert export.filename == (
        "LunarSight_ephemeris_SYNTHETIC_DEMO_south_pole_candidate_1_"
        "2026-11-15_72h.csv"
    )
    assert export.data.startswith(b"time_utc,sun_az,sun_el,earth_az,earth_el\n")
