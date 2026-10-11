#import "common.typ": blue, grey

#let render(data) = {
  heading(level: 2, [Historique des subventions (#data.lignes.len())])

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
      .lignes
      .map(l => (
        text(size: 8pt, l.annee.label),
        text(size: 8pt, l.financeur.label),
        text(size: 8pt, l.projet.label),
        text(size: 8pt, l.cout.label),
        text(size: 8pt, weight: "medium", l.montant.label),
        text(size: 8pt, l.taux.label),
      ))
      .flatten()
  )
}
