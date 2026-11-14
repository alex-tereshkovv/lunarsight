import re
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

from horizons import EphemerisValidationError, HorizonsNetworkError, HorizonsResponseError

ROOT = Path(__file__).resolve().parents[1]


def widget_with_label(elements, label):
    return next(element for element in elements if element.label == label)


def live_comparison_frame(start_date: str, offset: float) -> pd.DataFrame:
    return pd.DataFrame({
        "time_utc": pd.date_range(start_date, periods=4, freq="h", tz="UTC"),
        "sun_az": [100.0, 101.0, 102.0, 103.0],
        "sun_el": [-1.0 + offset, 0.0 + offset, 1.0 + offset, 2.0 + offset],
        "earth_az": [300.0, 301.0, 302.0, 303.0],
        "earth_el": [2.0 + offset, 1.0 + offset, 0.0 + offset, -1.0 + offset],
    })


def test_demo_mode_renders_both_elevation_charts_without_network():
    app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2
    download = app.get("download_button")[0]
    assert download.label == "Download Ephemeris CSV"
    assert download.proto.ignore_rerun is True
    assert sum("Analysis pending" in item.value for item in app.markdown) == 4
    assert any("Demo (Synthetic)" in item.value for item in app.markdown)


def test_mission_configuration_controls_update():
    app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
    widget_with_label(app.selectbox, "Landing Site").set_value("Demo Plateau Beta")
    widget_with_label(app.selectbox, "Duration").set_value(24)
    app.date_input[0].set_value(date(2026, 11, 15))
    app.run(timeout=30)

    assert not app.exception
    assert widget_with_label(app.selectbox, "Landing Site").value == "Demo Plateau Beta"
    assert widget_with_label(app.selectbox, "Duration").value == 24
    assert app.date_input[0].value == date(2026, 11, 15)
    assert len(app.get("plotly_chart")) == 2
    displayed = app.dataframe[0].value
    assert len(displayed) == 5
    assert displayed["time_utc"].iloc[0] == pd.Timestamp("2026-11-15T00:00:00Z")
    assert displayed["time_utc"].iloc[-1] == pd.Timestamp("2026-11-16T00:00:00Z")


def test_mission_preview_swap_exchanges_sites_without_fetching_live_data():
    with patch("horizons.fetch_ephemeris") as fetch:
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        site_a = widget_with_label(app.selectbox, "Site A")
        site_b = widget_with_label(app.selectbox, "Site B")
        original_a, original_b = site_a.value, site_b.value

        next(button for button in app.button if button.label == "Swap sites").click()
        app.run(timeout=30)

    assert not app.exception
    assert widget_with_label(app.selectbox, "Site A").value == original_b
    assert widget_with_label(app.selectbox, "Site B").value == original_a
    fetch.assert_not_called()


def test_dashboard_assets_and_streamlit_theme_are_packaged():
    asset_dir = ROOT / "static" / "assets"
    assert (asset_dir / "lunar-hero.png").is_file()
    assert (asset_dir / "lunar-sidebar.png").is_file()
    assert (asset_dir / "lunar-crescent.png").is_file()

    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert "enableStaticServing = true" in config
    assert 'base = "dark"' in config

    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '"/~/+/app/static/assets"' in source
    assert '"/app/static/assets"' in source
    assert 'static_asset_url("lunar-sidebar.png")' in source
    assert 'static_asset_url("lunar-hero.png")' in source
    assert "static_asset_url('lunar-crescent.png')" in source


def test_live_network_error_falls_back_to_demo_charts():
    with patch(
        "horizons.fetch_ephemeris",
        side_effect=HorizonsNetworkError("offline test"),
    ):
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        widget_with_label(app.segmented_control, "Data Source").set_value(
            "Live NASA (Horizons)"
        )
        app.run(timeout=30)

    assert not app.exception
    assert len(app.error) == 1
    assert "offline test" in app.error[0].value
    assert len(app.get("plotly_chart")) == 2
    assert any("Demo (Fallback)" in item.value for item in app.markdown)


