// A choropleth of a table whose columns are code, name, value, geometry: each
// feature takes the shade of its value's band, the focused row is outlined.

import { escape, panel } from "/assets/common.js"

const SEUILS = [0.15, 0.25, 0.35, 0.5]
const COULEURS = ["#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091"]
const SANS_DONNEE = "#e5e5e5"
const FOCUS = "#000000"
const MARGIN = 0.01
const NOM = 1
const VALEUR = 2
const CONTOUR = 3

function couleur(valeur) {
  if (valeur === null) {
    return SANS_DONNEE
  }
  const rang = SEUILS.findIndex((seuil) => valeur < seuil)
  return rang === -1 ? COULEURS.at(-1) : COULEURS[rang]
}

function pourcent(valeur) {
  return `${Math.round(valeur * 100)} %`
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
  const all = rows.flatMap((row) => [...points(row[CONTOUR].value.coordinates)])
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
      return `<path d="${pathData(row[CONTOUR].value, scale)}" fill="${couleur(row[VALEUR].value)}" stroke="${stroke}" fill-rule="evenodd"${focused ? ' class="focus"' : ""}><title>${escape(row[NOM].label)} — ${escape(row[VALEUR].label)}</title></path>`
    })
    .join("")
  return `<svg class="map" viewBox="${viewbox.join(" ")}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${escape(data.titre)}">${paths}</svg>`
}

function legend(data) {
  const swatch = (color) => `<span class="swatch" data-fill="${color}"></span>`
  const focused = data.focus === null ? "" : `<span class="swatch" data-outline="${FOCUS}"></span> ${escape(data.rows[data.focus][NOM].label)}`
  return `<div class="legend fr-text--xs">
    ${escape(data.columns[VALEUR])}
    <div class="legend-row">
      <span>&lt; ${pourcent(SEUILS[0])}</span><span>${COULEURS.map(swatch).join("")}</span><span>≥ ${pourcent(SEUILS.at(-1))}</span>
      ${swatch(SANS_DONNEE)} n.c.
      ${focused}
    </div>
  </div>`
}

export function map(data) {
  return panel(data.titre, `${svg(data)}${legend(data)}`, data.header)
}
