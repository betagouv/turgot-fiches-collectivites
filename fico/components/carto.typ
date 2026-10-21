// A choropleth of a table whose columns are code, name, value, geometry: each
// feature takes the shade of its value's band, the focused row is outlined.

#import "@preview/mercator:0.1.2": render-map
#import "common.typ": muted, panel

#let seuils = (0.15, 0.25, 0.35, 0.5)
#let couleurs = ("#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091")
#let sans-donnee = "#e5e5e5"
#let focus-color = "#000000"
#let margin = 0.01
#let stroke-ratio = 0.0015
#let nom = 1
#let valeur = 2
#let contour = 3

#let couleur(v) = if v == none {
  sans-donnee
} else {
  let rang = seuils.position(seuil => v < seuil)
  if rang == none { couleurs.last() } else { couleurs.at(rang) }
}

#let pourcent(v) = str(calc.round(v * 100)) + "\u{202f}%"

// (min longitude, min latitude, max longitude, max latitude) of nested coordinates.
#let bounds(coordinates) = if type(coordinates.first()) in (int, float) {
  (coordinates.at(0), coordinates.at(1), coordinates.at(0), coordinates.at(1))
} else {
  let parts = coordinates.map(bounds)
  (
    calc.min(..parts.map(b => b.at(0))),
    calc.min(..parts.map(b => b.at(1))),
    calc.max(..parts.map(b => b.at(2))),
    calc.max(..parts.map(b => b.at(3))),
  )
}

// Longitudes are scaled by the cosine of the central latitude, which keeps
// shapes undistorted at this scale. mercator frames every map in a square and
// pins it to the top, so the exact extent is handed to it as a viewbox, with
// the latitude negated because SVG's y axis points down.
#let frame(rows) = {
  let box = bounds(rows.map(row => row.at(contour).value.coordinates))
  let scale = calc.cos((box.at(1) + box.at(3)) / 2 * 1deg)
  let (min-x, max-x) = (box.at(0) * scale, box.at(2) * scale)
  let (width, height) = (max-x - min-x, box.at(3) - box.at(1))
  let pad = calc.max(width, height) * margin
  (
    scale: scale,
    viewbox: (min-x - pad, -box.at(3) - pad, width + 2 * pad, height + 2 * pad),
    stroke: calc.max(width, height) * stroke-ratio,
  )
}

#let project(coordinates, scale) = if type(coordinates.first()) in (int, float) {
  (coordinates.first() * scale, ..coordinates.slice(1))
} else {
  coordinates.map(part => project(part, scale))
}

#let feature(row, scale) = (
  type: "Feature",
  properties: (couleur: couleur(row.at(valeur).value)),
  geometry: (
    ..row.at(contour).value,
    coordinates: project(row.at(contour).value.coordinates, scale),
  ),
)

#let swatch(color, outlined: false) = rect(
  width: 12pt,
  height: 5pt,
  fill: if outlined { white } else { rgb(color) },
  stroke: if outlined { 1pt + rgb(color) } else { none },
)

#let legend(data) = {
  set text(size: 6.5pt, fill: muted)
  data.columns.at(valeur)
  v(0.2em)
  stack(
    dir: ltr,
    ..couleurs.map(swatch),
    h(5pt),
    swatch(sans-donnee),
    ..if data.focus != none { (h(5pt), swatch(focus-color, outlined: true)) } else { () },
  )
  v(0.15em)
  box(width: 12pt * couleurs.len())[< #pourcent(seuils.first()) #h(1fr) ≥ #pourcent(seuils.last())]
  h(5pt)
  [n.c.]
  if data.focus != none {
    h(10pt)
    data.rows.at(data.focus).at(nom).label
  }
}

#let map(data) = panel(
  data.titre,
  header: data.header,
  {
    let framed = frame(data.rows)
    // stroke_width rejects a `{property}` template: a string there drops the
    // whole style, fill included.
    let extent = (stroke_width: framed.stroke, viewbox: framed.viewbox)
    let draw(features, style) = render-map(
      bytes(json.encode((type: "FeatureCollection", features: features))),
      json.encode(style + extent),
      width: 100%,
      height: 100%,
      fit: "contain",
    )
    let features = data.rows.map(row => feature(row, framed.scale))
    // The focused row is drawn again on top, alone, with the same frame: its
    // outline is never covered by a neighbour.
    box(width: 100%, height: 5.8cm, {
      draw(features, (fill: "{couleur}", stroke: "#ffffff"))
      if data.focus != none {
        place(top + left, draw((features.at(data.focus),), (fill: "none", stroke: focus-color)))
      }
    })
    v(0.3em)
    legend(data)
  },
)
