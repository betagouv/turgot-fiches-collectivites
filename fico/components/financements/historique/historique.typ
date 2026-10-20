#import "common.typ": blue, grey, muted

#let render(data) = {
  if data.lignes.len() == 0 {
    heading(level: 2, [Historique des subventions])
    text(size: 9pt, fill: muted, style: "italic", [Aucun financement])
    return
  }

  heading(level: 2, [Historique des subventions (#data.lignes.len())])

  table(
    columns: (auto, auto, 1fr, auto, auto, auto),
    stroke: none,
    inset: (x: 5pt, y: 4pt),
    align: (left, left, left, right, right, right),
    fill: (_, y) => if y == 0 { none } else if calc.odd(y) { grey },
    table.header(
      ..([Année], [Financeur], [Projet], [Coût], [Subvention], [Taux]).map(c => text(
        size: 8pt,
        weight: "bold",
        fill: blue,
        c,
      )),
    ),
    table.hline(y: 1, stroke: 0.5pt + blue),
    ..data
      .lignes
      .map(ligne => (
        text(size: 8pt, ligne.annee.label),
        {
          text(size: 8pt, ligne.financeur.label)
          if ligne.reference.value != none {
            linebreak()
            text(size: 7pt, fill: muted, [numéro~: #ligne.reference.label])
          }
        },
        text(size: 8pt, ligne.projet.label),
        text(size: 8pt, ligne.cout.label),
        text(size: 8pt, weight: "medium", ligne.montant.label),
        text(size: 8pt, ligne.taux.label),
      ))
      .flatten()
  )
}
