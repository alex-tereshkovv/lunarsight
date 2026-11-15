"""Conceptual solar-rover planning helpers for LunarSight.

This module deliberately stays independent from ``analysis.py``.  It evaluates
the same geometric target-centre visibility predicate used by the UI, estimates
great-circle distances between published NASA traverse stations, and builds a
continuous, explainable display route.  It does not model terrain, energy,
hazards, wheel slip, or communications link performance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from math import asin, atan2, ceil, cos, degrees, radians, sin, sqrt
from typing import Final, Mapping, Sequence

import pandas as pd

from horizons import EPHEMERIS_COLUMNS, EphemerisValidationError, validate_ephemeris
from rover_geo import (
    LOLA_LOCAL_DEM_URL,
    LUNAR_SURFACE_DATA_BOOK_URL,
    SHACKLETON_CENTER_LATITUDE_DEG,
    SHACKLETON_CENTER_LONGITUDE_DEG_EAST,
    SHACKLETON_DIAMETER_KM,
    SHACKLETON_FEATURE_URL,
    SHACKLETON_OVERVIEW_URL,
    VERIFIED_STATIONS,
    scale_bar_fraction,
    shackleton_map_position,
    shackleton_within_map,
    station_map_position,
)

MOON_RADIUS_KM: Final = 1737.4
SOURCE_NASA_LIVE: Final = "NASA JPL Horizons — Live"
SOURCE_NASA_CACHED: Final = "NASA JPL Horizons — Cached"
SOURCE_SYNTHETIC: Final = "Conceptual Scientific Layer (Synthetic)"


@dataclass(frozen=True)
class RoverWaypoint:
    """One published NASA representative-traverse station."""

    id: str
    label: str
    latitude_deg: float
    longitude_deg_east: float
    map_x: float
    map_y: float
    color: str


@dataclass(frozen=True)
class RouteSegment:
    """A stationary or moving interval in a precalculated mission route."""

    start_utc: datetime
    end_utc: datetime
    from_id: str
    to_id: str
    distance_km: float
    moving: bool
    reason: str


@dataclass(frozen=True)
class RoverRouteScenario:
    """A documented endpoint scenario with a conceptual display connector."""

    id: str
    label: str
    station_ids: tuple[str, ...]
    official_traverse_length_km: float | None
    source_pages: str


_STATION_COLORS: Final = {
    "CR1": "#ffd23f",
    "CR2": "#9a78ff",
    "CR3": "#ad8aff",
    "SR1": "#38c9ff",
    "SR2": "#5ed6ff",
    "SR3": "#73e1d1",
    "PSR1": "#c58cff",
}

WAYPOINTS: Final[tuple[RoverWaypoint, ...]] = tuple(
    RoverWaypoint(
        station.id,
        station.label,
        station.latitude_deg,
        station.longitude_deg_east,
        *station_map_position(station),
        _STATION_COLORS[station.id],
    )
    for station in VERIFIED_STATIONS
)

ROUTE_SCENARIOS: Final[tuple[RoverRouteScenario, ...]] = (
    RoverRouteScenario(
        "CR1_SR1",
        "CR1 → SR1 representative traverse",
        ("CR1", "SR1"),
        11.15,
        "NASA Lunar Surface Data Book, pp. 55–59",
    ),
    RoverRouteScenario(
        "SR3_PSR1",
        "SR3 → PSR1 representative traverse",
        ("SR3", "PSR1"),
        8.66,
        "NASA Lunar Surface Data Book, pp. 55–60",
    ),
)
DEFAULT_ROUTE_ID: Final = "CR1_SR1"
DYNAMIC_ROUTE_ID: Final = "DYNAMIC_VISIBILITY"
DYNAMIC_ROUTE_SCENARIO: Final = RoverRouteScenario(
    DYNAMIC_ROUTE_ID,
    "Visibility Optimization",
    tuple(waypoint.id for waypoint in WAYPOINTS),
    None,
    "Verified stations from NASA M2M-30044; conceptual links are not published traverses",
)
CONTINUOUS_EXPLORATION_ID: Final = "CONTINUOUS_EXPLORATION"
CONTINUOUS_EXPLORATION_SCENARIO: Final = RoverRouteScenario(
    CONTINUOUS_EXPLORATION_ID,
    "Continuous Exploration",
    tuple(waypoint.id for waypoint in WAYPOINTS),
    None,
    "Conceptual closed walk on published-station links; not a validated traverse",
)
# These edges form a transparent planning graph between published stations.  They
# are display/planning links only: the Moon has not signed off on our shortcuts.
CONNECTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("CR1", "CR2"),
    ("CR2", "CR3"),
    ("CR1", "SR1"),
    ("SR1", "SR2"),
    ("SR2", "SR3"),
    ("SR1", "PSR1"),
    ("SR3", "PSR1"),
)
EXPLORATION_WALKS: Final[tuple[tuple[str, ...], ...]] = (
    (
        "CR1", "CR2", "CR3", "CR2", "CR1", "SR1",
        "SR2", "SR3", "PSR1", "SR1", "CR1",
    ),
    ("CR1", "SR1", "SR2", "SR3", "PSR1", "SR1", "CR1"),
    ("CR1", "CR2", "CR3", "CR2", "CR1"),
    ("CR1", "CR2", "CR1"),
)


def get_route_scenario(route_id: str) -> RoverRouteScenario:
    """Return one supported NASA endpoint scenario."""
    if route_id == DYNAMIC_ROUTE_ID:
        return DYNAMIC_ROUTE_SCENARIO
    if route_id == CONTINUOUS_EXPLORATION_ID:
        return CONTINUOUS_EXPLORATION_SCENARIO
    try:
        return next(item for item in ROUTE_SCENARIOS if item.id == route_id)
    except StopIteration as error:
        raise ValueError(f"Unknown rover route scenario: {route_id}") from error


def dual_visibility(frame: pd.DataFrame) -> pd.Series:
    """Return the geometric Sun-and-Earth-above-zero predicate."""
    validated = validate_ephemeris(frame)
    return (validated["sun_el"] > 0.0) & (validated["earth_el"] > 0.0)


def great_circle_distance_km(first: RoverWaypoint, second: RoverWaypoint) -> float:
    """Estimate surface distance on a spherical Moon."""
    lat1, lat2 = radians(first.latitude_deg), radians(second.latitude_deg)
    delta_lat = lat2 - lat1
    delta_lon = radians(second.longitude_deg_east - first.longitude_deg_east)
    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * MOON_RADIUS_KM * asin(min(1.0, sqrt(a)))


def interpolate_fraction(start: datetime, end: datetime, moment: datetime) -> float:
    """Return a clamped UTC interpolation fraction for ``moment``."""
    start_utc, end_utc, moment_utc = (_ensure_utc(value) for value in (start, end, moment))
    duration = (end_utc - start_utc).total_seconds()
    if duration <= 0:
        raise ValueError("end must be after start")
    return min(1.0, max(0.0, (moment_utc - start_utc).total_seconds() / duration))


def interpolate_position(
    first: RoverWaypoint,
    second: RoverWaypoint,
    fraction: float,
) -> tuple[float, float, float]:
    """Linearly interpolate map position and return screen-space heading.

    The rover SVG's local forward axis is +X.  Because SVG Y increases down the
    screen, ``atan2(dy, dx)`` directly gives the clockwise rotation required to
    keep the vehicle nose aligned with its direction of travel.
    """
    progress = min(1.0, max(0.0, float(fraction)))
    dx, dy = second.map_x - first.map_x, second.map_y - first.map_y
    x = first.map_x + dx * progress
    y = first.map_y + dy * progress
    heading = (degrees(atan2(dy, dx)) + 360.0) % 360.0 if dx or dy else 0.0
    return x, y, heading


def build_synthetic_ephemerides(
    waypoint: RoverWaypoint,
    start_date: date,
    duration_days: int,
    *,
    step_hours: int = 3,
) -> pd.DataFrame:
    """Build an explicitly synthetic, site-distinct demonstration table.

    The curves are deterministic visual fixtures, not an astronomical model and
    never carry a NASA provenance label.
    """
    if duration_days not in (7, 14, 28, 60):
        raise ValueError("duration_days must be 7, 14, 28, or 60")
    if step_hours < 1:
        raise ValueError("step_hours must be positive")
    start = pd.Timestamp(start_date, tz="UTC")
    periods = duration_days * 24 // step_hours + 1
    times = pd.date_range(start, periods=periods, freq=f"{step_hours}h")
    index = next(i for i, item in enumerate(WAYPOINTS) if item.id == waypoint.id)
    hours = pd.Series(range(periods), dtype="float64") * step_hours
    phase = index * 0.58

    # Short illustrative cycles ensure the offline demo exercises waiting and
    # relocation. They are intentionally not presented as lunar-period physics.
    sun_el = 4.8 * (hours.mul(2 * 3.141592653589793 / 132) + phase).map(sin) + 1.0
    earth_el = 3.6 * (hours.mul(2 * 3.141592653589793 / 174) + 0.4 - phase * 0.45).map(cos) + 0.7
    sun_az = (hours * 1.31 + 42.0 + index * 29.0) % 360.0
    earth_az = (hours * 0.73 + 210.0 - index * 17.0) % 360.0

    return validate_ephemeris(pd.DataFrame({
        "time_utc": times,
        "sun_az": sun_az,
        "sun_el": sun_el,
        "earth_az": earth_az,
        "earth_el": earth_el,
    }))


def downsample_ephemeris(frame: pd.DataFrame, step_hours: int = 3) -> pd.DataFrame:
    """Validate and select a regular subset while retaining the final sample."""
    if step_hours < 1:
        raise ValueError("step_hours must be positive")
    validated = validate_ephemeris(frame)
    start = validated["time_utc"].iloc[0]
    elapsed_hours = (
        validated["time_utc"] - start
    ).dt.total_seconds().div(3600).round(9)
    selected = validated.loc[(elapsed_hours % step_hours).abs() < 1e-8]
    if selected.empty or selected.index[-1] != validated.index[-1]:
        selected = pd.concat([selected, validated.tail(1)])
    return selected.drop_duplicates("time_utc").reset_index(drop=True)


def validate_waypoint_ephemerides(
    ephemerides: Mapping[str, pd.DataFrame],
    waypoints: Sequence[RoverWaypoint] = WAYPOINTS,
) -> dict[str, pd.DataFrame]:
    """Validate complete, timestamp-aligned data for every waypoint."""
    expected = {waypoint.id for waypoint in waypoints}
    missing = expected.difference(ephemerides)
    if missing:
        raise EphemerisValidationError(
            f"Missing waypoint ephemerides: {', '.join(sorted(missing))}"
        )
    validated = {
        waypoint.id: validate_ephemeris(ephemerides[waypoint.id])
        for waypoint in waypoints
    }
    reference = validated[waypoints[0].id]["time_utc"].tolist()
    if any(frame["time_utc"].tolist() != reference for frame in validated.values()):
        raise EphemerisValidationError(
            "Waypoint ephemerides must use identical increasing UTC timestamps"
        )
    return validated


def plan_route(
    ephemerides: Mapping[str, pd.DataFrame],
    *,
    rover_speed_kmh: float,
    waypoints: Sequence[RoverWaypoint] = WAYPOINTS,
    connections: Sequence[tuple[str, str]] = CONNECTIONS,
    start_waypoint_id: str = "CR1",
    minimum_gain_hours: float = 0.25,
    turn_allowance_hours: float = 0.25,
) -> list[RouteSegment]:
    """Optimize cumulative geometric dual visibility on a time-expanded graph.

    Each state is ``(UTC sample, verified station)``. Staying earns one sample
    interval when both target centres are above the ideal 0-degree horizon.
    Moving is allowed only on an explicit conceptual connection, consumes the
    spherical-distance travel time plus a small turning allowance, and pays the
    ``minimum_gain_hours`` relocation penalty. Visibility along an edge is not
    inferred because no timestamped terrain-safe path geometry is available.
    """
    if rover_speed_kmh <= 0:
        raise ValueError("rover_speed_kmh must be positive")
    if minimum_gain_hours < 0 or turn_allowance_hours < 0:
        raise ValueError("planning penalties must not be negative")
    frames = validate_waypoint_ephemerides(ephemerides, waypoints)
    waypoint_by_id = {waypoint.id: waypoint for waypoint in waypoints}
    if start_waypoint_id not in waypoint_by_id:
        raise ValueError("start_waypoint_id is not a known waypoint")
    valid_ids = set(waypoint_by_id)
    if any(first not in valid_ids or second not in valid_ids for first, second in connections):
        raise ValueError("connections contain an unknown waypoint")

    times = frames[start_waypoint_id]["time_utc"].tolist()
    if len(times) < 2:
        raise EphemerisValidationError("Route planning needs at least two UTC samples")
    step_hours = (times[1] - times[0]).total_seconds() / 3600
    if step_hours <= 0:
        raise EphemerisValidationError("Route timestamps must increase")
    visible = {
        waypoint.id: dual_visibility(frames[waypoint.id]).tolist()
        for waypoint in waypoints
    }
    neighbours = {waypoint.id: set() for waypoint in waypoints}
    for first, second in connections:
        neighbours[first].add(second)
        neighbours[second].add(first)

    count = len(times)
    scores = [{waypoint.id: 0.0 for waypoint in waypoints} for _ in range(count)]
    decisions: list[dict[str, tuple[str, int, float]]] = [dict() for _ in range(count)]

    for index in range(count - 2, -1, -1):
        for current in sorted(valid_ids):
            stay_score = (
                step_hours if visible[current][index] else 0.0
            ) + scores[index + 1][current]
            best_score = stay_score
            best_decision = (current, index + 1, 0.0)
            for candidate in sorted(neighbours[current]):
                distance = great_circle_distance_km(
                    waypoint_by_id[current], waypoint_by_id[candidate]
                )
                travel_hours = distance / rover_speed_kmh
                arrival_steps = max(
                    1,
                    ceil((travel_hours + turn_allowance_hours) / step_hours),
                )
                arrival_index = index + arrival_steps
                if arrival_index >= count:
                    continue
                candidate_score = (
                    scores[arrival_index][candidate] - minimum_gain_hours
                )
                if candidate_score > best_score + 1e-9:
                    best_score = candidate_score
                    best_decision = (candidate, arrival_index, distance)
            scores[index][current] = best_score
            decisions[index][current] = best_decision

    segments: list[RouteSegment] = []
    current = start_waypoint_id
    index = 0
    while index < count - 1:
        destination, next_index, distance = decisions[index][current]
        start_time = times[index].to_pydatetime()
        end_time = times[next_index].to_pydatetime()
        if destination == current:
            has_future_option = any(
                any(visible[item][index:]) for item in neighbours[current]
            )
            reason = (
                "Remain stationary: relocation would not improve cumulative "
                "geometric dual-visibility time after travel and movement penalty."
                if has_future_option
                else "Remain stationary: no feasible connected waypoint is available."
            )
            segments.append(RouteSegment(
                start_time, end_time, current, current, 0.0, False, reason
            ))
        else:
            physical_hours = distance / rover_speed_kmh
            reason = (
                f"Move to {destination}: dynamic planning improves the remaining "
                f"geometric dual-visibility objective. Spherical distance "
                f"{distance:.2f} km; minimum drive time {physical_hours:.1f} h. "
                "Visibility and traversability along this conceptual link are unverified."
            )
            segments.append(RouteSegment(
                start_time,
                end_time,
                current,
                destination,
                distance,
                True,
                reason,
            ))
        current = destination
        index = next_index

    return _merge_stationary_segments(segments)


def plan_continuous_exploration(
    ephemerides: Mapping[str, pd.DataFrame],
    *,
    rover_speed_kmh: float,
    waypoints: Sequence[RoverWaypoint] = WAYPOINTS,
    connections: Sequence[tuple[str, str]] = CONNECTIONS,
    pause_hours: float = 0.5,
    turn_allowance_hours: float = 0.25,
) -> list[RouteSegment]:
    """Build repeating closed demonstration walks without inventing shortcuts.

    The longest predefined closed walk that physically fits the observation
    period is selected. Every leg is an explicit conceptual graph edge; the
    rover returns to CR1 before another cycle starts, so looped playback has no
    position discontinuity. Ephemerides are validated but do not influence this
    demonstration-only route.
    """
    if rover_speed_kmh <= 0:
        raise ValueError("rover_speed_kmh must be positive")
    if pause_hours < 0 or turn_allowance_hours < 0:
        raise ValueError("exploration timing values must not be negative")
    frames = validate_waypoint_ephemerides(ephemerides, waypoints)
    waypoint_by_id = {waypoint.id: waypoint for waypoint in waypoints}
    allowed = {frozenset(edge) for edge in connections}
    start_time = frames[waypoints[0].id]["time_utc"].iloc[0].to_pydatetime()
    end_time = frames[waypoints[0].id]["time_utc"].iloc[-1].to_pydatetime()
    available_hours = (end_time - start_time).total_seconds() / 3600.0

    def walk_duration_hours(walk: Sequence[str]) -> float:
        return sum(
            great_circle_distance_km(waypoint_by_id[first], waypoint_by_id[second])
            / rover_speed_kmh
            + turn_allowance_hours
            + pause_hours
            for first, second in zip(walk, walk[1:])
        )

    selected: tuple[str, ...] | None = None
    for walk in EXPLORATION_WALKS:
        if any(frozenset(edge) not in allowed for edge in zip(walk, walk[1:])):
            continue
        if walk[0] != walk[-1]:
            raise ValueError("exploration walks must be closed")
        if walk_duration_hours(walk) <= available_hours + 1e-9:
            selected = walk
            break

    if selected is None:
        return [RouteSegment(
            start_time,
            end_time,
            "CR1",
            "CR1",
            0.0,
            False,
            "Remain stationary: no closed conceptual exploration walk fits the period.",
        )]

    segments: list[RouteSegment] = []
    cursor = start_time
    cycle_index = 1
    cycle_duration = timedelta(hours=walk_duration_hours(selected))
    while cursor + cycle_duration <= end_time + timedelta(microseconds=1):
        for first, second in zip(selected, selected[1:]):
            distance = great_circle_distance_km(
                waypoint_by_id[first], waypoint_by_id[second]
            )
            drive_end = cursor + timedelta(
                hours=distance / rover_speed_kmh + turn_allowance_hours
            )
            segments.append(RouteSegment(
                cursor,
                drive_end,
                first,
                second,
                distance,
                True,
                f"Conceptual Exploration Loop {cycle_index}: travel to {second}. "
                "This graph edge is not a terrain-validated traverse.",
            ))
            cursor = drive_end
            if pause_hours:
                pause_end = cursor + timedelta(hours=pause_hours)
                segments.append(RouteSegment(
                    cursor,
                    pause_end,
                    second,
                    second,
                    0.0,
                    False,
                    f"Planned pause at published station {second}.",
                ))
                cursor = pause_end
        cycle_index += 1

    if cursor < end_time:
        segments.append(RouteSegment(
            cursor,
            end_time,
            selected[0],
            selected[0],
            0.0,
            False,
            "Exploration cycles complete; remain at the start station until period end.",
        ))
    return _merge_stationary_segments(segments)


def route_state_at(
    moment: datetime,
    segments: Sequence[RouteSegment],
    waypoint_by_id: Mapping[str, RoverWaypoint],
) -> dict[str, object]:
    """Interpolate the rover state at one UTC instant."""
    if not segments:
        raise ValueError("segments must not be empty")
    moment_utc = _ensure_utc(moment)
    segment = next(
        (
            item
            for item in segments
            if item.start_utc <= moment_utc <= item.end_utc
        ),
        segments[0] if moment_utc < segments[0].start_utc else segments[-1],
    )
    progress = (
        interpolate_fraction(segment.start_utc, segment.end_utc, moment_utc)
        if segment.moving
        else 0.0
    )
    x, y, heading = interpolate_position(
        waypoint_by_id[segment.from_id], waypoint_by_id[segment.to_id], progress
    )
    return {
        "x": x,
        "y": y,
        "heading_deg": heading,
        "from_id": segment.from_id,
        "to_id": segment.to_id,
        "current_waypoint": segment.to_id if progress >= 1.0 else segment.from_id,
        "next_waypoint": segment.to_id,
        "moving": segment.moving and progress < 1.0,
        "progress": progress,
        "distance_km": segment.distance_km,
        "travel_hours": (
            (segment.end_utc - segment.start_utc).total_seconds() / 3600
            if segment.moving
            else 0.0
        ),
        "reason": segment.reason,
    }


def build_component_payload(
    ephemerides: Mapping[str, pd.DataFrame],
    segments: Sequence[RouteSegment],
    *,
    source_label: str,
    rover_speed_kmh: float,
    map_url: str,
    overview_url: str = "",
    route_scenario: RoverRouteScenario | None = None,
    waypoints: Sequence[RoverWaypoint] = WAYPOINTS,
    connections: Sequence[tuple[str, str]] = CONNECTIONS,
) -> dict[str, object]:
    """Serialize validated planning inputs for the client-side simulation."""
    if source_label not in {SOURCE_NASA_LIVE, SOURCE_NASA_CACHED, SOURCE_SYNTHETIC}:
        raise ValueError("Unknown ephemeris provenance label")
    frames = validate_waypoint_ephemerides(ephemerides, waypoints)
    scenario = route_scenario or get_route_scenario(DEFAULT_ROUTE_ID)
    waypoint_by_id = {waypoint.id: waypoint for waypoint in waypoints}
    times = frames[waypoints[0].id]["time_utc"]
    used_ids = {
        station_id
        for segment in segments
        for station_id in (segment.from_id, segment.to_id)
    }
    visited_station_ids = [
        waypoint.id for waypoint in waypoints if waypoint.id in used_ids
    ]
    excluded_station_ids = [
        waypoint.id for waypoint in waypoints if waypoint.id not in used_ids
    ]
    exploration_mode = scenario.id == CONTINUOUS_EXPLORATION_ID

    states: list[dict[str, object]] = []
    for row_index, timestamp in enumerate(times):
        state = route_state_at(timestamp.to_pydatetime(), segments, waypoint_by_id)
        from_row = frames[str(state["from_id"])].iloc[row_index]
        to_row = frames[str(state["to_id"])].iloc[row_index]
        progress = float(state["progress"])
        for column in EPHEMERIS_COLUMNS[1:]:
            state[column] = float(
                from_row[column] + (to_row[column] - from_row[column]) * progress
            )
        state["dual_visible"] = bool(
            state["sun_el"] > 0 and state["earth_el"] > 0
        )
        state["time_utc"] = timestamp.isoformat()
        upcoming = next(
            (
                item.to_id
                for item in segments
                if item.moving and item.start_utc >= timestamp.to_pydatetime()
            ),
            str(state["to_id"]),
        )
        state["recommended_waypoint"] = upcoming
        states.append(state)

    series = []
    for waypoint in waypoints:
        frame = frames[waypoint.id]
        points = [
            {
                "time_utc": row.time_utc.isoformat(),
                "sun_el": float(row.sun_el),
                "earth_el": float(row.earth_el),
                "sun_az": float(row.sun_az),
                "earth_az": float(row.earth_az),
                "dual_visible": bool(row.sun_el > 0 and row.earth_el > 0),
            }
            for row in frame.itertuples(index=False)
        ]
        series.append({
            **asdict(waypoint),
            "points": points,
        })

    return {
        "source_label": source_label,
        "source_kind": "synthetic" if source_label == SOURCE_SYNTHETIC else "nasa",
        "start_utc": times.iloc[0].isoformat(),
        "end_utc": times.iloc[-1].isoformat(),
        "sample_hours": (
            (times.iloc[1] - times.iloc[0]).total_seconds() / 3600
            if len(times) > 1
            else None
        ),
        "rover_speed_kmh": rover_speed_kmh,
        "map_url": map_url,
        "overview_url": overview_url,
        "map_credit": "NASA/GSFC PGDA — LOLA Site01 + Site04, 5 m/pixel DEM",
        "map_source_url": LOLA_LOCAL_DEM_URL,
        "spatial_note": (
            "Georeferenced terrain hillshade in lunar south-polar stereographic "
            "metres. It is not timestamp-specific illumination."
        ),
        "terrain_note": (
            "The station graph uses conceptual straight connectors between verified "
            "NASA stations; it is not the NASA traverse polyline, a published "
            "traverse length, or a terrain-safe route."
        ),
        "station_source_url": LUNAR_SURFACE_DATA_BOOK_URL,
        "shackleton": {
            "name": "Shackleton Crater",
            "latitude_deg": SHACKLETON_CENTER_LATITUDE_DEG,
            "longitude_deg_east": SHACKLETON_CENTER_LONGITUDE_DEG_EAST,
            "diameter_km": SHACKLETON_DIAMETER_KM,
            "map_x": shackleton_map_position()[0],
            "map_y": shackleton_map_position()[1],
            "inside_route_crop": shackleton_within_map(),
            "feature_source_url": SHACKLETON_FEATURE_URL,
            "overview_source_url": SHACKLETON_OVERVIEW_URL,
            "overview_note": (
                "NASA multi-temporal LROC overview; not the route-map scale and "
                "not timestamp-specific illumination."
            ),
        },
        "scale_bar": {"distance_km": 2.0, "fraction": scale_bar_fraction(2.0)},
        "route": {
            **asdict(scenario),
            "mode_kind": "exploration" if exploration_mode else "visibility",
            "visited_station_ids": visited_station_ids,
            "excluded_station_ids": excluded_station_ids,
            "spotlight_label": (
                "Exploration Destination"
                if exploration_mode
                else "Recommended Candidate Zone"
            ),
            "loop_playback_default": exploration_mode,
            "closed_at_boundary": bool(
                segments
                and segments[0].from_id == segments[-1].to_id
            ),
            "display_connector_length_km": sum(
                segment.distance_km for segment in segments if segment.moving
            ),
            "connector_label": "Conceptual station graph — not terrain validated",
        },
        "waypoints": [asdict(waypoint) for waypoint in waypoints],
        "connections": [list(connection) for connection in connections],
        "segments": [
            {
                **asdict(segment),
                "start_utc": segment.start_utc.isoformat(),
                "end_utc": segment.end_utc.isoformat(),
            }
            for segment in segments
        ],
        "states": states,
        "series": series,
    }


def assert_route_constraints(
    segments: Sequence[RouteSegment],
    *,
    rover_speed_kmh: float,
    connections: Sequence[tuple[str, str]] = CONNECTIONS,
    tolerance: float = 1e-9,
) -> None:
    """Raise when route continuity, connectivity, or speed is invalid."""
    allowed = {frozenset(connection) for connection in connections}
    previous: RouteSegment | None = None
    for segment in segments:
        if segment.end_utc <= segment.start_utc:
            raise ValueError("Route segments must have positive duration")
        if previous:
            if segment.start_utc != previous.end_utc:
                raise ValueError("Route segments must be time-continuous")
            if segment.from_id != previous.to_id:
                raise ValueError("Route segments must be spatially continuous")
        duration_hours = (segment.end_utc - segment.start_utc).total_seconds() / 3600
        if segment.moving:
            if frozenset((segment.from_id, segment.to_id)) not in allowed:
                raise ValueError("Route uses an invalid waypoint transition")
            if segment.distance_km / duration_hours > rover_speed_kmh + tolerance:
                raise ValueError("Route exceeds the configured rover speed")
        elif segment.from_id != segment.to_id or segment.distance_km != 0:
            raise ValueError("Stationary segments must remain at one waypoint")
        previous = segment


def _merge_stationary_segments(segments: Sequence[RouteSegment]) -> list[RouteSegment]:
    merged: list[RouteSegment] = []
    for segment in segments:
        if (
            merged
            and not segment.moving
            and not merged[-1].moving
            and segment.from_id == merged[-1].from_id
            and segment.start_utc == merged[-1].end_utc
            and segment.reason == merged[-1].reason
        ):
            previous = merged[-1]
            merged[-1] = RouteSegment(
                previous.start_utc,
                segment.end_utc,
                previous.from_id,
                previous.to_id,
                0.0,
                False,
                previous.reason,
            )
        else:
            merged.append(segment)
    return merged


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime values must be timezone-aware")
    return value.astimezone(timezone.utc)
