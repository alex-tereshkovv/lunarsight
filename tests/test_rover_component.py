"""Regression checks for the browser-only Solar Rover component."""

from rover_component import _CSS, _HTML, _JS


def test_rover_svg_has_six_wheels_and_mission_hardware():
    assert _HTML.count('class="wheel"') == 6
    assert 'class="solar-panel"' in _HTML
    assert 'class="mast"' in _HTML
    assert 'class="camera"' in _HTML
    assert 'id="rover-heading"' in _HTML


def test_animation_is_client_side_smooth_and_rotates_wheels():
    assert "requestAnimationFrame(frame)" in _JS
    assert "lerpAngle" in _JS
    assert "Math.exp(-delta/78)" in _JS
    assert "wheelAngle" in _JS
    assert "if(rolling)" in _JS
    assert "Streamlit.setComponentValue" not in _JS
    assert "window.parent.postMessage" not in _JS


def test_route_overlay_uses_curves_and_visual_hierarchy():
    assert "function curvedRoute" in _JS
    assert " Q " in _JS
    assert "route-network" in _CSS
    assert "route-active" in _CSS
    assert "route-progress" in _CSS
    assert "stroke-dasharray:9 7" in _CSS


def test_spotlight_remains_explicitly_conceptual():
    assert "Recommended Candidate Zone" in _HTML
    assert 'id="candidate-spotlight"' in _HTML
    assert 'id="spotlight-haze"' in _HTML
    assert ".spotlight-bloom" in _CSS
    assert "Conceptual visualization." in _HTML
    assert "No terrain shadows" in _HTML
