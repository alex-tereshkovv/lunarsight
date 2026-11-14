from datetime import datetime, timedelta, timezone

import pytest
import requests

from horizons import (
    HORIZONS_API_URL,
    HorizonsNetworkError,
    HorizonsResponseError,
    build_observer_parameters,
    fetch_ephemeris,
    fetch_target_ephemeris,
    parse_observer_result,
)


def observer_result(first_az: float, first_el: float) -> str:
    return f"""
*******************************************************************************
$$SOE
 2026-Jan-01 00:00,*, , {first_az}, {first_el},
 2026-Jan-01 01:00,*, , {first_az + 1}, {first_el + 1},
$$EOE
*******************************************************************************
"""


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payloads):
        self.payloads = iter(payloads)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse(next(self.payloads))


def test_lunar_topocentric_request_uses_documented_horizons_syntax():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    params = build_observer_parameters("sun", -89.4, 45.0, start, start + timedelta(hours=24))
    assert params["COMMAND"] == "'10'"
    assert params["CENTER"] == "'coord@301'"
    assert params["COORD_TYPE"] == "'GEODETIC'"
    assert params["SITE_COORD"] == "'45.0,-89.4,0'"
    assert params["QUANTITIES"] == "'4'"
    assert params["APPARENT"] == "'AIRLESS'"
    assert params["TIME_TYPE"] == "'UT'"
    assert params["TIME_ZONE"] == "'+00:00'"
    assert params["STEP_SIZE"] == "'60m'"
    assert HORIZONS_API_URL == "https://ssd.jpl.nasa.gov/api/horizons.api"


def test_parser_returns_utc_and_target_columns():
    frame = parse_observer_result(observer_result(123.5, -2.25), "sun")
    assert list(frame.columns) == ["time_utc", "sun_az", "sun_el"]
    assert str(frame["time_utc"].dt.tz) == "UTC"
    assert frame.iloc[0]["sun_az"] == 123.5
    assert frame.iloc[0]["sun_el"] == -2.25


def test_fetch_ephemeris_merges_sun_and_earth_by_utc():
    session = FakeSession([
        {"result": observer_result(10, 2)},
        {"result": observer_result(200, 5)},
    ])
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    frame = fetch_ephemeris(
        -89.4, 45.0, start, start + timedelta(hours=1), session=session
    )
    assert list(frame.columns) == [
        "time_utc", "sun_az", "sun_el", "earth_az", "earth_el"
    ]
    assert len(frame) == 2
    assert frame.iloc[0][["sun_az", "sun_el", "earth_az", "earth_el"]].tolist() == [
        10, 2, 200, 5
    ]
    assert [call[1]["COMMAND"] for call in session.calls] == ["'10'", "'399'"]


def test_fetch_translates_network_errors():
    class BrokenSession:
        def get(self, *args, **kwargs):
            raise requests.ConnectionError("offline")

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(HorizonsNetworkError, match="offline"):
        fetch_target_ephemeris(
            "sun", -89.4, 45.0, start, start + timedelta(hours=1),
            session=BrokenSession(),
        )


def test_parser_rejects_missing_data_markers():
    with pytest.raises(HorizonsResponseError, match="markers"):
        parse_observer_result("no table", "earth")


def test_parser_rejects_empty_ephemeris_section():
    with pytest.raises(HorizonsResponseError, match="empty ephemeris"):
        parse_observer_result("$$SOE\n\n$$EOE", "sun")


def test_fetch_rejects_horizons_error_payload():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    session = FakeSession([{"error": "invalid observer"}])
    with pytest.raises(HorizonsResponseError, match="invalid observer"):
        fetch_target_ephemeris(
            "earth",
            -89.4,
            45.0,
            start,
            start + timedelta(hours=1),
            session=session,
        )


def test_fetch_rejects_invalid_json():
    class InvalidJsonResponse(FakeResponse):
        def json(self):
            raise ValueError("not json")

    class InvalidJsonSession:
        def get(self, *args, **kwargs):
            return InvalidJsonResponse(None)

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(HorizonsResponseError, match="invalid JSON"):
        fetch_target_ephemeris(
            "sun",
            -89.4,
            45.0,
            start,
            start + timedelta(hours=1),
            session=InvalidJsonSession(),
        )
