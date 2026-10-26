// A choropleth of a table whose columns are code, name, value, geometry: each
// feature takes the shade of its value's band, the focused row is outlined.

#import "@preview/mercator:0.1.2": render-map
#import "common.typ": muted, panel

#let thresholds = (0.15, 0.25, 0.35, 0.5)
#let colors = ("#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091")
#let no-data = "#e5e5e5"
#let focus-color = "#000000"
#let margin = 0.01
#let stroke-ratio = 0.0015
#let name = 1
#let value = 2
#let geometry = 3

#let shade(v) = if v == none {
  no-data
} else {
  let band = thresholds.position(threshold => v < threshold)
  if band == none { colors.last() } else { colors.at(band) }
}

#let percent(v) = str(calc.round(v * 100)) + "\u{202f}%"

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
  let box = bounds(rows.map(row => row.at(geometry).value.coordinates))
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

// Rounded to the contours' own precision, which keeps the rendered map light.
#let project(coordinates, scale) = if type(coordinates.first()) in (int, float) {
  (calc.round(coordinates.first() * scale, digits: 4), ..coordinates.slice(1))
} else {
  coordinates.map(part => project(part, scale))
}

#let feature(row, scale) = (
  type: "Feature",
  properties: (shade: shade(row.at(value).value)),
  geometry: (
    ..row.at(geometry).value,
    coordinates: project(row.at(geometry).value.coordinates, scale),
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
  data.columns.at(value)
  v(0.2em)
  stack(
    dir: ltr,
    ..colors.map(swatch),
    h(5pt),
    swatch(no-data),
    ..if data.focus != none { (h(5pt), swatch(focus-color, outlined: true)) } else { () },
  )
  v(0.15em)
  box(width: 12pt * colors.len())[< #percent(thresholds.first()) #h(1fr) ≥ #percent(thresholds.last())]
  h(5pt)
  [n.c.]
  if data.focus != none {
    h(10pt)
    data.rows.at(data.focus).at(name).label
  }
}

#let map(data) = panel(
  data.title,
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
      draw(features, (fill: "{shade}", stroke: "#ffffff"))
      if data.focus != none {
        place(top + left, draw((features.at(data.focus),), (fill: "none", stroke: focus-color)))
      }
    })
    v(0.3em)
    legend(data)
  },
)
