"""LunarSight Streamlit application."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horizons import HorizonsError, fetch_ephemeris, load_ephemeris_csv

ROOT = Path(__file__).resolve().parent


@st.cache_data
def load_sites() -> list[dict]:
    with (ROOT / "sites.json").open(encoding="utf-8") as handle:
        return json.load(handle)["sites"]


@st.cache_data
def load_demo() -> pd.DataFrame:
    return load_ephemeris_csv(str(ROOT / "data" / "demo_ephemeris.csv"))


@st.cache_data(ttl=3600, max_entries=24, show_spinner=False)
def load_live(
    latitude_deg: float,
    longitude_deg_east: float,
    start_date_iso: str,
    duration_hours: int,
) -> pd.DataFrame:
    """Fetch and cache only successful Horizons responses for one hour."""
    start_utc = datetime.fromisoformat(start_date_iso).replace(tzinfo=timezone.utc)
    stop_utc = start_utc + timedelta(hours=duration_hours)
    return fetch_ephemeris(
        latitude_deg,
        longitude_deg_east,
        start_utc,
        stop_utc,
    )


def rebase_demo(frame: pd.DataFrame, selected_date: date, duration_hours: int) -> pd.DataFrame:
    result = frame.copy()
    offsets = result["time_utc"] - result["time_utc"].iloc[0]
    result["time_utc"] = pd.Timestamp(selected_date, tz="UTC") + offsets
    end = result["time_utc"].iloc[0] + pd.Timedelta(hours=duration_hours)
    return result[result["time_utc"] <= end]


def elevation_chart(frame: pd.DataFrame, column: str, target: str, color: str) -> go.Figure:
    figure = go.Figure()
    figure.add_hrect(y0=-90, y1=0, fillcolor="#ef4444", opacity=0.07, line_width=0)
    figure.add_hline(y=0, line_dash="dash", line_color="#64748b")
    figure.add_trace(go.Scatter(
        x=frame["time_utc"], y=frame[column], mode="lines+markers", name=target,
        line={"color": color, "width": 3}, marker={"size": 5},
    ))
    figure.update_layout(
        title=f"{target} elevation", height=330,
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        paper_bgcolor="#0b1220", plot_bgcolor="#101a2e",
        font={"color": "#dbeafe"}, xaxis_title="UTC",
        yaxis_title="Elevation (degrees)", hovermode="x unified",
        yaxis={"range": [-20, 20], "zeroline": False}, showlegend=False,
    )
    return figure


st.set_page_config(page_title="LunarSight", page_icon="🌙", layout="wide")
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at 80% 0%, #172554 0, #070b14 38%, #030712 100%); }
[data-testid="stSidebar"] { background: #080d19; border-right: 1px solid #1e3a5f; }
.hero { padding: 1.2rem 0 .6rem; }
.eyebrow { color: #67e8f9; letter-spacing: .18em; font-size: .75rem; font-weight: 700; }
.hero h1 { color: #f8fafc; font-size: 2.65rem; margin: .25rem 0; }
.hero p { color: #a5b4c7; max-width: 780px; font-size: 1.04rem; }
.demo { border: 1px solid #a16207; background: #42200666; color: #fde68a;
        padding: .75rem 1rem; border-radius: .6rem; }
.live { border: 1px solid #0e7490; background: #08334466; color: #a5f3fc;
        padding: .75rem 1rem; border-radius: .6rem; }
[data-testid="stMetric"] { background: #0f172acc; border: 1px solid #1e3a5f;
                          padding: 1rem; border-radius: .7rem; }
</style>
""", unsafe_allow_html=True)

sites = load_sites()
with st.sidebar:
    st.header("Mission parameters")
    data_mode = st.radio("Data source", ["Demo Data", "Live NASA Data"])
    site_name = st.selectbox("Landing site", [site["name"] for site in sites])
    selected_date = st.date_input("Start date (UTC)", value=date.today())
    duration = st.selectbox("Analysis duration", [24, 48, 72], index=1,
                            format_func=lambda hours: f"{hours} hours")
    site = next(item for item in sites if item["name"] == site_name)
    st.caption(f"Demo coordinate: {site['latitude_deg']:.2f}° lat, "
               f"{site['longitude_deg_east']:.2f}° E")
    st.caption("Site coordinates are synthetic and not validated landing locations.")
    st.divider()
    st.caption("Local horizon: ideal geometric plane. Terrain is not modeled.")

actual_source = data_mode
live_error: str | None = None
if data_mode == "Live NASA Data":
    try:
        with st.spinner("Requesting Sun and Earth ephemerides from NASA JPL Horizons..."):
            frame = load_live(
                site["latitude_deg"],
                site["longitude_deg_east"],
                selected_date.isoformat(),
                duration,
            )
    except HorizonsError as error:
        live_error = str(error)
        actual_source = "Demo Data"
        frame = rebase_demo(load_demo(), selected_date, duration)
else:
    frame = rebase_demo(load_demo(), selected_date, duration)

st.markdown("""<div class="hero"><div class="eyebrow">LUNAR SOUTH POLE · MISSION PLANNING</div>
<h1>🌙 LunarSight</h1><p>Compare candidate landing sites through Sun illumination
and Earth line-of-sight geometry.</p></div>""", unsafe_allow_html=True)
if actual_source == "Live NASA Data":
    st.markdown("<div class='live'><strong>Live NASA data</strong> — Sun and Earth "
                "azimuth/elevation were returned by JPL Horizons. The selected site "
                "coordinate is still an unverified demonstration location.</div>",
                unsafe_allow_html=True)
else:
    st.markdown("<div class='demo'><strong>Synthetic demo mode</strong> — charts are "
                "illustrative and are not live NASA calculations.</div>",
                unsafe_allow_html=True)
if live_error:
    st.error(f"Live Horizons request failed: {live_error}")
    st.info("The application automatically switched to Demo Data.")

st.subheader(site_name)
c1, c2, c3 = st.columns(3)
c1.metric("☀️ Sunlight availability", "Pending", help="Developer 2 interface is ready")
c2.metric("📡 Earth communication", "Pending", help="Geometric Earth visibility only")
c3.metric("◉ Simultaneous visibility", "Pending", help="Sun and Earth above 0 degrees")

left, right = st.columns(2)
with left:
    st.plotly_chart(elevation_chart(frame, "sun_el", "Sun", "#fbbf24"),
                    width="stretch")
with right:
    st.plotly_chart(elevation_chart(frame, "earth_el", "Earth", "#38bdf8"),
                    width="stretch")

with st.expander("Data and scientific caveats"):
    st.write("Azimuth is clockwise from local north through east. Elevation is relative "
             "to the ideal local horizontal plane. Positive elevation indicates geometric "
             "visibility only; terrain obstruction is not included.")
    st.dataframe(frame, width="stretch", hide_index=True)
