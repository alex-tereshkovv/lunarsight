"""Streamlit Components v2 renderer for the synchronized rover simulation."""

from __future__ import annotations

from collections.abc import Mapping

import streamlit as st


_HTML = """
<section class="rover-shell" aria-label="Interactive solar rover mission simulation">
  <header class="sim-header">
    <div class="header-copy">
      <span class="eyebrow">SHACKLETON–DE GERLACHE · VERIFIED STATIONS</span>
      <strong>Solar Rover Mission Playback</strong>
    </div>
    <div class="header-badges">
      <span id="source-badge" class="badge"></span>
      <time id="header-time" class="utc-badge"></time>
    </div>
  </header>

  <div class="workspace">
    <section class="map-card" aria-label="LOLA terrain map">
      <svg id="terrain-map" viewBox="0 0 1000 435" role="img"
           aria-label="Georeferenced NASA LOLA hillshade with published traverse stations">
        <defs>
          <radialGradient id="zone-glow" cx="50%" cy="48%" r="52%">
            <stop offset="0" stop-color="#fff4b0" stop-opacity=".84"></stop>
            <stop offset=".2" stop-color="#ffd85a" stop-opacity=".62"></stop>
            <stop offset=".52" stop-color="#f4ad28" stop-opacity=".25"></stop>
            <stop offset="1" stop-color="#e58b18" stop-opacity="0"></stop>
          </radialGradient>
          <linearGradient id="chassis-metal" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#fff2ba"></stop><stop offset=".46" stop-color="#caa64d"></stop><stop offset="1" stop-color="#725622"></stop>
          </linearGradient>
          <linearGradient id="panel-blue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#2359a0"></stop><stop offset="1" stop-color="#071d4b"></stop>
          </linearGradient>
          <filter id="rover-shadow" x="-90%" y="-90%" width="280%" height="280%">
            <feDropShadow dx="0" dy="4" stdDeviation="3.6" flood-color="#000" flood-opacity=".9"></feDropShadow>
            <feDropShadow dx="0" dy="0" stdDeviation="1.4" flood-color="#ffdf69" flood-opacity=".52"></feDropShadow>
          </filter>
          <filter id="spotlight-haze" x="-70%" y="-70%" width="240%" height="240%">
            <feGaussianBlur stdDeviation="9"></feGaussianBlur>
          </filter>
          <filter id="route-glow" x="-30%" y="-60%" width="160%" height="220%">
            <feGaussianBlur stdDeviation="2.3" result="blur"></feGaussianBlur>
            <feMerge><feMergeNode in="blur"></feMergeNode><feMergeNode in="SourceGraphic"></feMergeNode></feMerge>
          </filter>
        </defs>
        <image id="terrain-image" x="0" y="0" width="1000" height="435" preserveAspectRatio="none"></image>
        <rect x="0" y="0" width="1000" height="435" fill="#020712" opacity=".34"></rect>
        <g id="shackleton-main-label" class="crater-label" opacity="0">
          <text text-anchor="middle"><tspan x="0" y="-4">Shackleton</tspan><tspan x="0" y="12">Crater</tspan></text>
        </g>
        <g id="network-route-layer"></g>
        <g id="active-route-layer"></g>
        <g id="candidate-spotlight" opacity="0" aria-label="Mission focus">
          <ellipse class="spotlight-haze" rx="58" ry="48" fill="#e8a62b" opacity=".24" filter="url(#spotlight-haze)"></ellipse>
          <ellipse class="spotlight-bloom" rx="54" ry="44" fill="url(#zone-glow)"></ellipse>
          <circle class="spotlight-ring" r="16"></circle>
          <circle class="spotlight-core" r="5"></circle>
          <g class="spotlight-label" transform="translate(24 -39)">
            <rect x="0" y="0" width="154" height="24" rx="7"></rect>
            <circle cx="13" cy="12" r="4"></circle>
            <text id="spotlight-label-text" x="24" y="15">Recommended Candidate Zone</text>
          </g>
        </g>
        <g id="waypoint-layer"></g>
        <g id="rover" class="rover-wrap">
          <g id="rover-heading" filter="url(#rover-shadow)">
            <g id="rover-model" transform="scale(.27)" data-forward-axis="positive-y">
              <ellipse class="rover-ground-shadow" cx="0" cy="3" rx="30" ry="39"></ellipse>
              <g id="rover-vehicle">
                <g class="suspension" fill="none" stroke="#c6d2df" stroke-width="1.7">
                  <path d="M-15-20L-24-24M-17 0L-25 0M-15 20L-24 24M15-20L24-24M17 0L25 0M15 20L24 24"></path>
                </g>
                <g class="wheel" data-wheel="1" data-side="left" transform="translate(-27 -24)"><rect x="-4" y="-7" width="8" height="14" rx="3"></rect><g class="wheel-spinner"><circle r="2.4"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g><path class="wheel-tread" d="M-3-5h6M-3-1.7h6M-3 1.7h6M-3 5h6"></path></g>
                <g class="wheel" data-wheel="2" data-side="left" transform="translate(-28 0)"><rect x="-4" y="-7" width="8" height="14" rx="3"></rect><g class="wheel-spinner"><circle r="2.4"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g><path class="wheel-tread" d="M-3-5h6M-3-1.7h6M-3 1.7h6M-3 5h6"></path></g>
                <g class="wheel" data-wheel="3" data-side="left" transform="translate(-27 24)"><rect x="-4" y="-7" width="8" height="14" rx="3"></rect><g class="wheel-spinner"><circle r="2.4"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g><path class="wheel-tread" d="M-3-5h6M-3-1.7h6M-3 1.7h6M-3 5h6"></path></g>
                <g class="wheel" data-wheel="4" data-side="right" transform="translate(27 -24)"><rect x="-4" y="-7" width="8" height="14" rx="3"></rect><g class="wheel-spinner"><circle r="2.4"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g><path class="wheel-tread" d="M-3-5h6M-3-1.7h6M-3 1.7h6M-3 5h6"></path></g>
                <g class="wheel" data-wheel="5" data-side="right" transform="translate(28 0)"><rect x="-4" y="-7" width="8" height="14" rx="3"></rect><g class="wheel-spinner"><circle r="2.4"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g><path class="wheel-tread" d="M-3-5h6M-3-1.7h6M-3 1.7h6M-3 5h6"></path></g>
                <g class="wheel" data-wheel="6" data-side="right" transform="translate(27 24)"><rect x="-4" y="-7" width="8" height="14" rx="3"></rect><g class="wheel-spinner"><circle r="2.4"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g><path class="wheel-tread" d="M-3-5h6M-3-1.7h6M-3 1.7h6M-3 5h6"></path></g>
                <path class="chassis-outline" d="M-19-30L14-30 21-22 21 24 14 31-14 31-21 23-21-22Z"></path>
                <path class="chassis-deck" d="M-16-27H13L18-20V21L12 27H-13L-18 21V-20Z"></path>
                <g class="solar-panel">
                  <rect x="-14" y="-16" width="28" height="18" rx="1"></rect><path d="M-7-16V2M0-16V2M7-16V2M-14-10h28M-14-4h28"></path>
                  <rect x="-14" y="4" width="28" height="18" rx="1"></rect><path d="M-7 4v18M0 4v18M7 4v18M-14 10h28M-14 16h28"></path>
                </g>
                <rect class="electronics" x="5" y="-25" width="11" height="7" rx="1.5"></rect>
                <g class="mast" transform="translate(-8 -23)"><circle r="4.5"></circle><path d="M0 0V-18"></path><circle cy="-19" r="3.3"></circle></g>
                <path class="front-chevron" d="M-8 25H8L5 31H-5Z"></path>
                <circle class="camera" cx="0" cy="29" r="3"></circle>
              </g>
            </g>
          </g>
        </g>
        <g id="shackleton-overview" class="overview-card" transform="translate(808 50)">
          <rect width="174" height="142" rx="9"></rect>
          <image id="overview-image" x="4" y="4" width="166" height="134" preserveAspectRatio="xMidYMid slice"></image>
          <rect class="overview-shade" x="4" y="4" width="166" height="134" rx="6"></rect>
          <text class="overview-kicker" x="12" y="18">REGIONAL OVERVIEW · SEPARATE SCALE</text>
          <g class="crater-label" transform="translate(87 75)">
            <text text-anchor="middle"><tspan x="0" y="-4">Shackleton</tspan><tspan x="0" y="12">Crater</tspan></text>
          </g>
          <text class="overview-coordinate" x="87" y="128" text-anchor="middle">IAU centre · 89.67°S, 129.78°E</text>
        </g>
        <g class="map-label" transform="translate(18 18)">
          <rect width="312" height="55" rx="8"></rect>
          <text x="15" y="22">Shackleton–de Gerlache region</text>
          <text class="sub" x="15" y="42">NASA LOLA terrain hillshade · 5 m source DEM</text>
        </g>
        <g class="north" transform="translate(950 27)">
          <text x="12" y="-7" text-anchor="middle">N</text>
          <path d="M0 27l12-27 12 27-12-7Z" fill="#fff"></path>
        </g>
        <g id="scale-bar" class="scale-bar" transform="translate(28 392)">
          <line id="scale-line" x1="0" y1="0" x2="80" y2="0"></line>
          <line y1="-6" y2="6"></line><line id="scale-end" x1="80" x2="80" y1="-6" y2="6"></line>
          <text id="scale-label" x="40" y="20" text-anchor="middle">2 km</text>
        </g>
        <g class="map-legend" transform="translate(708 307)">
          <rect width="274" height="110" rx="8"></rect>
          <circle cx="18" cy="20" r="6" fill="none" stroke="#ffd43b" stroke-width="2.5"></circle>
          <text id="legend-focus-text" x="34" y="24">Recommended Candidate Zone</text>
          <circle cx="18" cy="47" r="5" fill="#8f69ff" stroke="#e5dcff" stroke-width="2"></circle>
          <text x="34" y="51">Rover Waypoint</text>
          <path d="M10 73h22" stroke="#f4f6f8" stroke-width="2" stroke-dasharray="6 5"></path>
          <text x="40" y="77">Planned Route · conceptual</text>
          <g transform="translate(18 96) scale(.22)"><rect x="-18" y="-12" width="36" height="24" rx="5" fill="#d7bb69"></rect><rect x="-12" y="-8" width="24" height="16" fill="#123a75"></rect><circle cx="-21" cy="-8" r="5" fill="#111"></circle><circle cx="21" cy="-8" r="5" fill="#111"></circle><circle cx="-21" cy="8" r="5" fill="#111"></circle><circle cx="21" cy="8" r="5" fill="#111"></circle></g>
          <text x="40" y="101">Rover · current position</text>
        </g>
      </svg>
      <div class="map-footer">
        <span id="spatial-note"></span>
        <span class="source-links"><a id="station-credit" target="_blank" rel="noopener noreferrer">Stations: NASA M2M-30044</a><a id="shackleton-credit" target="_blank" rel="noopener noreferrer">Shackleton: IAU/USGS</a><a id="map-credit" target="_blank" rel="noopener noreferrer"></a></span>
      </div>
    </section>

    <aside class="status-stack">
      <section class="status-card status-main">
        <div class="card-title"><span>ROVER STATUS</span><b id="motion-badge"></b></div>
        <dl>
          <div><dt>Current station</dt><dd id="current-waypoint"></dd></div><div><dt>Next station</dt><dd id="next-waypoint"></dd></div>
          <div><dt>Sun elevation</dt><dd id="sun-elevation"></dd></div><div><dt>Earth elevation</dt><dd id="earth-elevation"></dd></div>
          <div><dt>Dual visibility</dt><dd id="dual-status"></dd></div><div><dt>Travel estimate</dt><dd id="travel-time"></dd></div>
        </dl>
        <p id="decision-reason" class="reason"></p>
      </section>
      <section class="status-card mission-card">
        <div class="card-title"><span>MISSION TIMELINE</span></div>
        <dl>
          <div><dt>Scenario</dt><dd id="route-label"></dd></div><div><dt>Period</dt><dd id="mission-period"></dd></div>
          <div><dt>Sampling</dt><dd id="sampling"></dd></div><div><dt>Speed cap</dt><dd id="max-speed"></dd></div>
          <div><dt>Station coverage</dt><dd id="route-coverage"></dd></div><div><dt>Planned travel</dt><dd id="display-length"></dd></div>
        </dl>
      </section>
      <section class="status-card metrics-card">
        <div class="card-title"><span>KEY GEOMETRY</span></div>
        <dl><div><dt>Sun azimuth</dt><dd id="sun-azimuth"></dd></div><div><dt>Earth azimuth</dt><dd id="earth-azimuth"></dd></div><div><dt>Current UTC</dt><dd id="status-time"></dd></div></dl>
        <p class="limitation"><b>Conceptual visualization.</b> Geometric target-centre visibility only. No terrain shadows, verified traversability, energy storage, link budget, or hazard analysis.</p>
      </section>
    </aside>
  </div>

  <section class="timeline-card">
    <div class="timeline-title">
      <div><strong>Sun Elevation Along Planned Display Route</strong><span>Yellow: rover position · faint: scenario endpoints · purple: Earth above ideal horizon</span></div>
      <span class="horizon-key">– – 0° ideal horizon</span>
    </div>
    <div class="chart-wrap">
      <svg id="timeline" viewBox="0 0 1000 205" role="img" aria-label="Interactive UTC chart of real NASA Sun elevation and Earth visibility">
        <g id="earth-bands"></g><g id="grid-layer"></g><g id="alternate-series"></g><path id="main-series"></path>
        <line id="time-cursor" y1="18" y2="158"></line><circle id="cursor-dot" r="5.5"></circle>
        <rect id="interaction-surface" x="58" y="14" width="920" height="150" fill="transparent"></rect>
      </svg>
      <div id="chart-tooltip" class="chart-tooltip" hidden></div>
    </div>
  </section>

  <div class="playback-bar">
    <div class="playback-buttons"><button id="play" type="button" aria-label="Play">▶</button><button id="pause" type="button" aria-label="Pause">Ⅱ</button><button id="restart" type="button" aria-label="Restart">↻</button><button id="loop-toggle" type="button" aria-label="Loop playback" aria-pressed="false">Loop off</button></div>
    <div class="speed-control" role="group" aria-label="Playback speed"><span>Playback speed</span><button type="button" data-speed="1">1×</button><button type="button" data-speed="5">5×</button><button type="button" data-speed="20">20×</button><button type="button" data-speed="100">100×</button></div>
    <input id="mission-range" type="range" aria-label="Mission time" min="0" max="1000" value="0"><time id="playback-time" aria-label="Current mission UTC"></time>
  </div>
</section>
"""


