#import "@preview/mercator:0.1.2": render-map
#import "common.typ": muted, no-data, palette, panel, red

#let legend = {
  set text(size: 6.5pt, fill: muted)
  [Taux de financement]
  v(0.2em)
  stack(
    dir: ltr,
    ..palette.map(c => rect(width: 12pt, height: 5pt, fill: rgb(c), stroke: none)),
    h(5pt),
    rect(width: 12pt, height: 5pt, fill: no-data, stroke: none),
    h(5pt),
    rect(width: 12pt, height: 5pt, fill: white, stroke: 1pt + red),
  )
  v(0.15em)
  box(width: 60pt)[0 #h(1fr) 50 %+] + h(5pt) + [n.c.] + h(16pt) + [cette commune]
}

#let map(spec) = panel(
  [
    #spec.titre
    #h(0.4em)
    #text(size: 7.5pt, fill: luma(45%), weight: "regular")[#spec.communes communes]
  ],
  {
    // stroke_width n'accepte pas de template `{propriete}` : passer une chaîne
    // y fait tomber tout le style, remplissage compris.
    render-map(
      read(spec.fichier, encoding: none),
      json.encode((
        projection: (type: "mercator"),
        fill: "{couleur}",
        stroke: "{contour}",
        stroke_width: 0.005,
        viewbox_padding: 0.01,
      )),
      height: 5.8cm,
    )
    v(0.3em)
    legend
  },
)

#let render(data) = {
  heading(level: 2, [Cartographie])
  grid(
    columns: (1fr,) * data.len(),
    column-gutter: 10pt,
    ..data.map(map),
  )
}
