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
        <g id="network-route-layer"></g>
        <g id="active-route-layer"></g>
        <g id="candidate-spotlight" opacity="0" aria-label="Recommended Candidate Zone">
          <ellipse class="spotlight-haze" rx="82" ry="66" fill="#e8a62b" opacity=".28" filter="url(#spotlight-haze)"></ellipse>
          <ellipse class="spotlight-bloom" rx="76" ry="61" fill="url(#zone-glow)"></ellipse>
          <circle class="spotlight-ring" r="20"></circle>
          <circle class="spotlight-core" r="5"></circle>
          <g class="spotlight-label" transform="translate(24 -39)">
            <rect x="0" y="0" width="154" height="24" rx="7"></rect>
            <circle cx="13" cy="12" r="4"></circle>
            <text x="24" y="15">Recommended Candidate Zone</text>
          </g>
        </g>
        <g id="waypoint-layer"></g>
        <g id="rover" class="rover-wrap">
          <g id="rover-heading" filter="url(#rover-shadow)">
            <ellipse class="rover-ground-shadow" cx="-1" cy="5" rx="34" ry="23"></ellipse>
            <g id="rover-vehicle">
              <g class="suspension" fill="none" stroke="#c6d2df" stroke-width="1.4">
                <path d="M-20-11L-25-20M0-13V-22M20-11L25-20M-20 11L-25 20M0 13V22M20 11L25 20"></path>
              </g>
              <g class="wheel" data-wheel="1" transform="translate(-25 -21)"><rect x="-6" y="-3.8" width="12" height="7.6" rx="3"></rect><circle r="2.3"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g>
              <g class="wheel" data-wheel="2" transform="translate(0 -23)"><rect x="-6" y="-3.8" width="12" height="7.6" rx="3"></rect><circle r="2.3"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g>
              <g class="wheel" data-wheel="3" transform="translate(25 -21)"><rect x="-6" y="-3.8" width="12" height="7.6" rx="3"></rect><circle r="2.3"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g>
              <g class="wheel" data-wheel="4" transform="translate(-25 21)"><rect x="-6" y="-3.8" width="12" height="7.6" rx="3"></rect><circle r="2.3"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g>
              <g class="wheel" data-wheel="5" transform="translate(0 23)"><rect x="-6" y="-3.8" width="12" height="7.6" rx="3"></rect><circle r="2.3"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g>
              <g class="wheel" data-wheel="6" transform="translate(25 21)"><rect x="-6" y="-3.8" width="12" height="7.6" rx="3"></rect><circle r="2.3"></circle><path d="M-2.2 0h4.4M0-2.2v4.4"></path></g>
              <path class="chassis-outline" d="M-22-15L18-15 27-8 27 8 18 15-22 15-27 9-27-9Z"></path>
              <rect class="chassis-deck" x="-21" y="-13" width="41" height="26" rx="5"></rect>
              <g class="solar-panel">
                <rect x="-17" y="-10" width="13" height="20" rx="1"></rect><path d="M-10.5-10v20M-17-3.3h13M-17 3.3h13"></path>
                <rect x="3" y="-10" width="13" height="20" rx="1"></rect><path d="M9.5-10v20M3-3.3h13M3 3.3h13"></path>
              </g>
              <rect class="electronics" x="-1.5" y="-7" width="5" height="14" rx="1.5"></rect>
              <g class="mast" transform="translate(18 -2)">
                <path d="M0 0L8-10"></path><circle cx="8" cy="-10" r="3.7"></circle><path d="M8-10l8-3-5 7Z"></path>
              </g>
              <path class="front-chevron" d="M22-7L31 0 22 7Z"></path>
              <circle class="camera" cx="22" cy="0" r="2.2"></circle>
            </g>
          </g>
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
        <g class="map-legend" transform="translate(708 347)">
          <rect width="274" height="70" rx="8"></rect>
          <circle cx="18" cy="20" r="6" fill="none" stroke="#ffd43b" stroke-width="2.5"></circle>
          <text x="34" y="24">Recommended Candidate Zone</text>
          <path d="M10 47h22" stroke="#f4f6f8" stroke-width="2" stroke-dasharray="6 5"></path>
          <text x="40" y="51">Conceptual station link</text>
        </g>
      </svg>
      <div class="map-footer">
        <span id="spatial-note"></span>
        <span class="source-links"><a id="station-credit" target="_blank" rel="noopener noreferrer">Stations: NASA M2M-30044</a><a id="map-credit" target="_blank" rel="noopener noreferrer"></a></span>
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
          <div><dt>NASA traverse</dt><dd id="official-length"></dd></div><div><dt>Display link</dt><dd id="display-length"></dd></div>
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
    <div class="playback-buttons"><button id="play" type="button" aria-label="Play">▶</button><button id="pause" type="button" aria-label="Pause">Ⅱ</button><button id="restart" type="button" aria-label="Restart">↻</button></div>
    <div class="speed-control" role="group" aria-label="Playback speed"><span>Playback</span><button type="button" data-speed="1">1×</button><button type="button" data-speed="5">5×</button><button type="button" data-speed="20">20×</button><button type="button" data-speed="100">100×</button></div>
    <input id="mission-range" type="range" aria-label="Mission time" min="0" max="1000" value="0"><time id="playback-time"></time>
  </div>