def test_live_mission_control_uses_selected_site_period_and_nasa_label():
    live_frame = live_comparison_frame("2045-08-01", 0.25)
    with patch("horizons.fetch_ephemeris", return_value=live_frame) as fetch:
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.date_input[0].set_value(date(2045, 8, 1)).run(timeout=30)
        widget_with_label(app.selectbox, "Landing Site").set_value(
            "Demo Crater Rim Gamma"
        )
        widget_with_label(app.selectbox, "Duration").set_value(24)
        widget_with_label(app.segmented_control, "Data Source").set_value(
            "Live NASA (Horizons)"
        )
        app.run(timeout=30)

    assert not app.exception
    assert not app.error
    assert fetch.call_count == 1
    assert fetch.call_args.args[:2] == (-89.1, 285.0)
    assert fetch.call_args.args[2].isoformat() == "2045-08-01T00:00:00+00:00"
    assert fetch.call_args.args[3].isoformat() == "2045-08-02T00:00:00+00:00"
    assert any("NASA JPL Horizons (Live)" in item.value for item in app.markdown)
    assert len(app.get("plotly_chart")) == 2
    assert len(app.get("download_button")) == 1


def test_live_invalid_table_falls_back_to_clearly_labeled_demo():
    invalid_frame = pd.DataFrame({
        "time_utc": ["2044-07-01T00:00:00Z"],
        "sun_az": [10.0],
    })
    with patch("horizons.fetch_ephemeris", return_value=invalid_frame):
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.date_input[0].set_value(date(2044, 7, 1)).run(timeout=30)
        widget_with_label(app.segmented_control, "Data Source").set_value(
            "Live NASA (Horizons)"
        )
        app.run(timeout=30)

    assert not app.exception
    assert len(app.error) == 1
    assert "violates the LunarSight schema" in app.error[0].value
    assert any("Demo (Fallback)" in item.value for item in app.markdown)
    assert len(app.get("plotly_chart")) == 2


def test_invalid_demo_dataset_suppresses_charts_and_export():
    st.cache_data.clear()
    try:
        with patch(
            "horizons.load_ephemeris_csv",
            side_effect=EphemerisValidationError("empty demo"),
        ):
            app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
    finally:
        st.cache_data.clear()

    assert not app.exception
    assert len(app.error) == 1
    assert "synthetic demo data is unavailable" in app.error[0].value
    assert len(app.get("plotly_chart")) == 0
    assert len(app.get("download_button")) == 0


def test_sidebar_navigation_opens_all_sections():
    app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
    navigation = app.radio[0]

    for section, heading in [
        ("Site Comparison", "Landing Site Comparison"),
        ("Solar Rover Planner", "Solar Rover Planner"),
        ("Data & Sources", "Data & Sources"),
        ("About", "About LunarSight"),
    ]:
        navigation.set_value(section)
        app.run(timeout=30)
        navigation = app.radio[0]
        assert not app.exception
        assert any(heading in item.value for item in app.markdown)


def test_solar_rover_planner_defaults_to_explicit_real_nasa_cache():
    with patch("horizons.fetch_ephemeris") as fetch:
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.radio[0].set_value("Solar Rover Planner").run(timeout=30)

    assert not app.exception
    fetch.assert_not_called()
    assert widget_with_label(
        app.selectbox, "Ephemerides"
    ).value == "NASA JPL Horizons — Cached"
    assert "Synthetic Demonstration" not in widget_with_label(
        app.selectbox, "Ephemerides"
    ).options
    assert not app.error
    assert not app.warning


def test_solar_rover_cached_nasa_source_is_offline_and_explicit():
    with patch("horizons.fetch_ephemeris") as fetch:
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.radio[0].set_value("Solar Rover Planner").run(timeout=30)
        widget_with_label(app.selectbox, "Ephemerides").set_value(
            "NASA JPL Horizons — Cached"
        )
        app.date_input[0].set_value(date(2026, 11, 14))
        widget_with_label(app.selectbox, "Period").set_value(7)
        app.form_submit_button[0].click().run(timeout=30)

    assert not app.exception
    fetch.assert_not_called()
    assert not app.error
    assert widget_with_label(app.selectbox, "Ephemerides").value == (
        "NASA JPL Horizons — Cached"
    )


