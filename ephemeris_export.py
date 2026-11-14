"""CSV export helpers for LunarSight ephemeris data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from numbers import Integral

import pandas as pd

CSV_MIME_TYPE = "text/csv;charset=utf-8"
SOURCE_FILENAME_LABELS = {
    "NASA JPL Horizons (Live)": "NASA_LIVE",
    "Demo (Synthetic)": "SYNTHETIC_DEMO",
    "Demo (Fallback)": "SYNTHETIC_DEMO",
}


@dataclass(frozen=True)
class EphemerisExport:
    """A complete file download prepared from an in-memory ephemeris table."""

    data: bytes
    filename: str
    mime_type: str = CSV_MIME_TYPE


def serialize_ephemeris_csv(frame: pd.DataFrame) -> bytes:
    """Serialize the displayed ephemeris table as UTF-8 CSV.

    UTC timestamps use an unambiguous ISO 8601 representation. Pandas' default
    float formatting emits the shortest round-trip representation, avoiding
    display-oriented rounding while keeping the file readable.
    """
    if frame.empty:
        raise ValueError("Cannot export an empty ephemeris table")
    if "time_utc" not in frame.columns:
        raise ValueError("Ephemeris table must contain time_utc")

    export_frame = frame.copy()
    timestamps = pd.to_datetime(export_frame["time_utc"], utc=True, errors="raise")
    export_frame["time_utc"] = timestamps.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    csv_text = export_frame.to_csv(index=False, lineterminator="\n")
    return csv_text.encode("utf-8")


def build_export_filename(
    *,
    data_source: str,
    site_id: str,
    start_date: date,
    duration_hours: int,
) -> str:
    """Build a safe, self-describing ephemeris export filename."""
    try:
        source_label = SOURCE_FILENAME_LABELS[data_source]
    except KeyError as error:
        raise ValueError(f"Unsupported ephemeris data source: {data_source}") from error
    if (
        isinstance(duration_hours, bool)
        or not isinstance(duration_hours, Integral)
        or duration_hours <= 0
    ):
        raise ValueError("duration_hours must be a positive integer")

    safe_site_id = re.sub(r"[^A-Za-z0-9_-]+", "_", site_id).strip("_")
    if not safe_site_id:
        raise ValueError("site_id must contain a filename-safe identifier")

    return (
        f"LunarSight_ephemeris_{source_label}_{safe_site_id}_"
        f"{start_date.isoformat()}_{duration_hours}h.csv"
    )


def build_ephemeris_export(
    frame: pd.DataFrame,
    *,
    data_source: str,
    site_id: str,
    start_date: date,
    duration_hours: int,
) -> EphemerisExport:
    """Prepare a download from the already displayed in-memory DataFrame."""
    return EphemerisExport(
        data=serialize_ephemeris_csv(frame),
        filename=build_export_filename(
            data_source=data_source,
            site_id=site_id,
            start_date=start_date,
            duration_hours=duration_hours,
        ),
    )
