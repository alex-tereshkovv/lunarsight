"""LunarSight v0.2 Mission Control dashboard."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from comparison import (
    ComparisonAlignmentError,
    comparison_elevation_chart,
    geometric_visibility_status,
    validate_matching_timestamps,
)
from ephemeris_export import build_ephemeris_export
from horizons import (
    EphemerisValidationError,
    HorizonsError,
    HorizonsResponseError,
    fetch_ephemeris,
    load_ephemeris_csv,
    validate_ephemeris,
)
from rover_component import solar_rover_simulation
from rover_planner import (
    CONNECTIONS,
    CONTINUOUS_EXPLORATION_ID,
    DYNAMIC_ROUTE_ID,
    SOURCE_NASA_CACHED,
    SOURCE_NASA_LIVE,
    SOURCE_SYNTHETIC,
    WAYPOINTS,
    assert_route_constraints,
    build_component_payload,
    build_synthetic_ephemerides,
    downsample_ephemeris,
    get_route_scenario,
    plan_continuous_exploration,
    plan_route,
)

ROOT = Path(__file__).resolve().parent
MIN_OBSERVATION_DATE = date(2000, 1, 1)
MAX_OBSERVATION_DATE = date(2100, 12, 31)
ROVER_CACHE_START_DATE = date(2026, 11, 14)
ROVER_CACHE_DURATION_DAYS = 7
LIVE_SOURCE = "Live NASA (Horizons)"
NASA_SOURCE_LABEL = "NASA JPL Horizons (Live)"
REFERENCE_SOURCE = "Reference Profile (Synthetic)"
REFERENCE_FALLBACK_SOURCE = "Reference Profile (Synthetic Fallback)"


def static_asset_url(filename: str, app_url: str | None = None) -> str:
    """Return a static URL that works locally and behind Community Cloud proxy."""
    if app_url is None:
        app_url = str(st.context.url or "")
    prefix = (
        "/~/+/app/static/assets"
        if ".streamlit.app" in app_url.lower()
        else "/app/static/assets"
    )
    return f"{prefix}/{filename}"

COLORS = {
    "background": "#07111F",
    "panel": "#101E32",
    "panel_secondary": "#17283F",
    "border": "#294361",
    "blue": "#42A5F5",
    "sun": "#FFC845",
    "earth": "#42B4FF",
    "success": "#26C281",
    "warning": "#EF5350",
    "text": "#F1F5FA",
    "muted": "#9FB0C5",
}

ICON_PATHS = {
    "settings": (
        '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21h-4v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3.1 14H3v-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3.1V3h4v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.5 1h.1v4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>'
    ),
    "metrics": '<path d="M4 20V10M10 20V4M16 20v-7M22 20V7"/>',
    "trend": '<path d="M3 18V5M3 18h18M6 14l4-4 3 2 6-7"/>',
    "target": '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    "compare": '<path d="M7 7h12l-3-3M19 17H7l3 3M19 7l-3 3M7 17l3-3"/>',
    "warning": '<path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v5M12 17h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "catalog": '<path d="M4 4h16v16H4zM4 10h16M10 4v16"/>',
    "moon": '<path d="M18.5 15.5A8 8 0 0 1 8.5 5.5a8 8 0 1 0 10 10Z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 1v3M12 20v3M1 12h3M20 12h3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M19.8 4.2l-2.1 2.1M6.3 17.7l-2.1 2.1"/>',
    "earth": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 2.5 4 5.5 4 9s-1 6.5-4 9c-3-2.5-4-5.5-4-9s1-6.5 4-9Z"/>',
    "overlap": '<circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/>',
}


def icon_svg(name: str, size: int = 22) -> str:
    """Return a small accessible-hidden outline icon matching the dashboard UI."""
    paths = ICON_PATHS.get(name, ICON_PATHS["info"])
    return (
        f'<span class="ui-icon" aria-hidden="true" style="width:{size}px;height:{size}px">'
        f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'{paths}</svg></span>'
    )


@st.cache_data
def load_sites() -> list[dict]:
    """Load the landing-site catalog."""
    with (ROOT / "sites.json").open(encoding="utf-8") as handle:
        return json.load(handle)["sites"]


@st.cache_data
def load_demo() -> pd.DataFrame:
    """Load validated, offline synthetic ephemerides."""
    return load_ephemeris_csv(str(ROOT / "data" / "demo_ephemeris.csv"))


@st.cache_data(ttl=3600, max_entries=24, show_spinner=False)
def load_live(
    latitude_deg: float,
    longitude_deg_east: float,
    start_date_iso: str,
    duration_hours: int,
) -> pd.DataFrame:
    """Fetch and cache successful Horizons responses for one hour."""
    start_utc = datetime.fromisoformat(start_date_iso).replace(tzinfo=timezone.utc)
    stop_utc = start_utc + timedelta(hours=duration_hours)
    try:
        return validate_ephemeris(fetch_ephemeris(
            latitude_deg,
            longitude_deg_east,
            start_utc,
            stop_utc,
        ))
    except EphemerisValidationError as error:
        raise HorizonsResponseError(
            f"Horizons data violates the LunarSight schema: {error}"
        ) from error


def rebase_demo(
    frame: pd.DataFrame,
    selected_date: date,
    duration_hours: int,
) -> pd.DataFrame:
    """Move the synthetic time profile to the selected UTC date."""
    result = frame.copy()
    offsets = result["time_utc"] - result["time_utc"].iloc[0]
    result["time_utc"] = pd.Timestamp(selected_date, tz="UTC") + offsets
    end = result["time_utc"].iloc[0] + pd.Timedelta(hours=duration_hours)
    return result[result["time_utc"] <= end].reset_index(drop=True)


def format_latitude(value: float) -> str:
    hemisphere = "N" if value >= 0 else "S"
    return f"{abs(value):.2f}° {hemisphere}"


def format_longitude(value: float) -> str:
    return f"{value % 360:.2f}° E"


def format_timestamp(value: pd.Timestamp) -> str:
    return value.strftime("%Y-%m-%d %H:%M UTC")


def sampling_interval(frame: pd.DataFrame) -> str:
    if len(frame) < 2:
        return "n/a"
    hours = frame["time_utc"].diff().dropna().median().total_seconds() / 3600
    if hours.is_integer():
        return f"{int(hours)} hour step"
    return f"{hours:.1f} hour step"


def elevation_chart(frame: pd.DataFrame) -> go.Figure:
    """Build the combined Sun/Earth elevation chart."""
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=frame["time_utc"],
        y=frame["sun_el"],
        customdata=frame[["sun_az"]],
        mode="lines+markers",
        name="Sun",
        line={"color": COLORS["sun"], "width": 3},
        marker={"size": 5, "color": COLORS["sun"]},
        hovertemplate=(
            "<b>Sun</b><br>%{x|%Y-%m-%d %H:%M UTC}<br>"
            "Azimuth: %{customdata[0]:.2f}°<br>"
            "Elevation: %{y:+.2f}°<extra></extra>"
        ),
    ))
    figure.add_trace(go.Scatter(
        x=frame["time_utc"],
        y=frame["earth_el"],
        customdata=frame[["earth_az"]],
        mode="lines+markers",
        name="Earth",
        line={"color": COLORS["earth"], "width": 3},
        marker={"size": 5, "color": COLORS["earth"]},
        hovertemplate=(
            "<b>Earth</b><br>%{x|%Y-%m-%d %H:%M UTC}<br>"
            "Azimuth: %{customdata[0]:.2f}°<br>"
            "Elevation: %{y:+.2f}°<extra></extra>"
        ),
    ))
    figure.add_trace(go.Scatter(
        x=[frame["time_utc"].iloc[0], frame["time_utc"].iloc[-1]],
        y=[0, 0],
        mode="lines",
        name="Ideal Horizon (0°)",
        line={"color": "#D7E3F4", "width": 1.5, "dash": "dash"},
        hoverinfo="skip",
    ))

    minimum = min(frame["sun_el"].min(), frame["earth_el"].min(), 0)
    maximum = max(frame["sun_el"].max(), frame["earth_el"].max(), 0)
    padding = max(1.0, (maximum - minimum) * 0.18)
    figure.update_layout(
        height=390,
        margin={"l": 10, "r": 10, "t": 12, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,17,31,0.35)",
        font={"color": COLORS["text"], "family": "Inter, Segoe UI, sans-serif"},
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


def direction_chart(row: pd.Series) -> go.Figure:
    """Plot physically meaningful azimuth and zenith distance."""
    horizon_theta = list(range(0, 361, 5))
    figure = go.Figure()
    figure.add_trace(go.Scatterpolar(
        theta=horizon_theta,
        r=[90] * len(horizon_theta),
        mode="lines",
        name="Ideal Horizon",
        line={"color": "#89A1BC", "width": 1, "dash": "dot"},
        hoverinfo="skip",
    ))
    figure.add_trace(go.Scatterpolar(
        theta=[row["sun_az"]],
        r=[90 - row["sun_el"]],
        mode="markers",
        name="Sun",
        marker={
            "color": COLORS["sun"],
            "size": 18,
            "line": {"color": "#FFF3B8", "width": 2},
        },
        customdata=[[row["sun_el"]]],
        hovertemplate=(
            "<b>Sun</b><br>Azimuth: %{theta:.2f}°<br>"
            "Elevation: %{customdata[0]:+.2f}°<extra></extra>"
        ),
    ))
    figure.add_trace(go.Scatterpolar(
        theta=[row["earth_az"]],
        r=[90 - row["earth_el"]],
        mode="markers",
        name="Earth",
        marker={
            "color": COLORS["earth"],
            "size": 18,
            "line": {"color": "#C6ECFF", "width": 2},
        },
        customdata=[[row["earth_el"]]],
        hovertemplate=(
            "<b>Earth</b><br>Azimuth: %{theta:.2f}°<br>"
            "Elevation: %{customdata[0]:+.2f}°<extra></extra>"
        ),
    ))
    figure.update_layout(
        height=330,
        margin={"l": 30, "r": 30, "t": 30, "b": 25},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COLORS["text"], "family": "Inter, Segoe UI, sans-serif"},
        showlegend=False,
        polar={
            "bgcolor": "rgba(7,17,31,0.4)",
            "angularaxis": {
                "direction": "clockwise",
                "rotation": 90,
                "tickmode": "array",
                "tickvals": [0, 90, 180, 270],
                "ticktext": ["N · 0°", "E · 90°", "S · 180°", "W · 270°"],
                "tickfont": {"size": 13},
                "gridcolor": "#365572",
                "linecolor": "#5F7893",
            },
            "radialaxis": {
                "range": [0, 180],
                "tickmode": "array",
                "tickvals": [0, 90, 180],
                "ticktext": ["Zenith", "Horizon", "Nadir"],
                "gridcolor": "#365572",
                "linecolor": "#5F7893",
                "angle": 45,
                "tickfont": {"size": 11},
            },
        },
    )
    return figure


def render_header(title: str, subtitle: str, *, compact: bool = False) -> None:
    hero_class = "mission-hero compact" if compact else "mission-hero"
    st.markdown(
        f"""
        <section class="{hero_class}">
          <div>
            <div class="eyebrow">MISSION CONTROL · LUNAR SOUTH POLE</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div class="hero-status">
            <div class="provider-row">
              <span class="provider-mark">JPL</span>
              <div>
                <div class="provider">NASA JPL Horizons</div>
                <div class="provider-subtitle">Ephemerides · live mode data source</div>
              </div>
              <span class="version-badge">LunarSight v0.2</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def section_title(icon: str, title: str, detail: str | None = None) -> None:
    suffix = f"<span>{detail}</span>" if detail else ""
    st.markdown(
        f'<div class="section-heading"><b>{icon_svg(icon, 20)}{title}</b>{suffix}</div>',
        unsafe_allow_html=True,
    )


