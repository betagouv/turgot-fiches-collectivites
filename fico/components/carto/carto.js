import { escape, panel } from "/assets/common.js"

// Projected coordinates are already in map units: x is the projected longitude,
// y the latitude, negated because SVG's y axis points down.
function ring(points) {
  return "M" + points.map(([x, y]) => `${x},${-y}`).join("L") + "Z"
}

function pathData(geometry) {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates
  return polygons.flatMap((polygon) => polygon.map(ring)).join("")
}

function svg(carte) {
  // The commune goes last, so its neighbours do not paint over its outline.
  const isFocus = (feature) => feature.properties.code === carte.focus
  const features = [...carte.projected.features].sort((a, b) => isFocus(a) - isFocus(b))
  const paths = features
    .map((feature) => {
      const p = feature.properties
      const focused = isFocus(feature)
      const stroke = focused ? carte.legend.focus.color : "#ffffff"
      return `<path d="${pathData(feature.geometry)}" fill="${p.couleur}" stroke="${stroke}" fill-rule="evenodd"${focused ? ' class="focus"' : ""}><title>${escape(p.nom)} — ${escape(p.valeur.label)}</title></path>`
    })
    .join("")
  return `<svg class="map" viewBox="${carte.viewbox.join(" ")}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${escape(carte.titre)}">${paths}</svg>`
}

function legend(data) {
  const swatch = (step, outlined = false) =>
    outlined
      ? `<span class="swatch" data-outline="${escape(step.color)}"></span>`
      : `<span class="swatch" data-fill="${escape(step.color)}"></span>`
  const steps = data.steps.map((step) => swatch(step)).join("")
  return `<div class="legend fr-text--xs">
    ${escape(data.title)}
    <div class="legend-row">
      <span>${escape(data.steps[0].label)}</span><span>${steps}</span><span>${escape(data.steps.at(-1).label)}</span>
      ${swatch(data.no_data)} ${escape(data.no_data.label)}
      ${swatch(data.focus, true)} ${escape(data.focus.label)}
    </div>
  </div>`
}

export function map(carte) {
  return panel(`${carte.titre} — ${carte.communes} communes`, `${svg(carte)}${legend(carte.legend)}`)
}
