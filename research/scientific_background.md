
# Scientific Background: Lunar South Pole Site Selection

## 1. Why is NASA interested in the lunar South Pole?

The lunar South Pole is scientifically important because some permanently shadowed regions (PSRs) are cold enough to preserve water ice and other volatile materials. Studying these deposits can help scientists understand the origin, movement, and long-term stability of water and other substances on the Moon.

These materials may also become useful for future lunar exploration. However, their distribution, concentration, accessibility, and extractability must be established through measurements. Not every permanently shadowed region necessarily contains the same materials or quantities.

The South Pole also contains elevated terrain that can receive extended periods of sunlight, sometimes close to shadowed craters. This combination creates opportunities to study both illuminated highlands and extremely cold environments within the same broad exploration region.

## 2. Why is solar energy especially important?

Solar energy can provide electricity for communications, navigation, scientific instruments, thermal-control systems, and surface mobility. The availability of sunlight therefore affects both the power budget and the operational schedule of a lunar mission.

Near the lunar poles, sunlight arrives at a very shallow angle. A ridge or crater rim can block direct sunlight even when a simplified calculation places the Sun above an idealized horizon. Long periods without direct sunlight can require batteries, energy storage, carefully scheduled operations, or alternative power sources.

Solar illumination also affects thermal conditions. Lunar equipment and crew systems must operate in an environment with large temperature variations between illuminated and shadowed terrain.

## 3. Why can long periods of darkness occur near the poles?

The Moon's rotational axis is tilted by only about 1.5 degrees relative to the relevant orbital plane. Near the poles, the Sun therefore remains very close to the horizon rather than rising high into the sky.

Because sunlight arrives at such a low angle, crater rims and distant mountains cast very long shadows. Some deep crater floors never receive direct sunlight and are known as permanently shadowed regions.

NASA explains that these regions can remain extremely cold. Their temperatures can allow water ice and other volatile substances to remain stable for long periods. The cold conditions make PSRs scientifically valuable, but also difficult environments to explore.

## 4. Why can direct communication with Earth be interrupted?

From many lunar south-polar locations, Earth appears very low above the local horizon. A nearby ridge, crater rim, or mountain can block the direct line of sight between a lander and Earth.

When the direct path is obstructed, a mission may require a relay satellite or another communications architecture. Even when geometric line of sight exists, it does not guarantee a reliable radio connection.

NASA's Lunar Surface Propagation project studies how radio signals can reflect from lunar terrain, potentially causing interference and data loss. Antenna orientation, radio frequency, terrain, and the complete communications link budget are also important.

## 5. Why are ideal-horizon Sun and Earth elevations insufficient?

An ideal-horizon calculation estimates the elevation of the Sun or Earth relative to a simplified local horizontal plane. This is useful for first-order geometric analysis, but it does not account for the real skyline formed by lunar terrain.

At the South Pole, the difference is especially important. Since the Sun and Earth can both appear close to the horizon, a ridge or crater wall can obstruct them even when an idealized model predicts visibility.

A more realistic assessment needs a digital elevation model (DEM) and terrain-horizon analysis in the relevant azimuth direction. The model must test whether the terrain blocks the direction toward the Sun or Earth.

DEM resolution and data quality matter. Wueller et al. used LOLA elevation data at 20 m/pixel for their initial terrain analysis and noted that small craters and boulders may remain unresolved at that scale. They recommend additional 1–2 m image analysis for detailed hazard assessment.

## Implications for LunarSight

LunarSight should distinguish between three different levels of analysis:

1. Ideal geometric visibility: Sun or Earth elevation calculated without local terrain obstruction.
2. Terrain-aware visibility: a horizon-profile or ray test using a lunar DEM.
3. Communications feasibility: a more complete radio analysis that includes terrain, antenna properties, propagation, relays, and link-budget constraints.

A version of LunarSight that does not include terrain must label its outputs as idealized geometry. It must not describe them as verified sunlight duration, guaranteed Earth communications, safe landing conditions, or mission approval.

The three points in the accompanying dataset are published representative candidate locations. They are not final NASA-selected landing coordinates. Their suitability depends on the model assumptions, DEM resolution, illumination period, and additional local hazard assessment.

## References

1. NASA. The Lunar South Pole Region.
   https://www.nasa.gov/reference/moonbase-environment/

2. NASA Scientific Visualization Studio. Shadows near the Moon's South Pole.
   https://science.nasa.gov/resource/shadows-near-the-moons-south-pole/

3. NASA. Shackleton Crater's Illuminated Rim & Shadowed Interior.
   https://science.nasa.gov/resource/shackleton-craters-illuminated-rim-shadowed-interior/

4. NASA Glenn Research Center. Lunar Surface Propagation.
   https://www.nasa.gov/glenn/glenn-expertise-space-exploration/scan/lunar-surface-propagation/

5. Wueller et al. (2026). Assessing Potential Landing Sites With Favorable Illumination and Accessible, Potentially Volatile-Rich Permanently Shadowed Regions Within Artemis Candidate Landing Regions. Journal of Geophysical Research: Planets.
   https://doi.org/10.1029/2025JE009434

6. Kring et al. (2025). Notional Geological Traverses, Station Activities, and Sample Collection on Mons Malapert, Lunar South Polar Region. Journal of Geophysical Research: Planets.
   https://doi.org/10.1029/2024JE008905

