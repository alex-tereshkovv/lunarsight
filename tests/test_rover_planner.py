import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from horizons import EphemerisValidationError
from horizons import load_ephemeris_csv
from rover_planner import (
    CONNECTIONS,
    SOURCE_NASA_CACHED,
    SOURCE_NASA_LIVE,
    SOURCE_SYNTHETIC,
    WAYPOINTS,
    RouteSegment,
    assert_route_constraints,
    build_component_payload,
    build_synthetic_ephemerides,
    dual_visibility,
    interpolate_fraction,
    interpolate_position,
    plan_route,
    route_state_at,
)


def synthetic_frames(days: int = 14):
    return {
        waypoint.id: build_synthetic_ephemerides(
            waypoint, date(2026, 3, 14), days, step_hours=3
        )
        for waypoint in WAYPOINTS
    }


def constant_frame(sun_el: float, earth_el: float, periods: int = 8):
    return pd.DataFrame({
        "time_utc": pd.date_range(
            "2026-03-14T00:00:00Z", periods=periods, freq="3h"
        ),
        "sun_az": [100.0] * periods,
        "sun_el": [sun_el] * periods,
        "earth_az": [250.0] * periods,
        "earth_el": [earth_el] * periods,
    })


def test_utc_time_interpolation_is_clamped_and_timezone_aware():
    start = datetime(2026, 3, 14, tzinfo=timezone.utc)
    end = start + timedelta(hours=10)
    assert interpolate_fraction(start, end, start + timedelta(hours=4)) == 0.4
    assert interpolate_fraction(start, end, start - timedelta(hours=1)) == 0.0
    assert interpolate_fraction(start, end, end + timedelta(hours=1)) == 1.0
    with pytest.raises(ValueError, match="timezone-aware"):
        interpolate_fraction(start.replace(tzinfo=None), end, start)


def test_position_interpolation_is_smooth_and_heading_matches_motion():
    first, second = WAYPOINTS[0], WAYPOINTS[1]
    start = interpolate_position(first, second, 0.0)
    middle = interpolate_position(first, second, 0.5)
    end = interpolate_position(first, second, 1.0)
    assert middle[0] == pytest.approx((start[0] + end[0]) / 2)
    assert middle[1] == pytest.approx((start[1] + end[1]) / 2)
    assert middle[2] == pytest.approx(start[2]) == pytest.approx(end[2])


def test_dual_visibility_requires_both_object_centres_above_zero():
    frame = constant_frame(1.0, 2.0, periods=3)
    frame.loc[1, "sun_el"] = 0.0
    frame.loc[2, "earth_el"] = -0.1
    assert dual_visibility(frame).tolist() == [True, False, False]


def test_route_segments_are_continuous_connected_and_speed_limited():
    frames = synthetic_frames()
    segments = plan_route(frames, rover_speed_kmh=0.2)
    assert any(segment.moving for segment in segments)
    assert_route_constraints(segments, rover_speed_kmh=0.2)
    allowed = {frozenset(connection) for connection in CONNECTIONS}
    assert all(
        frozenset((segment.from_id, segment.to_id)) in allowed
        for segment in segments
        if segment.moving
    )


def test_route_state_moves_continuously_inside_a_segment():
    first, second = WAYPOINTS[0], WAYPOINTS[1]
    start = datetime(2026, 3, 14, tzinfo=timezone.utc)
    segment = RouteSegment(
        start,
        start + timedelta(hours=10),
        first.id,
        second.id,
        1.0,
        True,
        "test transition",
    )
    state = route_state_at(
        start + timedelta(hours=5),
        [segment],
        {waypoint.id: waypoint for waypoint in WAYPOINTS},
    )
    assert state["progress"] == pytest.approx(0.5)
    assert state["x"] == pytest.approx((first.map_x + second.map_x) / 2)
    assert state["moving"] is True


def test_planner_stays_stationary_when_travel_has_no_visibility_gain():
    frames = {waypoint.id: constant_frame(3.0, 2.0) for waypoint in WAYPOINTS}
    segments = plan_route(frames, rover_speed_kmh=0.2)
    assert segments
    assert all(not segment.moving for segment in segments)
    assert all(segment.from_id == "W1" for segment in segments)


def test_no_feasible_waypoint_scenario_remains_stationary():
    frames = {waypoint.id: constant_frame(-3.0, -2.0) for waypoint in WAYPOINTS}
    segments = plan_route(frames, rover_speed_kmh=0.2)
    assert all(not segment.moving for segment in segments)
    assert "Remain stationary" in segments[0].reason


def test_missing_waypoint_nasa_data_is_rejected():
    frames = synthetic_frames()
    frames.pop("W4")
    with pytest.raises(EphemerisValidationError, match="W4"):
        plan_route(frames, rover_speed_kmh=0.2)


@pytest.mark.parametrize(
    "source",
    [SOURCE_NASA_LIVE, SOURCE_NASA_CACHED, SOURCE_SYNTHETIC],
)
def test_component_payload_preserves_explicit_source_provenance(source):
    frames = synthetic_frames()
    segments = plan_route(frames, rover_speed_kmh=0.2)
    payload = build_component_payload(
        frames,
        segments,
        source_label=source,
        rover_speed_kmh=0.2,
        map_url="/app/static/assets/shackleton-lroc.png",
    )
    assert payload["source_label"] == source
    assert payload["source_kind"] == (
        "synthetic" if source == SOURCE_SYNTHETIC else "nasa"
    )
    assert payload["spatial_note"].startswith("Conceptual waypoint overlay")


def test_unknown_source_cannot_be_silently_presented_as_nasa():
    frames = synthetic_frames()
    segments = plan_route(frames, rover_speed_kmh=0.2)
    with pytest.raises(ValueError, match="provenance"):
        build_component_payload(
            frames,
            segments,
            source_label="NASA-ish",
            rover_speed_kmh=0.2,
            map_url="map.png",
        )


def test_bundled_nasa_cache_is_complete_aligned_and_explicitly_manifested():
    root = Path(__file__).resolve().parents[1]
    cache = root / "data" / "rover_nasa_cache"
    manifest = json.loads((cache / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_label"] == SOURCE_NASA_CACHED
    assert manifest["observation_start_utc"] == "2026-11-14T00:00:00Z"
    assert manifest["sample_interval_hours"] == 3

    frames = {
        waypoint.id: load_ephemeris_csv(str(cache / manifest["files"][waypoint.id]))
        for waypoint in WAYPOINTS
    }
    assert {len(frame) for frame in frames.values()} == {57}
    assert len({tuple(frame["time_utc"]) for frame in frames.values()}) == 1
    assert frames["W1"].iloc[0]["sun_el"] == pytest.approx(1.496957)
