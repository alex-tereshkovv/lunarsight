
# LunarSight QA Checklist

## 1. Site data and coordinates

- [ ] Load Haworth HW10 at latitude −86.5270°, longitude −14.8760°.
- [ ] Load Mons Malapert MMA04 at latitude −86.3100°, longitude −0.4590°.
- [ ] Load Nobile Rim 1 NR101 at latitude −85.2950°, longitude +36.9170°.
- [ ] Preserve the published point IDs.
- [ ] Display the source for every coordinate.
- [ ] Identify each point as a published representative candidate, not an approved final landing site.
- [ ] Validate the latitude and longitude ranges.
- [ ] Make the longitude convention explicit.

## 2. Lunar visualization

- [ ] Render the Moon using a documented surface texture.
- [ ] Display a coordinate grid.
- [ ] Identify the lunar South Pole.
- [ ] Place all three candidate markers at their correct geographic positions.
- [ ] Verify the markers against an independent lunar map.
- [ ] Implement camera rotation and zoom.
- [ ] Add a camera reset function.

## 3. Site information panel

- [ ] Show the selected point's name and ID.
- [ ] Show latitude and longitude.
- [ ] Show the coordinate source.
- [ ] Show the point's status and research caveats.
- [ ] Distinguish candidate points from NASA notional planning points.

## 4. Solar geometry

- [ ] Define the time system and date convention.
- [ ] Record the coordinate frame and ephemeris used.
- [ ] Calculate the Sun direction consistently in the selected frame.
- [ ] Calculate ideal-horizon solar elevation.
- [ ] Label ideal-horizon output as a simplified geometric result.
- [ ] Do not claim verified sunlight duration before validation.
- [ ] Compare at least one test case with an independent source.

## 5. Earth visibility

- [ ] Calculate the Earth direction in the same coordinate frame.
- [ ] Calculate ideal-horizon Earth elevation.
- [ ] Distinguish ideal geometric visibility from terrain-obstructed visibility.
- [ ] Display when terrain blocks the Earth direction.
- [ ] Do not treat geometric visibility as a complete radio-link analysis.

## 6. Terrain analysis

- [ ] Record the DEM source and product version.
- [ ] Record DEM spatial resolution.
- [ ] Record map projection and coordinate frame.
- [ ] Record vertical reference and units.
- [ ] Detect missing or interpolated DEM cells.
- [ ] Calculate local horizon profiles by azimuth.
- [ ] Test Sun and Earth visibility against the terrain profile.
- [ ] Warn that coarse terrain data can miss small hazards.
- [ ] Compare terrain-derived results with an independent reference.

## 7. Scientific integrity

- [ ] Do not invent illumination or communications values.
- [ ] Do not describe candidate points as confirmed landing locations.
- [ ] Keep source links available in the interface.
- [ ] Record all model assumptions.
- [ ] Label idealized outputs clearly.
- [ ] Separate model results from observed data.
- [ ] Display data-quality warnings where appropriate.