_CSS = """
:host { color:var(--st-text-color,#eef4ff); font-family:var(--st-font,Inter,system-ui,sans-serif); }
* { box-sizing:border-box; } button,input { font:inherit; }
.rover-shell { --panel:#0b1627; --edge:#294661; --muted:#9dacc1; --purple:#956fff; --green:#43de91; --red:#ff6577; display:grid; grid-template-rows:46px 500px 205px 42px; gap:8px; width:100%; height:817px; overflow:hidden; }
.sim-header,.map-card,.status-card,.timeline-card,.playback-bar { border:1px solid var(--edge); border-radius:11px; background:linear-gradient(145deg,rgba(13,27,46,.98),rgba(5,13,25,.98)); box-shadow:0 10px 28px rgba(0,0,0,.22); }
.sim-header { display:flex; align-items:center; justify-content:space-between; padding:7px 13px; }.header-copy strong { display:block; margin-top:1px; font-size:15px; }.eyebrow { color:#a9bad1; font-size:8px; font-weight:800; letter-spacing:.18em; }.header-badges { display:flex; align-items:center; gap:7px; }
.badge,.utc-badge { border:1px solid #345573; border-radius:7px; padding:5px 9px; font-size:10px; white-space:nowrap; }.badge.nasa { color:#64f2b1; border-color:#267450; background:#09271e; }.badge.synthetic { color:#ffd57b; border-color:#85632d; background:#30230c; }.utc-badge { color:#dbe5f1; background:#0f1929; font-variant-numeric:tabular-nums; }
.workspace { display:grid; grid-template-columns:minmax(0,2.35fr) minmax(270px,.82fr); gap:8px; min-height:0; }.map-card { overflow:hidden; min-width:0; display:grid; grid-template-rows:minmax(0,1fr) 25px; }#terrain-map { display:block; width:100%; height:100%; min-height:0; background:#030711; }
.map-label rect,.map-legend rect { fill:rgba(4,10,20,.82); stroke:#72839a; stroke-width:1; }.map-label text { fill:#f4f7fb; font-size:14px; font-weight:750; }.map-label .sub { fill:#b6c2d1; font-size:9px; font-weight:500; }.map-legend text { fill:#dbe4ef; font-size:9px; }.north text,.scale-bar text { fill:#fff; font-size:10px; font-weight:750; }.scale-bar line { stroke:#fff; stroke-width:2; }
.overview-card > rect:first-child { fill:rgba(3,8,16,.92); stroke:#8da0b7; stroke-width:1; }.overview-shade { fill:rgba(2,6,12,.18); stroke:rgba(255,255,255,.3); stroke-width:.7; }.overview-kicker { fill:#dce8f6; font-size:6.5px; font-weight:800; letter-spacing:.08em; paint-order:stroke; stroke:#05080e; stroke-width:2px; }.overview-coordinate { fill:#c8d4e3; font-size:7px; paint-order:stroke; stroke:#05080e; stroke-width:2px; }.crater-label text { fill:#fff; font-size:12px; font-weight:800; letter-spacing:.02em; paint-order:stroke; stroke:rgba(0,0,0,.9); stroke-width:4px; filter:drop-shadow(0 2px 3px #000); }
.route-network,.route-active-underlay,.route-active,.route-progress { fill:none; stroke-linecap:round; stroke-linejoin:round; }
.route-network { stroke:#9a78e8; stroke-width:1.35; stroke-dasharray:3 7; opacity:.46; }
.route-active-underlay { stroke:#d9c8ff; stroke-width:6; opacity:.12; filter:url(#route-glow); }
.route-active { stroke:#fffaf0; stroke-width:2.05; stroke-dasharray:9 7; opacity:.95; filter:url(#route-glow); }
.route-progress { stroke:#ffd857; stroke-width:2.35; opacity:.92; filter:url(#route-glow); }
.waypoint .orbit { fill:none; stroke:#b69aff; stroke-width:1.15; opacity:.62; }.waypoint .halo { fill:#8f69ff; opacity:.16; filter:url(#route-glow); }.waypoint .core { fill:#8f69ff; stroke:#eee7ff; stroke-width:1.65; }.waypoint .pin { fill:#e5dcff; opacity:.78; }.waypoint text { fill:#fff; paint-order:stroke; stroke:#07101d; stroke-width:3.5px; font-size:9.5px; font-weight:800; letter-spacing:.02em; }.waypoint.active .core { fill:#ffd43b; stroke:#fff6c0; }.waypoint.active .halo { fill:#ffd43b; opacity:.3; }.waypoint.active .orbit { stroke:#ffe783; stroke-width:1.6; opacity:.9; }.waypoint.active .pin { fill:#fff5b0; opacity:1; }
#candidate-spotlight { pointer-events:none; transition:opacity .45s ease,transform .72s cubic-bezier(.2,.72,.22,1); transform-box:view-box; transform-origin:0 0; }.spotlight-bloom { mix-blend-mode:screen; }.spotlight-ring { fill:none; stroke:#ffe783; stroke-width:1.2; opacity:.22; }.spotlight-core { fill:#fff9cf; stroke:#ffc733; stroke-width:2; }.spotlight-label rect { fill:rgba(14,14,18,.84); stroke:#8d7131; stroke-width:1; }.spotlight-label circle { fill:#ffd43b; filter:url(#route-glow); }.spotlight-label text { fill:#fff8db; font-size:8px; font-weight:750; letter-spacing:.015em; }
.rover-wrap { pointer-events:none; }.rover-ground-shadow { fill:#000; opacity:.62; filter:blur(2px); }.suspension { opacity:.9; }.wheel-spinner { transform-box:fill-box; transform-origin:center; }.wheel rect { fill:#0a0e16; stroke:#cbd5e1; stroke-width:1.1; }.wheel circle { fill:#46505e; stroke:#f0f4f8; stroke-width:.8; }.wheel-spinner path { fill:none; stroke:#e7c65f; stroke-width:.8; stroke-linecap:round; }.wheel-tread { fill:none; stroke:#8993a2; stroke-width:.75; stroke-dasharray:1.7 1.2; }.chassis-outline { fill:#151b24; stroke:#f2d88a; stroke-width:1.2; }.chassis-deck { fill:url(#chassis-metal); stroke:#fff2b0; stroke-width:1.2; }.solar-panel rect { fill:url(#panel-blue); stroke:#75a9ff; stroke-width:.9; }.solar-panel path { fill:none; stroke:#739bdd; stroke-width:.55; opacity:.9; }.electronics { fill:#303844; stroke:#e9eef5; stroke-width:.7; }.mast path { fill:none; stroke:#eaf0f6; stroke-width:1.4; stroke-linecap:round; }.mast circle { fill:#c9d4df; stroke:#fff; stroke-width:.8; }.front-chevron { fill:#f7cc4d; stroke:#fff1a8; stroke-width:.9; }.camera { fill:#8de5ff; stroke:#fff; stroke-width:.8; }.rover-moving #rover-vehicle { animation:rover-breathe .72s ease-in-out infinite alternate; }
@keyframes rover-breathe { from { transform:translateY(-.6px) rotate(-.25deg); } to { transform:translateY(.75px) rotate(.25deg); } }
.map-footer { display:flex; align-items:center; justify-content:space-between; gap:10px; min-width:0; padding:4px 9px; border-top:1px solid #263e58; color:#9fadc0; font-size:8px; }.map-footer > span:first-child { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.map-footer a { color:#62c9ff; white-space:nowrap; }.source-links { display:flex; gap:10px; flex:0 0 auto; }
.status-stack { display:grid; grid-template-rows:1.22fr 1fr 1fr; gap:8px; min-height:0; }.status-card { min-height:0; padding:9px 11px; overflow:hidden; }.card-title { display:flex; align-items:center; justify-content:space-between; padding-bottom:5px; margin-bottom:4px; border-bottom:1px solid #273b54; color:#f2f6fb; font-size:10px; font-weight:850; letter-spacing:.07em; }.card-title b { padding:3px 6px; border:1px solid #326849; border-radius:5px; color:#69e5a6; background:#0b2a20; font-size:8px; }
dl { display:grid; gap:0; margin:0; } dl div { display:flex; justify-content:space-between; align-items:center; gap:10px; min-height:18px; border-bottom:1px solid rgba(49,69,94,.55); } dt { color:#aebbd0; font-size:8.5px; } dd { margin:0; color:#f0f5fb; text-align:right; font-size:9px; font-weight:720; font-variant-numeric:tabular-nums; }.positive { color:#55e99e!important; }.negative { color:#ff7181!important; }.reason { margin:5px 0 0; color:#cbd5e2; font-size:8px; line-height:1.3; font-style:italic; }.limitation { margin:5px 0 0; color:#aebccf; font-size:7.8px; line-height:1.35; }.limitation b { color:#b696ff; }
.timeline-card { overflow:hidden; display:grid; grid-template-rows:35px minmax(0,1fr); }.timeline-title { display:flex; justify-content:space-between; align-items:center; gap:10px; padding:6px 12px 3px; }.timeline-title strong { display:block; font-size:11px; }.timeline-title span { display:block; color:var(--muted); font-size:7.5px; margin-top:1px; }.horizon-key { white-space:nowrap; }.chart-wrap { position:relative; min-height:0; } #timeline { display:block; width:100%; height:100%; touch-action:none; user-select:none; }.grid-line { stroke:#29415d; stroke-width:1; opacity:.82; }.axis-label { fill:#9eacc0; font-size:8px; }.horizon { stroke:#e7edf5; stroke-width:1.4; stroke-dasharray:6 6; opacity:.8; }.earth-band { fill:#825fd0; opacity:.17; }.alternate-path { fill:none; stroke-width:1.15; opacity:.28; }.main-path { fill:none; stroke:#ffd43b; stroke-width:3; filter:drop-shadow(0 0 3px rgba(255,212,59,.34)); } #time-cursor { stroke:#fff; stroke-width:1.3; } #cursor-dot { fill:#ffd43b; stroke:#fff4b3; stroke-width:2; }.chart-tooltip { position:absolute; z-index:4; pointer-events:none; min-width:195px; padding:7px 9px; border:1px solid #527091; border-radius:7px; background:rgba(4,12,24,.96); color:#edf3fa; font-size:8.5px; line-height:1.45; box-shadow:0 8px 22px rgba(0,0,0,.42); }.tooltip-time { display:block; color:#fff; font-weight:800; margin-bottom:3px; }
.playback-bar { display:grid; grid-template-columns:auto auto minmax(120px,1fr) auto; align-items:center; gap:10px; padding:5px 10px; }.playback-buttons,.speed-control { display:flex; align-items:center; gap:5px; }.playback-bar button { min-width:27px; height:27px; border:1px solid #465c78; border-radius:7px; color:#e4ebf4; background:#111b2d; cursor:pointer; font-size:9px; }.playback-bar button.active { border-color:#9b79ff; color:#fff; background:#5d38bb; }#loop-toggle { min-width:58px; }#loop-toggle:disabled { cursor:not-allowed; opacity:.42; }.speed-control span { margin-right:2px; color:var(--muted); font-size:8px; }.playback-bar input { width:100%; accent-color:#8f69ff; }.playback-bar time { color:#e1e8f1; font-size:9px; font-variant-numeric:tabular-nums; white-space:nowrap; }
@media(max-width:900px){.rover-shell{height:auto;grid-template-rows:58px auto 220px 80px;overflow:visible}.workspace{grid-template-columns:1fr}.map-card{min-height:330px}.status-stack{grid-template-columns:repeat(3,minmax(0,1fr));grid-template-rows:auto}.playback-bar{grid-template-columns:auto 1fr}.header-badges{align-items:flex-end;flex-direction:column}.sim-header{align-items:flex-start}.mission-card dd{max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
@media(max-width:620px){.status-stack{grid-template-columns:1fr}.header-copy strong{font-size:13px}.map-legend{display:none}.playback-bar{grid-template-columns:1fr}.map-footer span{display:none}}
"""


