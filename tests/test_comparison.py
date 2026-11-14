import pandas as pd
import pytest

from comparison import (
    ComparisonAlignmentError,
    comparison_elevation_chart,
    geometric_visibility_status,
    validate_matching_timestamps,
)


def comparison_frame(*, elevation_offset: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame({
        "time_utc": pd.date_range("2042-05-01", periods=3, freq="h", tz="UTC"),
        "sun_az": [100.0, 101.0, 102.0],
        "sun_el": [-1.0 + elevation_offset, 0.0 + elevation_offset, 1.0 + elevation_offset],
        "earth_az": [300.0, 301.0, 302.0],
        "earth_el": [2.0 + elevation_offset, 1.0 + elevation_offset, -1.0 + elevation_offset],
    })


def test_matching_timestamps_are_returned_in_utc():
    times = validate_matching_timestamps(comparison_frame(), comparison_frame())
    assert len(times) == 3
    assert str(times.dt.tz) == "UTC"


def test_different_timestamps_are_rejected():
    frame_b = comparison_frame()
    frame_b.loc[2, "time_utc"] += pd.Timedelta(minutes=30)
    with pytest.raises(ComparisonAlignmentError, match="different UTC sample"):
        validate_matching_timestamps(comparison_frame(), frame_b)


def test_comparison_chart_contains_two_sites_and_ideal_horizon():
    figure = comparison_elevation_chart(
        comparison_frame(),
        comparison_frame(elevation_offset=0.5),
        elevation_column="sun_el",
        azimuth_column="sun_az",
        target_name="Sun",
        site_a_name="Alpha",
        site_b_name="Beta",
    )
    assert [trace.name for trace in figure.data] == [
        "Alpha",
        "Beta",
        "Ideal horizon (0°)",
    ]
    assert list(figure.data[2].y) == [0, 0]
    assert figure.layout.xaxis.title.text == "Time (UTC)"
    assert "azimuth" in figure.data[0].hovertemplate


@pytest.mark.parametrize(
    ("elevation", "expected"),
    [
        (0.01, "Above ideal horizon"),
        (0.0, "On ideal horizon"),
        (-0.01, "Below ideal horizon"),
    ],
)
def test_geometric_visibility_status(elevation, expected):
    assert geometric_visibility_status(elevation)[0] == expected
