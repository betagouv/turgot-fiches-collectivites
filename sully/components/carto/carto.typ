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

#let map(spec, legend-data) = panel(
  [
    #spec.titre
    #h(0.4em)
    #text(size: 7.5pt, fill: luma(45%), weight: "regular")[#spec.communes communes]
  ],
  {
    // stroke_width rejects a `{property}` template: a string there drops the
    // whole style, fill included.
    render-map(
      read(spec.fichier, encoding: none),
      json.encode((
        fill: "{couleur}",
        stroke: "{contour}",
        stroke_width: spec.stroke,
        viewbox: spec.viewbox,
      )),
      width: 100%,
      height: 5.8cm,
      fit: "contain",
    )
    v(0.3em)
    legend(legend-data)
  },
)

#let render(data) = {
  heading(level: 2, [Cartographie])
  grid(
    columns: (1fr,) * data.cartes.len(),
    column-gutter: 10pt,
    ..data.cartes.map(carte => map(carte, data.legend)),
  )
}