def direction_details(name: str, azimuth: float, elevation: float, css_class: str) -> str:
    status, status_class = geometric_visibility_status(elevation)
    icon = "sun" if name == "Sun" else "earth"
    return f"""
    <div class="direction-card {css_class}">
      <div class="direction-name">{icon_svg(icon, 24)}{name}</div>
      <div>Azimuth <b>{azimuth:.2f}°</b></div>
      <div>Elevation <b>{elevation:+.2f}°</b></div>
      <span class="visibility-pill {status_class}">{status}</span>
    </div>
    """


def site_details(site: dict) -> None:
    st.caption(
        f"{format_latitude(site['latitude_deg'])} · "
        f"{format_longitude(site['longitude_deg_east'])}"
    )
    st.caption(site["scientific_source"])


def comparison_status_card(
    body_name: str,
    row: pd.Series,
    *,
    azimuth_column: str,
    elevation_column: str,
    css_class: str,
) -> str:
    """Render an instantaneous geometric visibility card for one celestial body."""
    elevation = float(row[elevation_column])
    status, status_class = geometric_visibility_status(elevation)
    icon = "sun" if body_name == "Sun" else "earth"
    return f"""
    <div class="direction-card {css_class}">
      <div class="direction-name">{icon_svg(icon, 24)}{body_name}</div>
      <div>Azimuth <b>{float(row[azimuth_column]):.2f}°</b></div>
      <div>Elevation <b>{elevation:+.2f}°</b></div>
      <span class="visibility-pill {status_class}">{status}</span>
    </div>
    """


def load_live_site_pair(
    site_a: dict,
    site_b: dict,
    selected_date: date,
    duration: int,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, str | None]:
    """Load aligned live ephemerides without falling back to mixed data sources."""
    frames: list[pd.DataFrame] = []
    for label, site in (("Site A", site_a), ("Site B", site_b)):
        try:
            frame = load_live(
                site["latitude_deg"],
                site["longitude_deg_east"],
                selected_date.isoformat(),
                duration,
            )
        except HorizonsError as error:
            return None, None, f"{label} ({site['name']}) failed: {error}"
        frames.append(frame)

    try:
        validate_matching_timestamps(frames[0], frames[1])
    except ComparisonAlignmentError as error:
        return None, None, str(error)
    return frames[0], frames[1], None


