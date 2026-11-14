"""Streamlit Components v2 renderer for the synchronized rover simulation."""

from __future__ import annotations

from collections.abc import Mapping

import streamlit as st


_HTML = """
<section class="rover-shell" aria-label="Interactive solar rover mission simulation">
  <header class="sim-header">
    <div>
      <span class="eyebrow">SHACKLETON LOCAL SCENARIO</span>
      <strong>Conceptual mobility simulation</strong>
    </div>
    <div class="header-badges">
      <span id="source-badge" class="badge"></span>
      <time id="header-time" class="utc-badge"></time>
    </div>
  </header>

  <div class="workspace">
    <div class="map-card">
      <svg id="terrain-map" viewBox="0 0 1000 540" role="img"
           aria-label="Conceptual rover route over a NASA LROC south-pole image">
        <defs>
          <radialGradient id="zone-glow">
            <stop offset="0" stop-color="#ffd43b" stop-opacity=".62"></stop>
            <stop offset=".38" stop-color="#ffd43b" stop-opacity=".24"></stop>
            <stop offset="1" stop-color="#ffd43b" stop-opacity="0"></stop>
          </radialGradient>
          <filter id="rover-shadow" x="-60%" y="-60%" width="220%" height="220%">
            <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity=".8"></feDropShadow>
          </filter>
          <filter id="node-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="5" result="blur"></feGaussianBlur>
            <feMerge><feMergeNode in="blur"></feMergeNode><feMergeNode in="SourceGraphic"></feMergeNode></feMerge>
          </filter>
        </defs>
        <image id="terrain-image" x="0" y="0" width="1000" height="540"
               preserveAspectRatio="xMidYMid slice"></image>
        <rect x="0" y="0" width="1000" height="540" fill="#030611" opacity=".47"></rect>
        <g id="route-layer"></g>
        <circle id="spotlight" r="118" fill="url(#zone-glow)" opacity="0"></circle>
        <g id="waypoint-layer"></g>
        <g id="rover" filter="url(#rover-shadow)">
          <g class="wheel-set" fill="#10131d" stroke="#bbc5d8" stroke-width="2">
            <rect class="wheel" x="-39" y="-31" width="13" height="21" rx="4"></rect>
            <rect class="wheel" x="-7" y="-34" width="14" height="21" rx="4"></rect>
            <rect class="wheel" x="26" y="-31" width="13" height="21" rx="4"></rect>
            <rect class="wheel" x="-39" y="10" width="13" height="21" rx="4"></rect>
            <rect class="wheel" x="-7" y="13" width="14" height="21" rx="4"></rect>
            <rect class="wheel" x="26" y="10" width="13" height="21" rx="4"></rect>
          </g>
          <rect x="-29" y="-21" width="58" height="42" rx="7" fill="#d6c587" stroke="#fff1b7" stroke-width="2"></rect>
          <rect x="-24" y="-17" width="20" height="34" rx="2" fill="#123979" stroke="#4d83df"></rect>
          <rect x="4" y="-17" width="20" height="34" rx="2" fill="#123979" stroke="#4d83df"></rect>
          <path d="M-22 -11h16M-22 -3h16M-22 5h16M-22 13h16M6 -11h16M6 -3h16M6 5h16M6 13h16"
                stroke="#75a8ff" stroke-width="1"></path>
          <circle cx="0" cy="0" r="8" fill="#b4bdc9" stroke="#f2f5f8" stroke-width="2"></circle>
          <path d="M0 -8V-31M-8 -31h16L0 -40Z" fill="#dbe5ef" stroke="#fff"></path>
          <path d="M0 -24L-9 -17M0 -24l9 7" stroke="#dbe5ef" stroke-width="2"></path>
          <path d="M0 -46l-7 11h14Z" fill="#ffcf36" stroke="#fff0a5" stroke-width="1.5"></path>
        </g>
        <g class="map-label" transform="translate(22 24)">
          <rect width="300" height="57" rx="9"></rect>
          <text x="18" y="24">Shackleton south-pole region</text>
          <text class="sub" x="18" y="45">Conceptual waypoint overlay · not terrain-validated</text>
        </g>
        <g class="map-legend" transform="translate(728 430)">
          <rect width="250" height="91" rx="9"></rect>
          <circle cx="18" cy="22" r="7" fill="none" stroke="#ffd43b" stroke-width="3"></circle>
          <text x="35" y="27">Recommended Candidate Zone</text>
          <circle cx="18" cy="49" r="6" fill="#8a69ff" stroke="#d4c8ff" stroke-width="2"></circle>
          <text x="35" y="54">Conceptual waypoint</text>
          <path d="M10 75h20" stroke="#e6e9ee" stroke-width="2" stroke-dasharray="7 6"></path>
          <text x="35" y="80">Non-validated connection</text>
        </g>
        <g class="north" transform="translate(951 30)">
          <path d="M0 28l12-28 12 28-12-7Z" fill="#fff"></path>
          <text x="12" y="-7" text-anchor="middle">N</text>
        </g>
      </svg>
      <div class="map-footer">
        <span id="spatial-note"></span>
        <a id="map-credit" target="_blank" rel="noopener noreferrer"></a>
      </div>
    </div>

    <aside class="status-stack">
      <section class="status-card">
        <div class="card-title"><span>ROVER STATUS</span><b id="motion-badge"></b></div>
        <dl>
          <div><dt>Current UTC</dt><dd id="status-time"></dd></div>
          <div><dt>Current waypoint</dt><dd id="current-waypoint"></dd></div>
          <div><dt>Sun elevation</dt><dd id="sun-elevation"></dd></div>
          <div><dt>Earth elevation</dt><dd id="earth-elevation"></dd></div>
          <div><dt>Dual visibility</dt><dd id="dual-status"></dd></div>
          <div><dt>Next waypoint</dt><dd id="next-waypoint"></dd></div>
          <div><dt>Travel estimate</dt><dd id="travel-time"></dd></div>
        </dl>
        <div id="decision-reason" class="reason"></div>
        <div id="no-candidate" class="no-candidate" hidden>No waypoint is geometrically favorable at this time.</div>
      </section>
      <section class="status-card compact">
        <div class="card-title"><span>MISSION CONFIGURATION</span></div>
        <dl>
          <div><dt>Period</dt><dd id="mission-period"></dd></div>
          <div><dt>Sampling</dt><dd id="sampling"></dd></div>
          <div><dt>Maximum speed</dt><dd id="max-speed"></dd></div>
          <div><dt>Map</dt><dd>NASA LROC illumination composite</dd></div>
        </dl>
      </section>
      <section class="limitation-card">
        <strong>Conceptual visualization</strong>
        <p>This is a conceptual rover mobility visualization based on geometric Sun and Earth visibility. It does not model local terrain shadows, energy storage, surface hazards, or verified traversable paths.</p>
      </section>
    </aside>
  </div>

  <section class="timeline-card">
    <div class="timeline-title">
      <div><strong>Sun elevation at waypoints</strong><span>Earth-above-horizon track follows the planned rover position</span></div>
      <div id="timeline-legend" class="timeline-legend"></div>
    </div>
    <div class="chart-wrap">
      <svg id="timeline" viewBox="0 0 1000 320" role="img"
           aria-label="Interactive UTC timeline of Sun elevation and Earth visibility">
        <g id="grid-layer"></g>
        <g id="earth-track"></g>
        <g id="series-layer"></g>
        <g id="transition-layer"></g>
        <line id="time-cursor" y1="22" y2="284"></line>
        <circle id="cursor-dot" r="6"></circle>
        <rect id="interaction-surface" x="65" y="18" width="895" height="270" fill="transparent"></rect>
      </svg>
      <div id="chart-tooltip" class="chart-tooltip" hidden></div>
    </div>
    <div class="track-caption"><span class="earth-swatch"></span> Earth center above ideal horizon along planned route</div>
  </section>

  <div class="playback-bar">
    <div class="playback-buttons">
      <button id="play" type="button" aria-label="Play">▶</button>
      <button id="pause" type="button" aria-label="Pause">Ⅱ</button>
      <button id="restart" type="button" aria-label="Restart">↻</button>
    </div>
    <div class="speed-control" role="group" aria-label="Playback speed">
      <span>Playback</span>
      <button type="button" data-speed="1">1×</button>
      <button type="button" data-speed="5">5×</button>
      <button type="button" data-speed="20">20×</button>
      <button type="button" data-speed="100">100×</button>
    </div>
    <input id="mission-range" type="range" aria-label="Mission time" min="0" max="1000" value="0">
    <time id="playback-time"></time>
  </div>
</section>
"""


