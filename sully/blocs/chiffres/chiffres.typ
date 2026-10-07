#import "@preview/lilaq:0.5.0" as lq
#import "commun.typ": bleu, discret, encadre, gris

#let tuile(periode, t) = block(
  fill: gris,
  stroke: (left: 2pt + bleu),
  inset: (x: 10pt, y: 9pt),
  width: 100%,
  breakable: false,
  {
    box(
      fill: white,
      inset: (x: 4pt, y: 2pt),
      text(size: 6.5pt, fill: bleu, weight: "medium", periode),
    )
    v(0.5em)
    text(size: 13pt, weight: "bold", t.at(0))
    linebreak()
    text(size: 7.5pt, fill: discret, t.at(1))
    v(0.4em)
    text(size: 11pt, weight: "bold", t.at(2))
    linebreak()
    text(size: 7.5pt, fill: discret, t.at(3))
  },
)

#let rendu(donnees) = {
  heading(level: 2, [Subventions d'investissement])

  grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 8pt,
    ..donnees.tuiles.map(t => tuile(donnees.periode, t)),
  )

  v(0.9em)

  grid(
    columns: (1.1fr, 1fr),
    column-gutter: 10pt,
    encadre(
      [Montants accordés par année (€)],
      lq.diagram(
        width: 8cm,
        height: 3.6cm,
        xaxis: (ticks: donnees.annees.map(a => (a, text(size: 6pt)[#a]))),
        lq.bar(donnees.annees, donnees.montants, fill: bleu),
      ),
    ),
    encadre(
      [Répartition par dispositif],
      table(
        columns: (1fr, auto),
        stroke: none,
        inset: (x: 0pt, y: 3pt),
        ..donnees.dispositifs
          .map(d => (
            text(size: 8.5pt, d.nom),
            text(size: 8.5pt, weight: "medium", [#calc.round(d.montant / 1000) k€]),
          ))
          .flatten()
      ),
    ),
  )
}
