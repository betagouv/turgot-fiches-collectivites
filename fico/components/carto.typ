#import "@preview/mercator:0.1.2": render-map
#import "common.typ": muted, panel

#let swatch(step, outlined: false) = rect(
  width: 12pt,
  height: 5pt,
  fill: if outlined { white } else { rgb(step.color) },
  stroke: if outlined { 1pt + rgb(step.color) } else { none },
)

#let legend(data) = {
  set text(size: 6.5pt, fill: muted)
  data.title
  v(0.2em)
  stack(
    dir: ltr,
    ..data.steps.map(swatch),
    h(5pt),
    swatch(data.no_data),
    h(5pt),
    swatch(data.focus, outlined: true),
  )
  v(0.15em)
  box(width: 12pt * data.steps.len())[#data.steps.first().label #h(1fr) #data.steps.last().label]
  h(5pt)
  data.no_data.label
  h(10pt)
  data.focus.label
}

#let project(coordinates, scale) = if type(coordinates.first()) in (int, float) {
  (coordinates.first() * scale, ..coordinates.slice(1))
} else {
  coordinates.map(part => project(part, scale))
}

#let projected(collection, scale) = (
  type: "FeatureCollection",
  features: collection.features.map(feature => (
    ..feature,
    geometry: (
      ..feature.geometry,
      coordinates: project(feature.geometry.coordinates, scale),
    ),
  )),
)

#let map(carte) = panel(
  [
    #carte.titre
    #h(0.4em)
    #text(size: 7.5pt, fill: luma(45%), weight: "regular")[#carte.effectif]
  ],
  {
    // stroke_width rejects a `{property}` template: a string there drops the
    // whole style, fill included.
    let frame = (stroke_width: carte.stroke, viewbox: carte.viewbox)
    let draw(geojson, style) = render-map(
      geojson,
      json.encode(style + frame),
      width: 100%,
      height: 100%,
      fit: "contain",
    )
    // The commune is drawn again on top, alone, with the same frame: its
    // outline is never covered by a neighbour.
    let territoire = projected(carte.territoire, carte.scale)
    let commune = (
      type: "FeatureCollection",
      features: territoire.features.filter(f => f.properties.code == carte.focus),
    )
    box(width: 100%, height: 5.8cm, {
      draw(bytes(json.encode(territoire)), (fill: "{couleur}", stroke: "#ffffff"))
      place(top + left, draw(
        bytes(json.encode(commune)),
        (fill: "none", stroke: carte.legend.focus.color),
      ))
    })
    v(0.3em)
    legend(carte.legend)
  },
)