_CSS = """
:host { color: var(--st-text-color, #eef4ff); font-family: var(--st-font, system-ui, sans-serif); }
* { box-sizing: border-box; }
button, input { font: inherit; }
.rover-shell { --panel:#0c1728; --panel2:#111f34; --edge:#294661; --muted:#9fb0c7; --purple:#8f69ff; --green:#46dc91; --red:#ff6377; display:grid; gap:12px; width:100%; }
.sim-header,.map-card,.status-card,.limitation-card,.timeline-card,.playback-bar { border:1px solid var(--edge); border-radius:12px; background:linear-gradient(145deg,rgba(13,26,44,.97),rgba(6,14,27,.97)); box-shadow:0 12px 34px rgba(0,0,0,.24); }
.sim-header { display:flex; align-items:center; justify-content:space-between; padding:12px 16px; min-height:68px; }
.sim-header strong { display:block; font-size:18px; margin-top:3px; }
.eyebrow { color:#9fb5d1; font-size:10px; font-weight:800; letter-spacing:.2em; }
.header-badges { display:flex; align-items:center; gap:9px; }
.badge,.utc-badge { border:1px solid #345573; border-radius:8px; padding:8px 11px; font-size:12px; white-space:nowrap; }
.badge.nasa { color:#5ff2ae; border-color:#25724f; background:#0a281f; }
.badge.synthetic { color:#ffd75c; border-color:#77652a; background:#2a2410; }
.utc-badge { color:#d9e4f2; background:#101827; font-variant-numeric:tabular-nums; }
.workspace { display:grid; grid-template-columns:minmax(0, 2.35fr) minmax(275px, .82fr); gap:12px; }
.map-card { overflow:hidden; min-width:0; }
#terrain-map { display:block; width:100%; height:auto; min-height:430px; background:#030711; touch-action:none; }
.map-label rect,.map-legend rect { fill:rgba(5,10,19,.85); stroke:#72839b; stroke-width:1; }
.map-label text { fill:#f7f9fc; font-size:16px; font-weight:800; }
.map-label text.sub { fill:#bdc9d8; font-size:11px; font-weight:500; }
.map-legend text { fill:#e5eaf1; font-size:11px; }
.north text { fill:#fff; font-size:12px; }
.route-link { fill:none; stroke:#dfe8f6; stroke-width:2.2; stroke-dasharray:8 7; opacity:.78; }
.route-link.planned { stroke:#b69aff; stroke-width:3.2; opacity:.95; }
.waypoint .halo { fill:rgba(115,78,255,.23); stroke:#b095ff; stroke-width:2; }
.waypoint .core { fill:#6f4fe3; stroke:#dfd5ff; stroke-width:2; }
.waypoint text { fill:#f1ecff; font-size:13px; font-weight:800; paint-order:stroke; stroke:#09101c; stroke-width:4px; }
.waypoint.recommended .halo { fill:rgba(255,210,63,.3); stroke:#ffd23f; filter:url(#node-glow); }
#spotlight { transition:cx .45s ease,cy .45s ease,opacity .25s ease; }
#rover { transition:filter .2s ease; }
#rover.moving .wheel { animation:wheel-pulse .55s linear infinite alternate; transform-box:fill-box; transform-origin:center; }
@keyframes wheel-pulse { from{transform:scaleY(.82)} to{transform:scaleY(1.08)} }
.map-footer { display:flex; justify-content:space-between; gap:12px; padding:8px 12px; color:var(--muted); font-size:10px; background:#07111e; }
.map-footer a { color:#66c8ff; text-align:right; }
.status-stack { display:grid; align-content:start; gap:12px; }
.status-card,.limitation-card { padding:13px 15px; }
.card-title { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid rgba(86,119,151,.38); padding-bottom:9px; margin-bottom:4px; font-size:12px; letter-spacing:.08em; }
#motion-badge { color:var(--green); border:1px solid #2d7656; border-radius:7px; padding:4px 7px; font-size:10px; letter-spacing:0; }
dl { margin:0; }
dl div { display:flex; justify-content:space-between; gap:12px; padding:7px 0; border-bottom:1px solid rgba(65,90,118,.34); }
dt { color:#aebdd0; font-size:11px; }
dd { margin:0; color:#f3f7fc; text-align:right; font-size:11px; font-weight:700; font-variant-numeric:tabular-nums; }
.positive { color:var(--green)!important; } .negative { color:var(--red)!important; }
.reason { margin-top:10px; color:#d0d9e5; font-size:11px; line-height:1.45; font-style:italic; }
.no-candidate { margin-top:9px; padding:8px; border-radius:7px; color:#ffd7dc; background:#421621; border:1px solid #7e2939; font-size:11px; }
.limitation-card strong { color:#bd9fff; font-size:12px; }
.limitation-card p { color:#c2cede; font-size:11px; line-height:1.55; margin:8px 0 0; }
.timeline-card { overflow:hidden; padding:12px 14px 8px; }
.timeline-title { display:flex; justify-content:space-between; gap:14px; align-items:flex-start; }
.timeline-title strong { display:block; font-size:14px; }
.timeline-title span { color:var(--muted); font-size:10px; }
.timeline-legend { display:flex; flex-wrap:wrap; justify-content:flex-end; gap:9px; }
.legend-item { display:flex; align-items:center; gap:5px; font-size:10px; color:#cbd5e2; }
.legend-line { width:18px; height:3px; border-radius:3px; }
.chart-wrap { position:relative; }
#timeline { display:block; width:100%; min-height:285px; touch-action:none; user-select:none; }
.grid-line { stroke:#29415d; stroke-width:1; }
.axis-label { fill:#9fb0c7; font-size:10px; }
.axis-title { fill:#c9d3e1; font-size:11px; font-weight:700; }
.horizon { stroke:#eef2f6; stroke-width:1.5; stroke-dasharray:6 6; }
.sun-path { fill:none; stroke-width:2.2; vector-effect:non-scaling-stroke; }
.earth-visible { fill:rgba(102,109,203,.34); }
.transition-marker { stroke:#bf9dff; stroke-width:1; stroke-dasharray:4 5; opacity:.65; }
#time-cursor { stroke:#fff; stroke-width:2; pointer-events:none; }
#cursor-dot { fill:#ffd23f; stroke:#fff4b9; stroke-width:2; pointer-events:none; }
#interaction-surface { cursor:crosshair; }
.chart-tooltip { position:absolute; z-index:3; pointer-events:none; min-width:210px; max-width:280px; padding:9px 11px; border:1px solid #4c6988; border-radius:8px; background:rgba(5,13,25,.95); box-shadow:0 8px 22px rgba(0,0,0,.4); color:#edf3fa; font-size:10px; line-height:1.45; }
.tooltip-time { display:block; color:#fff; font-weight:800; margin-bottom:5px; }
.track-caption { color:#9eacc0; font-size:10px; margin-left:58px; }
.earth-swatch { display:inline-block; width:14px; height:8px; margin-right:5px; background:rgba(102,109,203,.5); }
.playback-bar { display:grid; grid-template-columns:auto auto minmax(140px,1fr) auto; align-items:center; gap:14px; padding:10px 14px; }
.playback-buttons,.speed-control { display:flex; align-items:center; gap:7px; }
.playback-bar button { border:1px solid #465b78; color:#dfe7f1; background:#121b2d; border-radius:8px; min-width:34px; height:32px; cursor:pointer; }
.playback-buttons button:first-child { border-color:#7654da; background:#5630ba; color:white; }
.playback-bar button.active { color:#fff; border-color:#9b79ff; background:#5d38be; }
.speed-control span { color:var(--muted); font-size:10px; margin-right:3px; }
#mission-range { width:100%; accent-color:#8f69ff; cursor:pointer; }
#playback-time { color:#e8eef7; font-size:11px; font-variant-numeric:tabular-nums; white-space:nowrap; }
@media(max-width:900px){
  .workspace{grid-template-columns:1fr}.status-stack{grid-template-columns:repeat(2,minmax(0,1fr))}.limitation-card{grid-column:1/-1}
  .playback-bar{grid-template-columns:1fr}.header-badges{align-items:flex-end;flex-direction:column}.sim-header{align-items:flex-start}
  .map-footer{flex-direction:column}.timeline-title{flex-direction:column}.timeline-legend{justify-content:flex-start}
}
@media(max-width:620px){.status-stack{grid-template-columns:1fr}.limitation-card{grid-column:auto}.speed-control{flex-wrap:wrap}.sim-header{flex-direction:column;gap:10px}.header-badges{align-items:flex-start}.map-label,.map-legend{display:none}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
"""