def open_full_site_comparison() -> None:
    """Carry compact selections into the full comparison page."""
    st.session_state["comparison_site_a"] = st.session_state[
        "mission_preview_site_a"
    ]
    st.session_state["comparison_site_b"] = st.session_state[
        "mission_preview_site_b"
    ]
    st.session_state["navigation"] = "Site Comparison"


def swap_mission_preview_sites() -> None:
    """Swap the two dashboard preview selectors without requesting ephemerides."""
    site_a = st.session_state.get("mission_preview_site_a")
    site_b = st.session_state.get("mission_preview_site_b")
    if site_a is not None and site_b is not None:
        st.session_state["mission_preview_site_a"] = site_b
        st.session_state["mission_preview_site_b"] = site_a


def render_embedded_site_comparison(sites: list[dict]) -> None:
    """Keep Mission Control's compact comparison preview free of API calls."""
    with st.container(border=True):
        section_title("compare", "Site Comparison")
        left, middle, right, action = st.columns([1, 0.12, 1, 0.72])
        with left:
            site_a_name = st.selectbox(
                "Site A",
                [site["name"] for site in sites],
                key="mission_preview_site_a",
            )
            site_a = next(site for site in sites if site["name"] == site_a_name)
            st.caption(
                f"{format_latitude(site_a['latitude_deg'])} · "
                f"{format_longitude(site_a['longitude_deg_east'])}"
            )
        with middle:
            st.markdown('<div class="comparison-swap-spacer"></div>', unsafe_allow_html=True)
            st.button(
                "Swap sites",
                key="swap_mission_preview_sites",
                icon=":material/swap_horiz:",
                help="Swap Site A and Site B",
                width="stretch",
                on_click=swap_mission_preview_sites,
            )
        with right:
            site_b_name = st.selectbox(
                "Site B",
                [site["name"] for site in sites],
                index=min(1, len(sites) - 1),
                key="mission_preview_site_b",
            )
            site_b = next(site for site in sites if site["name"] == site_b_name)
            st.caption(
                f"{format_latitude(site_b['latitude_deg'])} · "
                f"{format_longitude(site_b['longitude_deg_east'])}"
            )
        with action:
            st.markdown('<div class="comparison-action-spacer"></div>', unsafe_allow_html=True)
            st.button(
                "Compare Sites",
                key="compare_sites_from_mission",
                icon=":material/analytics:",
                width="stretch",
                on_click=open_full_site_comparison,
            )