_JS = """
const instances = new WeakMap()
const SVG_NS='http://www.w3.org/2000/svg'
const svg=(name,attrs={})=>{const node=document.createElementNS(SVG_NS,name);Object.entries(attrs).forEach(([key,value])=>node.setAttribute(key,String(value)));return node}
const clamp=(value,min,max)=>Math.max(min,Math.min(max,value))
const formatUtc=ms=>new Intl.DateTimeFormat('en-GB',{timeZone:'UTC',year:'numeric',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(ms)).replace(',','')+' UTC'
const shortUtc=ms=>new Intl.DateTimeFormat('en-GB',{timeZone:'UTC',month:'short',day:'2-digit',hour:'2-digit',hour12:false}).format(new Date(ms)).replace(',',' ')
function bracket(points,ms){let hi=points.findIndex(item=>item.ms>=ms);if(hi<0)hi=points.length-1;if(hi===0)return [points[0],points[0],0];const a=points[hi-1],b=points[hi],f=b.ms===a.ms?0:(ms-a.ms)/(b.ms-a.ms);return[a,b,clamp(f,0,1)]}
const lerp=(a,b,f)=>a+(b-a)*f
const angleDelta=(from,to)=>((to-from+540)%360)-180
const lerpAngle=(from,to,f)=>from+angleDelta(from,to)*f
function interpolated(points,ms){const[a,b,f]=bracket(points,ms);const out={...(f<.5?a:b)};['x','y','progress','sun_el','earth_el','sun_az','earth_az','distance_km','travel_hours'].forEach(key=>{if(Number.isFinite(a[key])&&Number.isFinite(b[key]))out[key]=lerp(a[key],b[key],f)});if(Number.isFinite(a.heading_deg)&&Number.isFinite(b.heading_deg))out.heading_deg=lerpAngle(a.heading_deg,b.heading_deg,f);return out}
const ROVER_LOCAL_FORWARD_DEG=90
const WHEEL_RADIUS_METRES=.28
const WHEEL_TRACK_METRES=1.65
const routeKey=(first,second)=>[first,second].sort().join('|')
const screenHeading=(from,to)=>(Math.atan2(to.y-from.y,to.x-from.x)*180/Math.PI+360)%360
const roverRotation=heading=>(heading-ROVER_LOCAL_FORWARD_DEG+360)%360
function buildRouteGeometry(first,second){const points=[{x:first.map_x*1000,y:first.map_y*435},{x:second.map_x*1000,y:second.map_y*435}],legs=[];let total=0;for(let index=1;index<points.length;index++){const from=points[index-1],to=points[index],length=Math.hypot(to.x-from.x,to.y-from.y);legs.push({from,to,start:total,end:total+length,length});total+=length}return{points,legs,total}}
function routePath(geometry){return geometry.points.map((point,index)=>`${index?'L':'M'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(' ')}
function pointAtArcFraction(geometry,fraction){const distance=clamp(fraction,0,1)*geometry.total,leg=geometry.legs.find(item=>distance<=item.end)||geometry.legs[geometry.legs.length-1],local=leg.length?clamp((distance-leg.start)/leg.length,0,1):0;return{x:lerp(leg.from.x,leg.to.x,local),y:lerp(leg.from.y,leg.to.y,local),heading:screenHeading(leg.from,leg.to)}}
function tangentHeading(geometry,fraction){const epsilon=Math.min(.012,8/Math.max(geometry.total,1)),before=pointAtArcFraction(geometry,Math.max(0,fraction-epsilon)),after=pointAtArcFraction(geometry,Math.min(1,fraction+epsilon));return screenHeading(before,after)}
const smoothstep=value=>{const x=clamp(value,0,1);return x*x*(3-2*x)}

function createController(root,data){
  data.startMs=Date.parse(data.start_utc);data.endMs=Date.parse(data.end_utc)
  data.states=data.states.map(item=>({...item,ms:Date.parse(item.time_utc)}));data.series=data.series.map(item=>({...item,points:item.points.map(point=>({...point,ms:Date.parse(point.time_utc)}))}));data.segments=data.segments.map(item=>({...item,startMs:Date.parse(item.start_utc),endMs:Date.parse(item.end_utc)}))
  const byId=Object.fromEntries(data.waypoints.map(item=>[item.id,item]));const q=id=>root.querySelector(id)
  q('#terrain-image').setAttribute('href',data.map_url);q('#spatial-note').textContent=data.spatial_note;q('#map-credit').textContent=data.map_credit;q('#map-credit').href=data.map_source_url;q('#station-credit').href=data.station_source_url;q('#shackleton-credit').href=data.shackleton.feature_source_url
  q('#overview-image').setAttribute('href',data.overview_url);const mainCraterLabel=q('#shackleton-main-label'),overview=q('#shackleton-overview');if(data.shackleton.inside_route_crop){mainCraterLabel.setAttribute('transform',`translate(${data.shackleton.map_x*1000} ${data.shackleton.map_y*435})`);mainCraterLabel.setAttribute('opacity','1');overview.setAttribute('display','none')}else{mainCraterLabel.setAttribute('opacity','0');overview.removeAttribute('display')}
  const source=q('#source-badge');source.textContent=data.source_label;source.className=`badge ${data.source_kind==='synthetic'?'synthetic':'nasa'}`
  const visited=data.route.visited_station_ids||data.route.station_ids,excluded=data.route.excluded_station_ids||[];q('#mission-period').textContent=`${shortUtc(data.startMs)} — ${shortUtc(data.endMs)}`;q('#sampling').textContent=`${data.sample_hours} h`;q('#max-speed').textContent=`${data.rover_speed_kmh.toFixed(2)} km/h`;q('#route-label').textContent=data.route.label;q('#route-coverage').textContent=`${visited.length}/${data.waypoints.length}${excluded.length?` · excludes ${excluded.join(', ')}`:''}`;q('#display-length').textContent=`${data.route.display_connector_length_km.toFixed(2)} km planned`;q('#legend-focus-text').textContent=data.route.spotlight_label;q('#spotlight-label-text').textContent=data.route.spotlight_label
  const scaleWidth=data.scale_bar.fraction*1000;q('#scale-line').setAttribute('x2',scaleWidth);q('#scale-end').setAttribute('x1',scaleWidth);q('#scale-end').setAttribute('x2',scaleWidth);q('#scale-label').setAttribute('x',scaleWidth/2);q('#scale-label').textContent=`${data.scale_bar.distance_km} km`
  const networkLayer=q('#network-route-layer'),activeLayer=q('#active-route-layer'),waypointLayer=q('#waypoint-layer'),routeIds=new Set(visited),geometryByKey=new Map(),activeProgress=[];networkLayer.replaceChildren();activeLayer.replaceChildren();waypointLayer.replaceChildren()
  data.connections.forEach(([first,second])=>{const geometry=buildRouteGeometry(byId[first],byId[second]),d=routePath(geometry);geometryByKey.set(routeKey(first,second),geometry);networkLayer.appendChild(svg('path',{d,class:'route-network'}))})
  const movingByEdge=new Map();data.segments.filter(item=>item.moving).forEach(segment=>{const key=routeKey(segment.from_id,segment.to_id);if(!movingByEdge.has(key))movingByEdge.set(key,[]);movingByEdge.get(key).push(segment)});movingByEdge.forEach((segments,key)=>{const segment=segments[0],geometry=buildRouteGeometry(byId[segment.from_id],byId[segment.to_id]),d=routePath(geometry);activeLayer.appendChild(svg('path',{d,class:'route-active-underlay'}));activeLayer.appendChild(svg('path',{d,class:'route-active'}));const progress=svg('path',{d,class:'route-progress',pathLength:'1','stroke-dasharray':'0 1','data-route-key':key});activeLayer.appendChild(progress);activeProgress.push({segments,node:progress})})
  data.waypoints.forEach(item=>{const mapX=item.map_x*1000,mapY=item.map_y*435,group=svg('g',{class:'waypoint','data-id':item.id,transform:`translate(${mapX} ${mapY})`});group.appendChild(svg('circle',{class:'halo',r:14}));group.appendChild(svg('circle',{class:'orbit',r:10.5}));group.appendChild(svg('circle',{class:'core',r:5.5}));group.appendChild(svg('circle',{class:'pin',r:1.7}));const labelRight=mapX<900,label=svg('text',{x:labelRight?11:-11,y:mapY<28?18:-11,'text-anchor':labelRight?'start':'end'});label.textContent=item.id;group.appendChild(label);waypointLayer.appendChild(group)})
  const plot={x:58,y:18,w:920,h:140};const allSun=[...data.states.map(item=>item.sun_el),...data.series.filter(item=>routeIds.has(item.id)).flatMap(item=>item.points.map(point=>point.sun_el))];let yMin=Math.min(-2,...allSun),yMax=Math.max(2,...allSun);const pad=Math.max(1,(yMax-yMin)*.13);yMin-=pad;yMax+=pad
  const xFor=ms=>plot.x+(ms-data.startMs)/(data.endMs-data.startMs)*plot.w;const yFor=value=>plot.y+plot.h-(value-yMin)/(yMax-yMin)*plot.h;const grid=q('#grid-layer');grid.replaceChildren();q('#earth-bands').replaceChildren();q('#alternate-series').replaceChildren()
  for(let i=0;i<=4;i++){const value=yMin+(yMax-yMin)*i/4,y=yFor(value);grid.appendChild(svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:y,y2:y,class:'grid-line'}));const label=svg('text',{x:plot.x-8,y:y+3,'text-anchor':'end',class:'axis-label'});label.textContent=`${value.toFixed(1)}°`;grid.appendChild(label)}for(let i=0;i<=6;i++){const ms=data.startMs+(data.endMs-data.startMs)*i/6,x=xFor(ms);grid.appendChild(svg('line',{x1:x,x2:x,y1:plot.y,y2:plot.y+plot.h,class:'grid-line'}));const label=svg('text',{x,y:183,'text-anchor':'middle',class:'axis-label'});label.textContent=shortUtc(ms);grid.appendChild(label)}grid.appendChild(svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:yFor(0),y2:yFor(0),class:'horizon'}))
  data.states.forEach((state,index)=>{if(state.earth_el<=0)return;const next=data.states[Math.min(index+1,data.states.length-1)];q('#earth-bands').appendChild(svg('rect',{x:xFor(state.ms),y:plot.y,width:Math.max(1,xFor(next.ms)-xFor(state.ms)+.5),height:plot.h,class:'earth-band'}))});data.series.filter(item=>routeIds.has(item.id)).forEach(item=>{const d=item.points.map((point,index)=>`${index?'L':'M'} ${xFor(point.ms).toFixed(2)} ${yFor(point.sun_el).toFixed(2)}`).join(' ');q('#alternate-series').appendChild(svg('path',{d,class:'alternate-path',stroke:item.color}))});const mainD=data.states.map((state,index)=>`${index?'L':'M'} ${xFor(state.ms).toFixed(2)} ${yFor(state.sun_el).toFixed(2)}`).join(' ');q('#main-series').setAttribute('d',mainD);q('#main-series').setAttribute('class','main-path')
  let missionMs=data.startMs,previewMs=null,previewEvent=null,playing=!window.matchMedia('(prefers-reduced-motion: reduce)').matches,speed=1,lastFrame=performance.now(),dragging=false,raf=0,loopDistanceKm=0,loopTurnRadians=0
  const rover=q('#rover'),roverHeading=q('#rover-heading'),spotlight=q('#candidate-spotlight'),cursor=q('#time-cursor'),dot=q('#cursor-dot'),range=q('#mission-range'),tooltip=q('#chart-tooltip'),wheelSpinners=[...root.querySelectorAll('.wheel-spinner')]
  const segmentIndexAt=ms=>{const found=data.segments.findIndex((item,index)=>item.startMs<=ms&&(ms<item.endMs||index===data.segments.length-1));return found<0?(ms<data.segments[0].startMs?0:data.segments.length-1):found}
  const geometryFor=segment=>buildRouteGeometry(byId[segment.from_id],byId[segment.to_id])
  const travelHeading=(segment,atEnd=false)=>tangentHeading(geometryFor(segment),atEnd?1:0)
  function previousTravelHeading(index){for(let cursorIndex=index-1;cursorIndex>=0;cursorIndex--){if(data.segments[cursorIndex].moving)return travelHeading(data.segments[cursorIndex],true)}return null}
  function nextTravelHeading(index){for(let cursorIndex=index+1;cursorIndex<data.segments.length;cursorIndex++){if(data.segments[cursorIndex].moving)return travelHeading(data.segments[cursorIndex],false)}return null}
  function loopIncomingHeading(){if(!data.route.closed_at_boundary)return null;for(let cursorIndex=data.segments.length-1;cursorIndex>=0;cursorIndex--){if(data.segments[cursorIndex].moving)return travelHeading(data.segments[cursorIndex],true)}return null}
  function travelledBefore(index){let distance=0;for(let cursorIndex=0;cursorIndex<index;cursorIndex++){if(data.segments[cursorIndex].moving)distance+=data.segments[cursorIndex].distance_km}return distance}
  function turnFor(index){const segment=data.segments[index];if(!segment?.moving)return 0;const target=travelHeading(segment),incoming=previousTravelHeading(index)??loopIncomingHeading()??target;return angleDelta(incoming,target)}
  function turnsBefore(index){let degrees=0;for(let cursorIndex=0;cursorIndex<index;cursorIndex++)degrees+=turnFor(cursorIndex);return degrees*Math.PI/180}
  function missionPose(ms){const index=segmentIndexAt(ms),segment=data.segments[index],travelledKm=travelledBefore(index),priorTurn=turnsBefore(index);if(!segment.moving||segment.from_id===segment.to_id){const station=byId[segment.to_id],heading=previousTravelHeading(index)??nextTravelHeading(index)??0;return{x:station.map_x*1000,y:station.map_y*435,heading,mode:'stationary',progress:0,travelledKm,turnRadians:priorTurn,segment}}
    const geometry=geometryFor(segment),raw=clamp((ms-segment.startMs)/(segment.endMs-segment.startMs),0,1),targetHeading=tangentHeading(geometry,0),incoming=previousTravelHeading(index)??loopIncomingHeading()??targetHeading,signedTurn=angleDelta(incoming,targetHeading),turnAngle=Math.abs(signedTurn),durationHours=(segment.endMs-segment.startMs)/3600000,driveHours=segment.distance_km/data.rover_speed_kmh,slackShare=clamp((durationHours-driveHours)/durationHours,0,.2),desiredShare=turnAngle>4?clamp(turnAngle/180*.14,.025,.14):0,turnShare=Math.min(desiredShare,slackShare)
    if(turnShare>0&&raw<turnShare){const turnFraction=smoothstep(raw/turnShare),point=pointAtArcFraction(geometry,0),heading=lerpAngle(incoming,targetHeading,turnFraction);return{...point,heading,mode:'turning',progress:0,travelledKm,turnRadians:priorTurn+signedTurn*Math.PI/180*turnFraction,segment}}
    const progress=turnShare>=1?1:clamp((raw-turnShare)/(1-turnShare),0,1),point=pointAtArcFraction(geometry,progress),heading=tangentHeading(geometry,progress);return{...point,heading,mode:progress>=1?'stationary':'moving',progress,travelledKm:travelledKm+segment.distance_km*progress,turnRadians:priorTurn+signedTurn*Math.PI/180,segment}}
  function routeProgress(ms){activeProgress.forEach(item=>{let progress=0;item.segments.forEach(segment=>{if(ms>=segment.endMs)progress=1;else if(ms>segment.startMs&&progress<1)progress=Math.max(progress,clamp((ms-segment.startMs)/(segment.endMs-segment.startMs),0,1))});item.node.setAttribute('stroke-dasharray',`${progress} 1`)})}
  function syncData(ms,showTip=false,event=null){const state=interpolated(data.states,ms),pose=missionPose(ms),cx=xFor(ms),active=pose.mode==='stationary'?pose.segment.to_id:(pose.progress<.5?pose.segment.from_id:pose.segment.to_id),activeSeries=data.series.find(item=>item.id===active),activePoint=activeSeries?interpolated(activeSeries.points,ms):state,focusId=byId[state.recommended_waypoint]?state.recommended_waypoint:active,focus=byId[focusId]||byId[active],focusSeries=data.series.find(item=>item.id===focusId),focusPoint=focusSeries?interpolated(focusSeries.points,ms):activePoint,candidate=focusPoint.sun_el>0&&focusPoint.earth_el>0;root.querySelectorAll('.waypoint').forEach(node=>node.classList.toggle('active',node.dataset.id===active));spotlight.style.transform=`translate(${focus.map_x*1000}px,${focus.map_y*435}px)`;spotlight.style.opacity=candidate?'.9':'.42';routeProgress(ms);cursor.setAttribute('x1',cx);cursor.setAttribute('x2',cx);dot.setAttribute('cx',cx);dot.setAttribute('cy',yFor(state.sun_el));const utc=formatUtc(ms);q('#header-time').textContent=`UTC ${utc.replace(' UTC','')}`;q('#status-time').textContent=utc;q('#playback-time').textContent=utc;q('#current-waypoint').textContent=active;q('#next-waypoint').textContent=pose.mode==='stationary'?(focusId===active?'—':focusId):pose.segment.to_id;q('#sun-elevation').textContent=`${state.sun_el>=0?'+':''}${state.sun_el.toFixed(2)}°`;q('#earth-elevation').textContent=`${state.earth_el>=0?'+':''}${state.earth_el.toFixed(2)}°`;q('#sun-azimuth').textContent=`${state.sun_az.toFixed(2)}°`;q('#earth-azimuth').textContent=`${state.earth_az.toFixed(2)}°`;q('#sun-elevation').className=state.sun_el>0?'positive':'negative';q('#earth-elevation').className=state.earth_el>0?'positive':'negative';const dual=state.sun_el>0&&state.earth_el>0;q('#dual-status').textContent=dual?'Yes · geometric':'No';q('#dual-status').className=dual?'positive':'negative';q('#motion-badge').textContent=pose.mode.toUpperCase();q('#travel-time').textContent=pose.segment.moving?`${((pose.segment.endMs-pose.segment.startMs)/3600000).toFixed(1)} h · ${pose.segment.distance_km.toFixed(2)} km`:'—';q('#decision-reason').textContent=pose.segment.reason;range.value=String(Math.round((ms-data.startMs)/(data.endMs-data.startMs)*1000));q('#play').classList.toggle('active',playing);q('#pause').classList.toggle('active',!playing);if(showTip&&event){tooltip.innerHTML=`<span class="tooltip-time">${utc}</span><div>Sun: ${state.sun_el>=0?'+':''}${state.sun_el.toFixed(2)}° · az ${state.sun_az.toFixed(2)}°</div><div>Earth: ${state.earth_el>=0?'+':''}${state.earth_el.toFixed(2)}° · az ${state.earth_az.toFixed(2)}°</div><div>Station: ${active} · ${dual?'dual geometric visibility':'no dual visibility'}</div>`;tooltip.hidden=false;const box=q('.chart-wrap').getBoundingClientRect();tooltip.style.left=`${clamp(event.clientX-box.left+10,4,box.width-230)}px`;tooltip.style.top=`${clamp(event.clientY-box.top-55,3,box.height-80)}px`}else tooltip.hidden=true;return{state,pose}}
  function paintPose(target){const pose=target.pose,distanceKm=pose.travelledKm+loopDistanceKm,turnRadians=pose.turnRadians+loopTurnRadians,leftMetres=distanceKm*1000-turnRadians*WHEEL_TRACK_METRES/2,rightMetres=distanceKm*1000+turnRadians*WHEEL_TRACK_METRES/2;rover.setAttribute('transform',`translate(${pose.x.toFixed(2)} ${pose.y.toFixed(2)})`);roverHeading.setAttribute('transform',`rotate(${roverRotation(pose.heading).toFixed(2)})`);rover.classList.toggle('rover-moving',pose.mode==='moving');rover.classList.toggle('rover-turning',pose.mode==='turning');wheelSpinners.forEach(spinner=>{const side=spinner.closest('.wheel').dataset.side,distance=side==='left'?leftMetres:rightMetres,degrees=(distance/(2*Math.PI*WHEEL_RADIUS_METRES)*360)%360;spinner.style.transform=`rotate(${degrees.toFixed(2)}deg)`;const tread=spinner.closest('.wheel').querySelector('.wheel-tread');if(tread)tread.style.strokeDashoffset=`${(-distance/.18).toFixed(2)}`})}
  // The rover gets one clock; Streamlit does not need sixty reruns per second.
  const missionDistanceKm=data.segments.filter(item=>item.moving).reduce((sum,item)=>sum+item.distance_km,0),missionTurnRadians=turnsBefore(data.segments.length);let loopEnabled=Boolean(data.route.loop_playback_default&&data.route.closed_at_boundary)
  function frame(now){const delta=Math.min(80,Math.max(0,now-lastFrame));lastFrame=now;if(playing&&!dragging&&previewMs===null){missionMs+=delta*3600*speed;if(missionMs>=data.endMs){if(loopEnabled&&data.route.closed_at_boundary){loopDistanceKm+=missionDistanceKm;loopTurnRadians+=missionTurnRadians;missionMs=data.startMs+(missionMs-data.startMs)%(data.endMs-data.startMs)}else{missionMs=data.endMs;playing=false}}}const displayMs=previewMs??missionMs,target=syncData(displayMs,previewMs!==null,previewEvent);paintPose(target);raf=requestAnimationFrame(frame)}
  const surface=q('#interaction-surface'),pointerTime=event=>{const rect=surface.getBoundingClientRect();return data.startMs+clamp((event.clientX-rect.left)/rect.width,0,1)*(data.endMs-data.startMs)}
  surface.onpointermove=event=>{previewEvent=event;const ms=pointerTime(event);if(dragging)missionMs=ms;previewMs=ms}
  surface.onpointerdown=event=>{dragging=true;surface.setPointerCapture(event.pointerId);missionMs=pointerTime(event);previewMs=missionMs;previewEvent=event}
  surface.onpointerup=event=>{dragging=false;missionMs=pointerTime(event);previewMs=null;previewEvent=null}
  surface.onpointerleave=()=>{if(!dragging){previewMs=null;previewEvent=null;tooltip.hidden=true}}
  q('#play').onclick=()=>{playing=true;lastFrame=performance.now()};q('#pause').onclick=()=>{playing=false};q('#restart').onclick=()=>{playing=false;missionMs=data.startMs;previewMs=null;previewEvent=null;loopDistanceKm=0;loopTurnRadians=0}
  const loopButton=q('#loop-toggle');loopButton.disabled=!data.route.closed_at_boundary;loopButton.title=data.route.closed_at_boundary?'Repeat playback without changing mission timestamps':'Loop playback requires a route that ends at its start';function paintLoopButton(){loopButton.textContent=loopEnabled?'Loop on':'Loop off';loopButton.classList.toggle('active',loopEnabled);loopButton.setAttribute('aria-pressed',String(loopEnabled))}paintLoopButton();loopButton.onclick=()=>{if(!data.route.closed_at_boundary)return;loopEnabled=!loopEnabled;paintLoopButton()}
  root.querySelectorAll('[data-speed]').forEach(button=>button.onclick=()=>{speed=Number(button.dataset.speed);root.querySelectorAll('[data-speed]').forEach(item=>item.classList.toggle('active',item===button))});root.querySelector('[data-speed="1"]').classList.add('active')
  range.oninput=event=>{missionMs=data.startMs+Number(event.target.value)/1000*(data.endMs-data.startMs);previewMs=null;previewEvent=null;loopDistanceKm=0;loopTurnRadians=0}
  const initial=syncData(missionMs);paintPose(initial);raf=requestAnimationFrame(frame);return{destroy(){cancelAnimationFrame(raf)}}}
export default function(component){const{data,parentElement}=component;const root=parentElement.querySelector('.rover-shell');if(!root||!data)return;const previous=instances.get(parentElement);if(previous)previous.destroy();const controller=createController(root,data);instances.set(parentElement,controller);return()=>controller.destroy()}
"""


_SOLAR_ROVER_COMPONENT = st.components.v2.component(
    "lunarsight_solar_rover_planner",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def solar_rover_simulation(
    scenario: Mapping[str, object],
    *,
    key: str = "solar_rover_simulation",
) -> object:
    """Mount the synchronized client-side rover simulation."""
    return _SOLAR_ROVER_COMPONENT(
        data=dict(scenario),
        key=key,
        width="stretch",
        height="content",
    )
