"""Pure helpers for comparing two LunarSight ephemeris tables."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

SITE_A_COLOR = "#FFC845"
SITE_B_COLOR = "#42B4FF"
HORIZON_COLOR = "#D7E3F4"


class ComparisonAlignmentError(ValueError):
    """Raised when two ephemeris tables cannot be compared timestamp by timestamp."""


def validate_matching_timestamps(
    frame_a: pd.DataFrame,
    frame_b: pd.DataFrame,
) -> pd.Series:
    """Return the shared UTC timeline or raise when the samples are not aligned."""
    if frame_a.empty or frame_b.empty:
        raise ComparisonAlignmentError("Both ephemeris tables must contain samples")
    if "time_utc" not in frame_a.columns or "time_utc" not in frame_b.columns:
        raise ComparisonAlignmentError("Both ephemeris tables must contain time_utc")

    times_a = pd.to_datetime(frame_a["time_utc"], utc=True, errors="raise").reset_index(
        drop=True
    )
    times_b = pd.to_datetime(frame_b["time_utc"], utc=True, errors="raise").reset_index(
        drop=True
    )
    if times_a.duplicated().any() or times_b.duplicated().any():
        raise ComparisonAlignmentError("Ephemeris timestamps must be unique")
    if not times_a.equals(times_b):
        raise ComparisonAlignmentError(
            "NASA responses for the two sites use different UTC sample timestamps"
        )
    return times_a


def geometric_visibility_status(elevation_deg: float) -> tuple[str, str]:
    """Describe instantaneous visibility relative to the ideal geometric horizon."""
    if elevation_deg > 0:
        return "Above ideal horizon", "above"
    if elevation_deg < 0:
        return "Below ideal horizon", "below"
    return "On ideal horizon", "horizon"


def comparison_elevation_chart(
    frame_a: pd.DataFrame,
    frame_b: pd.DataFrame,
    *,
    elevation_column: str,
    azimuth_column: str,
    target_name: str,
    site_a_name: str,
    site_b_name: str,
) -> go.Figure:
    """Build an aligned Site A versus Site B elevation chart."""
    times = validate_matching_timestamps(frame_a, frame_b)
    for frame in (frame_a, frame_b):
        missing = [
            column
            for column in (elevation_column, azimuth_column)
            if column not in frame.columns
        ]
        if missing:
            raise ComparisonAlignmentError(
                f"Ephemeris table is missing columns: {', '.join(missing)}"
            )

    figure = go.Figure()
    for frame, name, color in (
        (frame_a, site_a_name, SITE_A_COLOR),
        (frame_b, site_b_name, SITE_B_COLOR),
    ):
        figure.add_trace(go.Scatter(
            x=times,
            y=frame[elevation_column],
            customdata=frame[[azimuth_column]],
            mode="lines+markers",
            name=name,
            line={"color": color, "width": 3},
            marker={"color": color, "size": 5},
            hovertemplate=(
                f"<b>{name}</b><br>%{{x|%Y-%m-%d %H:%M UTC}}<br>"
                f"{target_name} azimuth: %{{customdata[0]:.2f}}°<br>"
                "Elevation: %{y:+.2f}°<extra></extra>"
            ),
        ))

    figure.add_trace(go.Scatter(
        x=[times.iloc[0], times.iloc[-1]],
        y=[0, 0],
        mode="lines",
        name="Ideal horizon (0°)",
        line={"color": HORIZON_COLOR, "width": 1.5, "dash": "dash"},
        hoverinfo="skip",
    ))

    minimum = min(frame_a[elevation_column].min(), frame_b[elevation_column].min(), 0)
    maximum = max(frame_a[elevation_column].max(), frame_b[elevation_column].max(), 0)
    padding = max(1.0, (maximum - minimum) * 0.18)
    figure.update_layout(
        height=390,
        margin={"l": 12, "r": 12, "t": 48, "b": 12},
        title={"text": f"{target_name} elevation", "x": 0.02},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,17,31,0.35)",
        font={"color": "#F1F5FA", "family": "Inter, Segoe UI, sans-serif"},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "bgcolor": "rgba(7,17,31,0.55)",
        },
        xaxis={
            "title": "Time (UTC)",
            "gridcolor": "#294361",
            "linecolor": "#294361",
            "showspikes": True,
            "spikecolor": "#9FB0C5",
        },
        yaxis={
            "title": "Elevation (degrees)",
            "range": [max(-90, minimum - padding), min(90, maximum + padding)],
            "gridcolor": "#294361",
            "linecolor": "#294361",
            "zeroline": False,
        },
    )
    return figure