def render_live_comparison_result(result: dict) -> None:
    """Render aligned live comparison charts and instantaneous visibility."""
    site_a = result["site_a"]
    site_b = result["site_b"]
    frame_a = result["frame_a"]
    frame_b = result["frame_b"]
    signature = result["signature"]
    period = (
        f"{format_timestamp(frame_a['time_utc'].iloc[0])} — "
        f"{format_timestamp(frame_a['time_utc'].iloc[-1])}"
    )

    st.markdown(
        '<div class="source-banner source-live">'
        '<b>Data Source:</b> NASA JPL Horizons (Live)'
        f'<span>{period} · {len(frame_a)} matched samples · '
        f'{sampling_interval(frame_a)}</span></div>',
        unsafe_allow_html=True,
    )

    coordinate_columns = st.columns(2)
    for column, label, site in (
        (coordinate_columns[0], "Site A", site_a),
        (coordinate_columns[1], "Site B", site_b),
    ):
        with column:
            with st.container(border=True):
                st.markdown(f"#### {label} · {site['name']}")
                st.caption(
                    f"{format_latitude(site['latitude_deg'])} · "
                    f"{format_longitude(site['longitude_deg_east'])}"
                )
                st.caption(site["scientific_source"])

    chart_columns = st.columns(2)
    with chart_columns[0]:
        with st.container(border=True):
            st.plotly_chart(
                comparison_elevation_chart(
                    frame_a,
                    frame_b,
                    elevation_column="sun_el",
                    azimuth_column="sun_az",
                    target_name="Sun",
                    site_a_name=site_a["name"],
                    site_b_name=site_b["name"],
                ),
                key=f"comparison_sun_{signature}",
                width="stretch",
                config={"displaylogo": False, "scrollZoom": False},
                alt="Sun elevation at Site A and Site B over the shared UTC period",
            )
    with chart_columns[1]:
        with st.container(border=True):
            st.plotly_chart(
                comparison_elevation_chart(
                    frame_a,
                    frame_b,
                    elevation_column="earth_el",
                    azimuth_column="earth_az",
                    target_name="Earth",
                    site_a_name=site_a["name"],
                    site_b_name=site_b["name"],
                ),
                key=f"comparison_earth_{signature}",
                width="stretch",
                config={"displaylogo": False, "scrollZoom": False},
                alt="Earth elevation at Site A and Site B over the shared UTC period",
            )

    with st.container(border=True):
        section_title("target", "Geometric Visibility at Selected Time")
        default_time = frame_a["time_utc"].iloc[len(frame_a) // 2]
        selected_time = st.select_slider(
            "Observation Time (UTC)",
            options=frame_a["time_utc"].tolist(),
            value=default_time,
            format_func=format_timestamp,
            key=f"comparison_time_{signature}",
        )
        row_a = frame_a.loc[frame_a["time_utc"] == selected_time].iloc[0]
        row_b = frame_b.loc[frame_b["time_utc"] == selected_time].iloc[0]
        site_columns = st.columns(2)
        for column, label, site, row in (
            (site_columns[0], "Site A", site_a, row_a),
            (site_columns[1], "Site B", site_b, row_b),
        ):
            with column:
                st.markdown(f"#### {label} · {site['name']}")
                body_columns = st.columns(2)
                with body_columns[0]:
                    st.markdown(
                        comparison_status_card(
                            "Sun",
                            row,
                            azimuth_column="sun_az",
                            elevation_column="sun_el",
                            css_class="sun",
                        ),
                        unsafe_allow_html=True,
                    )
                with body_columns[1]:
                    st.markdown(
                        comparison_status_card(
                            "Earth",
                            row,
                            azimuth_column="earth_az",
                            elevation_column="earth_el",
                            css_class="earth",
                        ),
                        unsafe_allow_html=True,
                    )

        st.caption(
            "Instantaneous geometric elevation relative to an ideal local horizon. "
            "Terrain masking, illumination duration, and communications link quality "
            "are outside this comparison."
        )


def render_site_comparison(sites: list[dict], embedded: bool = False) -> None:
    if embedded:
        render_embedded_site_comparison(sites)
        return

    render_header(
        "Landing Site Comparison",
        "Compare matched Sun and Earth geometry for two lunar surface observers.",
    )
    with st.form("site_comparison_configuration", border=True):
        section_title("settings", "Comparison Configuration", "One shared UTC period")
        site_a_col, site_b_col, date_col, duration_col, source_col = st.columns(
            [1.25, 1.25, 1, 0.8, 1.2]
        )
        with site_a_col:
            site_a_name = st.selectbox(
                "Landing Site A",
                [site["name"] for site in sites],
                key="comparison_site_a",
            )
            site_a = next(site for site in sites if site["name"] == site_a_name)
            st.caption(
                f"{format_latitude(site_a['latitude_deg'])} · "
                f"{format_longitude(site_a['longitude_deg_east'])}"
            )
        with site_b_col:
            site_b_name = st.selectbox(
                "Landing Site B",
                [site["name"] for site in sites],
                index=min(1, len(sites) - 1),
                key="comparison_site_b",
            )
            site_b = next(site for site in sites if site["name"] == site_b_name)
            st.caption(
                f"{format_latitude(site_b['latitude_deg'])} · "
                f"{format_longitude(site_b['longitude_deg_east'])}"
            )
        with date_col:
            selected_date = st.date_input(
                "Start Date (UTC)",
                value=date.today(),
                min_value=MIN_OBSERVATION_DATE,
                max_value=MAX_OBSERVATION_DATE,
                key="comparison_date",
            )
        with duration_col:
            duration = st.selectbox(
                "Duration",
                [24, 48, 72],
                index=1,
                format_func=lambda hours: f"{hours} hours",
                key="comparison_duration",
            )
        with source_col:
            data_source = st.selectbox(
                "Data Source",
                [LIVE_SOURCE, REFERENCE_SOURCE],
                key="comparison_source",
            )
        submitted = st.form_submit_button(
            "Run Site Comparison",
            type="primary",
            icon=":material/compare_arrows:",
            width="stretch",
        )

    result_key = "site_comparison_result"
    error_key = "site_comparison_error"
    if submitted:
        st.session_state.pop(result_key, None)
        st.session_state.pop(error_key, None)
        if site_a["id"] == site_b["id"]:
            st.session_state[error_key] = (
                "Select two different landing sites before requesting a comparison."
            )
        elif data_source == REFERENCE_SOURCE:
            st.session_state[result_key] = {
                "source": data_source,
                "site_a": site_a,
                "site_b": site_b,
                "selected_date": selected_date,
                "duration": duration,
            }
        else:
            with st.spinner(
                "Requesting matched ephemerides for Site A and Site B from NASA JPL Horizons..."
            ):
                frame_a, frame_b, error = load_live_site_pair(
                    site_a,
                    site_b,
                    selected_date,
                    duration,
                )
            if error:
                st.session_state[error_key] = error
            else:
                signature = (
                    f"{site_a['id']}_{site_b['id']}_"
                    f"{selected_date.isoformat()}_{duration}h"
                )
                st.session_state[result_key] = {
                    "source": "NASA JPL Horizons (Live)",
                    "site_a": site_a,
                    "site_b": site_b,
                    "selected_date": selected_date,
                    "duration": duration,
                    "frame_a": frame_a,
                    "frame_b": frame_b,
                    "signature": signature,
                }

    comparison_error = st.session_state.get(error_key)
    comparison_result = st.session_state.get(result_key)
    if comparison_error:
        st.error(f"Site comparison unavailable: {comparison_error}")
        st.info(
            "No partial result is shown, and LunarSight did not substitute synthetic "
            "data for either site."
        )
    elif comparison_result is None:
        st.info(
            "Choose two sites and run the comparison. Live requests are cached, and "
            "changing the observation-time slider will not call NASA again."
        )
    elif comparison_result["source"] == REFERENCE_SOURCE:
        with st.container(border=True):
            section_title("warning", "Reference Profile Comparison Disabled")
            st.warning(
                "The bundled reference profile is one shared synthetic trajectory and is not "
                "site-specific. Plotting it for both locations would imply a false "
                "scientific comparison, so comparison charts are disabled for this source."
            )
            demo_columns = st.columns(2)
            for column, label, site in (
                (demo_columns[0], "Site A", comparison_result["site_a"]),
                (demo_columns[1], "Site B", comparison_result["site_b"]),
            ):
                with column:
                    st.markdown(f"#### {label} · {site['name']}")
                    site_details(site)
    else:
        render_live_comparison_result(comparison_result)


def render_scientific_notes() -> None:
    with st.container(border=True):
        section_title("info", "Scientific Notes & Limitations")
        st.markdown(
            """
            <ul class="science-notes">
              <li>Positive Sun elevation is geometric visibility, not guaranteed illumination;
              local terrain and shadowing are not modeled.</li>
              <li>Geometric Earth visibility does not guarantee reliable radio communication.</li>
              <li>Elevation refers to the center of the observed celestial body.</li>
              <li>Catalog coordinates are NASA-published representative traverse stations,
              not validated landing sites or terrain-safe route points.</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )


def render_data_sources(sites: list[dict]) -> None:
    render_header(
        "Data & Sources",
        "Trace the origin, schema, and limitations of LunarSight mission data.",
    )
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            section_title("earth", "Live NASA Data")
            st.write(
                "NASA JPL Horizons observer tables provide apparent topocentric "
                "azimuth and elevation for the Sun and Earth."
            )
            st.markdown(
                "[Open official Horizons API documentation]"
                "(https://ssd-api.jpl.nasa.gov/doc/horizons.html)"
            )
            st.code(
                "Observer: coord@301\n"
                "Coordinates: geodetic east longitude, latitude, height (km)\n"
                "Time scale: UT / UTC+00:00\n"
                "Angles: degrees, airless apparent azimuth/elevation"
            )
    with right:
        with st.container(border=True):
            section_title("database", "Offline Reference Profile")
            st.write(
                "The bundled CSV is an explicitly synthetic reference profile that keeps the dashboard "
                "functional without network access."
            )
            st.code("time_utc, sun_az, sun_el, earth_az, earth_el")
            st.warning("Synthetic data must not be used for scientific conclusions.")

    with st.container(border=True):
        section_title("catalog", "Landing Site Catalog")
        catalog = pd.DataFrame([{
            "Site": site["name"],
            "Latitude": format_latitude(site["latitude_deg"]),
            "Longitude": format_longitude(site["longitude_deg_east"]),
            "NASA-published station": site["verified"],
            "Source": site["scientific_source"],
        } for site in sites])
        st.dataframe(
            catalog,
            hide_index=True,
            width="stretch",
            alt="NASA-published station coordinates and scientific source",
        )


def render_about() -> None:
    render_header(
        "About LunarSight",
        "A scientifically honest mission-planning prototype for the lunar south pole.",
    )
    with st.container(border=True):
        section_title("moon", "Project Mission")
        st.write(
            "LunarSight helps teams explore geometric Sun and Earth visibility for "
            "candidate lunar landing coordinates. It is a hackathon "
            "prototype, not a flight-certified mission design system."
        )
        st.markdown(
            """
            **Current capabilities**

            - Offline reference profile (explicitly synthetic)
            - Live NASA JPL Horizons ephemerides
            - Interactive elevation and direction visualizations
            - CSV export of the currently displayed ephemeris table

            **Not currently modeled**

            - Local topography and shadowing
            - Landing hazards and surface slope
            - Communications link budgets
            - Operational safety margins
            """
        )


def load_demo_for_period(
    selected_date: date,
    duration: int,
) -> tuple[pd.DataFrame | None, str | None]:
    """Load the bundled demo safely and report validation or filesystem failures."""
    try:
        return rebase_demo(load_demo(), selected_date, duration), None
    except (
        EphemerisValidationError,
        OSError,
        UnicodeError,
        pd.errors.ParserError,
    ) as error:
        return None, f"Bundled synthetic demo data is unavailable: {error}"


def fetch_selected_data(
    data_source: str,
    site: dict,
    selected_date: date,
    duration: int,
) -> tuple[pd.DataFrame | None, str, str | None]:
    """Return selected data, actual source label, and any fallback error."""
    if data_source == LIVE_SOURCE:
        try:
            with st.spinner(
                "Requesting Sun and Earth ephemerides from NASA JPL Horizons..."
            ):
                frame = load_live(
                    site["latitude_deg"],
                    site["longitude_deg_east"],
                    selected_date.isoformat(),
                    duration,
                )
            return frame, NASA_SOURCE_LABEL, None
        except HorizonsError as error:
            frame, demo_error = load_demo_for_period(selected_date, duration)
            if demo_error:
                return None, "Unavailable", f"{error}; {demo_error}"
            return frame, REFERENCE_FALLBACK_SOURCE, str(error)
    frame, demo_error = load_demo_for_period(selected_date, duration)
    if demo_error:
        return None, "Unavailable", demo_error
    return frame, REFERENCE_SOURCE, None


def build_rover_ephemerides(
    selected_date: date,
    duration_days: int,
    data_source: str,
) -> dict[str, pd.DataFrame]:
    """Load one aligned ephemeris table per verified NASA station."""
    frames: dict[str, pd.DataFrame] = {}
    if data_source == SOURCE_SYNTHETIC:
        return {
            waypoint.id: build_synthetic_ephemerides(
                waypoint,
                selected_date,
                duration_days,
                step_hours=3,
            )
            for waypoint in WAYPOINTS
        }
    if data_source == SOURCE_NASA_CACHED:
        if (
            selected_date != ROVER_CACHE_START_DATE
            or duration_days != ROVER_CACHE_DURATION_DAYS
        ):
            raise ValueError(
                "The bundled NASA cache is available only for 2026-11-14 UTC "
                "and a 7-day observation period."
            )
        return {
            waypoint.id: load_ephemeris_csv(
                str(ROOT / "data" / "rover_nasa_cache" / f"{waypoint.id}.csv")
            )
            for waypoint in WAYPOINTS
        }

    for waypoint in WAYPOINTS:
        try:
            hourly = load_live(
                waypoint.latitude_deg,
                waypoint.longitude_deg_east,
                selected_date.isoformat(),
                duration_days * 24,
            )
            frames[waypoint.id] = downsample_ephemeris(hourly, step_hours=3)
        except HorizonsError as error:
            raise HorizonsResponseError(
                f"{waypoint.id} ({format_latitude(waypoint.latitude_deg)}, "
                f"{format_longitude(waypoint.longitude_deg_east)}) failed: {error}"
            ) from error
    return frames


def render_solar_rover_planner() -> None:
    """Render the synchronized NASA-station rover scenario."""
    render_header(
        "Solar Rover Planner",
        "Conceptual mobility playback with verified stations and geometric Sun/Earth visibility.",
        compact=True,
    )

    with st.form("rover_configuration", border=True):
        date_col, duration_col, route_col, source_col, speed_col, action_col = st.columns(
            [1.05, 0.72, 1.35, 1.15, 0.8, 0.9], vertical_alignment="bottom"
        )
        with date_col:
            selected_date = st.date_input(
                "Start Date (UTC)",
                value=ROVER_CACHE_START_DATE,
                min_value=MIN_OBSERVATION_DATE,
                max_value=MAX_OBSERVATION_DATE,
                key="rover_start_date",
            )
        with duration_col:
            duration_days = st.selectbox(
                "Period",
                [7, 14, 28, 60],
                format_func=lambda value: f"{value} days",
                key="rover_duration_days",
            )
        with route_col:
            route_id = st.selectbox(
                "Planning Mode",
                [DYNAMIC_ROUTE_ID, CONTINUOUS_EXPLORATION_ID],
                index=0,
                format_func=lambda value: get_route_scenario(value).label,
                key="rover_route",
                help=(
                    "Visibility Optimization evaluates real ephemerides. Continuous "
                    "Exploration is a conceptual closed playback route. "
                    "All graph links are conceptual, not terrain-validated."
                ),
            )
        with source_col:
            data_source = st.selectbox(
                "Ephemerides",
                [SOURCE_NASA_CACHED, SOURCE_NASA_LIVE],
                key="rover_data_source",
                help=(
                    "Cached mode is a fixed, real Horizons dataset. Live mode never "
                    "substitutes synthetic values."
                ),
            )
        with speed_col:
            rover_speed = st.selectbox(
                "Speed Cap",
                [0.1, 0.2, 0.5],
                index=1,
                format_func=lambda value: f"{value:.1f} km/h",
                key="rover_speed",
            )
        with action_col:
            submitted = st.form_submit_button(
                "Build Plan",
                type="primary",
                icon=":material/route:",
                width="stretch",
            )

    requested_config = (
        selected_date.isoformat(),
        duration_days,
        route_id,
        data_source,
        rover_speed,
    )
    stored_plan = st.session_state.get("rover_plan")
    should_build = submitted or stored_plan is None

    if should_build:
        fallback_note: str | None = None
        try:
            if data_source == SOURCE_NASA_LIVE:
                with st.spinner(
                    "Requesting Horizons ephemerides for seven verified NASA stations..."
                ):
                    try:
                        frames = build_rover_ephemerides(
                            selected_date,
                            duration_days,
                            data_source,
                        )
                        actual_source = SOURCE_NASA_LIVE
                    except HorizonsError as live_error:
                        if (
                            selected_date != ROVER_CACHE_START_DATE
                            or duration_days != ROVER_CACHE_DURATION_DAYS
                        ):
                            raise
                        frames = build_rover_ephemerides(
                            selected_date,
                            duration_days,
                            SOURCE_NASA_CACHED,
                        )
                        actual_source = SOURCE_NASA_CACHED
                        fallback_note = (
                            "Live Horizons request failed; the planner is explicitly "
                            f"showing the fixed real-NASA cache instead: {live_error}"
                        )
            else:
                frames = build_rover_ephemerides(
                    selected_date,
                    duration_days,
                    data_source,
                )
                actual_source = SOURCE_NASA_CACHED
            scenario = get_route_scenario(route_id)
            route_connections = CONNECTIONS
            segments = (
                plan_continuous_exploration(
                    frames,
                    rover_speed_kmh=rover_speed,
                    connections=route_connections,
                )
                if route_id == CONTINUOUS_EXPLORATION_ID
                else plan_route(
                    frames,
                    rover_speed_kmh=rover_speed,
                    connections=route_connections,
                    start_waypoint_id=scenario.station_ids[0],
                )
            )
            assert_route_constraints(
                segments,
                rover_speed_kmh=rover_speed,
                connections=route_connections,
            )
            st.session_state["rover_plan"] = {
                "config": requested_config,
                "frames": frames,
                "segments": segments,
                "source_label": actual_source,
                "fallback_note": fallback_note,
            }
            stored_plan = st.session_state["rover_plan"]
        except (HorizonsError, EphemerisValidationError, ValueError) as error:
            st.session_state.pop("rover_plan", None)
            st.error(
                f"Rover scenario could not be built: {error}",
                icon=":material/error:",
            )
            st.info(
                "No synthetic ephemerides were substituted. Choose the bundled "
                "NASA cache for the fixed 2026-11-14 seven-day period.",
            )
            return

    if stored_plan is None:
        return
    if stored_plan["config"] != requested_config:
        st.info(
            "The visualization still shows the last completed scenario. Select "
            "Build Mission Plan to apply the configuration above."
        )

    source_label = stored_plan["source_label"]
    scenario = get_route_scenario(stored_plan["config"][2])
    route_connections = CONNECTIONS
    payload = build_component_payload(
        stored_plan["frames"],
        stored_plan["segments"],
        source_label=source_label,
        rover_speed_kmh=stored_plan["config"][4],
        map_url=static_asset_url("lola-shackleton-hillshade.webp"),
        overview_url=static_asset_url("shackleton-lroc.png"),
        route_scenario=scenario,
        connections=route_connections,
    )
    solar_rover_simulation(payload)
    if stored_plan.get("fallback_note"):
        st.warning(
            stored_plan["fallback_note"],
            icon=":material/cloud_off:",
        )
    mode_note = (
        "CONCEPTUAL MODE — cyclic station exploration; no optimality or "
        "terrain-safety claim."
        if scenario.id == CONTINUOUS_EXPLORATION_ID
        else "SCIENTIFIC MODE — movement decisions use geometric Horizons visibility."
    )
    st.caption(
        f"{source_label} · published NASA stations · east-positive longitude · "
        f"{mode_note} Graph links are not validated traverses."
    )


def render_mission_control(sites: list[dict]) -> None:
    render_header(
        "Lunar Landing Site Analysis",
        "Geometric Sun and Earth visibility for lunar surface operations.",
    )

    with st.container(border=True):
        section_title("settings", "Mission Configuration")
        site_col, date_col, duration_col, source_col, action_col = st.columns(
            [1.55, 1.05, 0.9, 1.35, 0.9]
        )
        with site_col:
            site_name = st.selectbox(
                "Landing Site",
                [site["name"] for site in sites],
                key="mission_site",
            )
            site = next(item for item in sites if item["name"] == site_name)
            st.caption(
                f"{format_latitude(site['latitude_deg'])} · "
                f"{format_longitude(site['longitude_deg_east'])}"
            )
        with date_col:
            selected_date = st.date_input(
                "Start Date (UTC)",
                value=date.today(),
                min_value=MIN_OBSERVATION_DATE,
                max_value=MAX_OBSERVATION_DATE,
                key="mission_date",
            )
        with duration_col:
            duration = st.selectbox(
                "Duration",
                [24, 48, 72],
                index=1,
                format_func=lambda hours: f"{hours} hours",
                key="mission_duration",
            )
        with source_col:
            data_source = st.segmented_control(
                "Data Source",
                [REFERENCE_SOURCE, LIVE_SOURCE],
                default=REFERENCE_SOURCE,
                required=True,
                format_func=lambda source: (
                    "Synthetic Reference" if source == REFERENCE_SOURCE else "Live NASA"
                ),
                key="mission_source",
                width="stretch",
            )
        with action_col:
            st.markdown('<div class="run-spacer"></div>', unsafe_allow_html=True)
            run_analysis = st.button(
                "Run Analysis",
                key="run_analysis",
                type="primary",
                icon=":material/play_arrow:",
                width="stretch",
            )
        if run_analysis:
            st.toast("Mission configuration applied.")

    frame, actual_source, live_error = fetch_selected_data(
        data_source,
        site,
        selected_date,
        duration,
    )

    if frame is None:
        st.error(f"Ephemeris data unavailable: {live_error}")
        st.info(
            "No charts, visibility indicators, or CSV export are shown because "
            "LunarSight has no validated ephemeris samples."
        )
        return

    if live_error:
        st.error(f"Live Horizons request failed: {live_error}")
        st.info("The dashboard switched to the clearly labeled synthetic reference profile.")

    source_class = "source-live" if actual_source.startswith("NASA") else "source-demo"

    chart_column, direction_column = st.columns([1.45, 1.35])
    with chart_column:
        with st.container(border=True):
            section_title("trend", "Sun & Earth Elevation")
            st.plotly_chart(
                elevation_chart(frame),
                key="elevation_chart",
                width="stretch",
                config={"displaylogo": False, "scrollZoom": False},
                alt="Sun and Earth elevation relative to the ideal local horizon over UTC",
            )

    with direction_column:
        with st.container(border=True):
            default_time = frame["time_utc"].iloc[len(frame) // 2]
            section_title("target", "Current Direction", "Interactive UTC geometry")
            selected_time = st.select_slider(
                "Observation Time (UTC)",
                options=frame["time_utc"].tolist(),
                value=default_time,
                format_func=format_timestamp,
                key="mission_observation_time",
            )
            selected_row = frame.loc[frame["time_utc"] == selected_time].iloc[0]
            direction_visual, direction_data = st.columns([1.25, 1])
            with direction_visual:
                st.plotly_chart(
                    direction_chart(selected_row),
                    key="direction_chart",
                    width="stretch",
                    config={"displayModeBar": False, "displaylogo": False},
                    alt="Current Sun and Earth azimuth and elevation around the lunar observer",
                )
            with direction_data:
                st.markdown(
                    direction_details(
                        "Sun",
                        selected_row["sun_az"],
                        selected_row["sun_el"],
                        "sun",
                    ),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    direction_details(
                        "Earth",
                        selected_row["earth_az"],
                        selected_row["earth_el"],
                        "earth",
                    ),
                    unsafe_allow_html=True,
                )

    comparison_column, notes_column = st.columns([1.35, 1])
    with comparison_column:
        render_site_comparison(sites, embedded=True)
    with notes_column:
        render_scientific_notes()

    period_start = format_timestamp(frame["time_utc"].iloc[0])
    period_end = format_timestamp(frame["time_utc"].iloc[-1])
    st.markdown(
        f"""
        <div class="status-bar">
          <span><i class="{source_class}"></i><b>Data Source:</b> {actual_source}</span>
          <span><b>Period:</b> {period_start} — {period_end}</span>
          <span><b>Samples:</b> {len(frame)} ({sampling_interval(frame)})</span>
          <span><b>Observer:</b> Lunar Surface, {format_latitude(site['latitude_deg'])},
          {format_longitude(site['longitude_deg_east'])}</span>
          <a href="https://ssd-api.jpl.nasa.gov/doc/horizons.html" target="_blank">
          Source Details ↗</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Observation Data Table"):
        st.dataframe(
            frame,
            width="stretch",
            hide_index=True,
            alt="Displayed UTC Sun and Earth ephemeris samples",
        )
        # Keep rolling Streamlit Cloud deployments compatible with a worker that
        # has not re-imported ephemeris_export.py yet. The filename provenance is
        # unchanged: both compatibility labels resolve to SYNTHETIC_DEMO.
        export_source = {
            REFERENCE_SOURCE: "Demo (Synthetic)",
            REFERENCE_FALLBACK_SOURCE: "Demo (Fallback)",
        }.get(actual_source, actual_source)
        export = build_ephemeris_export(
            frame,
            data_source=export_source,
            site_id=site["id"],
            start_date=selected_date,
            duration_hours=duration,
        )
        st.download_button(
            "Download Ephemeris CSV",
            data=export.data,
            file_name=export.filename,
            mime=export.mime_type,
            key="download_ephemeris_csv",
            help="Export the exact ephemeris table displayed above.",
            on_click="ignore",
            type="primary",
            icon=":material/download:",
            width="stretch",
        )


st.set_page_config(
    page_title="LunarSight Mission Control",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
)

dashboard_styles = """
    <style>
    :root {
      --bg: #07111F;
      --panel: #101E32;
      --panel-2: #17283F;
      --border: #294361;
      --blue: #42A5F5;
      --sun: #FFC845;
      --earth: #42B4FF;
      --success: #26C281;
      --warning: #EF5350;
      --text: #F1F5FA;
      --muted: #9FB0C5;
    }
    .stApp {
      background:
        radial-gradient(circle at 82% 8%, rgba(66,165,245,.16) 0 1px, transparent 2px),
        radial-gradient(circle at 68% 18%, rgba(255,255,255,.13) 0 1px, transparent 2px),
        linear-gradient(145deg, #050c17 0%, #071421 48%, #030914 100%);
      color: var(--text);
    }
    [data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none; }
    [data-testid="stMainBlockContainer"] {
      max-width: 1600px;
      padding: .35rem .75rem 1rem;
    }
    [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
      gap: .6rem;
    }
    [data-testid="stSidebar"] {
      background:
        linear-gradient(180deg, rgba(4,14,27,.99) 0%, rgba(5,18,33,.96) 43%, rgba(4,15,28,.56) 72%, rgba(3,10,20,.2) 100%),
        url("__LUNAR_SIDEBAR_ASSET__") center bottom / cover no-repeat;
      border-right: 1px solid #173754;
      box-shadow: 8px 0 30px rgba(0,0,0,.28);
      min-width: 238px;
      max-width: 238px;
    }
    [data-testid="stSidebarContent"] { padding: .8rem .75rem; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
      border: 1px solid transparent;
      border-radius: 9px;
      padding: .62rem .65rem .62rem 2.55rem;
      margin: .12rem 0;
      min-height: 46px;
      position: relative;
      transition: all .15s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:before {
      color: #b9d4ee;
      font-family: "Segoe UI Symbol", sans-serif;
      font-size: 1.35rem;
      left: .78rem;
      line-height: 1;
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
    }
    [data-testid="stSidebar"] [role="radiogroup"] > div:nth-child(1) label:before { content: "⌂"; }
    [data-testid="stSidebar"] [role="radiogroup"] > div:nth-child(2) label:before { content: "⚖"; }
    [data-testid="stSidebar"] [role="radiogroup"] > div:nth-child(3) label:before { content: "⚙"; }
    [data-testid="stSidebar"] [role="radiogroup"] > div:nth-child(4) label:before { content: "▤"; }
    [data-testid="stSidebar"] [role="radiogroup"] > div:nth-child(5) label:before { content: "ⓘ"; }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
      background: rgba(66,165,245,.10);
      border-color: rgba(66,165,245,.3);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
      background: linear-gradient(90deg, #0c4a99, #096bd8);
      border-color: #1687ff;
      box-shadow: 0 0 20px rgba(22,135,255,.28), inset 0 1px rgba(255,255,255,.08);
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none; }
    .sidebar-brand {
      display: flex;
      gap: .7rem;
      align-items: center;
      padding: .25rem .15rem 1rem;
      border-bottom: 1px solid rgba(66,165,245,.2);
      margin-bottom: .85rem;
    }
    .moon-mark {
      filter: drop-shadow(-4px 0 10px rgba(210,230,247,.28));
      height: 48px;
      object-fit: contain;
      width: 48px;
    }
    .brand-title { font-size: 1.42rem; font-weight: 820; color: #f4f8fc; letter-spacing: -.03em; }
    .brand-title span { color: #56c8ff; }
    .brand-subtitle { color: #c0cfdd; font-size: .68rem; white-space: nowrap; }
    .sidebar-footer {
      color: #6F87A1;
      font-size: .72rem;
      border-top: 1px solid rgba(66,165,245,.12);
      margin-top: 1rem;
      opacity: .72;
      padding: .7rem .2rem 0;
    }
    .mission-hero {
      position: relative;
      overflow: hidden;
      box-sizing: border-box;
      height: 108px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      padding: .4rem 1rem .55rem;
      margin-bottom: .55rem;
      border-bottom: 1px solid rgba(66,165,245,.35);
      border-radius: 0 0 12px 12px;
      background:
        linear-gradient(90deg, rgba(3,12,24,.95) 0%, rgba(3,12,24,.76) 35%, rgba(3,12,24,.42) 67%, rgba(3,12,24,.76) 100%),
        url("__LUNAR_HERO_ASSET__") center 61% / cover no-repeat;
      box-shadow: inset 0 -28px 42px rgba(3,10,20,.76);
    }
    .mission-hero > div { position: relative; z-index: 1; }
    .mission-hero.compact { height: 92px; margin-bottom: .35rem; }
    .mission-hero.compact h1 { font-size: 1.45rem; margin: .12rem 0; }
    .mission-hero.compact p { font-size: .76rem; }
    .mission-hero.compact .provider-mark { height: 34px; width: 34px; }
    .eyebrow {
      color: #8FD8FF;
      letter-spacing: .22em;
      font-size: .68rem;
      font-weight: 800;
    }
    .mission-hero h1 {
      color: var(--text);
      font-size: clamp(1.55rem, 2.2vw, 1.95rem);
      line-height: 1.1;
      margin: .25rem 0;
    }
    .mission-hero p { color: #e1e9f1; margin: 0; font-size: .84rem; text-shadow: 0 1px 8px #020812; }
    .hero-status {
      position: relative;
      z-index: 1;
      text-align: right;
      min-width: 360px;
    }
    .provider-row { align-items: center; display: flex; gap: .7rem; justify-content: flex-end; }
    .provider-mark {
      align-items: center;
      background: radial-gradient(circle at 35% 30%, #1687ff, #0b3976 68%, #071629);
      border: 1px solid #40a8ff;
      border-radius: 50%;
      box-shadow: 0 0 18px rgba(22,135,255,.25);
      color: #fff;
      display: inline-flex;
      font-size: .62rem;
      font-weight: 900;
      height: 42px;
      justify-content: center;
      letter-spacing: .08em;
      width: 42px;
    }
    .provider { color: var(--text); font-weight: 800; }
    .provider-subtitle { color: var(--muted); font-size: .76rem; }
    .version-badge {
      display: inline-block;
      margin-left: .4rem;
      border: 1px solid #4F6D8E;
      border-radius: 8px;
      padding: .25rem .55rem;
      color: #D9E8F6;
      background: rgba(16,30,50,.75);
      font-size: .75rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
      border-color: #31597b !important;
      border-radius: 12px !important;
      background: linear-gradient(145deg, rgba(15,31,50,.97), rgba(6,20,35,.98));
      box-shadow: 0 8px 24px rgba(0,0,0,.2), inset 0 1px rgba(255,255,255,.035), 0 0 12px rgba(26,110,174,.07);
    }
    .section-heading {
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--text);
      font-size: 1.02rem;
      margin: -.2rem 0 .4rem;
    }
    .section-heading b, .direction-name { align-items: center; display: flex; gap: .45rem; }
    .ui-icon { display: inline-flex; flex: 0 0 auto; }
    .ui-icon svg { height: 100%; width: 100%; }
    .section-heading span {
      color: var(--muted);
      font-size: .72rem;
      font-weight: 500;
    }
    label, [data-testid="stWidgetLabel"] p { color: #DDE8F3 !important; font-weight: 650 !important; }
    div[data-baseweb="select"] > div,
    [data-testid="stDateInput"] input {
      background: #142741 !important;
      border-color: #496A8D !important;
      color: var(--text) !important;
    }
    .run-spacer, .comparison-action-spacer { height: 27px; }
    [data-testid="stButton"] button[kind="primary"] {
      background: linear-gradient(180deg, #20B85D, #11873F);
      border: 1px solid #39D978;
      box-shadow: 0 0 16px rgba(38,194,129,.22);
      font-weight: 800;
    }
    [data-testid="stButton"] button {
      border-radius: 9px;
      min-height: 39px;
    }
    .st-key-run_analysis button {
      background: linear-gradient(180deg, #19bd5a, #087e37) !important;
      border-color: #35e477 !important;
      box-shadow: 0 0 18px rgba(25,189,90,.25), inset 0 1px rgba(255,255,255,.16) !important;
    }
    .st-key-mission_source [data-testid="stSegmentedControl"] button {
      font-size: .7rem;
      min-height: 35px;
      padding-left: .45rem;
      padding-right: .45rem;
    }
    .source-banner {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: .5rem .75rem;
      margin: .45rem 0 .65rem;
      color: #DDE8F3;
      font-size: .79rem;
    }
    .source-banner span { color: var(--muted); }
    .source-live { background: rgba(38,194,129,.1); border-color: rgba(38,194,129,.55); }
    .source-demo { background: rgba(255,200,69,.08); border-color: rgba(255,200,69,.42); }
    .direction-card {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: .72rem .78rem;
      min-height: 112px;
      background: rgba(7,17,31,.52);
      color: #C8D5E3;
      font-size: .82rem;
    }
    .direction-card.sun { box-shadow: inset 3px 0 var(--sun); }
    .direction-card.earth { box-shadow: inset 3px 0 var(--earth); }
    .direction-name { color: var(--text); font-size: 1rem; font-weight: 800; margin-bottom: .32rem; }
    .direction-card b { color: var(--text); float: right; }
    .visibility-pill {
      display: inline-block;
      margin-top: .2rem;
      padding: .16rem .45rem;
      border-radius: 99px;
      font-size: .72rem;
      font-weight: 800;
    }
    .visibility-pill.above { background: #128548; color: #E5FFF0; }
    .visibility-pill.below { background: #A62532; color: #FFE9EC; }
    .visibility-pill.horizon { background: #526981; color: #F1F5FA; }
    .comparison-vs {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 78px;
      color: var(--blue);
      font-weight: 900;
    }
    .comparison-swap-spacer { height: 1.42rem; }
    .science-notes {
      margin: .25rem 0 0;
      padding-left: 1.1rem;
      color: #D2DDE9;
      font-size: .72rem;
      line-height: 1.35;
    }
    .science-notes li::marker { color: var(--earth); }
    .status-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: .5rem 0;
      margin-top: .65rem;
      padding: .72rem .8rem;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: rgba(16,30,50,.9);
      color: #C7D4E1;
      font-size: .73rem;
    }
    .status-bar span {
      padding: 0 .75rem;
      border-right: 1px solid #365572;
    }
    .status-bar span:first-child { padding-left: 0; }
    .status-bar a { color: #55C7FF; margin-left: auto; font-weight: 750; }
    .status-bar i {
      display: inline-block;
      width: 9px;
      height: 9px;
      border-radius: 50%;
      margin-right: .35rem;
    }
    .status-bar i.source-live { background: var(--success); box-shadow: 0 0 8px var(--success); }
    .status-bar i.source-demo { background: var(--sun); box-shadow: 0 0 8px var(--sun); }
    [data-testid="stCaptionContainer"] { color: var(--muted); }
    [data-testid="stPlotlyChart"] { border-radius: 10px; overflow: hidden; }
    @media (max-width: 900px) {
      [data-testid="stMain"] {
        margin-left: 0 !important;
        width: 100% !important;
        min-width: 0 !important;
      }
      [data-testid="stSidebar"] {
        min-width: min(238px, 85vw);
        max-width: 85vw;
      }
      [data-testid="stMainBlockContainer"] {
        width: 100% !important;
        padding-left: .75rem !important;
        padding-right: .75rem !important;
      }
      [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: .75rem !important;
      }
      [data-testid="stColumn"] {
        width: 100% !important;
        min-width: 100% !important;
        flex: 1 1 100% !important;
      }
      .hero-status { display: none; }
      .mission-hero { min-height: 88px; padding-left: .2rem; }
      .source-banner {
        align-items: flex-start;
        flex-direction: column;
        gap: .25rem;
      }
      .section-heading { align-items: flex-start; flex-wrap: wrap; gap: .3rem; }
      .status-bar { display: block; }
      .status-bar span { display: block; border: none; padding: .18rem 0; }
    }
    </style>
    """
dashboard_styles = dashboard_styles.replace(
    "__LUNAR_SIDEBAR_ASSET__", static_asset_url("lunar-sidebar.png")
).replace(
    "__LUNAR_HERO_ASSET__", static_asset_url("lunar-hero.png")
)
st.markdown(dashboard_styles, unsafe_allow_html=True)

sites = load_sites()

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand">
          <img class="moon-mark" src="{static_asset_url('lunar-crescent.png')}"
               alt="Crescent Moon">
          <div>
            <div class="brand-title"><span>Lunar</span>Sight</div>
            <div class="brand-subtitle">Lunar Landing Site Analysis</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    navigation = st.radio(
        "Navigation",
        [
            "Mission Control",
            "Site Comparison",
            "Solar Rover Planner",
            "Data & Sources",
            "About",
        ],
        key="navigation",
        label_visibility="collapsed",
    )
    st.markdown(
        '<div class="sidebar-footer">Independent mission-planning prototype<br>'
        'NASA JPL Horizons data integration</div>',
        unsafe_allow_html=True,
    )

if navigation == "Mission Control":
    render_mission_control(sites)
elif navigation == "Site Comparison":
    render_site_comparison(sites)
elif navigation == "Solar Rover Planner":
    render_solar_rover_planner()
elif navigation == "Data & Sources":
    render_data_sources(sites)
else:
    render_about()
