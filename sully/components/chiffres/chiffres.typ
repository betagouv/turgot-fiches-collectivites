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
  heading(level: 2, [Financements reçus])

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
      [Montants reçus par année (€)],
      {
        if data.annees.len() > 0 {
          let positions = range(data.annees.len())
          lq.diagram(
            width: 8cm,
            height: 3.4cm,
            xaxis: (
              ticks: positions
                .zip(data.annees)
                .map(((position, annee)) => (position, text(size: 6pt)[#annee])),
            ),
            lq.bar(positions, data.montants, fill: blue),
          )
        }
        if data.sans_date > 0 {
          v(0.3em)
          text(size: 7pt, fill: muted)[
            #data.sans_date financement(s) sans date d'attribution, non représenté(s).
          ]
        }
      },
    ),
    panel(
      [Répartition par financeur],
      table(
        columns: (1fr, auto),
        stroke: none,
        inset: (x: 0pt, y: 3pt),
        ..data.financeurs
          .map(d => (
            text(size: 8.5pt, d.nom),
            text(size: 8.5pt, weight: "medium", [#calc.round(d.montant / 1000) k€]),
          ))
          .flatten()
      ),
    ),
  )
}
