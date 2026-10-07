#import "@preview/lilaq:0.5.0" as lq
#import "common.typ": blue, grey, muted, panel

#let tile(periode, t) = block(
  fill: grey,
  stroke: (left: 2pt + blue),
  inset: (x: 10pt, y: 9pt),
  width: 100%,
  breakable: false,
  {
    box(
      fill: white,
      inset: (x: 4pt, y: 2pt),
      text(size: 6.5pt, fill: blue, weight: "medium", periode),
    )
    v(0.5em)
    text(size: 13pt, weight: "bold", t.at(0))
    linebreak()
    text(size: 7.5pt, fill: muted, t.at(1))
    v(0.4em)
    text(size: 11pt, weight: "bold", t.at(2))
    linebreak()
    text(size: 7.5pt, fill: muted, t.at(3))
  },
)

#let render(data) = {
  heading(level: 2, [Subventions d'investissement])

  grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 8pt,
    ..data.tuiles.map(t => tile(data.periode, t)),
  )

  v(0.9em)

  grid(
    columns: (1.1fr, 1fr),
    column-gutter: 10pt,
    panel(
      [Montants accordés par année (€)],
      lq.diagram(
        width: 8cm,
        height: 3.4cm,
        xaxis: (ticks: data.annees.map(a => (a, text(size: 6pt)[#a]))),
        lq.bar(data.annees, data.montants, fill: blue),
      ),
    ),
    panel(
      [Répartition par dispositif],
      table(
        columns: (1fr, auto),
        stroke: none,
        inset: (x: 0pt, y: 3pt),
        ..data.dispositifs
          .map(d => (
            text(size: 8.5pt, d.nom),
            text(size: 8.5pt, weight: "medium", [#calc.round(d.montant / 1000) k€]),
          ))
          .flatten()
      ),
    ),
  )
}
