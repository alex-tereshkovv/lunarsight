from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from horizons import HorizonsNetworkError

ROOT = Path(__file__).resolve().parents[1]


def test_demo_mode_renders_both_elevation_charts_without_network():
    app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2
    assert len(app.metric) == 3


def test_live_network_error_falls_back_to_demo_charts():
    with patch(
        "horizons.fetch_ephemeris",
        side_effect=HorizonsNetworkError("offline test"),
    ):
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.radio[0].set_value("Live NASA Data").run(timeout=30)

    assert not app.exception
    assert len(app.error) == 1
    assert "offline test" in app.error[0].value
    assert len(app.get("plotly_chart")) == 2