_JS = r"""
const instances = new WeakMap()

function clamp(value, low, high) { return Math.max(low, Math.min(high, value)) }
function formatUtc(ms) {
  return new Date(ms).toISOString().replace('T', ' ').replace('.000Z', ' UTC')
}
function shortUtc(ms) {
  const value = new Date(ms)
  return value.toLocaleString('en-GB', {timeZone:'UTC', month:'short', day:'2-digit', hour:'2-digit', minute:'2-digit', hour12:false}).replace(',', '')
}
function svg(tag, attrs={}) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', tag)
  for (const [key,value] of Object.entries(attrs)) node.setAttribute(key, String(value))
  return node
}
function pointAt(points, ms) {
  if (ms <= points[0].ms) return {...points[0]}
  if (ms >= points[points.length-1].ms) return {...points[points.length-1]}
  let low=0, high=points.length-1
  while (high-low>1) { const mid=(low+high)>>1; if(points[mid].ms<=ms) low=mid; else high=mid }
  const a=points[low], b=points[high], f=(ms-a.ms)/(b.ms-a.ms)
  const out={}
  for (const key of Object.keys(a)) out[key] = typeof a[key] === 'number' && typeof b[key] === 'number' ? a[key]+(b[key]-a[key])*f : (f<.5?a[key]:b[key])
  out.ms=ms
  return out
}
function createController(root, raw) {
  const data = structuredClone(raw)
  data.startMs=Date.parse(data.start_utc); data.endMs=Date.parse(data.end_utc)
  data.series.forEach(series => { series.points.forEach(point => { point.ms=Date.parse(point.time_utc) }) })
  data.states.forEach(state => { state.ms=Date.parse(state.time_utc) })
  data.segments.forEach(segment => { segment.startMs=Date.parse(segment.start_utc); segment.endMs=Date.parse(segment.end_utc) })
  const byId=Object.fromEntries(data.waypoints.map(item=>[item.id,item]))
  const q=id=>root.querySelector(id)
  const terrain=q('#terrain-image'); terrain.setAttribute('href',data.map_url)
  q('#spatial-note').textContent=data.spatial_note
  q('#map-credit').textContent=data.map_credit; q('#map-credit').href=data.map_source_url
  const source=q('#source-badge'); source.textContent=data.source_label; source.classList.add(data.source_kind==='nasa'?'nasa':'synthetic')
  q('#mission-period').textContent=`${shortUtc(data.startMs)} — ${shortUtc(data.endMs)} UTC`
  q('#sampling').textContent=`${data.sample_hours} h`
  q('#max-speed').textContent=`${data.rover_speed_kmh.toFixed(2)} km/h`

  const routeLayer=q('#route-layer'), waypointLayer=q('#waypoint-layer')
  const planned=new Set(data.segments.filter(s=>s.moving).map(s=>[s.from_id,s.to_id].sort().join('-')))
  data.connections.forEach(([first,second])=>{
    const a=byId[first], b=byId[second]
    routeLayer.appendChild(svg('path',{d:`M ${a.map_x*1000} ${a.map_y*540} L ${b.map_x*1000} ${b.map_y*540}`,class:`route-link ${planned.has([first,second].sort().join('-'))?'planned':''}`}))
  })
  data.waypoints.forEach(item=>{
    const group=svg('g',{class:'waypoint','data-id':item.id,transform:`translate(${item.map_x*1000} ${item.map_y*540})`})
    group.appendChild(svg('circle',{class:'halo',r:15})); group.appendChild(svg('circle',{class:'core',r:7}))
    const label=svg('text',{x:14,y:-14}); label.textContent=item.id; group.appendChild(label); waypointLayer.appendChild(group)
  })

  const timeline=q('#timeline'), grid=q('#grid-layer'), seriesLayer=q('#series-layer'), earthTrack=q('#earth-track'), transitionLayer=q('#transition-layer')
  const plot={x:65,y:22,w:895,h:222,trackY:258,trackH:24}
  const allSun=data.series.flatMap(s=>s.points.map(p=>p.sun_el)); let yMin=Math.min(-5,...allSun), yMax=Math.max(5,...allSun)
  const pad=Math.max(1,(yMax-yMin)*.12); yMin-=pad; yMax+=pad
  const xFor=ms=>plot.x+(ms-data.startMs)/(data.endMs-data.startMs)*plot.w
  const yFor=value=>plot.y+plot.h-(value-yMin)/(yMax-yMin)*plot.h
  for(let i=0;i<=5;i++){
    const value=yMin+(yMax-yMin)*i/5, y=yFor(value)
    grid.appendChild(svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:y,y2:y,class:'grid-line'}))
    const label=svg('text',{x:plot.x-9,y:y+4,'text-anchor':'end',class:'axis-label'}); label.textContent=`${value.toFixed(0)}°`; grid.appendChild(label)
  }
  for(let i=0;i<=6;i++){
    const ms=data.startMs+(data.endMs-data.startMs)*i/6, x=xFor(ms)
    grid.appendChild(svg('line',{x1:x,x2:x,y1:plot.y,y2:plot.y+plot.h,class:'grid-line'}))
    const label=svg('text',{x:x,y:plot.trackY+plot.trackH+21,'text-anchor':'middle',class:'axis-label'}); label.textContent=shortUtc(ms); grid.appendChild(label)
  }
  grid.appendChild(svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:yFor(0),y2:yFor(0),class:'horizon'}))
  const horizonLabel=svg('text',{x:plot.x+plot.w-3,y:yFor(0)-6,'text-anchor':'end',class:'axis-label'}); horizonLabel.textContent='0° ideal horizon'; grid.appendChild(horizonLabel)
  const yTitle=svg('text',{x:14,y:plot.y+plot.h/2,transform:`rotate(-90 14 ${plot.y+plot.h/2})`,'text-anchor':'middle',class:'axis-title'}); yTitle.textContent='Sun elevation (deg)'; grid.appendChild(yTitle)
  const trackLabel=svg('text',{x:plot.x-9,y:plot.trackY+16,'text-anchor':'end',class:'axis-label'}); trackLabel.textContent='Earth'; grid.appendChild(trackLabel)

  data.series.forEach(series=>{
    const d=series.points.map((point,index)=>`${index?'L':'M'} ${xFor(point.ms).toFixed(2)} ${yFor(point.sun_el).toFixed(2)}`).join(' ')
    seriesLayer.appendChild(svg('path',{d,class:'sun-path',stroke:series.color}))
    const legend=document.createElement('span'); legend.className='legend-item'; legend.innerHTML=`<i class="legend-line" style="background:${series.color}"></i>${series.id}`; q('#timeline-legend').appendChild(legend)
  })
  data.states.forEach((state,index)=>{
    if(state.earth_el<=0) return
    const next=data.states[Math.min(index+1,data.states.length-1)]
    earthTrack.appendChild(svg('rect',{x:xFor(state.ms),y:plot.trackY,width:Math.max(1,xFor(next.ms)-xFor(state.ms)+.5),height:plot.trackH,class:'earth-visible'}))
  })
  data.segments.filter(s=>s.moving).forEach(segment=>{
    transitionLayer.appendChild(svg('line',{x1:xFor(segment.startMs),x2:xFor(segment.startMs),y1:plot.y,y2:plot.trackY+plot.trackH,class:'transition-marker'}))
  })

  let missionMs=data.startMs, previewMs=null, playing=!window.matchMedia('(prefers-reduced-motion: reduce)').matches, speed=1, lastFrame=performance.now(), dragging=false, raf=0
  const rover=q('#rover'), spotlight=q('#spotlight'), cursor=q('#time-cursor'), dot=q('#cursor-dot'), range=q('#mission-range'), tooltip=q('#chart-tooltip')
  function scientificAt(ms,state){
    const from=pointAt(data.series.find(s=>s.id===state.from_id).points,ms), to=pointAt(data.series.find(s=>s.id===state.to_id).points,ms), f=state.progress||0
    return {sun_el:from.sun_el+(to.sun_el-from.sun_el)*f,earth_el:from.earth_el+(to.earth_el-from.earth_el)*f,sun_az:from.sun_az+(to.sun_az-from.sun_az)*f,earth_az:from.earth_az+(to.earth_az-from.earth_az)*f}
  }
  function render(ms,showTip=false,event=null){
    const state=pointAt(data.states,ms), science=scientificAt(ms,state), x=state.x*1000, y=state.y*540, cx=xFor(ms)
    rover.setAttribute('transform',`translate(${x} ${y}) rotate(${state.heading_deg})`); rover.classList.toggle('moving',Boolean(state.moving))
    const candidates=data.series.filter(series=>pointAt(series.points,ms).sun_el>0&&pointAt(series.points,ms).earth_el>0)
    const preferred=candidates.find(series=>series.id===state.recommended_waypoint)||candidates[0]
    root.querySelectorAll('.waypoint').forEach(node=>node.classList.toggle('recommended',Boolean(preferred&&node.dataset.id===preferred.id)))
    if(preferred){ spotlight.setAttribute('cx',preferred.map_x*1000); spotlight.setAttribute('cy',preferred.map_y*540); spotlight.setAttribute('opacity','.9') } else spotlight.setAttribute('opacity','0')
    cursor.setAttribute('x1',cx); cursor.setAttribute('x2',cx); dot.setAttribute('cx',cx); dot.setAttribute('cy',yFor(science.sun_el))
    const formatted=formatUtc(ms); q('#header-time').textContent=`UTC ${formatted.replace(' UTC','')}`; q('#status-time').textContent=formatted; q('#playback-time').textContent=formatted
    q('#current-waypoint').textContent=state.current_waypoint; q('#next-waypoint').textContent=state.moving?state.to_id:'—'
    q('#sun-elevation').textContent=`${science.sun_el>=0?'+':''}${science.sun_el.toFixed(2)}°`; q('#sun-elevation').className=science.sun_el>0?'positive':'negative'
    q('#earth-elevation').textContent=`${science.earth_el>=0?'+':''}${science.earth_el.toFixed(2)}°`; q('#earth-elevation').className=science.earth_el>0?'positive':'negative'
    const dual=science.sun_el>0&&science.earth_el>0; q('#dual-status').textContent=dual?'Yes · geometric':'No'; q('#dual-status').className=dual?'positive':'negative'
    q('#motion-badge').textContent=state.moving?'IN TRANSIT':'STATIONARY'; q('#travel-time').textContent=state.moving?`${state.travel_hours.toFixed(1)} h · ${state.distance_km.toFixed(2)} km`:'—'
    q('#decision-reason').textContent=state.reason; q('#no-candidate').hidden=Boolean(preferred)
    range.value=String(Math.round((ms-data.startMs)/(data.endMs-data.startMs)*1000))
    q('#play').classList.toggle('active',playing); q('#pause').classList.toggle('active',!playing)
    if(showTip&&event){
      const lines=data.series.map(series=>{const p=pointAt(series.points,ms);return `<div style="color:${series.color}">${series.id}: Sun ${p.sun_el>=0?'+':''}${p.sun_el.toFixed(2)}° · Earth ${p.earth_el>=0?'+':''}${p.earth_el.toFixed(2)}°</div>`}).join('')
      tooltip.innerHTML=`<span class="tooltip-time">${formatted}</span>${lines}`; tooltip.hidden=false
      const box=q('.chart-wrap').getBoundingClientRect(); tooltip.style.left=`${clamp(event.clientX-box.left+12,4,box.width-286)}px`; tooltip.style.top=`${clamp(event.clientY-box.top-55,4,box.height-120)}px`
    } else tooltip.hidden=true
  }
  function frame(now){
    const delta=now-lastFrame; lastFrame=now
    if(playing&&!dragging&&previewMs===null){ missionMs+=delta*3600*speed; if(missionMs>=data.endMs){missionMs=data.endMs;playing=false} }
    render(previewMs??missionMs); raf=requestAnimationFrame(frame)
  }
  function pointerTime(event){ const rect=q('#interaction-surface').getBoundingClientRect(); return data.startMs+clamp((event.clientX-rect.left)/rect.width,0,1)*(data.endMs-data.startMs) }
  const surface=q('#interaction-surface')
  surface.onpointermove=event=>{ const ms=pointerTime(event); if(dragging) missionMs=ms; else previewMs=ms; render(ms,true,event) }
  surface.onpointerdown=event=>{ dragging=true; surface.setPointerCapture(event.pointerId); missionMs=pointerTime(event); previewMs=missionMs; render(missionMs,true,event) }
  surface.onpointerup=event=>{ dragging=false; missionMs=pointerTime(event); previewMs=null; render(missionMs,false) }
  surface.onpointerleave=()=>{ if(!dragging){previewMs=null;tooltip.hidden=true;render(missionMs)} }
  q('#play').onclick=()=>{playing=true;lastFrame=performance.now()}; q('#pause').onclick=()=>{playing=false}; q('#restart').onclick=()=>{playing=false;missionMs=data.startMs;previewMs=null;render(missionMs)}
  root.querySelectorAll('[data-speed]').forEach(button=>button.onclick=()=>{speed=Number(button.dataset.speed);root.querySelectorAll('[data-speed]').forEach(item=>item.classList.toggle('active',item===button))})
  root.querySelector('[data-speed="1"]').classList.add('active')
  range.oninput=event=>{missionMs=data.startMs+Number(event.target.value)/1000*(data.endMs-data.startMs);previewMs=null;render(missionMs)}
  render(missionMs); raf=requestAnimationFrame(frame)
  return {destroy(){cancelAnimationFrame(raf)}}
}

export default function(component) {
  const {data,parentElement}=component
  const root=parentElement.querySelector('.rover-shell')
  if(!root||!data) return
  const previous=instances.get(parentElement); if(previous) previous.destroy()
  const controller=createController(root,data); instances.set(parentElement,controller)
  return ()=>controller.destroy()
}
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
