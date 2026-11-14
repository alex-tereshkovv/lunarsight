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
    assert "missionPose(ms)" in _JS
    assert "ROVER_LOCAL_FORWARD_DEG=90" in _JS
    assert "Math.atan2(to.y-from.y,to.x-from.x)" in _JS
    assert "roverRotation(pose.heading)" in _JS
    assert "pose.travelledKm*1000" in _JS
    assert "WHEEL_RADIUS_METRES" in _JS
    assert "WHEEL_TRACK_METRES" in _JS
    assert _HTML.count('class="wheel-spinner"') == 6
    assert _HTML.count('class="wheel-tread"') == 6
    assert 'id="rover-model" transform="scale(.31)"' in _HTML
    assert 'data-forward-axis="positive-y"' in _HTML
    assert "Streamlit.setComponentValue" not in _JS
    assert "window.parent.postMessage" not in _JS


def test_route_overlay_and_rover_share_arc_length_geometry():
    assert "function buildRouteGeometry" in _JS
    assert "function pointAtArcFraction" in _JS
    assert "function tangentHeading" in _JS
    assert "routePath(geometry)" in _JS
    assert "curvedRoute" not in _JS
    assert " Q " not in _JS
    assert "route-network" in _CSS
    assert "route-active" in _CSS
    assert "route-progress" in _CSS
    assert "stroke-dasharray:9 7" in _CSS
    assert "activeProgress.forEach" in _JS


def test_all_visual_state_uses_one_mission_timestamp():
    assert "const displayMs=previewMs??missionMs" in _JS
    assert "syncData(displayMs" in _JS
    assert "paintPose(target)" in _JS
    assert "wheelSpinners.forEach" in _JS


def test_spotlight_remains_explicitly_conceptual():
    assert "Recommended Candidate Zone" in _HTML
    assert 'id="candidate-spotlight"' in _HTML
    assert 'id="spotlight-haze"' in _HTML
    assert ".spotlight-bloom" in _CSS
    assert "Conceptual visualization." in _HTML
    assert "No terrain shadows" in _HTML
