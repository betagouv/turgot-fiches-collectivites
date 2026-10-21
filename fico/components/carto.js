// A choropleth of a table whose columns are code, name, value, geometry: each
// feature takes the shade of its value's band, the focused row is outlined.

import { escape, panel } from "/assets/common.js"

const THRESHOLDS = [0.15, 0.25, 0.35, 0.5]
const COLORS = ["#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091"]
const NO_DATA = "#e5e5e5"
const FOCUS = "#000000"
const MARGIN = 0.01
const NAME = 1
const VALUE = 2
const GEOMETRY = 3

function shade(value) {
  if (value === null) {
    return NO_DATA
  }
  const band = THRESHOLDS.findIndex((threshold) => value < threshold)
  return band === -1 ? COLORS.at(-1) : COLORS[band]
}

function percent(value) {
  return `${Math.round(value * 100)} %`
}

function* points(coordinates) {
  if (typeof coordinates[0] === "number") {
    yield coordinates
  } else {
    for (const part of coordinates) {
      yield* points(part)
    }
  }
}

// Longitudes are scaled by the cosine of the central latitude, which keeps
// shapes undistorted at this scale; the latitude is negated because SVG's y
// axis points down.
function frame(rows) {
  const all = rows.flatMap((row) => [...points(row[GEOMETRY].value.coordinates)])
  const latitudes = all.map(([, y]) => y)
  const minLat = Math.min(...latitudes)
  const maxLat = Math.max(...latitudes)
  const scale = Math.cos((((minLat + maxLat) / 2) * Math.PI) / 180)
  const xs = all.map(([x]) => x * scale)
  const width = Math.max(...xs) - Math.min(...xs)
  const height = maxLat - minLat
  const margin = Math.max(width, height) * MARGIN
  const viewbox = [Math.min(...xs) - margin, -maxLat - margin, width + 2 * margin, height + 2 * margin]
  return { scale, viewbox }
}

function ring(ringPoints, scale) {
  return "M" + ringPoints.map(([x, y]) => `${x * scale},${-y}`).join("L") + "Z"
}

function pathData(geometry, scale) {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates
  return polygons.flatMap((polygon) => polygon.map((ringPoints) => ring(ringPoints, scale))).join("")
}

function svg(data) {
  const { scale, viewbox } = frame(data.rows)
  // The focused row goes last, so its neighbours do not paint over its outline.
  const order = data.rows.map((_, index) => index).sort((a, b) => (a === data.focus) - (b === data.focus))
  const paths = order
    .map((index) => {
      const row = data.rows[index]
      const focused = index === data.focus
      const stroke = focused ? FOCUS : "#ffffff"
      return `<path d="${pathData(row[GEOMETRY].value, scale)}" fill="${shade(row[VALUE].value)}" stroke="${stroke}" fill-rule="evenodd"${focused ? ' class="focus"' : ""}><title>${escape(row[NAME].label)} — ${escape(row[VALUE].label)}</title></path>`
    })
    .join("")
  return `<svg class="map" viewBox="${viewbox.join(" ")}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${escape(data.title)}">${paths}</svg>`
}

function legend(data) {
  const swatch = (color) => `<span class="swatch" data-fill="${color}"></span>`
  const focused = data.focus === null ? "" : `<span class="swatch" data-outline="${FOCUS}"></span> ${escape(data.rows[data.focus][NAME].label)}`
  return `<div class="legend fr-text--xs">
    ${escape(data.columns[VALUE])}
    <div class="legend-row">
      <span>&lt; ${percent(THRESHOLDS[0])}</span><span>${COLORS.map(swatch).join("")}</span><span>≥ ${percent(THRESHOLDS.at(-1))}</span>
      ${swatch(NO_DATA)} n.c.
      ${focused}
    </div>
  </div>`
}

export function map(data) {
  return panel(data.title, `${svg(data)}${legend(data)}`, data.header)
}
