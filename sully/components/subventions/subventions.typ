#import "common.typ": blue, grey

#let render(data) = {
  heading(level: 2, [Historique des subventions (#data.len())])

  table(
    columns: (auto, auto, 1fr, auto, auto, auto),
    stroke: none,
    inset: (x: 5pt, y: 4pt),
    align: (left, left, left, right, right, right),
    fill: (_, y) => if y == 0 { none } else if calc.odd(y) { grey },
    table.header(
      ..([Année], [Dotation], [Projet], [Coût], [Subvention], [Taux]).map(c => text(
        size: 8pt,
        weight: "bold",
        fill: blue,
        c,
      )),
    ),
    table.hline(y: 1, stroke: 0.5pt + blue),
    ..data
      .map(l => (
        text(size: 8pt, [#l.annee]),
        text(size: 8pt, l.dispositif),
        text(size: 8pt, l.libelle),
        text(size: 8pt, l.cout),
        text(size: 8pt, weight: "medium", l.montant),
        text(size: 8pt, l.taux),
      ))
      .flatten()
  )
}