def test_rover_live_failure_falls_back_only_to_explicit_matching_nasa_cache():
    with patch(
        "horizons.fetch_ephemeris",
        side_effect=HorizonsResponseError("simulated network outage"),
    ) as fetch:
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.radio[0].set_value("Solar Rover Planner").run(timeout=30)
        widget_with_label(app.selectbox, "Ephemerides").set_value(
            "NASA JPL Horizons — Live"
        )
        app.form_submit_button[0].click().run(timeout=30)

    assert not app.exception
    assert not app.error
    assert fetch.call_count == 1
    assert any(
        "fixed real-NASA cache" in item.value
        and "simulated network outage" in item.value
        for item in app.warning
    )


def test_live_site_comparison_uses_each_site_coordinates_and_shared_period():
    frame_a = live_comparison_frame("2042-05-01", 0.0)
    frame_b = live_comparison_frame("2042-05-01", 0.5)
    with patch("horizons.fetch_ephemeris", side_effect=[frame_a, frame_b]) as fetch:
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.radio[0].set_value("Site Comparison").run(timeout=30)
        widget_with_label(app.selectbox, "Landing Site A").set_value(
            "Demo Ridge Alpha"
        )
        widget_with_label(app.selectbox, "Landing Site B").set_value(
            "Demo Plateau Beta"
        )
        widget_with_label(app.selectbox, "Duration").set_value(24)
        app.date_input[0].set_value(date(2042, 5, 1))
        app.form_submit_button[0].click().run(timeout=30)

        assert not app.exception
        assert fetch.call_count == 2
        assert len(app.get("plotly_chart")) == 2
        assert any("NASA JPL Horizons (Live)" in item.value for item in app.markdown)
        assert any("Above ideal horizon" in item.value for item in app.markdown)

        first_call, second_call = fetch.call_args_list
        assert first_call.args[:2] == (-89.4, 45.0)
        assert second_call.args[:2] == (-88.8, 120.0)
        assert first_call.args[2:] == second_call.args[2:]

        widget_with_label(
            app.select_slider,
            "Observation Time (UTC)",
        ).set_value(frame_a["time_utc"].iloc[-1])
        app.run(timeout=30)
        assert not app.exception
        assert fetch.call_count == 2


def test_comparison_reports_failed_site_without_synthetic_fallback():
    frame_a = live_comparison_frame("2043-06-01", 0.0)
    with patch(
        "horizons.fetch_ephemeris",
        side_effect=[frame_a, HorizonsNetworkError("offline Site B")],
    ):
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.radio[0].set_value("Site Comparison").run(timeout=30)
        app.date_input[0].set_value(date(2043, 6, 1))
        app.form_submit_button[0].click().run(timeout=30)

    assert not app.exception
    assert len(app.error) == 1
    assert "Site B (Demo Plateau Beta) failed" in app.error[0].value
    assert len(app.get("plotly_chart")) == 0
    assert any("did not substitute synthetic data" in item.value for item in app.info)


def test_demo_site_comparison_is_explicitly_disabled_without_network():
    with patch("horizons.fetch_ephemeris") as fetch:
        app = AppTest.from_file(ROOT / "app.py").run(timeout=30)
        app.radio[0].set_value("Site Comparison").run(timeout=30)
        widget_with_label(app.selectbox, "Data Source").set_value(
            "Demo (Synthetic)"
        )
        app.form_submit_button[0].click().run(timeout=30)

    assert not app.exception
    assert fetch.call_count == 0
    assert len(app.get("plotly_chart")) == 0
    assert len(app.warning) == 1
    assert "not site-specific" in app.warning[0].value


def test_user_interface_source_contains_no_cyrillic_text():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert re.search(r"[А-Яа-яЁё]", source) is None


def test_mobile_css_does_not_reserve_desktop_sidebar_width():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "margin-left: 248px !important" not in source
    assert "width: calc(100% - 248px) !important" not in source
    assert "max-width: 85vw" in source


def test_ui_uses_scientifically_qualified_visibility_language():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "Sunlight Availability" in source
    assert "Geometric proxy only; terrain not modeled" in source
    assert "Not a communications link budget" in source
    assert "not a flight-certified mission design system" in source
