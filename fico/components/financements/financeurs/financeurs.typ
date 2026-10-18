#import "common.typ": muted, panel

#let render(data) = panel(
  [Répartition par financeur],
  if data.financeurs.len() == 0 {
    text(size: 9pt, fill: muted, style: "italic", [Aucun financement])
  } else {
    table(
      columns: (1fr, auto),
      stroke: none,
      inset: (x: 0pt, y: 3pt),
      ..data
        .financeurs
        .map(ligne => (
          text(size: 8.5pt, ligne.financeur),
          text(size: 8.5pt, weight: "medium", ligne.montant.label),
        ))
        .flatten()
    )
  },
)
