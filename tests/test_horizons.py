from datetime import datetime, timedelta, timezone

from horizons import build_observer_parameters


def test_lunar_topocentric_request_uses_documented_horizons_syntax():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    params = build_observer_parameters("sun", -89.4, 45.0, start, start + timedelta(hours=24))
    assert params["COMMAND"] == "'10'"
    assert params["CENTER"] == "'coord@301'"
    assert params["COORD_TYPE"] == "'GEODETIC'"
    assert params["SITE_COORD"] == "'45.0,-89.4,0'"
    assert params["QUANTITIES"] == "'4'"
    assert params["APPARENT"] == "'AIRLESS'"