</section>
"""


_CSS = """
:host { color:var(--st-text-color,#eef4ff); font-family:var(--st-font,Inter,system-ui,sans-serif); }
* { box-sizing:border-box; } button,input { font:inherit; }
.rover-shell { --panel:#0b1627; --edge:#294661; --muted:#9dacc1; --purple:#956fff; --green:#43de91; --red:#ff6577; display:grid; grid-template-rows:46px 500px 205px 42px; gap:8px; width:100%; height:817px; overflow:hidden; }
.sim-header,.map-card,.status-card,.timeline-card,.playback-bar { border:1px solid var(--edge); border-radius:11px; background:linear-gradient(145deg,rgba(13,27,46,.98),rgba(5,13,25,.98)); box-shadow:0 10px 28px rgba(0,0,0,.22); }
.sim-header { display:flex; align-items:center; justify-content:space-between; padding:7px 13px; }.header-copy strong { display:block; margin-top:1px; font-size:15px; }.eyebrow { color:#a9bad1; font-size:8px; font-weight:800; letter-spacing:.18em; }.header-badges { display:flex; align-items:center; gap:7px; }
.badge,.utc-badge { border:1px solid #345573; border-radius:7px; padding:5px 9px; font-size:10px; white-space:nowrap; }.badge.nasa { color:#64f2b1; border-color:#267450; background:#09271e; }.utc-badge { color:#dbe5f1; background:#0f1929; font-variant-numeric:tabular-nums; }
.workspace { display:grid; grid-template-columns:minmax(0,2.35fr) minmax(270px,.82fr); gap:8px; min-height:0; }.map-card { overflow:hidden; min-width:0; display:grid; grid-template-rows:minmax(0,1fr) 25px; }#terrain-map { display:block; width:100%; height:100%; min-height:0; background:#030711; }
.map-label rect,.map-legend rect { fill:rgba(4,10,20,.82); stroke:#72839a; stroke-width:1; }.map-label text { fill:#f4f7fb; font-size:14px; font-weight:750; }.map-label .sub { fill:#b6c2d1; font-size:9px; font-weight:500; }.map-legend text { fill:#dbe4ef; font-size:9px; }.north text,.scale-bar text { fill:#fff; font-size:10px; font-weight:750; }.scale-bar line { stroke:#fff; stroke-width:2; }
.route-network,.route-active-underlay,.route-active,.route-progress { fill:none; stroke-linecap:round; stroke-linejoin:round; }
.route-network { stroke:#9a78e8; stroke-width:1.35; stroke-dasharray:3 7; opacity:.46; }
.route-active-underlay { stroke:#d9c8ff; stroke-width:6; opacity:.12; filter:url(#route-glow); }
.route-active { stroke:#fffaf0; stroke-width:2.05; stroke-dasharray:9 7; opacity:.95; filter:url(#route-glow); }
.route-progress { stroke:#ffd857; stroke-width:2.35; opacity:.92; filter:url(#route-glow); }
.waypoint .orbit { fill:none; stroke:#a987ff; stroke-width:1.2; opacity:.5; }.waypoint .halo { fill:#8f69ff; opacity:.18; }.waypoint .core { fill:#8f69ff; stroke:#e5dcff; stroke-width:2; }.waypoint .pin { fill:#d7ccff; opacity:.7; }.waypoint text { fill:#fff; paint-order:stroke; stroke:#07101d; stroke-width:4px; font-size:11px; font-weight:800; letter-spacing:.02em; }.waypoint.active .core { fill:#ffd43b; stroke:#fff6c0; }.waypoint.active .halo { fill:#ffd43b; opacity:.35; }.waypoint.active .orbit { stroke:#ffe783; stroke-width:1.8; opacity:.9; }.waypoint.active .pin { fill:#fff5b0; opacity:1; }
#candidate-spotlight { pointer-events:none; transition:opacity .45s ease,transform .72s cubic-bezier(.2,.72,.22,1); transform-box:view-box; transform-origin:0 0; }.spotlight-bloom { mix-blend-mode:screen; }.spotlight-ring { fill:none; stroke:#ffe783; stroke-width:2.2; opacity:.95; filter:url(#route-glow); }.spotlight-core { fill:#fff9cf; stroke:#ffc733; stroke-width:2; }.spotlight-label rect { fill:rgba(14,14,18,.84); stroke:#8d7131; stroke-width:1; }.spotlight-label circle { fill:#ffd43b; filter:url(#route-glow); }.spotlight-label text { fill:#fff8db; font-size:8px; font-weight:750; letter-spacing:.015em; }
.rover-wrap { pointer-events:none; }.rover-ground-shadow { fill:#000; opacity:.6; filter:blur(2px); }.suspension { opacity:.9; }.wheel { transform-box:fill-box; transform-origin:center; }.wheel rect { fill:#0b1019; stroke:#d4ddea; stroke-width:1.1; }.wheel circle { fill:#424c5d; stroke:#f0f4f8; stroke-width:.8; }.wheel path { fill:none; stroke:#f5dc76; stroke-width:.8; stroke-linecap:round; }.chassis-outline { fill:#131a24; stroke:#f8e9a4; stroke-width:1.2; }.chassis-deck { fill:url(#chassis-metal); stroke:#fff2b0; stroke-width:1.2; }.solar-panel rect { fill:url(#panel-blue); stroke:#75a9ff; stroke-width:.9; }.solar-panel path { fill:none; stroke:#5f8fda; stroke-width:.55; opacity:.9; }.electronics { fill:#2f3945; stroke:#e9eef5; stroke-width:.7; }.mast path { fill:none; stroke:#eaf0f6; stroke-width:1.2; stroke-linecap:round; }.mast circle { fill:#c9d4df; stroke:#fff; stroke-width:.8; }.front-chevron { fill:#f7cc4d; stroke:#fff1a8; stroke-width:.9; }.camera { fill:#8de5ff; stroke:#fff; stroke-width:.8; }.rover-moving #rover-vehicle { animation:rover-breathe .72s ease-in-out infinite alternate; }
@keyframes rover-breathe { from { transform:translateY(-.6px) rotate(-.25deg); } to { transform:translateY(.75px) rotate(.25deg); } }
.map-footer { display:flex; align-items:center; justify-content:space-between; gap:10px; min-width:0; padding:4px 9px; border-top:1px solid #263e58; color:#9fadc0; font-size:8px; }.map-footer > span:first-child { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.map-footer a { color:#62c9ff; white-space:nowrap; }.source-links { display:flex; gap:10px; flex:0 0 auto; }
.status-stack { display:grid; grid-template-rows:1.22fr 1fr 1fr; gap:8px; min-height:0; }.status-card { min-height:0; padding:9px 11px; overflow:hidden; }.card-title { display:flex; align-items:center; justify-content:space-between; padding-bottom:5px; margin-bottom:4px; border-bottom:1px solid #273b54; color:#f2f6fb; font-size:10px; font-weight:850; letter-spacing:.07em; }.card-title b { padding:3px 6px; border:1px solid #326849; border-radius:5px; color:#69e5a6; background:#0b2a20; font-size:8px; }
dl { display:grid; gap:0; margin:0; } dl div { display:flex; justify-content:space-between; align-items:center; gap:10px; min-height:18px; border-bottom:1px solid rgba(49,69,94,.55); } dt { color:#aebbd0; font-size:8.5px; } dd { margin:0; color:#f0f5fb; text-align:right; font-size:9px; font-weight:720; font-variant-numeric:tabular-nums; }.positive { color:#55e99e!important; }.negative { color:#ff7181!important; }.reason { margin:5px 0 0; color:#cbd5e2; font-size:8px; line-height:1.3; font-style:italic; }.limitation { margin:5px 0 0; color:#aebccf; font-size:7.8px; line-height:1.35; }.limitation b { color:#b696ff; }
.timeline-card { overflow:hidden; display:grid; grid-template-rows:35px minmax(0,1fr); }.timeline-title { display:flex; justify-content:space-between; align-items:center; gap:10px; padding:6px 12px 3px; }.timeline-title strong { display:block; font-size:11px; }.timeline-title span { display:block; color:var(--muted); font-size:7.5px; margin-top:1px; }.horizon-key { white-space:nowrap; }.chart-wrap { position:relative; min-height:0; } #timeline { display:block; width:100%; height:100%; touch-action:none; user-select:none; }.grid-line { stroke:#29415d; stroke-width:1; opacity:.82; }.axis-label { fill:#9eacc0; font-size:8px; }.horizon { stroke:#e7edf5; stroke-width:1.4; stroke-dasharray:6 6; opacity:.8; }.earth-band { fill:#825fd0; opacity:.17; }.alternate-path { fill:none; stroke-width:1.15; opacity:.28; }.main-path { fill:none; stroke:#ffd43b; stroke-width:3; filter:drop-shadow(0 0 3px rgba(255,212,59,.34)); } #time-cursor { stroke:#fff; stroke-width:1.3; } #cursor-dot { fill:#ffd43b; stroke:#fff4b3; stroke-width:2; }.chart-tooltip { position:absolute; z-index:4; pointer-events:none; min-width:195px; padding:7px 9px; border:1px solid #527091; border-radius:7px; background:rgba(4,12,24,.96); color:#edf3fa; font-size:8.5px; line-height:1.45; box-shadow:0 8px 22px rgba(0,0,0,.42); }.tooltip-time { display:block; color:#fff; font-weight:800; margin-bottom:3px; }
.playback-bar { display:grid; grid-template-columns:auto auto minmax(120px,1fr) auto; align-items:center; gap:10px; padding:5px 10px; }.playback-buttons,.speed-control { display:flex; align-items:center; gap:5px; }.playback-bar button { min-width:27px; height:27px; border:1px solid #465c78; border-radius:7px; color:#e4ebf4; background:#111b2d; cursor:pointer; font-size:9px; }.playback-bar button.active { border-color:#9b79ff; color:#fff; background:#5d38bb; }.speed-control span { margin-right:2px; color:var(--muted); font-size:8px; }.playback-bar input { width:100%; accent-color:#8f69ff; }.playback-bar time { color:#e1e8f1; font-size:9px; font-variant-numeric:tabular-nums; white-space:nowrap; }
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
function curvedRoute(a,b,bend=1){const ax=a.map_x*1000,ay=a.map_y*435,bx=b.map_x*1000,by=b.map_y*435,dx=bx-ax,dy=by-ay,length=Math.max(1,Math.hypot(dx,dy)),offset=clamp(length*.085,10,30)*bend,mx=(ax+bx)/2-dy/length*offset,my=(ay+by)/2+dx/length*offset;return`M ${ax.toFixed(2)} ${ay.toFixed(2)} Q ${mx.toFixed(2)} ${my.toFixed(2)} ${bx.toFixed(2)} ${by.toFixed(2)}`}

function createController(root,data){
  data.startMs=Date.parse(data.start_utc);data.endMs=Date.parse(data.end_utc)
  data.states=data.states.map(item=>({...item,ms:Date.parse(item.time_utc)}));data.series=data.series.map(item=>({...item,points:item.points.map(point=>({...point,ms:Date.parse(point.time_utc)}))}))
  const byId=Object.fromEntries(data.waypoints.map(item=>[item.id,item]));const q=id=>root.querySelector(id)
  q('#terrain-image').setAttribute('href',data.map_url);q('#spatial-note').textContent=data.spatial_note;q('#map-credit').textContent=data.map_credit;q('#map-credit').href=data.map_source_url;q('#station-credit').href=data.station_source_url
  const source=q('#source-badge');source.textContent=data.source_label;source.classList.add('nasa')
  q('#mission-period').textContent=`${shortUtc(data.startMs)} — ${shortUtc(data.endMs)}`;q('#sampling').textContent=`${data.sample_hours} h`;q('#max-speed').textContent=`${data.rover_speed_kmh.toFixed(2)} km/h`;q('#route-label').textContent=data.route.label;q('#official-length').textContent=`${data.route.official_traverse_length_km.toFixed(2)} km (published)`;q('#display-length').textContent=`${data.route.display_connector_length_km.toFixed(2)} km (straight)`
  const scaleWidth=data.scale_bar.fraction*1000;q('#scale-line').setAttribute('x2',scaleWidth);q('#scale-end').setAttribute('x1',scaleWidth);q('#scale-end').setAttribute('x2',scaleWidth);q('#scale-label').setAttribute('x',scaleWidth/2);q('#scale-label').textContent=`${data.scale_bar.distance_km} km`
  const networkLayer=q('#network-route-layer'),activeLayer=q('#active-route-layer'),waypointLayer=q('#waypoint-layer'),routeIds=new Set(data.route.station_ids);let activeProgress=null
  data.connections.forEach(([first,second],index)=>{const a=byId[first],b=byId[second],d=curvedRoute(a,b,index%2===0?1:-1),isActive=routeIds.has(first)&&routeIds.has(second);networkLayer.appendChild(svg('path',{d,class:'route-network'}));if(isActive){activeLayer.appendChild(svg('path',{d,class:'route-active-underlay'}));activeLayer.appendChild(svg('path',{d,class:'route-active'}));activeProgress=svg('path',{d,class:'route-progress',pathLength:'1','stroke-dasharray':'0 1'});activeLayer.appendChild(activeProgress)}})
  data.waypoints.forEach(item=>{const mapX=item.map_x*1000,mapY=item.map_y*435,group=svg('g',{class:'waypoint','data-id':item.id,transform:`translate(${mapX} ${mapY})`});group.appendChild(svg('circle',{class:'halo',r:14}));group.appendChild(svg('circle',{class:'orbit',r:10.5}));group.appendChild(svg('circle',{class:'core',r:5.5}));group.appendChild(svg('circle',{class:'pin',r:1.7}));const labelRight=mapX<900,label=svg('text',{x:labelRight?11:-11,y:mapY<28?18:-11,'text-anchor':labelRight?'start':'end'});label.textContent=item.id;group.appendChild(label);waypointLayer.appendChild(group)})
  const plot={x:58,y:18,w:920,h:140};const allSun=[...data.states.map(item=>item.sun_el),...data.series.filter(item=>data.route.station_ids.includes(item.id)).flatMap(item=>item.points.map(point=>point.sun_el))];let yMin=Math.min(-2,...allSun),yMax=Math.max(2,...allSun);const pad=Math.max(1,(yMax-yMin)*.13);yMin-=pad;yMax+=pad
  const xFor=ms=>plot.x+(ms-data.startMs)/(data.endMs-data.startMs)*plot.w;const yFor=value=>plot.y+plot.h-(value-yMin)/(yMax-yMin)*plot.h;const grid=q('#grid-layer')
  for(let i=0;i<=4;i++){const value=yMin+(yMax-yMin)*i/4,y=yFor(value);grid.appendChild(svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:y,y2:y,class:'grid-line'}));const label=svg('text',{x:plot.x-8,y:y+3,'text-anchor':'end',class:'axis-label'});label.textContent=`${value.toFixed(1)}°`;grid.appendChild(label)}for(let i=0;i<=6;i++){const ms=data.startMs+(data.endMs-data.startMs)*i/6,x=xFor(ms);grid.appendChild(svg('line',{x1:x,x2:x,y1:plot.y,y2:plot.y+plot.h,class:'grid-line'}));const label=svg('text',{x,y:183,'text-anchor':'middle',class:'axis-label'});label.textContent=shortUtc(ms);grid.appendChild(label)}grid.appendChild(svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:yFor(0),y2:yFor(0),class:'horizon'}))
  data.states.forEach((state,index)=>{if(state.earth_el<=0)return;const next=data.states[Math.min(index+1,data.states.length-1)];q('#earth-bands').appendChild(svg('rect',{x:xFor(state.ms),y:plot.y,width:Math.max(1,xFor(next.ms)-xFor(state.ms)+.5),height:plot.h,class:'earth-band'}))});data.series.filter(item=>data.route.station_ids.includes(item.id)).forEach(item=>{const d=item.points.map((point,index)=>`${index?'L':'M'} ${xFor(point.ms).toFixed(2)} ${yFor(point.sun_el).toFixed(2)}`).join(' ');q('#alternate-series').appendChild(svg('path',{d,class:'alternate-path',stroke:item.color}))});const mainD=data.states.map((state,index)=>`${index?'L':'M'} ${xFor(state.ms).toFixed(2)} ${yFor(state.sun_el).toFixed(2)}`).join(' ');q('#main-series').setAttribute('d',mainD);q('#main-series').setAttribute('class','main-path')
  let missionMs=data.startMs,previewMs=null,previewEvent=null,playing=!window.matchMedia('(prefers-reduced-motion: reduce)').matches,speed=1,lastFrame=performance.now(),dragging=false,raf=0,visualPose=null,wheelAngle=0
  const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches,rover=q('#rover'),roverHeading=q('#rover-heading'),spotlight=q('#candidate-spotlight'),cursor=q('#time-cursor'),dot=q('#cursor-dot'),range=q('#mission-range'),tooltip=q('#chart-tooltip'),wheels=[...root.querySelectorAll('.wheel')],wheelCenters=[[-25,-21],[0,-23],[25,-21],[-25,21],[0,23],[25,21]]
  function routeProgress(state){if(!activeProgress)return;if(state.moving&&routeIds.has(state.from_id)&&routeIds.has(state.to_id)){const direction=state.from_id===data.route.station_ids[0]?state.progress:1-state.progress;activeProgress.setAttribute('stroke-dasharray',`${clamp(direction,0,1)} 1`)}else{const complete=state.current_waypoint===data.route.station_ids[1]?1:0;activeProgress.setAttribute('stroke-dasharray',`${complete} 1`)}}
  function syncData(ms,showTip=false,event=null){const state=interpolated(data.states,ms),cx=xFor(ms),active=state.moving?(state.progress<.5?state.from_id:state.to_id):state.current_waypoint,activeSeries=data.series.find(item=>item.id===active),activePoint=activeSeries?interpolated(activeSeries.points,ms):state,candidate=activePoint.sun_el>0&&activePoint.earth_el>0,focusId=byId[state.recommended_waypoint]?state.recommended_waypoint:active,focus=byId[focusId]||byId[active];root.querySelectorAll('.waypoint').forEach(node=>node.classList.toggle('active',node.dataset.id===active));spotlight.style.transform=`translate(${focus.map_x*1000}px,${focus.map_y*435}px)`;spotlight.style.opacity=candidate?'.98':'.54';routeProgress(state);cursor.setAttribute('x1',cx);cursor.setAttribute('x2',cx);dot.setAttribute('cx',cx);dot.setAttribute('cy',yFor(state.sun_el));const utc=formatUtc(ms);q('#header-time').textContent=`UTC ${utc.replace(' UTC','')}`;q('#status-time').textContent=utc;q('#playback-time').textContent=utc;q('#current-waypoint').textContent=active;q('#next-waypoint').textContent=state.moving?state.to_id:'—';q('#sun-elevation').textContent=`${state.sun_el>=0?'+':''}${state.sun_el.toFixed(2)}°`;q('#earth-elevation').textContent=`${state.earth_el>=0?'+':''}${state.earth_el.toFixed(2)}°`;q('#sun-azimuth').textContent=`${state.sun_az.toFixed(2)}°`;q('#earth-azimuth').textContent=`${state.earth_az.toFixed(2)}°`;q('#sun-elevation').className=state.sun_el>0?'positive':'negative';q('#earth-elevation').className=state.earth_el>0?'positive':'negative';const dual=state.sun_el>0&&state.earth_el>0;q('#dual-status').textContent=dual?'Yes · geometric':'No';q('#dual-status').className=dual?'positive':'negative';q('#motion-badge').textContent=state.moving?'MOVING':'STATIONARY';q('#travel-time').textContent=state.moving?`${state.travel_hours.toFixed(1)} h · ${state.distance_km.toFixed(2)} km`:'—';q('#decision-reason').textContent=state.reason;range.value=String(Math.round((ms-data.startMs)/(data.endMs-data.startMs)*1000));q('#play').classList.toggle('active',playing);q('#pause').classList.toggle('active',!playing);if(showTip&&event){tooltip.innerHTML=`<span class="tooltip-time">${utc}</span><div>Sun: ${state.sun_el>=0?'+':''}${state.sun_el.toFixed(2)}° · az ${state.sun_az.toFixed(2)}°</div><div>Earth: ${state.earth_el>=0?'+':''}${state.earth_el.toFixed(2)}° · az ${state.earth_az.toFixed(2)}°</div><div>Station: ${active} · ${dual?'dual geometric visibility':'no dual visibility'}</div>`;tooltip.hidden=false;const box=q('.chart-wrap').getBoundingClientRect();tooltip.style.left=`${clamp(event.clientX-box.left+10,4,box.width-230)}px`;tooltip.style.top=`${clamp(event.clientY-box.top-55,3,box.height-80)}px`}else tooltip.hidden=true;return{state,x:state.x*1000,y:state.y*435,heading:Number.isFinite(state.heading_deg)?state.heading_deg:0}}
  function paintPose(target,delta){if(!visualPose)visualPose={x:target.x,y:target.y,heading:target.heading};const gap=Math.hypot(target.x-visualPose.x,target.y-visualPose.y),ease=reducedMotion||gap>300?1:1-Math.exp(-delta/78),beforeX=visualPose.x,beforeY=visualPose.y;visualPose.x=lerp(visualPose.x,target.x,ease);visualPose.y=lerp(visualPose.y,target.y,ease);visualPose.heading=lerpAngle(visualPose.heading,target.heading,ease);const travelled=Math.hypot(visualPose.x-beforeX,visualPose.y-beforeY),rolling=Boolean(target.state.moving)&&travelled>.001;rover.setAttribute('transform',`translate(${visualPose.x.toFixed(2)} ${visualPose.y.toFixed(2)})`);roverHeading.setAttribute('transform',`rotate(${visualPose.heading.toFixed(2)})`);rover.classList.toggle('rover-moving',rolling);if(rolling){wheelAngle=(wheelAngle+travelled*22)%360;wheels.forEach((wheel,index)=>{const[x,y]=wheelCenters[index],direction=index<3?1:-1;wheel.setAttribute('transform',`translate(${x} ${y}) rotate(${(wheelAngle*direction).toFixed(2)})`)})}}
  // The rover gets one clock; Streamlit does not need sixty reruns per second.
  function frame(now){const delta=Math.min(80,Math.max(0,now-lastFrame));lastFrame=now;if(playing&&!dragging&&previewMs===null){missionMs+=delta*3600*speed;if(missionMs>=data.endMs){missionMs=data.endMs;playing=false}}const displayMs=previewMs??missionMs,target=syncData(displayMs,previewMs!==null,previewEvent);paintPose(target,delta);raf=requestAnimationFrame(frame)}
  const surface=q('#interaction-surface'),pointerTime=event=>{const rect=surface.getBoundingClientRect();return data.startMs+clamp((event.clientX-rect.left)/rect.width,0,1)*(data.endMs-data.startMs)}
  surface.onpointermove=event=>{previewEvent=event;const ms=pointerTime(event);if(dragging)missionMs=ms;previewMs=ms}
  surface.onpointerdown=event=>{dragging=true;surface.setPointerCapture(event.pointerId);missionMs=pointerTime(event);previewMs=missionMs;previewEvent=event}
  surface.onpointerup=event=>{dragging=false;missionMs=pointerTime(event);previewMs=null;previewEvent=null}
  surface.onpointerleave=()=>{if(!dragging){previewMs=null;previewEvent=null;tooltip.hidden=true}}
  q('#play').onclick=()=>{playing=true;lastFrame=performance.now()};q('#pause').onclick=()=>{playing=false};q('#restart').onclick=()=>{playing=false;missionMs=data.startMs;previewMs=null;previewEvent=null}
  root.querySelectorAll('[data-speed]').forEach(button=>button.onclick=()=>{speed=Number(button.dataset.speed);root.querySelectorAll('[data-speed]').forEach(item=>item.classList.toggle('active',item===button))});root.querySelector('[data-speed="1"]').classList.add('active')
  range.oninput=event=>{missionMs=data.startMs+Number(event.target.value)/1000*(data.endMs-data.startMs);previewMs=null;previewEvent=null}
  const initial=syncData(missionMs);paintPose(initial,1000);raf=requestAnimationFrame(frame);return{destroy(){cancelAnimationFrame(raf)}}}
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
