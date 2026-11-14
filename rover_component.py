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
          <radialGradient id="zone-glow">
            <stop offset="0" stop-color="#ffd43b" stop-opacity=".62"></stop>
            <stop offset=".42" stop-color="#ffd43b" stop-opacity=".22"></stop>
            <stop offset="1" stop-color="#ffd43b" stop-opacity="0"></stop>
          </radialGradient>
          <filter id="soft-shadow" x="-80%" y="-80%" width="260%" height="260%">
            <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#000" flood-opacity=".85"></feDropShadow>
          </filter>
        </defs>
        <image id="terrain-image" x="0" y="0" width="1000" height="435" preserveAspectRatio="none"></image>
        <rect x="0" y="0" width="1000" height="435" fill="#020712" opacity=".34"></rect>
        <g id="route-layer"></g>
        <circle id="spotlight" r="62" fill="url(#zone-glow)" opacity="0"></circle>
        <g id="waypoint-layer"></g>
        <g id="rover" filter="url(#soft-shadow)">
          <g fill="#0a0e18" stroke="#d4dfed" stroke-width="1.4">
            <rect x="-27" y="-18" width="9" height="14" rx="3"></rect><rect x="18" y="-18" width="9" height="14" rx="3"></rect>
            <rect x="-27" y="4" width="9" height="14" rx="3"></rect><rect x="18" y="4" width="9" height="14" rx="3"></rect>
          </g>
          <rect x="-20" y="-14" width="40" height="28" rx="5" fill="#d6c27a" stroke="#fff1b0" stroke-width="1.6"></rect>
          <rect x="-16" y="-10" width="13" height="20" fill="#123a78" stroke="#6fa2ff"></rect>
          <rect x="3" y="-10" width="13" height="20" fill="#123a78" stroke="#6fa2ff"></rect>
          <circle r="5" fill="#eef4fa" stroke="#74849a"></circle>
          <path d="M0 -5V-24M-6 -24h12L0 -31Z" fill="#f4f7fa" stroke="#fff"></path>
          <path d="M0 -36l-5 8h10Z" fill="#ffd43b" stroke="#fff1a3"></path>
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
          <text x="34" y="24">Geometric candidate zone</text>
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
.route-link { fill:none; stroke:#f5f6f8; stroke-width:2.2; stroke-dasharray:8 7; opacity:.88; }.waypoint .halo { fill:#8f69ff; opacity:.24; }.waypoint .core { fill:#8f69ff; stroke:#ded5ff; stroke-width:2; }.waypoint text { fill:#fff; paint-order:stroke; stroke:#07101d; stroke-width:4px; font-size:11px; font-weight:800; }.waypoint.active .core { fill:#ffd43b; stroke:#fff3ae; }.waypoint.active .halo { fill:#ffd43b; opacity:.36; }
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
function interpolated(points,ms){const[a,b,f]=bracket(points,ms);const out={...(f<.5?a:b)};['x','y','heading_deg','progress','sun_el','earth_el','sun_az','earth_az','distance_km','travel_hours'].forEach(key=>{if(Number.isFinite(a[key])&&Number.isFinite(b[key]))out[key]=lerp(a[key],b[key],f)});return out}

function createController(root,data){
  data.startMs=Date.parse(data.start_utc);data.endMs=Date.parse(data.end_utc)
  data.states=data.states.map(item=>({...item,ms:Date.parse(item.time_utc)}));data.series=data.series.map(item=>({...item,points:item.points.map(point=>({...point,ms:Date.parse(point.time_utc)}))}))
  const byId=Object.fromEntries(data.waypoints.map(item=>[item.id,item]));const q=id=>root.querySelector(id)
  q('#terrain-image').setAttribute('href',data.map_url);q('#spatial-note').textContent=data.spatial_note;q('#map-credit').textContent=data.map_credit;q('#map-credit').href=data.map_source_url;q('#station-credit').href=data.station_source_url
  const source=q('#source-badge');source.textContent=data.source_label;source.classList.add('nasa')
  q('#mission-period').textContent=`${shortUtc(data.startMs)} — ${shortUtc(data.endMs)}`;q('#sampling').textContent=`${data.sample_hours} h`;q('#max-speed').textContent=`${data.rover_speed_kmh.toFixed(2)} km/h`;q('#route-label').textContent=data.route.label;q('#official-length').textContent=`${data.route.official_traverse_length_km.toFixed(2)} km (published)`;q('#display-length').textContent=`${data.route.display_connector_length_km.toFixed(2)} km (straight)`
  const scaleWidth=data.scale_bar.fraction*1000;q('#scale-line').setAttribute('x2',scaleWidth);q('#scale-end').setAttribute('x1',scaleWidth);q('#scale-end').setAttribute('x2',scaleWidth);q('#scale-label').setAttribute('x',scaleWidth/2);q('#scale-label').textContent=`${data.scale_bar.distance_km} km`
  const routeLayer=q('#route-layer'),waypointLayer=q('#waypoint-layer');data.connections.forEach(([first,second])=>{const a=byId[first],b=byId[second];routeLayer.appendChild(svg('path',{d:`M ${a.map_x*1000} ${a.map_y*435} L ${b.map_x*1000} ${b.map_y*435}`,class:'route-link'}))});data.waypoints.forEach(item=>{const mapY=item.map_y*435;const group=svg('g',{class:'waypoint','data-id':item.id,transform:`translate(${item.map_x*1000} ${mapY})`});group.appendChild(svg('circle',{class:'halo',r:13}));group.appendChild(svg('circle',{class:'core',r:6}));const label=svg('text',{x:10,y:mapY<24?18:-10});label.textContent=item.id;group.appendChild(label);waypointLayer.appendChild(group)})
  const plot={x:58,y:18,w:920,h:140};const allSun=[...data.states.map(item=>item.sun_el),...data.series.filter(item=>data.route.station_ids.includes(item.id)).flatMap(item=>item.points.map(point=>point.sun_el))];let yMin=Math.min(-2,...allSun),yMax=Math.max(2,...allSun);const pad=Math.max(1,(yMax-yMin)*.13);yMin-=pad;yMax+=pad
  const xFor=ms=>plot.x+(ms-data.startMs)/(data.endMs-data.startMs)*plot.w;const yFor=value=>plot.y+plot.h-(value-yMin)/(yMax-yMin)*plot.h;const grid=q('#grid-layer')
  for(let i=0;i<=4;i++){const value=yMin+(yMax-yMin)*i/4,y=yFor(value);grid.appendChild(svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:y,y2:y,class:'grid-line'}));const label=svg('text',{x:plot.x-8,y:y+3,'text-anchor':'end',class:'axis-label'});label.textContent=`${value.toFixed(1)}°`;grid.appendChild(label)}for(let i=0;i<=6;i++){const ms=data.startMs+(data.endMs-data.startMs)*i/6,x=xFor(ms);grid.appendChild(svg('line',{x1:x,x2:x,y1:plot.y,y2:plot.y+plot.h,class:'grid-line'}));const label=svg('text',{x,y:183,'text-anchor':'middle',class:'axis-label'});label.textContent=shortUtc(ms);grid.appendChild(label)}grid.appendChild(svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:yFor(0),y2:yFor(0),class:'horizon'}))
  data.states.forEach((state,index)=>{if(state.earth_el<=0)return;const next=data.states[Math.min(index+1,data.states.length-1)];q('#earth-bands').appendChild(svg('rect',{x:xFor(state.ms),y:plot.y,width:Math.max(1,xFor(next.ms)-xFor(state.ms)+.5),height:plot.h,class:'earth-band'}))});data.series.filter(item=>data.route.station_ids.includes(item.id)).forEach(item=>{const d=item.points.map((point,index)=>`${index?'L':'M'} ${xFor(point.ms).toFixed(2)} ${yFor(point.sun_el).toFixed(2)}`).join(' ');q('#alternate-series').appendChild(svg('path',{d,class:'alternate-path',stroke:item.color}))});const mainD=data.states.map((state,index)=>`${index?'L':'M'} ${xFor(state.ms).toFixed(2)} ${yFor(state.sun_el).toFixed(2)}`).join(' ');q('#main-series').setAttribute('d',mainD);q('#main-series').setAttribute('class','main-path')
  let missionMs=data.startMs,previewMs=null,playing=!window.matchMedia('(prefers-reduced-motion: reduce)').matches,speed=1,lastFrame=performance.now(),dragging=false,raf=0;const rover=q('#rover'),spotlight=q('#spotlight'),cursor=q('#time-cursor'),dot=q('#cursor-dot'),range=q('#mission-range'),tooltip=q('#chart-tooltip')
  function render(ms,showTip=false,event=null){const state=interpolated(data.states,ms),x=state.x*1000,y=state.y*435,cx=xFor(ms);rover.setAttribute('transform',`translate(${x} ${y}) rotate(${state.heading_deg})`);const active=state.moving?(state.progress<.5?state.from_id:state.to_id):state.current_waypoint;root.querySelectorAll('.waypoint').forEach(node=>node.classList.toggle('active',node.dataset.id===active));const activeSeries=data.series.find(item=>item.id===active),activePoint=activeSeries?interpolated(activeSeries.points,ms):state;const candidate=activePoint.sun_el>0&&activePoint.earth_el>0;if(candidate){spotlight.setAttribute('cx',byId[active].map_x*1000);spotlight.setAttribute('cy',byId[active].map_y*435);spotlight.setAttribute('opacity','.92')}else spotlight.setAttribute('opacity','0');cursor.setAttribute('x1',cx);cursor.setAttribute('x2',cx);dot.setAttribute('cx',cx);dot.setAttribute('cy',yFor(state.sun_el));const utc=formatUtc(ms);q('#header-time').textContent=`UTC ${utc.replace(' UTC','')}`;q('#status-time').textContent=utc;q('#playback-time').textContent=utc;q('#current-waypoint').textContent=active;q('#next-waypoint').textContent=state.moving?state.to_id:'—';q('#sun-elevation').textContent=`${state.sun_el>=0?'+':''}${state.sun_el.toFixed(2)}°`;q('#earth-elevation').textContent=`${state.earth_el>=0?'+':''}${state.earth_el.toFixed(2)}°`;q('#sun-azimuth').textContent=`${state.sun_az.toFixed(2)}°`;q('#earth-azimuth').textContent=`${state.earth_az.toFixed(2)}°`;q('#sun-elevation').className=state.sun_el>0?'positive':'negative';q('#earth-elevation').className=state.earth_el>0?'positive':'negative';const dual=state.sun_el>0&&state.earth_el>0;q('#dual-status').textContent=dual?'Yes · geometric':'No';q('#dual-status').className=dual?'positive':'negative';q('#motion-badge').textContent=state.moving?'MOVING':'STATIONARY';q('#travel-time').textContent=state.moving?`${state.travel_hours.toFixed(1)} h · ${state.distance_km.toFixed(2)} km`:'—';q('#decision-reason').textContent=state.reason;range.value=String(Math.round((ms-data.startMs)/(data.endMs-data.startMs)*1000));q('#play').classList.toggle('active',playing);q('#pause').classList.toggle('active',!playing);if(showTip&&event){tooltip.innerHTML=`<span class="tooltip-time">${utc}</span><div>Sun: ${state.sun_el>=0?'+':''}${state.sun_el.toFixed(2)}° · az ${state.sun_az.toFixed(2)}°</div><div>Earth: ${state.earth_el>=0?'+':''}${state.earth_el.toFixed(2)}° · az ${state.earth_az.toFixed(2)}°</div><div>Station: ${active} · ${dual?'dual geometric visibility':'no dual visibility'}</div>`;tooltip.hidden=false;const box=q('.chart-wrap').getBoundingClientRect();tooltip.style.left=`${clamp(event.clientX-box.left+10,4,box.width-230)}px`;tooltip.style.top=`${clamp(event.clientY-box.top-55,3,box.height-80)}px`}else tooltip.hidden=true}
  function frame(now){const delta=now-lastFrame;lastFrame=now;if(playing&&!dragging&&previewMs===null){missionMs+=delta*3600*speed;if(missionMs>=data.endMs){missionMs=data.endMs;playing=false}}render(previewMs??missionMs);raf=requestAnimationFrame(frame)}const surface=q('#interaction-surface');const pointerTime=event=>{const rect=surface.getBoundingClientRect();return data.startMs+clamp((event.clientX-rect.left)/rect.width,0,1)*(data.endMs-data.startMs)};surface.onpointermove=event=>{const ms=pointerTime(event);if(dragging)missionMs=ms;else previewMs=ms;render(ms,true,event)};surface.onpointerdown=event=>{dragging=true;surface.setPointerCapture(event.pointerId);missionMs=pointerTime(event);previewMs=missionMs;render(missionMs,true,event)};surface.onpointerup=event=>{dragging=false;missionMs=pointerTime(event);previewMs=null;render(missionMs)};surface.onpointerleave=()=>{if(!dragging){previewMs=null;tooltip.hidden=true;render(missionMs)}};q('#play').onclick=()=>{playing=true;lastFrame=performance.now()};q('#pause').onclick=()=>{playing=false};q('#restart').onclick=()=>{playing=false;missionMs=data.startMs;previewMs=null;render(missionMs)};root.querySelectorAll('[data-speed]').forEach(button=>button.onclick=()=>{speed=Number(button.dataset.speed);root.querySelectorAll('[data-speed]').forEach(item=>item.classList.toggle('active',item===button))});root.querySelector('[data-speed="1"]').classList.add('active');range.oninput=event=>{missionMs=data.startMs+Number(event.target.value)/1000*(data.endMs-data.startMs);previewMs=null;render(missionMs)};render(missionMs);raf=requestAnimationFrame(frame);return{destroy(){cancelAnimationFrame(raf)}}}
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
